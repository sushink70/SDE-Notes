# Interrupt Handling: A Complete Systems Engineering Reference

> **Summary:** Interrupts are the fundamental mechanism by which hardware and software signal the CPU to preempt normal execution and handle asynchronous events. This guide covers the complete interrupt subsystem — from hardware pin assertions through IDT/GDT setup, APIC/MSI/MSI-X, Linux kernel top-half/bottom-half architecture, softirqs, tasklets, workqueues, threaded IRQs, NOHZ, interrupt affinity, and real-time extensions — with production-grade C (kernel modules), Go (userspace/eBPF), and Rust (kernel modules via rust-for-linux and bare-metal) implementations. Security threat modeling, NUMA-aware affinity, CPU isolation, and IOMMU interactions are covered throughout.

---

## Table of Contents

1. [Hardware Fundamentals](#1-hardware-fundamentals)
2. [CPU Interrupt Architecture](#2-cpu-interrupt-architecture)
3. [Interrupt Controllers: PIC, APIC, GIC](#3-interrupt-controllers)
4. [MSI and MSI-X](#4-msi-and-msi-x)
5. [Linux Kernel Interrupt Subsystem Architecture](#5-linux-kernel-interrupt-subsystem-architecture)
6. [IDT, GDT, and Interrupt Gates](#6-idt-gdt-and-interrupt-gates)
7. [Top-Half: IRQ Handlers](#7-top-half-irq-handlers)
8. [Bottom-Half Mechanisms](#8-bottom-half-mechanisms)
9. [Softirqs](#9-softirqs)
10. [Tasklets](#10-tasklets)
11. [Workqueues](#11-workqueues)
12. [Threaded IRQs](#12-threaded-irqs)
13. [IRQ Domains and Chip Descriptors](#13-irq-domains-and-chip-descriptors)
14. [NUMA-Aware Interrupt Affinity](#14-numa-aware-interrupt-affinity)
15. [CPU Isolation and IRQ Balancing](#15-cpu-isolation-and-irq-balancing)
16. [NOHZ and Tickless Kernels](#16-nohz-and-tickless-kernels)
17. [Real-Time (PREEMPT_RT) Interrupt Handling](#17-real-time-preempt_rt-interrupt-handling)
18. [NMI: Non-Maskable Interrupts](#18-nmi-non-maskable-interrupts)
19. [Inter-Processor Interrupts (IPI)](#19-inter-processor-interrupts-ipi)
20. [Virtual Interrupts: KVM, Xen, Hyper-V](#20-virtual-interrupts)
21. [eBPF and Interrupt Observability](#21-ebpf-and-interrupt-observability)
22. [Interrupt Coalescing and NAPI](#22-interrupt-coalescing-and-napi)
23. [Security Threat Model](#23-security-threat-model)
24. [C Kernel Module Implementations](#24-c-kernel-module-implementations)
25. [Go Implementations (Userspace + eBPF)](#25-go-implementations)
26. [Rust Implementations (Kernel + Bare-Metal)](#26-rust-implementations)
27. [Performance Benchmarking and Tracing](#27-performance-benchmarking-and-tracing)
28. [Architecture Diagrams (ASCII)](#28-architecture-diagrams)
29. [Rollout / Rollback Plan](#29-rollout--rollback-plan)
30. [References](#30-references)

---

## 1. Hardware Fundamentals

### 1.1 What is an Interrupt?

An interrupt is an asynchronous signal to the processor that indicates an event requiring immediate attention. The CPU suspends current execution, saves state, and transfers control to a pre-registered handler (the Interrupt Service Routine, ISR).

Interrupts are fundamentally distinct from exceptions and system calls:

| Mechanism | Source | Synchronous? | Maskable? | Example |
|-----------|--------|-------------|-----------|---------|
| Hardware Interrupt (IRQ) | External device | No | Yes (mostly) | NIC packet, disk I/O done |
| Software Interrupt | CPU instruction (INT n) | Yes | Yes | Legacy syscall (int 0x80) |
| Exception (Fault/Trap/Abort) | CPU detecting error | Yes | No | Page fault, divide-by-zero |
| NMI | Hardware (special pin) | No | No | Hardware error, watchdog |
| SMI | Chipset → SMM | No | No | ACPI power management |
| IPI | Another CPU | No | Yes | TLB shootdown, scheduler |

### 1.2 The Interrupt Request Line (IRQ)

Historically, devices connect to the interrupt controller via dedicated IRQ lines. The ISA bus defined 16 IRQ lines (IRQ0–IRQ15). PCI extended this with level-triggered shared IRQs. PCIe replaced physical lines with in-band MSI/MSI-X messages.

**IRQ triggering modes:**

- **Edge-triggered**: Interrupt fires on signal transition (low→high or high→low). CPU must re-arm for next interrupt. A missed edge = missed interrupt.
- **Level-triggered**: Interrupt fires while signal remains asserted. Device must de-assert (acknowledge) before interrupt clears. Safe for sharing.
- **Active-high / Active-low**: Polarity convention for the assertion direction.

### 1.3 Interrupt Latency Components

Total interrupt latency = hardware recognition + controller arbitration + CPU context switch + OS dispatch + handler execution.

```
Hardware pin asserted
    |
    +-- [IRQ line propagation ~1-5ns]
    |
APIC receives and arbitrates
    |
    +-- [APIC arbitration ~50-200ns]
    |
CPU INTR pin asserted
    |
    +-- [CPU completes in-flight instruction ~1-10 cycles]
    |
CPU acknowledges, saves RIP/RFLAGS/RSP
    |
    +-- [Hardware interrupt frame save ~10-20 cycles]
    |
IDT lookup, gate descriptor fetch
    |
    +-- [IDT walk ~5-15 cycles]
    |
ISR entry (arch interrupt entry stub)
    |
    +-- [register save, stack switch ~20-50 cycles]
    |
Actual handler begins executing
```

Typical total: **1–10 µs** for non-RT kernels, **< 100 µs** worst-case on PREEMPT_RT.

### 1.4 x86_64 RFLAGS and the IF Bit

The Interrupt Flag (IF, bit 9) in RFLAGS controls whether the CPU accepts maskable hardware interrupts:

- `STI` — Set IF, enable interrupts
- `CLI` — Clear IF, disable interrupts
- `PUSHF`/`POPF` — Save/restore flags (and thus IF)

**Critical:** `CLI`/`STI` are privileged (CPL=0). They affect only the current CPU. The NMI, SMI, and machine check exception (MCE) ignore IF.

```
RFLAGS Register (64-bit):
 63      22 21 20 19 18 17 16 15 14 13 12 11 10  9  8  7  6  5  4  3  2  1  0
 [reserved][ID][VIP][VIF][AC][VM][RF][ ][NT][IOPL][OF][DF][IF][TF][SF][ZF][ ][AF][ ][PF][ ][CF]
                                                                ^
                                                          Interrupt Flag
```

### 1.5 ARM64 Interrupt Architecture Differences

On ARM64 (AArch64), interrupts are controlled via PSTATE.I (IRQ mask) and PSTATE.F (FIQ mask):

- `MSR DAIFSET, #2` — Mask IRQs (set I bit)
- `MSR DAIFCLR, #2` — Unmask IRQs
- **DAIF**: Debug, SError, IRQ, FIQ mask bits

ARM uses the **Generic Interrupt Controller (GIC)** instead of APIC. GICv3/v4 support LPIs (Locality-specific Peripheral Interrupts) equivalent to MSI-X.

---

## 2. CPU Interrupt Architecture

### 2.1 x86_64 Interrupt Delivery Pipeline

```
Device asserts IRQ
       |
       v
[Local APIC or I/O APIC]
       |
       | APIC message on FSB/QPI/UPI
       v
[CPU Local APIC receives message]
       |
       | Checks TPR (Task Priority Register)
       | Checks IRR (Interrupt Request Register)
       | Sets ISR (In-Service Register)
       v
[CPU INTR pin signaled at instruction boundary]
       |
       v
[CPU completes current instruction]
       |
       v
[Microcode: saves SS, RSP, RFLAGS, CS, RIP to stack]
       |
       v
[IDT lookup: vector → gate descriptor]
       |
       v
[CS:RIP loaded from gate, CPL check, stack switch via TSS if needed]
       |
       v
[ISR (Interrupt Service Routine) begins]
```

### 2.2 The Interrupt Stack

x86_64 has **7 IST (Interrupt Stack Table)** slots per CPU in the TSS (Task State Segment). This enables switching to a known-good stack for critical exceptions/interrupts, preventing double-fault cascades from stack overflow.

```
TSS (Task State Segment) layout (simplified):
  +0x04  RSP0   ← Ring 0 stack pointer (used on privilege change)
  +0x0C  RSP1
  +0x14  RSP2
  +0x24  IST1   ← Used by NMI handler
  +0x2C  IST2   ← Used by #DF (double fault)
  +0x34  IST3   ← Used by #MC (machine check)
  +0x3C  IST4   ← Used by #DB (debug)
  ...
  +0x66  IOPB   ← I/O Permission Bitmap offset
```

Linux uses IST1 for NMI, IST2 for double fault, IST3 for MCE, IST4 for debug.

### 2.3 Interrupt Stack Frame (x86_64)

When an interrupt occurs, the CPU pushes this frame (hardware-managed, no software involvement):

```
Stack before interrupt:    Stack after interrupt (ring 3→0 transition):
                           +--------+
                           | SS     | ← Saved user stack segment
                           +--------+
                           | RSP    | ← Saved user stack pointer
                           +--------+
                           | RFLAGS | ← Saved flags (with IF=1)
                           +--------+
                           | CS     | ← Saved code segment
                           +--------+
                           | RIP    | ← Return address (next instruction)
                           +--------+
                           | Error  | ← Error code (if applicable, else none)
                           +--------+  ← RSP now points here
```

For same-privilege interrupts (kernel→kernel), SS and RSP are not pushed.

### 2.4 APIC Architecture Deep Dive

Each CPU has a **Local APIC (LAPIC)** handling:

1. Receiving interrupts from I/O APIC, other LAPICs (IPI), and self (timer, thermal, performance).
2. Tracking in-service interrupts via ISR register.
3. Sending EOI (End of Interrupt) to signal completion.
4. Arbitrating priority via TPR/PPR registers.

**LAPIC Registers (MMIO at 0xFEE00000 or x2APIC via MSR):**

| Register | Offset | Description |
|----------|--------|-------------|
| ID | 0x020 | APIC ID |
| Version | 0x030 | APIC version |
| TPR | 0x080 | Task Priority Register |
| APR | 0x090 | Arbitration Priority |
| PPR | 0x0A0 | Processor Priority |
| EOI | 0x0B0 | End Of Interrupt (write-only) |
| RRD | 0x0C0 | Remote Read |
| LDR | 0x0D0 | Logical Destination |
| DFR | 0x0E0 | Destination Format |
| SVR | 0x0F0 | Spurious Vector |
| ISR | 0x100-0x170 | In-Service Register (256 bits) |
| TMR | 0x180-0x1F0 | Trigger Mode Register (256 bits) |
| IRR | 0x200-0x270 | Interrupt Request Register (256 bits) |
| ICR | 0x300-0x310 | Interrupt Command Register (IPI) |
| LVT Timer | 0x320 | Local Vector Table: Timer |
| LVT Thermal | 0x330 | LVT: Thermal Sensor |
| LVT PMC | 0x340 | LVT: Performance Counter |
| LVT LINT0 | 0x350 | LVT: Local Interrupt 0 |
| LVT LINT1 | 0x360 | LVT: Local Interrupt 1 |
| LVT Error | 0x370 | LVT: Error |
| Timer ICR | 0x380 | Timer Initial Count |
| Timer CCR | 0x390 | Timer Current Count |
| Timer DCR | 0x3E0 | Timer Divide Config |

### 2.5 x2APIC Mode

Modern systems use x2APIC (enabled via `cpuid` check + `IA32_APIC_BASE` MSR bit 10). x2APIC uses MSR-based access (faster than MMIO), supports 32-bit APIC IDs (vs 8-bit in xAPIC), and is required for systems with >255 CPUs.

```c
/* Check x2APIC support */
uint32_t eax, ebx, ecx, edx;
__cpuid(1, eax, ebx, ecx, edx);
bool x2apic_supported = (ecx >> 21) & 1;

/* Enable x2APIC via MSR */
uint64_t apic_base = rdmsr(IA32_APIC_BASE);
apic_base |= (1 << 10); /* x2APIC enable */
apic_base |= (1 << 11); /* global APIC enable */
wrmsr(IA32_APIC_BASE, apic_base);
```

---

## 3. Interrupt Controllers

### 3.1 Legacy 8259A PIC (Programmable Interrupt Controller)

The original PC used two cascaded Intel 8259A PICs: a master (IRQ0–7) and slave (IRQ8–15) connected through IRQ2. Each maps hardware lines to CPU vectors.

**Limitations:** Only 15 usable IRQs, edge-triggered only, no CPU affinity, no per-interrupt masking without software coordination.

Linux still initializes the 8259 PIC on x86 but immediately masks all interrupts and switches to APIC mode.

### 3.2 I/O APIC (IOAPIC)

The IOAPIC sits on the PCH (Platform Controller Hub) and routes device interrupts to one or more CPUs via the APIC bus.

**IOAPIC Redirection Table Entry (64-bit per IRQ line):**

```
Bits [63:56] - Destination Field (APIC ID or logical dest)
Bit  [16]    - Interrupt Mask (1 = masked)
Bit  [15]    - Trigger Mode (0 = edge, 1 = level)
Bit  [14]    - Remote IRR (level-triggered: 1 if CPU accepted, EOI pending)
Bit  [13]    - Interrupt Input Pin Polarity (0 = high, 1 = low)
Bit  [12]    - Delivery Status (0 = idle, 1 = pending)
Bit  [11]    - Destination Mode (0 = physical, 1 = logical)
Bits [10:8]  - Delivery Mode (000=Fixed, 001=Lowest Prio, 010=SMI, 100=NMI, 101=INIT, 111=ExtINT)
Bits [7:0]   - Interrupt Vector (0x10–0xFE valid for hardware interrupts)
```

### 3.3 ARM GICv3/v4

The ARM Generic Interrupt Controller (GIC) architecture supports:

- **SGI** (Software Generated Interrupts, INTID 0–15): IPIs
- **PPI** (Private Peripheral Interrupts, INTID 16–31): per-CPU (timer)
- **SPI** (Shared Peripheral Interrupts, INTID 32–1019): device interrupts
- **LPI** (Locality-specific Peripheral Interrupts, INTID ≥ 8192): MSI-equivalent, table-based

GICv4 adds direct injection of virtual LPIs for guests (no VM exit needed for common device interrupts).

**GIC Distributor (GICD)** — Global, controls SPI routing.  
**GIC Redistributor (GICR)** — Per-CPU, handles SGI, PPI, LPI.  
**CPU Interface (ICC_*)** — System registers, fast interrupt acknowledgment.

```
Device → SPI → GICD → GICR → CPU Interface → Core
                              (ICC_IAR1_EL1 to ack)
                              (ICC_EOIR1_EL1 for EOI)
```

### 3.4 Interrupt Virtualization

**Intel VT-x / AMD-V interrupt virtualization:**

- **Virtual APIC Page**: VMCS contains a 4KB Virtual APIC page mirroring LAPIC registers. Reads/writes can be trapped or pass through (based on APIC-access page and VAPIC bitmap).
- **Posted Interrupts (Intel)**: Hardware delivers virtual interrupts directly to vCPU without VM exit if vCPU is running. Posted Interrupt Descriptor (PID) in VMCS holds pending virtual interrupts.
- **AVIC (AMD)**: Advanced Virtual Interrupt Controller — similar to posted interrupts, reduces VM exits for IPI delivery.

---

## 4. MSI and MSI-X

### 4.1 Message Signaled Interrupts

MSI replaces physical IRQ wires with in-band PCI/PCIe writes. A device "fires" an interrupt by performing a DMA write to a specific memory address with a specific data value. The LAPIC decodes this write as an interrupt.

**MSI Capability Structure (PCIe Config Space):**

```
Offset +0: Capability ID (0x05) | Next Ptr | Message Control
              [15:8]=reserved [7]=per-vector masking [6:4]=multiple msgs enabled
              [3:1]=multiple msgs capable [0]=MSI enable

Offset +4: Message Address Low (32-bit, must be 4-byte aligned)
           = 0xFEE00000 | (dest_id << 12) | (redirection << 3) | (dest_mode << 2)

Offset +8: Message Address High (64-bit MSI only)

Offset +8/12: Message Data
           = vector[7:0] | delivery_mode[10:8] | trigger_mode[15] | trigger_level[14]
```

### 4.2 MSI-X

MSI-X extends MSI to support up to 2048 vectors per device, with independent masking per vector and a table stored in a BAR (Base Address Register) region.

**MSI-X Table Entry (16 bytes):**

```
+0x0: Message Address Low
+0x4: Message Address High  
+0x8: Message Data
+0xC: Vector Control (bit 0 = mask bit)
```

**MSI-X in the Linux kernel:**

```c
/* Allocate MSI-X vectors */
struct msix_entry entries[NUM_VECTORS];
for (int i = 0; i < NUM_VECTORS; i++)
    entries[i].entry = i;
int nvecs = pci_enable_msix_range(pdev, entries, 1, NUM_VECTORS);

/* Request IRQ for each vector */
for (int i = 0; i < nvecs; i++)
    request_irq(entries[i].vector, handler, 0, "mydev", dev);
```

### 4.3 MSI-X and IOMMU Security

Without IOMMU, a compromised device can write to any MSI address — effectively injecting arbitrary interrupts. The IOMMU (Intel VT-d / AMD-Vi) restricts DMA writes, including MSI writes, to authorized destinations. **Interrupt Remapping** (IR) in VT-d adds a level of indirection: devices write to an IR table entry index, not directly to LAPIC addresses. This prevents:

- Interrupt injection attacks (device spoofing MSI to arbitrary vector)
- DMA-based interrupt storms
- Cross-tenant interrupt interference in multi-tenant baremetal

---

## 5. Linux Kernel Interrupt Subsystem Architecture

### 5.1 Top-Level Architecture

```
Hardware IRQ
     |
     v
[CPU: IDT lookup → common_interrupt entry stub]
     |
     v
[irq_enter() — marks CPU in interrupt context, updates /proc/interrupts]
     |
     v
[irq_find_mapping() → irq_desc lookup]
     |
     v
[irq_desc->handle_irq() — high-level handler (handle_edge_irq, handle_level_irq, etc.)]
     |
     v
[irqaction->handler() — driver's top-half ISR]
     |
     v
[IRQ_HANDLED / IRQ_WAKE_THREAD]
     |
  [if IRQ_WAKE_THREAD]
     v
[kthread_wake_up(irq_thread)] ← threaded IRQ
     |
     v
[irq_exit() — processes pending softirqs, checks need_resched]
     |
     v
[return to interrupted code or schedule()]
```

### 5.2 Key Data Structures

```c
/* irq_desc: per-IRQ descriptor (one per Linux IRQ number) */
struct irq_desc {
    struct irq_common_data   irq_common_data; /* shared data */
    struct irq_data          irq_data;         /* chip + domain data */
    unsigned int __percpu   *kstat_irqs;       /* per-CPU stats */
    irq_flow_handler_t       handle_irq;       /* flow handler */
    struct irqaction        *action;           /* ISR chain */
    unsigned int             status_use_accessors;
    unsigned int             core_internal_state__do_not_mess_with_it;
    unsigned int             depth;            /* nested disable depth */
    unsigned int             wake_depth;       /* nested wake depth */
    unsigned int             tot_count;
    unsigned int             irq_count;        /* for detecting broken IRQs */
    unsigned long            last_unhandled;
    unsigned int             irqs_unhandled;
    atomic_t                 threads_handled;
    int                      threads_handled_last;
    raw_spinlock_t           lock;
    struct cpumask          *percpu_enabled;
    const struct cpumask    *percpu_affinity;
    const struct cpumask    *affinity_hint;
    struct irq_affinity_notify *affinity_notify;
    cpumask_var_t            pending_mask;
    unsigned long            threads_oneshot;
    atomic_t                 threads_active;
    wait_queue_head_t        wait_for_threads;
    /* ... many more fields ... */
};

/* irqaction: per-handler (one per registered handler sharing an IRQ) */
struct irqaction {
    irq_handler_t            handler;    /* top-half handler */
    void                    *dev_id;     /* cookie passed to handler */
    void __percpu           *percpu_dev_id;
    struct irqaction        *next;       /* next handler in shared IRQ chain */
    irq_handler_t            thread_fn;  /* threaded IRQ bottom half */
    struct task_struct      *thread;     /* kthread for threaded IRQ */
    struct irqaction        *secondary;  /* secondary action */
    unsigned int             irq;
    unsigned int             flags;      /* IRQF_* flags */
    unsigned long            thread_flags;
    unsigned long            thread_mask;
    const char              *name;
    proc_dir_entry_t        *dir;
};

/* irq_chip: per-controller operations */
struct irq_chip {
    const char   *name;
    void (*irq_enable)(struct irq_data *data);
    void (*irq_disable)(struct irq_data *data);
    void (*irq_ack)(struct irq_data *data);      /* clear edge-triggered */
    void (*irq_mask)(struct irq_data *data);
    void (*irq_unmask)(struct irq_data *data);
    void (*irq_eoi)(struct irq_data *data);      /* end-of-interrupt */
    int  (*irq_set_affinity)(struct irq_data *data, const struct cpumask *dest, bool force);
    int  (*irq_set_type)(struct irq_data *data, unsigned int flow_type);
    int  (*irq_set_vcpu_affinity)(struct irq_data *data, void *vcpu_info);
    /* ... */
};
```

### 5.3 IRQ Flags (IRQF_*)

```c
#define IRQF_SHARED         0x00000080  /* share IRQ with other handlers */
#define IRQF_PROBE_SHARED   0x00000100  /* OK if sharing not available */
#define IRQF_TIMER          0x00000200  /* flag for timer interrupts */
#define IRQF_PERCPU         0x00000400  /* handler is per-CPU */
#define IRQF_NOBALANCING    0x00000800  /* exclude from IRQ balancing */
#define IRQF_IRQPOLL        0x00001000  /* used for polling (no spurious check) */
#define IRQF_ONESHOT        0x00002000  /* keep IRQ masked until thread_fn done */
#define IRQF_NO_SUSPEND     0x00004000  /* don't disable during suspend */
#define IRQF_FORCE_RESUME   0x00008000  /* force enable after suspend even if disabled */
#define IRQF_NO_THREAD      0x00010000  /* do NOT force-thread this IRQ */
#define IRQF_EARLY_RESUME   0x00020000  /* resume IRQ early on syscore_resume */
#define IRQF_COND_SUSPEND   0x00040000  /* suspend if all handlers have it */
#define IRQF_NO_AUTOEN      0x00080000  /* don't enable IRQ on request_irq */
#define IRQF_NO_DEBUG       0x00100000  /* skip long IRQ check for percpu handler */
```

### 5.4 Flow Handlers

Flow handlers implement the high-level IRQ protocol for different trigger types:

```c
/* Edge-triggered: ack immediately, no mask needed */
void handle_edge_irq(struct irq_desc *desc);

/* Level-triggered: mask during handling, unmask after all handlers done */
void handle_level_irq(struct irq_desc *desc);

/* Fast-EOI: send EOI before calling handlers (for certain APIC configs) */
void handle_fasteoi_irq(struct irq_desc *desc);

/* Per-CPU: no locking, used for timer/IPI */
void handle_percpu_irq(struct irq_desc *desc);

/* Bad/spurious */
void handle_bad_irq(struct irq_desc *desc);
void handle_spurious_irq(struct irq_desc *desc);

/* MSI/MSI-X edge: similar to handle_edge_irq but EOI to APIC first */
void handle_edge_eoi_irq(struct irq_desc *desc);
```

### 5.5 The `irq_enter` / `irq_exit` Boundary

```c
/* irq_enter(): called at start of hardware interrupt handling */
void irq_enter(void) {
    rcu_irq_enter();
    if (is_idle_task(current) && !in_interrupt()) {
        /* Interrupt from idle: account time */
        tick_irq_enter();
        _local_bh_enable();
    }
    __irq_enter();  /* sets HARDIRQ_OFFSET in preempt_count */
}

/* irq_exit(): called at end, may trigger softirq processing */
void irq_exit(void) {
    __irq_exit_rcu();
    rcu_irq_exit();
    /* If not in nested interrupt and softirqs pending: */
    if (!in_interrupt() && local_softirq_pending())
        invoke_softirq();  /* or __do_softirq() */
}
```

The `preempt_count` field encodes the current context:

```
preempt_count bits:
[31:20] NMI count (1 bit used)
[19:16] Hardirq count (4 bits: supports 16 nested hardirqs)
[15:8]  Softirq count (8 bits)
[7:0]   Preemption disable count (8 bits)

in_hardirq()  = (preempt_count & HARDIRQ_MASK) != 0
in_softirq()  = (preempt_count & SOFTIRQ_MASK) != 0
in_interrupt() = (preempt_count & (HARDIRQ_MASK|SOFTIRQ_MASK|NMI_MASK)) != 0
```

---

## 6. IDT, GDT, and Interrupt Gates

### 6.1 Interrupt Descriptor Table (IDT)

The IDT is a 256-entry table (up to 256 vectors). Each entry is a **gate descriptor** (16 bytes on x86_64).

**Gate Descriptor Format (64-bit):**

```
Bits 127:96:   [Offset[63:32]]
Bits  95:64:   [reserved]
Bits  63:32:   [Offset[31:16] | P | DPL | Type | IST | Segment Selector | Offset[15:0]]

Where:
  P    = Present bit
  DPL  = Descriptor Privilege Level (0=kernel, 3=user can invoke via INT instruction)
  Type = Gate type:
         0xE = 64-bit Interrupt Gate  (clears IF on entry)
         0xF = 64-bit Trap Gate       (preserves IF on entry)
  IST  = Interrupt Stack Table index (0 = use RSP0, 1-7 = use IST1-7 from TSS)
```

**Key distinction**: Interrupt gates clear IF (disabling further interrupts). Trap gates do not. Linux uses interrupt gates for all hardware interrupts and most exceptions.

### 6.2 IDT Setup in Linux

```c
/* arch/x86/kernel/idt.c */

/* Linux uses a static IDT with fixed entries */
static gate_desc idt_table[IDT_ENTRIES] __page_aligned_bss;
struct desc_ptr idt_descr __ro_after_init = {
    .size = (IDT_ENTRIES * 2 * sizeof(unsigned long)) - 1,
    .address = (unsigned long) idt_table,
};

/* Vector assignments */
#define FIRST_EXTERNAL_VECTOR   0x20  /* 0x00-0x1F: CPU exceptions */
#define IA32_SYSCALL_VECTOR     0x80  /* legacy int 0x80 syscall */
#define LOCAL_TIMER_VECTOR      0xec  /* APIC local timer */
#define NMI_VECTOR              0x02

/* Set an IDT entry */
static void set_intr_gate(unsigned int n, const void *addr) {
    struct idt_data data;
    init_idt_data(&data, n, addr);
    idt_setup_from_table(idt_table, &data, 1, true);
}
```

### 6.3 Interrupt Entry Stubs

Linux generates per-vector entry stubs at boot time (since 5.x kernel: compile-time with `DEFINE_IDTENTRY_*` macros). Each stub:

1. Pushes the vector number
2. Calls `common_interrupt` (or vector-specific entry)
3. Common code saves all registers, switches to kernel stack if needed
4. Calls `do_IRQ` → `handle_irq`

```c
/* include/linux/idtentry.h */

/* Standard external interrupt */
#define DEFINE_IDTENTRY_IRQ(func)                           \
    static void __##func(struct pt_regs *regs, u32 vector); \
    __visible noinstr void func(struct pt_regs *regs,       \
                                u32 vector) {               \
        irqentry_state_t state = irqentry_enter(regs);      \
        instrumentation_begin();                            \
        __##func(regs, vector);                             \
        instrumentation_end();                              \
        irqentry_exit(regs, state);                         \
    }                                                       \
    static void __##func(struct pt_regs *regs, u32 vector)

/* Sysvec (local APIC-sourced) */
#define DEFINE_IDTENTRY_SYSVEC(func)  /* similar, with APIC EOI */
```

### 6.4 GDT and Privilege Rings

The GDT (Global Descriptor Table) defines memory segments. On x86_64 with long mode, segmentation is mostly bypass (all segments are flat), but CS, SS segment selectors still encode **CPL (Current Privilege Level)**.

When an interrupt transitions from ring 3 (user) to ring 0 (kernel):
1. CPU reads RSP0 from TSS (or IST[n] if specified)
2. Switches to kernel stack
3. Saves user SS, RSP, RFLAGS, CS, RIP
4. Loads new CS from IDT gate (ring 0 CS)
5. Jumps to ISR

This privilege transition is the **only** time TSS RSP0 is consulted for interrupt handling.

---

## 7. Top-Half: IRQ Handlers

### 7.1 Constraints of the Top-Half

The top-half ISR runs with:
- Hardirq context (`in_hardirq()` = true)
- Interrupts disabled (IF=0 for interrupt gates)
- Cannot sleep / block
- Cannot call schedule()
- Cannot acquire sleeping locks (mutex, semaphore)
- Can use spinlocks (`spin_lock` — no preemption disable since already disabled)
- Should be as short as possible

**What to do in the top-half:**
- Acknowledge the interrupt to the device (write to status register)
- Read minimal state from device registers
- Wake a bottom-half (schedule softirq, tasklet, or threaded IRQ)
- Update per-CPU statistics

**What NOT to do:**
- I/O operations (disk, network socket)
- Memory allocation with `GFP_KERNEL` (may sleep)
- Mutex/semaphore operations
- Any function that might call `schedule()`

### 7.2 Return Values

```c
typedef enum irqreturn {
    IRQ_NONE        = (0 << 0),  /* handler did not handle this IRQ */
    IRQ_HANDLED     = (1 << 0),  /* handler processed this IRQ */
    IRQ_WAKE_THREAD = (1 << 1),  /* wake the handler thread (threaded IRQ) */
} irqreturn_t;
```

For shared IRQs, the kernel iterates all registered handlers until one returns `IRQ_HANDLED` or all return `IRQ_NONE` (which triggers spurious interrupt detection).

### 7.3 request_irq and free_irq

```c
/* Request an IRQ */
int request_irq(unsigned int irq,           /* Linux IRQ number */
                irq_handler_t handler,       /* top-half handler */
                unsigned long flags,         /* IRQF_* */
                const char *name,            /* /proc/interrupts name */
                void *dev_id);               /* cookie (must be unique for shared) */

/* Threaded version: separate top-half and thread_fn */
int request_threaded_irq(unsigned int irq,
                         irq_handler_t handler,     /* top-half (can be NULL) */
                         irq_handler_t thread_fn,   /* bottom-half thread */
                         unsigned long flags,
                         const char *name,
                         void *dev_id);

/* Per-CPU IRQ (no affinity, no sharing) */
int request_percpu_irq(unsigned int irq,
                       irq_handler_t handler,
                       const char *devname,
                       void __percpu *percpu_dev_id);

/* Release */
void free_irq(unsigned int irq, void *dev_id);
```

### 7.4 Interrupt Context Checking

```c
/* Runtime checks */
if (in_hardirq())
    /* We are in a hardware interrupt handler */

if (in_softirq())
    /* We are in a softirq/tasklet handler */

if (in_interrupt())
    /* Either hardirq or softirq context */

if (in_atomic())
    /* Cannot sleep: preemption disabled, or in_interrupt() */

/* Compile-time annotation */
might_sleep();  /* warns if called from non-sleepable context */
```

---

## 8. Bottom-Half Mechanisms

### 8.1 Overview and Comparison

The bottom-half is work deferred from the interrupt top-half to run with interrupts re-enabled (and sometimes in a schedulable context).

```
Top-Half (hardirq context)
    |
    | defer work via:
    +---> raise_softirq()      → runs in softirq context (irq_exit or ksoftirqd)
    |                             - per-CPU, LIFO-ish priority, NOT preemptible
    |
    +---> tasklet_schedule()   → built on softirq (HI_SOFTIRQ or TASKLET_SOFTIRQ)
    |                             - per-tasklet serialized, dynamic allocation
    |
    +---> queue_work()         → workqueue (process context kthread)
    |                             - sleepable, NUMA-aware, concurrency-managed
    |
    +---> IRQ_WAKE_THREAD      → dedicated per-IRQ kthread
                                  - simplest model, IRQF_ONESHOT support
```

| Mechanism | Context | Sleepable | Per-CPU | Serialized | Use case |
|-----------|---------|-----------|---------|------------|----------|
| Softirq | Softirq (BH) | No | Yes | No | Network RX/TX, timer, block |
| Tasklet | Softirq (BH) | No | No | Per-tasklet | Simple deferred work |
| Workqueue | Process | Yes | Optional | Optional | Complex work needing sleep |
| Threaded IRQ | Process | Yes | No | Per-handler | RT-friendly drivers |

---

## 9. Softirqs

### 9.1 Architecture

Softirqs are the fastest bottom-half mechanism — essentially continuation callbacks running in a special "softirq context" with interrupts enabled but preemption disabled.

**Registered softirq vectors (priority order):**

```c
/* include/linux/interrupt.h */
enum {
    HI_SOFTIRQ      = 0,  /* tasklet_hi (highest priority) */
    TIMER_SOFTIRQ   = 1,  /* timer wheel callbacks */
    NET_TX_SOFTIRQ  = 2,  /* network transmit */
    NET_RX_SOFTIRQ  = 3,  /* network receive (NAPI) */
    BLOCK_SOFTIRQ   = 4,  /* block device completion */
    IRQ_POLL_SOFTIRQ= 5,  /* block device polling */
    TASKLET_SOFTIRQ = 6,  /* regular tasklets */
    SCHED_SOFTIRQ   = 7,  /* scheduler load balancing */
    HRTIMER_SOFTIRQ = 8,  /* high-resolution timer */
    RCU_SOFTIRQ     = 9,  /* RCU callbacks (lowest priority) */
    NR_SOFTIRQS     = 10
};
```

### 9.2 Softirq Data Structures

```c
/* Per-softirq action */
struct softirq_action {
    void (*action)(struct softirq_action *);
};

static struct softirq_action softirq_vec[NR_SOFTIRQS] __cacheline_aligned_in_smp;

/* Per-CPU pending bitmask */
DEFINE_PER_CPU_ALIGNED(irq_cpustat_t, irq_stat);
/* irq_stat.__softirq_pending is a bitmask of pending softirqs */

/* Raise a softirq from hardirq context */
void raise_softirq(unsigned int nr) {
    unsigned long flags;
    local_irq_save(flags);
    raise_softirq_irqoff(nr);  /* sets bit in __softirq_pending */
    local_irq_restore(flags);
}

/* Raise without disabling interrupts (must already be in hardirq or disabled) */
void raise_softirq_irqoff(unsigned int nr) {
    __raise_softirq_irqoff(nr);
    if (!in_interrupt())
        wakeup_softirqd();  /* wake ksoftirqd if not in interrupt context */
}
```

### 9.3 Softirq Processing

```c
/* Called from irq_exit() or ksoftirqd */
asmlinkage __visible void __softirq_entry __do_softirq(void) {
    unsigned long end = jiffies + MAX_SOFTIRQ_TIME;
    unsigned long old_flags = current->flags;
    int max_restart = MAX_SOFTIRQ_RESTART;  /* = 10 */
    struct softirq_action *h;
    __u32 pending;

    pending = local_softirq_pending();
    /* ... */

    __local_bh_disable_ip(_RET_IP_, SOFTIRQ_OFFSET);  /* enter softirq context */

restart:
    set_softirq_pending(0);  /* clear pending bits */
    local_irq_enable();       /* RE-ENABLE interrupts during processing */

    h = softirq_vec;
    while ((softirq_bit = ffs(pending))) {
        h += softirq_bit - 1;
        h->action(h);         /* call the softirq handler */
        h++;
        pending >>= softirq_bit;
    }

    local_irq_disable();      /* disable to check if more raised */
    pending = local_softirq_pending();
    if (pending) {
        if (time_before(jiffies, end) && !need_resched() && --max_restart)
            goto restart;
        wakeup_softirqd();    /* offload remaining to ksoftirqd */
    }
    __local_bh_enable(SOFTIRQ_OFFSET);  /* leave softirq context */
}
```

### 9.4 ksoftirqd

Each CPU runs a `ksoftirqd/N` kthread that handles softirqs when:
- Softirq processing would monopolize CPU for too long
- Softirqs are raised outside interrupt context (from process context)

`ksoftirqd` runs at SCHED_NORMAL priority (nice 0 by default). On PREEMPT_RT kernels, it's elevated and softirqs run in threaded context.

### 9.5 local_bh_enable/disable

```c
/* Disable softirq processing (used in process context to protect data shared with softirq) */
local_bh_disable();   /* increments SOFTIRQ_DISABLE_OFFSET in preempt_count */
/* critical section */
local_bh_enable();    /* decrements, runs pending softirqs if not in interrupt */

/* In network driver (process context touching RX ring shared with NET_RX_SOFTIRQ): */
local_bh_disable();
spin_lock(&ring->lock);
/* access ring buffer */
spin_unlock(&ring->lock);
local_bh_enable();
```

---

## 10. Tasklets

### 10.1 Architecture

Tasklets are built on top of softirqs (HI_SOFTIRQ and TASKLET_SOFTIRQ). They provide a simpler API than raw softirqs and guarantee that a given tasklet runs on only one CPU at a time (serialized per-tasklet).

### 10.2 Tasklet Data Structures

```c
struct tasklet_struct {
    struct tasklet_struct *next;  /* next in per-CPU list */
    unsigned long          state; /* TASKLET_STATE_SCHED | TASKLET_STATE_RUN */
    atomic_t               count; /* 0 = enabled, >0 = disabled */
    bool                   use_callback;
    union {
        void (*func)(unsigned long);    /* legacy callback */
        void (*callback)(struct tasklet_struct *); /* modern callback */
    };
    unsigned long data;  /* passed to func */
};

/* State bits */
#define TASKLET_STATE_SCHED  0  /* scheduled for execution */
#define TASKLET_STATE_RUN    1  /* currently running (SMP only) */
```

### 10.3 Tasklet Usage

```c
/* Static initialization */
DECLARE_TASKLET(name, callback);
DECLARE_TASKLET_DISABLED(name, callback);

/* Dynamic initialization */
void tasklet_init(struct tasklet_struct *t,
                  void (*func)(unsigned long),
                  unsigned long data);

/* Modern API */
void tasklet_setup(struct tasklet_struct *t,
                   void (*callback)(struct tasklet_struct *));

/* Schedule (from any context) */
void tasklet_schedule(struct tasklet_struct *t);    /* TASKLET_SOFTIRQ */
void tasklet_hi_schedule(struct tasklet_struct *t); /* HI_SOFTIRQ */

/* Disable/enable (count-based) */
void tasklet_disable(struct tasklet_struct *t);  /* waits if running */
void tasklet_disable_nosync(struct tasklet_struct *t);
void tasklet_enable(struct tasklet_struct *t);

/* Kill: wait for completion and prevent rescheduling */
void tasklet_kill(struct tasklet_struct *t);  /* may sleep */
```

### 10.4 Tasklet Scheduling Internals

```c
void tasklet_schedule(struct tasklet_struct *t) {
    if (!test_and_set_bit(TASKLET_STATE_SCHED, &t->state)) {
        /* Not yet scheduled: add to per-CPU list and raise softirq */
        __tasklet_schedule(t);
    }
    /* If already scheduled: no-op (tasklet will run once) */
}

void __tasklet_schedule(struct tasklet_struct *t) {
    struct tasklet_head *head;
    unsigned long flags;
    local_irq_save(flags);
    head = &__get_cpu_var(tasklet_vec);
    t->next = NULL;
    *head->tail = t;
    head->tail = &t->next;
    raise_softirq_irqoff(TASKLET_SOFTIRQ);
    local_irq_restore(flags);
}
```

**Note:** Tasklets are considered legacy. New code should prefer threaded IRQs or workqueues. The kernel community has discussed removing tasklets (they add SMP complexity and latency).

---

## 11. Workqueues

### 11.1 Architecture

Workqueues execute work in process context (a kthread), making them the only bottom-half mechanism that can sleep. Linux uses the **CMWQ (Concurrency Managed Workqueue)** infrastructure introduced in kernel 2.6.36.

### 11.2 CMWQ Architecture

```
Workqueue (logical)
    |
    | work items submitted to
    v
Worker Pool (per-NUMA-node, per-priority: NORMAL or HIGHPRI)
    |
    | one or more
    v
Worker Threads (kworker/N:M) — dynamically created/destroyed
    |
    | execute
    v
work_struct callbacks
```

**Key CMWQ properties:**
- Worker threads are shared across all non-ordered workqueues (same pool)
- When a worker blocks, another worker is created to maintain concurrency
- Concurrency ceiling: one running worker per pool (by default)
- CPU hotplug aware, NUMA-aware placement

### 11.3 Work Item API

```c
/* work_struct: non-sleepable basic work (can sleep, but not on a fixed schedule) */
struct work_struct {
    atomic_long_t data;       /* flags + wq_pool pointer */
    struct list_head entry;
    work_func_t func;
};

/* delayed_work: work with a timer delay */
struct delayed_work {
    struct work_struct work;
    struct timer_list timer;
    struct workqueue_struct *wq;
    int cpu;
};

/* Initialize */
INIT_WORK(&work, work_function);
INIT_DELAYED_WORK(&dwork, work_function);

/* Submit */
bool queue_work(struct workqueue_struct *wq, struct work_struct *work);
bool queue_work_on(int cpu, struct workqueue_struct *wq, struct work_struct *work);
bool queue_delayed_work(struct workqueue_struct *wq,
                        struct delayed_work *dwork,
                        unsigned long delay); /* in jiffies */

/* System workqueues (always available) */
queue_work(system_wq, &work);           /* NORMAL priority */
queue_work(system_highpri_wq, &work);   /* HIGHPRI */
queue_work(system_long_wq, &work);      /* for long-running work */
queue_work(system_unbound_wq, &work);   /* not bound to any CPU */
queue_work(system_freezable_wq, &work); /* freezable for suspend */
queue_work(system_power_efficient_wq, &work); /* bound or unbound per config */

/* Cancel */
bool cancel_work_sync(struct work_struct *work);    /* may sleep */
bool cancel_delayed_work_sync(struct delayed_work *dwork);

/* Flush: wait for all currently queued work to complete */
void flush_workqueue(struct workqueue_struct *wq);
void flush_work(struct work_struct *work);
```

### 11.4 Custom Workqueues

```c
/* Create workqueue */
struct workqueue_struct *wq;

/* Ordered: work items execute serially in submission order */
wq = alloc_ordered_workqueue("my_ordered_wq", WQ_MEM_RECLAIM);

/* Unordered, multi-threaded */
wq = alloc_workqueue("my_wq",
                     WQ_UNBOUND |       /* not bound to specific CPU */
                     WQ_HIGHPRI |       /* high priority workers */
                     WQ_MEM_RECLAIM,    /* guaranteed forward progress (memory pressure) */
                     max_active);       /* 0 = default concurrency */

/* Destroy */
destroy_workqueue(wq);
```

### 11.5 WQ Flags

```c
#define WQ_UNBOUND          (1 << 1)  /* not bound to any cpu */
#define WQ_FREEZABLE        (1 << 2)  /* freeze during suspend */
#define WQ_MEM_RECLAIM      (1 << 3)  /* guaranteed forward progress */
#define WQ_HIGHPRI          (1 << 4)  /* high priority worker threads */
#define WQ_CPU_INTENSIVE    (1 << 5)  /* CPU intensive workload */
#define WQ_SYSFS            (1 << 6)  /* visible in /sys/bus/workqueue/ */
#define WQ_POWER_EFFICIENT  (1 << 7)  /* power-efficient unbound */
#define WQ_BH               (1 << 8)  /* BH compat, disables preemption */
#define WQ_ORDERED          __WQ_ORDERED
```

---

## 12. Threaded IRQs

### 12.1 Concept

Threaded IRQs (`request_threaded_irq`) create a dedicated kernel thread per IRQ line that runs the "thread_fn" bottom half. This is the preferred model for new drivers and is mandatory for PREEMPT_RT compatibility.

### 12.2 Lifecycle

```
Hardware IRQ fires
    |
    v
Top-half handler() called in hardirq context
    |
    +-- returns IRQ_HANDLED → done, no thread needed
    |
    +-- returns IRQ_WAKE_THREAD → wake the IRQ thread
    |
    +-- handler is NULL → kernel provides default that returns IRQ_WAKE_THREAD
    |
    v
irq_thread (kthread: irq/N-name) scheduled
    |
    v
thread_fn() called in process context (may sleep)
    |
    v
IRQF_ONESHOT: IRQ line kept masked until thread_fn returns
    (prevents re-entry while thread processes current interrupt)
```

### 12.3 IRQF_ONESHOT

Critical for level-triggered interrupts with threaded handlers. Without `IRQF_ONESHOT`:
- IRQ fires, top-half runs, thread_fn scheduled, IRQ re-enabled
- Device still asserting level → IRQ fires again immediately
- Infinite interrupt storm

With `IRQF_ONESHOT`:
- After top-half acks, IRQ line is masked
- Thread runs, processes interrupt, clears device interrupt source
- On thread_fn return, IRQ line is unmasked

### 12.4 IRQ Thread Priority

```c
/* IRQ threads run at SCHED_FIFO priority 50 by default */
/* Configurable via /proc/irq/N/smp_affinity */

/* From kernel: irq_setup_forced_threading() in kernel/irq/manage.c */
/* On RT kernels: ALL interrupt handlers are forced to threaded mode */
```

---

## 13. IRQ Domains and Chip Descriptors

### 13.1 IRQ Domain

An IRQ domain maps hardware interrupt numbers (HW IRQ) to Linux IRQ numbers (virtual IRQ / virq). This abstraction allows multiple interrupt controllers with overlapping HW IRQ numbering.

```c
/* irq_domain types */
enum irq_domain_bus_token {
    DOMAIN_BUS_ANY,
    DOMAIN_BUS_WIRED,
    DOMAIN_BUS_GENERIC_MSI,
    DOMAIN_BUS_PCI_MSI,
    DOMAIN_BUS_PLATFORM_MSI,
    DOMAIN_BUS_NEXUS,
    DOMAIN_BUS_IPI,
    DOMAIN_BUS_FSL_MC_MSI,
    DOMAIN_BUS_TI_SCI_INTA_MSI,
    DOMAIN_BUS_WAKEUP,
    DOMAIN_BUS_VMD_MSI,
};

/* Create a domain */
struct irq_domain *irq_domain_add_linear(
    struct device_node *of_node,
    unsigned int size,             /* max HW IRQ number */
    const struct irq_domain_ops *ops,
    void *host_data);

/* Ops structure */
struct irq_domain_ops {
    int (*match)(struct irq_domain *d, struct device_node *node,
                 enum irq_domain_bus_token bus_token);
    int (*map)(struct irq_domain *d, unsigned int virq, irq_hw_number_t hw);
    void (*unmap)(struct irq_domain *d, unsigned int virq);
    int (*xlate)(struct irq_domain *d, struct device_node *node,
                 const u32 *intspec, unsigned int intsize,
                 unsigned long *out_hwirq, unsigned int *out_type);
    /* ... */
};
```

### 13.2 IRQ Mapping

```c
/* Allocate a virq for a hw IRQ */
unsigned int irq_create_mapping(struct irq_domain *domain,
                                irq_hw_number_t hwirq);

/* Find existing virq for hw IRQ */
unsigned int irq_find_mapping(struct irq_domain *domain,
                              irq_hw_number_t hwirq);

/* MSI domain: allocate virqs for MSI/MSI-X */
int irq_domain_alloc_irqs(struct irq_domain *domain,
                          unsigned int nr_irqs,
                          int node,
                          void *arg);
```

---

## 14. NUMA-Aware Interrupt Affinity

### 14.1 CPU Affinity Fundamentals

Interrupt affinity controls which CPU(s) handle a given interrupt. Optimal affinity:
- Routes interrupts to CPUs in the same NUMA node as the device's memory
- Reduces cross-node memory accesses (NUMA penalty: 2–4x latency)
- Keeps interrupt processing and application processing on same CPU (cache warm)

### 14.2 Sysfs Interface

```bash
# View current affinity
cat /proc/irq/24/smp_affinity        # hex bitmask
cat /proc/irq/24/smp_affinity_list   # human-readable CPU list

# Set affinity (root required)
echo "3"    > /proc/irq/24/smp_affinity       # CPUs 0 and 1 (bitmask 0x3)
echo "0-3"  > /proc/irq/24/smp_affinity_list  # CPUs 0-3
echo "4,8"  > /proc/irq/24/smp_affinity_list  # CPUs 4 and 8

# View effective affinity (may differ from requested)
cat /proc/irq/24/effective_affinity
cat /proc/irq/24/effective_affinity_list

# NUMA node for an IRQ
cat /sys/kernel/irq/24/node
```

### 14.3 Programmatic Affinity Setting

```c
/* Set IRQ affinity from kernel module */
int irq_set_affinity(unsigned int irq, const struct cpumask *cpumask);
int irq_force_affinity(unsigned int irq, const struct cpumask *cpumask);

/* Set affinity hint (advisory, irqbalance may override) */
int irq_set_affinity_hint(unsigned int irq, const struct cpumask *m);

/* NUMA-aware: set affinity to CPUs on same node as device */
int irq_set_affinity(irq, cpumask_of_node(dev_to_node(&pdev->dev)));
```

### 14.4 irqbalance

`irqbalance` is a userspace daemon that distributes IRQs across CPUs to balance load and optimize for NUMA topology. Key concepts:

```bash
# irqbalance policy hints via sysfs
echo "1" > /proc/irq/24/node     # bind to NUMA node 1

# irqbalance config: /etc/sysconfig/irqbalance
IRQBALANCE_ONESHOT=0             # 0=continuous, 1=run once
IRQBALANCE_BANNED_CPUS=f0000000  # exclude these CPUs (hex mask)
IRQBALANCE_ARGS="--hintpolicy=subset"  # honor affinity hints

# Policies:
# exact   = exactly respect hint
# subset  = hint is a subset restriction
# ignore  = ignore hints
```

### 14.5 RPS/RFS (Receive Packet Steering)

For network devices, **RPS** (Receive Packet Steering) extends interrupt affinity to the application level:

```bash
# RPS: distribute received packets across CPUs (software-only, no NIC support needed)
echo "ff"  > /sys/class/net/eth0/queues/rx-0/rps_cpus  # all CPUs

# RFS: steer packets to CPU running the receiving application (flow-aware)
echo 32768 > /proc/sys/net/core/rps_sock_flow_entries
echo 2048  > /sys/class/net/eth0/queues/rx-0/rps_flow_cnt
```

---

## 15. CPU Isolation and IRQ Balancing

### 15.1 isolcpus

Kernel boot parameter to remove CPUs from the general scheduling and IRQ domains:

```bash
# /etc/default/grub
GRUB_CMDLINE_LINUX="isolcpus=2-7 nohz_full=2-7 rcu_nocbs=2-7"
```

Effects of `isolcpus=2-7`:
- CPUs 2-7 removed from scheduler load balancing
- IRQs not automatically assigned to these CPUs
- Must explicitly set affinity to use these CPUs
- Does NOT prevent per-CPU kthreads from running there

### 15.2 Fully Isolated CPUs for Real-Time

```bash
# Complete RT isolation stack:
isolcpus=domain,managed_irq,2-7   # isolate + keep managed IRQs away
nohz_full=2-7                      # disable periodic tick
rcu_nocbs=2-7                      # move RCU callbacks off these CPUs
irqaffinity=0-1                    # default IRQ affinity = CPUs 0-1 only
tsc=reliable                       # disable TSC stability checking (saves IPI)
```

### 15.3 Verifying Isolation

```bash
# Check which IRQs land on isolated CPUs
for irq in /proc/irq/*/smp_affinity_list; do
    aff=$(cat $irq); echo "$irq: $aff"
done

# Check CPU usage (wakeups on isolated CPUs)
perf stat -e cs -C 2 sleep 10   # context switches on CPU 2

# trace-cmd to see what runs on isolated CPUs
trace-cmd record -C 2 -e sched:sched_switch sleep 10
trace-cmd report | grep cpu=2
```

---

## 16. NOHZ and Tickless Kernels

### 16.1 The Periodic Tick Problem

The traditional Linux kernel used a fixed-rate periodic timer (HZ = 100/250/1000) that fired on every CPU. This prevents CPUs from staying in deep sleep states and adds ~1000 interrupts/sec of OS overhead.

### 16.2 NOHZ Modes

```
CONFIG_NO_HZ_IDLE    — stop tick when CPU is idle (default since 3.10)
CONFIG_NO_HZ_FULL    — stop tick when CPU runs a single task (RT/HPC use)
```

**NOHZ_FULL** requirements:
- At least one non-nohz CPU (for timekeeping)
- `nohz_full=` boot parameter specifying the isolated CPUs
- `rcu_nocbs=` to move RCU callback invocation off those CPUs
- Process must be the sole runnable task on the CPU

### 16.3 Timer Interrupts in NOHZ

```bash
# Check tick rate and NOHZ status
cat /proc/timer_list | grep -A5 "tick_cpu_device"

# See interrupts per CPU (Column = CPU0, CPU1, ...)
cat /proc/interrupts | grep "LOC"    # local APIC timer
cat /proc/interrupts | grep "TIM"    # timer

# With NOHZ_FULL: isolated CPUs should show near-zero LOC count
```

### 16.4 Adaptive-Ticks and RCU

NOHZ_FULL requires RCU to not require per-CPU tick activity. `rcu_nocbs=N` moves RCU callback invocation to `rcuop/N` and `rcuog/N` kthreads, allowing the tick to stop.

```bash
# Verify RCU offloading
cat /sys/kernel/debug/rcu/rcu_preempt/rcuog_count  # per-CPU offload thread count
dmesg | grep "nocb"  # RCU nocb initialization messages
```

---

## 17. Real-Time (PREEMPT_RT) Interrupt Handling

### 17.1 PREEMPT_RT Philosophy

PREEMPT_RT (now mainlined in Linux 6.12+) converts almost all interrupt handlers to kernel threads, enabling full kernel preemptibility and bounded latency.

**Key transformations under PREEMPT_RT:**

| Vanilla | PREEMPT_RT |
|---------|-----------|
| Hardirq runs with IF=0 | Hardirq runs in its own kthread, IF=1 |
| Spinlocks disable preemption | RT mutexes (sleeping locks) |
| softirqs run in irq_exit | softirqs run in ksoftirqd threads |
| local_bh_disable masks softirqs | BH disabled via lock, not preemption |
| NMI still non-maskable | NMI still non-maskable |

### 17.2 Interrupt Threading in PREEMPT_RT

```c
/* On PREEMPT_RT: ALL interrupts except NMI, MCE, LAPIC timer, IPI
   are converted to threaded interrupts automatically via:
   CONFIG_IRQ_FORCED_THREADING=y (set by PREEMPT_RT) */

/* irq_setup_forced_threading() in kernel/irq/manage.c converts:
   - handlers without IRQF_NO_THREAD
   - to threaded handlers in kthread at SCHED_FIFO prio 50 */
```

### 17.3 Measuring RT Latency

```bash
# cyclictest: measures scheduling latency
cyclictest --mlockall --smp --priority=80 --interval=200 --distance=0 \
           --duration=60 --histogram=400 --quiet

# With CPU isolation:
cyclictest -t1 -p99 -i200 -a2 -d0 -l1000000

# Output interpretation:
# T: 0 (0: 0) P:99 I:200 C:1000000 Min:  3 Act: 12 Avg:  9 Max:  47
#                                         ^min µs      ^avg µs  ^max µs

# hwlatdetect: detect SMI/hardware latency
hwlatdetect --duration=60 --threshold=10  # flag latencies > 10µs
```

### 17.4 Locking in RT Context

```c
/* Under PREEMPT_RT, raw_spinlock_t is a true spinlock (IF=0 while held) */
/* spin_lock_t becomes a sleeping RT mutex */

/* For code that MUST spin (cannot sleep): use raw_spinlock */
raw_spinlock_t lock;
raw_spin_lock(&lock);        /* disables preemption + interrupts */
raw_spin_unlock(&lock);

/* For regular mutual exclusion: use spinlock (becomes RT mutex on RT) */
spinlock_t lock;
spin_lock(&lock);            /* on RT: may sleep if contended */
spin_unlock(&lock);

/* Bottom-half locking */
spin_lock_bh(&lock);         /* disables BH + acquires lock */
spin_unlock_bh(&lock);

/* IRQ-safe locking */
spin_lock_irqsave(&lock, flags);
spin_unlock_irqrestore(&lock, flags);
/* On PREEMPT_RT: _irqsave becomes _bh (BH disable) */
```

---

## 18. NMI: Non-Maskable Interrupts

### 18.1 NMI Sources

The NMI (vector 2) cannot be masked by software (IF bit irrelevant). Sources:

- **Hardware NMI pin**: Memory ECC errors, bus parity errors, PCI SERR#
- **Watchdog NMI**: Via performance counter overflow (`perf_event` NMI watchdog, detects soft lockup)
- **Machine Check Exception (MCE)**: Hardware error reporting (vector 18, similar constraints)
- **IOCK / RCIN**: Legacy PC bus errors
- **IPI NMI**: Sent via ICR with NMI delivery mode (kernel uses for crash dumps, KDB)

### 18.2 NMI Handler Constraints

NMI handlers are the most constrained context in the kernel:

- Cannot be interrupted (no nested NMIs on x86 until `IRET`)
- Cannot use locks that might be held by interrupted code
- Cannot use `printk` (may take lock held by interrupted code)
- Must be reentrant on systems with NMI windows (paranoid NMI handling)
- Stack: uses IST1 (dedicated NMI stack)

### 18.3 NMI Registration

```c
/* Register NMI handler */
int register_nmi_handler(unsigned int type, nmi_handler_t handler,
                         unsigned long flags, const char *name);

void unregister_nmi_handler(unsigned int type, const char *name);

/* Types */
#define NMI_LOCAL     0x00000001  /* local APIC NMI (LVT NMI) */
#define NMI_UNKNOWN   0x00000002  /* unknown source */
#define NMI_SERR      0x00000004  /* PCI SERR# */
#define NMI_IO_CHECK  0x00000008  /* I/O check */

/* Handler return values */
#define NMI_DONE    0  /* handler did not handle */
#define NMI_HANDLED 1  /* handler handled */
```

### 18.4 NMI Watchdog

```bash
# Enable NMI watchdog (detects hard lockups: CPU stuck in kernel for >10s)
echo 1 > /proc/sys/kernel/nmi_watchdog

# Check watchdog configuration
cat /proc/sys/kernel/watchdog_thresh   # default 10 seconds
cat /proc/sys/kernel/hardlockup_panic  # 1 = panic on hard lockup
cat /proc/sys/kernel/softlockup_panic  # 1 = panic on soft lockup

# perf-based NMI watchdog uses CPU performance counter
# LAPIC counts PMU overflow → NMI → checks if CPU moved since last check
```

---

## 19. Inter-Processor Interrupts (IPI)

### 19.1 IPI Mechanism

IPIs are sent via the Local APIC ICR (Interrupt Command Register). The sending CPU writes the destination APIC ID + vector/delivery mode to ICR.

```c
/* Send IPI to specific CPU (x86) */
void apic->send_IPI(int cpu, int vector);
void apic->send_IPI_mask(const struct cpumask *mask, int vector);
void apic->send_IPI_allbutself(int vector);
void apic->send_IPI_all(int vector);

/* Linux-defined IPI vectors */
#define RESCHEDULE_VECTOR           0xfc  /* TIF_NEED_RESCHED */
#define CALL_FUNCTION_VECTOR        0xfb  /* smp_call_function */
#define CALL_FUNCTION_SINGLE_VECTOR 0xfa  /* smp_call_function_single */
#define REBOOT_VECTOR               0xf8  /* system reboot */
#define IRQ_MOVE_CLEANUP_VECTOR     0xf7  /* IRQ migration cleanup */
```

### 19.2 TLB Shootdown

TLB shootdown is the most performance-critical IPI use case. When one CPU unmaps a page, all other CPUs sharing that mapping must invalidate their TLB entries.

```c
/* Flush TLB on all CPUs (kernel) */
flush_tlb_all();              /* via IPI to all CPUs */
flush_tlb_mm(mm);             /* for a specific mm, only CPUs running it */
flush_tlb_page(vma, addr);    /* for a single page */
flush_tlb_range(vma, start, end);

/* High-performance path: lazy TLB (CPU not running mm can defer flush) */
/* ptep_clear_flush() returns old PTE, schedules shootdown only if needed */
```

**TLB shootdown overhead** is a major scalability concern at high CPU counts. KPTI (Kernel Page Table Isolation, for Meltdown mitigation) made this significantly worse by requiring additional TLB flushes on every kernel/user transition.

### 19.3 smp_call_function

```c
/* Run function on all other CPUs */
void smp_call_function(smp_call_func_t func, void *info, int wait);

/* Run on specific CPU */
int smp_call_function_single(int cpu, smp_call_func_t func,
                             void *info, int wait);

/* Run on CPU mask */
void smp_call_function_many(const struct cpumask *mask,
                            smp_call_func_t func, void *info, int wait);

/* Async version (don't wait for completion) */
void smp_call_function_single_async(int cpu, struct call_single_data *csd);
```

---

## 20. Virtual Interrupts

### 20.1 KVM Interrupt Injection

KVM injects virtual interrupts into guest VMs without requiring actual hardware. The mechanism differs by guest mode:

**For x86 guests:**

```c
/* KVM: inject interrupt via VMCS (VT-x) */
struct kvm_lapic *apic = vcpu->arch.apic;

/* Method 1: Virtual Interrupt Delivery (VID) — hardware-assisted */
/* Set bit in VAPIC IRR, set VM-Entry interrupt info in VMCS */
/* Guest LAPIC reads from VAPIC page (no VM exit for EOI if TPR threshold not hit) */

/* Method 2: Posted Interrupts (PI) */
/* Set bit in Posted Interrupt Descriptor */
/* If guest is running: VMCS pi_desc causes hardware notification delivery */
/* If guest is not running: bit stays pending, delivered on next VM entry */

/* Method 3: Traditional (no hardware assist) */
/* VM exit to KVM, KVM sets interrupt pending, re-enter guest */
```

### 20.2 Virtio Interrupt Model

Virtio devices use **vring** (virtual ring buffer) for I/O. The interrupt model:

- **Guest → Host notification**: `VIRTIO_MMIO_QUEUE_NOTIFY` register write or `ioeventfd`
- **Host → Guest notification**: Virtual interrupt injection or `irqfd`

**irqfd** allows the host kernel to inject interrupts into a guest by writing to a file descriptor:

```c
/* irqfd: file descriptor → virtual interrupt injection */
struct kvm_irqfd {
    __u32 fd;       /* eventfd */
    __u32 gsi;      /* guest interrupt line */
    __u32 flags;    /* KVM_IRQFD_FLAG_DEASSIGN */
    __u32 resamplefd;
    __u8  pad[16];
};
ioctl(vm_fd, KVM_IRQFD, &irqfd);  /* eventfd write triggers guest IRQ */
```

### 20.3 Xen Event Channels

Xen uses **event channels** as its virtual interrupt mechanism:

```c
/* Event channel types */
EVTCHNSTAT_unbound      /* allocated but not connected */
EVTCHNSTAT_interdomain  /* between two domains */
EVTCHNSTAT_pirq         /* physical IRQ mapping */
EVTCHNSTAT_virq         /* virtual IRQ (timer, etc.) */
EVTCHNSTAT_ipi          /* inter-vCPU IPI */

/* Shared info page: contains event channel pending bitmaps */
struct shared_info {
    struct vcpu_info vcpu_info[MAX_VIRT_CPUS];
    unsigned long    evtchn_pending[sizeof(unsigned long) * 8];
    unsigned long    evtchn_mask[sizeof(unsigned long) * 8];
    /* ... */
};

/* Guest checks pending events via XCHG on evtchn_pending */
```

---

## 21. eBPF and Interrupt Observability

### 21.1 Tracing Interrupt Events

```bash
# Available tracepoints
ls /sys/kernel/debug/tracing/events/irq/
# irq_handler_entry  irq_handler_exit
# softirq_entry      softirq_exit      softirq_raise
# tasklet_entry      tasklet_exit

# Trace all IRQ handlers taking >100µs
cat > /sys/kernel/debug/tracing/events/irq/irq_handler_entry/enable
# Use bpftrace or perf instead for production

# Using perf
perf record -e irq:irq_handler_entry,irq:irq_handler_exit -a sleep 5
perf script

# Using trace-cmd
trace-cmd record -e irq:irq_handler_entry -e irq:irq_handler_exit sleep 5
trace-cmd report
```

### 21.2 bpftrace Scripts

```bash
# IRQ handler latency histogram
bpftrace -e '
tracepoint:irq:irq_handler_entry { @start[args->irq] = nsecs; }
tracepoint:irq:irq_handler_exit  {
    $delta = nsecs - @start[args->irq];
    if ($delta > 0) {
        @latency_us = hist($delta / 1000);
        @per_irq[args->irq] = hist($delta / 1000);
        delete(@start[args->irq]);
    }
}'

# Softirq time per CPU
bpftrace -e '
tracepoint:irq:softirq_entry { @start[cpu] = nsecs; }
tracepoint:irq:softirq_exit  {
    @time_us[cpu, args->vec] = sum((nsecs - @start[cpu]) / 1000);
}'

# Top interrupt sources by count
bpftrace -e '
tracepoint:irq:irq_handler_entry { @count[args->name]++; }
interval:s:5 { print(@count); clear(@count); }'
```

---

## 22. Interrupt Coalescing and NAPI

### 22.1 Hardware Interrupt Coalescing

Most NICs support interrupt coalescing (IC): delay raising an interrupt until N packets arrive or a timeout expires. This amortizes per-interrupt overhead across multiple packets.

```bash
# View and set coalescing parameters (ethtool)
ethtool -c eth0           # show current coalescing settings
ethtool -C eth0 \
    rx-usecs 50 \         # max µs before RX interrupt after first packet
    rx-frames 16 \        # max frames before interrupt
    tx-usecs 50 \
    tx-frames 16 \
    adaptive-rx on        # let driver auto-tune RX coalescing
```

### 22.2 NAPI (New API)

NAPI is Linux's hybrid interrupt+polling model for high-speed networking:

```
Normal (low load):
    RX interrupt fires → napi_schedule() → NAPI poll_list
                      ↓
                  napi_poll() via NET_RX_SOFTIRQ
                      ↓
                  process up to budget packets
                      ↓
             if queue empty: re-enable interrupts (napi_complete_done)
             if budget exhausted: reschedule (yield to other softirqs)

Flood (high load):
    First interrupt → NAPI scheduled, interrupts disabled
                     ↓
                 Polling loop: process packets in bulk
                     ↓
              Interrupts stay disabled → no interrupt overhead
              Timer-based wakeup if queue drains
```

```c
/* NAPI structure */
struct napi_struct {
    struct list_head poll_list;    /* per-CPU softirq list */
    unsigned long    state;        /* NAPIF_STATE_* flags */
    int              weight;       /* max packets per poll */
    int (*poll)(struct napi_struct *, int);  /* poll function */
    /* ... */
};

/* Driver usage */
netif_napi_add(dev, &priv->napi, my_poll, NAPI_POLL_WEIGHT);

/* In interrupt handler: schedule NAPI and disable IRQ */
irqreturn_t my_irq_handler(int irq, void *dev) {
    disable_irq_nosync(irq);   /* or mask via chip */
    napi_schedule(&priv->napi);
    return IRQ_HANDLED;
}

/* NAPI poll: called from softirq */
int my_poll(struct napi_struct *napi, int budget) {
    int work_done = 0;
    while (work_done < budget && packet_available()) {
        process_packet();
        work_done++;
    }
    if (work_done < budget) {
        napi_complete_done(napi, work_done);  /* re-enable interrupts */
        enable_irq(priv->irq);
    }
    return work_done;
}
```

---

## 23. Security Threat Model

### 23.1 Threat Actors and Attack Surfaces

```
Attack Surface                  Threat                          Mitigation
─────────────────────────────────────────────────────────────────────────────
DMA from malicious device      MSI injection (fake interrupts)  Interrupt Remapping (VT-d IR)
                               DMA to arbitrary kernel memory   IOMMU + DMA API
                               MSI address spoofing             VT-d posted interrupts

Userspace process              Trigger interrupt storms         Rate limiting, rlimit
                               Exploit handler race conditions  IRQF_ONESHOT, proper locking
                               INT n injection                  SMEP/SMAP, DPL=0 in IDT

Kernel driver bug              Double-free in irqaction chain   KASAN, lockdep, slab randomization
                               Handler UAF after free_irq       synchronize_irq before free
                               Stack overflow in handler        IST stacks, KASAN stack

Hypervisor/VMM                 Interrupt injection into guest   VT-x interrupt filtering
                               Spurious interrupt flooding      KVM rate limiting
                               Shared interrupt covert channel  Interrupt isolation per guest

NMI                            NMI handler locking             rcu_nmi_enter, raw_spinlocks only
                               NMI storm (hardware fault loop)  NMI watchdog timeout + panic

Side channels                  IRQ timing covert channel        Interrupt isolation, RT scheduling
(Spectre/Meltdown)             Interrupt-based cache attacks    KPTI, retpoline, IBRS
                               NMI during Spectre gadget        LFENCE barriers
```

### 23.2 Interrupt Handler Security Rules

```c
/* 1. NEVER trust data from interrupt frame without validation */
irqreturn_t handler(int irq, void *dev_id) {
    struct my_dev *dev = dev_id;
    /* Validate dev_id before use — could be NULL if free_irq raced */
    if (unlikely(!dev))
        return IRQ_NONE;
    /* Validate device state */
    status = readl(dev->base + STATUS_REG);
    if (!(status & MY_IRQ_BITS))
        return IRQ_NONE;  /* not our interrupt (shared IRQ) */
    /* ...handle... */
}

/* 2. Use synchronize_irq before freeing resources */
void cleanup(struct my_dev *dev) {
    free_irq(dev->irq, dev);  /* waits for handler to complete */
    synchronize_irq(dev->irq); /* extra safety barrier */
    kfree(dev);  /* now safe */
}

/* 3. IRQF_SHARED requires unique dev_id */
request_irq(irq, handler, IRQF_SHARED, "dev", &my_unique_struct);

/* 4. Avoid sleeping locks in handler */
/* Use spinlock, not mutex */
spin_lock(&dev->lock);  /* OK in hardirq */
/* mutex_lock(&dev->mutex);  ← ILLEGAL in hardirq */

/* 5. Memory barriers for shared data */
/* Handler writes, process context reads: */
smp_store_release(&dev->flag, 1);   /* in handler */
val = smp_load_acquire(&dev->flag); /* in process context */
```

### 23.3 Interrupt Remapping and IOMMU

```bash
# Verify interrupt remapping is active
dmesg | grep -i "interrupt remapping"
# [    0.476543] DMAR-IR: Enabled IRQ remapping in x2apic mode

# Check IOMMU groups (each group = isolation boundary)
ls /sys/kernel/iommu_groups/
for group in /sys/kernel/iommu_groups/*/; do
    echo "Group $(basename $group):"
    ls $group/devices/
done

# Ensure devices are in IOMMU domain
cat /sys/bus/pci/devices/0000:01:00.0/iommu_group/type
# DMAr or identity or unmanaged

# vfio-pci: securely pass device to VM with interrupt remapping
echo vfio-pci > /sys/bus/pci/devices/0000:01:00.0/driver_override
echo 0000:01:00.0 > /sys/bus/pci/drivers_probe
```

### 23.4 Hardening Configuration

```
Kernel configs for interrupt security:
  CONFIG_IRQ_DOMAIN_DEBUG          = n (production)
  CONFIG_GENERIC_IRQ_DEBUGFS       = n (production)
  CONFIG_IRQ_FORCED_THREADING      = y (PREEMPT_RT)
  CONFIG_X86_MCE                   = y (machine check detection)
  CONFIG_NMI_WATCHDOG              = y
  CONFIG_HARDLOCKUP_DETECTOR       = y
  CONFIG_SOFTLOCKUP_DETECTOR       = y
  CONFIG_DETECT_HUNG_TASK          = y
  CONFIG_INTEL_IOMMU               = y
  CONFIG_INTEL_IOMMU_DEFAULT_ON    = y
  CONFIG_IRQ_REMAP                 = y  ← interrupt remapping
  CONFIG_RANDOMIZE_BASE            = y  (KASLR)
  CONFIG_SHADOW_CALL_STACK         = y  (arm64)
  CONFIG_CFI_CLANG                 = y  (control flow integrity)
```

---

## 24. C Kernel Module Implementations

### 24.1 Complete IRQ Handler Module

```c
// irq_demo.c — Complete interrupt handler kernel module
// Build: make -C /lib/modules/$(uname -r)/build M=$PWD modules
// Test:  insmod irq_demo.ko irq=<IRQ_NUMBER>
// Clean: rmmod irq_demo

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/interrupt.h>
#include <linux/irq.h>
#include <linux/ktime.h>
#include <linux/percpu.h>
#include <linux/seq_file.h>
#include <linux/proc_fs.h>
#include <linux/slab.h>
#include <linux/workqueue.h>
#include <linux/spinlock.h>
#include <linux/atomic.h>
#include <linux/cpumask.h>
#include <linux/delay.h>

#define MODULE_NAME "irq_demo"
#define MAX_LATENCY_BUCKETS 64

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Security Systems Engineer");
MODULE_DESCRIPTION("IRQ handler demonstration with latency tracking");

/* Module parameters */
static int irq_num = -1;
module_param(irq_num, int, 0444);
MODULE_PARM_DESC(irq_num, "IRQ number to hook");

static bool threaded = true;
module_param(threaded, bool, 0444);
MODULE_PARM_DESC(threaded, "Use threaded IRQ (default: true)");

/* Per-CPU statistics */
struct irq_cpu_stats {
    unsigned long long total_count;
    unsigned long long spurious_count;
    ktime_t            last_time;
    ktime_t            min_interval_ns;
    ktime_t            max_interval_ns;
    u64                latency_hist[MAX_LATENCY_BUCKETS]; /* log2 histogram */
} ____cacheline_aligned_in_smp;

static DEFINE_PER_CPU(struct irq_cpu_stats, irq_stats);

/* Global state */
static atomic64_t total_irq_count = ATOMIC64_INIT(0);
static DEFINE_SPINLOCK(state_lock);
static bool irq_registered = false;
static struct workqueue_struct *irq_wq;
static struct work_struct irq_work;
static struct proc_dir_entry *proc_entry;

/* Work item: process data in process context */
struct irq_work_data {
    ktime_t timestamp;
    int     cpu;
};

static void irq_work_handler(struct work_struct *work)
{
    struct irq_work_data *data;
    unsigned long flags;

    /* This runs in process context — can sleep, allocate, etc. */
    data = container_of(work, struct irq_work_data, work);  /* if embedded */

    /* Simulate workqueue processing */
    spin_lock_irqsave(&state_lock, flags);
    /* Process data from IRQ */
    spin_unlock_irqrestore(&state_lock, flags);

    /* In real code: might_sleep() here is safe */
}

/* Top-half: minimal, fast */
static irqreturn_t irq_top_half(int irq, void *dev_id)
{
    struct irq_cpu_stats *stats;
    ktime_t now, interval;
    int bucket;

    /* Verify this is our interrupt */
    if (unlikely(irq != irq_num))
        return IRQ_NONE;

    now = ktime_get();
    stats = this_cpu_ptr(&irq_stats);

    /* Update per-CPU statistics (no locks needed — per-CPU) */
    if (stats->total_count > 0) {
        interval = ktime_sub(now, stats->last_time);
        if (interval < stats->min_interval_ns)
            stats->min_interval_ns = interval;
        if (interval > stats->max_interval_ns)
            stats->max_interval_ns = interval;

        /* Log2 histogram of intervals */
        bucket = min_t(int, ilog2(max_t(u64, ktime_to_ns(interval), 1)),
                       MAX_LATENCY_BUCKETS - 1);
        stats->latency_hist[bucket]++;
    }

    stats->last_time = now;
    stats->total_count++;

    /* Global count */
    atomic64_inc(&total_irq_count);

    if (threaded)
        return IRQ_WAKE_THREAD;  /* defer to thread */

    /* Non-threaded: schedule workqueue for deferred processing */
    queue_work(irq_wq, &irq_work);
    return IRQ_HANDLED;
}

/* Bottom-half: threaded handler (runs in process context) */
static irqreturn_t irq_thread_fn(int irq, void *dev_id)
{
    /* Safe to sleep here */
    /* In real driver: process DMA buffer, post skb to network stack, etc. */

    /* Schedule workqueue for even more deferred processing */
    queue_work(irq_wq, &irq_work);

    return IRQ_HANDLED;
}

/* /proc/irq_demo/stats */
static int irq_stats_show(struct seq_file *m, void *v)
{
    int cpu;
    unsigned long long grand_total = 0;

    seq_printf(m, "IRQ %d Statistics\n", irq_num);
    seq_printf(m, "=================\n");
    seq_printf(m, "Total:  %lld\n", atomic64_read(&total_irq_count));
    seq_printf(m, "\nPer-CPU breakdown:\n");

    for_each_online_cpu(cpu) {
        struct irq_cpu_stats *stats = per_cpu_ptr(&irq_stats, cpu);
        if (stats->total_count == 0)
            continue;
        seq_printf(m, "  CPU%d: count=%llu spurious=%llu "
                      "min_interval=%lldns max_interval=%lldns\n",
                   cpu, stats->total_count, stats->spurious_count,
                   ktime_to_ns(stats->min_interval_ns),
                   ktime_to_ns(stats->max_interval_ns));
        grand_total += stats->total_count;
    }

    seq_printf(m, "\nLatency Histogram (interval between interrupts):\n");
    /* Aggregate across CPUs */
    for_each_online_cpu(cpu) {
        struct irq_cpu_stats *stats = per_cpu_ptr(&irq_stats, cpu);
        for (int b = 0; b < MAX_LATENCY_BUCKETS; b++) {
            if (stats->latency_hist[b] > 0)
                seq_printf(m, "  [2^%2d ns]: %llu\n", b,
                           stats->latency_hist[b]);
        }
    }
    return 0;
}

static int irq_stats_open(struct inode *inode, struct file *file)
{
    return single_open(file, irq_stats_show, NULL);
}

static const struct proc_ops irq_stats_fops = {
    .proc_open    = irq_stats_open,
    .proc_read    = seq_read,
    .proc_lseek   = seq_lseek,
    .proc_release = single_release,
};

/* Module init */
static int __init irq_demo_init(void)
{
    int ret;
    int cpu;
    unsigned long irqflags;
    struct cpumask affinity_mask;

    if (irq_num < 0) {
        pr_err(MODULE_NAME ": irq parameter required\n");
        return -EINVAL;
    }

    pr_info(MODULE_NAME ": initializing for IRQ %d (threaded=%s)\n",
            irq_num, threaded ? "yes" : "no");

    /* Initialize per-CPU stats */
    for_each_possible_cpu(cpu) {
        struct irq_cpu_stats *stats = per_cpu_ptr(&irq_stats, cpu);
        memset(stats, 0, sizeof(*stats));
        stats->min_interval_ns = KTIME_MAX;
        stats->max_interval_ns = 0;
    }

    /* Create workqueue */
    irq_wq = alloc_workqueue("irq_demo_wq",
                             WQ_HIGHPRI | WQ_MEM_RECLAIM | WQ_UNBOUND, 0);
    if (!irq_wq) {
        pr_err(MODULE_NAME ": failed to create workqueue\n");
        return -ENOMEM;
    }
    INIT_WORK(&irq_work, irq_work_handler);

    /* Register IRQ */
    irqflags = IRQF_SHARED;
    if (threaded)
        irqflags |= IRQF_ONESHOT;

    if (threaded) {
        ret = request_threaded_irq(irq_num,
                                   irq_top_half,
                                   irq_thread_fn,
                                   irqflags,
                                   MODULE_NAME,
                                   &irq_num /* unique dev_id */);
    } else {
        ret = request_irq(irq_num,
                          irq_top_half,
                          irqflags,
                          MODULE_NAME,
                          &irq_num);
    }

    if (ret) {
        pr_err(MODULE_NAME ": request_irq(%d) failed: %d\n", irq_num, ret);
        destroy_workqueue(irq_wq);
        return ret;
    }
    irq_registered = true;

    /* Set NUMA-aware affinity */
    cpumask_copy(&affinity_mask, cpu_online_mask);
    /* Prefer NUMA node 0 CPUs */
    if (!cpumask_empty(cpumask_of_node(0)))
        cpumask_and(&affinity_mask, &affinity_mask, cpumask_of_node(0));
    irq_set_affinity(irq_num, &affinity_mask);

    /* Create proc entry */
    proc_mkdir(MODULE_NAME, NULL);
    proc_entry = proc_create(MODULE_NAME "/stats", 0444, NULL, &irq_stats_fops);
    if (!proc_entry)
        pr_warn(MODULE_NAME ": failed to create proc entry\n");

    pr_info(MODULE_NAME ": registered on IRQ %d\n", irq_num);
    return 0;
}

/* Module exit */
static void __exit irq_demo_exit(void)
{
    if (proc_entry) {
        remove_proc_entry(MODULE_NAME "/stats", NULL);
        remove_proc_entry(MODULE_NAME, NULL);
    }

    if (irq_registered) {
        free_irq(irq_num, &irq_num);
        synchronize_irq(irq_num);
    }

    if (irq_wq) {
        flush_workqueue(irq_wq);
        destroy_workqueue(irq_wq);
    }

    pr_info(MODULE_NAME ": unloaded. total IRQs handled: %lld\n",
            atomic64_read(&total_irq_count));
}

module_init(irq_demo_init);
module_exit(irq_demo_exit);
```

### 24.2 Makefile

```makefile
# Makefile for irq_demo kernel module
obj-m := irq_demo.o

KDIR  := /lib/modules/$(shell uname -r)/build
PWD   := $(shell pwd)
EXTRA_CFLAGS := -Wall -Wextra -Werror

all:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean

install:
	$(MAKE) -C $(KDIR) M=$(PWD) modules_install
	depmod -a

.PHONY: all clean install
```

### 24.3 Tasklet Example

```c
// tasklet_demo.c — Tasklet with work deferral pattern
#include <linux/module.h>
#include <linux/interrupt.h>
#include <linux/atomic.h>

MODULE_LICENSE("GPL");

static atomic_t tasklet_run_count = ATOMIC_INIT(0);
static atomic_t tasklet_sched_count = ATOMIC_INIT(0);

/* Modern tasklet callback */
static void my_tasklet_callback(struct tasklet_struct *t)
{
    atomic_inc(&tasklet_run_count);
    /* Non-blocking work only */
    pr_debug("tasklet running on CPU%d (run #%d)\n",
             smp_processor_id(), atomic_read(&tasklet_run_count));
}

DECLARE_TASKLET(my_tasklet, my_tasklet_callback);

/* Simulate trigger from IRQ context */
static irqreturn_t fake_irq_handler(int irq, void *dev_id)
{
    atomic_inc(&tasklet_sched_count);
    tasklet_schedule(&my_tasklet);  /* safe from hardirq context */
    return IRQ_HANDLED;
}

static int __init tasklet_demo_init(void)
{
    /* In real use, this would be request_irq() */
    pr_info("tasklet_demo: loaded\n");
    return 0;
}

static void __exit tasklet_demo_exit(void)
{
    tasklet_kill(&my_tasklet);  /* waits for running tasklet, prevents rescheduling */
    pr_info("tasklet_demo: scheduled=%d ran=%d\n",
            atomic_read(&tasklet_sched_count),
            atomic_read(&tasklet_run_count));
}

module_init(tasklet_demo_init);
module_exit(tasklet_demo_exit);
```

### 24.4 Softirq Registration (in-kernel only, not modules)

```c
/* Register a softirq (built-in kernel code only, not loadable modules) */
void open_softirq(int nr, void (*action)(struct softirq_action *))
{
    softirq_vec[nr].action = action;
}

/* Example: NET_RX_SOFTIRQ registration in net/core/dev.c */
open_softirq(NET_RX_SOFTIRQ, net_rx_action);
open_softirq(NET_TX_SOFTIRQ, net_tx_action);

/* NET_RX_SOFTIRQ action (simplified) */
static __latent_entropy void net_rx_action(struct softirq_action *h)
{
    struct softnet_data *sd = this_cpu_ptr(&softnet_data);
    unsigned long time_limit = jiffies + usecs_to_jiffies(netdev_budget_usecs);
    int budget = netdev_budget;  /* default 300 packets */
    LIST_HEAD(list);
    LIST_HEAD(repoll);

    local_irq_disable();
    list_splice_init(&sd->poll_list, &list);
    local_irq_enable();

    for (;;) {
        struct napi_struct *n;
        if (list_empty(&list)) break;
        n = list_first_entry(&list, struct napi_struct, poll_list);
        budget -= napi_poll(n, &repoll);
        if (budget <= 0 || time_after_eq(jiffies, time_limit)) {
            sd->time_squeeze++;
            break;
        }
    }
    /* ... re-add to repoll list if needed ... */
}
```

### 24.5 IRQ Affinity Notification

```c
/* irq_affinity_notify: callback when affinity changes */
struct my_dev_affinity {
    struct irq_affinity_notify notify;
    struct my_device *dev;
};

static void my_affinity_notify(struct irq_affinity_notify *notify,
                                const cpumask_t *mask)
{
    struct my_dev_affinity *aff = container_of(notify,
                                               struct my_dev_affinity, notify);
    /* Update device-side affinity tracking */
    pr_info("IRQ affinity changed to: %*pbl\n", cpumask_pr_args(mask));
    /* e.g., re-configure NIC queue mapping */
}

static void my_affinity_release(struct kref *ref)
{
    struct my_dev_affinity *aff = container_of(ref,
                                               struct irq_affinity_notify, kref);
    kfree(aff);
}

/* Register */
struct my_dev_affinity *aff = kzalloc(sizeof(*aff), GFP_KERNEL);
aff->notify.notify  = my_affinity_notify;
aff->notify.release = my_affinity_release;
irq_set_affinity_notifier(irq_num, &aff->notify);
```

---

## 25. Go Implementations

### 25.1 Go: IRQ Statistics Reader and Monitor

```go
// irq_monitor.go — Production IRQ monitoring tool
// Build: go build -o irq_monitor ./irq_monitor.go
// Run:   sudo ./irq_monitor --interval=1s --top=20 --threshold-us=100

package main

import (
	"bufio"
	"flag"
	"fmt"
	"log"
	"os"
	"os/signal"
	"path/filepath"
	"runtime"
	"sort"
	"strconv"
	"strings"
	"syscall"
	"time"
)

type IRQStat struct {
	IRQ      string
	Counts   []uint64 // per-CPU counts
	Total    uint64
	Name     string
	LastRate float64  // interrupts/sec
	PrevTotal uint64
}

type IRQAffinityInfo struct {
	IRQ         string
	AffinityHex string
	AffinityList string
	NodeAffinity map[int]bool
}

func readProcInterrupts() (map[string]*IRQStat, int, error) {
	f, err := os.Open("/proc/interrupts")
	if err != nil {
		return nil, 0, fmt.Errorf("open /proc/interrupts: %w", err)
	}
	defer f.Close()

	stats := make(map[string]*IRQStat)
	numCPUs := runtime.NumCPU()
	lineNum := 0

	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := scanner.Text()
		lineNum++
		if lineNum == 1 {
			// Header line: "           CPU0       CPU1  ..."
			// Count actual CPU columns
			fields := strings.Fields(line)
			numCPUs = len(fields)
			continue
		}

		// Format: "  24:    1234    5678   PCI-MSI 524288-edge   xhci_hcd"
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}

		colonIdx := strings.Index(line, ":")
		if colonIdx < 0 {
			continue
		}

		irqKey := strings.TrimSpace(line[:colonIdx])
		rest := strings.TrimSpace(line[colonIdx+1:])
		fields := strings.Fields(rest)
		if len(fields) < numCPUs {
			continue
		}

		stat := &IRQStat{
			IRQ:    irqKey,
			Counts: make([]uint64, numCPUs),
		}

		for i := 0; i < numCPUs; i++ {
			n, _ := strconv.ParseUint(fields[i], 10, 64)
			stat.Counts[i] = n
			stat.Total += n
		}

		// Name is everything after the CPU counts + type
		if len(fields) > numCPUs+1 {
			stat.Name = strings.Join(fields[numCPUs+1:], " ")
		} else if len(fields) > numCPUs {
			stat.Name = fields[numCPUs]
		}

		stats[irqKey] = stat
	}

	return stats, numCPUs, scanner.Err()
}

func readIRQAffinity(irq string) (string, string, error) {
	listPath := filepath.Join("/proc/irq", irq, "smp_affinity_list")
	hexPath  := filepath.Join("/proc/irq", irq, "smp_affinity")

	readFile := func(path string) (string, error) {
		data, err := os.ReadFile(path)
		if err != nil {
			return "", err
		}
		return strings.TrimSpace(string(data)), nil
	}

	list, err1 := readFile(listPath)
	hex,  err2  := readFile(hexPath)

	if err1 != nil || err2 != nil {
		return "", "", fmt.Errorf("affinity unavailable")
	}
	return hex, list, nil
}

func readIRQNode(irq string) (int, error) {
	data, err := os.ReadFile(filepath.Join("/proc/irq", irq, "node"))
	if err != nil {
		return -1, err
	}
	node, err := strconv.Atoi(strings.TrimSpace(string(data)))
	return node, err
}

type IRQRateEntry struct {
	IRQ  string
	Rate float64
	Name string
	Node int
	AffinityList string
}

func monitor(interval time.Duration, topN int, thresholdUs float64) {
	prev := make(map[string]*IRQStat)
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM)

	fmt.Printf("Monitoring IRQs (interval=%v, top=%d)\n", interval, topN)
	fmt.Printf("%-8s %-10s %-20s %-12s %s\n",
		"IRQ", "Rate/s", "Name", "Affinity", "NUMA Node")
	fmt.Println(strings.Repeat("-", 80))

	for {
		select {
		case <-sigs:
			fmt.Println("\nStopped.")
			return

		case t := <-ticker.C:
			current, numCPUs, err := readProcInterrupts()
			if err != nil {
				log.Printf("error reading /proc/interrupts: %v", err)
				continue
			}
			_ = numCPUs

			var rates []IRQRateEntry
			for key, stat := range current {
				rate := 0.0
				if pstat, ok := prev[key]; ok {
					delta := float64(stat.Total - pstat.Total)
					rate = delta / interval.Seconds()
				}
				if rate < 1.0 {
					continue
				}

				hexAff, listAff, _ := readIRQAffinity(key)
				_ = hexAff
				node, _ := readIRQNode(key)

				rates = append(rates, IRQRateEntry{
					IRQ:          key,
					Rate:         rate,
					Name:         stat.Name,
					Node:         node,
					AffinityList: listAff,
				})
			}

			// Sort by rate descending
			sort.Slice(rates, func(i, j int) bool {
				return rates[i].Rate > rates[j].Rate
			})

			fmt.Printf("\n=== %s ===\n", t.Format("15:04:05"))
			for i, e := range rates {
				if i >= topN {
					break
				}
				nodeStr := "N/A"
				if e.Node >= 0 {
					nodeStr = strconv.Itoa(e.Node)
				}
				fmt.Printf("%-8s %10.0f  %-20s %-12s node=%s\n",
					e.IRQ, e.Rate,
					truncate(e.Name, 20),
					truncate(e.AffinityList, 12),
					nodeStr)
			}

			prev = current
		}
	}
}

func truncate(s string, n int) string {
	if len(s) <= n {
		return s
	}
	return s[:n-3] + "..."
}

func setAffinity(irq string, cpuList string) error {
	// Requires root
	path := filepath.Join("/proc/irq", irq, "smp_affinity_list")
	return os.WriteFile(path, []byte(cpuList+"\n"), 0644)
}

func main() {
	intervalFlag := flag.Duration("interval", 2*time.Second, "polling interval")
	topFlag      := flag.Int("top", 20, "show top N IRQs by rate")
	threshFlag   := flag.Float64("threshold-us", 0, "latency threshold in µs (future use)")
	affinityIRQ  := flag.String("set-affinity-irq", "", "IRQ number to set affinity for")
	affinityCPUs := flag.String("set-affinity-cpus", "", "CPU list (e.g. '0-3,8')")
	flag.Parse()

	if *affinityIRQ != "" && *affinityCPUs != "" {
		if err := setAffinity(*affinityIRQ, *affinityCPUs); err != nil {
			log.Fatalf("set affinity: %v", err)
		}
		fmt.Printf("Set IRQ %s affinity to CPUs %s\n", *affinityIRQ, *affinityCPUs)
		return
	}

	monitor(*intervalFlag, *topFlag, *threshFlag)
}
```

### 25.2 Go: eBPF-based IRQ Latency Tracer

```go
// irq_latency_ebpf.go — IRQ latency tracing via eBPF
// Requires: github.com/cilium/ebpf
// Build: go build -tags linux ./irq_latency_ebpf.go
// Run:   sudo ./irq_latency_ebpf

package main

import (
	"bytes"
	_ "embed"
	"encoding/binary"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"
	"unsafe"

	"github.com/cilium/ebpf"
	"github.com/cilium/ebpf/link"
	"github.com/cilium/ebpf/perf"
	"github.com/cilium/ebpf/rlimit"
)

// IRQ event from eBPF
type IRQEvent struct {
	IRQ       uint32
	CPU       uint32
	DurationNs uint64
	Comm      [16]byte
}

// eBPF program source (compiled separately with clang or go generate)
// In production: use go:generate to compile .c → .o → embed
const ebpfSource = `
// irq_latency.c — compile with: clang -O2 -target bpf -c irq_latency.c -o irq_latency.o

#include <linux/bpf.h>
#include <linux/tracepoint.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

struct irq_event {
    __u32 irq;
    __u32 cpu;
    __u64 duration_ns;
    char  comm[16];
};

// Map: cpu → entry timestamp
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __type(key, __u32);
    __type(value, __u64);
    __uint(max_entries, 1);
} entry_ts SEC(".maps");

// Ring buffer for events
struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);
} events SEC(".maps");

// Histogram map: duration bucket → count
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __type(key, __u32);
    __type(value, __u64);
    __uint(max_entries, 64);  // 64 log2 buckets
} latency_hist SEC(".maps");

SEC("tp/irq/irq_handler_entry")
int irq_entry(struct trace_event_raw_irq_handler_entry *ctx) {
    __u32 key = 0;
    __u64 ts = bpf_ktime_get_ns();
    bpf_map_update_elem(&entry_ts, &key, &ts, BPF_ANY);
    return 0;
}

SEC("tp/irq/irq_handler_exit")
int irq_exit(struct trace_event_raw_irq_handler_exit *ctx) {
    __u32 key = 0;
    __u64 *start = bpf_map_lookup_elem(&entry_ts, &key);
    if (!start) return 0;

    __u64 duration = bpf_ktime_get_ns() - *start;

    // Update histogram
    __u32 bucket = 0;
    __u64 tmp = duration;
    while (tmp > 1 && bucket < 63) { tmp >>= 1; bucket++; }
    __u64 *count = bpf_map_lookup_elem(&latency_hist, &bucket);
    if (count) __sync_fetch_and_add(count, 1);

    // Only emit event if duration > 10µs
    if (duration < 10000) return 0;

    struct irq_event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e) return 0;

    e->irq = ctx->irq;
    e->cpu = bpf_get_smp_processor_id();
    e->duration_ns = duration;
    bpf_get_current_comm(&e->comm, sizeof(e->comm));

    bpf_ringbuf_submit(e, 0);
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
`

func runeBPFLatencyTracer() error {
	// Remove memory lock limit
	if err := rlimit.RemoveMemlock(); err != nil {
		return fmt.Errorf("remove memlock: %w", err)
	}

	// Load pre-compiled eBPF object (in production, embed with //go:embed)
	spec, err := ebpf.LoadCollectionSpec("irq_latency.o")
	if err != nil {
		return fmt.Errorf("load eBPF spec: %w (compile irq_latency.c first)", err)
	}

	coll, err := ebpf.NewCollection(spec)
	if err != nil {
		return fmt.Errorf("new collection: %w", err)
	}
	defer coll.Close()

	// Attach tracepoints

    ent entryLink, err := link.Tracepoint("irq", "irq_handler_entry",
		coll.Programs["irq_entry"], nil)
	if err != nil {
		return fmt.Errorf("attach irq_handler_entry: %w", err)
	}
	defer entryLink.Close()

	exitLink, err := link.Tracepoint("irq", "irq_handler_exit",
		coll.Programs["irq_exit"], nil)
	if err != nil {
		return fmt.Errorf("attach irq_handler_exit: %w", err)
	}
	defer exitLink.Close()

	// Read ring buffer events
	rd, err := perf.NewReader(coll.Maps["events"], os.Getpagesize())
	if err != nil {
		return fmt.Errorf("ringbuf reader: %w", err)
	}
	defer rd.Close()

	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM)

	fmt.Println("Tracing IRQ handlers > 10µs... Ctrl-C to stop")
	fmt.Printf("%-8s %-6s %-16s %s\n", "IRQ", "CPU", "Duration", "Comm")

	go func() {
		for {
			record, err := rd.Read()
			if err != nil {
				return
			}

			var event IRQEvent
			if err := binary.Read(bytes.NewReader(record.RawSample),
				binary.LittleEndian, &event); err != nil {
				continue
			}

			comm := string(bytes.TrimRight(event.Comm[:], "\x00"))
			dur := time.Duration(event.DurationNs)
			fmt.Printf("%-8d %-6d %-16s %v\n",
				event.IRQ, event.CPU, comm, dur)
		}
	}()

	<-sigs
	fmt.Println("\nDumping histogram...")

	// Read latency histogram
	histMap := coll.Maps["latency_hist"]
	fmt.Println("\nLatency Histogram (per-CPU aggregated):")
	for bucket := 0; bucket < 64; bucket++ {
		key := uint32(bucket)
		var values []uint64 = make([]uint64, 0)

		if err := histMap.Lookup(unsafe.Pointer(&key),
			unsafe.Pointer(&values)); err != nil {
			continue
		}
		total := uint64(0)
		for _, v := range values {
			total += v
		}
		if total > 0 {
			lowNs := uint64(1) << bucket
			highNs := lowNs << 1
			bar := strings.Repeat("*", int(min64(total, 50)))
			fmt.Printf("[%8dns - %8dns): %6d %s\n",
				lowNs, highNs, total, bar)
		}
	}
	return nil
}

func min64(a, b uint64) uint64 {
	if a < b {
		return a
	}
	return b
}

func main() {
	if err := runeBPFLatencyTracer(); err != nil {
		log.Fatalf("tracer: %v", err)
	}
}
```

### 25.3 Go: IRQ Affinity Optimizer (NUMA-Aware)

```go
// irq_affinity_optimizer.go — NUMA-aware IRQ affinity optimization
// Build: go build -o irq_opt ./irq_affinity_optimizer.go
// Run:   sudo ./irq_opt --dry-run

package main

import (
	"bufio"
	"flag"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
)

type NUMATopology struct {
	Nodes    map[int][]int   // node → CPU list
	CPUNode  map[int]int     // CPU → node
	NumNodes int
	NumCPUs  int
}

type PCIDeviceInfo struct {
	BDF      string // Bus:Device.Function
	NUMANode int
	IRQs     []int
	Driver   string
	Class    string
}

func readNUMATopology() (*NUMATopology, error) {
	topo := &NUMATopology{
		Nodes:   make(map[int][]int),
		CPUNode: make(map[int]int),
	}

	// Read from /sys/devices/system/node/nodeN/cpulist
	nodePattern := "/sys/devices/system/node/node*"
	nodes, err := filepath.Glob(nodePattern)
	if err != nil || len(nodes) == 0 {
		// Fallback: assume single node
		topo.Nodes[0] = getAllCPUs()
		for _, cpu := range topo.Nodes[0] {
			topo.CPUNode[cpu] = 0
		}
		topo.NumNodes = 1
		return topo, nil
	}

	for _, nodePath := range nodes {
		nodeName := filepath.Base(nodePath)
		nodeID, err := strconv.Atoi(strings.TrimPrefix(nodeName, "node"))
		if err != nil {
			continue
		}

		cpuListData, err := os.ReadFile(filepath.Join(nodePath, "cpulist"))
		if err != nil {
			continue
		}

		cpus := parseCPUList(strings.TrimSpace(string(cpuListData)))
		topo.Nodes[nodeID] = cpus
		for _, cpu := range cpus {
			topo.CPUNode[cpu] = nodeID
		}
		if nodeID+1 > topo.NumNodes {
			topo.NumNodes = nodeID + 1
		}
	}

	for _, cpus := range topo.Nodes {
		topo.NumCPUs += len(cpus)
	}
	return topo, nil
}

func parseCPUList(s string) []int {
	var cpus []int
	for _, part := range strings.Split(s, ",") {
		part = strings.TrimSpace(part)
		if part == "" {
			continue
		}
		if strings.Contains(part, "-") {
			bounds := strings.SplitN(part, "-", 2)
			lo, _ := strconv.Atoi(bounds[0])
			hi, _ := strconv.Atoi(bounds[1])
			for i := lo; i <= hi; i++ {
				cpus = append(cpus, i)
			}
		} else {
			n, _ := strconv.Atoi(part)
			cpus = append(cpus, n)
		}
	}
	sort.Ints(cpus)
	return cpus
}

func getAllCPUs() []int {
	data, err := os.ReadFile("/sys/devices/system/cpu/online")
	if err != nil {
		return []int{0}
	}
	return parseCPUList(strings.TrimSpace(string(data)))
}

func readPCIDeviceNUMANode(bdf string) (int, error) {
	path := fmt.Sprintf("/sys/bus/pci/devices/%s/numa_node", bdf)
	data, err := os.ReadFile(path)
	if err != nil {
		return -1, err
	}
	node, err := strconv.Atoi(strings.TrimSpace(string(data)))
	return node, err
}

func listIRQsForDevice(bdf string) ([]int, error) {
	// Read MSI-X IRQs from /sys/bus/pci/devices/<bdf>/msi_irqs/
	path := fmt.Sprintf("/sys/bus/pci/devices/%s/msi_irqs", bdf)
	entries, err := os.ReadDir(path)
	if err != nil {
		// Fall back to /proc/irq search
		return searchProcIRQForDevice(bdf)
	}

	var irqs []int
	for _, e := range entries {
		irq, err := strconv.Atoi(e.Name())
		if err == nil {
			irqs = append(irqs, irq)
		}
	}
	return irqs, nil
}

func searchProcIRQForDevice(bdf string) ([]int, error) {
	// Simplified: scan /proc/irq/*/
	var irqs []int
	entries, _ := filepath.Glob("/proc/irq/*/")
	for _, entry := range entries {
		// Check if this IRQ belongs to our device via /proc/irq/N/affinity_hint
		// or by reading the interrupt name from /proc/interrupts
		_ = entry
	}
	return irqs, nil
}

type AffinityRecommendation struct {
	IRQ          int
	CurrentAff   string
	RecommendedAff string
	Reason       string
	PCIDevice    string
	NUMANode     int
}

func generateRecommendations(topo *NUMATopology) ([]AffinityRecommendation, error) {
	var recs []AffinityRecommendation

	// Scan PCI devices
	devEntries, err := os.ReadDir("/sys/bus/pci/devices/")
	if err != nil {
		return nil, err
	}

	for _, de := range devEntries {
		bdf := de.Name()
		node, err := readPCIDeviceNUMANode(bdf)
		if err != nil || node < 0 {
			continue
		}

		irqs, err := listIRQsForDevice(bdf)
		if err != nil || len(irqs) == 0 {
			continue
		}

		// Recommended CPUs: those on same NUMA node
		nodeCPUs, ok := topo.Nodes[node]
		if !ok || len(nodeCPUs) == 0 {
			continue
		}

		// Build CPU list string
		recAff := cpuListToString(nodeCPUs)

		for _, irq := range irqs {
			currentAff, _ := readCurrentAffinity(irq)

			recs = append(recs, AffinityRecommendation{
				IRQ:            irq,
				CurrentAff:     currentAff,
				RecommendedAff: recAff,
				Reason:         fmt.Sprintf("Device %s on NUMA node %d", bdf, node),
				PCIDevice:      bdf,
				NUMANode:       node,
			})
		}
	}

	return recs, nil
}

func readCurrentAffinity(irq int) (string, error) {
	data, err := os.ReadFile(fmt.Sprintf("/proc/irq/%d/smp_affinity_list", irq))
	if err != nil {
		return "", err
	}
	return strings.TrimSpace(string(data)), nil
}

func cpuListToString(cpus []int) string {
	if len(cpus) == 0 {
		return ""
	}
	// Build range notation
	var parts []string
	start := cpus[0]
	prev := cpus[0]

	for i := 1; i <= len(cpus); i++ {
		if i < len(cpus) && cpus[i] == prev+1 {
			prev = cpus[i]
			continue
		}
		if start == prev {
			parts = append(parts, strconv.Itoa(start))
		} else {
			parts = append(parts, fmt.Sprintf("%d-%d", start, prev))
		}
		if i < len(cpus) {
			start = cpus[i]
			prev = cpus[i]
		}
	}
	return strings.Join(parts, ",")
}

func applyAffinity(irq int, cpuList string) error {
	path := fmt.Sprintf("/proc/irq/%d/smp_affinity_list", irq)
	return os.WriteFile(path, []byte(cpuList+"\n"), 0644)
}

func main() {
	dryRun := flag.Bool("dry-run", true, "print recommendations without applying")
	verbose := flag.Bool("verbose", false, "show all IRQs including unchanged")
	flag.Parse()

	topo, err := readNUMATopology()
	if err != nil {
		log.Fatalf("read NUMA topology: %v", err)
	}

	fmt.Printf("NUMA Topology: %d nodes, %d CPUs\n", topo.NumNodes, topo.NumCPUs)
	for node, cpus := range topo.Nodes {
		fmt.Printf("  Node %d: CPUs %s\n", node, cpuListToString(cpus))
	}

	recs, err := generateRecommendations(topo)
	if err != nil {
		log.Fatalf("generate recommendations: %v", err)
	}

	changed := 0
	for _, rec := range recs {
		if rec.CurrentAff == rec.RecommendedAff && !*verbose {
			continue
		}
		action := "APPLY"
		if rec.CurrentAff == rec.RecommendedAff {
			action = "OK   "
		}
		fmt.Printf("[%s] IRQ %-6d current=%-12s recommended=%-12s  // %s\n",
			action, rec.IRQ, rec.CurrentAff, rec.RecommendedAff, rec.Reason)

		if !*dryRun && rec.CurrentAff != rec.RecommendedAff {
			if err := applyAffinity(rec.IRQ, rec.RecommendedAff); err != nil {
				log.Printf("  ERROR setting affinity for IRQ %d: %v", rec.IRQ, err)
			} else {
				changed++
			}
		}
	}

	if *dryRun && changed == 0 {
		fmt.Printf("\n[dry-run] Would change %d IRQ affinity settings\n", len(recs))
	} else if !*dryRun {
		fmt.Printf("\nApplied %d affinity changes\n", changed)
	}
}

// readFile helper for scanning
func readLines(path string) ([]string, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	var lines []string
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		lines = append(lines, sc.Text())
	}
	return lines, sc.Err()
}
```

---

## 26. Rust Implementations

### 26.1 Rust: Bare-Metal x86_64 IDT Setup

```rust
// idt_setup.rs — Bare-metal x86_64 IDT configuration
// Crates: x86_64 = "0.15", spin = "0.9"
// This is a #![no_std] example for OS/hypervisor development

#![no_std]
#![feature(abi_x86_interrupt)]

use core::fmt;
use spin::Lazy;
use x86_64::structures::idt::{InterruptDescriptorTable, InterruptStackFrame, PageFaultErrorCode};

/// IDT vector assignments
#[repr(u8)]
#[derive(Debug, Clone, Copy)]
pub enum InterruptIndex {
    // CPU exceptions 0–31 (handled by x86_64 crate defaults)
    
    // Hardware interrupts (remapped to 0x20–0xFF by PIC/APIC)
    Timer       = 0x20,
    Keyboard    = 0x21,
    Cascade     = 0x22,  // PIC cascade (unused)
    Serial2     = 0x23,
    Serial1     = 0x24,
    
    // APIC vectors
    ApicTimer   = 0xEC,
    Spurious    = 0xFF,
    
    // IPI vectors
    TlbShootdown = 0xF0,
    Reschedule   = 0xF1,
}

impl InterruptIndex {
    fn as_u8(self) -> u8 { self as u8 }
    fn as_usize(self) -> usize { usize::from(self.as_u8()) }
}

/// Global IDT instance (lazy initialized, static lifetime)
static IDT: Lazy<InterruptDescriptorTable> = Lazy::new(|| {
    let mut idt = InterruptDescriptorTable::new();

    // CPU exception handlers
    idt.breakpoint.set_handler_fn(breakpoint_handler);
    idt.page_fault.set_handler_fn(page_fault_handler);
    idt.general_protection_fault.set_handler_fn(gpf_handler);
    idt.double_fault
        .set_handler_fn(double_fault_handler)
        // Use IST stack 1 for double fault (safe even if stack overflowed)
        .set_stack_index(DOUBLE_FAULT_IST_INDEX);

    // Machine check exception
    idt.machine_check.set_handler_fn(mce_handler);

    // Hardware interrupt handlers
    idt[InterruptIndex::Timer.as_usize()].set_handler_fn(timer_interrupt_handler);
    idt[InterruptIndex::Keyboard.as_usize()].set_handler_fn(keyboard_interrupt_handler);
    idt[InterruptIndex::ApicTimer.as_usize()].set_handler_fn(apic_timer_handler);
    idt[InterruptIndex::Spurious.as_usize()].set_handler_fn(spurious_interrupt_handler);
    
    // IPI handlers
    idt[InterruptIndex::TlbShootdown.as_usize()].set_handler_fn(tlb_shootdown_handler);
    idt[InterruptIndex::Reschedule.as_usize()].set_handler_fn(reschedule_handler);

    idt
});

/// IST indices (must match TSS configuration)
const DOUBLE_FAULT_IST_INDEX: u16 = 0;

/// Initialize and load the IDT
pub fn init_idt() {
    IDT.load();
}

/// Per-CPU interrupt statistics
#[repr(C)]
pub struct CpuIrqStats {
    pub total_count:    u64,
    pub spurious_count: u64,
    pub timer_count:    u64,
    pub page_faults:    u64,
}

impl CpuIrqStats {
    const fn new() -> Self {
        Self {
            total_count: 0,
            spurious_count: 0,
            timer_count: 0,
            page_faults: 0,
        }
    }
}

// Per-CPU stats (in real OS: use per-CPU storage via FS/GS base)
static mut IRQ_STATS: CpuIrqStats = CpuIrqStats::new();

// ─── Exception Handlers ───────────────────────────────────────────────────────

/// Breakpoint (#BP) — INT3, used by debuggers
extern "x86-interrupt" fn breakpoint_handler(stack_frame: InterruptStackFrame) {
    // In a real OS: notify debugger subsystem, do not panic
    // The "x86-interrupt" ABI automatically handles register save/restore
    // and IRET (via LLVM backend)
    unsafe { IRQ_STATS.total_count += 1; }
}

/// Page fault (#PF)
extern "x86-interrupt" fn page_fault_handler(
    stack_frame: InterruptStackFrame,
    error_code: PageFaultErrorCode,
) {
    use x86_64::registers::control::Cr2;
    
    let fault_addr = Cr2::read().expect("CR2 invalid");
    
    unsafe { IRQ_STATS.page_faults += 1; }

    // Error code bits:
    // P  (bit 0): 0=not-present, 1=protection violation
    // W  (bit 1): 0=read, 1=write
    // U  (bit 2): 0=kernel, 1=user
    // R  (bit 3): reserved bit violation
    // I  (bit 4): 0=data, 1=instruction fetch
    // PK (bit 5): protection key violation
    // SS (bit 6): shadow stack access fault
    
    if error_code.contains(PageFaultErrorCode::CAUSED_BY_WRITE) {
        // Handle copy-on-write, demand paging, etc.
        handle_write_fault(fault_addr, stack_frame);
    } else {
        handle_read_fault(fault_addr, error_code, stack_frame);
    }
}

fn handle_write_fault(
    addr: x86_64::VirtAddr,
    _frame: InterruptStackFrame,
) {
    // In a real OS: check VMA, allocate physical page, update PTE
    // For now: panic (bare-metal demo)
    panic!("Unhandled write page fault at {:?}", addr);
}

fn handle_read_fault(
    addr: x86_64::VirtAddr,
    error_code: PageFaultErrorCode,
    frame: InterruptStackFrame,
) {
    panic!("Read page fault at {:?}: {:?}\nFrame: {:#?}", addr, error_code, frame);
}

/// General Protection Fault (#GP)
extern "x86-interrupt" fn gpf_handler(
    stack_frame: InterruptStackFrame,
    error_code: u64,
) {
    // error_code encodes segment selector index (bits 15:3) if segment-related
    panic!("#GP at {:#x} error={:#x}\n{:#?}", 
           stack_frame.instruction_pointer,
           error_code, 
           stack_frame);
}

/// Double Fault (#DF) — runs on IST stack
extern "x86-interrupt" fn double_fault_handler(
    stack_frame: InterruptStackFrame,
    _error_code: u64, // always 0 for #DF
) -> ! {
    // Cannot recover from double fault — must halt or reset
    panic!("DOUBLE FAULT\n{:#?}", stack_frame);
}

/// Machine Check Exception (#MC)
extern "x86-interrupt" fn mce_handler(stack_frame: InterruptStackFrame) -> ! {
    // Read MCG_STATUS, MCi_STATUS MSRs to get error details
    // In production: log to persistent storage, attempt recovery or halt
    panic!("MACHINE CHECK EXCEPTION\n{:#?}", stack_frame);
}

// ─── Hardware Interrupt Handlers ─────────────────────────────────────────────

/// PIC Timer (IRQ0) — if using legacy 8259 PIC
extern "x86-interrupt" fn timer_interrupt_handler(_stack_frame: InterruptStackFrame) {
    unsafe {
        IRQ_STATS.total_count += 1;
        IRQ_STATS.timer_count += 1;
    }
    
    // Acknowledge to PIC: send EOI to master (port 0x20)
    unsafe {
        x86_64::instructions::port::Port::<u8>::new(0x20).write(0x20);
    }
    
    // Tick the scheduler, update timers, etc.
    tick_scheduler();
}

/// APIC Local Timer
extern "x86-interrupt" fn apic_timer_handler(_stack_frame: InterruptStackFrame) {
    unsafe {
        IRQ_STATS.total_count += 1;
        IRQ_STATS.timer_count += 1;
    }
    
    // Send EOI to local APIC (MMIO write to 0xFEE000B0, or x2APIC MSR)
    send_apic_eoi();
    
    tick_scheduler();
}

/// Keyboard (IRQ1)
extern "x86-interrupt" fn keyboard_interrupt_handler(_stack_frame: InterruptStackFrame) {
    unsafe { IRQ_STATS.total_count += 1; }
    
    // Read scancode from keyboard data port (0x60)
    let scancode: u8 = unsafe {
        x86_64::instructions::port::Port::<u8>::new(0x60).read()
    };
    
    // Process scancode (in real OS: push to keyboard event queue)
    process_scancode(scancode);
    
    // EOI to PIC
    unsafe {
        x86_64::instructions::port::Port::<u8>::new(0x20).write(0x20);
    }
}

/// Spurious interrupt — do NOT send EOI for spurious interrupts!
extern "x86-interrupt" fn spurious_interrupt_handler(_stack_frame: InterruptStackFrame) {
    unsafe {
        IRQ_STATS.total_count += 1;
        IRQ_STATS.spurious_count += 1;
    }
    // No EOI for spurious — the interrupt was not actually asserted
}

// ─── IPI Handlers ────────────────────────────────────────────────────────────

/// TLB shootdown IPI
extern "x86-interrupt" fn tlb_shootdown_handler(_stack_frame: InterruptStackFrame) {
    // Flush TLB as requested by the initiating CPU
    // The initiating CPU will have set up a per-CPU shootdown descriptor
    perform_tlb_flush();
    send_apic_eoi();
}

/// Reschedule IPI — just sets TIF_NEED_RESCHED
extern "x86-interrupt" fn reschedule_handler(_stack_frame: InterruptStackFrame) {
    // Set need-reschedule flag for this CPU
    // The actual scheduling happens on IRQ exit
    set_need_resched();
    send_apic_eoi();
}

// ─── Stubs (to be implemented in real OS) ────────────────────────────────────

fn tick_scheduler() { /* update jiffies, check for expired timers */ }
fn process_scancode(_sc: u8) { /* push to event queue */ }
fn perform_tlb_flush() { 
    // CR3 reload flushes all non-global TLB entries
    unsafe {
        let cr3 = x86_64::registers::control::Cr3::read();
        x86_64::registers::control::Cr3::write(cr3.0, cr3.1);
    }
}
fn set_need_resched() { /* set per-CPU flag */ }
fn send_apic_eoi() {
    // Write 0 to LAPIC EOI register (MMIO: 0xFEE000B0)
    const LAPIC_EOI: *mut u32 = 0xFEE0_00B0 as *mut u32;
    unsafe { LAPIC_EOI.write_volatile(0); }
}
```

### 26.2 Rust: Linux Kernel Module (rust-for-linux)

```rust
// irq_module.rs — Linux kernel module in Rust
// Requires: rust-for-linux (linux kernel with CONFIG_RUST=y)
// Build: make -C /path/to/linux M=$PWD
// See: https://rust-for-linux.com

//! IRQ Demo Kernel Module
//!
//! Demonstrates IRQ registration, threaded IRQs, per-CPU statistics,
//! and workqueue integration using the Rust kernel abstractions.

use kernel::{
    prelude::*,
    irq::{self, IrqData, IrqHandler, Return},
    sync::{Arc, SpinLock},
    workqueue::{self, Work, WorkItem},
    cpumask::CpuMask,
    task::Task,
    time::Ktime,
};
use core::sync::atomic::{AtomicU64, Ordering};

module! {
    type: IrqDemoModule,
    name: "irq_demo_rust",
    author: "Security Systems Engineer",
    description: "IRQ handler demo in Rust",
    license: "GPL",
    params: {
        irq_num: u32 {
            default: 0,
            permissions: 0o444,
            description: "IRQ number to register",
        },
        use_threaded: bool {
            default: true,
            permissions: 0o444,
            description: "Use threaded IRQ",
        },
    },
}

/// Per-CPU IRQ statistics
struct IrqStats {
    total:    AtomicU64,
    spurious: AtomicU64,
    last_ns:  AtomicU64,
}

impl IrqStats {
    const fn new() -> Self {
        Self {
            total:    AtomicU64::new(0),
            spurious: AtomicU64::new(0),
            last_ns:  AtomicU64::new(0),
        }
    }

    fn record_irq(&self) {
        let now = Ktime::ktime_get().to_ns() as u64;
        self.last_ns.store(now, Ordering::Relaxed);
        self.total.fetch_add(1, Ordering::Relaxed);
    }
}

/// Work item for deferred processing
struct IrqWorkItem {
    timestamp: u64,
    cpu: u32,
}

impl WorkItem for IrqWorkItem {
    type Pointer = Arc<IrqWorkItem>;

    fn run(this: Arc<Self>) {
        // Process context: can sleep
        pr_debug!("IRQ work item: ts={} cpu={}\n", this.timestamp, this.cpu);
    }
}

/// Module-level device state
struct DeviceState {
    irq:   u32,
    stats: IrqStats,
    wq:    workqueue::BoxedQueue,
}

impl DeviceState {
    fn new(irq: u32) -> Result<Arc<SpinLock<Self>>> {
        let wq = workqueue::Queue::try_new(
            format_args!("irq_demo_rust"),
            workqueue::Flags::HIGHPRI | workqueue::Flags::MEM_RECLAIM,
        )?;

        let state = Arc::try_new(SpinLock::new(Self {
            irq,
            stats: IrqStats::new(),
            wq,
        }))?;
        Ok(state)
    }
}

/// Top-half interrupt handler (hardirq context)
struct TopHalfHandler {
    state: Arc<SpinLock<DeviceState>>,
}

impl IrqHandler for TopHalfHandler {
    fn handle_irq(&self, _data: &IrqData) -> Return {
        // SAFETY: We are in hardirq context. SpinLock::lock disables preemption.
        // We do NOT take the lock here (could deadlock if lock held in process ctx
        // and we get interrupted). Instead, use atomics directly.
        
        // Access stats via atomic (no lock needed for per-field updates)
        // In production: use per-CPU variables for lockless stats
        
        // Record IRQ time
        let now = Ktime::ktime_get().to_ns() as u64;
        
        // Quick check: is this actually our interrupt?
        // In real driver: read device status register here
        // For demo: always handle
        
        if *use_threaded.read() {
            // Wake threaded handler
            Return::WakeThread
        } else {
            // Schedule workqueue for deferred processing
            // Note: queue_work is safe from hardirq context
            Return::Handled
        }
    }
}

/// Threaded bottom-half (process context, may sleep)
struct ThreadHandler {
    state: Arc<SpinLock<DeviceState>>,
}

impl IrqHandler for ThreadHandler {
    fn handle_irq(&self, _data: &IrqData) -> Return {
        // We are in process context now (kthread irq/N-irq_demo_rust)
        // Can sleep, allocate memory, take mutexes
        
        let state = self.state.lock();
        state.stats.record_irq();
        
        // Queue work for further processing
        let work = Arc::try_new(IrqWorkItem {
            timestamp: Ktime::ktime_get().to_ns() as u64,
            cpu: Task::current_cpu() as u32,
        });
        
        if let Ok(work) = work {
            state.wq.enqueue(work);
        }
        
        Return::Handled
    }
}

/// Module state
struct IrqDemoModule {
    _irq_registration: irq::Registration<TopHalfHandler>,
    _state: Arc<SpinLock<DeviceState>>,
}

impl kernel::Module for IrqDemoModule {
    fn init(_name: &'static CStr, _module: &'static ThisModule) -> Result<Self> {
        let irq = *irq_num.read();
        if irq == 0 {
            pr_err!("irq_num parameter required\n");
            return Err(EINVAL);
        }

        pr_info!("irq_demo_rust: registering on IRQ {}\n", irq);

        let state = DeviceState::new(irq)?;

        // Build IRQ registration
        let flags = irq::flags::SHARED | irq::flags::ONESHOT;
        
        let top_handler = TopHalfHandler { state: state.clone() };
        let thread_handler = ThreadHandler { state: state.clone() };

        let registration = if *use_threaded.read() {
            irq::Registration::try_new_threaded(
                irq,
                top_handler,
                thread_handler,
                flags,
                fmt!("irq_demo_rust"),
            )?
        } else {
            irq::Registration::try_new(
                irq,
                top_handler,
                flags,
                fmt!("irq_demo_rust"),
            )?
        };

        // Set NUMA-aware affinity
        let mut mask = CpuMask::new();
        // Prefer CPUs on NUMA node 0
        for cpu in CpuMask::online() {
            if kernel::numa::cpu_to_node(cpu) == 0 {
                mask.set(cpu);
            }
        }
        if !mask.is_empty() {
            if let Err(e) = irq::set_affinity(irq, &mask) {
                pr_warn!("Failed to set IRQ affinity: {:?}\n", e);
            }
        }

        pr_info!("irq_demo_rust: registered on IRQ {}\n", irq);

        Ok(Self {
            _irq_registration: registration,
            _state: state,
        })
    }
}

impl Drop for IrqDemoModule {
    fn drop(&mut self) {
        // _irq_registration Drop impl calls free_irq + synchronize_irq
        pr_info!("irq_demo_rust: unloaded\n");
    }
}
```

### 26.3 Rust: eBPF Program (aya framework)

```rust
// irq_tracer/src/main.rs — IRQ latency tracer using aya eBPF framework
// Build: cargo build --release
// Run:   sudo ./target/release/irq_tracer

use aya::{
    include_bytes_aligned,
    maps::{HashMap, PerCpuArray, RingBuf},
    programs::TracePoint,
    Bpf,
};
use aya_log::BpfLogger;
use clap::Parser;
use log::{info, warn, error};
use std::{
    convert::TryInto,
    sync::atomic::{AtomicBool, Ordering},
    sync::Arc,
    time::Duration,
};
use tokio::signal;

/// IRQ event from eBPF ring buffer
#[repr(C)]
#[derive(Debug, Clone, Copy)]
struct IrqEvent {
    irq:         u32,
    cpu:         u32,
    duration_ns: u64,
    comm:        [u8; 16],
}

#[derive(Parser)]
struct Opts {
    #[clap(short, long, default_value = "10")]
    threshold_us: u64,
    #[clap(short, long, default_value = "60")]
    duration_secs: u64,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    env_logger::init();
    let opts = Opts::parse();

    // Load eBPF bytecode (embedded at compile time)
    // The eBPF program is compiled by build.rs using aya-build
    let mut bpf = Bpf::load(include_bytes_aligned!(
        "../../target/bpfel-unknown-none/release/irq-tracer-ebpf"
    ))?;

    if let Err(e) = BpfLogger::init(&mut bpf) {
        warn!("BPF logger init failed: {}", e);
    }

    // Attach to irq_handler_entry tracepoint
    let prog_entry: &mut TracePoint = bpf
        .program_mut("irq_handler_entry")
        .unwrap()
        .try_into()?;
    prog_entry.load()?;
    prog_entry.attach("irq", "irq_handler_entry")?;

    // Attach to irq_handler_exit tracepoint
    let prog_exit: &mut TracePoint = bpf
        .program_mut("irq_handler_exit")
        .unwrap()
        .try_into()?;
    prog_exit.load()?;
    prog_exit.attach("irq", "irq_handler_exit")?;

    // Set threshold in eBPF map
    let mut config: HashMap<_, u32, u64> =
        HashMap::try_from(bpf.map_mut("config").unwrap())?;
    config.insert(0u32, opts.threshold_us * 1000, 0)?; // convert to ns

    // Read events from ring buffer
    let mut ring = RingBuf::try_from(bpf.map_mut("events").unwrap())?;

    // Latency histogram (shared with eBPF, updated by kernel)
    let hist: PerCpuArray<_, u64> =
        PerCpuArray::try_from(bpf.map("latency_hist").unwrap())?;

    info!("Tracing IRQ handlers > {}µs for {}s...",
          opts.threshold_us, opts.duration_secs);
    println!("{:<8} {:<6} {:<16} {:>12}", "IRQ", "CPU", "Comm", "Duration");
    println!("{}", "-".repeat(50));

    let running = Arc::new(AtomicBool::new(true));
    let r = running.clone();
    
    tokio::spawn(async move {
        signal::ctrl_c().await.expect("signal handler");
        r.store(false, Ordering::Relaxed);
    });

    let deadline = std::time::Instant::now() +
        Duration::from_secs(opts.duration_secs);

    while running.load(Ordering::Relaxed) &&
          std::time::Instant::now() < deadline {
        
        // Poll ring buffer for events
        while let Some(item) = ring.next() {
            if item.len() < std::mem::size_of::<IrqEvent>() {
                continue;
            }
            let event: IrqEvent = unsafe {
                std::ptr::read_unaligned(item.as_ptr() as *const IrqEvent)
            };
            let comm = std::str::from_utf8(&event.comm)
                .unwrap_or("")
                .trim_end_matches('\0');
            let dur = Duration::from_nanos(event.duration_ns);
            println!("{:<8} {:<6} {:<16} {:>12.1}µs",
                     event.irq, event.cpu, comm,
                     dur.as_nanos() as f64 / 1000.0);
        }
        tokio::time::sleep(Duration::from_millis(100)).await;
    }

    // Print histogram
    println!("\n=== Latency Histogram ===");
    println!("{:<25} {:>10}", "Bucket (ns)", "Count");
    for bucket in 0..64u32 {
        let values = hist.get(&bucket, 0)?;
        let total: u64 = values.iter().sum();
        if total > 0 {
            let low = 1u64 << bucket;
            let high = low << 1;
            let bar = "*".repeat((total.min(40)) as usize);
            println!("[{:>8}ns - {:>8}ns)  {:>8}  {}",
                     low, high, total, bar);
        }
    }

    Ok(())
}

// irq-tracer-ebpf/src/main.rs — The eBPF kernel-side program (aya-bpf)
// This compiles to BPF bytecode

#[cfg(bpf_program)]
mod bpf_program {
use aya_bpf::{
    macros::{map, tracepoint},
    maps::{PerCpuArray, RingBuf, HashMap},
    programs::TracePointContext,
    helpers::{bpf_get_smp_processor_id, bpf_ktime_get_ns, bpf_get_current_comm},
    BpfContext,
};

#[map]
static ENTRY_TS: PerCpuArray<u64> = PerCpuArray::with_max_entries(1, 0);

#[map]
static EVENTS: RingBuf = RingBuf::with_byte_size(256 * 1024, 0);

#[map]
static LATENCY_HIST: PerCpuArray<u64> = PerCpuArray::with_max_entries(64, 0);

#[map]
static CONFIG: HashMap<u32, u64> = HashMap::with_max_entries(1, 0);

#[repr(C)]
struct IrqEvent {
    irq:         u32,
    cpu:         u32,
    duration_ns: u64,
    comm:        [u8; 16],
}

#[tracepoint(name = "irq_handler_entry", category = "irq")]
pub fn irq_handler_entry(ctx: TracePointContext) -> u32 {
    let ts = unsafe { bpf_ktime_get_ns() };
    if let Some(entry) = ENTRY_TS.get_ptr_mut(0) {
        unsafe { *entry = ts; }
    }
    0
}

#[tracepoint(name = "irq_handler_exit", category = "irq")]
pub fn irq_handler_exit(ctx: TracePointContext) -> u32 {
    let now = unsafe { bpf_ktime_get_ns() };
    let start = match ENTRY_TS.get(0) {
        Some(v) => *v,
        None => return 0,
    };
    if start == 0 { return 0; }
    
    let duration = now - start;
    
    // Update histogram
    let mut bucket = 0u32;
    let mut tmp = duration;
    while tmp > 1 && bucket < 63 { tmp >>= 1; bucket += 1; }
    if let Some(count) = LATENCY_HIST.get_ptr_mut(bucket) {
        unsafe { *count += 1; }
    }
    
    // Check threshold
    let threshold = CONFIG.get(&0u32).copied().unwrap_or(10_000); // 10µs default
    if duration < threshold { return 0; }
    
    // Emit event to ring buffer
    let irq: u32 = unsafe { ctx.read_at(8).unwrap_or(0) }; // irq field offset in tracepoint
    
    if let Some(event) = EVENTS.reserve::<IrqEvent>(0) {
        unsafe {
            let e = event.as_mut_ptr();
            (*e).irq = irq;
            (*e).cpu = bpf_get_smp_processor_id();
            (*e).duration_ns = duration;
            bpf_get_current_comm(
                (*e).comm.as_mut_ptr() as *mut _,
                (*e).comm.len() as u32,
            );
        }
        event.submit(0);
    }
    0
}
} // mod bpf_program
```

### 26.4 Cargo.toml for aya project

```toml
# Cargo.toml
[package]
name = "irq-tracer"
version = "0.1.0"
edition = "2021"

[[bin]]
name = "irq-tracer"
path = "src/main.rs"

[dependencies]
aya = { version = "0.12", features = ["async_tokio"] }
aya-log = "0.2"
anyhow = "1"
clap = { version = "4", features = ["derive"] }
env_logger = "0.11"
log = "0.4"
tokio = { version = "1", features = ["macros", "rt", "rt-multi-thread", "net", "signal", "time"] }

[build-dependencies]
aya-build = "0.1"

# irq-tracer-ebpf/Cargo.toml
[package]
name = "irq-tracer-ebpf"
version = "0.1.0"
edition = "2021"

[dependencies]
aya-bpf = { version = "0.1", features = ["v6_0"] }
aya-log-ebpf = "0.1"

[profile.release]
opt-level = 3
lto = true
codegen-units = 1
```

---

## 27. Performance Benchmarking and Tracing

### 27.1 Measuring Interrupt Latency

```bash
# ─── Hardware-level latency ───────────────────────────────────────────────────

# cyclictest: gold standard for interrupt latency
cyclictest \
    --mlockall \          # lock all pages to prevent page fault jitter
    --smp \               # test all CPUs
    --priority=99 \       # SCHED_FIFO priority 99
    --interval=200 \      # wake-up interval: 200µs
    --distance=0 \        # all CPUs same interval
    --duration=300 \      # run for 5 minutes
    --histogram=1000 \    # histogram up to 1000µs
    --histfile=/tmp/hist.dat

# Plot histogram
gnuplot -e "
set terminal png; set output '/tmp/latency.png';
set xlabel 'Latency (µs)'; set ylabel 'Count';
plot '/tmp/hist.dat' using 1:2 with linespoints title 'CPU0'"

# ─── Kernel tracing ───────────────────────────────────────────────────────────

# Function tracer: measure time in hardirq handlers
echo function > /sys/kernel/debug/tracing/current_tracer
echo "irq_handler_entry irq_handler_exit" > /sys/kernel/debug/tracing/set_ftrace_filter
echo 1 > /sys/kernel/debug/tracing/tracing_on
sleep 5
echo 0 > /sys/kernel/debug/tracing/tracing_on
cat /sys/kernel/debug/tracing/trace

# irqsoff tracer: record longest time spent with IRQs disabled
echo irqsoff > /sys/kernel/debug/tracing/current_tracer
echo 1 > /sys/kernel/debug/tracing/tracing_on
sleep 10
echo 0 > /sys/kernel/debug/tracing/tracing_on
cat /sys/kernel/debug/tracing/trace
# Shows: the longest irq-disabled window with full call stack

# preemptoff tracer
echo preemptoff > /sys/kernel/debug/tracing/current_tracer

# preemptirqsoff: combined preemption + IRQ disabled
echo preemptirqsoff > /sys/kernel/debug/tracing/current_tracer
```

### 27.2 perf for IRQ Analysis

```bash
# Profile IRQ handlers
perf record -e irq:irq_handler_entry,irq:irq_handler_exit \
    -e irq:softirq_entry,irq:softirq_exit \
    -a -g sleep 10
perf report --sort=dso,symbol

# IRQ handler time (stat)
perf stat -e irq:irq_handler_entry \
          -e irq:softirq_entry \
          -e irq:softirq_raise \
          -a sleep 5

# Interrupt counts per CPU
perf stat -e irq:irq_handler_entry --per-cpu -a sleep 5

# Trace specific IRQ
perf trace -e irq:irq_handler_entry \
           --filter "irq==24" \
           sleep 5

# Top functions called during IRQ handling
perf top -e irq:irq_handler_entry --sort=cpu,symbol
```

### 27.3 /proc and /sys Monitoring

```bash
# Real-time IRQ rates (watch every 1 second)
watch -n1 'cat /proc/interrupts'

# Softirq counts
watch -n1 'cat /proc/softirqs'

# IRQ affinity overview
for irq_dir in /proc/irq/*/; do
    irq=$(basename $irq_dir)
    [[ "$irq" == "default_smp_affinity" ]] && continue
    aff=$(cat $irq_dir/smp_affinity_list 2>/dev/null || echo "N/A")
    name=$(ls $irq_dir 2>/dev/null | head -1)
    printf "IRQ %-6s affinity=%-12s\n" "$irq" "$aff"
done

# IRQ storms (rapid increase in count)
prev=$(grep -E "^[ ]*[0-9]" /proc/interrupts | awk '{print $1, $2}')
sleep 1
curr=$(grep -E "^[ ]*[0-9]" /proc/interrupts | awk '{print $1, $2}')
diff <(echo "$prev") <(echo "$curr") | grep "^>" | awk '{rate=$2; if(rate>10000) print "HIGH RATE:", $0}'

# NMI count per CPU
cat /proc/interrupts | grep "NMI"

# Machine check events
cat /proc/interrupts | grep "MCE"
mcelog --client 2>/dev/null || journalctl -k | grep -i "machine check"
```

### 27.4 Benchmarking Interrupt Throughput

```bash
# iperf3 + IRQ rate: network IRQ throughput
iperf3 -s &
iperf3 -c 127.0.0.1 -t 30 -P 8 &
# Watch IRQ rate for the NIC
watch -n0.5 'grep eth0 /proc/net/dev; cat /proc/interrupts | grep eth0'

# Block I/O IRQ rate
fio --rw=randread --bs=512 --ioengine=libaio --direct=1 \
    --numjobs=4 --iodepth=32 --size=1G --filename=/dev/nvme0n1 \
    --name=bench --time_based --runtime=30 &
watch -n1 'cat /proc/interrupts | grep nvme'

# Measure IRQ overhead contribution to total CPU time
perf stat -a --timeout=5000 sleep 5 2>&1 | grep -E "irq_time|softirq_time"
# Or via /proc/stat irq + softirq columns
awk '/^cpu /{irq=$7+$8; total=$2+$3+$4+$5+$6+$7+$8; printf "IRQ%%: %.2f\n", irq/total*100}' /proc/stat
```

---

## 28. Architecture Diagrams (ASCII)

### 28.1 Complete Interrupt Flow (x86_64)

```
                         HARDWARE LAYER
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌──────────┐  MSI write   ┌────────────┐  APIC bus  ┌──────────────────┐ │
│  │  PCIe    │─────────────>│  I/O APIC  │───────────>│   CPU 0          │ │
│  │  Device  │  (0xFEE0..)  │ Redirection│            │  ┌─────────────┐ │ │
│  └──────────┘              │  Table     │            │  │ Local APIC  │ │ │
│                            └────────────┘            │  │  IRR: pending│ │ │
│  ┌──────────┐  Physical    ┌────────────┐            │  │  ISR: in-svc│ │ │
│  │  Legacy  │──IRQ line───>│  8259 PIC  │──INTR────>│  │  TPR: prio  │ │ │
│  │  Device  │              │ (cascaded) │            │  └──────┬──────┘ │ │
│  └──────────┘              └────────────┘            │         │        │ │
│                                                       │  INTR pin asserted │
│                                                       └─────────┼────────┘ │
└─────────────────────────────────────────────────────────────────┼──────────┘
                                                                   │
                         CPU MICROCODE LAYER                       │
┌──────────────────────────────────────────────────────────────────▼──────────┐
│                                                                             │
│  1. Complete current instruction (or abort if faulting)                    │
│  2. Check IF flag (maskable) or NMI pin (non-maskable)                     │
│  3. Determine target stack (TSS RSP0 or IST[n])                            │
│  4. Push: SS, RSP, RFLAGS, CS, RIP [, ErrorCode]                          │
│  5. Clear IF (interrupt gate)                                               │
│  6. Load CS:RIP from IDT[vector]                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                                                   │
                         KERNEL ENTRY LAYER                        │
┌──────────────────────────────────────────────────────────────────▼──────────┐
│                                                                             │
│  arch/x86/entry/entry_64.S:                                                │
│  common_interrupt:                                                          │
│    PUSH_AND_CLEAR_REGS          ← save all GPRs                           │
│    call irqentry_enter          ← RCU, context tracking                    │
│    mov  %rsp, %rdi              ← pt_regs* argument                        │
│    call do_IRQ (or direct handler via IDT stub)                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                                                   │
                         GENERIC IRQ LAYER                         │
┌──────────────────────────────────────────────────────────────────▼──────────┐
│                                                                             │
│  do_IRQ(regs, vector)                                                      │
│    │                                                                        │
│    ▼                                                                        │
│  irq_enter()  ──── sets HARDIRQ_OFFSET in preempt_count                   │
│    │                                                                        │
│    ▼                                                                        │
│  irq_desc = irq_to_desc(vector)  ←── lookup by Linux IRQ number           │
│    │                                                                        │
│    ▼                                                                        │
│  handle_irq(desc, regs)                                                    │
│    │                                                                        │
│    ├─ handle_edge_irq() ──── ack chip, call action chain                  │
│    ├─ handle_level_irq() ─── mask chip, call actions, unmask              │
│    └─ handle_fasteoi_irq() ─ call actions, EOI                            │
│              │                                                              │
│              ▼                                                              │
│         irqaction->handler()                                               │
│              │                                                              │
│         IRQ_HANDLED ──────────────────────────────────────────────────┐   │
│              │                                                          │   │
│         IRQ_WAKE_THREAD ─────────────────────────────────────────┐   │   │
│                                                                   │   │   │
└───────────────────────────────────────────────────────────────────┼───┼───┘
                                                                   │   │
                         RETURN PATH                               │   │
┌──────────────────────────────────────────────────────────────────▼───▼───┐
│                                                                           │
│  irq_exit()                                                               │
│    │                                                                       │
│    ├── clears HARDIRQ_OFFSET                                              │
│    ├── if local_softirq_pending(): invoke_softirq()                       │
│    │     │                                                                 │
│    │     ▼                                                                 │
│    │   __do_softirq()    ─── processes pending softirq bits               │
│    │     │  (up to MAX_SOFTIRQ_RESTART=10 passes, then ksoftirqd)        │
│    │     └── NET_RX, NET_TX, TIMER, TASKLET, RCU, ...                   │
│    │                                                                       │
│    └── if need_resched(): preempt_schedule_irq()                         │
│                                                                           │
│  RESTORE_REGS                                                             │
│  IRET (or SYSRET for syscall path)                                        │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
                   ↕ if IRQ_WAKE_THREAD
┌──────────────────────────────────────────────────────────────────────────┐
│  Threaded IRQ kthread: irq/N-<name>                                      │
│                                                                          │
│  irq_thread()                                                            │
│    while (!kthread_should_stop()) {                                      │
│        wait_event_interruptible(irq_thread_wait, ...)                   │
│        thread_fn(irq, dev_id)   ← bottom-half, process ctx              │
│        if IRQF_ONESHOT: unmask IRQ line after completion                 │
│    }                                                                     │
└──────────────────────────────────────────────────────────────────────────┘
```

### 28.2 Bottom-Half Processing Model

```
Time →

  Hardirq       ━━━━━━━━━━[TOP HALF ~1-5µs]━━━━━━━━━━
  (IF=0)                   │raise_softirq()│
                           │or sched work  │
  IF=0 ←────────────────────────────────────────────────── IF=1 (after IRET)

  Softirq       ══════════════════════[SOFTIRQ ~10-100µs]═══════════
  (irq_exit)               raise         run      done
                           bit set       __do_softirq()

  ksoftirqd     ┄┄┄┄┄┄┄┄┄┄┄┄[sleeping]┄┄┄[woken if budget exceeded]┄┄┄
  (SCHED_NORMAL)                                   ┌──[SOFTIRQ]──┐

  Tasklet       ════════════════════════════════[TASKLET callback]════
  (softirq ctx)                                    (serialized per-tasklet)

  Workqueue     ──────────────────────────────────────────────────────
  kworker/N:M               schedule              [WORK ITEM]
  (process ctx)             work_struct            (can sleep)

  Threaded IRQ  ──────────────────────────────────────────────────────
  irq/N-name               IRQ_WAKE_THREAD         [thread_fn]
  (SCHED_FIFO 50)                                  (can sleep)
  ONESHOT: IRQ         [masked]━━━━━━━━━━━━━━━━━━━━[unmask on return]
```

### 28.3 NUMA-Aware Interrupt Routing

```
                    NUMA Node 0                    NUMA Node 1
         ┌──────────────────────────┐    ┌──────────────────────────┐
         │  CPU 0   CPU 1   CPU 2   │    │  CPU 4   CPU 5   CPU 6   │
         │  ┌───┐   ┌───┐   ┌───┐  │    │  ┌───┐   ┌───┐   ┌───┐  │
         │  │L1 │   │L1 │   │L1 │  │    │  │L1 │   │L1 │   │L1 │  │
         │  └─┬─┘   └─┬─┘   └─┬─┘  │    │  └─┬─┘   └─┬─┘   └─┬─┘  │
         │    └──┬────┘   ┌───┘   │    │    └──┬────┘   ┌───┘   │
         │     ┌─┴──────────┴─┐   │    │     ┌─┴──────────┴─┐   │
         │     │  L3 Cache    │   │    │     │  L3 Cache    │   │
         │     └──────┬───────┘   │    │     └──────┬───────┘   │
         │            │  Local    │    │            │  Local    │
         │         DRAM           │    │         DRAM           │
         │            │           │    │            │           │
         │     ┌──────┴──────┐    │    │     ┌──────┴──────┐   │
         │     │  I/O APIC 0 │    │    │     │  I/O APIC 1 │   │
         │     └──────┬──────┘    │    │     └──────┬──────┘   │
         └────────────┼───────────┘    └────────────┼──────────┘
                      │                             │
              ┌───────┴────────┐           ┌────────┴───────┐
              │  PCIe Root     │           │  PCIe Root     │
              │  NIC (eth0)    │           │  NVMe (nvme0)  │
              │  numa_node=0   │           │  numa_node=1   │
              └────────────────┘           └────────────────┘

  Optimal Affinity:
    eth0 IRQs (24-31) → smp_affinity_list: 0-3  (NUMA node 0 CPUs)
    nvme0 IRQs (32-39) → smp_affinity_list: 4-7 (NUMA node 1 CPUs)

  Cross-node penalty avoided:
    Without affinity: eth0 IRQ might land on CPU 4 → remote DRAM access
    With affinity:    eth0 IRQ always on CPU 0-3  → local DRAM access
```

### 28.4 IRQ Subsystem Data Structure Relations

```
  Linux IRQ number (virq)
         │
         ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  struct irq_desc                                            │
  │  ┌─────────────────────┐  ┌──────────────────────────────┐ │
  │  │  irq_data           │  │  irqaction chain             │ │
  │  │  ┌───────────────┐  │  │  ┌──────────────────────┐   │ │
  │  │  │  irq_chip ────┼──┼──┼─>│  handler (top-half)  │   │ │
  │  │  │  (hw ops)     │  │  │  │  thread_fn (bot-half) │   │ │
  │  │  ├───────────────┤  │  │  │  thread (kthread)     │   │ │
  │  │  │  irq_domain ──┼──┼──┼─>│  flags (IRQF_*)      │   │ │
  │  │  │  (hw mapping) │  │  │  │  dev_id              │   │ │
  │  │  ├───────────────┤  │  │  │  next ───────────────┼──>│ │
  │  │  │  hwirq        │  │  │  └──────────────────────┘   │ │
  │  │  │  (hw IRQ num) │  │  └──────────────────────────────┘ │
  │  │  └───────────────┘  │                                   │
  │  ├─────────────────────┤  ┌──────────────────────────────┐ │
  │  │  handle_irq ────────┼─>│  flow handler                │ │
  │  │  (edge/level/etc)   │  │  (handle_edge_irq, etc.)     │ │
  │  ├─────────────────────┤  └──────────────────────────────┘ │
  │  │  kstat_irqs (percpu)│   per-CPU interrupt counters      │
  │  │  lock (raw_spinlock)│                                   │
  │  │  depth (disable cnt)│                                   │
  │  │  affinity_hint      │                                   │
  │  └─────────────────────┘                                   │
  └─────────────────────────────────────────────────────────────┘
         │
         ▼
  ┌─────────────────┐     ┌─────────────────────────────────┐
  │  irq_domain     │────>│  struct irq_chip                │
  │                 │     │  .irq_ack()                     │
  │  hwirq → virq  │     │  .irq_mask/unmask()             │
  │  mapping table  │     │  .irq_eoi()                     │
  │                 │     │  .irq_set_affinity()            │
  └─────────────────┘     │  .irq_set_type()               │
                          └─────────────────────────────────┘
```

---

## 29. Rollout / Rollback Plan

### 29.1 Kernel Module Deployment

```bash
# ─── Pre-deployment checks ────────────────────────────────────────────────────

# Verify kernel version compatibility
uname -r
modinfo irq_demo.ko | grep -E "vermagic|depends"

# Check for existing handlers on the target IRQ
cat /proc/interrupts | awk -v irq=24 '$1 ~ "^"irq":"'

# Verify no lockdep warnings in test environment
dmesg | grep -i "lockdep\|WARNING\|BUG"

# Run with KASAN/KCSAN enabled kernel first (dev environment)
# CONFIG_KASAN=y, CONFIG_KCSAN=y

# ─── Staged rollout ────────────────────────────────────────────────────────────

# Stage 1: Single node, non-production
insmod irq_demo.ko irq=24 threaded=1
dmesg | tail -20
cat /proc/irq/24/smp_affinity_list
cat /proc/irq_demo/stats

# Stage 2: Canary production node
# Monitor for 24h:
watch -n5 'cat /proc/irq_demo/stats; dmesg | tail -5'

# Stage 3: Full rollout
for node in prod-01 prod-02 prod-03; do
    ssh $node "insmod /opt/modules/irq_demo.ko irq=24" && \
    echo "$node: OK" || echo "$node: FAILED"
done

# ─── Rollback ─────────────────────────────────────────────────────────────────

# Remove module (free_irq called in module_exit)
rmmod irq_demo

# Verify IRQ returned to previous state
cat /proc/interrupts | grep " 24:"

# Emergency: if module hangs on rmmod (handler stuck)
# The kernel will forcibly remove after irq synchronization timeout
# To avoid: always use synchronize_irq() in cleanup

# ─── Monitoring post-deploy ───────────────────────────────────────────────────

# Alert conditions:
# - /proc/irq/N/spurious_count increasing rapidly → hardware issue
# - IRQ handler time > 100µs (via bpftrace) → handler too slow
# - CPU[0] irq time > 80% → affinity imbalance
# - NMI count increasing → hardware errors (check mcelog)

# Prometheus metrics (via node_exporter)
# node_interrupts_total{cpu="0",type="24",devices="xhci_hcd"} 12345
```

### 29.2 Production Interrupt Tuning Checklist

```bash
# ─── Boot parameters (requires reboot) ────────────────────────────────────────
# Add to /etc/default/grub GRUB_CMDLINE_LINUX:

# RT/latency-sensitive systems:
# isolcpus=domain,managed_irq,2-7 nohz_full=2-7 rcu_nocbs=2-7
# irqaffinity=0-1 processor.max_cstate=1 intel_idle.max_cstate=0
# idle=poll (extreme: prevents any C-state)

# Network-heavy systems (high PPS):
# default_hugepagesz=1G hugepagesz=1G hugepages=8
# iommu=pt (passthrough, reduces IOMMU overhead for trusted devices)

# ─── Runtime tuning (no reboot) ───────────────────────────────────────────────

# Disable irqbalance for manual control
systemctl stop irqbalance
systemctl disable irqbalance

# Set NIC interrupt affinity (RSS queues)
ethtool -l eth0  # check number of queues
for i in $(seq 0 7); do
    irq=$(cat /sys/class/net/eth0/queues/rx-$i/rps_cpus 2>/dev/null)
    echo "$((i % 4))" > /proc/irq/$((24+i))/smp_affinity_list
done

# Enable NIC hardware coalescing
ethtool -C eth0 adaptive-rx on adaptive-tx on

# Set socket buffer sizes
sysctl -w net.core.rmem_max=134217728
sysctl -w net.core.wmem_max=134217728
sysctl -w net.ipv4.tcp_rmem="4096 87380 134217728"

# ─── Verification ─────────────────────────────────────────────────────────────

# Run cyclictest to verify latency after changes
cyclictest -t1 -p99 -i200 -a2 -d0 -l1000000 2>&1 | tail -5
# Target: Max < 100µs (non-RT), Max < 200µs (RT with CONFIG_PREEMPT_RT)
```

---

## 30. References

### Linux Kernel Documentation

- `Documentation/core-api/genericirq.rst` — Generic IRQ layer architecture
- `Documentation/admin-guide/irq-affinity.rst` — IRQ affinity configuration
- `Documentation/admin-guide/sysrq.rst` — Emergency NMI/debug options
- `Documentation/trace/ftrace.rst` — Ftrace usage for IRQ tracing
- `Documentation/scheduler/sched-RT-group.rst` — RT scheduling
- `kernel/irq/` — Core IRQ subsystem source
- `arch/x86/kernel/irq.c`, `arch/x86/kernel/idt.c` — x86 IRQ setup
- `arch/x86/include/asm/apic.h` — APIC definitions

### Intel Architecture References

- Intel SDM Volume 3A, Chapter 6: Interrupt and Exception Handling
- Intel SDM Volume 3A, Chapter 10: Advanced Programmable Interrupt Controller (APIC)
- Intel VT-x Specification: Posted Interrupt Processing
- Intel VT-d Specification: Interrupt Remapping

### Books

- *Linux Device Drivers, 3rd Ed.* — Corbet, Rubini, Kroah-Hartman (Ch. 10: Interrupt Handling)
- *Understanding the Linux Kernel, 3rd Ed.* — Bovet & Cesati (Ch. 4: Interrupts and Exceptions)
- *Professional Linux Kernel Architecture* — Mauerer (Ch. 14)
- *Systems Performance, 2nd Ed.* — Brendan Gregg (Ch. 6: CPUs — section on interrupts)

### Real-Time Linux

- PREEMPT_RT patchset: https://wiki.linuxfoundation.org/realtime
- RTL (Real-Time Linux) merged in kernel 6.12: see kernel.org changelogs
- Red Hat RT Tuning Guide: https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux_for_real_time

### eBPF and Tracing

- BCC tools: `hardirqs`, `softirqs`, `irqsnoop` — https://github.com/iovisor/bcc
- bpftrace one-liners: https://github.com/bpftrace/bpftrace/blob/master/docs/reference_guide.md
- Aya eBPF framework (Rust): https://aya-rs.dev
- Cilium eBPF (Go): https://github.com/cilium/ebpf

### Security

- IOMMU interrupt remapping: VT-d spec, Section 5.1
- Interrupt injection attacks: "Interrupting the Interrupt" (BlackHat 2019)
- CVE-2021-39633: I/O APIC interrupt injection
- ACPI/SMI interrupt attacks: "SMM Rootkits" research

---

## Next 3 Steps

**Step 1 — Set up IRQ latency baseline on your systems**
```bash
# Install cyclictest and run baseline
apt-get install -y rt-tests
cyclictest --mlockall --smp --priority=99 --interval=200 --distance=0 \
           --duration=120 --histogram=1000 --histfile=/tmp/baseline_hist.dat
# Compare against PREEMPT_RT kernel if latency > 500µs worst-case
```

**Step 2 — Deploy eBPF IRQ tracer to identify slow handlers**
```bash
# Build and run the aya-based tracer (26.3)
cd irq-tracer && cargo build --release
sudo ./target/release/irq-tracer --threshold-us=50 --duration-secs=300
# Identify any handlers taking > 50µs → candidates for threaded IRQ conversion
```

**Step 3 — Audit and optimize NIC interrupt affinity**
```bash
# Run the NUMA affinity optimizer (25.3)
go build -o irq_opt ./irq_affinity_optimizer.go
sudo ./irq_opt --dry-run --verbose
# Apply recommended changes
sudo ./irq_opt
# Validate: measure packet processing latency before/after with netperf
netperf -H <server> -t TCP_RR -l 30 -- -o mean_latency,stddev_latency,p99_latency
```