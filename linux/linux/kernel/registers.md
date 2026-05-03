# Registers & The Linux Kernel: A Complete In-Depth Guide

> *"To understand the kernel is to understand the machine. To understand the machine is to understand registers."*

---

## Table of Contents

1. [What Is a Register?](#1-what-is-a-register)
2. [Why Registers Exist — The Memory Hierarchy](#2-why-registers-exist--the-memory-hierarchy)
3. [Register Architecture: x86-64 (AMD64)](#3-register-architecture-x86-64-amd64)
4. [Register Architecture: ARM64 (AArch64)](#4-register-architecture-arm64-aarch64)
5. [General-Purpose Registers (GPRs) Deep Dive](#5-general-purpose-registers-gprs-deep-dive)
6. [Special-Purpose Registers Deep Dive](#6-special-purpose-registers-deep-dive)
7. [Segment Registers (x86-64)](#7-segment-registers-x86-64)
8. [Control Registers (x86-64)](#8-control-registers-x86-64)
9. [Debug Registers (x86-64)](#9-debug-registers-x86-64)
10. [SIMD / Floating-Point Registers](#10-simd--floating-point-registers)
11. [Model-Specific Registers (MSRs)](#11-model-specific-registers-msrs)
12. [The EFLAGS / RFLAGS Register](#12-the-eflags--rflags-register)
13. [Calling Conventions — How Registers Are Used by ABI](#13-calling-conventions--how-registers-are-used-by-abi)
14. [The Linux Kernel and Registers: `pt_regs`](#14-the-linux-kernel-and-registers-pt_regs)
15. [System Calls — The Register Dance](#15-system-calls--the-register-dance)
16. [Context Switching — Saving & Restoring Registers](#16-context-switching--saving--restoring-registers)
17. [Interrupt Handling and Registers](#17-interrupt-handling-and-registers)
18. [Signals and Register State](#18-signals-and-register-state)
19. [Register-Level Debugging (ptrace)](#19-register-level-debugging-ptrace)
20. [Inline Assembly in C and Rust](#20-inline-assembly-in-c-and-rust)
21. [Register Allocation in Compilers](#21-register-allocation-in-compilers)
22. [Security: Register Leakage and Spectre/Meltdown](#22-security-register-leakage-and-spectremeltdown)
23. [Complete C Implementation Reference](#23-complete-c-implementation-reference)
24. [Complete Rust Implementation Reference](#24-complete-rust-implementation-reference)
25. [Mental Models and Summary](#25-mental-models-and-summary)

---

## 1. What Is a Register?

### Concept From Scratch

A **register** is the fastest, smallest, and most fundamental unit of storage in a computer. It lives **directly inside the CPU chip** — not on the RAM chip, not on any external memory bus. It is wired directly to the CPU's execution units (ALU, FPU, control logic).

**Analogy:**
Think of a chef cooking in a kitchen:
- **Register** = the chef's two hands (instant access, tiny capacity)
- **L1 Cache** = the countertop (very fast, small)
- **L2/L3 Cache** = shelves in the kitchen (fast, medium)
- **RAM** = the pantry (slower, large)
- **Disk** = the warehouse across the street (very slow, huge)

A register can be **read or written in a single CPU clock cycle** (< 1 nanosecond at 3GHz). RAM access takes ~100 nanoseconds. This 100x speed difference is why registers exist.

### Physical Reality

Registers are built from **flip-flops** (D-type latches) — tiny circuits that store a single bit using two states of voltage. A 64-bit register is literally 64 flip-flops wired together. The CPU can read all 64 bits simultaneously in one clock tick.

```
Single Bit Storage (D Flip-Flop):
                ┌──────────────┐
  Data (D) ─────┤              ├───── Output (Q)   ← stores 1 bit
  Clock    ─────┤   D FF       ├───── NOT Q
                └──────────────┘

64-bit Register = 64 such flip-flops in parallel:
  Bit 63 ... Bit 32 | Bit 31 ... Bit 16 | Bit 15 ... Bit 8 | Bit 7 ... Bit 0
  ┌────────────────────────────────────────────────────────────────────────┐
  │  FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF ... │
  └────────────────────────────────────────────────────────────────────────┘
  Each FF = one D flip-flop = one bit
```

---

## 2. Why Registers Exist — The Memory Hierarchy

### The Memory Hierarchy Pyramid

```
                    ┌─────────────────────┐
                    │      REGISTERS      │  ← ~16-32 regs, 1 cycle
                    │    (inside CPU)     │    ~3.3 GHz = 0.3ns
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │     L1 CACHE        │  ← 32–64 KB, 4-5 cycles
                    │   (inside CPU die)  │    ~1-2ns
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │     L2 CACHE        │  ← 256 KB–1MB, 12 cycles
                    │   (on CPU die)      │    ~3-4ns
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │     L3 CACHE        │  ← 4MB–64MB, 30-40 cycles
                    │  (shared on die)    │    ~10-20ns
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │      MAIN RAM       │  ← GBs, ~200 cycles
                    │   (DDR5 sticks)     │    ~60-100ns
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │    SSD / NVMe       │  ← TBs, ~100,000 cycles
                    │   (storage bus)     │    ~50-100 microseconds
                    └─────────────────────┘
```

The CPU **cannot do arithmetic on RAM values directly**. It must:
1. Load value from RAM → register (`MOV RAX, [address]`)
2. Perform operation on register (`ADD RAX, RBX`)
3. Store result back to RAM if needed (`MOV [address], RAX`)

This **load → compute → store** cycle is the heartbeat of all computation.

---

## 3. Register Architecture: x86-64 (AMD64)

### Overview

x86-64 (also called AMD64, Intel 64) is the dominant architecture for desktop, server, and Linux systems. It was an extension of the original 8086 (1978) through 286, 386, 486, Pentium, to 64-bit Athlon 64/Intel Core.

### The Full Register Map

```
x86-64 COMPLETE REGISTER ARCHITECTURE
═══════════════════════════════════════════════════════════════════════════

GENERAL PURPOSE REGISTERS (64-bit capable):
┌────────────────────────────────────────────────────────────────────────┐
│  63          32│31        16│15      8│7       0│  Name   Purpose      │
├────────────────┼────────────┼─────────┼─────────┼─────────────────────┤
│       RAX      │    EAX     │   AX    │AH │ AL  │ rax   Accumulator   │
│       RBX      │    EBX     │   BX    │BH │ BL  │ rbx   Base          │
│       RCX      │    ECX     │   CX    │CH │ CL  │ rcx   Counter       │
│       RDX      │    EDX     │   DX    │DH │ DL  │ rdx   Data          │
│       RSI      │    ESI     │   SI    │   │ SIL │ rsi   Source Index  │
│       RDI      │    EDI     │   DI    │   │ DIL │ rdi   Dest Index    │
│       RSP      │    ESP     │   SP    │   │ SPL │ rsp   Stack Pointer │
│       RBP      │    EBP     │   BP    │   │ BPL │ rbp   Base/Frame Ptr│
│       R8       │    R8D     │  R8W    │   │ R8B │ r8    Extended      │
│       R9       │    R9D     │  R9W    │   │ R9B │ r9    Extended      │
│       R10      │   R10D     │  R10W   │   │R10B │ r10   Extended      │
│       R11      │   R11D     │  R11W   │   │R11B │ r11   Extended      │
│       R12      │   R12D     │  R12W   │   │R12B │ r12   Extended      │
│       R13      │   R13D     │  R13W   │   │R13B │ r13   Extended      │
│       R14      │   R14D     │  R14W   │   │R14B │ r14   Extended      │
│       R15      │   R15D     │  R15W   │   │R15B │ r15   Extended      │
└────────────────┴────────────┴─────────┴─────────┴─────────────────────┘

SPECIAL PURPOSE REGISTERS:
┌──────────────────────────────────────────────────────────────────────┐
│  RIP (64-bit)   │  Instruction Pointer — points to NEXT instruction  │
│  RFLAGS (64-bit)│  Status/Condition Flags register                   │
└──────────────────────────────────────────────────────────────────────┘

SEGMENT REGISTERS (16-bit each):
┌──────────────────────────────────────────────────────────────────────┐
│  CS │ DS │ ES │ FS │ GS │ SS │  Code/Data/Extra/Thread-Local/Stack  │
└──────────────────────────────────────────────────────────────────────┘

CONTROL REGISTERS (64-bit):
┌──────────────────────────────────────────────────────────────────────┐
│  CR0 │ CR2 │ CR3 │ CR4 │ CR8  │  Paging, protection, features       │
└──────────────────────────────────────────────────────────────────────┘

DEBUG REGISTERS (64-bit):
┌──────────────────────────────────────────────────────────────────────┐
│  DR0 │ DR1 │ DR2 │ DR3 │ DR6 │ DR7  │  Hardware breakpoints         │
└──────────────────────────────────────────────────────────────────────┘

SIMD / VECTOR REGISTERS:
┌──────────────────────────────────────────────────────────────────────┐
│  XMM0–XMM15  (128-bit)  │  SSE/SSE2–SSE4 floating point + SIMD      │
│  YMM0–YMM15  (256-bit)  │  AVX / AVX2 (contains XMM as lower half)  │
│  ZMM0–ZMM31  (512-bit)  │  AVX-512                                   │
└──────────────────────────────────────────────────────────────────────┘

MSRs (Model-Specific Registers):
┌──────────────────────────────────────────────────────────────────────┐
│  EFER, LSTAR, STAR, FS_BASE, GS_BASE, ...  (accessed via RDMSR/WRMSR)│
└──────────────────────────────────────────────────────────────────────┘
```

### Register Width Aliasing (Historical Baggage)

x86-64 inherits from 8086 (16-bit) → 80386 (32-bit) → x86-64 (64-bit). Each register has multiple "views":

```
RAX — The 64-bit "accumulator" register, shown as nested views:
┌───────────────────────────────────────────────────────────────────┐
│                           RAX (64-bit)                            │
│  Bit 63                                                   Bit 0   │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ 63                    32 │ 31              16 │ 15    8│7   0│  │
│  │      upper 32 bits       │                   │  AH    │ AL  │  │
│  │      (no alias)          │        AX          (16-bit)      │  │
│  │                          │                                   │  │
│  │                    EAX (32-bit)                              │  │
│  └─────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────┘

Key Rules:
  - Writing to EAX ZERO-EXTENDS to RAX (upper 32 bits cleared) ← CRITICAL!
  - Writing to AX does NOT affect upper 48 bits of RAX
  - Writing to AL does NOT affect upper 56 bits of RAX
  - Writing to AH does NOT affect bits 0-7 or 16-63

Example:
  RAX = 0xDEAD_BEEF_1234_5678
  Write AX = 0xFFFF
  Result: RAX = 0xDEAD_BEEF_1234_FFFF  ← upper 48 bits UNCHANGED

  Write EAX = 0xFFFFFFFF
  Result: RAX = 0x0000_0000_FFFF_FFFF  ← upper 32 bits ZEROED!
```

**Why this matters in the kernel:** GCC/Clang/LLVM exploit zero-extension heavily. A simple `int` comparison in C might emit `movl` (32-bit move) instead of `movq` (64-bit move) to get the zero-extension for free.

---

## 4. Register Architecture: ARM64 (AArch64)

ARM64 is the architecture of modern phones, Apple Silicon (M1/M2/M3), AWS Graviton, and Raspberry Pi 4+. Linux runs on ARM64 extensively.

### ARM64 Register Map

```
ARM64 COMPLETE REGISTER ARCHITECTURE
═══════════════════════════════════════════════════════════════════════════

GENERAL PURPOSE REGISTERS (31 registers, 64-bit):
┌─────────────────────────────────────────────────────────────────────┐
│  64-bit name │ 32-bit view │  ABI Role                              │
├──────────────┼─────────────┼────────────────────────────────────────┤
│  X0          │  W0         │  Arg1 / Return value                   │
│  X1          │  W1         │  Arg2 / Return value (high)            │
│  X2          │  W2         │  Arg3                                  │
│  X3          │  W3         │  Arg4                                  │
│  X4          │  W4         │  Arg5                                  │
│  X5          │  W5         │  Arg6                                  │
│  X6          │  W6         │  Arg7                                  │
│  X7          │  W7         │  Arg8                                  │
│  X8          │  W8         │  Indirect result / syscall number      │
│  X9–X15      │  W9–W15     │  Caller-saved temporaries             │
│  X16 (IP0)   │  W16        │  Intra-procedure-call scratch 1        │
│  X17 (IP1)   │  W17        │  Intra-procedure-call scratch 2        │
│  X18         │  W18        │  Platform register (OS-reserved)       │
│  X19–X28     │  W19–W28    │  Callee-saved (preserved across calls) │
│  X29 (FP)    │  W29        │  Frame Pointer                         │
│  X30 (LR)    │  W30        │  Link Register (return address)        │
│  XZR         │  WZR        │  Zero register (reads as 0)            │
│  SP          │  WSP        │  Stack Pointer (NOT X31!)              │
└──────────────┴─────────────┴────────────────────────────────────────┘

SPECIAL PURPOSE:
┌─────────────────────────────────────────────────────────────────────┐
│  PC  (64-bit) │  Program Counter (NOT directly accessible)          │
│  NZCV         │  Condition flags (N=Neg, Z=Zero, C=Carry, V=oVerflow│
│  DAIF         │  Interrupt mask bits (D,A,I,F flags)                │
│  SPSel        │  Stack Pointer selection (SP_EL0 or SP_ELx)         │
│  CurrentEL    │  Current Exception Level (EL0/EL1/EL2/EL3)         │
└─────────────────────────────────────────────────────────────────────┘

FLOATING POINT / SIMD (32 registers):
┌─────────────────────────────────────────────────────────────────────┐
│  V0–V31  (128-bit)  │  General SIMD                                 │
│  B0–B31   (8-bit)   │  Byte view of V registers                     │
│  H0–H31  (16-bit)   │  Half-precision FP view                       │
│  S0–S31  (32-bit)   │  Single-precision FP view                     │
│  D0–D31  (64-bit)   │  Double-precision FP view                     │
│  Q0–Q31 (128-bit)   │  Quad view (same as V)                        │
└─────────────────────────────────────────────────────────────────────┘

EXCEPTION LEVEL BANKED REGISTERS:
┌─────────────────────────────────────────────────────────────────────┐
│  EL0: User space (applications)                                     │
│  EL1: Kernel (Linux kernel runs here)                               │
│  EL2: Hypervisor (KVM, Xen)                                         │
│  EL3: Secure Monitor (ARM TrustZone, firmware)                      │
│                                                                     │
│  Each EL has its own: SP_ELx, SPSR_ELx, ELR_ELx, ESR_ELx           │
└─────────────────────────────────────────────────────────────────────┘
```

### Key ARM64 Difference from x86-64

ARM64 is a **RISC** (Reduced Instruction Set Computer) architecture — clean, orthogonal, and regular:
- All 31 GPRs are truly general (unlike x86 where RAX/RCX/RDX have special roles)
- No high/low byte aliasing — W-registers are just the lower 32 bits of X-registers
- Writing to W0 zero-extends to X0 (same as x86-64 EAX→RAX rule)
- Has a dedicated **zero register** (XZR/WZR) — reads always return 0, writes are discarded
- **X30 stores return address** — no CALL/RET instructions like x86; instead `BL` (Branch with Link) saves return addr in X30, and `RET` branches to X30

---

## 5. General-Purpose Registers (GPRs) Deep Dive

### x86-64 GPR Roles and Conventions

```
REGISTER USAGE CONVENTION TABLE (x86-64 Linux)
═══════════════════════════════════════════════════════════════════════

Register │ Syscall Role  │ Function Call Role │ Preserved? │ Notes
─────────┼───────────────┼────────────────────┼────────────┼──────────────────
RAX      │ syscall #     │ Return value       │ NO (caller)│ Also: 2nd return
RBX      │ —             │ —                  │ YES(callee)│ General purpose
RCX      │ —             │ 4th argument       │ NO (caller)│ Also used by LOOP
RDX      │ 3rd argument  │ 3rd argument       │ NO (caller)│ Also: I/O port
RSI      │ 2nd argument  │ 2nd argument       │ NO (caller)│ "Source Index"
RDI      │ 1st argument  │ 1st argument       │ NO (caller)│ "Dest Index"
RBP      │ —             │ Frame pointer      │ YES(callee)│ Can be omitted -O
RSP      │ —             │ Stack pointer      │ YES(callee)│ Always valid
R8       │ 5th argument  │ 5th argument       │ NO (caller)│ x86-64 addition
R9       │ 6th argument  │ 6th argument       │ NO (caller)│ x86-64 addition
R10      │ 4th argument  │ —                  │ NO (caller)│ Scratch in kernel
R11      │ RFLAGS copy   │ —                  │ NO (caller)│ Trashed by syscall
R12–R15  │ —             │ —                  │ YES(callee)│ Callee must save

─────────────────────────────────────────────────────────────────────────────
"Caller-saved" = the CALLING function must save before calling a sub-function
"Callee-saved" = the CALLED function must restore before returning
```

**Mental Model: Caller vs Callee Saved**

```
main() calls foo():

CALLER (main) must save before calling:
  RAX, RCX, RDX, RSI, RDI, R8, R9, R10, R11
  → These may be DESTROYED by foo()

CALLEE (foo) must restore before returning:
  RBX, RBP, R12, R13, R14, R15, RSP
  → foo() PROMISES to leave these unchanged

TIMELINE:
  main:
    push r12          ; main saves r12 if it uses it? NO!
    ; r12 is callee-saved — foo() must save it, not main
    call foo
    ; after return: RBX, RBP, R12-R15, RSP are unchanged
    ; but RAX has foo's return value
    ; RCX, RDX, etc. may be garbage

  foo:
    push rbx          ; foo must save rbx if it uses rbx
    push r12          ; foo must save r12 if it uses r12
    ; ... do work ...
    pop r12           ; restore before return
    pop rbx
    ret
```

---

## 6. Special-Purpose Registers Deep Dive

### RIP — Instruction Pointer

```
RIP (Instruction Pointer) — also called "Program Counter" (PC)
═══════════════════════════════════════════════════════════════

  ┌──────────────────────────────────────────────────────────┐
  │   Virtual Memory (simplified)                           │
  │                                                          │
  │   0xffff_8000_0000_0000  ← kernel space boundary        │
  │   ...                                                    │
  │   0x0000_7fff_ffff_ffff  ← user space top               │
  │                                                          │
  │   Code Section (text):                                   │
  │   ┌──────────────────┐                                   │
  │   │  instruction 1   │ ← RIP points here (next to exec) │
  │   │  instruction 2   │                                   │
  │   │  instruction 3   │                                   │
  │   └──────────────────┘                                   │
  └──────────────────────────────────────────────────────────┘

  CRITICAL: RIP always points to the NEXT instruction to execute,
  NOT the currently executing one.

  After CALL instruction:
    - RIP of current instruction + sizeof(CALL) is pushed to stack
    - RIP is set to the function's address

  After RET instruction:
    - Pop address from stack into RIP
    - Execution continues after the original CALL

  RIP-relative addressing (x86-64 feature):
    MOV RAX, [RIP + 0x20]  ; load from address = (current RIP + 0x20)
    → Used for Position-Independent Code (PIC), shared libraries
```

### RSP — Stack Pointer

```
RSP (Stack Pointer)
═══════════════════

  IMPORTANT: The stack grows DOWNWARD (toward lower addresses)

  High addresses:
  ┌─────────────────────────────────┐
  │        (program start)          │  RSP = 0x7fff_ffff_ffff
  │  argc, argv, envp, auxv         │  ← initial stack top
  ├─────────────────────────────────┤
  │         local vars              │
  │         saved registers         │  ← RSP moves DOWN as we push
  ├─────────────────────────────────┤
  │  <--- RSP currently here        │
  │         (free space)            │
  ├─────────────────────────────────┤
  │         GUARD PAGE              │  ← causes SIGSEGV on access
  └─────────────────────────────────┘
  Low addresses

  PUSH instruction:
    RSP = RSP - 8       ; move stack pointer down 8 bytes
    [RSP] = value       ; store value

  POP instruction:
    value = [RSP]       ; read value
    RSP = RSP + 8       ; move stack pointer up 8 bytes

  CALL instruction:
    RSP = RSP - 8
    [RSP] = RIP + sizeof_call_instruction   ; push return address
    RIP = target_function

  RET instruction:
    RIP = [RSP]         ; pop return address
    RSP = RSP + 8

  ALIGNMENT RULE (ABI): RSP must be 16-byte aligned BEFORE a CALL.
    After CALL pushes return address (8 bytes), RSP is 8-byte aligned.
    Function prologue must adjust: SUB RSP, 8 (or push one more reg)
```

---

## 7. Segment Registers (x86-64)

Segment registers are a legacy from the 16-bit and 32-bit era. In x86-64 **protected mode with flat memory model**, most segment registers (CS, DS, ES, SS) have their base address set to 0 and their limit set to the entire address space — effectively making them useless for segmentation.

However, **FS and GS** are critically important in the Linux kernel and modern software.

```
SEGMENT REGISTERS IN x86-64
═══════════════════════════════════════════════════════════════

Register │ Full Name        │ Linux Usage
─────────┼──────────────────┼─────────────────────────────────────
CS       │ Code Segment     │ CPL (bits 0-1) = privilege level
         │                  │ 0 = ring 0 (kernel), 3 = ring 3 (user)
DS       │ Data Segment     │ Effectively unused (base=0 always)
ES       │ Extra Segment    │ Effectively unused (base=0 always)
FS       │ F Segment        │ Thread-Local Storage (TLS) in userspace
         │                  │ per-CPU data in kernel (on some kernels)
GS       │ G Segment        │ per-CPU data in Linux kernel
         │                  │ TLS in Windows (difference from Linux)
SS       │ Stack Segment    │ Effectively unused (base=0 always)

FS and GS are special — their BASE addresses are configurable:
  MSR FS_BASE (0xC0000100) → base address of FS segment
  MSR GS_BASE (0xC0000101) → base address of GS segment
  MSR KERNEL_GS_BASE (0xC0000102) → swapped with GS_BASE by SWAPGS

SWAPGS INSTRUCTION:
  Used when entering kernel from user space:
    User  GS_BASE  → points to thread's TLS
    Kernel GS_BASE → points to per-CPU kernel data

  On syscall/interrupt entry:
    SWAPGS   ; swap GS_BASE with KERNEL_GS_BASE
    ; now GS points to kernel's per-CPU area
    MOV RAX, [GS:current_task_offset]  ; access current task_struct

PER-CPU DATA STRUCTURE (Linux kernel):
  ┌───────────────────────────────────────────────────────┐
  │  GS_BASE ──────────────────────────────────────────►  │
  │                                                        │
  │  CPU 0's per-CPU data:                                 │
  │    current_task       (pointer to running task_struct) │
  │    kernel_stack       (kernel stack pointer)           │
  │    irq_stack          (IRQ stack pointer)              │
  │    cpu_number         (which CPU this is)              │
  │    preempt_count      (preemption count)               │
  │    ...                                                 │
  └───────────────────────────────────────────────────────┘
  CPU 1, CPU 2 ... each have their own such area.
  GS_BASE per CPU points to that CPU's area.
```

---

## 8. Control Registers (x86-64)

Control registers configure fundamental CPU behavior. They are **only accessible from ring 0 (kernel mode)** — user space cannot read or write them.

```
CONTROL REGISTERS
═══════════════════════════════════════════════════════════════════

CR0 — System Control
────────────────────────────────────────────────────────────────────
Bit 31 (PG)  : Paging Enable — enables virtual memory
Bit 30 (CD)  : Cache Disable
Bit 29 (NW)  : Not Write-through
Bit 18 (AM)  : Alignment Mask
Bit 16 (WP)  : Write Protect — even ring 0 can't write to read-only pages
Bit  5 (NE)  : Numeric Error (x87 FPU error handling)
Bit  4 (ET)  : Extension Type (always 1 on modern CPUs)
Bit  3 (TS)  : Task Switched — used for lazy FPU context save
Bit  2 (EM)  : Emulation — if set, no FPU (emulate in software)
Bit  1 (MP)  : Monitor co-Processor
Bit  0 (PE)  : Protection Enable — enables protected mode

CR2 — Page Fault Linear Address
────────────────────────────────────────────────────────────────────
When a page fault occurs, CR2 is automatically loaded with the
virtual address that caused the fault.

  do_page_fault() in Linux:
    fault_address = read_cr2();  // the faulting virtual address

CR3 — Page Directory Base Register (PDBR)
────────────────────────────────────────────────────────────────────
Contains the physical address of the top-level page table (PGD).

  ┌────────────────────────────────────────────────────────────┐
  │ CR3                                                        │
  │ Bits 63-12: Physical address of Page Global Directory (PGD)│
  │ Bit  3 (PWT): Page-level Write Through                     │
  │ Bit  4 (PCD): Page-level Cache Disable                     │
  │ Bits 11-5: PCID (Process Context ID) if PCIDE=1 in CR4    │
  └────────────────────────────────────────────────────────────┘

  On context switch: CR3 is updated → flushes TLB
  This is why context switches are expensive!

  Kernel Address Space Isolation (KPTI/Meltdown fix):
    Two CR3 values per process:
      - User CR3: maps user space + minimal kernel trampoline
      - Kernel CR3: maps full kernel + user space
    SWAPGS + CR3 swap on every syscall/interrupt (performance hit!)

CR4 — Feature Control
────────────────────────────────────────────────────────────────────
Bit 20 (SMEP): Supervisor Mode Execution Prevention
               Ring 0 cannot execute code in user-space pages
               Security feature against kernel exploits
Bit 19 (SMAP): Supervisor Mode Access Prevention
               Ring 0 cannot access user-space pages without STAC/CLAC
Bit 17 (PCIDE): Process Context ID Enable
Bit  9 (OSFXSR): OS support for FXSAVE/FXRSTOR
Bit  7 (PGE): Page Global Enable — global pages not flushed on CR3 write
Bit  5 (PAE): Physical Address Extension — 64-bit physical addresses
Bit  4 (PSE): Page Size Extension — 4MB pages (legacy)

CR8 — Task Priority Register
────────────────────────────────────────────────────────────────────
Controls which interrupts are allowed to preempt the current task.
  CR8 = 0 → all interrupts allowed
  CR8 = 15 → no external interrupts allowed
  Used in conjunction with APIC TPR (Task Priority Register)
```

---

## 9. Debug Registers (x86-64)

Debug registers provide **hardware breakpoint** capability — the ability to break execution when a specific memory address is accessed, without modifying the code (unlike software INT3 breakpoints).

```
DEBUG REGISTERS
═══════════════════════════════════════════════════════════════════

DR0, DR1, DR2, DR3 — Breakpoint Address Registers
  Each holds a 64-bit linear address for a hardware breakpoint.
  Up to 4 hardware breakpoints simultaneously.

DR6 — Debug Status Register (read by exception handler)
────────────────────────────────────────────────────────────────────
Bit 3 (B3): Breakpoint DR3 was triggered
Bit 2 (B2): Breakpoint DR2 was triggered
Bit 1 (B1): Breakpoint DR1 was triggered
Bit 0 (B0): Breakpoint DR0 was triggered
Bit 14 (BT): Task switch breakpoint
Bit 13 (BD): Debug register access
Bit 12 (BS): Single-step breakpoint (TF flag in RFLAGS)

DR7 — Debug Control Register (configures breakpoints)
────────────────────────────────────────────────────────────────────
For each breakpoint i (0–3):
  Bits 2i+1, 2i (G0-G3, L0-L3): Global/Local enable for breakpoint i
  Bits 18+4i to 16+4i (Condition): When to break:
    00 = Execution (when instruction at DRi is fetched)
    01 = Data Write (when DRi address is written)
    10 = I/O port access (if CR4.DE=1)
    11 = Data Read OR Write (but not instruction fetch)
  Bits 22+4i, 23+4i (Size):
    00 = 1 byte
    01 = 2 bytes
    10 = 8 bytes (64-bit)
    11 = 4 bytes

PTRACE AND DEBUG REGISTERS:
  Linux exposes debug registers via ptrace(PTRACE_POKEUSER, ...)
  GDB uses these internally for hardware watchpoints:
    (gdb) watch variable   → sets DR0-DR3 via ptrace
    (gdb) break *0xaddr    → sets INT3 in code (software breakpoint)
                           → or DR0-DR3 (hardware execution breakpoint)
```

---

## 10. SIMD / Floating-Point Registers

### x87 FPU (Legacy)

```
x87 FPU REGISTER STACK
═══════════════════════════════════════════════════════════════

  8 registers in a STACK configuration:
  ST(0) ← top of stack (most recently pushed)
  ST(1)
  ST(2)
  ...
  ST(7)

  Each is 80-bit extended precision:
  ┌──────────────────────────────────────────────────────┐
  │ 79  Sign │ 78-64  Exponent (15-bit) │ 63-0  Mantissa │
  └──────────────────────────────────────────────────────┘

  Operations:
    FLD   → push value onto FPU stack
    FSTP  → pop value from FPU stack and store
    FADD  → ST(0) = ST(0) + ST(1)

  Linux kernel NEVER uses x87 — only SSE/AVX.
  Userspace C programs: compiler uses SSE by default (-mfpmath=sse)
```

### SSE/AVX Registers

```
XMM / YMM / ZMM REGISTER HIERARCHY
═══════════════════════════════════════════════════════════════

ZMM0 (512-bit) = AVX-512
├── YMM0 (256-bit, lower half of ZMM0) = AVX/AVX2
│   └── XMM0 (128-bit, lower half of YMM0) = SSE

ZMM0:
┌─────────────────────────────────────────────────────────────────┐
│ 511                 256│255              128│127              0  │
│   upper ZMM (256-bit)  │  upper YMM (128)  │     XMM0 (128)    │
└─────────────────────────────────────────────────────────────────┘

XMM can hold:
  2 × double (64-bit float)   — "packed double" pd
  4 × float  (32-bit float)   — "packed single" ps
  2 × int64 (64-bit integer)  — "packed qword"
  4 × int32 (32-bit integer)  — "packed dword"
  8 × int16 (16-bit integer)  — "packed word"
 16 × int8  (8-bit integer)   — "packed byte"

SCALAR vs PACKED operations:
  ADDSS XMM0, XMM1 → add single scalar float (only lowest 32 bits)
  ADDPS XMM0, XMM1 → add 4 floats in parallel (packed single)
  ADDPD XMM0, XMM1 → add 2 doubles in parallel (packed double)

Linux kernel SIMD rules:
  - Kernel code CANNOT use SIMD by default
  - SIMD registers not saved on context switch by default
    (lazy FPU: only saved when userspace uses them)
  - Kernel can use SIMD with: kernel_fpu_begin() / kernel_fpu_end()
    These save/restore the full FPU state
  - Used in: crypto (AES-NI), RAID parity, copy operations
```

---

## 11. Model-Specific Registers (MSRs)

MSRs are a class of special registers unique to each processor model (hence "model-specific"). They control features, performance counters, power management, and system-level configuration.

```
IMPORTANT MSRs IN LINUX
═══════════════════════════════════════════════════════════════

Access:
  RDMSR: Read MSR (ECX = MSR address → result in EDX:EAX)
  WRMSR: Write MSR (ECX = MSR address, value in EDX:EAX)
  Both are PRIVILEGED — only ring 0 can execute them

MSR Address │ Name              │ Purpose
────────────┼───────────────────┼───────────────────────────────────
0xC000_0080 │ EFER              │ Extended Feature Enable Register
            │                   │ Bit 8 (LME): Long Mode Enable
            │                   │ Bit 10 (LMA): Long Mode Active
            │                   │ Bit 11 (NXE): No-Execute Enable
────────────┼───────────────────┼───────────────────────────────────
0xC000_0081 │ STAR              │ Syscall Target Address (legacy 32-bit)
            │                   │ Bits 63-48: SYSRET CS/SS selectors
            │                   │ Bits 47-32: SYSCALL CS/SS selectors
────────────┼───────────────────┼───────────────────────────────────
0xC000_0082 │ LSTAR             │ Long Mode SYSCALL Target
            │                   │ = address of kernel's syscall entry
            │                   │ (entry_SYSCALL_64 in Linux)
────────────┼───────────────────┼───────────────────────────────────
0xC000_0084 │ SFMASK            │ SYSCALL FLAGS Mask
            │                   │ Bits cleared in RFLAGS during SYSCALL
────────────┼───────────────────┼───────────────────────────────────
0xC000_0100 │ FS_BASE           │ Base address of FS segment
            │                   │ = Thread Local Storage (TLS) pointer
────────────┼───────────────────┼───────────────────────────────────
0xC000_0101 │ GS_BASE           │ Base address of GS segment
            │                   │ = per-CPU area pointer (kernel mode)
────────────┼───────────────────┼───────────────────────────────────
0xC000_0102 │ KERNEL_GS_BASE    │ Shadow GS base (swapped by SWAPGS)
────────────┼───────────────────┼───────────────────────────────────
0x0000_010A │ IA32_ARCH_CAP     │ Architecture capabilities (Meltdown fix)
────────────┼───────────────────┼───────────────────────────────────
0x0000_0174 │ IA32_SYSENTER_CS  │ SYSENTER target CS (legacy syscall)
0x0000_0175 │ IA32_SYSENTER_ESP │ SYSENTER target ESP
0x0000_0176 │ IA32_SYSENTER_EIP │ SYSENTER entry point
────────────┼───────────────────┼───────────────────────────────────
0x0000_0186 │ PERF_EVENTSELx    │ Performance monitoring event select
0x0000_00C1 │ PMC0              │ Performance counter 0
────────────┼───────────────────┼───────────────────────────────────
0x0000_019A │ IA32_CLOCK_MOD    │ Clock modulation (thermal throttle)
0x0000_01A0 │ IA32_MISC_ENABLE  │ Misc enables (Enhanced SpeedStep, etc.)
────────────┼───────────────────┼───────────────────────────────────
0x0000_048F │ TSX_CTRL          │ TSX (Transactional Sync Ext) control
            │                   │ Meltdown/TAA vulnerability mitigation

How Linux sets up SYSCALL:
  // arch/x86/kernel/cpu/common.c
  wrmsrl(MSR_LSTAR, (unsigned long)entry_SYSCALL_64);
  wrmsrl(MSR_STAR, ...);
  wrmsrl(MSR_SYSCALL_MASK, X86_EFLAGS_TF|X86_EFLAGS_DF|...);
```

---

## 12. The EFLAGS / RFLAGS Register

RFLAGS is a 64-bit register (called EFLAGS in 32-bit mode) that contains **condition codes**, **control bits**, and **system flags**. It's the CPU's "state machine status panel."

```
RFLAGS BIT MAP
═══════════════════════════════════════════════════════════════

Bit │ Symbol │ Name                  │ Description
────┼────────┼───────────────────────┼──────────────────────────────
 0  │  CF    │ Carry Flag            │ Arithmetic carry/borrow
    │        │                       │ Also: bit shift carry-out
 2  │  PF    │ Parity Flag           │ Parity of lowest byte of result
 4  │  AF    │ Auxiliary Carry Flag  │ Carry between nibbles (BCD)
 6  │  ZF    │ Zero Flag             │ Set if result == 0
 7  │  SF    │ Sign Flag             │ Set if result MSB == 1 (negative)
 8  │  TF    │ Trap Flag             │ Enable single-step mode (debug)
 9  │  IF    │ Interrupt Enable Flag │ IF=1: hardware interrupts enabled
10  │  DF    │ Direction Flag        │ DF=0: string ops go forward
    │        │                       │ DF=1: string ops go backward
11  │  OF    │ Overflow Flag         │ Signed arithmetic overflow
12-13│  IOPL │ I/O Privilege Level   │ Min privilege for I/O instructions
14  │  NT    │ Nested Task           │ For nested tasks (legacy TSS)
16  │  RF    │ Resume Flag           │ Suppress debug exceptions
17  │  VM    │ Virtual-8086 Mode     │ Enable V8086 mode (legacy)
18  │  AC    │ Alignment Check       │ Trap on misaligned memory access
19  │  VIF   │ Virtual Interrupt Flag│ Virtual IF for V8086
20  │  VIP   │ Virtual Interrupt Pend│ Pending virtual interrupt
21  │  ID    │ ID Flag               │ CPUID instruction supported

CRITICAL FLAGS FOR ALGORITHM THINKING:
  ZF (Zero Flag):   JZ/JNZ, SETZ, test if result is zero
  SF (Sign Flag):   JS/JNS, test if result is negative
  CF (Carry Flag):  JC/JNC, multi-precision arithmetic, rotate
  OF (Overflow):    JO/JNO, signed overflow detection
  PF (Parity):      Used in float comparisons, CRC checks

HOW CONDITIONAL JUMPS USE FLAGS:
  After: CMP RAX, RBX   (computes RAX - RBX, sets flags, discards result)
  After: TEST RAX, RBX  (computes RAX & RBX, sets flags, discards result)

  Condition │ Flags          │ Meaning
  ──────────┼────────────────┼────────────────────────────────
  JE / JZ   │ ZF=1           │ Equal / Zero
  JNE / JNZ │ ZF=0           │ Not equal / Not zero
  JL / JNGE │ SF≠OF          │ Less than (signed)
  JLE / JNG │ ZF=1 or SF≠OF  │ Less or equal (signed)
  JG / JNLE │ ZF=0 and SF=OF │ Greater than (signed)
  JGE / JNL │ SF=OF          │ Greater or equal (signed)
  JB / JNAE │ CF=1           │ Below (unsigned)
  JBE / JNA │ CF=1 or ZF=1   │ Below or equal (unsigned)
  JA / JNBE │ CF=0 and ZF=0  │ Above (unsigned)
  JAE / JNB │ CF=0           │ Above or equal (unsigned)

SYSCALL AND RFLAGS:
  During SYSCALL:
    RFLAGS is saved in R11 (automatically by hardware)
    RFLAGS is masked by SFMASK MSR (IF=0, TF=0, DF=0, etc.)
    → This disables interrupts and debug traps in kernel entry

  During SYSRET:
    RFLAGS is restored from R11
    → R11 is trashed after a syscall (it holds the saved flags)
```

---

## 13. Calling Conventions — How Registers Are Used by ABI

### What Is an ABI?

**ABI** = Application Binary Interface. It's a contract between:
- Compiler A and Compiler B
- Compiler and Operating System
- Kernel and Userspace

It defines: how arguments are passed, where return values go, which registers can be trashed, how the stack is laid out.

### System V AMD64 ABI (Linux x86-64)

```
SYSTEM V AMD64 ABI — ARGUMENT PASSING
═══════════════════════════════════════════════════════════════

INTEGER / POINTER ARGUMENTS (up to 6):
  Argument #  │ Register
  ────────────┼──────────
       1      │  RDI
       2      │  RSI
       3      │  RDX
       4      │  RCX
       5      │  R8
       6      │  R9
      7+      │  pushed onto stack (in reverse order)

FLOATING-POINT ARGUMENTS (up to 8):
  Argument #  │ Register
  ────────────┼──────────
      1-8     │  XMM0–XMM7
      9+      │  pushed onto stack

RETURN VALUES:
  Type            │ Location
  ────────────────┼────────────────────────────────
  Integer ≤ 64bit │ RAX
  Integer 128bit  │ RAX (low), RDX (high)
  Float/Double    │ XMM0
  2 × Float       │ XMM0 (1st), XMM1 (2nd)
  Struct ≤ 16B    │ RAX + RDX (packed)
  Struct > 16B    │ Caller allocates memory, passes ptr in RDI
                  │ Function writes to that memory, returns ptr in RAX

STACK FRAME LAYOUT:
  (higher address)
  ┌──────────────────────────────────────────┐
  │ ... caller's locals ...                  │
  ├──────────────────────────────────────────┤ ← old RSP
  │ arg 8 (if > 6 args)                      │ ← pushed last
  │ arg 7                                    │
  ├──────────────────────────────────────────┤
  │ RETURN ADDRESS (pushed by CALL)          │ ← [RSP+0] on entry
  ├──────────────────────────────────────────┤ ← RSP on function entry
  │ saved RBP (optional)                     │ ← if frame pointer used
  ├──────────────────────────────────────────┤ ← RBP (frame pointer)
  │ local variable 1                         │
  │ local variable 2                         │
  │ ... locals ...                           │
  │ saved callee regs (RBX, R12-R15)         │
  ├──────────────────────────────────────────┤ ← RSP (stack pointer)
  │ (16-byte aligned before next CALL)       │
  └──────────────────────────────────────────┘

EXAMPLE: int add(int a, int b, int c) { return a + b + c; }
  Compiled to:
    add:
        LEA EAX, [RDI + RSI]   ; EAX = a + b
        ADD EAX, EDX           ; EAX += c
        RET                    ; return EAX (= RAX lower 32 bits)
  Caller: add(1, 2, 3)
        MOV EDI, 1             ; arg1 in RDI
        MOV ESI, 2             ; arg2 in RSI
        MOV EDX, 3             ; arg3 in RDX
        CALL add
        ; result now in RAX (= EAX = 6)
```

### ARM64 AAPCS64 ABI

```
ARM64 ABI (AAPCS64) — ARGUMENT PASSING
═══════════════════════════════════════════════════════════════

INTEGER / POINTER ARGUMENTS (up to 8):
  X0–X7 for arguments 1–8
  Stack for argument 9+

FLOAT/SIMD ARGUMENTS (up to 8):
  V0–V7 (D0–D7 for double, S0–S7 for float)

RETURN VALUES:
  Integer: X0 (and X1 for 128-bit)
  Float:   V0 (D0 for double, S0 for float)

CALLEE-SAVED: X19–X28, X29 (FP), X30 (LR), SP, V8–V15
CALLER-SAVED: X0–X18, X30, V0–V7, V16–V31

KEY DIFFERENCE FROM x86-64:
  ARM64 has a dedicated Link Register (X30/LR):
    BL function_name    ; Branch with Link — saves PC+4 into X30
    ; inside function ...
    RET                 ; = BR X30 — branch to address in X30

  Nested calls: X30 must be saved to stack
    function:
        STP X29, X30, [SP, #-16]!   ; push FP and LR
        MOV X29, SP                  ; set frame pointer
        ; ... call other functions ...
        LDP X29, X30, [SP], #16     ; restore FP and LR
        RET
```

---

## 14. The Linux Kernel and Registers: `pt_regs`

### What Is `pt_regs`?

When the CPU transitions from **user space (ring 3)** to **kernel space (ring 0)** — via syscall, interrupt, or exception — the hardware and early kernel assembly code save all user-space register values to a structure on the kernel stack. This structure is called `pt_regs` ("process trace registers").

It is the **complete snapshot of the CPU state** at the moment of kernel entry.

```
pt_regs STRUCTURE AND KERNEL STACK LAYOUT (x86-64)
═══════════════════════════════════════════════════════════════

Linux source: arch/x86/include/asm/ptrace.h

struct pt_regs {
    unsigned long r15;   // +0x00
    unsigned long r14;   // +0x08
    unsigned long r13;   // +0x10
    unsigned long r12;   // +0x18
    unsigned long rbp;   // +0x20
    unsigned long rbx;   // +0x28
    // Arguments: pushed in reverse order
    unsigned long r11;   // +0x30
    unsigned long r10;   // +0x38
    unsigned long r9;    // +0x40
    unsigned long r8;    // +0x48
    unsigned long rax;   // +0x50
    unsigned long rcx;   // +0x58
    unsigned long rdx;   // +0x60
    unsigned long rsi;   // +0x68
    unsigned long rdi;   // +0x70
    // Fields below are pushed by hardware or syscall entry asm:
    unsigned long orig_rax;  // +0x78 = original syscall number
    unsigned long rip;       // +0x80
    unsigned long cs;        // +0x88
    unsigned long eflags;    // +0x90
    unsigned long rsp;       // +0x98
    unsigned long ss;        // +0xA0
};

KERNEL STACK LAYOUT DURING SYSCALL:
  (high address)
  ┌───────────────────────────────────────────────────────┐
  │  SS        (user stack segment)      pushed by CPU    │
  │  RSP       (user stack pointer)      pushed by CPU    │
  │  RFLAGS    (saved in R11 by SYSCALL) pushed by asm    │
  │  CS        (user code segment)       pushed by CPU    │
  │  RIP       (return address)          pushed by CPU    │
  │  orig_rax  (syscall number)          pushed by asm    │
  ├───────────────────────────────────────────────────────┤ ← pt_regs start
  │  RDI  RSI  RDX  RCX  RAX  R8-R11                     │
  │  RBX  RBP  R12  R13  R14  R15                         │
  └───────────────────────────────────────────────────────┘ ← kernel stack top

WHY orig_rax?
  RAX is used for BOTH the syscall number (on entry)
  AND the return value (on exit).
  orig_rax preserves the original syscall number so the kernel
  can restart the syscall (e.g., after EINTR from a signal).

ACCESSING pt_regs:
  // In a syscall handler, pt_regs is accessible via:
  struct pt_regs *regs = current_pt_regs();

  // Or directly in the entry point assembly:
  // RSP points to the bottom of pt_regs on kernel stack
  // The do_syscall_64() function receives pt_regs*
```

### The Path of a Syscall Through Registers

```
SYSCALL FLOW: REGISTER JOURNEY
═══════════════════════════════════════════════════════════════

USER SPACE:                     KERNEL SPACE:
                                (entry_SYSCALL_64)
  RAX = syscall number  ──────► orig_rax saved
  RDI = arg 1           ──────► accessible as regs->di
  RSI = arg 2           ──────► accessible as regs->si
  RDX = arg 3           ──────► accessible as regs->dx
  R10 = arg 4           ──────► accessible as regs->r10
                                (NOT RCX! RCX is trashed by SYSCALL)
  R8  = arg 5           ──────► accessible as regs->r8
  R9  = arg 6           ──────► accessible as regs->r9

  SYSCALL instruction:
    1. Saves RIP into RCX  (so SYSCALL trashes RCX in userspace)
    2. Saves RFLAGS into R11 (trashes R11)
    3. Loads new RIP from MSR_LSTAR (= entry_SYSCALL_64)
    4. Clears RFLAGS bits per MSR_SFMASK
    5. Does NOT switch stacks (kernel uses SWAPGS + GS to find kernel stack)

  Entry assembly (entry_SYSCALL_64):
    SWAPGS                          ; switch to kernel GS_BASE
    MOV [GS:rsp_scratch], RSP       ; save user RSP
    MOV RSP, [GS:kernel_stack]      ; switch to kernel stack
    PUSH SS, RSP, R11(RFLAGS), CS, RIP (orig)
    PUSH orig_rax (= RAX = syscall #)
    PUSH registers (RDI..R15)
    CALL do_syscall_64(regs, orig_rax)
      → syscall_table[orig_rax](regs)
      → e.g., __x64_sys_read(regs)
          → fd   = regs->di
          → buf  = regs->si
          → count= regs->dx
          → return value placed in regs->ax
    POP registers
    SWAPGS
    SYSRETQ                         ; restores RIP from RCX, RFLAGS from R11

COMPLETE FLOW DIAGRAM:
  User process                   CPU hardware              Linux kernel
  ──────────                     ────────────              ────────────
  RAX=1(write)                       │                         │
  RDI=fd                             │                         │
  RSI=buf                            │                         │
  RDX=len                            │                         │
  SYSCALL ──────────────────────────►│                         │
                                     │ Save RIP→RCX            │
                                     │ Save RFLAGS→R11         │
                                     │ RIP = MSR_LSTAR ────────►│ entry_SYSCALL_64
                                     │                         │ SWAPGS
                                     │                         │ switch stack
                                     │                         │ push pt_regs
                                     │                         │ do_syscall_64()
                                     │                         │ sys_write(regs)
                                     │                         │ regs->ax = retval
                                     │                         │ pop pt_regs
                                     │                         │ SWAPGS
                                     │◄────────────────────────│ SYSRETQ
                                     │ RIP = RCX (user RIP)    │
                                     │ RFLAGS = R11            │
  RAX = return value◄────────────────│                         │
```

---

## 15. System Calls — The Register Dance

### Five Syscall Mechanisms (Historical)

```
SYSCALL MECHANISMS (x86)
═══════════════════════════════════════════════════════════════

1. INT 0x80 (32-bit Linux, legacy):
   - Software interrupt
   - Very slow: full IDT lookup, privilege level check, ring transition
   - Registers: EAX=syscall#, EBX,ECX,EDX,ESI,EDI,EBP = args
   - Still works on 64-bit Linux for 32-bit compatibility (IA32)

2. SYSENTER/SYSEXIT (Intel, 32-bit):
   - Introduced in Pentium II for faster syscalls
   - Uses MSRs: IA32_SYSENTER_CS, _ESP, _EIP
   - Faster than INT 0x80 (no IDT lookup)

3. SYSCALL/SYSRET (AMD64, used by 64-bit Linux):
   - Fastest mechanism on x86-64
   - Uses MSRs: LSTAR (entry), STAR (segments), SFMASK (flags mask)
   - SYSCALL: saves RIP→RCX, RFLAGS→R11, jumps to LSTAR
   - SYSRET: restores from RCX, R11
   - Does NOT automatically switch stacks!

4. VDSO (Virtual Dynamic Shared Object):
   - Kernel maps a shared library into every user process
   - Contains: gettimeofday, clock_gettime, getcpu
   - These read kernel data directly (via vsyscall page) — no ring switch!
   - Pure register/memory operations, fastest of all

5. vsyscall (deprecated):
   - Fixed mapping at 0xFFFF_FFFF_FF60_0000
   - Security risk (fixed address = ROP gadget)
   - Replaced by VDSO
```

### The Six Syscall Arguments — Why Only Six?

```
WHY ONLY 6 ARGUMENTS IN SYSCALL ABI?
═══════════════════════════════════════════════════════════════

SYSCALL uses:
  RAX  = syscall number (consumed)
  RCX  = saved RIP (trashed by CPU hardware)
  R11  = saved RFLAGS (trashed by CPU hardware)

REMAINING GPRs FOR ARGS: RDI, RSI, RDX, R10, R8, R9 = 6 registers
  (Note: R10 instead of RCX because RCX is trashed!)

If a syscall needs more than 6 args:
  → Pass a POINTER to a struct containing the args
  → Example: clone3() passes a struct clone_args pointer
  → Example: io_uring_enter() passes pointer to extra args

SYSTEM CALL TABLE (partial, x86-64):
  Number │ Name         │ RDI       │ RSI        │ RDX     │ R10      │
  ───────┼──────────────┼───────────┼────────────┼─────────┼──────────┤
    0    │ read         │ fd        │ buf*       │ count   │          │
    1    │ write        │ fd        │ buf*       │ count   │          │
    2    │ open         │ filename* │ flags      │ mode    │          │
    3    │ close        │ fd        │            │         │          │
    9    │ mmap         │ addr      │ length     │ prot    │ flags    │
   56    │ clone        │ flags     │ newsp      │ parent* │ child*   │
   60    │ exit         │ status    │            │         │          │
  231    │ exit_group   │ status    │            │         │          │
```

---

## 16. Context Switching — Saving & Restoring Registers

### What Is a Context Switch?

A **context switch** occurs when the OS scheduler decides to stop running process A and start running process B (or resume process A on a different CPU). The CPU state — all registers — must be saved for A and restored for B.

```
CONTEXT SWITCH: THE COMPLETE REGISTER PICTURE
═══════════════════════════════════════════════════════════════

What must be saved per thread/task?
  ┌─────────────────────────────────────────────────────────────┐
  │  thread_struct (inside task_struct)                         │
  │                                                             │
  │  Saved registers:                                           │
  │    sp  (stack pointer = RSP)    — mandatory                 │
  │    ip  (instruction ptr = RIP)  — set by __switch_to_asm   │
  │    flags (RFLAGS)               — saved via pushfq          │
  │    es, ds, fs, gs               — segment registers         │
  │    fs_base, gs_base             — MSR values for TLS        │
  │    ... more arch-specific ...                               │
  │                                                             │
  │  Saved in thread_struct.fpu:                                │
  │    XMM0–XMM15 (or YMM/ZMM)     — FPU/SIMD state           │
  │    x87 FPU state                — if used                   │
  │    MXCSR (SSE control register) — rounding mode etc.        │
  └─────────────────────────────────────────────────────────────┘

WHY NOT SAVE ALL GPRs IN thread_struct?
  The callee-saved convention is exploited!
  __switch_to_asm is called like a normal C function.
  → Callee-saved regs (RBX, RBP, R12-R15) are pushed to the KERNEL stack
    by the compiler-generated prologue.
  → Only RSP needs to be saved in thread_struct
  → Restoring RSP restores the kernel stack → popping from it
    restores all the callee-saved regs.

CONTEXT SWITCH CODE FLOW (x86-64):
  schedule()
    → __schedule()
      → context_switch(rq, prev, next)
        → switch_mm(prev->mm, next->mm, next)
          → CR3 = next->mm->pgd (page table switch — TLB flush!)
        → switch_to(prev, next, prev)
          → __switch_to_asm(prev, next)  ← in arch/x86/entry/entry_64.S
          → __switch_to(prev, next)      ← in arch/x86/kernel/process_64.c

__switch_to_asm (simplified Assembly):
  __switch_to_asm:
      // Save callee-saved regs of 'prev' to its kernel stack
      pushq %rbp
      pushq %rbx
      pushq %r12
      pushq %r13
      pushq %r14
      pushq %r15

      // Save 'prev' stack pointer
      movq %rsp, TASK_threadsp(%rdi)    ; prev->thread.sp = RSP

      // Load 'next' stack pointer
      movq TASK_threadsp(%rsi), %rsp    ; RSP = next->thread.sp

      // (optional) Update stack canary for stack overflow detection

      // Pop callee-saved regs of 'next' from its kernel stack
      popq %r15
      popq %r14
      popq %r13
      popq %r12
      popq %rbx
      popq %rbp

      // Jump to __switch_to (C function) to finish (FS/GS base, FPU, etc.)
      jmp __switch_to

TIMELINE OF A CONTEXT SWITCH:
  Task A                         Scheduler              Task B
  ──────                         ─────────              ──────
  running ...                        │                     (sleeping)
  (interrupt or yield)               │                         │
  enters kernel                      │                         │
  RSP → kernel stack A               │                         │
      │                              │                         │
      └──────────► schedule() ───────┤                         │
                  pushes R15-RBX     │                         │
                  saves RSP → A.sp   │                         │
                  loads RSP ← B.sp ──┼─────────────────────────►│
                  pops R15-RBX                               (resumes)
                  (was saved when B                          RSP = B's
                  last switched out)                         kernel stack
                                                             returns from
                                                             its last call
```

### FPU/SIMD Lazy Save

```
LAZY FPU CONTEXT SAVE
═══════════════════════════════════════════════════════════════

Saving 512 bytes of SIMD registers (XMM0-XMM15 + MXCSR + ...) on
EVERY context switch would be expensive if most tasks don't use FPU.

SOLUTION: Lazy FPU saving

  When task A is running:   CR0.TS = 0 (task switched flag clear)
                            → FPU instructions execute normally

  On context switch to B:   CR0.TS = 1 (set task switched flag)
                            → FPU instructions will FAULT (#NM device-not-avail)
                            → FPU state is NOT yet saved!

  When task B uses FPU:     #NM exception fires
                            → do_device_not_available() handler runs
                            → SAVES task A's FPU state NOW
                            → RESTORES task B's FPU state
                            → Clears CR0.TS
                            → Retries the FPU instruction

  This optimization means FPU state is only saved/restored when
  BOTH tasks actually use FPU.

MODERN APPROACH: Eager FPU (since kernel 4.2 for XSAVE):
  With XSAVEOPT/XSAVES instructions, saving is optimized to only
  save registers that have actually changed (hardware tracks this).
  The overhead is small enough that lazy saving is no longer used.
```

---

## 17. Interrupt Handling and Registers

### Hardware Interrupt Flow

```
HARDWARE INTERRUPT: REGISTER LIFECYCLE
═══════════════════════════════════════════════════════════════

  CPU is executing userspace code.
  Disk controller fires IRQ (interrupt request).

  HARDWARE AUTOMATICALLY:
    1. Checks IF flag in RFLAGS — if IF=0, interrupts disabled, ignore
    2. Acknowledges interrupt from APIC (gets interrupt vector number)
    3. Looks up IDT[vector] for the handler address
    4. Pushes to CURRENT stack (or switches to IST stack if configured):
         SS    (user stack segment)
         RSP   (user stack pointer)
         RFLAGS
         CS    (user code segment)
         RIP   (return address = next instruction to execute)
         Error code (for some exceptions like page fault, #GP)
    5. Loads new CS:RIP from IDT descriptor
    6. Loads new SS:RSP from TSS (Task State Segment) if ring change

  KERNEL ENTRY ASSEMBLY (arch/x86/entry/entry_64.S):
    irq_entry:
        SWAPGS_UNSAFE_STACK      ; switch to kernel GS if from userspace
        cld                      ; clear DF (direction flag)
        PUSH_REGS                ; push all GPRs → build pt_regs
        movq %rsp, %rdi          ; pass pt_regs* as 1st argument
        call do_IRQ              ; or specific handler

  IDT (Interrupt Descriptor Table):
  ┌───────────────────────────────────────────────────────────────┐
  │ Vector │ Handler              │ Description                    │
  ├────────┼──────────────────────┼────────────────────────────────┤
  │   0    │ divide_error         │ #DE Division by zero           │
  │   1    │ debug                │ #DB Debug exception            │
  │   2    │ nmi                  │ NMI Non-Maskable Interrupt      │
  │   3    │ int3                 │ #BP Breakpoint (INT3)          │
  │   4    │ overflow             │ #OF Overflow (INTO)            │
  │   6    │ invalid_op           │ #UD Invalid Opcode             │
  │   7    │ device_not_available │ #NM No FPU                     │
  │   8    │ double_fault         │ #DF (uses IST stack!)          │
  │   13   │ general_protection   │ #GP General Protection Fault   │
  │   14   │ page_fault           │ #PF Page Fault (CR2=address)   │
  │  32–47 │ IRQ0–IRQ15           │ Hardware IRQs (8259A PIC)      │
  │ 48–255 │ APIC / MSI           │ APIC interrupts                │
  │  128   │ ia32_syscall         │ INT 0x80 (32-bit compat)       │
  │  242   │ CALL_FUNCTION_VECTOR │ IPI: call function on this CPU │
  │  251   │ RESCHEDULE_VECTOR    │ IPI: reschedule this CPU       │
  └────────┴──────────────────────┴────────────────────────────────┘

IST (Interrupt Stack Table) — for critical exceptions:
  #DF (double fault), #NMI, #MC (machine check) use dedicated stacks
  defined in the TSS — prevents stack overflow from corrupting handler
```

---

## 18. Signals and Register State

### What Happens to Registers During Signal Delivery

```
SIGNAL DELIVERY: REGISTER STATE MANIPULATION
═══════════════════════════════════════════════════════════════

When the kernel delivers a signal to a user process:
  1. Process is in kernel mode (returning from syscall/interrupt)
  2. Kernel checks for pending signals
  3. Kernel sets up a SIGNAL FRAME on the user's STACK
  4. Changes user RIP to point to the signal handler
  5. Returns to user space — handler runs

SIGNAL FRAME layout on user stack (x86-64):
  ┌───────────────────────────────────────────────────────┐
  │  siginfo_t         │ signal info (signo, code, etc.)  │
  │  ucontext_t        │ complete CPU state snapshot       │
  │    uc_mcontext     │                                   │
  │      gregs[REG_RIP]│ saved RIP (where to return)       │
  │      gregs[REG_RSP]│ saved RSP                         │
  │      gregs[REG_RAX]│ saved RAX (syscall return value!) │
  │      ... all GPRs  │                                   │
  │      fpregs*       │ pointer to FPU state              │
  │  FPU state (xstate)│ XMM/YMM registers if used        │
  │  RESTORER (trampoline):                                │
  │    MOV EAX, 15     │ syscall: rt_sigreturn            │
  │    SYSCALL         │                                   │
  └───────────────────────────────────────────────────────┘

ON RETURN FROM SIGNAL HANDLER:
  Handler calls return address → hits RESTORER trampoline
  RESTORER executes: syscall rt_sigreturn (syscall #15)
  Kernel: rt_sigreturn()
    → reads ucontext from user stack
    → restores ALL registers from the saved state
    → process continues as if signal never happened

REGISTER MANIPULATION FOR PROCESS INFECTION (understanding, not malice):
  ptrace(PTRACE_GETREGS) → reads all registers
  ptrace(PTRACE_SETREGS) → modifies all registers
  Debuggers use this to:
    - Set RIP to call a function in the debugged process
    - Modify arguments before syscall executes
    - Inject code
```

---

## 19. Register-Level Debugging (ptrace)

```
ptrace AND REGISTERS
═══════════════════════════════════════════════════════════════

ptrace() syscall: parent process can observe and control child.
Used by: GDB, strace, valgrind, rr, perf, seccomp.

struct user_regs_struct {     // for PTRACE_GETREGS / PTRACE_SETREGS
    unsigned long r15, r14, r13, r12, rbp, rbx;
    unsigned long r11, r10, r9, r8;
    unsigned long rax, rcx, rdx, rsi, rdi;
    unsigned long orig_rax;
    unsigned long rip, cs, eflags, rsp, ss;
    unsigned long fs_base, gs_base;
    unsigned long ds, es, fs, gs;
};

HOW GDB SETS A BREAKPOINT:
  1. ptrace(PTRACE_PEEKTEXT, pid, addr, ...) → read instruction byte
  2. ptrace(PTRACE_POKETEXT, pid, addr, (orig & ~0xFF) | 0xCC)
                                → write INT3 (0xCC) at address
  3. When breakpoint hits: SIGTRAP delivered to debugger (parent)
  4. ptrace(PTRACE_GETREGS, ...) → get current RIP, RSP, etc.
  5. Debugger shows current state
  6. ptrace(PTRACE_POKETEXT, pid, addr, orig) → restore original byte
  7. ptrace(PTRACE_SINGLESTEP) → set TF in RFLAGS → execute one instr
  8. ptrace(PTRACE_POKETEXT, ...) → put INT3 back

HARDWARE WATCHPOINT (uses debug registers):
  ptrace(PTRACE_POKEUSER, pid,
         offsetof(struct user, u_debugreg[0]), watch_address)
  → Sets DR0 to watch_address
  ptrace(PTRACE_POKEUSER, pid,
         offsetof(struct user, u_debugreg[7]), dr7_value)
  → Configures DR7 to enable breakpoint with read/write condition

SYSCALL TRACING (strace):
  ptrace(PTRACE_SYSCALL) → stop at each syscall entry AND exit
  On stop: read pt_regs to see syscall # and arguments
    regs.orig_rax = syscall number
    regs.rdi      = first argument
    ... etc
```

---

## 20. Inline Assembly in C and Rust

### Why Inline Assembly?

Inline assembly is needed when:
1. Accessing registers not exposed by any C/Rust abstraction
2. Using CPU instructions with no intrinsic (CPUID, RDTSC, RDMSR, etc.)
3. Implementing extremely performance-critical code
4. Writing OS/kernel code that must manipulate privileged registers

### C Inline Assembly (GCC AT&T Syntax)

```c
/*
 * AT&T Syntax: operation src, dst  (reversed from Intel!)
 * Intel Syntax: operation dst, src
 *
 * Register names prefixed with %: %rax, %rbx, %rcx
 * Immediate values prefixed with $: $42, $0xFF
 * Memory: parentheses: (%rax) = [rax], 8(%rax) = [rax+8]
 */

// Basic template:
asm volatile (
    "assembly instructions"
    : output operands       // what registers/memory the asm writes
    : input operands        // what registers/memory the asm reads
    : clobbered registers   // what the asm trashes (besides output)
);

// Operand constraints:
// "r" = any general-purpose register
// "m" = memory location
// "i" = immediate (compile-time constant)
// "a" = RAX specifically
// "b" = RBX specifically
// "c" = RCX specifically
// "d" = RDX specifically
// "S" = RSI specifically
// "D" = RDI specifically
// "=" = write-only (output)
// "+" = read-write
// "&" = early-clobber (written before inputs are consumed)

// Example 1: Read RIP (instruction pointer)
static inline unsigned long read_rip(void) {
    unsigned long rip;
    asm volatile (
        "leaq 1f, %0\n"  // load address of label 1: into %0
        "1:"              // label
        : "=r"(rip)       // output: rip = %0 = any register
    );
    return rip;
}

// Example 2: CPUID instruction
static inline void cpuid(unsigned int leaf,
                          unsigned int *eax, unsigned int *ebx,
                          unsigned int *ecx, unsigned int *edx) {
    asm volatile (
        "cpuid"
        : "=a"(*eax), "=b"(*ebx), "=c"(*ecx), "=d"(*edx)
        : "a"(leaf)
        // no clobber needed: all outputs declared
    );
}

// Example 3: RDTSC (Read Time Stamp Counter)
static inline unsigned long long rdtsc(void) {
    unsigned int lo, hi;
    asm volatile (
        "rdtsc"
        : "=a"(lo), "=d"(hi)
        :
        : // RDTSC also modifies ECX on some CPUs with RDTSCP variant
    );
    return ((unsigned long long)hi << 32) | lo;
}

// Example 4: Atomic compare-and-swap (CMPXCHG)
static inline int atomic_cas(volatile int *ptr, int expected, int newval) {
    int result;
    asm volatile (
        "lock cmpxchgl %2, %1"
        : "=a"(result), "+m"(*ptr)  // result in EAX, ptr is read-write memory
        : "r"(newval), "0"(expected) // newval in any reg, EAX=expected (operand 0)
        : "memory"                   // memory barrier
    );
    return result == expected;
}

// Example 5: Read/Write MSR (kernel only, ring 0)
static inline void wrmsr(unsigned int msr, unsigned long long value) {
    unsigned int lo = (unsigned int)value;
    unsigned int hi = (unsigned int)(value >> 32);
    asm volatile (
        "wrmsr"
        :
        : "c"(msr), "a"(lo), "d"(hi)
        : // WRMSR modifies no outputs
    );
}

static inline unsigned long long rdmsr(unsigned int msr) {
    unsigned int lo, hi;
    asm volatile (
        "rdmsr"
        : "=a"(lo), "=d"(hi)
        : "c"(msr)
    );
    return ((unsigned long long)hi << 32) | lo;
}

// Example 6: Memory barrier (serializing instruction)
static inline void mb(void) {
    asm volatile ("mfence" ::: "memory");
    // "memory" clobber tells GCC: don't reorder memory accesses around this
}

static inline void rmb(void) {
    asm volatile ("lfence" ::: "memory");  // load fence
}

static inline void wmb(void) {
    asm volatile ("sfence" ::: "memory");  // store fence
}

// Example 7: Get current stack pointer
static inline unsigned long get_rsp(void) {
    unsigned long sp;
    asm volatile ("movq %%rsp, %0" : "=r"(sp));
    return sp;
    // Note: %% is an escaped % — needed before register names in
    // constraints-style operands in the template string
}

// Example 8: CLI / STI (Disable/Enable Interrupts — kernel only!)
static inline void local_irq_disable(void) {
    asm volatile ("cli" ::: "memory");
}

static inline void local_irq_enable(void) {
    asm volatile ("sti" ::: "memory");
}

// Example 9: SWAPGS (kernel entry/exit)
static inline void swapgs(void) {
    asm volatile ("swapgs" ::: "memory");
}

// Example 10: Read CR3 (page table base — kernel only)
static inline unsigned long read_cr3(void) {
    unsigned long cr3;
    asm volatile ("movq %%cr3, %0" : "=r"(cr3));
    return cr3;
}

static inline void write_cr3(unsigned long cr3) {
    asm volatile ("movq %0, %%cr3" :: "r"(cr3) : "memory");
}
```

### C: Reading pt_regs in a Kernel Module

```c
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/ptrace.h>
#include <linux/sched.h>

/* Dump registers of current task */
void dump_current_regs(void) {
    struct pt_regs *regs = task_pt_regs(current);

    if (!regs) {
        pr_info("No pt_regs (kernel thread?)\n");
        return;
    }

    pr_info("Register dump for task: %s (pid %d)\n",
            current->comm, current->pid);
    pr_info("  RIP: 0x%016lx\n", regs->ip);
    pr_info("  RSP: 0x%016lx\n", regs->sp);
    pr_info("  RAX: 0x%016lx\n", regs->ax);
    pr_info("  RBX: 0x%016lx\n", regs->bx);
    pr_info("  RCX: 0x%016lx\n", regs->cx);
    pr_info("  RDX: 0x%016lx\n", regs->dx);
    pr_info("  RSI: 0x%016lx\n", regs->si);
    pr_info("  RDI: 0x%016lx\n", regs->di);
    pr_info("  RBP: 0x%016lx\n", regs->bp);
    pr_info("  R8:  0x%016lx\n", regs->r8);
    pr_info("  R9:  0x%016lx\n", regs->r9);
    pr_info("  R10: 0x%016lx\n", regs->r10);
    pr_info("  R11: 0x%016lx\n", regs->r11);
    pr_info("  R12: 0x%016lx\n", regs->r12);
    pr_info("  R13: 0x%016lx\n", regs->r13);
    pr_info("  R14: 0x%016lx\n", regs->r14);
    pr_info("  R15: 0x%016lx\n", regs->r15);
    pr_info("  CS:  0x%04lx  SS: 0x%04lx\n", regs->cs, regs->ss);
    pr_info("  RFLAGS: 0x%016lx  [%s%s%s%s%s]\n",
            regs->flags,
            (regs->flags & X86_EFLAGS_CF) ? "CF " : "",
            (regs->flags & X86_EFLAGS_ZF) ? "ZF " : "",
            (regs->flags & X86_EFLAGS_SF) ? "SF " : "",
            (regs->flags & X86_EFLAGS_OF) ? "OF " : "",
            (regs->flags & X86_EFLAGS_IF) ? "IF " : "");
}

/* Custom syscall hook using kprobes (to intercept syscalls and read regs) */
#include <linux/kprobes.h>

static struct kprobe kp = {
    .symbol_name = "__x64_sys_openat",  // hook the openat syscall
};

static int handler_pre(struct kprobe *p, struct pt_regs *regs) {
    /* regs here contains the state at the probe point */
    /* For syscall probes, regs->di = first arg (dfd for openat) */
    pr_info("openat called: dfd=%ld, filename=0x%lx, flags=%ld\n",
            regs->di, regs->si, regs->dx);
    return 0; /* 0 = don't modify execution, continue normally */
}

static int __init register_syscall_hook(void) {
    kp.pre_handler = handler_pre;
    return register_kprobe(&kp);
}

static void __exit unregister_syscall_hook(void) {
    unregister_kprobe(&kp);
}

module_init(register_syscall_hook);
module_exit(unregister_syscall_hook);
MODULE_LICENSE("GPL");
```

---

## 21. Register Allocation in Compilers

### What Is Register Allocation?

Your program has unlimited virtual variables. The CPU has 16 GPRs. The **register allocator** in the compiler assigns variables to registers (or spills them to stack when all registers are used).

```
REGISTER ALLOCATION — MENTAL MODEL
═══════════════════════════════════════════════════════════════

Source code variables: a, b, c, d, e, f, g, h, i, j ... (unlimited)
Available registers:   RAX RBX RCX RDX RSI RDI R8 R9 R10 R11 R12 R13 R14 R15
                       (14 usable, minus RSP/RBP if frame pointer used)

LIVENESS ANALYSIS:
  A variable is "live" from its definition to its last use.
  Two variables with non-overlapping live ranges can share a register.

  int a = 1;          // a is live here: ─────────────────────────────┐
  int b = 2;          // b is live here:     ─────────────────────────┤
  int c = a + b;      // a,b last used; c starts:                     │ c ─┐
  int d = c * 3;      // c last used; d starts:                       │    │ d ─┐
  return d;           // d last used                                  │    │    │
                      //                                              └────┘    │
                      //                                                        └────

  Live ranges:  a = [line 1-3], b = [line 2-3], c = [line 3-4], d = [line 4-5]
  Interference: a and b overlap → need different registers
                a and c overlap (at line 3) → different registers
                BUT: a ends at line 3, d starts at line 4 → CAN share register!

GRAPH COLORING:
  Build "interference graph": node = variable, edge = overlapping live ranges
  "Color" the graph with N colors (= N registers)
  If a node has > N neighbors, it must be "spilled" to stack

  a ─── b       (a and b interfere → different colors)
  a ─── c       (a and c interfere → different colors)
  b ─── c       (b and c interfere)
  c ─── d       (c and d interfere)
                 a and d don't interfere → can get same register!

  Solution: a=RAX, b=RBX, c=RCX, d=RAX (reuse!)

SPILLING:
  When all registers are full and a new variable needs one:
    - Choose a variable to "spill" to stack
    - STORE current register value to stack
    - Use the register for the new variable
    - When original variable is needed again: LOAD from stack
    - This is expensive! Stack access = cache miss potential

COMPILER OPTIMIZATION IMPLICATION FOR DSA:
  - Local variables in tight loops → compiler keeps them in regs
  - Too many loop variables → some spill to stack
  - This is why struct AOS (Array of Structs) vs SOA (Struct of Arrays)
    matters: SOA loops may have fewer live variables at once
  - Understanding this helps write "register-friendly" algorithms
```

---

## 22. Security: Register Leakage and Spectre/Meltdown

```
SECURITY: REGISTERS AND VULNERABILITIES
═══════════════════════════════════════════════════════════════

1. SPECTRE (CVE-2017-5753, CVE-2017-5715)
────────────────────────────────────────────────────────────────────
The CPU speculatively executes instructions beyond a branch before
knowing the branch outcome. This can read KERNEL REGISTER STATE
into microarchitectural state (cache), then leak via timing.

  // Spectre variant 1 (bounds check bypass):
  if (index < array_size) {         // bounds check
      secret = array[index];        // speculative out-of-bounds read
      dummy = array2[secret * 512]; // secret leaks into cache
  }
  // Measure timing of array2 reads → learn 'secret' from cache state

  REGISTER INVOLVEMENT: speculative register state of secret value
  leaks through cache timing, even though the branch was mispredicted
  and the register value was "rolled back."

  LINUX MITIGATIONS:
    - Retpoline (return trampoline): prevents branch target injection
    - IBRS/IBPB: indirect branch restriction speculation MSRs
    - STIBP: Single Thread Indirect Branch Predictors (for hyperthreads)

2. MELTDOWN (CVE-2017-5754)
────────────────────────────────────────────────────────────────────
A CPU bug (Intel pre-2019, some ARM) where speculative execution
allowed USER SPACE to read KERNEL REGISTERS AND MEMORY:

  // Userspace tries to read kernel address:
  MOV RAX, [kernel_address]   // should fault, but speculatively executes!
  MOV RBX, [user_array + RAX*4096]  // kernel byte is in RAX speculatively
  // Page fault fires — RAX "rolled back" — but cache side-channel leaks it!

  LINUX MITIGATION: KPTI (Kernel Page Table Isolation)
    - Separate page tables for user and kernel
    - User page table does NOT map kernel space (except tiny trampoline)
    - CR3 is switched on every kernel/user transition
    → KILLS SPECULATIVE KERNEL MEMORY ACCESS FROM USER SPACE
    → Performance cost: ~5-30% on syscall-heavy workloads

3. REGISTER FILE LEAKAGE
────────────────────────────────────────────────────────────────────
  If the kernel forgets to zero registers before returning to user:
    - User can read stale kernel data in registers
    - Must zero: RAX (partial returns), RBX, RDX, etc.
    - Linux entry/exit code explicitly zeroes registers

4. SMAP/SMEP (Security Features via CR4)
────────────────────────────────────────────────────────────────────
  SMEP (Supervisor Mode Execution Prevention) — CR4.SMEP:
    Prevents kernel from executing pages marked as user-accessible.
    Stops "ret2user" attacks where attacker makes kernel jump to
    shellcode in user space memory.

  SMAP (Supervisor Mode Access Prevention) — CR4.SMAP:
    Prevents kernel from directly reading/writing user space memory.
    Kernel must use copy_from_user()/copy_to_user() which temporarily
    clears AC flag (via STAC/CLAC instructions) around the access.
    Prevents confused deputy attacks via kernel register manipulation.
```

---

## 23. Complete C Implementation Reference

```c
/*
 * registers_demo.c
 * Complete demonstration of register access from C (userspace and kernel)
 *
 * Compile (userspace):
 *   gcc -O2 -march=native -o registers_demo registers_demo.c
 *
 * Features demonstrated:
 *   - CPUID feature detection via registers
 *   - RDTSC high-resolution timing
 *   - Atomic CAS via CMPXCHG
 *   - Memory barriers
 *   - Stack pointer inspection
 *   - RFLAGS reading
 *   - Register-based context (setjmp/longjmp internals exposed)
 *   - Syscall via inline asm
 */

#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdbool.h>
#include <unistd.h>
#include <sys/syscall.h>

/* ═══════════════════════════════════════════════════════════════
 * SECTION 1: CPU IDENTIFICATION VIA CPUID
 * ═══════════════════════════════════════════════════════════════ */

typedef struct {
    uint32_t eax, ebx, ecx, edx;
} cpuid_result_t;

static inline cpuid_result_t cpuid(uint32_t leaf, uint32_t subleaf) {
    cpuid_result_t r;
    asm volatile (
        "cpuid"
        : "=a"(r.eax), "=b"(r.ebx), "=c"(r.ecx), "=d"(r.edx)
        : "a"(leaf), "c"(subleaf)
    );
    return r;
}

static void print_cpu_vendor(void) {
    cpuid_result_t r = cpuid(0, 0);
    char vendor[13];
    /* EBX, EDX, ECX hold vendor string in that order */
    memcpy(vendor + 0, &r.ebx, 4);
    memcpy(vendor + 4, &r.edx, 4);
    memcpy(vendor + 8, &r.ecx, 4);
    vendor[12] = '\0';
    printf("CPU Vendor: %s\n", vendor);
    printf("Max CPUID leaf: %u\n", r.eax);
}

static void print_cpu_features(void) {
    cpuid_result_t r = cpuid(1, 0);
    printf("\nCPU Features (CPUID leaf 1):\n");
    printf("  Stepping: %u  Model: %u  Family: %u\n",
           r.eax & 0xF,
           (r.eax >> 4) & 0xF,
           (r.eax >> 8) & 0xF);

    /* ECX features */
    printf("  ECX features: %08X\n", r.ecx);
    printf("    SSE4.2:  %s\n", (r.ecx >> 20) & 1 ? "YES" : "NO");
    printf("    AVX:     %s\n", (r.ecx >> 28) & 1 ? "YES" : "NO");
    printf("    AES-NI:  %s\n", (r.ecx >> 25) & 1 ? "YES" : "NO");
    printf("    RDRAND:  %s\n", (r.ecx >> 30) & 1 ? "YES" : "NO");

    /* EDX features */
    printf("  EDX features: %08X\n", r.edx);
    printf("    FPU:     %s\n", (r.edx >> 0)  & 1 ? "YES" : "NO");
    printf("    SSE:     %s\n", (r.edx >> 25) & 1 ? "YES" : "NO");
    printf("    SSE2:    %s\n", (r.edx >> 26) & 1 ? "YES" : "NO");
    printf("    HTT:     %s\n", (r.edx >> 28) & 1 ? "YES" : "NO");
}

/* ═══════════════════════════════════════════════════════════════
 * SECTION 2: HIGH-RESOLUTION TIMING WITH RDTSC
 * ═══════════════════════════════════════════════════════════════ */

static inline uint64_t rdtsc(void) {
    uint32_t lo, hi;
    /*
     * RDTSC reads the Time Stamp Counter — a 64-bit counter
     * that increments every CPU clock cycle.
     * Result: EDX:EAX (EDX = high 32 bits, EAX = low 32 bits)
     */
    asm volatile (
        "rdtsc"
        : "=a"(lo), "=d"(hi)
    );
    return ((uint64_t)hi << 32) | lo;
}

static inline uint64_t rdtscp(uint32_t *cpu_id) {
    uint32_t lo, hi, aux;
    /*
     * RDTSCP is like RDTSC but also returns the CPU ID in ECX (via aux).
     * It also serializes (waits for prior loads to complete).
     * Useful for accurate benchmarking across CPUs.
     */
    asm volatile (
        "rdtscp"
        : "=a"(lo), "=d"(hi), "=c"(aux)
    );
    if (cpu_id) *cpu_id = aux;
    return ((uint64_t)hi << 32) | lo;
}

static void demonstrate_timing(void) {
    printf("\nTiming demonstration (RDTSC):\n");
    uint64_t start = rdtsc();
    /* Serialize to prevent reordering */
    asm volatile ("mfence" ::: "memory");

    volatile uint64_t sum = 0;
    for (int i = 0; i < 1000000; i++) sum += i;

    asm volatile ("mfence" ::: "memory");
    uint64_t end = rdtsc();

    printf("  Sum loop (1M iter): %lu cycles\n", end - start);
    printf("  Sum result: %lu\n", sum);
}

/* ═══════════════════════════════════════════════════════════════
 * SECTION 3: ATOMIC OPERATIONS VIA LOCK PREFIX + CMPXCHG
 * ═══════════════════════════════════════════════════════════════ */

/*
 * LOCK prefix: turns a read-modify-write instruction into an
 * ATOMIC operation on the memory bus.
 * The CPU asserts its bus lock signal, preventing other CPUs from
 * accessing the same memory location during the operation.
 * On modern CPUs with cache coherency: uses MESIF/MOESI protocol
 * to get exclusive ownership of the cache line.
 */

static inline bool atomic_compare_exchange(volatile int *ptr,
                                            int *expected,
                                            int desired) {
    /*
     * CMPXCHG dest, src:
     *   if (EAX == *dest) { ZF=1; *dest = src; }
     *   else { ZF=0; EAX = *dest; }
     *
     * "lock" prefix makes this atomic across CPUs.
     *
     * Constraints:
     *   "=a"(*expected) : output — EAX holds old value if CAS failed
     *   "+m"(*ptr)      : read-write memory operand
     *   "r"(desired)    : desired new value, any register
     *   "0"(*expected)  : input for EAX (constraint "0" = same as output 0)
     */
    bool success;
    asm volatile (
        "lock cmpxchgl %[desired], %[ptr]"
        : "=a"(*expected), [ptr] "+m"(*ptr), "=@ccz"(success)
        : [desired] "r"(desired), "a"(*expected)
        : "memory"
    );
    return success;
}

static inline int atomic_fetch_add(volatile int *ptr, int val) {
    /*
     * XADD: exchange and add
     *   temp = *ptr
     *   *ptr = *ptr + val
     *   val  = temp  (original value returned in val register)
     */
    asm volatile (
        "lock xaddl %0, %1"
        : "+r"(val), "+m"(*ptr)
        :
        : "memory"
    );
    return val; /* original value before add */
}

static inline void atomic_store(volatile int *ptr, int val) {
    /*
     * XCHG always has implicit LOCK prefix (bus lock)
     * Simple store with full memory barrier semantics.
     */
    asm volatile (
        "xchgl %0, %1"
        : "+r"(val), "+m"(*ptr)
        :
        : "memory"
    );
}

static void demonstrate_atomics(void) {
    printf("\nAtomic operations demonstration:\n");

    volatile int counter = 0;

    /* fetch_add */
    int old = atomic_fetch_add(&counter, 5);
    printf("  fetch_add(0, 5): old=%d, new=%d\n", old, counter);

    /* CAS success */
    int expected = 5;
    bool ok = atomic_compare_exchange(&counter, &expected, 10);
    printf("  CAS(5→10): success=%d, counter=%d\n", ok, counter);

    /* CAS failure */
    expected = 5; /* wrong expected value */
    ok = atomic_compare_exchange(&counter, &expected, 20);
    printf("  CAS(5→20, should fail): success=%d, expected now=%d, counter=%d\n",
           ok, expected, counter);
}

/* ═══════════════════════════════════════════════════════════════
 * SECTION 4: READING CPU FLAGS AND STACK POINTER
 * ═══════════════════════════════════════════════════════════════ */

static inline uint64_t read_rflags(void) {
    uint64_t flags;
    asm volatile (
        "pushfq\n"   /* push RFLAGS to stack */
        "popq %0\n"  /* pop into variable */
        : "=r"(flags)
        :
        : "memory"
    );
    return flags;
}

static inline uint64_t read_rsp(void) {
    uint64_t sp;
    asm volatile ("movq %%rsp, %0" : "=r"(sp));
    return sp;
}

static inline uint64_t read_rbp(void) {
    uint64_t bp;
    asm volatile ("movq %%rbp, %0" : "=r"(bp));
    return bp;
}

static void demonstrate_flags(void) {
    printf("\nCPU Flags demonstration:\n");

    uint64_t flags = read_rflags();
    printf("  RFLAGS: 0x%016lx\n", flags);
    printf("    CF (Carry):     %lu\n", (flags >> 0)  & 1);
    printf("    PF (Parity):    %lu\n", (flags >> 2)  & 1);
    printf("    AF (Aux Carry): %lu\n", (flags >> 4)  & 1);
    printf("    ZF (Zero):      %lu\n", (flags >> 6)  & 1);
    printf("    SF (Sign):      %lu\n", (flags >> 7)  & 1);
    printf("    IF (Interrupts):%lu\n", (flags >> 9)  & 1);
    printf("    DF (Direction): %lu\n", (flags >> 10) & 1);
    printf("    OF (Overflow):  %lu\n", (flags >> 11) & 1);
    printf("    IOPL:           %lu\n", (flags >> 12) & 3);
    printf("    ID (CPUID ok):  %lu\n", (flags >> 21) & 1);

    printf("\nStack pointers:\n");
    printf("  RSP (stack pointer): 0x%016lx\n", read_rsp());
    printf("  RBP (frame pointer): 0x%016lx\n", read_rbp());
}

/* ═══════════════════════════════════════════════════════════════
 * SECTION 5: DIRECT SYSCALL VIA INLINE ASM
 * ═══════════════════════════════════════════════════════════════ */

/*
 * Make a raw syscall, bypassing libc.
 * This shows exactly how registers are used for syscalls.
 */
static inline long raw_syscall3(long number, long arg1, long arg2, long arg3) {
    long ret;
    asm volatile (
        "syscall"
        : "=a"(ret)                            /* output: RAX = return value */
        : "0"(number),                         /* RAX = syscall number */
          "D"(arg1),                           /* RDI = arg1 */
          "S"(arg2),                           /* RSI = arg2 */
          "d"(arg3)                            /* RDX = arg3 */
        : "rcx", "r11", "memory"               /* syscall trashes RCX and R11 */
    );
    return ret;
}

static void demonstrate_raw_syscall(void) {
    printf("\nRaw syscall demonstration:\n");
    const char msg[] = "  [raw write syscall output]\n";
    /* syscall write(1, msg, len) */
    long ret = raw_syscall3(SYS_write, 1, (long)msg, sizeof(msg) - 1);
    printf("  write() returned: %ld\n", ret);
}

/* ═══════════════════════════════════════════════════════════════
 * SECTION 6: STACK FRAME WALKING
 * ═══════════════════════════════════════════════════════════════ */

typedef struct frame {
    struct frame *prev;   /* saved RBP = pointer to previous frame */
    void         *ret;    /* return address = saved RIP */
} frame_t;

static void walk_stack_frames(int max_frames) {
    printf("\nStack frame walk (using RBP chain):\n");
    printf("  (Requires -fno-omit-frame-pointer to work reliably)\n");

    frame_t *frame;
    asm volatile ("movq %%rbp, %0" : "=r"(frame));

    for (int i = 0; i < max_frames && frame != NULL; i++) {
        printf("  Frame %d: RBP=0x%016lx  RIP=0x%016lx\n",
               i, (unsigned long)frame, (unsigned long)frame->ret);
        /* Sanity check: stack grows down, prev frame is at higher address */
        if ((unsigned long)frame->prev <= (unsigned long)frame) break;
        frame = frame->prev;
    }
}

/* ═══════════════════════════════════════════════════════════════
 * SECTION 7: MEMORY BARRIERS AND ORDERING
 * ═══════════════════════════════════════════════════════════════ */

/*
 * x86-64 memory model: TSO (Total Store Order)
 *   - Stores are NOT reordered with other stores
 *   - Loads are NOT reordered with other loads
 *   - BUT: stores CAN be reordered with SUBSEQUENT loads
 *     (due to store buffer)
 *
 * This is STRONGER than ARM/POWER (weaker memory models)
 * but WEAKER than sequential consistency.
 *
 * When you need full ordering: MFENCE
 * When you need load serialization: LFENCE
 * When you need store serialization: SFENCE (mostly for WC memory)
 *
 * "memory" clobber in asm: prevents COMPILER reordering
 * MFENCE/LFENCE/SFENCE: prevents CPU reordering
 * Both needed for true synchronization!
 */

static inline void full_memory_barrier(void) {
    asm volatile ("mfence" ::: "memory");
}

static inline void load_fence(void) {
    asm volatile ("lfence" ::: "memory");
}

static inline void store_fence(void) {
    asm volatile ("sfence" ::: "memory");
}

/* Compiler-only barrier (no CPU instruction) */
static inline void compiler_barrier(void) {
    asm volatile ("" ::: "memory");
}

/* ═══════════════════════════════════════════════════════════════
 * SECTION 8: HARDWARE PREFETCH HINT
 * ═══════════════════════════════════════════════════════════════ */

static inline void prefetch_read(const void *addr) {
    asm volatile ("prefetcht0 %0" :: "m"(*(const char *)addr));
}

static inline void prefetch_write(const void *addr) {
    asm volatile ("prefetchw %0" :: "m"(*(const char *)addr));
}

/* ═══════════════════════════════════════════════════════════════
 * MAIN
 * ═══════════════════════════════════════════════════════════════ */

int main(void) {
    printf("╔══════════════════════════════════════════════╗\n");
    printf("║   Register Architecture Demonstration (C)    ║\n");
    printf("╚══════════════════════════════════════════════╝\n\n");

    print_cpu_vendor();
    print_cpu_features();
    demonstrate_timing();
    demonstrate_atomics();
    demonstrate_flags();
    demonstrate_raw_syscall();
    walk_stack_frames(8);

    return 0;
}
```

---

## 24. Complete Rust Implementation Reference

```rust
//! registers_demo.rs
//!
//! Comprehensive register access demonstration in Rust.
//!
//! Compile:
//!   rustc -O -C target-cpu=native -o registers_demo registers_demo.rs
//!   or: cargo build --release (with nightly for core::arch::asm!)
//!
//! Features:
//!   - Inline assembly with Rust's `asm!` macro (stable in Rust 1.59+)
//!   - CPUID, RDTSC, atomic operations, memory barriers
//!   - pt_regs structure definition (kernel-compatible)
//!   - Safe wrapper types around raw register access

#![allow(unused_unsafe, dead_code)]
// For kernel/bare-metal: use #![no_std]

use std::sync::atomic::{AtomicI32, Ordering};

// ═══════════════════════════════════════════════════════════════
// SECTION 1: pt_regs — The Kernel Register Save Area
// ═══════════════════════════════════════════════════════════════

/// Mirror of Linux kernel's `pt_regs` structure (arch/x86/include/asm/ptrace.h)
/// This is the layout of registers on the kernel stack during syscall/interrupt.
///
/// `#[repr(C)]` ensures same memory layout as C struct.
/// Fields must be in EXACTLY this order.
#[repr(C)]
#[derive(Debug, Clone, Copy)]
pub struct PtRegs {
    pub r15:      u64,
    pub r14:      u64,
    pub r13:      u64,
    pub r12:      u64,
    pub rbp:      u64,
    pub rbx:      u64,
    // Arguments / scratch registers
    pub r11:      u64,
    pub r10:      u64,
    pub r9:       u64,
    pub r8:       u64,
    pub rax:      u64,
    pub rcx:      u64,
    pub rdx:      u64,
    pub rsi:      u64,
    pub rdi:      u64,
    // Pushed by kernel entry asm:
    pub orig_rax: u64,  // original syscall number
    // Pushed by hardware on ring transition:
    pub rip:      u64,
    pub cs:       u64,
    pub eflags:   u64,
    pub rsp:      u64,
    pub ss:       u64,
}

impl PtRegs {
    /// Syscall number (from orig_rax)
    pub fn syscall_nr(&self) -> u64 { self.orig_rax }
    /// First syscall argument
    pub fn arg1(&self) -> u64 { self.rdi }
    /// Second syscall argument
    pub fn arg2(&self) -> u64 { self.rsi }
    /// Third syscall argument
    pub fn arg3(&self) -> u64 { self.rdx }
    /// Fourth syscall argument (R10, NOT RCX — RCX is trashed by SYSCALL)
    pub fn arg4(&self) -> u64 { self.r10 }
    /// Fifth syscall argument
    pub fn arg5(&self) -> u64 { self.r8 }
    /// Sixth syscall argument
    pub fn arg6(&self) -> u64 { self.r9 }

    /// Return value (written to rax before returning to user)
    pub fn return_value(&self) -> i64 { self.rax as i64 }

    /// Check if interrupted from user space (CPL=3 via CS bits)
    pub fn from_user_space(&self) -> bool { self.cs & 3 == 3 }

    /// Check carry flag
    pub fn carry_flag(&self) -> bool { self.eflags & (1 << 0) != 0 }
    /// Check zero flag
    pub fn zero_flag(&self) -> bool { self.eflags & (1 << 6) != 0 }
    /// Check sign flag
    pub fn sign_flag(&self) -> bool { self.eflags & (1 << 7) != 0 }
    /// Check interrupt enable flag
    pub fn interrupt_flag(&self) -> bool { self.eflags & (1 << 9) != 0 }
    /// Check overflow flag
    pub fn overflow_flag(&self) -> bool { self.eflags & (1 << 11) != 0 }
}

// ═══════════════════════════════════════════════════════════════
// SECTION 2: CPUID — CPU Feature Detection
// ═══════════════════════════════════════════════════════════════

#[derive(Debug)]
pub struct CpuidResult {
    pub eax: u32,
    pub ebx: u32,
    pub ecx: u32,
    pub edx: u32,
}

/// Execute CPUID instruction.
///
/// # Safety
/// Safe on all x86-64 CPUs. The CPUID instruction is always available
/// in protected/long mode. Does not write to memory.
pub fn cpuid(leaf: u32, subleaf: u32) -> CpuidResult {
    let (eax, ebx, ecx, edx): (u32, u32, u32, u32);
    unsafe {
        std::arch::asm!(
            "cpuid",
            // Outputs: named registers via operand constraints
            inout("eax") leaf  => eax,
            inout("ecx") subleaf => ecx,
            out("ebx") ebx,
            out("edx") edx,
        );
    }
    CpuidResult { eax, ebx, ecx, edx }
}

pub fn cpu_vendor() -> String {
    let r = cpuid(0, 0);
    // EBX, EDX, ECX hold 4-byte chunks of vendor string (note order!)
    let mut bytes = [0u8; 12];
    bytes[0..4].copy_from_slice(&r.ebx.to_le_bytes());
    bytes[4..8].copy_from_slice(&r.edx.to_le_bytes());
    bytes[8..12].copy_from_slice(&r.ecx.to_le_bytes());
    String::from_utf8_lossy(&bytes).into_owned()
}

/// CPU features from CPUID leaf 1
#[derive(Debug)]
pub struct CpuFeatures {
    pub sse4_2:  bool,
    pub avx:     bool,
    pub aes_ni:  bool,
    pub rdrand:  bool,
    pub popcnt:  bool,
    pub sse:     bool,
    pub sse2:    bool,
    pub htt:     bool,
    pub stepping: u32,
    pub model:    u32,
    pub family:   u32,
}

pub fn cpu_features() -> CpuFeatures {
    let r = cpuid(1, 0);
    CpuFeatures {
        sse4_2:   (r.ecx >> 20) & 1 == 1,
        avx:      (r.ecx >> 28) & 1 == 1,
        aes_ni:   (r.ecx >> 25) & 1 == 1,
        rdrand:   (r.ecx >> 30) & 1 == 1,
        popcnt:   (r.ecx >> 23) & 1 == 1,
        sse:      (r.edx >> 25) & 1 == 1,
        sse2:     (r.edx >> 26) & 1 == 1,
        htt:      (r.edx >> 28) & 1 == 1,
        stepping:  r.eax & 0xF,
        model:    (r.eax >> 4) & 0xF,
        family:   (r.eax >> 8) & 0xF,
    }
}

// ═══════════════════════════════════════════════════════════════
// SECTION 3: RDTSC — Cycle-accurate Timing
// ═══════════════════════════════════════════════════════════════

/// Read Time Stamp Counter.
/// Returns the number of CPU clock cycles since reset.
///
/// WARNING: May not be monotonic across CPU cores on older systems.
/// Use `rdtscp` or pin thread to a CPU for accurate measurements.
pub fn rdtsc() -> u64 {
    let lo: u32;
    let hi: u32;
    unsafe {
        std::arch::asm!(
            "rdtsc",
            out("eax") lo,
            out("edx") hi,
            // rdtsc doesn't need options - it's a read
        );
    }
    ((hi as u64) << 32) | (lo as u64)
}

/// Read Time Stamp Counter + CPU ID (serializing variant).
///
/// `rdtscp` waits for all previous instructions to complete (load-fence
/// semantics) and also returns the CPU ID in `ecx`. This makes it
/// suitable for accurate benchmarking.
///
/// Returns (tsc_value, cpu_id)
pub fn rdtscp() -> (u64, u32) {
    let lo: u32;
    let hi: u32;
    let cpu: u32;
    unsafe {
        std::arch::asm!(
            "rdtscp",
            out("eax") lo,
            out("edx") hi,
            out("ecx") cpu,
        );
    }
    (((hi as u64) << 32) | (lo as u64), cpu)
}

/// High-precision timer using RDTSC with serializing fences.
///
/// # Usage
/// ```rust
/// let start = precise_time_start();
/// // ... code to measure ...
/// let cycles = precise_time_end(start);
/// ```
pub fn precise_time_start() -> u64 {
    unsafe { std::arch::asm!("mfence", "lfence", options(nostack)); }
    rdtsc()
}

pub fn precise_time_end(start: u64) -> u64 {
    let (end, _) = rdtscp();
    unsafe { std::arch::asm!("lfence", options(nostack)); }
    end.wrapping_sub(start)
}

// ═══════════════════════════════════════════════════════════════
// SECTION 4: HARDWARE RANDOM NUMBER GENERATION (RDRAND)
// ═══════════════════════════════════════════════════════════════

/// Read a hardware random number using RDRAND.
/// Returns None if RDRAND is not available or failed (CF=0 after RDRAND).
pub fn rdrand() -> Option<u64> {
    if !cpu_features().rdrand {
        return None;
    }
    let value: u64;
    let ok: u8;
    unsafe {
        std::arch::asm!(
            "rdrand {val}",
            "setc {ok}",     // set ok=1 if CF=1 (success)
            val = out(reg) value,
            ok  = out(reg_byte) ok,
        );
    }
    if ok != 0 { Some(value) } else { None }
}

// ═══════════════════════════════════════════════════════════════
// SECTION 5: REGISTER ACCESSORS
// ═══════════════════════════════════════════════════════════════

/// Get the current stack pointer value.
pub fn read_rsp() -> u64 {
    let sp: u64;
    unsafe { std::arch::asm!("mov {}, rsp", out(reg) sp); }
    sp
}

/// Get the current frame (base) pointer.
pub fn read_rbp() -> u64 {
    let bp: u64;
    unsafe { std::arch::asm!("mov {}, rbp", out(reg) bp); }
    bp
}

/// Read RFLAGS register.
pub fn read_rflags() -> u64 {
    let flags: u64;
    unsafe {
        std::arch::asm!(
            "pushfq",       // push RFLAGS to stack
            "pop {flags}",  // pop into variable
            flags = out(reg) flags,
        );
    }
    flags
}

#[derive(Debug)]
pub struct Rflags {
    pub raw: u64,
}

impl Rflags {
    pub fn read() -> Self { Self { raw: read_rflags() } }
    pub fn carry(&self)     -> bool { self.raw & (1 << 0)  != 0 }
    pub fn parity(&self)    -> bool { self.raw & (1 << 2)  != 0 }
    pub fn zero(&self)      -> bool { self.raw & (1 << 6)  != 0 }
    pub fn sign(&self)      -> bool { self.raw & (1 << 7)  != 0 }
    pub fn trap(&self)      -> bool { self.raw & (1 << 8)  != 0 }
    pub fn interrupt(&self) -> bool { self.raw & (1 << 9)  != 0 }
    pub fn direction(&self) -> bool { self.raw & (1 << 10) != 0 }
    pub fn overflow(&self)  -> bool { self.raw & (1 << 11) != 0 }
    pub fn iopl(&self)      -> u8   { ((self.raw >> 12) & 3) as u8 }
    pub fn cpuid_ok(&self)  -> bool { self.raw & (1 << 21) != 0 }
}

impl std::fmt::Display for Rflags {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "RFLAGS=0x{:016X} [", self.raw)?;
        if self.carry()     { write!(f, "CF ")?; }
        if self.zero()      { write!(f, "ZF ")?; }
        if self.sign()      { write!(f, "SF ")?; }
        if self.overflow()  { write!(f, "OF ")?; }
        if self.interrupt() { write!(f, "IF ")?; }
        if self.direction() { write!(f, "DF ")?; }
        write!(f, "IOPL={}]", self.iopl())
    }
}

// ═══════════════════════════════════════════════════════════════
// SECTION 6: MEMORY BARRIERS
// ═══════════════════════════════════════════════════════════════

/// Full memory fence (MFENCE).
/// Ensures all loads and stores before this point complete before
/// any loads/stores after this point begin.
/// Also includes compiler barrier.
#[inline(always)]
pub fn memory_fence() {
    unsafe { std::arch::asm!("mfence", options(nostack, preserves_flags)); }
    std::sync::atomic::fence(Ordering::SeqCst);
}

/// Load fence (LFENCE).
/// Ensures all loads before this complete before any loads after.
#[inline(always)]
pub fn load_fence() {
    unsafe { std::arch::asm!("lfence", options(nostack, preserves_flags)); }
}

/// Store fence (SFENCE).
/// Ensures all stores before this complete before any stores after.
/// Mainly needed for weakly-ordered write-combining memory (WC).
#[inline(always)]
pub fn store_fence() {
    unsafe { std::arch::asm!("sfence", options(nostack, preserves_flags)); }
}

/// Compiler-only barrier (no CPU instruction).
/// Prevents the Rust/LLVM compiler from reordering operations,
/// but has no effect on CPU out-of-order execution.
#[inline(always)]
pub fn compiler_barrier() {
    unsafe { std::arch::asm!("", options(nostack, preserves_flags)); }
    std::sync::atomic::compiler_fence(Ordering::SeqCst);
}

// ═══════════════════════════════════════════════════════════════
// SECTION 7: CACHE OPERATIONS
// ═══════════════════════════════════════════════════════════════

/// Prefetch cache line for reading (T0 = all cache levels).
#[inline(always)]
pub fn prefetch_t0(addr: *const u8) {
    unsafe {
        std::arch::asm!(
            "prefetcht0 [{addr}]",
            addr = in(reg) addr,
            options(nostack, preserves_flags, readonly),
        );
    }
}

/// Prefetch cache line for writing.
#[inline(always)]
pub fn prefetch_write(addr: *mut u8) {
    unsafe {
        std::arch::asm!(
            "prefetchw [{addr}]",
            addr = in(reg) addr,
            options(nostack, preserves_flags),
        );
    }
}

/// Flush a cache line from all CPU caches (CLFLUSH).
/// Used for persistent memory, DMA coherency.
#[inline(always)]
pub unsafe fn cache_flush(addr: *const u8) {
    std::arch::asm!(
        "clflush [{addr}]",
        addr = in(reg) addr,
        options(nostack, preserves_flags),
    );
}

// ═══════════════════════════════════════════════════════════════
// SECTION 8: STACK FRAME WALKER
// ═══════════════════════════════════════════════════════════════

/// Represents one stack frame (RBP-based linked list).
#[repr(C)]
struct StackFrame {
    prev_rbp: *const StackFrame,  // saved RBP at [RBP+0]
    ret_addr: usize,               // return address at [RBP+8]
}

/// Walk the call stack by following the RBP frame pointer chain.
///
/// IMPORTANT: Requires compilation without `-C force-frame-pointers=no`
/// In release mode: use `RUSTFLAGS="-C force-frame-pointers=yes"`
pub fn walk_stack(max_frames: usize) -> Vec<usize> {
    let mut frames = Vec::new();
    let mut rbp = read_rbp() as *const StackFrame;

    for _ in 0..max_frames {
        if rbp.is_null() { break; }
        unsafe {
            let frame = &*rbp;
            frames.push(frame.ret_addr);
            // Sanity check: prev frame must be at higher address (stack grows down)
            if (frame.prev_rbp as usize) <= (rbp as usize) { break; }
            rbp = frame.prev_rbp;
        }
    }
    frames
}

// ═══════════════════════════════════════════════════════════════
// SECTION 9: DIRECT SYSCALL (bypassing libc)
// ═══════════════════════════════════════════════════════════════

/// Make a raw syscall with up to 3 arguments.
///
/// # Safety
/// The caller must ensure valid syscall number and correct argument types.
/// The syscall interface is the only stable ABI between Linux kernel and userspace.
pub unsafe fn syscall3(nr: u64, arg1: u64, arg2: u64, arg3: u64) -> i64 {
    let ret: i64;
    std::arch::asm!(
        "syscall",
        inout("rax") nr as i64 => ret,  // RAX: syscall# in, return val out
        in("rdi") arg1,                   // RDI: arg1
        in("rsi") arg2,                   // RSI: arg2
        in("rdx") arg3,                   // RDX: arg3
        // Syscall trashes RCX (saves RIP) and R11 (saves RFLAGS)
        out("rcx") _,
        out("r11") _,
        options(nostack),
    );
    ret
}

// ═══════════════════════════════════════════════════════════════
// SECTION 10: BENCHMARK HARNESS USING REGISTERS
// ═══════════════════════════════════════════════════════════════

/// Measure the cycle cost of a closure using RDTSCP + serialization.
/// Returns (min_cycles, avg_cycles, max_cycles) over `iterations` runs.
pub fn bench_cycles<F: Fn()>(f: F, iterations: usize) -> (u64, u64, u64) {
    let mut min = u64::MAX;
    let mut max = 0u64;
    let mut total = 0u64;

    // Warmup: fill branch predictor and instruction cache
    for _ in 0..10 { f(); }

    for _ in 0..iterations {
        let start = precise_time_start();
        f();
        let cycles = precise_time_end(start);

        total += cycles;
        if cycles < min { min = cycles; }
        if cycles > max { max = cycles; }
    }

    (min, total / iterations as u64, max)
}

// ═══════════════════════════════════════════════════════════════
// MAIN — Integration demonstration
// ═══════════════════════════════════════════════════════════════

fn main() {
    println!("╔══════════════════════════════════════════════╗");
    println!("║  Register Architecture Demonstration (Rust)  ║");
    println!("╚══════════════════════════════════════════════╝\n");

    // ── CPU identification ──────────────────────────────────
    println!("── CPU Identification ──");
    println!("Vendor: {}", cpu_vendor());
    let features = cpu_features();
    println!("Features: {:?}", features);

    // ── Timing ──────────────────────────────────────────────
    println!("\n── RDTSC Timing ──");
    let (tsc, cpu_id) = rdtscp();
    println!("Current TSC: {tsc}  (CPU #{cpu_id})");

    let (min, avg, max) = bench_cycles(
        || {
            // Measure a simple atomic operation
            let x = AtomicI32::new(0);
            x.fetch_add(1, Ordering::SeqCst);
        },
        1000,
    );
    println!("AtomicI32::fetch_add cycles: min={min} avg={avg} max={max}");

    // ── Hardware random ──────────────────────────────────────
    println!("\n── Hardware Random (RDRAND) ──");
    match rdrand() {
        Some(r) => println!("RDRAND: 0x{r:016X}"),
        None    => println!("RDRAND not available"),
    }

    // ── Registers ───────────────────────────────────────────
    println!("\n── Register State ──");
    println!("RSP (stack pointer): 0x{:016X}", read_rsp());
    println!("RBP (frame pointer): 0x{:016X}", read_rbp());
    println!("{}", Rflags::read());

    // ── Stack walk ───────────────────────────────────────────
    println!("\n── Call Stack (RBP chain) ──");
    let stack = walk_stack(8);
    for (i, ret_addr) in stack.iter().enumerate() {
        println!("  Frame {i}: return addr = 0x{ret_addr:016X}");
    }

    // ── pt_regs structure layout ─────────────────────────────
    println!("\n── pt_regs struct layout ──");
    println!("sizeof(PtRegs) = {} bytes", std::mem::size_of::<PtRegs>());
    println!("offsetof rip   = {} (expected 0x80 = 128)",
             std::mem::offset_of!(PtRegs, rip));
    println!("offsetof rsp   = {} (expected 0x98 = 152)",
             std::mem::offset_of!(PtRegs, rsp));

    // ── Raw syscall ──────────────────────────────────────────
    println!("\n── Raw Syscall (write) ──");
    let msg = b"  [via raw SYSCALL instruction]\n";
    let ret = unsafe {
        syscall3(1, 1, msg.as_ptr() as u64, msg.len() as u64) // sys_write
    };
    println!("  sys_write returned: {ret}");
}
```

---

## 25. Mental Models and Summary

### The Register Mental Model Hierarchy

```
REGISTER MENTAL MODELS — STACK OF ABSTRACTIONS
═══════════════════════════════════════════════════════════════

Level 5: ALGORITHM THINKING
  "This loop has 4 active variables — they should all fit in registers."
  "I'm processing 8 int32s — use AVX2 to do them in parallel in YMM."
  "This atomic CAS needs LOCK CMPXCHG — cache line becomes exclusive."

Level 4: KERNEL THINKING
  "When a syscall fires, RDI/RSI/RDX/R10/R8/R9 hold arguments in pt_regs."
  "Context switch: save callee-saved regs to kernel stack, swap RSP."
  "GS segment → per-CPU area → current task_struct → register state."

Level 3: ABI THINKING
  "First 6 integer args: RDI RSI RDX RCX R8 R9."
  "Caller must save RAX RCX RDX RSI RDI R8 R9 R10 R11 before a call."
  "Float return in XMM0. Struct > 16 bytes → hidden pointer in RDI."

Level 2: INSTRUCTION THINKING
  "PUSH = RSP-=8; [RSP]=val."
  "CALL = push RIP; jmp."
  "Writing EAX zero-extends to RAX (upper 32 bits cleared)."
  "LOCK CMPXCHG: atomic if cache line is MESIF-exclusive."

Level 1: HARDWARE THINKING
  "A register is 64 flip-flops. Read/write in 1 clock cycle."
  "RIP advances automatically after each instruction fetch."
  "RFLAGS bits are set by arithmetic — they're how branches work."
```

### The Complete Data Flow — From Instruction to Result

```
HOW AN ADD INSTRUCTION WORKS AT REGISTER LEVEL:
═══════════════════════════════════════════════════════════════

Source: int c = a + b;
Assembly: ADD EAX, EBX  (where EAX=a, EBX=b, result in EAX)

CPU Pipeline:
  1. FETCH:    RIP → instruction cache → fetch 2-byte ADD opcode
               RIP += 2 (advance to next instruction)

  2. DECODE:   Decode opcode: "ADD r/m32, r32"
               Identify: source=EBX register, dest=EAX register

  3. RENAME:   Map EAX,EBX to physical registers (register renaming)
               Eliminates false data hazards in out-of-order execution

  4. DISPATCH: Issue to Integer ALU execution unit

  5. EXECUTE:  ALU computes: result = EAX + EBX
               Compute flags: ZF=(result==0), SF=(result<0),
                              CF=(unsigned overflow), OF=(signed overflow)

  6. WRITEBACK: Write result to physical register mapped to EAX (RAX)
                Update RFLAGS

  7. RETIRE:   Commit result to architectural register state
               (makes result visible to subsequent instructions)

Total time: ~1 clock cycle for integer ADD
            ~3-5 cycles for integer MUL
            ~20-30 cycles for integer DIV
            ~4-5 cycles for FP ADD (pipelined)
```

### Key Principles to Internalize

```
THE 10 LAWS OF REGISTER MASTERY
═══════════════════════════════════════════════════════════════

  1. REGISTERS ARE SPEED
     Every memory access is potentially 100× slower than a register op.
     The art of performance programming is keeping hot data in registers.

  2. THE ABI IS THE CONTRACT
     Functions communicate through registers. Violate the ABI → chaos.
     Caller/callee split: know which registers you can clobber freely.

  3. pt_regs IS THE KERNEL'S WINDOW INTO USER SPACE
     Every syscall, interrupt, signal uses pt_regs.
     To understand Linux internals: understand pt_regs.

  4. THE STACK IS REGISTERS IN DISGUISE
     RSP + push/pop = register extension for function calls.
     Frame pointer (RBP) creates navigable stack frames.

  5. FLAGS DRIVE CONTROL FLOW
     Every comparison sets flags. Every branch reads flags.
     ZF,SF,CF,OF are the four primitive decision bits of the CPU.

  6. CONTEXT SWITCH = REGISTER SWAP
     Process scheduling reduces to: save one set of registers,
     load another set. That's it. Everything else is policy.

  7. PRIVILEGE COMES FROM REGISTER STATE
     CS bits determine ring level. GS_BASE determines kernel identity.
     SWAPGS bridges the user↔kernel register worlds.

  8. ATOMICITY REQUIRES CACHE LINE OWNERSHIP
     LOCK prefix → CPU gets exclusive ownership of cache line.
     This is how all mutexes, semaphores, spinlocks ultimately work.

  9. SIMD = MULTIPLE REGISTERS IN ONE
     YMM register = 8 floats processed simultaneously.
     Loop over arrays → think: can I vectorize this with AVX?

  10. REGISTERS HAVE MEMORY
      Zero-extension, aliasing (EAX/RAX), and partial writes have
      non-obvious interactions. Writing EAX zeroes upper RAX.
      Writing AX does NOT. This is a source of subtle bugs.
```

### Cognitive Model for Problem Solving

```
HOW AN EXPERT THINKS ABOUT REGISTERS IN DSA
═══════════════════════════════════════════════════════════════

WHEN WRITING A TIGHT LOOP:
  Q1: How many variables does this loop body need simultaneously?
  Q2: Are they ≤ 14? → They should all live in registers.
  Q3: Are there > 14? → Restructure to reduce live variable count.
  Q4: Are there arrays of integers/floats? → Can I use SIMD?
  Q5: Are there cross-iteration dependencies? → Limits parallelism.

WHEN DEBUGGING PERFORMANCE:
  Q1: Is the bottleneck computation or memory?
  Q2: What does perf stat show for cache-misses vs cycles?
  Q3: Are we spilling registers to stack? (look for PUSH/POP in hot loop asm)
  Q4: Is the compiler using the right register class? (XMM vs YMM)

WHEN WRITING KERNEL CODE:
  Q1: What is the register state at this point?
  Q2: Are interrupts enabled (IF flag)? Is preemption possible?
  Q3: Which CPU is this running on? (read from GS:cpu_number)
  Q4: What is current task? (read from GS:current_task)
  Q5: Has GS been swapped (SWAPGS called)? → user or kernel GS?
```

---

## Quick Reference: x86-64 Register Cheat Sheet

```
═══════════════════════════════════════════════════════════════════════
REGISTER          │ 64b  │ 32b  │ 16b │ 8bH │ 8bL │ ROLE
══════════════════╪══════╪══════╪═════╪═════╪═════╪══════════════════
Accumulator       │ RAX  │ EAX  │ AX  │ AH  │ AL  │ Return val, syscall#
Base              │ RBX  │ EBX  │ BX  │ BH  │ BL  │ Callee-saved
Counter           │ RCX  │ ECX  │ CX  │ CH  │ CL  │ Arg4 (saved by SYSCALL)
Data              │ RDX  │ EDX  │ DX  │ DH  │ DL  │ Arg3, RDMSR hi
Source Index      │ RSI  │ ESI  │ SI  │     │ SIL │ Arg2
Dest Index        │ RDI  │ EDI  │ DI  │     │ DIL │ Arg1
Stack Pointer     │ RSP  │ ESP  │ SP  │     │ SPL │ Stack top (callee)
Base/Frame Ptr    │ RBP  │ EBP  │ BP  │     │ BPL │ Frame (callee)
Extended 8        │ R8   │ R8D  │ R8W │     │ R8B │ Arg5
Extended 9        │ R9   │ R9D  │ R9W │     │ R9B │ Arg6
Extended 10       │ R10  │ R10D │R10W │     │R10B │ Syscall arg4 (caller)
Extended 11       │ R11  │ R11D │R11W │     │R11B │ RFLAGS in SYSCALL
Extended 12       │ R12  │ R12D │R12W │     │R12B │ Callee-saved
Extended 13       │ R13  │ R13D │R13W │     │R13B │ Callee-saved
Extended 14       │ R14  │ R14D │R14W │     │R14B │ Callee-saved
Extended 15       │ R15  │ R15D │R15W │     │R15B │ Callee-saved
Instr Pointer     │ RIP  │  —   │  —  │     │     │ Next instruction
Flags             │RFLAGS│EFLAGS│FLAGS│     │     │ Status/control
══════════════════╧══════╧══════╧═════╧═════╧═════╧══════════════════

SYSCALL ARG MAPPING:
  User:    RAX  RDI  RSI  RDX  R10  R8   R9
  Kernel:  nr   arg1 arg2 arg3 arg4 arg5 arg6
  (Note R10 for arg4 in syscall — NOT RCX, which is trashed by SYSCALL)

FUNCTION CALL ARG MAPPING (System V AMD64):
  Int args: RDI  RSI  RDX  RCX  R8   R9   (then stack)
  FP args:  XMM0 XMM1 XMM2 XMM3 XMM4 XMM5 XMM6 XMM7
  Return:   RAX  (int), XMM0 (float)

CALLEE-SAVED (function must restore):  RBX RBP R12 R13 R14 R15 RSP
CALLER-SAVED (function may clobber):   RAX RCX RDX RSI RDI R8-R11
═══════════════════════════════════════════════════════════════════════
```

---

*End of Guide — Registers & The Linux Kernel*

> *"The machine has no mystery once you see it as it is: a dance of electrons through registers, orchestrated by the kernel's conductor's baton."*