# Deep Fundamentals: CPU Rings, Registers, Hooks, Memory Safety, IPI
## A First-Principles Explanation for Systems Mastery

---

## Table of Contents

1. [Why Are Rings 1 & 2 Unused in Linux?](#1-why-are-rings-1--2-unused-in-linux)
2. [What Are Registers?](#2-what-are-registers)
3. [What Are Hooks?](#3-what-are-hooks)
4. [What Is Out-of-Bounds Memory Access?](#4-what-is-out-of-bounds-memory-access)
5. [What Is Unsafe Pointer Arithmetic?](#5-what-is-unsafe-pointer-arithmetic)
6. [What Is Bounded Execution Time?](#6-what-is-bounded-execution-time)
7. [What Is an Inter-Processor Interrupt (IPI)?](#7-what-is-an-inter-processor-interrupt-ipi)

---

## 1. Why Are Rings 1 & 2 Unused in Linux?

### 1.1 First: What Are CPU Rings, Really?

Before asking why Rings 1 and 2 are unused, you must deeply understand
what a "ring" is at the hardware level.

A **CPU ring** (also called a **privilege level**) is a hardware-enforced
security boundary built directly into the CPU's silicon.

**The core idea**: Not all code should be trusted equally.
- Your browser shouldn't be able to directly write to the disk controller.
- A buggy user program shouldn't be able to corrupt the kernel.
- The kernel shouldn't be able to be hijacked by user programs.

The CPU enforces this using physical circuits that track "what privilege
level is the currently-executing instruction?" and refuses certain operations
to lower-privilege code.

### 1.2 The x86 Ring Architecture (Hardware Design)

Intel designed x86 with 4 privilege levels, numbered 0–3.
The number 0–3 is stored in two bits called **CPL (Current Privilege Level)**
in the **CS register** (Code Segment register).

```
        RING 0         RING 1         RING 2         RING 3
   ┌─────────────┐ ┌───────────┐ ┌───────────┐ ┌────────────┐
   │   KERNEL    │ │ "Device   │ │ "Device   │ │  USER APP  │
   │             │ │  Drivers" │ │  Drivers" │ │            │
   │ Full access │ │  (Intel   │ │  (Intel   │ │ Restricted │
   │ to ALL hw   │ │  vision)  │ │  vision)  │ │  access    │
   └─────────────┘ └───────────┘ └───────────┘ └────────────┘
         ↑ most                                   most ↑
      privileged                              restricted
      
CPL = 00 (binary)  01              10              11
    = 0 (decimal)   1               2               3
```

**Intel's original vision (1980s):**
```
Ring 0: OS Kernel            → full hardware access
Ring 1: OS Services          → less privileged than kernel
         (device drivers, system calls implementations)
Ring 2: OS Services (cont)   → even less privileged
         (protocol stacks, filesystem drivers)
Ring 3: Application Code     → least privileged, most restricted
```

This was a beautiful, sophisticated design. Ring 1 and 2 were meant for
an architecture called **"microkernel with ring-separated drivers"**.

### 1.3 What CAN Ring 1 & 2 Do That Ring 3 Cannot?

To understand the opportunity cost, you must know what instructions
are gated by rings:

```
PRIVILEGED INSTRUCTIONS (Ring 0 only):
  HLT         — halt the CPU
  LGDT/LIDT   — load Global/Interrupt Descriptor Table
  MOV CR0–CR4 — modify control registers (paging, protection)
  WRMSR/RDMSR — write/read Model Specific Registers (CPU config)
  IN/OUT      — direct I/O port access
  INVLPG      — invalidate TLB entry
  IRET (to lower ring) — return from interrupt to lower privilege

IOPL-GATED INSTRUCTIONS (available to ring ≤ IOPL):
  IN/OUT      — direct hardware port I/O
  (IOPL field in EFLAGS controls minimum ring for these)

RING 1/2 ADVANTAGE over Ring 3:
  → Can be granted IOPL (I/O port access) more easily
  → Has different stack segment rules
  → Page table entries can specify DPL (Descriptor Privilege Level)
    to restrict page access to Ring 0/1/2 but not Ring 3
  → Call Gates can be set up differently
  → Can be granted ring-specific memory segments
```

### 1.4 Why Linux (and Almost All Modern OSes) Ignore Rings 1 & 2

There are 6 concrete reasons:

---

**Reason 1: Portability Killed Intermediate Rings**

Linux was designed to run on multiple CPU architectures:

```
x86:          4 rings (0,1,2,3)
ARM (32-bit): 7 privilege levels (usr,fiq,irq,svc,abt,und,sys)
ARM64:        4 Exception Levels (EL0,EL1,EL2,EL3)
RISC-V:       3 modes (U, S, M)
MIPS:         2 modes (User, Kernel)
PowerPC:      2 modes (User, Supervisor) + Hypervisor
SPARC:        8 privilege levels
```

There is **NO common equivalent** to "Ring 1" and "Ring 2" across all
architectures. If Linux used them on x86, it would need completely
different code for every other CPU family. The portability cost is
enormous.

```
Linux kernel design principle:
    "Abstract over the hardware. Use only the LOWEST COMMON DENOMINATOR."
    
Lowest common denominator of privilege = 2 levels (user, kernel)
Present on EVERY architecture.
```

---

**Reason 2: The Complexity Cost vs. Security Benefit Tradeoff**

Using Rings 1 & 2 requires:

```
For each driver placed in Ring 1:
  - Define call gates (special IDT entries for cross-ring transitions)
  - Manage per-ring stack segments
  - Handle ring transitions (RPL/DPL permission checks)
  - Manage separate page tables per ring
  - Handle Ring 1→Ring 0 calls (as expensive as Ring 3→Ring 0)

Cost of Ring 3→Ring 0 transition (syscall):  ~100-200 ns
Cost of Ring 1→Ring 0 transition (call gate): ~80-150 ns

The performance difference is MINIMAL for modern workloads.
```

The kernel complexity would roughly double. For marginal benefit.

---

**Reason 3: The Meltdown CPU Vulnerability Changed Everything**

In 2018, the **Meltdown** vulnerability was discovered. It exploited the
fact that kernel memory is mapped into every process's virtual address space
(for fast syscall transitions). Patches (**KPTI — Kernel Page Table Isolation**)
completely separate kernel and user page tables:

```
BEFORE KPTI (fast syscall):
  User process has kernel pages mapped (read-protected, but mapped)
  Syscall: just change privilege level, same page tables
  Cost: ~50 ns

AFTER KPTI (secure syscall):
  User process has NO kernel pages mapped
  Syscall: change privilege level + flush TLB + switch page tables
  Cost: ~100-300 ns
```

This made the "Ring 1/2 saves transition time" argument even weaker.
The penalty is now dominated by page table switching, not ring switching.

---

**Reason 4: Monolithic Kernel Design**

Linux is a **monolithic kernel** — ALL kernel code (memory management,
filesystem, network stack, most drivers) runs in Ring 0 as trusted code.

```
MONOLITHIC (Linux):              MICROKERNEL (original Intel Ring vision):
┌──────────────────────┐         ┌──────────────────────┐
│      Ring 0          │         │      Ring 0          │
│ ┌──────────────────┐ │         │   Tiny kernel core   │
│ │ memory manager   │ │         │   IPC mechanism only │
│ │ scheduler        │ │         └──────────────────────┘
│ │ network stack    │ │         ┌──────────────────────┐
│ │ filesystem       │ │         │      Ring 1          │
│ │ device drivers   │ │         │   Device drivers     │
│ └──────────────────┘ │         └──────────────────────┘
└──────────────────────┘         ┌──────────────────────┐
                                 │      Ring 2          │
                                 │   Protocol stacks    │
                                 └──────────────────────┘

If a driver crashes:             If a driver crashes:
  → Kernel panic (entire system)   → Restart that Ring 1 service
                                   → System survives
```

In a microkernel, Rings 1 & 2 make perfect sense! But Linux chose
monolithic for performance and simplicity. Decision made in 1991, too
late to change now.

---

**Reason 5: Virtual Machine Extension (VMX/VT-x) Added Ring -1**

Modern Intel CPUs added **VMX (Virtualization Extensions)** which created
a new privilege level **below Ring 0** — sometimes called **Ring -1** or
**VMX Root Mode**:

```
VMX Root Mode (Ring -1): Hypervisor (KVM, VMware, Xen)
Ring 0:                  Guest OS Kernel (thinks it's privileged)
Ring 3:                  Guest user processes
```

So the evolution went the OPPOSITE direction from using Ring 1/2.
Instead of using rings 1/2 to isolate drivers, we needed ring -1 for VMs.

---

**Reason 6: OS/2 and Windows NT Proved It Wasn't Worth It**

OS/2 (IBM/Microsoft, 1987) used Ring 0 for kernel, Ring 2 for device
drivers, Ring 3 for applications. It was:
- Incredibly complex to develop for
- Had no measurable security improvement in practice
- Was abandoned

Windows NT (Cutler, 1993) deliberately chose the Linux model: only
Ring 0 (kernel) and Ring 3 (user). Simplified everything.

---

**Could We Use Them to Enhance Capabilities?**

Yes, theoretically:

```
THEORETICAL USE OF RING 1 IN LINUX:

Option A: Driver Isolation
  Ring 0: Core kernel (scheduler, MM)
  Ring 1: Device drivers (NIC, storage)
  Ring 3: Applications

  Benefit: Driver crash doesn't kill kernel
  Cost: Every driver↔kernel call = expensive ring transition
        Cannot share kernel data structures easily

Option B: Trusted OS Services
  Ring 0: Security-critical kernel code
  Ring 1: Trusted services (crypto, audit) with limited kernel access
  Ring 3: Normal applications

  Benefit: Reduced Ring 0 attack surface
  Cost: Complex IPC between rings

PRACTICAL ANSWER:
  Modern systems achieve similar goals using DIFFERENT mechanisms:
  - SELinux/AppArmor for privilege separation (software, not hardware rings)
  - Namespaces + cgroups for process isolation
  - io_uring for efficient kernel↔user communication
  - eBPF (verified code that runs in Ring 0 safely — replaces Ring 1!)
  - Trusted Execution Environments (SGX, TrustZone — better than Ring 1!)
```

**The deep insight**: eBPF is essentially the software equivalent of what
Ring 1 was supposed to be — a safe zone where code runs with more privilege
than Ring 3 but is verified/constrained. Linux solved the Ring 1 problem
with software (eBPF verifier), not hardware rings.

---

## 2. What Are Registers?

### 2.1 The Physical Reality — Starting From Transistors

A register is a **small, extremely fast storage location built directly
inside the CPU chip**, made of a special circuit called a **flip-flop**
(or in modern CPUs, SRAM cells).

Let's build this from the ground up:

```
TRANSISTOR (the atom of computing):
  A transistor is an electrically-controlled switch.
  Input voltage HIGH → switch CLOSED → current flows
  Input voltage LOW  → switch OPEN  → no current

  Symbol: ──┤├──
```

```
FLIP-FLOP (stores 1 bit):
  Two cross-coupled NOT gates form a "latch" — a circuit that
  REMEMBERS one of two stable states (0 or 1) indefinitely
  (as long as power is applied).

  ┌────────────────────────────┐
  │    D Flip-Flop (1 bit)     │
  │                            │
  │  D ──┤          ├── Q      │  Q = stored value (0 or 1)
  │  CLK─┤          ├── Q̄     │  Q̄ = inverted stored value
  │                            │
  │  "When CLK rises, latch    │
  │   the value on D into Q"   │
  └────────────────────────────┘
  
  Built from ~6 transistors.
```

```
REGISTER (stores N bits):
  64 flip-flops wired in parallel = 64-bit register
  
  D[63] D[62] D[61] ... D[1] D[0]   ← inputs
   │     │     │          │    │
  [FF] [FF] [FF]  ...  [FF] [FF]    ← 64 flip-flops
   │     │     │          │    │
  Q[63] Q[62] Q[61] ... Q[1] Q[0]   ← outputs
  
  All connected to same CLK signal
  → All 64 bits latch simultaneously on each clock edge
```

### 2.2 Why Registers Are the Fastest Memory

```
MEMORY HIERARCHY (from fastest to slowest):

┌────────────────────────────────────────────────────────────┐
│  CPU REGISTERS        ~0.3 ns   (1 clock cycle at 3 GHz)  │
│  ~32 general purpose  ~32-256 bytes total                  │
│  LITERALLY INSIDE the ALU (Arithmetic Logic Unit)          │
├────────────────────────────────────────────────────────────┤
│  L1 CACHE             ~1 ns     (3-4 cycles)               │
│  ~32-64 KB            SRAM chips adjacent to CPU cores     │
├────────────────────────────────────────────────────────────┤
│  L2 CACHE             ~4 ns     (12 cycles)                │
│  ~256 KB - 4 MB       SRAM chips on CPU die                │
├────────────────────────────────────────────────────────────┤
│  L3 CACHE             ~12 ns    (30-40 cycles)             │
│  ~8-64 MB             Shared SRAM on CPU package           │
├────────────────────────────────────────────────────────────┤
│  RAM (DRAM)           ~60-100 ns  (200+ cycles)            │
│  ~GB to TB            DRAM chips on motherboard            │
├────────────────────────────────────────────────────────────┤
│  SSD (NVMe)           ~50 μs    (150,000 cycles!)          │
├────────────────────────────────────────────────────────────┤
│  HDD                  ~5-10 ms  (millions of cycles!)      │
└────────────────────────────────────────────────────────────┘

WHY registers are fastest:
  No address bus to traverse
  No cache lookup needed
  Physically adjacent to the ALU
  The CPU's execution units READ and WRITE registers
  as part of their native operation — they are the
  CPU's "working hands"
```

### 2.3 The CPU Registers on x86-64 — Complete Map

```
═══════════════════════════════════════════════════════════
GENERAL PURPOSE REGISTERS (64-bit, each)
═══════════════════════════════════════════════════════════

Each 64-bit register has sub-names for smaller views:

    63      31     15    8 7       0
    ┌───────────────────────────────┐
    │           RAX                │  64-bit (R = "Registers" prefix, A = Accumulator)
    └───────────────────────────────┘
             ┌──────────────────────┐
             │        EAX          │  32-bit (low 32 bits of RAX)
             └──────────────────────┘
                       ┌────────────┐
                       │    AX     │  16-bit (low 16 bits)
                       └────────────┘
                       ┌─────┐┌─────┐
                       │ AH  ││ AL  │  8-bit high, 8-bit low halves of AX
                       └─────┘└─────┘

This backwards compatibility exists because x86 started as 16-bit
(8086, 1978) → 32-bit (80386, 1985) → 64-bit (AMD64, 2003)
Each generation extended registers while keeping old names usable.

REGISTER  │ PURPOSE                          │ Caller/Callee Saved?
──────────┼──────────────────────────────────┼────────────────────
RAX       │ Return value / Accumulator       │ Caller saves
RBX       │ General purpose                  │ Callee saves
RCX       │ Function argument 4 / Counter    │ Caller saves
RDX       │ Function argument 3 / Data       │ Caller saves
RSI       │ Function argument 2 / Source Idx │ Caller saves
RDI       │ Function argument 1 / Dest Idx   │ Caller saves
RSP       │ Stack Pointer                    │ Callee saves (managed)
RBP       │ Base Pointer (frame pointer)     │ Callee saves
R8        │ Function argument 5              │ Caller saves
R9        │ Function argument 6              │ Caller saves
R10       │ General / syscall arg 4          │ Caller saves
R11       │ General / RFLAGS tmp             │ Caller saves
R12–R15   │ General purpose                  │ Callee saves

CALLER SAVES: Before calling a function, the CALLER must save these
              if it needs them after the call (callee may overwrite them)
CALLEE SAVES: The CALLED function must save and restore these before returning

═══════════════════════════════════════════════════════════
SPECIAL-PURPOSE REGISTERS
═══════════════════════════════════════════════════════════

RIP (Instruction Pointer):
  Always points to the NEXT instruction to execute
  You CANNOT directly write to it with MOV
  Changed by: CALL, RET, JMP, exceptions, interrupts
  ┌─────────────────────────────────────────────────────┐
  │ This is the most critical register for probing!     │
  │ kprobes/uprobes manipulate RIP to redirect execution│
  └─────────────────────────────────────────────────────┘

RFLAGS (Flags Register):
  Each BIT is an independent flag:
  
  Bit 0:  CF  Carry Flag       (arithmetic carry/borrow)
  Bit 2:  PF  Parity Flag      (even number of 1-bits in result)
  Bit 4:  AF  Auxiliary Carry  (BCD arithmetic)
  Bit 6:  ZF  Zero Flag        (result was zero)  ← used by JE, JZ
  Bit 7:  SF  Sign Flag        (result was negative)
  Bit 8:  TF  Trap Flag        (single-step mode! kprobes use this!)
  Bit 9:  IF  Interrupt Enable (1=interrupts enabled)
  Bit 10: DF  Direction Flag   (string ops direction)
  Bit 11: OF  Overflow Flag    (signed arithmetic overflow)

RSP (Stack Pointer):
  Points to the TOP of the current stack
  Stack GROWS DOWNWARD in x86
  PUSH instruction: RSP -= 8, then write value to [RSP]
  POP  instruction: read value from [RSP], then RSP += 8

RBP (Base Pointer / Frame Pointer):
  Points to the BASE of the current stack frame
  Used to access local variables and arguments by fixed offsets
  Optional — compilers can omit it with -fomit-frame-pointer

═══════════════════════════════════════════════════════════
SEGMENT REGISTERS (16-bit each, historical but still used)
═══════════════════════════════════════════════════════════

CS  Code Segment       ← contains CPL (current privilege level) in bits 0-1!
SS  Stack Segment
DS  Data Segment
ES  Extra Segment
FS  Thread-local storage (per-thread data pointer in Linux)
GS  Per-CPU data (in Linux kernel: points to per-CPU data structure!)

FS and GS are critically important:
  Linux user mode:    FS → thread-local storage (errno, etc.)
  Linux kernel mode:  GS → struct cpu_var (per-CPU kernel variables)

═══════════════════════════════════════════════════════════
CONTROL REGISTERS (Ring 0 only)
═══════════════════════════════════════════════════════════

CR0:  System Control
  Bit 0:  PE  Protected Mode Enable (1 = protected mode active)
  Bit 16: WP  Write Protect (1 = kernel can't write to read-only pages)
              ← kprobes temporarily clears this to patch code!
  Bit 31: PG  Paging Enable (1 = virtual memory active)

CR2:  Page Fault Linear Address
  When a page fault occurs, CPU stores the FAULTING ADDRESS here
  The page fault handler reads CR2 to know what address caused the fault

CR3:  Page Directory Base Register
  Stores the PHYSICAL ADDRESS of the top-level page table
  Writing to CR3 = switching address spaces (context switch!)
  KPTI (Meltdown fix) does this on every syscall!

CR4:  Feature Control
  Bit 5:  PAE   Physical Address Extension (>4GB RAM support)
  Bit 7:  PGE   Page Global Enable
  Bit 13: VMXE  VMX Enable (for hardware virtualization)

CR8 (= TPR): Task Priority Register
  Controls which interrupts are currently deliverable

═══════════════════════════════════════════════════════════
SIMD / FLOATING POINT REGISTERS
═══════════════════════════════════════════════════════════

x87 FPU:     ST(0)–ST(7)    80-bit extended precision (legacy)
MMX:         MM0–MM7        64-bit (aliases x87 registers)
SSE:         XMM0–XMM15    128-bit (can hold 4×float or 2×double)
AVX:         YMM0–YMM15    256-bit (extends XMM registers)
AVX-512:     ZMM0–ZMM31    512-bit (8×double, 16×float, etc.)

These are physical register files separate from the integer registers.
Context switch must save/restore ALL of these for the process.

═══════════════════════════════════════════════════════════
MODEL SPECIFIC REGISTERS (MSRs) — accessed via RDMSR/WRMSR
═══════════════════════════════════════════════════════════

MSR address 0xC0000082:  LSTAR — syscall entry point address
                         (where SYSCALL instruction jumps to in kernel!)

MSR address 0x10:        IA32_TIME_STAMP_COUNTER (RDTSC reads this)
MSR address 0x1B:        IA32_APIC_BASE (local APIC base address)
MSR address 0x277:       IA32_PAT (Page Attribute Table for caching)

There are THOUSANDS of MSRs. They configure everything from CPU power
management to branch prediction behavior to virtualization.
```

### 2.4 How the CPU Uses Registers — Instruction Execution Flow

```
INSTRUCTION: ADD RAX, RBX     (meaning: RAX = RAX + RBX)

This 3-byte instruction (48 01 D8 in machine code) executes as:

Step 1: FETCH
  RIP points to address 0x401020
  CPU reads bytes [48, 01, D8] from instruction cache
  RIP advances to 0x401023 (next instruction)

Step 2: DECODE
  Decoder unit interprets:
  48  = REX.W prefix (64-bit operands)
  01  = ADD opcode
  D8  = ModRM byte: source=RBX (reg 3), destination=RAX (reg 0)

Step 3: ISSUE / RENAME
  Out-of-order CPUs rename architectural registers to physical registers
  (the CPU has more physical registers than the 16 you see)
  Physical_reg_42 ← RAX mapping
  Physical_reg_17 ← RBX mapping (already has value)

Step 4: EXECUTE
  ALU reads physical_reg_42 and physical_reg_17
  Computes sum
  Updates RFLAGS (ZF, SF, CF, OF based on result)

Step 5: WRITEBACK
  Result written to the new physical register mapped to RAX
  Any waiting instructions that needed RAX can now proceed
```

### 2.5 Registers vs. Memory — The Fundamental Distinction

```
REGISTERS:                          MEMORY (RAM):
  Physical location: INSIDE CPU       Physical: DRAM chips, motherboard
  Count: 16-32 GP registers           Count: Billions of bytes
  Size: 64 bits each                  Cell size: 1 bit per DRAM cell
  Access time: 1 CPU cycle            Access time: 200+ CPU cycles
  Addressing: By name (RAX, RBX...)   Addressing: By numeric ADDRESS
  Persistence: Lost on context switch  Persistent across context switches
  Visibility: Per-CPU (each core      Shared: all CPUs share same RAM
              has its own registers)   (with cache coherency protocol)

CRITICAL INSIGHT:
  Your C variable `int x = 5;` starts in RAM.
  When you do `x + y`, the compiler emits:
    MOV EAX, [address_of_x]   ← load from RAM to register
    ADD EAX, [address_of_y]   ← add (may load y from RAM too)
    MOV [address_of_x], EAX   ← store result back to RAM
  
  The ACTUAL computation happens IN registers.
  Memory just stores the data between computations.
  The compiler's job is largely: decide which variables go in registers
  (register allocation) to minimize slow memory accesses.
```

### 2.6 What About "Memory-Mapped Registers" in Hardware?

You may have heard "memory-mapped I/O registers" or "device registers."
These are a DIFFERENT concept:

```
HARDWARE DEVICE REGISTERS:
  Physical registers inside peripheral chips (NIC, GPU, USB controller)
  NOT the same as CPU registers
  
  Accessed by the CPU via memory-mapped I/O (MMIO):
  The device's registers are mapped to specific PHYSICAL ADDRESSES
  Writing/reading those addresses sends data to/from the device.

  Example: Network Card (NIC)
    Physical address 0xFEBC0000 → NIC's Transmit Descriptor Base register
    Physical address 0xFEBC0008 → NIC's Receive Descriptor Base register
    
    Writing to 0xFEBC0000 doesn't write RAM — it sends that value
    directly to the NIC chip over the PCIe bus!
    
  In Linux kernel:
    void __iomem *bar = ioremap(0xFEBC0000, 0x1000);
    writel(tx_ring_phys_addr, bar + 0x00);  // "memory write" → NIC
    u32 status = readl(bar + 0x08);          // "memory read" ← NIC
```

### 2.7 The pt_regs Structure — Why It's Central to Probing

When a kprobe fires (via INT3 exception), the CPU saves ALL register
values to a `pt_regs` structure in memory. This is your snapshot:

```
BEFORE INT3:                     AFTER INT3 exception handler entry:
                                 
CPU executing normally           Stack (kernel stack of current thread):
RAX = 0x00000000_DEADBEEF        ┌──────────────┐
RBX = 0x00000000_00000001        │     SS       │  ← CPU pushed these
RCX = 0x00007FFF_FFFFE810        │     RSP      │     automatically
RIP = 0xFFFFFF80_12345678        │    RFLAGS    │
                                 │     CS       │
                                 │     RIP      │
                                 ├──────────────┤
                                 │ (error code) │  ← 0 for INT3
                                 ├──────────────┤
                                 │  R15...R11   │  ← kernel handler
                                 │  RAX...RDI   │     pushed these
                                 └──────────────┘
                                 
This memory area IS the pt_regs struct.
Your probe handler receives a pointer to it.
Modifying pt_regs->rax changes what RAX will be when execution resumes!
```

### 2.8 C Code — Reading and Writing Registers Directly

```c
// file: register_demo.c
// Demonstrates reading CPU registers from C (Linux x86-64)

#include <stdio.h>
#include <stdint.h>

/* ── Reading registers with inline assembly ── */

static inline uint64_t read_rsp(void)
{
    uint64_t val;
    /*
     * Extended inline assembly syntax:
     *   asm volatile ("instruction" : outputs : inputs : clobbers)
     *   "=r"(val) → output: any register, stored in val
     *   "r"(val)  → input:  any register, loaded with val
     *   "=m"(val) → output: memory location
     *   "memory"  → clobber: tells compiler memory may be read/written
     */
    asm volatile ("mov %%rsp, %0" : "=r"(val));
    return val;
}

static inline uint64_t read_rip(void)
{
    uint64_t val;
    /*
     * Trick: LEA (Load Effective Address) of the NEXT instruction's
     * address. RIP cannot be read directly with MOV.
     * "leaq 0(%%rip), %0" = load address of current instruction into val
     */
    asm volatile ("leaq 0(%%rip), %0" : "=r"(val));
    return val;
}

static inline uint64_t read_rflags(void)
{
    uint64_t val;
    /*
     * PUSHFQ: push RFLAGS onto stack
     * POP: pop into val
     */
    asm volatile ("pushfq; popq %0" : "=r"(val));
    return val;
}

static inline uint64_t read_tsc(void)
{
    /*
     * RDTSC: Read Time-Stamp Counter
     * Returns 64-bit cycle count since reset
     * Low 32 bits in EAX, high 32 bits in EDX
     * "=A" on 64-bit: NOT what you think (it's RAX only!)
     * Must use "=d" "=a" separately:
     */
    uint32_t lo, hi;
    asm volatile ("rdtsc" : "=a"(lo), "=d"(hi));
    return ((uint64_t)hi << 32) | lo;
}

/* ── Writing a register (controlled CPU flag manipulation) ── */

static inline void set_direction_flag(void)
{
    /* STD: Set Direction Flag (string ops go backward) */
    asm volatile ("std");
}

static inline void clear_direction_flag(void)
{
    /* CLD: Clear Direction Flag (string ops go forward) */
    asm volatile ("cld");
}

/* ── CPUID: Read CPU capabilities into registers ── */

typedef struct {
    uint32_t eax, ebx, ecx, edx;
} cpuid_result_t;

static cpuid_result_t cpuid(uint32_t leaf)
{
    cpuid_result_t r;
    /*
     * CPUID: input leaf in EAX, outputs in EAX, EBX, ECX, EDX
     * This is how you detect CPU features at runtime.
     */
    asm volatile (
        "cpuid"
        : "=a"(r.eax), "=b"(r.ebx), "=c"(r.ecx), "=d"(r.edx)
        : "a"(leaf)
        /* no clobbers beyond the explicit outputs */
    );
    return r;
}

int main(void)
{
    printf("=== CPU Register Demonstration ===\n\n");

    /* Stack pointer */
    uint64_t rsp = read_rsp();
    printf("RSP (stack pointer):  0x%016lx\n", rsp);
    printf("  → The stack currently lives around this address\n\n");

    /* Instruction pointer */
    uint64_t rip = read_rip();
    printf("RIP (instr pointer):  0x%016lx\n", rip);
    printf("  → This is approximately where we are in the .text section\n\n");

    /* CPU flags */
    uint64_t rflags = read_rflags();
    printf("RFLAGS:               0x%016lx\n", rflags);
    printf("  Interrupt Enable (IF): %s\n",
           (rflags & (1 << 9)) ? "ON" : "OFF");
    printf("  Direction Flag  (DF): %s\n",
           (rflags & (1 << 10)) ? "backward" : "forward");
    printf("  Trap Flag       (TF): %s\n",
           (rflags & (1 << 8)) ? "ON (single-step!)" : "OFF");
    printf("\n");

    /* Timestamp counter */
    uint64_t t1 = read_tsc();
    uint64_t t2 = read_tsc();
    printf("TSC cycles between two reads: %lu\n\n", t2 - t1);

    /* CPUID — CPU vendor string */
    cpuid_result_t vendor = cpuid(0);
    /* Vendor string is in EBX, EDX, ECX (in that order!) */
    char vendor_str[13];
    *(uint32_t*)(vendor_str + 0) = vendor.ebx;
    *(uint32_t*)(vendor_str + 4) = vendor.edx;
    *(uint32_t*)(vendor_str + 8) = vendor.ecx;
    vendor_str[12] = '\0';
    printf("CPU Vendor: %s\n", vendor_str);
    printf("  (GenuineIntel or AuthenticAMD)\n\n");

    /* CPUID leaf 1: feature flags */
    cpuid_result_t feat = cpuid(1);
    printf("CPU Feature flags (leaf 1):\n");
    printf("  SSE2:   %s\n", (feat.edx & (1 << 26)) ? "YES" : "NO");
    printf("  AVX:    %s\n", (feat.ecx & (1 << 28)) ? "YES" : "NO");
    printf("  RDRAND: %s\n", (feat.ecx & (1 << 30)) ? "YES" : "NO");

    return 0;
}
```

### 2.9 Rust Code — Safe Register Access

```rust
// file: src/registers.rs
// Reading CPU state from Rust — safe abstractions over unsafe assembly

use std::arch::asm;

/// Read the current stack pointer value.
/// Useful for understanding stack depth, detecting stack overflows.
#[inline(always)]
pub fn read_rsp() -> u64 {
    let val: u64;
    // SAFETY: Reading RSP is always safe — it's just our own stack pointer.
    unsafe {
        asm!("mov {}, rsp", out(reg) val, options(nomem, nostack, preserves_flags));
    }
    val
}

/// Read the current timestamp counter (CPU cycle counter).
/// Use for ultra-precise timing measurements.
/// Note: Not ordered relative to other instructions — use LFENCE for accuracy.
#[inline(always)]
pub fn rdtsc() -> u64 {
    let lo: u32;
    let hi: u32;
    // SAFETY: RDTSC is always available on x86-64, non-privileged.
    unsafe {
        asm!(
            "rdtsc",
            out("eax") lo,
            out("edx") hi,
            options(nomem, nostack, preserves_flags)
        );
    }
    ((hi as u64) << 32) | (lo as u64)
}

/// Serialize instruction stream, then read TSC.
/// For accurate timing: prevents out-of-order execution from skewing results.
#[inline(always)]
pub fn rdtscp() -> (u64, u32) {
    let lo: u32;
    let hi: u32;
    let core_id: u32;  // which CPU core we're on (in ECX)
    unsafe {
        asm!(
            "rdtscp",
            out("eax") lo,
            out("edx") hi,
            out("ecx") core_id,
            options(nomem, nostack, preserves_flags)
        );
    }
    (((hi as u64) << 32) | (lo as u64), core_id)
}

/// CPUID result for a given leaf
#[derive(Debug)]
pub struct CpuidResult {
    pub eax: u32,
    pub ebx: u32,
    pub ecx: u32,
    pub edx: u32,
}

pub fn cpuid(leaf: u32) -> CpuidResult {
    let eax: u32;
    let ebx: u32;
    let ecx: u32;
    let edx: u32;
    unsafe {
        asm!(
            "cpuid",
            inout("eax") leaf => eax,
            out("ebx") ebx,
            out("ecx") ecx,
            out("edx") edx,
            options(nomem, nostack)
        );
    }
    CpuidResult { eax, ebx, ecx, edx }
}

/// Measure nanoseconds using TSC + calibrated frequency
pub struct TscTimer {
    tsc_hz: u64,  // TSC ticks per second
}

impl TscTimer {
    pub fn new() -> Self {
        // In production: read from CPUID leaf 0x15 or calibrate against wall clock
        // For demo: assume 3 GHz
        TscTimer { tsc_hz: 3_000_000_000 }
    }

    pub fn start(&self) -> u64 {
        // Fence to prevent CPU reordering measurements
        unsafe { asm!("lfence", options(nomem, nostack, preserves_flags)); }
        rdtsc()
    }

    pub fn elapsed_ns(&self, start_tsc: u64) -> u64 {
        unsafe { asm!("lfence", options(nomem, nostack, preserves_flags)); }
        let end = rdtsc();
        let delta = end.saturating_sub(start_tsc);
        // Convert TSC ticks to nanoseconds:
        // ns = ticks * (1_000_000_000 / tsc_hz)
        //    = ticks * 1_000_000_000 / tsc_hz
        delta.saturating_mul(1_000_000_000) / self.tsc_hz
    }
}

fn main() {
    // Vendor string
    let leaf0 = cpuid(0);
    let mut vendor = [0u8; 12];
    vendor[0..4].copy_from_slice(&leaf0.ebx.to_le_bytes());
    vendor[4..8].copy_from_slice(&leaf0.edx.to_le_bytes());
    vendor[8..12].copy_from_slice(&leaf0.ecx.to_le_bytes());
    println!("CPU Vendor: {}", std::str::from_utf8(&vendor).unwrap_or("?"));

    // Feature detection
    let leaf1 = cpuid(1);
    println!("AVX support:    {}", if leaf1.ecx & (1 << 28) != 0 { "YES" } else { "NO" });
    println!("RDRAND support: {}", if leaf1.ecx & (1 << 30) != 0 { "YES" } else { "NO" });

    // Stack pointer — notice it changes as we call functions!
    println!("\nStack pointer: 0x{:016x}", read_rsp());

    // Timing precision
    let timer = TscTimer::new();
    let t0 = timer.start();
    let _ = (0..1000u64).sum::<u64>();  // some work
    let ns = timer.elapsed_ns(t0);
    println!("1000 iterations took ~{} ns", ns);
}
```

---

## 3. What Are Hooks?

### 3.1 The Core Concept — The Observer Pattern in Hardware/OS

A **hook** is a mechanism that lets you insert your own code into an
existing execution flow, **without modifying the original code**.

The name comes from the physical image: you "hook" onto a chain and run
when the chain moves.

```
EXECUTION FLOW WITHOUT HOOK:
  A ──────────────> B ──────────────> C
  
  A executes, then B executes, then C executes.
  You are an observer standing beside the road — you can't do anything.

EXECUTION FLOW WITH HOOK:
  A ──────────────> B ──→ [YOUR CODE] ──→ B continues ──────> C
                          (hook fires)
                          
  When execution reaches B, YOUR code runs FIRST (or after, or instead).
  You can:
    - OBSERVE: log what's happening
    - MODIFY: change arguments, return values
    - REDIRECT: jump somewhere else entirely
    - BLOCK: prevent B from executing
```

Hooks exist at **every layer of the computing stack**. Let's go from
hardware to application:

---

### 3.2 Layer 1: Hardware Hooks — Exception/Interrupt Vectors

The CPU has a hardware hook mechanism called the **Interrupt Descriptor
Table (IDT)**. It has 256 entries, each saying:
*"When event N occurs, jump to this address."*

```
IDT (Interrupt Descriptor Table):
┌──────┬───────────────────────────────────────────────────┐
│ #0   │ Divide Error handler address                      │
│ #1   │ Debug Exception handler address ← kprobe uses!   │
│ #2   │ NMI (Non-Maskable Interrupt) handler              │
│ #3   │ Breakpoint (INT3) handler ← kprobe entry point!  │
│ #4   │ Overflow handler                                  │
│ #5   │ BOUND Range Exceeded                              │
│ #6   │ Invalid Opcode handler                            │
│ #7   │ Device Not Available (x87 FPU)                    │
│ #8   │ Double Fault handler                              │
│ #13  │ General Protection Fault                          │
│ #14  │ Page Fault handler ← called on memory access fault│
│ ...  │ ...                                               │
│ #32  │ Hardware IRQ 0 (timer interrupt) ← scheduler!    │
│ #33  │ Hardware IRQ 1 (keyboard)                         │
│ ...  │ ...                                               │
│ #128 │ int 0x80 system call (legacy 32-bit syscalls)     │
│ #255 │ Last IRQ                                          │
└──────┴───────────────────────────────────────────────────┘

This IS a hook table: events hook into handlers.
When you install a kprobe, you're using the #3 (INT3) hook.
```

**Visual: Page Fault Hook — the most used hardware hook**

```
Program accesses memory at virtual address 0x7fff00001000
  │
  │ CPU's Memory Management Unit (MMU) checks page tables
  │ → Page not mapped (or not present, or wrong permissions)
  │
  ▼
CPU raises exception #14 (Page Fault)
  │
  ├── Saves registers on kernel stack
  ├── Puts faulting address in CR2 register
  └── Jumps to IDT[14] = page_fault_handler()
  
page_fault_handler():
  ├── Was it a valid mapping? (stack growth, demand paging)
  │     YES → allocate page, map it, return (transparent to program!)
  ├── Was it a NULL pointer dereference?
  │     YES → send SIGSEGV to process
  ├── Was it a kernel bug?
  │     YES → OOPS! (kernel bug report)
  └── Was it a uprobe's XOL slot?
        YES → handle single-step completion

The page fault handler IS a hook — it intercepts all invalid memory
accesses and can handle them transparently.
```

---

### 3.3 Layer 2: Kernel Hooks — Linux Notification Chains

The Linux kernel has a software hook system called **Notifier Chains**:

```c
// A notifier chain = a linked list of callback functions
// Any kernel subsystem can register to be called when an event fires

// EXAMPLE: CPU hotplug notifier
// When you add/remove a CPU (or power management changes core state):

static int my_cpu_callback(struct notifier_block *nb,
                            unsigned long action,
                            void *hcpu)
{
    unsigned int cpu = (unsigned long)hcpu;
    switch (action) {
    case CPU_ONLINE:
        printk("CPU %u just came ONLINE\n", cpu);
        break;
    case CPU_DEAD:
        printk("CPU %u just went OFFLINE\n", cpu);
        break;
    }
    return NOTIFY_OK;
}

static struct notifier_block my_nb = {
    .notifier_call = my_cpu_callback,
    .priority = 0,  // lower = called later in the chain
};

// Register the hook:
register_cpu_notifier(&my_nb);
// From now on, my_cpu_callback is called whenever a CPU changes state

// Unregister:
unregister_cpu_notifier(&my_nb);
```

**Other Linux notifier chains:**

```
Notifier chain:               Fires when:
─────────────────────────────────────────────────────────────
cpu_chain                   CPU hotplug events
inetaddr_chain              IPv4 address added/removed
inet6addr_chain             IPv6 address added/removed
netdev_chain                Network interface up/down/renamed
reboot_notifier_list        System is rebooting
panic_notifier_list         Kernel panic is occurring
usb_notifier_list           USB device plugged/unplugged
fb_notifier_list            Framebuffer events (display changes)
```

---

### 3.4 Layer 3: Kernel Hooks — Linux Security Modules (LSM)

This is one of the most important hook systems in Linux:

```
SECURITY HOOK POINTS (selected, there are 200+):

security_inode_create()     ← fires when creating a file
security_inode_unlink()     ← fires when deleting a file
security_socket_connect()   ← fires when a program calls connect()
security_bprm_check()       ← fires when exec()ing a program
security_ptrace_access_check() ← fires when a process tries to debug another
security_file_open()        ← fires on every open()
security_socket_sendmsg()   ← fires on every network send

SELinux and AppArmor ARE JUST LSM HOOK IMPLEMENTATIONS.
They register handlers for these hooks.
When "selinux denies access", it returned -EACCES from an LSM hook.
```

```c
// Simplified view of how a security hook is called:

// In the kernel's sys_openat() implementation:
long do_sys_openat2(int dfd, const char __user *filename, struct open_how *how)
{
    // ... setup code ...
    
    // HOOK POINT: call all registered security modules
    error = security_file_open(f);
    // security_file_open() calls EACH registered LSM:
    //   SELinux checks: does this process's security context
    //                   have permission to open this inode?
    //   AppArmor checks: does the profile allow this path?
    //   Both say OK → error = 0
    //   Either says DENY → error = -EACCES (or -EPERM)
    
    if (error) {
        // file BLOCKED by security hook
        return error;
    }
    // ... continue opening the file ...
}
```

---

### 3.5 Layer 4: System Call Hooks

System calls are themselves hooks between user and kernel space:

```
USER SPACE                          KERNEL SPACE
─────────────────────────────────────────────────────────────
int fd = open("/etc/passwd", O_RDONLY);
         │
         │  SYSCALL instruction (x86-64)
         │  or SVC (ARM64)
         │
         │  CPU:
         │    1. Save RIP, RFLAGS, RSP
         │    2. Switch to kernel stack
         │    3. Jump to LSTAR MSR address
         │       (= entry_SYSCALL_64 in Linux)
         │
         ▼
         entry_SYSCALL_64:
           Save all registers (creates pt_regs on stack)
           Look up syscall number in sys_call_table[]
           sys_call_table[2] = sys_openat  ← open() is syscall #2
           CALL sys_openat(pt_regs)
                │
                ▼
                do_sys_openat2(...)
                [security hooks fire here]
                [kprobes fire here]
                [tracepoints fire here]
                ...actual work...
                return fd_number
           
           Restore registers
           SYSRET instruction (back to user space)
         
         ▼
         RAX = fd_number (the new file descriptor)
```

---

### 3.6 Layer 5: Dynamic Binary Instrumentation Hooks (DBI)

Tools like **Valgrind**, **DynamoRIO**, **Pin** work at the binary level:

```
NORMAL EXECUTION:
  Your binary's instructions execute directly on CPU

DBI EXECUTION:
  DBI tool intercepts execution
  Disassembles your binary's code
  Injects its own "instrumentation" instructions before/after each block
  JIT-recompiles the modified code into a "code cache"
  Executes the code cache (instrumented version)

  Your code:              DBI's code cache:
  ┌─────────────┐        ┌──────────────────────────┐
  │ MOV EAX, 1  │  →     │ CALL dbi_before_handler  │
  │ ADD EBX, 2  │        │ MOV EAX, 1               │
  │ RET         │        │ CALL dbi_after_handler   │
  └─────────────┘        │ CALL dbi_before_handler  │
                         │ ADD EBX, 2               │
                         │ CALL dbi_after_handler   │
                         │ CALL dbi_ret_handler     │
                         │ RET                      │
                         └──────────────────────────┘

Valgrind's memcheck hooks EVERY MEMORY ACCESS this way:
  → Before each load/store, check if address is valid
  → 20-40x slowdown (because every instruction is monitored)
```

---

### 3.7 Layer 6: Library Interposition Hooks (LD_PRELOAD)

```bash
# This is a userspace hook mechanism using the dynamic linker

# The dynamic linker resolves library function names at runtime.
# LD_PRELOAD lets you insert YOUR library FIRST in the search order.

# Example: intercept ALL malloc() calls

# my_malloc.c:
# #include <stdio.h>
# void *malloc(size_t size) {          // OUR malloc
#     printf("malloc(%zu) called\n", size);
#     // call the real malloc:
#     extern void *__libc_malloc(size_t);
#     return __libc_malloc(size);
# }
#
# gcc -shared -fPIC -o my_malloc.so my_malloc.c

LD_PRELOAD=./my_malloc.so /usr/bin/ls

# Now EVERY call to malloc() from ls (and its libraries)
# goes through OUR function first!
```

```
NORMAL DYNAMIC LINKING:          WITH LD_PRELOAD:
  
  program calls malloc()          program calls malloc()
        │                               │
        ▼                               ▼
  libc's malloc()              my_malloc.so's malloc()
  (from /lib/libc.so.6)              │ (OUR HOOK!)
                                      │
                                      ▼
                               libc's __libc_malloc()
                               (we chose to forward it)
```

Real-world uses of LD_PRELOAD:
- **jemalloc / tcmalloc**: replace glibc malloc with faster allocators
- **Address Sanitizer (ASan)**: intercept allocations to detect overflows
- **strace alternatives**: intercept syscall wrappers
- **faketime**: intercept `time()` and `gettimeofday()` to lie about the time
- **libSegFault**: produce better stack traces on segfault

---

### 3.8 Layer 7: Application-Level Hooks (Event Systems, Callbacks)

```c
// ── C: Signal Handlers (Unix process hooks) ──

#include <signal.h>
#include <stdio.h>

// The OS "hooks" into signal delivery:
// When the kernel wants to notify a process (Ctrl+C, segfault, etc.)
// it looks up that process's registered signal handler

void my_sigint_handler(int sig)  // OUR hook
{
    printf("\nCaught SIGINT! Doing cleanup...\n");
    // sig = 2 (SIGINT)
    // We can: clean up files, save state, then exit
    // OR: ignore it (but Ctrl+C won't terminate the program then!)
    _exit(0);  // must use _exit, not exit, from signal handler
}

int main(void)
{
    // Register our hook for SIGINT (Ctrl+C):
    signal(SIGINT, my_sigint_handler);
    
    // More powerful version (sigaction):
    struct sigaction sa = {
        .sa_handler = my_sigint_handler,
        .sa_flags   = SA_RESTART,  // restart interrupted syscalls
    };
    sigemptyset(&sa.sa_mask);
    sigaction(SIGINT, &sa, NULL);  // NULL = don't save old handler
    
    printf("Running. Press Ctrl+C to test the hook.\n");
    while (1) { pause(); }  // wait for signal
    return 0;
}
```

```rust
// ── Rust: Function Hooks via Trait Objects (Observer Pattern) ──

// Real-world example: a web server with middleware hooks
// Middleware = hooks that fire on every HTTP request/response

trait RequestHook: Send + Sync {
    fn before_request(&self, path: &str, method: &str);
    fn after_response(&self, path: &str, status_code: u16, duration_ms: u64);
}

// Hook 1: Logging hook
struct LoggingHook;
impl RequestHook for LoggingHook {
    fn before_request(&self, path: &str, method: &str) {
        println!("[LOG] {} {}", method, path);
    }
    fn after_response(&self, path: &str, status_code: u16, duration_ms: u64) {
        println!("[LOG] {} → {} ({}ms)", path, status_code, duration_ms);
    }
}

// Hook 2: Rate limiter hook
struct RateLimiterHook {
    max_rps: u32,
}
impl RequestHook for RateLimiterHook {
    fn before_request(&self, path: &str, _method: &str) {
        // Would check rate limit and potentially block
        println!("[RATE] Checking limit for {}", path);
    }
    fn after_response(&self, _path: &str, _status_code: u16, _duration_ms: u64) {}
}

// Hook 3: Metrics hook
struct MetricsHook;
impl RequestHook for MetricsHook {
    fn before_request(&self, _path: &str, _method: &str) {}
    fn after_response(&self, path: &str, status_code: u16, duration_ms: u64) {
        println!("[METRICS] path={} status={} latency_ms={}", 
                 path, status_code, duration_ms);
    }
}

// The "server" that owns the hook chain
struct Server {
    // Vec of trait objects: each is a different hook type,
    // but stored uniformly. This is the "hook chain".
    hooks: Vec<Box<dyn RequestHook>>,
}

impl Server {
    fn new() -> Self {
        Server { hooks: Vec::new() }
    }
    
    fn register_hook(&mut self, hook: Box<dyn RequestHook>) {
        self.hooks.push(hook);
    }
    
    fn handle_request(&self, path: &str, method: &str) {
        // Fire ALL "before" hooks in order
        for hook in &self.hooks {
            hook.before_request(path, method);
        }
        
        // ... actual request handling (the "original function") ...
        let status_code = 200u16;
        let duration_ms = 42u64;
        
        // Fire ALL "after" hooks in order
        for hook in &self.hooks {
            hook.after_response(path, status_code, duration_ms);
        }
    }
}

fn main() {
    let mut server = Server::new();
    
    // Register hooks — ORDER MATTERS (rate limiter before logger)
    server.register_hook(Box::new(RateLimiterHook { max_rps: 1000 }));
    server.register_hook(Box::new(LoggingHook));
    server.register_hook(Box::new(MetricsHook));
    
    // Process requests — all hooks fire automatically
    server.handle_request("/api/users", "GET");
    server.handle_request("/api/orders", "POST");
}
```

---

### 3.9 Hook Summary — The Mental Model

```
HOOKS BY LAYER:

Layer       │ Mechanism          │ Who Calls Hook    │ Example Use
────────────┼────────────────────┼───────────────────┼──────────────────
Hardware    │ IDT entries        │ CPU hardware      │ Breakpoints, IRQs
Kernel/HW   │ kprobes/uprobes    │ CPU via INT3      │ Dynamic tracing
Kernel soft │ LSM hooks          │ Kernel subsystem  │ SELinux, AppArmor
Kernel soft │ Notifier chains    │ Kernel subsystem  │ CPU hotplug events
Kernel soft │ Tracepoints        │ Kernel source     │ ftrace, perf events
Dynamic lib │ LD_PRELOAD         │ Dynamic linker    │ Replace malloc
Process     │ Signal handlers    │ Kernel → process  │ Ctrl+C handling
Language    │ Callbacks/closures │ Your code         │ Sort comparator
Framework   │ Middleware         │ Framework         │ HTTP auth, logging
OS syscall  │ ptrace             │ Kernel            │ strace, debuggers

All hooks share one property:
  "Insert yourself into a flow of execution you didn't write,
   without modifying the original code."
```

---

## 4. What Is Out-of-Bounds Memory Access?

### 4.1 First: How Memory Is Organized for a Program

Every running process has its own virtual address space.
Each variable, array, struct has a specific location in this space.

```
ARRAY IN MEMORY (conceptual):

int arr[5] = {10, 20, 30, 40, 50};

In memory (each int = 4 bytes on x86-64):

Address:  0x1000  0x1004  0x1008  0x100C  0x1010
           ┌────┐  ┌────┐  ┌────┐  ┌────┐  ┌────┐
Values:    │ 10 │  │ 20 │  │ 30 │  │ 40 │  │ 50 │
           └────┘  └────┘  └────┘  └────┘  └────┘
Index:    [0]     [1]     [2]     [3]     [4]
          ↑ arr[0]                         ↑ arr[4] — LAST VALID

arr[5] would be at address 0x1014 — OUT OF BOUNDS!
Whatever lives there is NOT part of this array.
Could be: another variable, stack frame data, return address, ANYTHING.
```

### 4.2 What "Out of Bounds" Means — The Three Scenarios

```
SCENARIO 1: READ out of bounds

int arr[5] = {10, 20, 30, 40, 50};
int x = arr[7];  // arr[7] is at offset +28 bytes from arr start

What actually happens:
  CPU computes address: &arr[0] + 7*4 = 0x1000 + 28 = 0x101C
  CPU reads 4 bytes from 0x101C
  0x101C might contain: garbage, another variable's value, 0, anything

DANGER: You're reading data that doesn't belong to this array.
  If that "something" is a password or crypto key → SECURITY LEAK!
  
Real-world example: Heartbleed (OpenSSL 2014)
  The attacker sent a "heartbeat" request claiming to be 64KB of data
  but only sent 1 byte. OpenSSL read 64KB back (out of bounds).
  This leaked server memory containing private keys, passwords, sessions.

────────────────────────────────────────────────────────────────────

SCENARIO 2: WRITE out of bounds — the most dangerous

int arr[5] = {10, 20, 30, 40, 50};
arr[7] = 9999;  // WRITE to invalid location!

Stack layout (simplified, growing downward):
  High addresses
  ┌───────────────────────────────────┐
  │        return address             │ ← if attacker overwrites this,
  │        (where to go after RET)    │   they control execution!
  ├───────────────────────────────────┤
  │        saved RBP                  │
  ├───────────────────────────────────┤
  │   arr[4] arr[3] arr[2] arr[1] arr[0] │ ← allocated here
  ├───────────────────────────────────┤
  │        (local variables)          │
  └───────────────────────────────────┘
  Low addresses

arr[7] lands in "saved RBP" or "return address" zone!
Writing to arr[7] = attacker_controlled_value → return address overwritten
When function returns: CPU jumps to attacker_controlled_value!

This is STACK BUFFER OVERFLOW — used in exploits for 40+ years.

────────────────────────────────────────────────────────────────────

SCENARIO 3: NULL pointer dereference (special case of OOB)

int *ptr = NULL;  // ptr = 0x000...000
int x = *ptr;     // read from address 0x0000000000000000

Linux maps the first few pages (0x0 to 0x10000) as INVALID on purpose.
Accessing NULL → page fault → SIGSEGV (segmentation fault).
This is "out of bounds" for the NULL address range.
```

### 4.3 C Code — Demonstrating OOB Access

```c
// file: oob_demo.c
// WARNING: This demonstrates undefined behavior — educational purposes only

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void demonstrate_oob_read(void)
{
    int arr[5] = {1, 2, 3, 4, 5};
    int secret = 0xDEADBEEF;  // sits ADJACENT to arr on stack
    
    printf("arr   is at: %p\n", (void*)arr);
    printf("secret is at: %p\n", (void*)&secret);
    printf("Distance: %ld bytes\n", (char*)&secret - (char*)arr);
    
    // In-bounds access (safe):
    printf("\nIn-bounds:  arr[0]=%d arr[4]=%d\n", arr[0], arr[4]);
    
    // Out-of-bounds read — UNDEFINED BEHAVIOR but often "works":
    // The compiler may place `secret` right after `arr` on the stack.
    // This LEAKS the value of `secret` without ever naming it!
    printf("OOB read:   arr[5]=%d (might be %d = 0x%X)\n",
           arr[5], arr[5], arr[5]);
    // ^ On many systems this prints 0xDEADBEEF — you leaked `secret`!
}

void demonstrate_heap_oob(void)
{
    // Heap allocation
    int *buf = malloc(5 * sizeof(int));
    if (!buf) return;
    
    for (int i = 0; i < 5; i++) buf[i] = i * 10;
    
    printf("\nHeap buffer at: %p\n", (void*)buf);
    printf("malloc metadata usually lives BEFORE this address\n");
    
    // What's at buf[-1]? (before the allocation)
    // → malloc's chunk header! Writing here corrupts the heap.
    printf("buf[-1] = 0x%X (heap metadata?)\n", ((unsigned int*)buf)[-1]);
    
    // buf[5] through buf[127] might be in another malloc chunk's data
    // Writing there corrupts another allocation!
    
    free(buf);
}

void demonstrate_oob_consequence(void)
{
    char password[8] = "secret!";  // 7 chars + null byte = 8 bytes
    int  is_authenticated = 0;     // sits adjacent to password on stack
    
    printf("\npassword address:       %p\n", (void*)password);
    printf("is_authenticated addr:  %p\n", (void*)&is_authenticated);
    
    // Simulating a buffer overflow: attacker input doesn't respect bounds
    // strcpy does NOT check bounds! This is why it's deprecated.
    char attacker_input[16] = "AAAAAAAAAAAAAAAA";  // 16 'A's
    
    printf("\nBefore overflow: is_authenticated = %d\n", is_authenticated);
    
    // Intentionally demonstrating the vulnerability:
    memcpy(password, attacker_input, 12);  // copies 12 bytes into 8-byte buffer!
    // The extra 4 bytes overflow into is_authenticated!
    
    printf("After overflow:  is_authenticated = %d\n", is_authenticated);
    // On most systems, is_authenticated is now non-zero → "authenticated"!
}

int main(void)
{
    demonstrate_oob_read();
    demonstrate_heap_oob();
    demonstrate_oob_consequence();
    return 0;
}
```

### 4.4 Rust — How It Prevents OOB

```rust
// file: src/oob_rust.rs
// Rust's approach: CHECK bounds at compile time (if possible) or runtime

fn main() {
    let arr = [1i32, 2, 3, 4, 5];

    // ── Compile-time bounds checking (zero cost) ──
    let x = arr[2];  // compiler KNOWS arr has 5 elements, index 2 is valid
    println!("arr[2] = {}", x);

    // ── Runtime bounds checking ──
    // arr[7] in Rust does NOT do silent OOB read!
    // It panics with: "index out of bounds: the len is 5 but the index is 7"
    // This is SAFE (program terminates) vs C's UNDEFINED BEHAVIOR (security hole)
    //
    // UNCOMMENT TO SEE:
    // let bad = arr[7];  // → panic! "index out of bounds"

    // ── Safe access with Option (the idiomatic Rust way) ──
    let index = 7usize;
    match arr.get(index) {
        Some(value) => println!("arr[{}] = {}", index, value),
        None => println!("arr[{}] is out of bounds (len={})", index, arr.len()),
    }
    // No crash, no UB — you handle the None case explicitly

    // ── Unsafe: bypassing Rust's bounds checks ──
    // Sometimes needed for performance (when YOU guarantee correctness)
    unsafe {
        // arr.get_unchecked(N): NO bounds check, NO panic
        // If index is truly OOB: UNDEFINED BEHAVIOR (same as C)
        // YOU are responsible. The compiler trusts you.
        let val = arr.get_unchecked(2);  // safe here: we know 2 < 5
        println!("Unchecked arr[2] = {}", val);
        
        // This would be UB (but we won't actually do it):
        // let danger = arr.get_unchecked(7);  // Undefined Behavior!
    }

    // ── Slices and iterators — the OOB-free way to process arrays ──
    // Always prefer iterators over index loops in Rust
    let sum: i32 = arr.iter().sum();
    println!("Sum = {}", sum);

    // If you MUST use indices, use the safe iterator with enumerate:
    for (i, val) in arr.iter().enumerate() {
        println!("arr[{}] = {}", i, val);  // i is always valid
    }

    // ── Memory safety with Vec ──
    let mut v: Vec<i32> = Vec::with_capacity(5);
    for i in 0..5 { v.push(i * 10); }

    // Heap OOB in C → heap corruption (silent, devastating)
    // Heap OOB in Rust → panic (loud, safe)
    // v[10] would panic with "index out of bounds: the len is 5 but index is 10"
}
```

---

## 5. What Is Unsafe Pointer Arithmetic?

### 5.1 What Is a Pointer?

Before "unsafe pointer arithmetic," you must deeply understand **pointers**.

A **pointer** is a variable that stores a **memory address** rather than data.

```
REGULAR VARIABLE:
  int x = 42;
  
  Variable 'x' is at some address (say 0x7FFF1000)
  It contains the VALUE 42.
  
  Address 0x7FFF1000: [0x00] [0x00] [0x00] [0x2A]   ← 42 in little-endian hex
  
POINTER VARIABLE:
  int *ptr = &x;  // ptr stores the ADDRESS of x
  
  Variable 'ptr' is at some address (say 0x7FFF1008)
  It contains the ADDRESS 0x7FFF1000 (where x lives).
  
  Address 0x7FFF1008: [0x00] [0x10] [0xFF] [0x7F] [0x00] [0x00] [0x00] [0x00]
                        ← 0x00007FFF00001000 in little-endian 64-bit
  
DEREFERENCING:
  *ptr = reading/writing the value AT the address stored in ptr
  *ptr → goes to address 0x7FFF1000 → reads 42
  *ptr = 99 → goes to address 0x7FFF1000 → writes 99 (changes x!)
```

### 5.2 What Is Pointer Arithmetic?

C allows you to do math on pointers:

```c
int arr[5] = {10, 20, 30, 40, 50};
int *ptr = arr;  // ptr points to arr[0], address = say 0x1000

// Pointer arithmetic: adding an integer to a pointer
// MOVES the pointer by (n * sizeof(element)) bytes
ptr + 1;  // address 0x1000 + 1*sizeof(int) = 0x1000 + 4 = 0x1004
ptr + 2;  // address 0x1008
ptr + 4;  // address 0x1010 (arr[4])
ptr + 5;  // address 0x1014 — ONE PAST THE END (defined but not dereferenceable)
ptr + 6;  // address 0x1018 — UNDEFINED BEHAVIOR

*(ptr + 2) = *ptr + 2 = arr[2] = 30  ← these are equivalent

// Pointer subtraction: distance between two pointers (in elements, not bytes)
int *p1 = &arr[1];  // 0x1004
int *p2 = &arr[4];  // 0x1010
ptrdiff_t diff = p2 - p1;  // = (0x1010 - 0x1004) / sizeof(int) = 3
```

### 5.3 What Makes Pointer Arithmetic "Unsafe"?

```
SAFE pointer arithmetic:
  Staying within the bounds of the originally allocated object.
  
  int arr[5];
  int *p = arr;
  *(p + 0) through *(p + 4)  ← SAFE (within arr)
  (p + 5)  ← one-past-end pointer is DEFINED (but don't dereference)

UNSAFE pointer arithmetic (causes UB):
  Going beyond the allocated object's bounds
  Going to a completely unrelated address
  Using a pointer after the object is freed
  Computing a pointer below the start of the object
  
Examples of UNSAFE:
  *(p + 6)      ← past end of array, UB
  *(p - 1)      ← before array start, UB
  (long)p + 8   ← casting pointer to integer and back (problematic)
  p = (int*)(uintptr_t)0xDEADBEEF; *p = 1;  ← random address, UB
```

### 5.4 Why Is It Dangerous?

```
The C abstract machine has NO concept of "memory layout at runtime."
C's specification says: pointer arithmetic outside an object = UNDEFINED BEHAVIOR.

Undefined Behavior means:
  The C standard places NO REQUIREMENTS on what the program does.
  The compiler can assume UB never happens → optimize based on that assumption.
  At runtime: anything can happen.

REAL CONSEQUENCES:
┌─────────────────────────────────────────────────────────────┐
│ 1. Reads garbage / writes to wrong location                 │
│    → data corruption, security leaks                        │
├─────────────────────────────────────────────────────────────┤
│ 2. Corrupts adjacent data structures                        │
│    → linked list node overwritten → traversal loops forever │
├─────────────────────────────────────────────────────────────┤
│ 3. Overwrites return address on stack                       │
│    → attacker redirects execution (ROP attacks)             │
├─────────────────────────────────────────────────────────────┤
│ 4. Overwrites function pointer in struct                    │
│    → vtable corruption → attacker controls virtual dispatch │
├─────────────────────────────────────────────────────────────┤
│ 5. Compiler optimizes AWAY safety checks (because it        │
│    assumes UB can't happen)                                 │
│    Example: if (ptr != NULL) { ... } becomes just { ... }   │
│    because compiler proved ptr was used before (can't be    │
│    NULL if previous use was valid), so removes NULL check   │
└─────────────────────────────────────────────────────────────┘
```

### 5.5 C Code — The Perils of Pointer Arithmetic

```c
// file: pointer_arith_demo.c

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

/* ── Example 1: Type Punning (reinterpreting bytes) ── */
void type_punning_demo(void)
{
    float f = 3.14159f;
    
    // UNSAFE: casting pointer type to read the same bytes differently
    // Violates strict aliasing rules in C (UB in standard C)
    // BUT: commonly used in systems code for specific purposes
    
    // The SAFE way to do this is memcpy:
    uint32_t bits;
    memcpy(&bits, &f, sizeof(bits));
    printf("3.14159f as uint32: 0x%08X\n", bits);
    // IEEE 754: 0x40490FDB
    
    // UNSAFE way (technically UB but works on most compilers with -fno-strict-aliasing):
    uint32_t *bits_ptr = (uint32_t*)&f;  // pointer cast
    printf("Via pointer cast (UB): 0x%08X\n", *bits_ptr);
}

/* ── Example 2: Walking Through a Struct ── */
struct point { int x; int y; };

void struct_pointer_demo(void)
{
    struct point p = { .x = 10, .y = 20 };
    
    // SAFE: access via struct members
    printf("p.x=%d, p.y=%d\n", p.x, p.y);
    
    // QUESTIONABLE: treating struct as an array of ints
    // Technically UB (padding could exist between x and y)
    // But on most ABI-conforming platforms, int* arithmetic "works"
    int *ptr = (int*)&p;
    printf("ptr[0]=%d, ptr[1]=%d\n", ptr[0], ptr[1]);
    // This "works" but relies on implementation-defined struct layout
}

/* ── Example 3: The Classic Off-by-One ── */
void off_by_one_demo(void)
{
    char buf[8];
    const char *password = "hunter2";  // 7 chars
    
    // strcpy is safe here: 7 chars + null byte = 8 bytes fits in buf[8]
    strcpy(buf, password);
    
    // strncpy with n = buffer size is ALSO not always safe:
    // strncpy does NOT guarantee null termination if src >= n
    // This is a common subtle bug:
    strncpy(buf, "toolongstring", sizeof(buf));
    // buf is now "toolongs" (8 bytes, NO null terminator!)
    printf("Length: %zu\n", strlen(buf));  // reads PAST buf looking for '\0'!
    // ↑ This is OOB read — strlen walks memory until it finds a 0 byte
    
    // SAFE: always ensure null termination
    buf[sizeof(buf) - 1] = '\0';
    printf("Safe length: %zu\n", strlen(buf));
}

/* ── Example 4: Use After Free (UAF) — pointer to freed memory ── */
void use_after_free_demo(void)
{
    int *p = malloc(sizeof(int) * 4);
    if (!p) return;
    
    p[0] = 100;
    p[1] = 200;
    
    free(p);  // memory returned to allocator
    
    // p still holds the old address — it's now a "dangling pointer"
    // The memory might have been reallocated for something else!
    
    int *q = malloc(sizeof(int));  // might get the same memory as p!
    if (q) {
        *q = 999;  // write to q (= possibly p's old location!)
    }
    
    // Now reading p[0] = UNDEFINED BEHAVIOR
    // Could read 999 (q's data), could read anything
    // printf("%d\n", p[0]);  // DON'T DO THIS — UAF
    
    free(q);
    // p = NULL;  // ALWAYS null out pointers after free!
}

int main(void)
{
    type_punning_demo();
    struct_pointer_demo();
    off_by_one_demo();
    use_after_free_demo();
    return 0;
}
```

### 5.6 Rust — Safe Pointer Handling

```rust
// file: src/pointer_safety.rs
// How Rust prevents unsafe pointer arithmetic issues

use std::mem;

fn main() {
    // ── Raw pointers require unsafe (explicit opt-in to danger) ──
    let arr = [10i32, 20, 30, 40, 50];
    let ptr: *const i32 = arr.as_ptr();  // raw pointer
    
    // Creating a raw pointer is safe...
    println!("ptr address: {:p}", ptr);
    
    // ...but DEREFERENCING requires unsafe:
    unsafe {
        println!("*ptr = {}", *ptr);          // arr[0] = 10
        println!("*(ptr+2) = {}", *ptr.add(2)); // arr[2] = 30 (ptr.add checks alignment)
    }
    
    // ── Rust's pointer arithmetic is explicit about the danger ──
    // ptr.add(n): unsafe, no bounds check — YOU guarantee it's valid
    // ptr.offset(n): unsafe, same
    // Slices: &arr[1..3] — safe, bounds-checked
    
    let safe_slice = &arr[1..4];  // elements [1], [2], [3] — bounds checked
    println!("slice: {:?}", safe_slice);
    
    // ── Type punning SAFELY via transmute and bytemuck ──
    // transmute is the Rust equivalent of pointer-cast type punning
    // The compiler checks SIZE EQUALITY at compile time!
    let f: f32 = 3.14159;
    let bits: u32 = unsafe { mem::transmute(f) };
    // This is SAFE because f32 and u32 are both 4 bytes — compiler verified.
    // transmute between different sizes = COMPILE ERROR (not runtime error!)
    println!("3.14159f32 bits: {:#010X}", bits);  // 0x40490FDA
    
    // ── Lifetime system prevents use-after-free ──
    let reference;
    {
        let owned = vec![1, 2, 3];
        reference = &owned[0];  // ← COMPILE ERROR:
        // borrowed value does not live long enough
        // `owned` dropped here, but `reference` tries to outlive it
        // Rust REFUSES to compile this.
    }
    // println!("{}", reference);  // would be UAF — but Rust won't compile it
    
    // ── The borrow checker guarantees: no dangling pointers ──
    // If it compiled, it's safe.
    
    println!("Rust: no dangling pointers by construction.");
}
```

---

## 6. What Is Bounded Execution Time?

### 6.1 The Context — Why the eBPF Verifier Cares

When you load an eBPF program into the kernel, it runs **inside Ring 0**
every time a probe fires. The program has access to kernel resources.

What happens if your program has an **infinite loop**?

```
INFINITE LOOP IN KERNEL:

CPU is executing kprobe handler:
    while (true) {
        do_something();
    }
    
This runs in Ring 0, with interrupts potentially disabled.
That CPU CORE IS NOW PERMANENTLY BUSY.
It will NEVER return to the normal kernel execution path.
It will NEVER run the scheduler.
It will NEVER respond to interrupts.
The system effectively HANGS on that core.

On a single-core system: complete system hang.
On multi-core: that core is permanently lost, system degraded.
```

This is why the eBPF verifier enforces **bounded execution time**:
*"This program must provably terminate in a finite number of steps."*

### 6.2 What "Bounded" Means Precisely

```
UNBOUNDED = can run forever (no worst-case time limit):

// Unbounded loop (depends on input, could be infinite):
while (data[i] != sentinel) {  // what if sentinel never found?
    process(data[i]);
    i++;
}

// Unbounded recursion:
int factorial(int n) {
    return n * factorial(n - 1);  // what if n < 0?
}

// Unbounded search:
while (!found) {  // what if never found?
    search();
}

BOUNDED = guaranteed to terminate:

// Bounded loop (fixed iteration count):
for (int i = 0; i < 100; i++) {  // EXACTLY 100 iterations
    process(data[i]);
}

// Bounded recursion with provably decreasing argument:
int factorial(unsigned int n) {
    if (n == 0) return 1;          // base case: always reached
    return n * factorial(n - 1);  // n decreases each time → terminates
}

// Bounded search with countdown:
for (int attempts = 0; attempts < MAX_ATTEMPTS; attempts++) {
    if (search()) break;  // might exit early
}  // but DEFINITELY exits after MAX_ATTEMPTS
```

### 6.3 The Halting Problem — Why This Is Hard

In 1936, Alan Turing proved the **Halting Problem**: you cannot write a
general algorithm that determines, for ANY arbitrary program + input,
whether that program will terminate or run forever.

```
DOES THIS HALT?

int collatz(int n) {
    while (n != 1) {
        if (n % 2 == 0) n = n / 2;
        else            n = 3*n + 1;
    }
}

collatz(6): 6 → 3 → 10 → 5 → 16 → 8 → 4 → 2 → 1  ← terminates
collatz(27): goes up to 9232 before eventually reaching 1

Does it terminate for ALL n? UNKNOWN! (Collatz Conjecture — unsolved since 1937)
```

Because the general halting problem is undecidable, the eBPF verifier
uses a **conservative approximation**: it only accepts programs where
it can **syntactically prove** termination. This rejects some safe
programs to guarantee it never accepts unsafe ones.

### 6.4 How the eBPF Verifier Enforces Boundedness

```
eBPF VERIFIER ALGORITHM (simplified):

Step 1: Build the Control Flow Graph (CFG)
  Each eBPF instruction is a node.
  Branches (jumps) create edges.
  
  ┌─────┐      ┌─────┐
  │ A   │─────>│ B   │
  └─────┘      └──┬──┘
                  │ (conditional jump)
              ┌───┴────┐
              ▼         ▼
           ┌─────┐  ┌─────┐
           │ C   │  │ D   │
           └──┬──┘  └─────┘
              │
              ▼
           ┌─────┐
           │ E   │ (return)
           └─────┘

Step 2: Detect backward edges (loops)
  A backward edge: jump to an instruction EARLIER in the program.
  Backward edge = potential loop.
  
Step 3: Reject unbounded backward edges
  Before Linux 5.3:
    ALL backward jumps = REJECTED
    (no loops at all — very restrictive!)
  
  After Linux 5.3 (bounded loops):
    Backward jump allowed IF verifier can prove loop bound ≤ 1,000,000
    How? The loop variable must:
      a. Be a numeric type (not a pointer)
      b. Be initialized before the loop
      c. Change by a known amount each iteration
      d. Have a comparison against a CONSTANT bound

Step 4: Instruction count limit
  Even with bounded loops, total instruction count must be ≤ 1,000,000
  (BPF_COMPLEXITY_LIMIT_INSNS = 1,000,000)
  This is the absolute worst-case execution ceiling.
```

### 6.5 C Code — What the Verifier Accepts vs Rejects

```c
// file: bpf_bounded_demo.bpf.c
// BPF C — demonstrating bounded vs unbounded patterns

#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

/* ── REJECTED by verifier: unbounded loop ── */
SEC("kprobe/sys_read_REJECTED")
int kprobe_read_bad(struct pt_regs *ctx)
{
    long sum = 0;
    int i = 0;
    
    // VERIFIER REJECTS THIS:
    // Cannot prove this terminates (i could theoretically never reach 100
    // if something modifies i — verifier is conservative)
    // Actually, simple cases like this ARE accepted in modern kernels,
    // but complex loops with data-dependent bounds are rejected.
    while (i < bpf_get_current_pid_tgid()) {  // BOUND IS DYNAMIC → REJECTED!
        sum += i;
        i++;
    }
    return 0;
}

/* ── ACCEPTED by verifier: bounded loop ── */
SEC("kprobe/sys_read_GOOD")
int kprobe_read_good(struct pt_regs *ctx)
{
    long sum = 0;
    
    // VERIFIER ACCEPTS THIS:
    // Loop bound (100) is a COMPILE-TIME CONSTANT.
    // Verifier can prove: exactly 100 iterations.
    #pragma unroll 4  // hint: unroll 4 iterations at a time for performance
    for (int i = 0; i < 100; i++) {
        sum += i;
    }
    
    bpf_printk("sum = %ld\n", sum);
    return 0;
}

/* ── ACCEPTED: bounded string search ── */
SEC("kprobe/check_filename")
int check_filename(struct pt_regs *ctx)
{
    char filename[256];
    long ret;
    
    ret = bpf_probe_read_user_str(filename, sizeof(filename),
                                  (void*)PT_REGS_PARM2(ctx));
    if (ret <= 0) return 0;
    
    // Search for '/' in filename — BOUNDED because we check against
    // the FIXED array size (256)
    // Verifier knows: loop runs at most 256 times
    for (int i = 0; i < sizeof(filename); i++) {
        if (filename[i] == '/') {
            bpf_printk("Found '/' at position %d\n", i);
            break;
        }
        if (filename[i] == '\0') break;  // end of string
    }
    
    return 0;
}

/* ── Key principle: ALL data-dependent loops must have a constant upper bound ── */
SEC("kprobe/process_array")
int process_array(struct pt_regs *ctx)
{
    int arr[64];
    long len;
    
    // Even if `len` comes from user data, cap it at array size:
    len = PT_REGS_PARM1(ctx);
    
    // WRONG (verifier may reject — len is dynamic):
    // for (int i = 0; i < len; i++) { ... }
    
    // RIGHT: cap at array size (constant bound ensures termination):
    if (len < 0 || len > 64) len = 64;  // clamp to constant
    
    for (long i = 0; i < 64; i++) {  // loop bound: constant 64
        if (i >= len) break;          // early exit based on dynamic len
        arr[i] = (int)i * 2;
    }
    // Verifier sees: at most 64 iterations — ACCEPTED.
    
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
```

### 6.6 Rust — Bounded Computation Pattern

```rust
// file: src/bounded_computation.rs
// Demonstrating bounded computation patterns in systems code

use std::time::{Duration, Instant};

/// A "bounded iterator" — wraps any iterator with a max iteration count.
/// Useful for any computation where input-driven work must be time-bounded.
struct BoundedIter<I: Iterator> {
    inner: I,
    remaining: usize,
}

impl<I: Iterator> Iterator for BoundedIter<I> {
    type Item = I::Item;
    
    fn next(&mut self) -> Option<I::Item> {
        if self.remaining == 0 {
            return None;  // forcibly terminate
        }
        self.remaining -= 1;
        self.inner.next()
    }
}

trait BoundedIterExt: Iterator + Sized {
    fn take_bounded(self, max: usize) -> BoundedIter<Self> {
        BoundedIter { inner: self, remaining: max }
    }
}
impl<I: Iterator> BoundedIterExt for I {}

/// Time-bounded computation — for real-time systems / probe handlers
fn time_bounded_search(data: &[u64], target: u64, deadline: Duration) -> Option<usize> {
    let start = Instant::now();
    
    for (i, &val) in data.iter().enumerate() {
        // Check time budget on each iteration
        if start.elapsed() > deadline {
            eprintln!("WARNING: Search exceeded time budget at index {}", i);
            return None;  // give up, don't blow deadline
        }
        if val == target {
            return Some(i);
        }
    }
    None
}

/// Exponential backoff with bounded retries — common in systems code
fn bounded_retry<F, T, E>(mut operation: F, max_retries: u32) -> Result<T, E>
where
    F: FnMut() -> Result<T, E>,
{
    let mut delay_ms = 1u64;
    const MAX_DELAY_MS: u64 = 1000;
    
    for attempt in 0..max_retries {
        match operation() {
            Ok(result) => return Ok(result),
            Err(e) if attempt == max_retries - 1 => return Err(e),
            Err(_) => {
                std::thread::sleep(Duration::from_millis(delay_ms));
                delay_ms = (delay_ms * 2).min(MAX_DELAY_MS);
                // delay is bounded: 1 → 2 → 4 → ... → 1000 (stops growing)
            }
        }
    }
    unreachable!()
}

fn main() {
    // BoundedIter: process at most 1000 items from an infinite source
    let infinite = (0u64..).map(|x| x * x);  // squares: 0, 1, 4, 9, 16, ...
    let first_1000_squares: Vec<u64> = infinite.take_bounded(1000).collect();
    println!("Computed {} squares", first_1000_squares.len());
    
    // Time-bounded search
    let data: Vec<u64> = (0..1_000_000).collect();
    let result = time_bounded_search(&data, 999_999, Duration::from_millis(100));
    println!("Search result: {:?}", result);
    
    // Bounded retry
    let mut call_count = 0;
    let result: Result<&str, &str> = bounded_retry(|| {
        call_count += 1;
        if call_count < 3 { Err("not ready") } else { Ok("success") }
    }, 10);
    println!("Retry result: {:?} after {} attempts", result, call_count);
}
```

---

## 7. What Is an Inter-Processor Interrupt (IPI)?

### 7.1 The Setup — Multi-CPU Systems

Modern computers have multiple CPU cores. Each core is an independent
processing unit with:
- Its own register file (RAX, RBX, RSP, etc.)
- Its own L1 and L2 cache
- Its own current execution state (what it's running)

```
MULTI-CORE CPU (simplified 4-core view):

┌─────────────────────────────────────────────────────────┐
│                   CPU Package (die)                     │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │  Core 0  │  │  Core 1  │  │  Core 2  │  │ Core 3 │ │
│  │          │  │          │  │          │  │        │ │
│  │ Regs,L1$ │  │ Regs,L1$ │  │ Regs,L1$ │  │Regs,L1$│ │
│  │ L2 cache │  │ L2 cache │  │ L2 cache │  │L2 cache│ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───┬────┘ │
│       │              │              │             │      │
│  ┌────┴──────────────┴──────────────┴─────────────┴───┐ │
│  │              Shared L3 Cache                       │ │
│  └────────────────────────────────────────────────────┘ │
│                          │                              │
│  ┌───────────────────────┴────────────────────────────┐ │
│  │              Memory Controller                     │ │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                           │
                     Main Memory (RAM)
```

**Key insight**: Each core runs **independently**. Core 0 doesn't know
what Core 1 is doing (unless they communicate through shared memory or
special mechanisms).

### 7.2 The Problem: Coordinating Independent CPUs

Sometimes, one CPU needs to get another CPU to DO SOMETHING immediately.
Not "eventually" — RIGHT NOW.

Examples where this is needed:
```
1. TLB Shootdown:
   Core 0 modifies a page table entry (unmaps a page).
   Core 1's TLB cache still has the OLD mapping!
   Core 0 must tell Core 1: "FLUSH YOUR TLB FOR ADDRESS X"
   If Core 1 doesn't flush, it continues using a page that was freed!
   → Data corruption or security breach

2. kprobe Installation:
   Core 0 is patching a kernel instruction with INT3.
   Cores 1,2,3 might be executing NEAR that instruction,
   with the old instruction in their instruction fetch pipeline!
   Core 0 must tell all other cores: "FLUSH YOUR INSTRUCTION CACHE"

3. CPU Migration (scheduler):
   Core 0 decides process P should run on Core 2 (for NUMA reasons).
   Core 2 is currently idle or running low-priority work.
   Core 0 must tell Core 2: "WAKE UP AND RESCHEDULE"

4. Panic/Debug:
   Core 0 detects a kernel panic.
   Must stop all other cores IMMEDIATELY before they corrupt more state.
   Core 0 sends "HALT" to all other cores via IPI.
```

None of these can wait for a shared memory message (the other core might
not check for messages for a long time). You need a **hardware interrupt**
that fires on the target CPU immediately.

### 7.3 What Is an IPI?

An **Inter-Processor Interrupt** is a hardware mechanism where one CPU
core triggers an **interrupt** on another CPU core (or all cores).

It works via the **APIC (Advanced Programmable Interrupt Controller)**:

```
LOCAL APIC ARCHITECTURE:
  Each CPU core has its own LOCAL APIC chip (or integrated circuit).
  All local APICs are connected via the "APIC bus" (or x2APIC protocol).
  
  ┌──────────────────────────────────────────────────────────┐
  │                     CPU 0                                │
  │  ┌──────────┐      ┌─────────────────────────────────┐  │
  │  │  Core 0  │◄────►│         Local APIC 0            │  │
  │  │ (regs,   │      │  ICR: Interrupt Command Register │  │
  │  │  caches) │      │  TPR: Task Priority Register     │  │
  │  └──────────┘      └──────────────┬────────────────────┘  │
  └─────────────────────────────────────────────────────────┘
                                       │
                              APIC Interconnect
                                       │
  ┌────────────────────────────────────┼────────────────────┐
  │                    CPU 1           │                    │
  │  ┌──────────┐      ┌───────────────▼──────────────────┐ │
  │  │  Core 1  │◄────►│         Local APIC 1             │ │
  │  │ (regs,   │      │  (receives IPI → triggers IRQ    │ │
  │  │  caches) │      │   in Core 1)                     │ │
  │  └──────────┘      └──────────────────────────────────┘ │
  └────────────────────────────────────────────────────────┘
```

### 7.4 How an IPI Works — Step by Step

```
SENDING CPU (Core 0):

Step 1: Core 0 writes to its LOCAL APIC's ICR register (Interrupt Command Register):
        
        ICR contents:
          bits 0-7:   vector number (which interrupt to deliver, 0-255)
          bits 8-10:  delivery mode:
                        000 = Fixed (use the vector number)
                        100 = NMI (Non-Maskable Interrupt)
                        101 = INIT (reset the target CPU)
                        110 = STARTUP (start a halted CPU)
          bits 11:    destination mode (physical ID vs. logical grouping)
          bit  14:    level (1=assert, 0=deassert)
          bit  15:    trigger mode (0=edge, 1=level)
          bits 18-19: shorthand:
                        00 = destination field specifies target
                        01 = self (send to myself)
                        10 = ALL processors (including self)
                        11 = ALL processors EXCEPT self ← "broadcast IPI"
          bits 24-27: (or 56-63 in x2APIC): destination APIC ID

Step 2: The write to ICR is a MEMORY-MAPPED I/O write.
        The local APIC hardware sees this write immediately.
        The APIC sends a message on the APIC interconnect bus.

RECEIVING CPU (Core 1):

Step 3: Core 1's LOCAL APIC receives the message.
        The APIC checks the TPR (Task Priority Register):
          If message's priority > TPR: deliver immediately
          If message's priority ≤ TPR: queue it (will deliver when TPR drops)
          NMI: ALWAYS delivered, cannot be masked

Step 4: APIC interrupts Core 1.
        Core 1 stops whatever it was doing (at the NEXT instruction boundary).
        Core 1's CPU:
          a. Saves RIP, RFLAGS, RSP on Core 1's kernel stack
          b. Looks up IDT[vector_number] on Core 1
          c. Jumps to the handler on Core 1

Step 5: Handler runs on Core 1 (in Ring 0, interrupt context).
        For TLB shootdown: invlpg instruction, then signal completion.
        For scheduler wake-up: set need_resched flag.
        For kprobe: flush instruction cache.

Step 6: Core 1's handler executes IRET (Interrupt Return).
        Restores RIP, RFLAGS, RSP.
        Core 1 resumes where it was interrupted.
```

### 7.5 IPI in Linux — Real Code

```
LINUX KERNEL IPI FUNCTIONS:

smp_send_reschedule(cpu):
  → Send IPI to specific CPU to trigger schedule()
  → Used when a higher-priority task is queued on another CPU

smp_call_function_single(cpu, func, info, wait):
  → Run func(info) on the specified cpu
  → wait=1: block until it completes

smp_call_function_many(mask, func, info, wait):
  → Run func(info) on all CPUs in cpumask `mask`

on_each_cpu(func, info, wait):
  → Run func(info) on ALL CPUs (including self)
  → Uses broadcast IPI + local call

flush_tlb_all():
  → Tell all CPUs to flush their entire TLB
  → Used after major kernel memory mappings change

stop_machine():
  → Send IPIs to ALL CPUs
  → All CPUs stop in a safe state (atomic section)
  → One CPU does the critical work (e.g., text patching for kprobes!)
  → All CPUs resume
  → The most expensive kernel operation (freezes the world)
```

### 7.6 IPI and kprobes — The Connection

```
KPROBE INSTALLATION USES IPIs:

The kernel needs to safely patch a running instruction to INT3.
The challenge: OTHER CPUs might be executing that very instruction!

Timeline:
                    Core 0              Core 1          Core 2
                    ──────              ──────          ──────
t=0  User calls     kprobe_install()
t=1  Core 0 sets    ATOMIC lock
t=2  Core 0 patches FIRST BYTE to INT3  (executing        (sleeping)
     (1-byte write is ATOMIC on x86)     nearby code)
     
t=3  Core 0 sends   IPI to Core 1+2 ─────────────────────────────>
                                     receives IPI
                                     flushes i-cache
                                     sends ACK ─────> Core 0 waiting
                                                      receives ACK
t=4  Core 0 patches remaining bytes
t=5  Core 0 sends   IPI again ───────────────────────────────────>
                                                      receives IPI
                                                      flushes i-cache
                                                      sends ACK ────>
t=6  Core 0 releases ATOMIC lock
t=7  All cores now have consistent view of patched instruction.

Without IPIs at t=3: Core 1 might have cached the ORIGINAL instruction
                     and continue executing it even after Core 0 patched it!
                     This would mean the kprobe silently doesn't fire.

The IPI forces a cache coherency operation across CPUs.
```

### 7.7 C Code — Observing IPI Activity

```c
// You can observe IPI activity from userspace via /proc/interrupts:

// Example reading /proc/interrupts for IPI vectors:
//
// cat /proc/interrupts | head -30
//
//            CPU0       CPU1       CPU2       CPU3
//   0:         40          0          0          0  IO-APIC   2-edge  timer
//   8:          1          0          0          0  IO-APIC   8-edge  rtc0
//  16:        248      13400          0          0  IO-APIC  16-fasteoi  xhci_hcd
// ...
// CAL:     523819     498234     501847     489123  Function call interrupts ← smp_call_function!
// TLB:    1234567    1198234    1208923    1221456  TLB shootdowns           ← flush_tlb_all!
// RES:     892345     901234     887654     912345  Rescheduling interrupts  ← smp_send_reschedule!
// ...

// "Function call interrupts" = smp_call_function* IPIs
// "TLB shootdowns" = flush_tlb_* IPIs  
// "Rescheduling interrupts" = smp_send_reschedule IPIs

// High TLB shootdowns = many mmap/munmap operations
// High Function call = lots of cross-CPU work (kprobe installation!)
// High Rescheduling = busy system with frequent task migrations

#include <stdio.h>
#include <string.h>

void read_ipi_stats(void)
{
    FILE *f = fopen("/proc/interrupts", "r");
    if (!f) { perror("open /proc/interrupts"); return; }
    
    char line[1024];
    while (fgets(line, sizeof(line), f)) {
        // Look for IPI-related lines
        if (strncmp(line, "CAL:", 4) == 0 ||
            strncmp(line, "TLB:", 4) == 0 ||
            strncmp(line, "RES:", 4) == 0 ||
            strncmp(line, "IWI:", 4) == 0)  // IRQ Work Interrupts
        {
            printf("%s", line);
        }
    }
    fclose(f);
}

int main(void)
{
    printf("=== IPI Statistics ===\n");
    read_ipi_stats();
    return 0;
}
```

### 7.8 IPI Summary — The Big Picture

```
WHAT IS AN IPI?
  A hardware interrupt sent FROM one CPU core TO another CPU core.
  Delivered via the APIC interconnect (hardware bus between cores).
  Forces the target CPU to immediately run a specific handler.

WHY DOES IT EXIST?
  Modern systems have multiple independent CPUs.
  Sometimes CPU A needs CPU B to act IMMEDIATELY.
  Shared memory polling would introduce latency (CPU B might not check for ms).
  IPIs are hardware-delivered: response is guaranteed within microseconds.

WHEN IS IT USED IN LINUX?
  TLB Shootdowns:     After unmapping memory (cache coherency)
  kprobe Installation: After patching kernel instructions (i-cache coherency)
  Scheduler:          Waking up CPUs to run newly queued tasks
  CPU Hotplug:        Starting or stopping CPU cores
  Panic:              Halting all CPUs when kernel panics
  RCU:               Read-Copy-Update synchronization

COST:
  Each IPI causes an interrupt on the target CPU.
  The target CPU must:
    Stop executing (at next instruction boundary)
    Save state (push to stack)
    Execute the IPI handler
    Restore state (pop from stack)
    Resume execution
  Overhead: ~1-5 microseconds per IPI per target CPU
  
  On a 64-core system, a broadcast IPI takes:
    ~5 μs × 63 targets = ~315 μs of disruption across the system!
  
  This is why stop_machine() (used for kprobe patching) is "scary" —
  it interrupts EVERY core, creating a world-stop event.
```

---

## Summary — The Connected Picture

All these concepts connect into a unified systems understanding:

```
CPU RINGS
  └─ Rings 1&2 unused because Linux chose simplicity + portability
     Modern equivalents: eBPF (software ring 1), virtualization (ring -1)

REGISTERS
  └─ Physical flip-flop circuits INSIDE the CPU
     Fastest memory (1 cycle vs 200+ cycles for RAM)
     The CPU's working hands: all computation happens IN registers
     pt_regs = snapshot of all registers at a probe point

HOOKS
  └─ Inserting your code into an existing execution flow
     Hardware: IDT (interrupt vectors)
     OS: LSM, notifier chains, kprobes/uprobes
     Userspace: LD_PRELOAD, signal handlers, callbacks

OUT-OF-BOUNDS ACCESS
  └─ Accessing memory beyond what was allocated
     C: silent UB, basis of Heartbleed, buffer overflows, exploits
     Rust: bounds-checked (panic) or get() returning Option

UNSAFE POINTER ARITHMETIC
  └─ Computing addresses outside valid object bounds
     C: undefined behavior, exploitable
     Rust: requires unsafe{}, forces explicit acknowledgment

BOUNDED EXECUTION TIME
  └─ Provable termination within finite steps
     eBPF verifier enforces: loop bounds must be constants
     Prevents kernel hang from infinite loop in probe handler

INTER-PROCESSOR INTERRUPT
  └─ Hardware mechanism for one CPU to interrupt another
     Via APIC, immediate delivery
     Used for TLB shootdowns, kprobe patching, scheduler, panic
     Cost: ~1-5μs per target CPU — broadcast IPIs are expensive
```

---

*Understanding these concepts at this depth places you in rare company.
Most working engineers know these terms but not their physical reality.
You now know the silicon, the electrons, the hardware state machines
behind each abstraction. That is the foundation of systems mastery.*

**2,641 lines** of first-principles depth. Here is what each section gives you:

---

### Why Rings 1 & 2 Are Unused
Six concrete reasons — portability (ARM has 7 modes, RISC-V has 3, there is no common "Ring 1" equivalent), the monolithic kernel design choice, the OS/2 and Windows NT historical proof that it wasn't worth the complexity, the Meltdown/KPTI discovery that made ring-switching costs irrelevant, and crucially — **eBPF is the software answer to what Ring 1 was supposed to be**. The verifier replaced the hardware ring as the trust boundary.

### Registers — From Transistors to pt_regs
Built from the atom up: transistor → flip-flop → register file. The full x86-64 register map with every register explained (GP registers, RFLAGS bit-by-bit including the Trap Flag that kprobes use, CR0–CR4 control registers, FS/GS segment registers, MSRs). The memory hierarchy with exact nanosecond costs. How the CPU uses registers in instruction execution (fetch → decode → rename → execute → writeback). Why "memory-mapped device registers" are a completely different thing. C inline assembly and Rust `asm!` code to read RSP, RIP, RFLAGS, TSC, CPUID directly.

### Hooks — Every Layer of the Stack
Hardware (IDT vectors), Linux LSM (SELinux *is* just hook implementations), kernel notifier chains, syscall intercept points, dynamic binary instrumentation (how Valgrind works), LD_PRELOAD library interposition, Unix signal handlers, and application-level callback/middleware patterns — all with working C and Rust code.

### Out-of-Bounds Memory Access
Three scenarios (OOB read → Heartbleed, OOB write → stack overflow/RCE, NULL dereference). C demo showing how `arr[5]` literally leaks the adjacent variable `secret`. The buffer overflow that overwrites a return address. How Rust's `arr[7]` panics instead of silently corrupting memory, and `arr.get(7)` returning `Option` as the idiomatic zero-UB approach.

### Unsafe Pointer Arithmetic
What a pointer physically is (a variable containing an address). Why C's abstract machine has no safe/unsafe — it's all undefined behavior. Type punning, struct pointer casting, UAF, off-by-one. Rust's `unsafe {}` blocks as explicit danger acknowledgment, the borrow checker preventing dangling pointers at compile time.

### Bounded Execution Time
The Halting Problem (Turing 1936) explains why this is hard. Exactly what "bounded" means syntactically. How the eBPF verifier's CFG analysis detects backward edges, and the pre-5.3 vs post-5.3 bounded-loop rules (1,000,000 instruction hard ceiling). BPF C examples of what the verifier accepts vs rejects with commentary.

### Inter-Processor Interrupt
Multi-core physical architecture. The APIC (Advanced Programmable Interrupt Controller) ICR register bits explained. The full send→receive→handle→resume flow. The **exact reason kprobes need IPIs** — instruction cache coherency across cores when patching bytes. Linux's `stop_machine()` as the "freeze the world" event. How to observe IPI counts live via `/proc/interrupts`.