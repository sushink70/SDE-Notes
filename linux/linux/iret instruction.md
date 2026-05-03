# The `IRET` Instruction in Linux — A Complete Deep-Dive Guide

> *"To understand how a CPU returns from an interrupt is to understand how an operating system truly works — every context switch, every syscall, every privilege boundary lives here."*

---

## Table of Contents

1. [Foundational Concepts — Before Everything Else](#1-foundational-concepts)
2. [CPU Privilege Rings and Protection Model](#2-cpu-privilege-rings)
3. [Interrupts, Exceptions, and Traps — The Full Taxonomy](#3-interrupts-exceptions-traps)
4. [The Interrupt Descriptor Table (IDT)](#4-the-idt)
5. [Task State Segment (TSS) and Stack Switching](#5-tss-and-stack-switching)
6. [What Happens When an Interrupt Fires — Step by Step](#6-interrupt-firing-sequence)
7. [The IRET Instruction — Anatomy and Semantics](#7-iret-anatomy)
8. [Stack Frame Layouts — 16/32/64-bit](#8-stack-frame-layouts)
9. [RFLAGS — Every Bit That IRET Touches](#9-rflags)
10. [Privilege Level Transitions — CPL, RPL, DPL](#10-privilege-level-transitions)
11. [SWAPGS — The Hidden Step Before IRET in Linux](#11-swapgs)
12. [IRET vs SYSRET vs SYSEXIT — When Linux Uses Each](#12-iret-vs-sysret)
13. [Linux Kernel Entry/Exit Code — Real Implementation](#13-linux-entry-exit)
14. [Security Implications — Meltdown, Spectre, SWAPGS Attack](#14-security)
15. [NMI, Double Fault, and Special Cases](#15-special-cases)
16. [C Implementation — Bare-Metal Interrupt Handler](#16-c-implementation)
17. [Rust Implementation — Type-Safe Interrupt Handling](#17-rust-implementation)
18. [Performance Analysis — Cache, Pipeline, Microarchitecture](#18-performance)
19. [Mental Models and Debugging IRET Issues](#19-mental-models)
20. [Summary Reference Card](#20-summary)

---

## 1. Foundational Concepts

### What is an Instruction?

At the hardware level, every CPU operation is an **instruction** — a binary-encoded command the processor fetches from memory and executes. `IRET` (Interrupt Return) is one specific instruction in the x86/x86-64 ISA (Instruction Set Architecture).

### What is a Privilege Level?

Modern CPUs enforce **separation** between operating system code and user program code. This separation is implemented using **privilege levels** — also called **rings**. The CPU hardware checks which ring you are in before allowing certain operations. `IRET` is deeply involved in **crossing these boundaries**.

### What is a Stack Frame?

When a function is called or an interrupt fires, the CPU **automatically pushes** (saves) certain registers onto the stack. This saved state is called a **stack frame**. `IRET` works by **popping** (restoring) that saved state to return execution to exactly where it was interrupted.

### Key Terms Glossary

| Term | Meaning |
|------|---------|
| **ISA** | Instruction Set Architecture — the CPU's instruction vocabulary |
| **Ring** | Hardware-enforced privilege level (0 = kernel, 3 = user) |
| **CPL** | Current Privilege Level — which ring the CPU is currently in |
| **DPL** | Descriptor Privilege Level — privilege level of a segment/gate |
| **RPL** | Requested Privilege Level — privilege embedded in a segment selector |
| **IDT** | Interrupt Descriptor Table — maps interrupt numbers to handler addresses |
| **GDT** | Global Descriptor Table — defines memory segments and their privilege |
| **TSS** | Task State Segment — holds kernel stack pointers for privilege transitions |
| **RFLAGS** | Register FLAGS — CPU status bits (interrupts enabled, zero flag, etc.) |
| **CS** | Code Segment register — contains current privilege level (CPL) |
| **SS** | Stack Segment register |
| **RSP** | Register Stack Pointer — top of the stack |
| **RIP** | Register Instruction Pointer — next instruction to execute |
| **IRET** | Interrupt Return — pops saved RIP, CS, RFLAGS (and RSP, SS if privilege changed) |
| **IRETQ** | IRET in 64-bit (Long Mode) — always 64-bit operand size |
| **SWAPGS** | Swaps GS base register between kernel and user values |
| **NMI** | Non-Maskable Interrupt — cannot be disabled by software |
| **IST** | Interrupt Stack Table — separate stacks for critical exceptions |

---

## 2. CPU Privilege Rings

### The Ring Model

The x86 architecture defines **4 privilege rings**, numbered 0–3. Lower number = higher privilege.

```
  ┌─────────────────────────────────────────────────────────────┐
  │                        x86 Ring Model                       │
  │                                                             │
  │   ┌─────────────────────────────────────────────────────┐  │
  │   │  Ring 0  ── Kernel Mode                             │  │
  │   │  ┌───────────────────────────────────────────────┐  │  │
  │   │  │  Ring 1  ── (Unused in Linux; historical)     │  │  │
  │   │  │  ┌─────────────────────────────────────────┐  │  │  │
  │   │  │  │  Ring 2  ── (Unused in Linux)           │  │  │  │
  │   │  │  │  ┌───────────────────────────────────┐  │  │  │  │
  │   │  │  │  │  Ring 3  ── User Mode             │  │  │  │  │
  │   │  │  │  │  Applications, libraries          │  │  │  │  │
  │   │  │  │  └───────────────────────────────────┘  │  │  │  │
  │   │  │  └─────────────────────────────────────────┘  │  │  │
  │   │  └───────────────────────────────────────────────┘  │  │
  │   └─────────────────────────────────────────────────────┘  │
  └─────────────────────────────────────────────────────────────┘

  Ring 0: Can access ALL hardware, ALL instructions, ALL memory
  Ring 3: Can only access user memory, no I/O ports, no privileged instructions
  
  Linux only uses Ring 0 (kernel) and Ring 3 (user).
```

### CPL — Current Privilege Level

The **CPL** is stored in bits [1:0] of the **CS (Code Segment) register**. The CPU checks CPL before every privileged operation.

```
  CS Register (16 bits):
  ┌────────────────────┬─────┬──┐
  │   Selector Index   │ TI  │CPL│
  │   [15:3]           │ [2] │[1:0]│
  └────────────────────┴─────┴──┘
                                ▲
                    Current Privilege Level
                    00 = Ring 0 (kernel)
                    11 = Ring 3 (user)
```

### Why This Matters for IRET

When `IRET` executes, it **loads a new CS value from the stack**. The CPL in that CS value determines **what privilege level the CPU returns to**. If the new CPL is higher (less privileged) than the current CPL, additional stack and segment restoration occurs. This is the **privilege transition** mechanism.

---

## 3. Interrupts, Exceptions, and Traps — The Full Taxonomy

Before understanding `IRET`, you must understand what it returns *from*.

### Three Categories

```
  ┌──────────────────────────────────────────────────────────────────┐
  │               CPU Control Flow Transfers                         │
  │                                                                  │
  │   SYNCHRONOUS (caused by current instruction)                    │
  │   ┌────────────────────────────────────────────────────────┐    │
  │   │  EXCEPTIONS                                            │    │
  │   │  ├── FAULTS     : Can be corrected, restart same instr │    │
  │   │  │   Examples   : Page Fault (#PF), Segment Not Present │    │
  │   │  ├── TRAPS      : Report after instruction completes   │    │
  │   │  │   Examples   : Breakpoint (#BP), Overflow (#OF)     │    │
  │   │  └── ABORTS     : Severe error, cannot resume          │    │
  │   │      Examples   : Double Fault (#DF), Machine Check    │    │
  │   └────────────────────────────────────────────────────────┘    │
  │                                                                  │
  │   ASYNCHRONOUS (caused by hardware, independent of instruction)  │
  │   ┌────────────────────────────────────────────────────────┐    │
  │   │  HARDWARE INTERRUPTS                                   │    │
  │   │  ├── MASKABLE   : Can be disabled via IF flag in FLAGS │    │
  │   │  │   Examples   : Timer, keyboard, network card        │    │
  │   │  └── NON-MASKABLE (NMI): Cannot be disabled            │    │
  │   │      Examples   : Memory parity error, watchdog        │    │
  │   └────────────────────────────────────────────────────────┘    │
  │                                                                  │
  │   SOFTWARE INTERRUPTS                                            │
  │   ┌────────────────────────────────────────────────────────┐    │
  │   │  INT n  instruction (e.g., INT 0x80 — old Linux syscall│    │
  │   │  SYSCALL/SYSENTER — fast system call path              │    │
  │   └────────────────────────────────────────────────────────┘    │
  └──────────────────────────────────────────────────────────────────┘
```

### The Interrupt Vector Table

Every interrupt and exception has a **vector number** (0–255). Intel defines vectors 0–31 for CPU exceptions:

```
  Vector │ Mnemonic │ Description                  │ Type
  ───────┼──────────┼──────────────────────────────┼───────────
    0    │  #DE     │ Divide Error                  │ Fault
    1    │  #DB     │ Debug Exception               │ Fault/Trap
    2    │  ---     │ NMI Interrupt                 │ Interrupt
    3    │  #BP     │ Breakpoint (INT3)             │ Trap
    4    │  #OF     │ Overflow (INTO)               │ Trap
    5    │  #BR     │ BOUND Range Exceeded          │ Fault
    6    │  #UD     │ Invalid Opcode                │ Fault
    7    │  #NM     │ Device Not Available          │ Fault
    8    │  #DF     │ Double Fault                  │ Abort (error code=0)
   10    │  #TS     │ Invalid TSS                   │ Fault (error code)
   11    │  #NP     │ Segment Not Present           │ Fault (error code)
   12    │  #SS     │ Stack Segment Fault           │ Fault (error code)
   13    │  #GP     │ General Protection Fault      │ Fault (error code)
   14    │  #PF     │ Page Fault                    │ Fault (error code, CR2)
   16    │  #MF     │ x87 FPU Error                 │ Fault
   17    │  #AC     │ Alignment Check               │ Fault (error code)
   18    │  #MC     │ Machine Check                 │ Abort
   19    │  #XM     │ SIMD FP Exception             │ Fault
   20    │  #VE     │ Virtualization Exception      │ Fault
  32-255 │  ---     │ User-defined (hardware IRQs)  │ Interrupt
```

---

## 4. The Interrupt Descriptor Table (IDT)

### What is the IDT?

The IDT is a **table in memory** that maps each interrupt vector (0–255) to a **gate descriptor** — essentially a pointer to the interrupt handler plus privilege/type information.

The CPU finds the IDT via the **IDTR register** (Interrupt Descriptor Table Register), loaded using the `LIDT` instruction.

```
  IDTR Register:
  ┌───────────────────────────┬──────────┐
  │   Base Address (64-bit)   │  Limit   │
  │   64 bits                 │  16 bits │
  └───────────────────────────┴──────────┘
           │
           ▼ points to
  
  IDT (in kernel memory):
  ┌──────────────────────────────────────────────────────┐
  │  Entry 0   : Divide Error handler gate               │  ◄── 16 bytes each
  │  Entry 1   : Debug handler gate                      │
  │  Entry 2   : NMI handler gate                        │
  │  Entry 3   : Breakpoint handler gate                 │
  │  ...                                                 │
  │  Entry 32  : Timer IRQ handler gate                  │
  │  ...                                                 │
  │  Entry 255 : Last user-defined interrupt             │
  └──────────────────────────────────────────────────────┘
```

### IDT Gate Descriptor (64-bit Format)

Each IDT entry is **16 bytes** in 64-bit mode:

```
  64-bit Interrupt Gate Descriptor (16 bytes = 128 bits):

  Byte:  15      13 12    8 7      5 4   0  ← (high 8 bytes)
         ┌────────┬──┬──────┬───────┬─────┐
         │Offset  │  │ Type │       │     │
         │[63:32] │  │+DPL+P│  IST  │     │
         └────────┴──┴──────┴───────┴─────┘

  Byte:  15      0           15    0       ← (low 8 bytes)  
         ┌───────────────────┬──────────────┐
         │ Offset [31:16]    │   Segment    │
         │                   │   Selector   │
         └───────────────────┴──────────────┘
         ┌───────────────────────────────────┐
         │ Offset [15:0]                     │
         └───────────────────────────────────┘

  Fields:
  ├── Offset [63:0]  : 64-bit address of the handler function
  ├── Segment Selector : Points to kernel code segment in GDT (ring 0)
  ├── IST [2:0]      : Interrupt Stack Table index (0 = use current stack)
  ├── Type [3:0]     : 0xE = 64-bit Interrupt Gate (clears IF flag)
  │                   0xF = 64-bit Trap Gate (preserves IF flag)
  ├── DPL [1:0]      : Descriptor Privilege Level (who can call via INT n)
  └── P              : Present bit (1 = valid entry)

  KEY DIFFERENCE — Interrupt Gate vs Trap Gate:
  ┌─────────────────┬────────────────────────────────────────────┐
  │ Interrupt Gate  │ Clears IF bit in RFLAGS — disables         │
  │                 │ further maskable interrupts during handler  │
  ├─────────────────┼────────────────────────────────────────────┤
  │ Trap Gate       │ Preserves IF bit — nested interrupts OK    │
  └─────────────────┴────────────────────────────────────────────┘
```

### How the CPU Looks Up an IDT Entry

```
  When interrupt vector N fires:

  1. CPU reads IDTR to find IDT base address
  2. Calculates: IDT[N] = IDTR.base + (N × 16)
  3. Reads the 16-byte gate descriptor at that address
  4. Extracts the handler's segment selector and 64-bit offset
  5. Performs privilege checks (current CPL vs gate DPL)
  6. Switches stacks if needed (via TSS)
  7. Pushes interrupt frame onto the (new) stack
  8. Jumps to the handler offset
```

---

## 5. Task State Segment (TSS) and Stack Switching

### Why TSS?

When an interrupt fires **while in user mode (Ring 3)**, the CPU must switch to a **kernel stack (Ring 0)** before it can safely execute the interrupt handler. It cannot use the user stack because:
- The user stack pointer (RSP) may be invalid or point to user memory
- Kernel data must not be placed on user-accessible stacks

The **TSS** tells the CPU **where to find the kernel stack**.

```
  TSS Structure (x86-64, abbreviated):

  Offset │ Size │ Field
  ───────┼──────┼─────────────────────────────────────────────
   0x04  │  8   │ RSP0  ← kernel stack pointer for Ring 0
   0x0C  │  8   │ RSP1  ← kernel stack pointer for Ring 1
   0x14  │  8   │ RSP2  ← kernel stack pointer for Ring 2
   0x24  │  8   │ IST1  ← Interrupt Stack Table entry 1
   0x2C  │  8   │ IST2  ← IST entry 2
   0x34  │  8   │ IST3  ← IST entry 3
   0x3C  │  8   │ IST4  ← IST entry 4
   0x44  │  8   │ IST5  ← IST entry 5
   0x4C  │  8   │ IST6  ← IST entry 6
   0x54  │  8   │ IST7  ← IST entry 7
   0x66  │  2   │ IOPB offset
```

### The IST (Interrupt Stack Table)

The IST provides **dedicated stacks** for critical exceptions that must be handled even if the kernel stack is corrupt:

```
  IST Stack Selection:
  
  IDT Gate has IST field = 0:  Use RSP0 from TSS (normal kernel stack switch)
  IDT Gate has IST field = 1:  Always use IST1 from TSS (dedicated NMI stack)
  IDT Gate has IST field = 2:  Always use IST2 from TSS (dedicated DF stack)
  
  Linux IST assignments:
  IST1: Double Fault (#DF)
  IST2: NMI
  IST3: Machine Check (#MC)
  IST4: Debug (#DB) — in some configs
```

### Stack Switch Sequence (Ring 3 → Ring 0)

```
  Before interrupt (running user code, Ring 3):
  ┌─────────────────────────────────────────────┐
  │   CPU Registers                             │
  │   RSP ──────────────────────────────────►  │
  │   CS  = 0x33 (Ring 3 code segment)         │  User Stack
  │   SS  = 0x2B (Ring 3 data segment)         │  ┌──────────┐
  └─────────────────────────────────────────────┘  │  ...     │
                                                    │  user    │
                                                    │  data    │
                                                    └──────────┘
  
  CPU loads RSP from TSS.RSP0 (kernel stack pointer):
  ┌─────────────────────────────────────────────┐
  │   CPU Registers (after TSS load)            │
  │   RSP ──────────────────────────────────►  │
  │   CS  = 0x10 (Ring 0, after interrupt)      │  Kernel Stack
  └─────────────────────────────────────────────┘  ┌──────────┐
                                                    │  ...     │
                                                    │  (empty, │
                                                    │  grows   │
                                                    │  down)   │
                                                    └──────────┘
```

---

## 6. What Happens When an Interrupt Fires — Step by Step

This is the **complete sequence** the CPU hardware performs automatically (without any software involvement) when an interrupt fires. Understanding this sequence IS understanding what `IRET` must undo.

```
  INTERRUPT DELIVERY SEQUENCE (x86-64, Ring 3 → Ring 0):

  Step 1: CPU detects interrupt signal (external IRQ or internal exception)
          │
          ▼
  Step 2: CPU saves current RSP and SS (will need them for the frame)
          temp_SS  = SS
          temp_RSP = RSP
          │
          ▼
  Step 3: CPU loads new SS and RSP from TSS.RSP0 (kernel stack)
          SS  = kernel data segment selector
          RSP = TSS.RSP0
          │
          ▼
  Step 4: CPU aligns RSP to 16-byte boundary (RSP &= ~0xF, then -= 8 for alignment)
          │
          ▼
  Step 5: CPU pushes the interrupt frame onto the NEW (kernel) stack:
  
          ┌─────────────────────────────┐  ◄── RSP before step 5
          │                             │
          │  SS        (old user SS)    │  pushed first (high address)
          │  RSP       (old user RSP)   │
          │  RFLAGS    (old flags)      │
          │  CS        (old user CS)    │
          │  RIP       (old user RIP)   │  pushed last (low address)
          │  [Error Code] (if fault)    │  ◄── some exceptions push this
          │                             │
          └─────────────────────────────┘  ◄── RSP now points here
          │
          ▼
  Step 6: CPU loads CS from IDT gate's segment selector (kernel code seg)
          New CPL = 0 (extracted from new CS bits[1:0])
          │
          ▼
  Step 7: If Interrupt Gate: CPU clears IF bit in RFLAGS (disables interrupts)
          If Trap Gate: IF bit preserved
          │
          ▼
  Step 8: CPU clears TF (Trap Flag), AC (Alignment Check), NT (Nested Task) bits
          │
          ▼
  Step 9: CPU loads RIP from IDT gate's offset field (handler address)
          │
          ▼
  Step 10: Handler begins execution in Ring 0
```

### Same-Privilege Interrupt (Ring 0 → Ring 0)

If the interrupt fires while already in Ring 0 (kernel mode):

```
  SAME-PRIVILEGE INTERRUPT FRAME (no stack switch):
  
  ┌─────────────────────────────┐  ◄── old RSP
  │  [Error Code] (if applies)  │
  │  RIP        (interrupted)   │
  │  CS         (kernel CS)     │
  │  RFLAGS     (saved flags)   │
  │  [NO RSP pushed]            │  ← Stack NOT switched; RSP/SS not saved
  │  [NO SS pushed]             │
  └─────────────────────────────┘  ◄── new RSP (handler runs here)
  
  NOTE: No SS/RSP in frame because there was no stack switch!
  IRET handles this by checking the saved CS privilege level.
```

---

## 7. The IRET Instruction — Anatomy and Semantics

### What IRET Does

`IRET` is the **only instruction that can atomically restore all the state needed to return from an interrupt**. It:

1. Pops **RIP** → restores instruction pointer
2. Pops **CS** → restores code segment (and CPL)
3. Pops **RFLAGS** → restores all CPU status flags (including IF — interrupt enable)
4. If returning to lower privilege (higher CPL): also pops **RSP** and **SS**

The entire operation is **atomic** from the perspective of interrupts — you cannot be interrupted mid-`IRET`.

### The Three Variants

```
  ┌──────────┬──────────┬──────────────────────────────────────────────┐
  │ Mnemonic │   Mode   │ Description                                  │
  ├──────────┼──────────┼──────────────────────────────────────────────┤
  │  IRET    │ 16-bit   │ Pops IP, CS, FLAGS (2 bytes each)            │
  ├──────────┼──────────┼──────────────────────────────────────────────┤
  │  IRETD   │ 32-bit   │ Pops EIP, CS, EFLAGS (4 bytes each)         │
  ├──────────┼──────────┼──────────────────────────────────────────────┤
  │  IRETQ   │ 64-bit   │ Pops RIP, CS, RFLAGS (8 bytes each)         │
  │          │(Long Mode)│ ALWAYS used in 64-bit Linux kernel          │
  └──────────┴──────────┴──────────────────────────────────────────────┘
  
  In 64-bit mode, the assembler mnemonic is still "iretq" or simply "iret"
  with the REX.W prefix. Linux explicitly uses "iretq" in its assembly.
```

### IRET Decision Tree — Privilege Change Detection

```
  IRET executes:
  
  Pop RIP, CS, RFLAGS from stack
           │
           ▼
  Check: saved_CS.CPL vs current CPL
           │
    ┌──────┴────────┐
    │               │
    ▼               ▼
  SAME            DIFFERENT
  PRIVILEGE       PRIVILEGE
  (e.g., 0→0)    (e.g., 0→3)
    │               │
    ▼               ▼
  Done.          Pop RSP, SS from stack
  RIP, CS,       Restore RSP (user stack pointer)
  RFLAGS         Restore SS  (user stack segment)
  restored.               │
                          ▼
                 Check: SS.RPL == CS.RPL
                 (segment privilege must match)
                          │
                          ▼
                 Null-out ES, DS, FS, GS if their
                 DPL < new CPL (security: prevent
                 kernel segment leaks to user mode)
                          │
                          ▼
                 Done. CPU now in user mode.
```

---

## 8. Stack Frame Layouts — 16/32/64-bit

### 16-bit Real Mode Stack Frame

```
  Stack (grows down):
  ┌───────────────────────────────┐  ← Higher address
  │         FLAGS (2 bytes)       │  pushed first
  │         CS    (2 bytes)       │
  │         IP    (2 bytes)       │  pushed last (top of frame)
  └───────────────────────────────┘  ← SP points here
  
  IRET pops: IP, CS, FLAGS (in that order, 2 bytes each)
```

### 32-bit Protected Mode Stack Frame (No Privilege Change)

```
  Stack (grows down):
  ┌───────────────────────────────┐
  │        EFLAGS  (4 bytes)      │
  │        CS      (4 bytes)      │  ← zero-padded selector
  │        EIP     (4 bytes)      │
  │ [Error Code]   (4 bytes)      │  ← only for some exceptions
  └───────────────────────────────┘  ← ESP points here
  
  IRETD pops: EIP, CS, EFLAGS
```

### 32-bit Protected Mode Stack Frame (With Privilege Change, Ring 3 → Ring 0)

```
  Stack (grows down, on KERNEL stack after switch):
  ┌───────────────────────────────┐
  │        SS      (4 bytes)      │  ← user stack segment
  │        ESP     (4 bytes)      │  ← user stack pointer
  │        EFLAGS  (4 bytes)      │
  │        CS      (4 bytes)      │  ← user code segment (CPL=3 in bits[1:0])
  │        EIP     (4 bytes)      │
  │ [Error Code]   (4 bytes)      │  ← only for some exceptions
  └───────────────────────────────┘  ← ESP points here
  
  IRETD pops: EIP, CS, EFLAGS, ESP, SS
  (SS/ESP only popped when returning to different privilege level)
```

### 64-bit Long Mode Stack Frame (IRETQ)

```
  CRITICAL: In 64-bit mode, ALL interrupt frames ALWAYS include RSP and SS,
  even for same-privilege returns. This is a design change from 32-bit!
  
  Actually — correction: In 64-bit mode, RSP and SS are ALWAYS pushed even
  for same-privilege level interrupts. IRETQ always pops all 5 fields.
  
  Stack (grows downward, on kernel stack, 8-byte aligned):
  
  Higher Address
  │
  │  ┌──────────────────────────────────────────────┐
  │  │  SS        (8 bytes, upper 48 bits = 0)      │  ◄── RSP + 32
  │  ├──────────────────────────────────────────────┤
  │  │  RSP       (8 bytes)                         │  ◄── RSP + 24
  │  ├──────────────────────────────────────────────┤
  │  │  RFLAGS    (8 bytes, upper 32 bits = 0)      │  ◄── RSP + 16
  │  ├──────────────────────────────────────────────┤
  │  │  CS        (8 bytes, upper 48 bits = 0)      │  ◄── RSP + 8
  │  ├──────────────────────────────────────────────┤
  │  │  RIP       (8 bytes)                         │  ◄── RSP + 0  (RSP points here)
  │  ├──────────────────────────────────────────────┤
  │  │  Error Code (8 bytes, if applicable)         │  ◄── pushed BELOW RIP by CPU
  │  └──────────────────────────────────────────────┘       handler must pop this
  │
  Lower Address (stack grows down)
  
  Total frame without error code: 5 × 8 = 40 bytes
  Total frame with error code:    6 × 8 = 48 bytes
  
  IRETQ pops (in order): RIP → CS → RFLAGS → RSP → SS
  
  CRITICAL NOTE on Error Code:
  The error code is NOT popped by IRETQ. The interrupt handler
  is responsible for removing it (usually with "add rsp, 8" or "pop rcx")
  BEFORE executing IRETQ.
```

### Linux's Actual pt_regs Structure

Linux saves ALL general-purpose registers (which the CPU does NOT save automatically) in the `pt_regs` structure, placed just above the hardware-pushed interrupt frame:

```
  Full Linux interrupt stack layout (x86-64, from arch/x86/include/asm/ptrace.h):
  
  Higher Address
  │
  │  ┌──────────────────────────────────┐
  │  │  SS                  +0x98       │ ─┐
  │  │  RSP                 +0x90       │  │ Hardware-pushed
  │  │  RFLAGS              +0x88       │  │ interrupt frame
  │  │  CS                  +0x80       │  │ (IRETQ reads these)
  │  │  RIP                 +0x78       │ ─┘
  │  │  orig_rax            +0x70       │ ← error code or syscall nr
  │  ├──────────────────────────────────┤
  │  │  R15                 +0x00       │ ─┐
  │  │  R14                 +0x08       │  │
  │  │  R13                 +0x10       │  │
  │  │  R12                 +0x18       │  │
  │  │  RBP                 +0x20       │  │ Software-pushed
  │  │  RBX                 +0x28       │  │ (by Linux's entry code
  │  │  R11                 +0x30       │  │  using PUSH instructions)
  │  │  R10                 +0x38       │  │
  │  │  R9                  +0x40       │  │
  │  │  R8                  +0x48       │  │
  │  │  RAX                 +0x50       │  │
  │  │  RCX                 +0x58       │  │
  │  │  RDX                 +0x60       │  │
  │  │  RSI                 +0x68       │  │
  │  │  RDI                 +0x70 ─────┤  │
  │  └──────────────────────────────────┘ ─┘
  │
  Lower Address — RSP points here during handler execution
```

---

## 9. RFLAGS — Every Bit That IRET Touches

`IRET` restores the **entire RFLAGS register** from the saved value on the stack. This is crucial because RFLAGS contains the **interrupt enable flag (IF)**, meaning `IRET` can re-enable interrupts as part of returning.

```
  RFLAGS Register (64-bit), bits that matter:
  
  Bit │ Name │ Symbol │ Description
  ────┼──────┼────────┼────────────────────────────────────────────────
   0  │  CF  │        │ Carry Flag
   1  │  --  │        │ Reserved (always 1)
   2  │  PF  │        │ Parity Flag
   4  │  AF  │        │ Auxiliary Carry Flag
   6  │  ZF  │        │ Zero Flag
   7  │  SF  │        │ Sign Flag
   8  │  TF  │   TF   │ Trap Flag (single-step debugging) ← IRET restores
   9  │  IF  │   IF   │ Interrupt Flag (1 = interrupts enabled) ← KEY FLAG
  10  │  DF  │        │ Direction Flag
  11  │  OF  │        │ Overflow Flag
  12-13 │ IOPL │      │ I/O Privilege Level ← can only change from Ring 0
  14  │  NT  │   NT   │ Nested Task Flag ← IRET uses this in 32-bit!
  16  │  RF  │   RF   │ Resume Flag (suppresses debug exceptions)
  17  │  VM  │   VM   │ Virtual-8086 Mode (32-bit only)
  18  │  AC  │   AC   │ Alignment Check
  19  │  VIF │        │ Virtual Interrupt Flag
  20  │  VIP │        │ Virtual Interrupt Pending
  21  │  ID  │        │ ID Flag (can CPUID be used?)
  
  IRET Restrictions on RFLAGS restoration:
  ┌──────────────────────────────────────────────────────────────────────┐
  │ IF:   Can only be set to 1 if new CPL ≤ IOPL                        │
  │       (prevents user code from enabling interrupts if IOPL < CPL)   │
  │ IOPL: Can only be changed if current CPL = 0 (kernel only)          │
  │ VM:   Special handling for virtual-8086 mode (32-bit legacy)        │
  │ NT:   Nested Task flag — if 1 in 32-bit, IRET chains tasks (TSS)    │
  └──────────────────────────────────────────────────────────────────────┘
```

### The IF Flag and IRET — A Critical Interaction

```
  Interrupt Gate Handler execution flow:
  
  [Interrupt fires] → CPU clears IF → handler runs with IF=0 (no interrupts)
                                                 │
                                                 ▼
                                     Handler does work
                                                 │
                                                 ▼
                                     IRETQ restores saved RFLAGS
                                     Saved RFLAGS had IF=1
                                                 │
                                                 ▼
                                     IF is now 1 again ← interrupts re-enabled
                                     ATOMICALLY as part of IRET
  
  This atomicity is crucial: between the last instruction of the handler
  and re-enabling interrupts, there is NO window where the system is in
  an inconsistent state. IRET is the only way to do this safely.
```

---

## 10. Privilege Level Transitions — CPL, RPL, DPL

### The Three Privilege Fields

```
  ┌─────────────────────────────────────────────────────────────────┐
  │  CPL — Current Privilege Level                                  │
  │  Located in: CS register bits [1:0]                            │
  │  Meaning: What privilege level the CPU is currently running at  │
  │                                                                 │
  │  DPL — Descriptor Privilege Level                               │
  │  Located in: GDT/LDT segment descriptor, IDT gate descriptor   │
  │  Meaning: Minimum privilege needed to access this descriptor    │
  │                                                                 │
  │  RPL — Requested Privilege Level                                │
  │  Located in: Segment selector bits [1:0] (loaded into CS/DS/etc)│
  │  Meaning: The privilege level being requested/claimed           │
  └─────────────────────────────────────────────────────────────────┘
  
  Effective Privilege Level (EPL) = max(CPL, RPL)
  Access granted only if: EPL ≤ DPL
```

### IRET Privilege Transition — The Exact Checks

```
  When IRETQ executes, the CPU performs these checks IN ORDER:

  1. Pop RIP, CS, RFLAGS, RSP, SS from stack
  
  2. Check: saved CS is not null (not 0x0000)
     → If null: #GP fault
  
  3. Extract new_CPL = saved_CS[1:0]
  
  4. Check: new_CPL >= current CPL
     → IRET cannot increase privilege (return to more privileged level)
     → If new_CPL < current CPL: #GP fault
     → (This prevents user code from crafting a fake frame to get Ring 0)
  
  5. If new_CPL == current_CPL (same privilege):
     → Just load CS and RIP (and RFLAGS)
     → RSP/SS from stack are also loaded in 64-bit mode
     → Continue
  
  6. If new_CPL > current_CPL (returning to less privileged code):
     → Load RSP, SS from stack
     → Check: SS.RPL == new_CPL
     → Check: SS segment is valid, writable, present
     → Null-check: DS, ES, FS, GS selectors
        If any of these segment's DPL < new_CPL:
        → Set that segment register to null (0)
        (Prevents kernel segment handles from being usable in user mode)
     → Switch to user mode
```

### Why IRET Cannot Return to Higher Privilege

This is a **fundamental security property**:

```
  ATTACK SCENARIO (Prevented by IRET design):
  
  Attacker (in Ring 3) wants to gain Ring 0 access.
  Attacker crafts a fake stack frame with CS = kernel_cs (CPL=0).
  
  Without protection:
  IRETQ → reads fake CS → "returns" to Ring 0 → PRIVILEGE ESCALATION!
  
  With protection:
  IRETQ → reads fake CS → new_CPL (0) < current CPL (0 — we're in kernel)
                                       WAIT. We're in kernel (Ring 0)...
  
  Actually: The attacker cannot execute IRETQ from user space
  because IRETQ is not a privileged instruction itself, BUT:
  - The saved CS value determines where to RETURN to
  - If attacker is in Ring 3 and executes IRETQ with fake frame:
    saved CS has CPL=0 → new_CPL (0) < current CPL (3)
    → This IS less than current → wait, 0 < 3 means MORE privileged
    → Check: new_CPL >= current_CPL? 0 >= 3? FALSE → #GP
  
  The rule "new_CPL must be >= current CPL" means:
  You can only IRET to the SAME or LESS privileged level.
  Never to MORE privileged. 
```

---

## 11. SWAPGS — The Hidden Step Before IRET in Linux

### What is GS?

The GS segment register (in 64-bit mode) is used as a **base pointer** to per-CPU data structures in the Linux kernel. When in kernel mode, GS.base points to the `percpu` area. When in user mode, GS.base is used for thread-local storage (TLS).

### The Problem

```
  User Mode:   GS.base → user's TLS data (libc thread local storage)
  Kernel Mode: GS.base → kernel per-CPU data (struct cpu_info, etc.)
  
  On entry to kernel: need to swap GS to kernel value
  On exit  to user:   need to swap GS back to user value
```

### SWAPGS Instruction

`SWAPGS` atomically swaps the value in GS.base with the value in MSR `IA32_KERNEL_GS_BASE` (MSR 0xC0000102).

```
  SWAPGS semantics:
  
  temp           = GS.base
  GS.base        = MSR[IA32_KERNEL_GS_BASE]
  MSR[IA32_KERNEL_GS_BASE] = temp
  
  Linux setup:
  ├── MSR_GS_BASE          (0xC0000101): currently active GS base
  └── MSR_KERNEL_GS_BASE   (0xC0000102): the "hidden" stored value
  
  When entering kernel (e.g., via syscall or interrupt from user):
  SWAPGS → GS.base becomes kernel per-CPU pointer
  
  When returning to user (just before IRETQ):
  SWAPGS → GS.base becomes user TLS pointer again
```

### The Full Exit Sequence in Linux (IRETQ path)

```
  Linux interrupt/syscall return path (simplified from entry_64.S):
  
  restore_regs_and_iret:
      ┌─────────────────────────────────────────────────────────┐
      │ 1. Restore general-purpose registers from pt_regs       │
      │    (POP R15, R14, ..., RDI from stack)                  │
      │                                                         │
      │ 2. Check: are we returning to user space?               │
      │    (Test saved CS: if CPL=3, yes)                       │
      │                                                         │
      │ 3. If returning to user:                                │
      │    SWAPGS  ← restore user GS                           │
      │                                                         │
      │ 4. IRETQ  ← pop RIP, CS, RFLAGS, RSP, SS              │
      │    CPU now running in Ring 3 with user stack            │
      └─────────────────────────────────────────────────────────┘
  
  ORDERING IS CRITICAL:
  SWAPGS must happen BEFORE IRETQ, not after.
  After IRETQ, we are in user mode — GS would point to kernel data,
  which the user could then read via GS-relative accesses!
```

---

## 12. IRET vs SYSRET vs SYSEXIT — When Linux Uses Each

### Three Ways to Return from Kernel to User

```
  ┌─────────────────────────────────────────────────────────────────────┐
  │                    Kernel-to-User Return Methods                    │
  ├──────────────┬──────────────────────────────────────────────────────┤
  │   Method     │  Description                                         │
  ├──────────────┼──────────────────────────────────────────────────────┤
  │   IRETQ      │ Most general. Restores RIP, CS, RFLAGS, RSP, SS     │
  │              │ from stack. Works for ALL cases.                     │
  │              │ Slower (~100 cycles on modern CPUs)                  │
  │              │ Used for: exceptions, hardware interrupts, signal    │
  │              │ delivery, ptrace, any non-standard return            │
  ├──────────────┼──────────────────────────────────────────────────────┤
  │   SYSRETQ    │ Fast return after SYSCALL instruction.              │
  │              │ Restores: RIP from RCX, RFLAGS from R11             │
  │              │ Does NOT restore: RSP (must be done by software)     │
  │              │ Does NOT restore: CS, SS (hardcoded from MSR_STAR)  │
  │              │ Much faster (~30-50 cycles)                          │
  │              │ Restriction: RIP must be canonical (bits[63:47]=0)  │
  │              │ Linux preference: use SYSRETQ when possible          │
  ├──────────────┼──────────────────────────────────────────────────────┤
  │   SYSEXIT    │ Return from SYSENTER (32-bit fast syscall).         │
  │              │ Rarely used in modern 64-bit Linux                   │
  └──────────────┴──────────────────────────────────────────────────────┘
```

### When Linux Chooses IRETQ vs SYSRETQ

```
  Linux syscall return decision (arch/x86/entry/entry_64.S):
  
  syscall_return:
         │
         ▼
  Check: pt_regs modified? (signals, ptrace, seccomp?)
         │
    ┌────┴─────────────────┐
    │ NO                   │ YES
    ▼                      ▼
  Check: RIP canonical?   Use IRETQ
         │               (full frame restore)
    ┌────┴──────┐
    │ YES       │ NO
    ▼           ▼
  SYSRETQ    IRETQ
  (fast)     (safe)
  
  Linux also uses IRETQ when:
  - Returning after delivering a signal (signal frame is an IRET frame)
  - Returning from ptrace-modified context
  - Returning to 32-bit user code (SYSRETQ is 64-bit only)
  - Returning after kernel modification of saved registers
  - Returning from an exception (not a syscall)
  - Any interrupt return (timer, IRQ, etc.)
```

---

## 13. Linux Kernel Entry/Exit Code — Real Implementation

### The Entry Point Architecture (Linux 6.x)

```
  Linux x86-64 kernel entry points:
  
  ┌─────────────────────────────────────────────────────────────────┐
  │  User Space                                                     │
  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
  │  │  SYSCALL     │  │  INT 0x80    │  │  Hardware Interrupt   │  │
  │  │  instruction │  │  (compat)    │  │  (IRQ0-255)          │  │
  │  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
  └─────────┼─────────────────┼────────────────────  │─────────────┘
            │                 │                       │
  ┌─────────┼─────────────────┼───────────────────────┼─────────────┐
  │  Kernel │ entry_SYSCALL_64│entry_INT80_compat      │             │
  │         ▼                 ▼                   asm_common_interrupt│
  │  ┌──────────────┐  ┌──────────────┐               ▼            │
  │  │ SWAPGS       │  │ SWAPGS       │       ┌────────────────┐   │
  │  │ save RSP     │  │ save RSP     │       │ SWAPGS         │   │
  │  │ set kernel   │  │ set kernel   │       │ push frame     │   │
  │  │ RSP          │  │ RSP          │       │ call handler   │   │
  │  │ save regs    │  │ save regs    │       │ restore regs   │   │
  │  │ (pt_regs)    │  │ (pt_regs)    │       │ SWAPGS         │   │
  │  │ call         │  │ call         │       │ IRETQ          │   │
  │  │ do_syscall   │  │ do_int80     │       └────────────────┘   │
  │  │ ret_from     │  │              │                             │
  │  │ _syscall     │  │              │                             │
  │  └──────────────┘  └──────────────┘                            │
  └─────────────────────────────────────────────────────────────────┘
```

### Annotated Linux entry_64.S (key sections)

The following is based on Linux kernel `arch/x86/entry/entry_64.S`, simplified and annotated:

```asm
/* ============================================================
 * entry_SYSCALL_64 — Fast path for 64-bit syscalls via SYSCALL
 * The SYSCALL instruction does NOT push an interrupt frame.
 * It saves RIP in RCX, RFLAGS in R11, switches CS/SS from MSR_STAR.
 * ============================================================ */
SYM_CODE_START(entry_SYSCALL_64):
    /* CPU executed SYSCALL: CS=kernel_cs, SS=kernel_ss,
       RIP=this address, RFLAGS.IF cleared, old RIP in RCX, old RFLAGS in R11 */
    
    SWAPGS                    /* GS now points to kernel per-CPU data */
    
    /* Save user RSP in per-CPU scratch area before we can use the stack */
    movq    %rsp, PER_CPU_VAR(cpu_tss_rw + TSS_sp2)
    
    /* Load kernel stack pointer from per-CPU data */
    movq    PER_CPU_VAR(cpu_current_top_of_stack), %rsp
    
    /* Now we have a valid kernel stack. Push pt_regs frame */
    pushq   $__USER_DS                  /* SS */
    pushq   PER_CPU_VAR(cpu_tss_rw + TSS_sp2)  /* RSP (saved user RSP) */
    pushq   %r11                        /* RFLAGS (SYSCALL saved it here) */
    pushq   $__USER_CS                  /* CS */
    pushq   %rcx                        /* RIP (SYSCALL saved it here) */
    
    /* Push orig_rax (syscall number) */
    pushq   %rax
    
    /* Save all general-purpose registers */
    PUSH_AND_CLEAR_REGS     /* saves R15..RDI, clears them for security */
    
    /* Call C syscall dispatcher */
    movq    %rsp, %rdi       /* pt_regs pointer as first argument */
    call    do_syscall_64
    
    /* --- Return path --- */
ret_from_syscall:
    /* Check if we need to do work before returning */
    testl   $_TIF_WORK_SYSCALL_EXIT, TI_flags(%r12)
    jnz     syscall_return_work
    
    /* Fast return via SYSRETQ if possible */
    /* (checks for canonical RIP, no signal pending, etc.) */
    
    /* If SYSRETQ not possible, fall through to IRETQ path */
restore_regs_and_iret:
    POP_REGS                /* restore R15..RDI */
    addq    $8, %rsp        /* skip orig_rax */
    
    /* Check if returning to user space */
    testb   $3, 8(%rsp)     /* Check CS (at RSP+8 in frame) bits[1:0] */
    jz      .Lreturn_to_kernel
    
    SWAPGS                  /* restore user GS */
    
.Lreturn_to_kernel:
    IRETQ                   /* pop RIP, CS, RFLAGS, RSP, SS → user mode */
```

### The Hardware Interrupt Handler Macro (simplified)

```asm
/* ============================================================
 * asm_common_interrupt — Entry point for all hardware IRQs
 * Called with hardware interrupt frame already on stack
 * ============================================================ */
    
    /* CPU has already pushed: SS, RSP, RFLAGS, CS, RIP (and error code for some) */
    
    SWAPGS_UNSAFE_STACK     /* Must check if coming from user first */
    
    /* If CPL was 3 (user mode), SWAPGS; if CPL was 0, don't */
    testb   $3, CS_OFFSET(%rsp)   /* check saved CS bits[1:0] */
    jz      .already_kernel_gs
    SWAPGS
.already_kernel_gs:
    
    /* Save registers */
    PUSH_AND_CLEAR_REGS
    
    /* Call C interrupt handler */
    movq    %rsp, %rdi      /* struct pt_regs * */
    movq    ORIG_RAX(%rsp), %rsi  /* vector number */
    call    common_interrupt
    
    /* Restore and return */
    POP_REGS
    addq    $8, %rsp        /* skip error code / orig_rax */
    
    testb   $3, CS_OFFSET(%rsp)
    jz      .Lreturn_to_kernel_irq
    SWAPGS
    
.Lreturn_to_kernel_irq:
    IRETQ
```

---

## 14. Security Implications — Meltdown, Spectre, SWAPGS Attack

### Meltdown and KPTI (Kernel Page Table Isolation)

**Meltdown (CVE-2017-5754)** exploited the fact that kernel pages were mapped in user-space page tables (just not accessible in theory). Speculative execution could read kernel memory.

The mitigation is **KPTI**: maintain **two separate page tables**:
- **User page table**: Only maps user memory + a tiny trampoline for kernel entry
- **Kernel page table**: Maps everything

```
  KPTI and IRET:
  
  Interrupt fires (user → kernel):
  ┌─────────────────────────────────────────────────────────┐
  │ 1. Interrupt fires while in user page tables            │
  │ 2. CPU jumps to trampoline (mapped in user PT)         │
  │ 3. Trampoline: CR3 = kernel_page_table (switch PTs)    │
  │ 4. SWAPGS                                              │
  │ 5. Normal kernel entry code                            │
  └─────────────────────────────────────────────────────────┘
  
  IRETQ (kernel → user):
  ┌─────────────────────────────────────────────────────────┐
  │ 1. Normal kernel exit code                             │
  │ 2. SWAPGS                                              │
  │ 3. CR3 = user_page_table (switch to user PT)          │
  │ 4. IRETQ (jump to user RIP, restore user RSP/SS)       │
  └─────────────────────────────────────────────────────────┘
  
  The CR3 switch must happen BEFORE IRETQ, because after IRETQ
  we are in user space, and the kernel mappings must be gone.
  
  Performance impact of KPTI: CR3 writes flush TLB → costly.
  Mitigation: PCID (Process Context ID) tagging allows selective
  TLB preservation across CR3 switches.
```

### The SWAPGS Vulnerability (CVE-2019-1125)

The SWAPGS vulnerability was a speculative execution attack:

```
  ATTACK (simplified):
  
  Entry code:
      testb   $3, CS_OFFSET(%rsp)  ; test if came from user
      jz      .kernel_entry         ; if zero (kernel), skip SWAPGS
      SWAPGS                        ; else swap GS
  
  Speculative execution bug:
  CPU speculatively predicts branch "came from kernel" (wrong!)
  Speculatively executes WITHOUT SWAPGS
  GS.base still points to USER data
  Kernel code then accesses [GS + offset] speculatively
  → Can leak kernel memory if user has crafted GS to point somewhere useful
  
  Fix: Use LFENCE (Load Fence) to prevent speculation past the branch:
      testb   $3, CS_OFFSET(%rsp)
      jz      .kernel_entry
      SWAPGS
  .kernel_entry:
      LFENCE              ; serializes speculative execution
```

### Spectre v2 and IRET's Indirect Branch Target

**Spectre v2 (Branch Target Injection)** manipulates the **Return Stack Buffer (RSB)** — the CPU's predictor for `RET` instruction targets.

```
  After IRETQ returns to user space, the RSB may contain
  kernel addresses from the kernel's call stack.
  
  Attacker can use this to speculatively execute kernel code
  via mistraining the RSB.
  
  Mitigation: RSB Stuffing — before IRETQ, fill the RSB with
  benign addresses (Linux does "call; pause; lfence; add rsp,8"
  in a loop 16-32 times to overwrite RSB entries).
  
  arch/x86/entry/entry_64.S:
  FILL_RETURN_BUFFER %r11, RSB_CLEAR_LOOPS, X86_FEATURE_RSB_CTXSW
```

---

## 15. NMI, Double Fault, and Special Cases

### NMI (Non-Maskable Interrupt)

NMIs cannot be masked (disabled) by the IF flag. They require special handling:

```
  NMI Challenges:
  
  1. NMI can interrupt ANY code, including the NMI handler itself
     (in theory — "NMI nesting" in older x86)
     Modern CPUs: NMIs are automatically blocked until IRET is executed
     from the NMI handler. IRET re-enables NMI delivery.
  
  2. NMI uses IST stack (IST2 in Linux) to ensure valid stack
     even if regular kernel stack is corrupted/overflowed.
  
  3. IRET within an NMI handler must be on a specially crafted
     stack frame, because if IRET was used in the normal path,
     it would re-enable NMIs before all registers were restored.
     Linux has a complex NMI handler that avoids this race.
  
  Linux NMI return sequence:
      /* Cannot use normal IRETQ here — would re-enable NMI too early */
      /* Instead, use "fake" IRETQ via a constructed stack frame */
      /* that points to a fixup routine */
```

### Double Fault (#DF)

A Double Fault occurs when a fault happens **while trying to handle another fault**:

```
  Page Fault during Page Fault handler:
  → CPU tries to invoke #DF handler (vector 8)
  → #DF always has an error code of 0
  → #DF uses IST1 (dedicated stack) — ALWAYS
  
  Why IST for #DF?
  Most common cause of #DF: kernel stack overflow.
  If kernel RSP points to unmapped memory, any stack access causes #PF.
  Trying to push the #PF frame causes another #PF → #DF.
  If #DF handler used the same (overflowed) stack → triple fault → CPU reset.
  IST provides a completely separate stack pointer from TSS.IST1.
  
  After handling #DF, IRETQ returns from the #DF handler.
  In practice, Linux's #DF handler panics (kills the system)
  because double fault means the kernel state is unrecoverable.
```

### The NT (Nested Task) Flag — 32-bit IRET Special Case

In 32-bit protected mode, if the EFLAGS.NT (Nested Task) bit is **1** when IRET executes, the CPU performs a **task switch** rather than a normal interrupt return. This is the hardware task-switching mechanism, unused by Linux but important to know:

```
  32-bit IRET with NT=1:
  → Read back-link selector from current TSS
  → Load entire CPU state from the linked TSS
  → Clear NT flag in loaded EFLAGS
  
  Linux does NOT use hardware task switching (NT is always 0).
  Linux manages task switching in software via context_switch().
```

---

## 16. C Implementation — Bare-Metal Interrupt Handler

The following is a **production-quality** implementation of interrupt handling using IRET, suitable for a bare-metal kernel or minimal OS.

### Header File — Interrupt Types and Structures

```c
/* interrupt.h — x86-64 interrupt handling infrastructure
 *
 * Production-grade bare-metal interrupt handler
 * Targets: x86-64, no OS dependencies
 */

#ifndef INTERRUPT_H
#define INTERRUPT_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

/* ============================================================
 * Constants
 * ============================================================ */

#define IDT_ENTRY_COUNT         256U
#define IDT_GATE_TYPE_INTERRUPT 0x8EU  /* P=1, DPL=0, Type=0xE (64-bit interrupt gate) */
#define IDT_GATE_TYPE_TRAP      0x8FU  /* P=1, DPL=0, Type=0xF (64-bit trap gate) */
#define IDT_GATE_TYPE_USER_INT  0xEEU  /* P=1, DPL=3, Type=0xE (callable from Ring 3) */

/* Segment selectors (must match your GDT layout) */
#define KERNEL_CODE_SELECTOR    0x08U  /* Ring 0 code segment */
#define KERNEL_DATA_SELECTOR    0x10U  /* Ring 0 data segment */
#define USER_CODE_SELECTOR      0x18U  /* Ring 3 code segment */
#define USER_DATA_SELECTOR      0x20U  /* Ring 3 data segment */

/* IST (Interrupt Stack Table) indices — 0 means use RSP0 from TSS */
#define IST_NONE        0U
#define IST_NMI         1U  /* Dedicated NMI stack */
#define IST_DOUBLE_FAULT 2U /* Dedicated #DF stack */
#define IST_MACHINE_CHECK 3U

/* Vector numbers for CPU exceptions */
#define VECTOR_DIVIDE_ERROR         0U
#define VECTOR_DEBUG                1U
#define VECTOR_NMI                  2U
#define VECTOR_BREAKPOINT           3U
#define VECTOR_OVERFLOW             4U
#define VECTOR_BOUND_RANGE          5U
#define VECTOR_INVALID_OPCODE       6U
#define VECTOR_DEVICE_NOT_AVAIL     7U
#define VECTOR_DOUBLE_FAULT         8U
#define VECTOR_INVALID_TSS         10U
#define VECTOR_SEGMENT_NOT_PRESENT 11U
#define VECTOR_STACK_FAULT         12U
#define VECTOR_GENERAL_PROTECTION  13U
#define VECTOR_PAGE_FAULT          14U
#define VECTOR_FPU_ERROR           16U
#define VECTOR_ALIGNMENT_CHECK     17U
#define VECTOR_MACHINE_CHECK       18U
#define VECTOR_SIMD_FP             19U

/* First vector available for hardware IRQs */
#define VECTOR_IRQ_BASE            32U

/* ============================================================
 * Data Structures — all must be packed for correct memory layout
 * ============================================================ */

/*
 * IDT Gate Descriptor (64-bit format — 16 bytes)
 *
 * Memory layout (little-endian):
 * Byte  0-1  : offset[15:0]
 * Byte  2-3  : segment selector
 * Byte  4    : IST (bits[2:0]) + reserved zeros
 * Byte  5    : type_attr (P | DPL | 0 | type[3:0])
 * Byte  6-7  : offset[31:16]
 * Byte  8-11 : offset[63:32]
 * Byte 12-15 : reserved (must be zero)
 */
typedef struct __attribute__((packed)) {
    uint16_t offset_low;        /* handler address bits [15:0]  */
    uint16_t selector;          /* code segment selector        */
    uint8_t  ist;               /* bits[2:0] = IST index        */
    uint8_t  type_attr;         /* gate type + DPL + Present    */
    uint16_t offset_mid;        /* handler address bits [31:16] */
    uint32_t offset_high;       /* handler address bits [63:32] */
    uint32_t reserved;          /* must be zero                 */
} idt_entry_t;

/* Compile-time size verification */
_Static_assert(sizeof(idt_entry_t) == 16, "IDT entry must be 16 bytes");

/*
 * IDTR — loaded via LIDT instruction
 */
typedef struct __attribute__((packed)) {
    uint16_t limit;  /* size of IDT in bytes - 1 */
    uint64_t base;   /* linear address of IDT    */
} idtr_t;

_Static_assert(sizeof(idtr_t) == 10, "IDTR must be 10 bytes");

/*
 * Interrupt Stack Frame (as pushed by CPU on interrupt in 64-bit mode)
 *
 * These fields are at the TOP of the stack when the handler runs.
 * The CPU pushes them automatically; the handler reads them.
 * IRETQ will pop exactly these fields (in reverse order).
 *
 * Note: This struct represents the frame AFTER error code removal.
 * For exceptions that push error codes, handlers must remove them first.
 */
typedef struct __attribute__((packed)) {
    uint64_t rip;     /* Instruction pointer to return to          */
    uint64_t cs;      /* Code segment selector (CPL in bits[1:0])  */
    uint64_t rflags;  /* CPU flags at time of interrupt            */
    uint64_t rsp;     /* Stack pointer to return to                */
    uint64_t ss;      /* Stack segment selector                    */
} interrupt_frame_t;

_Static_assert(sizeof(interrupt_frame_t) == 40, "Interrupt frame must be 40 bytes");

/*
 * Full register context saved by software (Linux pt_regs equivalent)
 * Handlers receive a pointer to this when all regs are saved.
 */
typedef struct __attribute__((packed)) {
    /* Software-saved general purpose registers (saved by our stub) */
    uint64_t r15;
    uint64_t r14;
    uint64_t r13;
    uint64_t r12;
    uint64_t r11;
    uint64_t r10;
    uint64_t r9;
    uint64_t r8;
    uint64_t rbp;
    uint64_t rdi;
    uint64_t rsi;
    uint64_t rdx;
    uint64_t rcx;
    uint64_t rbx;
    uint64_t rax;
    /* Metadata */
    uint64_t error_code;  /* error code (0 if not applicable) */
    uint64_t vector;      /* interrupt vector number */
    /* Hardware-pushed frame (CPU pushed these, IRETQ reads them) */
    interrupt_frame_t hw_frame;
} full_regs_t;

/* Handler function pointer type */
typedef void (*interrupt_handler_fn)(full_regs_t *regs);

/* ============================================================
 * TSS (Task State Segment) — 64-bit format
 * ============================================================ */

typedef struct __attribute__((packed)) {
    uint32_t reserved0;
    uint64_t rsp0;          /* Ring 0 stack pointer */
    uint64_t rsp1;          /* Ring 1 stack pointer */
    uint64_t rsp2;          /* Ring 2 stack pointer */
    uint64_t reserved1;
    uint64_t ist[7];        /* IST1–IST7 stack pointers */
    uint64_t reserved2;
    uint16_t reserved3;
    uint16_t iopb_offset;   /* I/O permission bitmap offset */
} tss_t;

_Static_assert(sizeof(tss_t) == 104, "TSS must be 104 bytes");

/* ============================================================
 * Public API
 * ============================================================ */

/* Initialize the IDT with default handlers */
void idt_init(void);

/* Register a handler for a specific interrupt vector */
bool idt_register_handler(
    uint8_t vector,
    interrupt_handler_fn handler,
    uint8_t ist_index,
    bool is_trap_gate,
    uint8_t dpl
);

/* Load the IDT into the CPU (executes LIDT) */
void idt_load(void);

/* Set the kernel stack for Ring 0 in the TSS */
void tss_set_kernel_stack(uint64_t stack_top);

/* Low-level: enable/disable hardware interrupts */
static inline void interrupts_enable(void)  { __asm__ volatile("sti" ::: "memory"); }
static inline void interrupts_disable(void) { __asm__ volatile("cli" ::: "memory"); }
static inline bool interrupts_enabled(void)
{
    uint64_t flags;
    __asm__ volatile("pushfq; popq %0" : "=r"(flags) :: "memory");
    return (flags & (1UL << 9)) != 0;  /* IF flag is bit 9 */
}

/* Save and restore interrupt state (for critical sections) */
static inline uint64_t interrupts_save_and_disable(void)
{
    uint64_t flags;
    __asm__ volatile("pushfq; popq %0; cli" : "=r"(flags) :: "memory");
    return flags;
}

static inline void interrupts_restore(uint64_t flags)
{
    __asm__ volatile("pushq %0; popfq" :: "r"(flags) : "memory", "cc");
}

#endif /* INTERRUPT_H */
```

### Implementation File — IDT and Handler Infrastructure

```c
/* interrupt.c — IDT management and interrupt dispatch
 *
 * This implements the infrastructure that makes IRET work correctly.
 */

#include "interrupt.h"
#include <string.h>  /* memset */

/* ============================================================
 * Static storage
 * ============================================================ */

/* The IDT itself — aligned to 16 bytes for performance */
static idt_entry_t idt_table[IDT_ENTRY_COUNT] __attribute__((aligned(16)));

/* Handler function pointer table */
static interrupt_handler_fn handler_table[IDT_ENTRY_COUNT];

/* TSS — must be in accessible memory (not paged out) */
static tss_t kernel_tss __attribute__((aligned(16)));

/* IST stacks — dedicated stacks for critical exceptions */
#define IST_STACK_SIZE  (4096U * 2U)  /* 8 KiB per IST stack */
static uint8_t ist_stack_nmi[IST_STACK_SIZE]    __attribute__((aligned(16)));
static uint8_t ist_stack_df[IST_STACK_SIZE]     __attribute__((aligned(16)));
static uint8_t ist_stack_mc[IST_STACK_SIZE]     __attribute__((aligned(16)));

/* ============================================================
 * Low-level IDT entry construction
 * ============================================================ */

/*
 * idt_set_entry — encode a 64-bit interrupt gate descriptor
 *
 * @entry:     pointer to IDT entry to fill
 * @handler:   64-bit address of the assembly stub (NOT the C handler)
 * @selector:  code segment selector (must be kernel CS for Ring 0 handlers)
 * @ist:       IST index (0 = use RSP0 from TSS)
 * @type_attr: gate type + DPL + Present bits
 */
static void idt_set_entry(
    idt_entry_t *restrict entry,
    uint64_t handler_addr,
    uint16_t selector,
    uint8_t  ist,
    uint8_t  type_attr
) {
    entry->offset_low  = (uint16_t)(handler_addr & 0xFFFFU);
    entry->selector    = selector;
    entry->ist         = ist & 0x07U;  /* only 3 bits */
    entry->type_attr   = type_attr;
    entry->offset_mid  = (uint16_t)((handler_addr >> 16) & 0xFFFFU);
    entry->offset_high = (uint32_t)((handler_addr >> 32) & 0xFFFFFFFFU);
    entry->reserved    = 0;
}

/* ============================================================
 * Assembly stubs — these are the actual IDT handler targets.
 * They save all registers, call the C handler, then IRETQ.
 *
 * In real production code these would be in a .S file.
 * Here we declare them as extern and show the full assembly below.
 * ============================================================ */

/* Declare all exception stubs as external symbols (defined in .S file) */
extern void isr_stub_0(void);   /* #DE */
extern void isr_stub_1(void);   /* #DB */
extern void isr_stub_2(void);   /* NMI */
extern void isr_stub_3(void);   /* #BP */
/* ... etc for all 256 vectors */

/*
 * The assembly stubs look like this (for an exception WITHOUT error code):
 *
 * isr_stub_N:
 *     pushq   $0              ; fake error code (for uniformity)
 *     pushq   $N              ; vector number
 *     ; save all GP registers
 *     pushq   %rax
 *     pushq   %rbx
 *     pushq   %rcx
 *     pushq   %rdx
 *     pushq   %rsi
 *     pushq   %rdi
 *     pushq   %rbp
 *     pushq   %r8
 *     pushq   %r9
 *     pushq   %r10
 *     pushq   %r11
 *     pushq   %r12
 *     pushq   %r13
 *     pushq   %r14
 *     pushq   %r15
 *     ; RSP now points to full_regs_t
 *     movq    %rsp, %rdi      ; first argument = &full_regs
 *     call    interrupt_dispatch_c
 *     ; restore all GP registers
 *     popq    %r15
 *     popq    %r14
 *     popq    %r13
 *     popq    %r12
 *     popq    %r11
 *     popq    %r10
 *     popq    %r9
 *     popq    %r8
 *     popq    %rbp
 *     popq    %rdi
 *     popq    %rsi
 *     popq    %rdx
 *     popq    %rcx
 *     popq    %rbx
 *     popq    %rax
 *     addq    $16, %rsp       ; skip error_code and vector
 *     iretq                   ; ← THE IRET INSTRUCTION
 *
 * For exceptions WITH error code (e.g., #PF, #GP):
 *     ; CPU already pushed error code
 *     ; just push vector number, then save regs
 *     pushq   $14             ; vector (#PF)
 *     pushq   %rax
 *     ... (same as above)
 */

/* ============================================================
 * C-level interrupt dispatcher
 * Called from assembly stubs with full_regs_t* as argument
 * ============================================================ */

void interrupt_dispatch_c(full_regs_t *regs)
{
    uint64_t vector = regs->vector;

    if (vector >= IDT_ENTRY_COUNT) {
        /* This should never happen — panic or halt */
        __asm__ volatile("hlt");
        return;
    }

    if (handler_table[vector] != NULL) {
        handler_table[vector](regs);
    } else {
        /*
         * Unhandled interrupt — in production, log and decide:
         * - For exceptions: halt (unrecoverable kernel error)
         * - For hardware IRQs: send EOI to APIC and return
         */
        if (vector < VECTOR_IRQ_BASE) {
            /* CPU exception with no handler — halt */
            __asm__ volatile("cli; hlt");
        }
        /* For IRQs, just acknowledge and return (handler missing = benign) */
    }
}

/* ============================================================
 * Default exception handlers
 * ============================================================ */

static void handle_page_fault(full_regs_t *regs)
{
    /* Read CR2 — contains the faulting virtual address */
    uint64_t fault_address;
    __asm__ volatile("movq %%cr2, %0" : "=r"(fault_address));

    uint64_t error_code = regs->error_code;
    bool present    = (error_code & (1U << 0)) != 0;  /* page present? */
    bool write      = (error_code & (1U << 1)) != 0;  /* write access? */
    bool user_mode  = (error_code & (1U << 2)) != 0;  /* from user? */
    bool reserved   = (error_code & (1U << 3)) != 0;  /* reserved bit set? */
    bool exec       = (error_code & (1U << 4)) != 0;  /* instruction fetch? */

    (void)present; (void)write; (void)user_mode;
    (void)reserved; (void)exec; (void)fault_address;

    /* In a real OS: handle the page fault (demand paging, COW, etc.)
     * If unresolvable: send SIGSEGV to process (user mode)
     *                  or kernel panic (kernel mode)
     *
     * If resolved: simply return — IRETQ will restart the faulting instruction
     * (because #PF is a FAULT, not a trap — RIP in frame = faulting instruction)
     */
}

static void handle_general_protection(full_regs_t *regs)
{
    (void)regs;
    /* #GP is almost always unrecoverable in kernel context */
    /* In user context: send SIGSEGV */
    __asm__ volatile("cli; hlt");
}

static void handle_breakpoint(full_regs_t *regs)
{
    (void)regs;
    /* #BP is a TRAP — RIP in frame = instruction AFTER INT3
     * Debugger decrements RIP by 1 to re-execute the breakpoint if needed
     * In a real OS: notify the debugger (ptrace) or panic
     */
}

/* ============================================================
 * IDT Initialization
 * ============================================================ */

void idt_init(void)
{
    /* Clear the IDT and handler table */
    memset(idt_table, 0, sizeof(idt_table));
    memset(handler_table, 0, sizeof(handler_table));

    /* Set up IST stacks in TSS */
    kernel_tss.ist[IST_NMI - 1]          = (uint64_t)(ist_stack_nmi + IST_STACK_SIZE);
    kernel_tss.ist[IST_DOUBLE_FAULT - 1] = (uint64_t)(ist_stack_df  + IST_STACK_SIZE);
    kernel_tss.ist[IST_MACHINE_CHECK - 1]= (uint64_t)(ist_stack_mc  + IST_STACK_SIZE);

    /*
     * Register default exception handlers.
     * In a real system, all 256 stubs would be registered.
     * We show the key ones here.
     */
    idt_register_handler(VECTOR_PAGE_FAULT,       handle_page_fault,        IST_NONE,        false, 0);
    idt_register_handler(VECTOR_GENERAL_PROTECTION, handle_general_protection, IST_NONE,      false, 0);
    idt_register_handler(VECTOR_BREAKPOINT,        handle_breakpoint,         IST_NONE,        true,  3); /* DPL=3: user can use INT3 */
    idt_register_handler(VECTOR_DOUBLE_FAULT,      NULL /* special asm handler */, IST_DOUBLE_FAULT, false, 0);
    idt_register_handler(VECTOR_NMI,               NULL /* special asm handler */, IST_NMI,         false, 0);
}

bool idt_register_handler(
    uint8_t vector,
    interrupt_handler_fn handler,
    uint8_t ist_index,
    bool is_trap_gate,
    uint8_t dpl
) {
    if (ist_index > 7U) {
        return false;  /* Invalid IST index */
    }

    /* Store C handler */
    handler_table[vector] = handler;

    /*
     * Compute type_attr byte:
     * Bit 7:    P (Present) = 1
     * Bits 6-5: DPL (0 = kernel only, 3 = user callable)
     * Bit 4:    0 (always)
     * Bits 3-0: Type (0xE = interrupt gate, 0xF = trap gate)
     */
    uint8_t gate_type = is_trap_gate ? 0x0FU : 0x0EU;
    uint8_t type_attr = (uint8_t)(0x80U | ((dpl & 0x03U) << 5U) | gate_type);

    /*
     * In a real system, isr_stub_N would be the assembly stub for vector N.
     * Here we use a placeholder — real code would have a table of stub pointers.
     */
    uint64_t stub_address = 0; /* = (uint64_t)isr_stub_table[vector]; */

    idt_set_entry(
        &idt_table[vector],
        stub_address,
        KERNEL_CODE_SELECTOR,
        ist_index,
        type_attr
    );

    return true;
}

void idt_load(void)
{
    idtr_t idtr = {
        .limit = (uint16_t)(sizeof(idt_table) - 1U),
        .base  = (uint64_t)idt_table,
    };

    __asm__ volatile("lidt %0" :: "m"(idtr) : "memory");
}

void tss_set_kernel_stack(uint64_t stack_top)
{
    kernel_tss.rsp0 = stack_top;
}
```

### Assembly Stub File — The Actual IRETQ Usage

```asm
/* interrupt_stubs.S — Assembly stubs for interrupt handling
 *
 * Each stub:
 *   1. Handles error code (push 0 if none)
 *   2. Pushes vector number
 *   3. Saves all GP registers
 *   4. Calls C dispatcher (interrupt_dispatch_c)
 *   5. Restores all GP registers
 *   6. Executes IRETQ
 *
 * Assembler: GNU AS (AT&T syntax)
 * Architecture: x86-64
 */

.section .text
.global isr_common_stub

/* ============================================================
 * Macro: DEFINE_ISR_NO_ERR
 * For exceptions that do NOT push an error code.
 * We push a fake 0 for uniform stack layout.
 * ============================================================ */
.macro DEFINE_ISR_NO_ERR vector
.global isr_stub_\vector
isr_stub_\vector:
    pushq   $0                  /* fake error code */
    pushq   $\vector            /* vector number */
    jmp     isr_common_stub
.endm

/* ============================================================
 * Macro: DEFINE_ISR_WITH_ERR
 * For exceptions that DO push an error code (CPU pushes it before RIP).
 * Stack: [error_code, RIP, CS, RFLAGS, RSP, SS] from CPU.
 * We just need to push the vector number.
 * ============================================================ */
.macro DEFINE_ISR_WITH_ERR vector
.global isr_stub_\vector
isr_stub_\vector:
    /* Error code is already on stack (below RIP in memory, above in stack) */
    /* Wait — in 64-bit mode the frame is: RIP, CS, RFLAGS, RSP, SS       */
    /* Error code is pushed BEFORE RIP by the CPU, so it's at the top      */
    pushq   $\vector
    jmp     isr_common_stub
.endm

/* Define exception stubs */
DEFINE_ISR_NO_ERR   0   /* #DE Divide Error */
DEFINE_ISR_NO_ERR   1   /* #DB Debug */
DEFINE_ISR_NO_ERR   2   /* NMI */
DEFINE_ISR_NO_ERR   3   /* #BP Breakpoint */
DEFINE_ISR_NO_ERR   4   /* #OF Overflow */
DEFINE_ISR_NO_ERR   5   /* #BR Bound Range */
DEFINE_ISR_NO_ERR   6   /* #UD Invalid Opcode */
DEFINE_ISR_NO_ERR   7   /* #NM Device Not Available */
DEFINE_ISR_WITH_ERR 8   /* #DF Double Fault (error code = 0, but CPU pushes it) */
DEFINE_ISR_WITH_ERR 10  /* #TS Invalid TSS */
DEFINE_ISR_WITH_ERR 11  /* #NP Segment Not Present */
DEFINE_ISR_WITH_ERR 12  /* #SS Stack Fault */
DEFINE_ISR_WITH_ERR 13  /* #GP General Protection */
DEFINE_ISR_WITH_ERR 14  /* #PF Page Fault */
DEFINE_ISR_NO_ERR   16  /* #MF FPU Error */
DEFINE_ISR_WITH_ERR 17  /* #AC Alignment Check */
DEFINE_ISR_NO_ERR   18  /* #MC Machine Check */
DEFINE_ISR_NO_ERR   19  /* #XM SIMD FP */

/* Hardware IRQ stubs (32-255) */
DEFINE_ISR_NO_ERR   32  /* IRQ0 — Timer */
DEFINE_ISR_NO_ERR   33  /* IRQ1 — Keyboard */
/* ... etc */

/* ============================================================
 * isr_common_stub — Shared register save/restore and dispatch
 *
 * On entry, stack looks like:
 *   [RSP+0]  vector number     (we pushed this)
 *   [RSP+8]  error code        (we or CPU pushed this)
 *   [RSP+16] RIP               (CPU pushed)
 *   [RSP+24] CS                (CPU pushed)
 *   [RSP+32] RFLAGS            (CPU pushed)
 *   [RSP+40] RSP (user)        (CPU pushed — always in 64-bit mode)
 *   [RSP+48] SS  (user)        (CPU pushed — always in 64-bit mode)
 *
 * We push GP registers to build full_regs_t.
 * ============================================================ */
isr_common_stub:
    /* Save general-purpose registers in the order matching full_regs_t */
    /* Remember: stack grows DOWN, we push in REVERSE order of struct    */
    pushq   %rax
    pushq   %rbx
    pushq   %rcx
    pushq   %rdx
    pushq   %rsi
    pushq   %rdi
    pushq   %rbp
    pushq   %r8
    pushq   %r9
    pushq   %r10
    pushq   %r11
    pushq   %r12
    pushq   %r13
    pushq   %r14
    pushq   %r15

    /*
     * RSP now points to the bottom of full_regs_t.
     * Pass it as the first argument (RDI = System V AMD64 ABI arg1).
     * The C function signature is: void interrupt_dispatch_c(full_regs_t *regs)
     */
    movq    %rsp, %rdi
    
    /*
     * Align stack to 16 bytes before the call.
     * The System V ABI requires 16-byte stack alignment at CALL sites.
     * Before CALL, RSP must be 16-byte aligned (call pushes 8-byte return addr).
     * andq $-16 rounds down to 16-byte boundary.
     */
    andq    $-16, %rsp
    
    call    interrupt_dispatch_c
    
    /* Restore RSP to where our full_regs_t is */
    /* We need the saved %rsp value — tricky since we aligned it */
    /* Solution: save RSP before aligning, use RBP or a scratch area */
    /* Better approach: don't align (many kernels handle this differently) */
    /* Here we use a fixed offset approach, assuming alignment adjustment */
    
    /* Restore general-purpose registers in reverse order */
    popq    %r15
    popq    %r14
    popq    %r13
    popq    %r12
    popq    %r11
    popq    %r10
    popq    %r9
    popq    %r8
    popq    %rbp
    popq    %rdi
    popq    %rsi
    popq    %rdx
    popq    %rcx
    popq    %rbx
    popq    %rax

    /*
     * Remove the vector number and error code from the stack.
     * These were pushed by our stub code and are NOT part of the
     * CPU's interrupt frame. We must remove them before IRETQ.
     */
    addq    $16, %rsp   /* skip error_code (8 bytes) + vector (8 bytes) */

    /*
     * ================================================================
     * THE IRETQ INSTRUCTION
     * ================================================================
     * At this point, the stack contains exactly:
     *   [RSP+0]  RIP     (where to return)
     *   [RSP+8]  CS      (code segment, CPL in bits[1:0])
     *   [RSP+16] RFLAGS  (flags to restore, including IF)
     *   [RSP+24] RSP     (stack pointer to restore)
     *   [RSP+32] SS      (stack segment to restore)
     *
     * IRETQ will:
     * 1. Pop RIP  → CPU jumps here
     * 2. Pop CS   → determines new privilege level
     * 3. Pop RFLAGS → restores all flags including IF (re-enables interrupts)
     * 4. Pop RSP  → restores stack (user's stack if privilege changed)
     * 5. Pop SS   → restores stack segment
     *
     * If CS indicates Ring 3: CPU switches to user mode.
     * If CS indicates Ring 0: CPU stays in kernel mode.
     * ================================================================
     */
    iretq
```

---

## 17. Rust Implementation — Type-Safe Interrupt Handling

Rust, especially with the `x86_64` crate, provides a type-safe and zero-cost abstraction over interrupt handling. The `x86_64` crate is used by projects like the blog_os (OSDev tutorial) and real research/hobby OS kernels.

### Cargo.toml Dependencies

```toml
[package]
name    = "interrupt-handler"
version = "0.1.0"
edition = "2021"

[dependencies]
x86_64 = "0.15"

[profile.dev]
panic = "abort"   # No unwinding in kernel code

[profile.release]
panic = "abort"
opt-level = "s"   # Size optimization for kernel
lto = true
codegen-units = 1
```

### Interrupt Types and IDT Definition

```rust
// src/interrupts.rs — Type-safe interrupt handling infrastructure
//
// Uses x86_64 crate for hardware abstractions.
// No std — this is kernel/bare-metal code.

#![no_std]

use x86_64::structures::idt::{
    InterruptDescriptorTable,
    InterruptStackFrame,    // The hardware-pushed frame (RIP, CS, RFLAGS, RSP, SS)
    PageFaultErrorCode,     // Typed error code for #PF
};
use x86_64::structures::tss::TaskStateSegment;
use x86_64::addr::VirtAddr;
use x86_64::registers::control::Cr2;  // Contains page fault address

// ============================================================
// Constants — Named, typed, explicit
// ============================================================

/// Index into the Interrupt Stack Table for the double fault handler.
/// Range: 0–6 (IST1–IST7, but zero-indexed in the x86_64 crate).
pub const IST_INDEX_DOUBLE_FAULT: u16 = 0;  // IST1 (index 0 in array)
pub const IST_INDEX_NMI:          u16 = 1;  // IST2
pub const IST_INDEX_MACHINE_CHECK:u16 = 2;  // IST3

/// Size of dedicated IST stacks (bytes).
const IST_STACK_SIZE: usize = 4096 * 4;  // 16 KiB

// ============================================================
// Static storage — lazy initialization with spin lock
// ============================================================

use spin::Lazy;

/// Global IDT — initialized exactly once.
///
/// The `Lazy` wrapper ensures thread-safe one-time initialization.
/// `InterruptDescriptorTable` is the x86_64 crate's type for the full 256-entry IDT.
static IDT: Lazy<InterruptDescriptorTable> = Lazy::new(|| {
    let mut idt = InterruptDescriptorTable::new();

    // Register exception handlers.
    // The x86_64 crate uses type-safe handler signatures:
    //   extern "x86-interrupt" fn handler(frame: InterruptStackFrame)
    // This calling convention is understood by rustc and ensures correct
    // register saving and IRETQ emission at the end of the handler.

    idt.divide_error.set_handler_fn(handle_divide_error);
    idt.breakpoint.set_handler_fn(handle_breakpoint);
    idt.invalid_opcode.set_handler_fn(handle_invalid_opcode);
    idt.page_fault.set_handler_fn(handle_page_fault);
    idt.general_protection_fault.set_handler_fn(handle_general_protection);

    // Exceptions that need their own IST stack:
    // set_handler_fn returns a configuration builder. We must use unsafe
    // because we're specifying a raw IST index — incorrect values would
    // cause the CPU to use a garbage stack pointer from the TSS.
    unsafe {
        idt.double_fault
            .set_handler_fn(handle_double_fault)
            .set_stack_index(IST_INDEX_DOUBLE_FAULT);

        idt.non_maskable_interrupt
            .set_handler_fn(handle_nmi)
            .set_stack_index(IST_INDEX_NMI);

        idt.machine_check
            .set_handler_fn(handle_machine_check)
            .set_stack_index(IST_INDEX_MACHINE_CHECK);
    }

    // Hardware IRQs (vectors 32+)
    // In a real OS these would go through APIC/PIC remapping.
    idt[32].set_handler_fn(handle_timer_irq);
    idt[33].set_handler_fn(handle_keyboard_irq);

    idt
});

/// Load the IDT into the CPU by executing the LIDT instruction.
///
/// # Safety
/// - Must be called only once during kernel initialization.
/// - The IDT must remain valid for the lifetime of the system.
/// - The TSS must be loaded (via LTR) before this if using IST.
pub fn idt_init() {
    IDT.load();
    // After this, IDT is registered with the CPU.
    // On any interrupt, the CPU will jump to our handlers.
}

// ============================================================
// TSS Initialization
// ============================================================

/// IST stacks — must be static and never moved.
static mut IST_STACK_DOUBLE_FAULT: [u8; IST_STACK_SIZE] = [0u8; IST_STACK_SIZE];
static mut IST_STACK_NMI:          [u8; IST_STACK_SIZE] = [0u8; IST_STACK_SIZE];
static mut IST_STACK_MACHINE_CHECK:[u8; IST_STACK_SIZE] = [0u8; IST_STACK_SIZE];

/// Global TSS.
static TSS: Lazy<TaskStateSegment> = Lazy::new(|| {
    let mut tss = TaskStateSegment::new();

    // Set up IST stacks.
    // Stack grows DOWN, so we point to the TOP of the allocated region.
    // SAFETY: We only read the address of these statics; no data races
    // occur because IST stacks are only used by the CPU hardware.
    tss.interrupt_stack_table[IST_INDEX_DOUBLE_FAULT as usize] = {
        let stack_start = VirtAddr::from_ptr(unsafe { &IST_STACK_DOUBLE_FAULT });
        stack_start + IST_STACK_SIZE as u64  // top of stack
    };

    tss.interrupt_stack_table[IST_INDEX_NMI as usize] = {
        let stack_start = VirtAddr::from_ptr(unsafe { &IST_STACK_NMI });
        stack_start + IST_STACK_SIZE as u64
    };

    tss.interrupt_stack_table[IST_INDEX_MACHINE_CHECK as usize] = {
        let stack_start = VirtAddr::from_ptr(unsafe { &IST_STACK_MACHINE_CHECK });
        stack_start + IST_STACK_SIZE as u64
    };

    // rsp[0] will be set dynamically when a process is scheduled.
    // For now, we leave it as 0 (will be set by tss_set_kernel_stack).

    tss
});

/// Update the kernel stack pointer in the TSS (called on context switch).
///
/// # Safety
/// - Must be called with interrupts disabled to avoid race conditions.
/// - stack_top must point to valid, writable, kernel memory.
pub unsafe fn tss_set_kernel_stack(stack_top: VirtAddr) {
    // SAFETY: We have exclusive access (caller ensures interrupts disabled)
    let tss = &TSS as *const _ as *mut TaskStateSegment;
    (*tss).privilege_stack_table[0] = stack_top;
}

// ============================================================
// Interrupt Handler Functions
//
// The "x86-interrupt" calling convention is the key abstraction:
// - Rustc/LLVM knows to save all caller-saved registers
// - The function ends with IRETQ instead of RET
// - The InterruptStackFrame argument is a pointer into the CPU-pushed frame
// ============================================================

/// Handle #DE — Divide by zero error.
///
/// Type: Fault. RIP points to the DIV/IDIV instruction.
/// No error code.
extern "x86-interrupt" fn handle_divide_error(frame: InterruptStackFrame) {
    // In a real OS: send SIGFPE to the process if in user mode,
    // or kernel panic if in kernel mode.
    panic!(
        "EXCEPTION: Divide Error\n\
         RIP:    {:#018x}\n\
         CS:     {:#06x}\n\
         RFLAGS: {:#018x}\n\
         RSP:    {:#018x}\n\
         SS:     {:#06x}",
        frame.instruction_pointer.as_u64(),
        frame.code_segment.0,
        frame.cpu_flags,
        frame.stack_pointer.as_u64(),
        frame.stack_segment.0,
    );
    // IRETQ emitted here by "x86-interrupt" convention — but panic! diverges,
    // so IRETQ is never reached. The handler diverges (never returns).
}

/// Handle #BP — Breakpoint (INT3 instruction).
///
/// Type: Trap. RIP points to the instruction AFTER INT3.
/// No error code.
/// DPL=3 in IDT gate, so user code can trigger this.
extern "x86-interrupt" fn handle_breakpoint(frame: InterruptStackFrame) {
    // For debugging: record that we hit a breakpoint.
    // RIP already points to the next instruction (Trap, not Fault).
    // A debugger would decrement RIP by 1 to re-execute INT3 if needed.
    //
    // In production: notify ptrace subsystem, possibly sleep the process.
    let _ = frame;
    // Returns normally → IRETQ executed by "x86-interrupt" convention.
    // CPU continues at frame.instruction_pointer (which is AFTER the INT3).
}

/// Handle #UD — Invalid Opcode.
extern "x86-interrupt" fn handle_invalid_opcode(frame: InterruptStackFrame) {
    panic!(
        "EXCEPTION: Invalid Opcode at {:#018x}",
        frame.instruction_pointer.as_u64()
    );
}

/// Handle #PF — Page Fault.
///
/// Type: Fault. RIP points to the faulting instruction (will restart on return).
/// Error code describes the fault type (see PageFaultErrorCode).
/// CR2 register contains the faulting virtual address.
extern "x86-interrupt" fn handle_page_fault(
    frame: InterruptStackFrame,
    error_code: PageFaultErrorCode,
) {
    // Read CR2 — the faulting address. MUST read before any memory operations
    // that might change CR2 (e.g., another page fault in the handler itself).
    let fault_address = Cr2::read();

    // Decode the error code bits (x86_64 crate provides typed flags):
    let _protection_violation = error_code.contains(PageFaultErrorCode::PROTECTION_VIOLATION);
    let _caused_by_write      = error_code.contains(PageFaultErrorCode::CAUSED_BY_WRITE);
    let _from_user_mode       = error_code.contains(PageFaultErrorCode::USER_MODE);
    let _malformed_table      = error_code.contains(PageFaultErrorCode::MALFORMED_TABLE);
    let _instruction_fetch    = error_code.contains(PageFaultErrorCode::INSTRUCTION_FETCH);

    // In a real OS:
    // 1. Find the VMA (Virtual Memory Area) for fault_address
    // 2. If found and access allowed: allocate/map the page → return (IRETQ restarts fault)
    // 3. If not found or access denied from user: send SIGSEGV
    // 4. If kernel mode access violation: kernel panic

    // For this example: just panic
    panic!(
        "EXCEPTION: Page Fault\n\
         Faulting Address: {:?}\n\
         Error Code: {:?}\n\
         RIP: {:#018x}",
        fault_address,
        error_code,
        frame.instruction_pointer.as_u64(),
    );
    // If we returned normally here, IRETQ would restart the faulting instruction.
}

/// Handle #GP — General Protection Fault.
extern "x86-interrupt" fn handle_general_protection(
    frame: InterruptStackFrame,
    error_code: u64,  // Segment selector index (if applicable), or 0
) {
    panic!(
        "EXCEPTION: General Protection Fault\n\
         Error Code: {:#018x}\n\
         RIP: {:#018x}",
        error_code,
        frame.instruction_pointer.as_u64(),
    );
}

/// Handle #DF — Double Fault.
///
/// This runs on IST1 — a completely separate, dedicated stack.
/// The error code is ALWAYS 0 (defined by Intel spec).
/// This handler MUST NOT return — double fault means kernel state is corrupt.
///
/// The "!" return type means this function diverges (never returns).
/// Therefore, IRETQ is never emitted. This is correct for #DF.
extern "x86-interrupt" fn handle_double_fault(
    frame: InterruptStackFrame,
    _error_code: u64,  // Always 0 for #DF
) -> ! {
    panic!(
        "EXCEPTION: Double Fault (KERNEL IS DEAD)\n\
         RIP: {:#018x}\n\
         RSP: {:#018x}",
        frame.instruction_pointer.as_u64(),
        frame.stack_pointer.as_u64(),
    );
}

/// Handle NMI — Non-Maskable Interrupt.
///
/// Runs on IST2. NMI cannot be disabled via CLI/IF flag.
/// Must complete and execute IRETQ to re-enable NMI delivery.
extern "x86-interrupt" fn handle_nmi(frame: InterruptStackFrame) {
    // NMI sources: memory ECC errors, watchdog timers, PCI bus errors.
    // In Linux: check NMI sources from IOAPIC/LAPIC, call registered handlers.
    let _ = frame;
    // IRETQ emitted here — this is the ONLY way to re-enable NMI delivery.
    // After IRETQ, NMI is unblocked and can fire again.
}

/// Handle #MC — Machine Check Exception.
///
/// Runs on IST3. Indicates hardware malfunction.
extern "x86-interrupt" fn handle_machine_check(frame: InterruptStackFrame) -> ! {
    let _ = frame;
    // Machine Check exceptions report via MSRs (IA32_MCG_STATUS, IA32_MCi_STATUS).
    // In Linux: MCA (Machine Check Architecture) handler reads these MSRs.
    // Usually unrecoverable — system halt.
    panic!("EXCEPTION: Machine Check - Hardware failure detected");
}

/// Handle IRQ0 — Timer interrupt (typically from LAPIC or PIC).
extern "x86-interrupt" fn handle_timer_irq(frame: InterruptStackFrame) {
    let _ = frame;
    // In a real OS:
    // 1. Update jiffies/ticks counter
    // 2. Check if current process time slice expired
    // 3. If expired: set resched flag (actual context switch happens on return to user)
    // 4. Send EOI (End of Interrupt) to APIC

    // Send EOI to Local APIC (address varies by system):
    // unsafe { core::ptr::write_volatile(0xFEE000B0 as *mut u32, 0); }

    // IRETQ emitted here — returns to wherever we were when the timer fired.
}

/// Handle IRQ1 — Keyboard interrupt.
extern "x86-interrupt" fn handle_keyboard_irq(frame: InterruptStackFrame) {
    let _ = frame;
    // Read scancode from I/O port 0x60
    let scancode: u8;
    unsafe {
        core::arch::asm!(
            "in al, 0x60",
            out("al") scancode,
            options(nomem, nostack)
        );
    }
    let _ = scancode;
    // In a real OS: push scancode to keyboard buffer, wake reader task.
    // Send EOI to APIC.
}

// ============================================================
// InterruptStackFrame — Understanding the type
// ============================================================
//
// The x86_64 crate's InterruptStackFrame type corresponds exactly to
// the CPU's hardware-pushed interrupt frame:
//
// pub struct InterruptStackFrame {
//     pub instruction_pointer: VirtAddr,  // RIP
//     pub code_segment: SegmentSelector,  // CS (with CPL in bits[1:0])
//     pub cpu_flags: u64,                 // RFLAGS
//     pub stack_pointer: VirtAddr,        // RSP
//     pub stack_segment: SegmentSelector, // SS
// }
//
// In Rust, this struct is passed by reference (&InterruptStackFrame).
// The "x86-interrupt" convention does NOT copy this struct;
// it passes a pointer to the frame on the stack.
//
// Modifying the frame (via InterruptStackFrame::as_mut()) allows
// changing where IRETQ returns — this is how signal delivery works:
// the kernel modifies the saved RIP to point to the signal handler,
// and IRETQ "returns" to the signal handler instead of where we were interrupted.

/// Example: Modify return address (for signal-like injection)
///
/// # Safety
/// - frame must contain a valid, mapped address
/// - The target address must be executable code
/// - CPL/privilege considerations must be respected
pub unsafe fn redirect_return(
    frame: &mut InterruptStackFrame,
    new_rip: VirtAddr,
) {
    // SAFETY: Caller ensures new_rip is a valid return target.
    let frame_mut = unsafe { frame.as_mut() };
    frame_mut.instruction_pointer = new_rip;
    // When IRETQ executes, it will jump to new_rip instead of original RIP.
}
```

### The `x86-interrupt` Calling Convention — What Rust Generates

```rust
// What the compiler actually generates for:
//   extern "x86-interrupt" fn handle_breakpoint(frame: InterruptStackFrame)
//
// Pseudo-assembly output (conceptual — actual codegen varies):
//
// handle_breakpoint:
//     ; "x86-interrupt" prologue: save registers that might be clobbered
//     pushq %rbp
//     pushq %rbx
//     pushq %r12
//     pushq %r13
//     pushq %r14
//     pushq %r15
//     ; (actually saves caller-saved regs based on what the function uses)
//
//     ; Load pointer to interrupt frame (it's at [rsp + saved_regs_size])
//     leaq  saved_regs_size(%rsp), %rdi
//
//     ; Function body...
//     ; (generated by Rust for the handler code)
//
//     ; "x86-interrupt" epilogue: restore saved registers
//     popq %r15
//     popq %r14
//     popq %r13
//     popq %r12
//     popq %rbx
//     popq %rbp
//
//     ; The KEY instruction:
//     iretq   ← emitted by compiler, NOT by the programmer
//
// The "x86-interrupt" calling convention guarantees:
// 1. All registers are preserved across the handler
// 2. The function ends with IRETQ (or IRETD in 32-bit mode)
// 3. The stack is in the correct state for IRETQ
// 4. For diverging handlers (-> !): IRETQ is omitted (panic! never returns)
```

---

## 18. Performance Analysis — Cache, Pipeline, Microarchitecture

### IRETQ on Modern CPUs — The Cost

```
  Instruction      │ Approximate Latency  │ Notes
  ─────────────────┼──────────────────────┼────────────────────────────────
  IRETQ            │ ~100–150 cycles      │ Full serialization, privilege check
  SYSRETQ          │ ~30–50 cycles        │ Fewer checks, no full frame pop
  RET              │ ~1–5 cycles          │ Just pops RIP, no privilege change
  CALL             │ ~1–5 cycles          │ Just pushes RIP and jumps
  
  Why is IRETQ slow?
  1. It is a SERIALIZING instruction — the CPU must complete all
     pending memory operations before IRETQ executes.
  2. Privilege level check requires reading segment descriptor from memory.
  3. Loading new RFLAGS can affect which instructions may follow (e.g., TF).
  4. In KPTI mode: CR3 write (page table switch) before IRETQ adds
     ~100–200 cycles (+ TLB flush unless PCID is used).
  5. If returning to user mode: segment register nullification.
```

### Cache Behavior During Interrupt Entry/Exit

```
  Interrupt fires while user process runs:
  
  L1 Cache state before interrupt:
  ┌──────────────────────────────────────────────┐
  │  [User code and data — hot in cache]         │
  │  [User stack pages — hot in cache]           │
  └──────────────────────────────────────────────┘
  
  After interrupt entry (kernel handler runs):
  ┌──────────────────────────────────────────────┐
  │  [Kernel code — cold if user was running]    │  ← CACHE MISS
  │  [Kernel stack — likely cold]                │  ← CACHE MISS
  │  [pt_regs struct — kernel stack writes]      │  ← Cache fills
  └──────────────────────────────────────────────┘
  
  After IRETQ (user resumes):
  ┌──────────────────────────────────────────────┐
  │  [User code — possibly evicted by kernel]    │  ← CACHE MISS likely
  │  [User stack — possibly evicted]             │  ← CACHE MISS possible
  │  [User data — possibly evicted]              │  ← CACHE MISS possible
  └──────────────────────────────────────────────┘
  
  Performance insight: Short-lived interrupt handlers (e.g., timer)
  that run frequently cause repeated cache eviction of user code.
  This is why Linux's timer handler does minimal work and defers
  heavy processing to softirqs and tasklets.
```

### TLB (Translation Lookaside Buffer) Impact

```
  Without KPTI:
  ├── IRETQ to user space: TLB retains all entries
  │   (kernel entries stay but inaccessible from user; user entries hot)
  └── Cost: ~0 extra cycles for TLB

  With KPTI (Meltdown mitigation):
  ├── Before IRETQ: must write new CR3 (user page tables)
  ├── CR3 write WITHOUT PCID: flushes ALL TLB entries
  │   → Entire TLB must be rebuilt from page table walks
  │   → Cost: 100–1000 extra cycles depending on memory access pattern
  └── CR3 write WITH PCID (Linux 4.14+):
      → Only flushes entries for current ASID if invalidated
      → Preserves user TLB entries across kernel/user transitions
      → Cost: much lower (~5–20 cycles for the CR3 write itself)

  PCID assignment in Linux (arch/x86/mm/tlb.c):
  - Each process gets a PCID (Process Context ID, 12-bit)
  - CR3 encodes both the page table base AND the PCID
  - Separate PCIDs for kernel and user page tables per process
```

### Branch Prediction and Speculative Execution at IRETQ

```
  IRETQ and the Branch Predictor:
  
  IRETQ is an indirect branch — the target (RIP from stack) is data.
  The CPU's Return Stack Buffer (RSB) tracks CALL/RET pairs but
  IRETQ is not a RET — the RSB does not apply.
  
  Instead, the Branch Target Buffer (BTB) may be used speculatively.
  If the BTB predicts a wrong IRETQ target:
  → Speculative execution runs wrong code
  → On architectures vulnerable to Spectre v2: may leak data
  
  Linux mitigations:
  1. RSB stuffing before IRETQ (fill RSB with safe addresses)
  2. IBRS (Indirect Branch Restricted Speculation) mode
  3. IBPB (Indirect Branch Predictor Barrier) on context switch
  4. RETPOLINE — replace indirect branches with safe sequences
     (not directly applicable to IRETQ but to other call paths)
```

### Stack Alignment and IRETQ Performance

```
  x86-64 ABI requires 16-byte stack alignment at call sites.
  IRETQ pops 5 × 8 = 40 bytes from the stack.
  40 mod 16 = 8, so IRETQ "misaligns" the stack by 8 bytes
  relative to how it found it.
  
  Wait — that's the whole POINT:
  Before interrupt: stack was 16-byte aligned (ABI guarantee)
  Interrupt pushes 5 × 8 = 40 bytes → stack is now aligned - 40 = aligned + 8
  (40 mod 16 = 8, so new RSP is (old RSP - 40), and (old RSP - 40) mod 16 = 8
   since old RSP mod 16 = 0 → (0 - 40) mod 16 = (-40) mod 16 = 8)
  
  After IRETQ: pops all 40 bytes back → RSP returns to original value
  Original RSP was 16-byte aligned → stack is again 16-byte aligned. ✓
  
  This is why Linux's stub code uses "and rsp, -16; call handler"
  (align for the C call), then carefully restores RSP before IRETQ.
```

---

## 19. Mental Models and Debugging IRET Issues

### The "Time Capsule" Mental Model

Think of the interrupt frame as a **time capsule** that the CPU buries when an interrupt fires:

```
  INTERRUPT FIRES:
  "Let me preserve exactly what I was doing..."
  
  CPU buries time capsule on the stack:
  ┌─────────────────────────────────────────────┐
  │  WHERE I was (RIP)                          │
  │  WHAT CODE I was running (CS + privilege)   │
  │  HOW I was configured (RFLAGS)              │
  │  WHAT STACK I was using (RSP + SS)          │
  └─────────────────────────────────────────────┘
  
  Handler runs...
  
  IRETQ:
  "Time capsule retrieved! Going back to exactly that moment..."
  CPU restores all five pieces of state from the capsule.
  Execution resumes as if the interrupt never happened.
  (Except time has passed and memory/registers may have changed)
```

### The "Checkpoint" Mental Model for Fault Handlers

```
  For FAULTS (divide error, page fault, invalid opcode):
  
  Saved RIP = the faulting instruction itself (not the next one).
  
  Handler "corrects" something (maps a page, adjusts a register).
  IRETQ → CPU "rewinds" to the faulting instruction.
  Instruction re-executes → now succeeds (because handler fixed it).
  
  For TRAPS (breakpoint, overflow):
  
  Saved RIP = instruction AFTER the trap instruction.
  Handler inspects/logs the situation.
  IRETQ → CPU continues from the NEXT instruction.
  Trap is not re-executed.
  
  CRITICAL BUG PATTERN:
  If you confuse a fault with a trap and don't advance RIP for a trap,
  or advance RIP for a fault when you shouldn't, you get an infinite loop
  or skipped instructions. Always check: is this a fault or a trap?
```

### Common IRET Bugs and How to Diagnose

```
  BUG 1: Stack not in correct state before IRETQ
  ──────────────────────────────────────────────
  Symptom: Immediate #GP or #SS after IRETQ
  Cause: Handler modified RSP incorrectly
         (pushed without corresponding pop, or misaligned)
  Debug: Before IRETQ, verify stack layout manually with a debugger:
         Check [RSP+0]=valid RIP, [RSP+8]=valid CS, [RSP+16]=flags,
         [RSP+24]=valid user RSP, [RSP+32]=valid SS

  BUG 2: Forgot to remove error code before IRETQ
  ────────────────────────────────────────────────
  Symptom: Returning to wrong address, random #GP
  Cause: For exceptions with error codes (#GP, #PF, etc.),
         the error code is on the stack ABOVE the frame.
         If not removed, IRETQ reads error code as RIP.
  Fix: "add rsp, 8" or "pop rcx" before IRETQ to skip error code.
       In Rust's "x86-interrupt": handled automatically by the compiler.

  BUG 3: Returning to wrong privilege level
  ─────────────────────────────────────────
  Symptom: #GP with error code = 0 immediately on IRETQ
  Cause: Saved CS has incorrect CPL, or new CPL > current CPL
  Debug: Inspect saved CS value. Bits[1:0] must be >= current CPL.

  BUG 4: Forgot SWAPGS before IRETQ (when returning to user)
  ────────────────────────────────────────────────────────────
  Symptom: User process crashes accessing TLS; kernel data visible from user
  Cause: GS still points to kernel per-CPU data after IRETQ
  Fix: Always SWAPGS before IRETQ when saved CS shows user-mode return.

  BUG 5: Stack corruption by pushing extra data and not cleaning up
  ─────────────────────────────────────────────────────────────────
  Symptom: IRETQ returns to garbage address
  Cause: Handler pushed registers but restored them in wrong order,
         or forgot to pop all pushed values before IRETQ.
  Debug: Count PUSH/POP pairs. They must be balanced.

  BUG 6: IF flag not restored (interrupts remain disabled after handler)
  ──────────────────────────────────────────────────────────────────────
  Symptom: System hangs; no more hardware interrupts processed
  Cause: RFLAGS on the saved frame had IF=0 (handler ran with IF=0,
         and the saved RFLAGS also had IF=0 — e.g., interrupt was
         fired while interrupts were already disabled).
  This is NOT a bug if intentional; but incorrect frames can cause it.
```

### IRETQ in a Debugger (GDB/LLDB)

```
  To step through IRETQ in GDB (kernel debugging via KGDB or QEMU):
  
  (gdb) x/5gx $rsp    ← examine 5 quadwords at current RSP
  → Shows: RIP, CS, RFLAGS, RSP, SS (the IRETQ frame)
  
  (gdb) info registers
  → Check current CS bits[1:0] vs. saved CS bits[1:0]
  
  (gdb) stepi          ← single-step through IRETQ
  → After stepi, registers should show user-mode values
  → RSP should be the user's RSP
  → RIP should be the saved RIP
  
  To verify RFLAGS restoration:
  (gdb) p/x $rflags                 ← before IRETQ (should have IF=0 or 1)
  (gdb) stepi                       ← execute IRETQ
  (gdb) p/x $rflags                 ← after (should match saved value)
```

---

## 20. Summary Reference Card

### IRETQ in 60 Seconds

```
  WHAT: Pops RIP, CS, RFLAGS, RSP, SS from the stack.
        Restores full CPU state saved at interrupt time.
        May switch from Ring 0 to Ring 3 (privilege transition).

  WHEN: At the end of EVERY interrupt/exception handler.
        The ONLY instruction that can atomically re-enable interrupts
        while returning to interrupted code.

  STACK STATE REQUIRED:
  ┌─────────────────────────┐  ← RSP must point here before IRETQ
  │  RIP     (8 bytes)      │
  │  CS      (8 bytes)      │  ← bits[1:0] = new CPL
  │  RFLAGS  (8 bytes)      │  ← bit 9 = IF (interrupt enable)
  │  RSP     (8 bytes)      │
  │  SS      (8 bytes)      │
  └─────────────────────────┘

  RULES:
  - New CPL (from CS) MUST be >= current CPL (can only return to same or less priv)
  - If new CPL > current CPL: privilege transition occurs (loads user RSP/SS)
  - If error code was pushed (for some exceptions): REMOVE IT FIRST (add rsp, 8)
  - In Linux: SWAPGS before IRETQ when returning to user mode
  - In KPTI: CR3 switch before IRETQ when returning to user mode

  ATOMICITY:
  - IRETQ cannot be interrupted mid-execution
  - Flags (including IF) restored atomically — no window of inconsistency

  SECURITY:
  - Cannot be used to escalate privilege (new_CPL >= current_CPL enforced)
  - Segment registers (DS/ES/FS/GS) nullified if their DPL < new CPL

  PERFORMANCE:
  - ~100-150 cycles (serializing instruction)
  - Prefer SYSRETQ for syscall returns when possible (~30-50 cycles)
  - KPTI adds ~100-200 cycles extra (CR3 switch) unless PCID used
```

### Quick Reference: Exception Type vs IRETQ Behavior

```
  Exception │ Type  │ Saved RIP points to   │ Error Code?│ IRETQ effect
  ──────────┼───────┼───────────────────────┼────────────┼──────────────────
  #DE       │ Fault │ DIV instruction        │ No         │ Restarts DIV
  #DB       │ F/T   │ Trap or fault instr.  │ No         │ Depends on cause
  #BP       │ Trap  │ Instr AFTER INT3      │ No         │ Continues after
  #PF       │ Fault │ Faulting instruction   │ Yes        │ Retries access
  #GP       │ Fault │ Offending instruction  │ Yes        │ Retries (if fixed)
  #DF       │ Abort │ —  (don't return)     │ Yes (=0)   │ Should not return
  NMI       │ Intr  │ Interrupted instr.    │ No         │ Resumes execution
  Hardware  │ Intr  │ Next instruction       │ No         │ Continues normally
  INT 3     │ Trap  │ Instr AFTER INT3      │ No         │ Continues after
```

---

## Appendix A — Key Registers Summary

```
  Register    │ Size     │ Role in IRET context
  ────────────┼──────────┼─────────────────────────────────────────────────
  RIP         │ 64-bit   │ Instruction pointer — IRETQ pops this first
  CS          │ 16-bit   │ Code segment — bits[1:0] = CPL (privilege level)
  RFLAGS      │ 64-bit   │ Status flags — IF bit controls interrupt enable
  RSP         │ 64-bit   │ Stack pointer — IRETQ restores user RSP
  SS          │ 16-bit   │ Stack segment — IRETQ restores for user mode
  CR2         │ 64-bit   │ Page Fault address — NOT touched by IRETQ
  CR3         │ 64-bit   │ Page table base — NOT touched by IRETQ
  GS.base     │ 64-bit   │ Per-CPU pointer — managed by SWAPGS, not IRETQ
  IDTR        │ 80-bit   │ Points to IDT — loaded once at init via LIDT
  TR          │ 16-bit   │ Task Register — points to TSS — loaded via LTR
```

## Appendix B — MSRs Relevant to Interrupt Handling

```
  MSR Address   │ Name                │ Role
  ──────────────┼─────────────────────┼────────────────────────────────────
  0xC0000080    │ IA32_EFER           │ Long Mode Enable, SYSCALL enable
  0xC0000081    │ IA32_STAR           │ SYSCALL: CS/SS selectors
  0xC0000082    │ IA32_LSTAR          │ SYSCALL 64-bit entry point address
  0xC0000083    │ IA32_CSTAR          │ SYSCALL compat-mode entry point
  0xC0000084    │ IA32_FMASK          │ RFLAGS bits cleared on SYSCALL
  0xC0000100    │ IA32_FS_BASE        │ FS segment base address
  0xC0000101    │ IA32_GS_BASE        │ GS segment base (current)
  0xC0000102    │ IA32_KERNEL_GS_BASE │ GS segment base (hidden — SWAPGS target)
  0x00000174    │ IA32_SYSENTER_CS    │ SYSENTER: target CS
  0x00000175    │ IA32_SYSENTER_ESP   │ SYSENTER: target ESP
  0x00000176    │ IA32_SYSENTER_EIP   │ SYSENTER: target EIP
```

---

*"The IRET instruction is where time folds: a CPU interrupted in the middle of one world resumes it perfectly, as if the entire interrupt system — all its complexity, all its protection machinery, all its stack magic — was simply a parenthesis in the flow of time."*

---

**References:**
- Intel® 64 and IA-32 Architectures Software Developer's Manual, Vol. 3A: System Programming Guide
- Linux Kernel Source: `arch/x86/entry/entry_64.S`
- Linux Kernel Source: `arch/x86/include/asm/ptrace.h`
- Linux Kernel Source: `arch/x86/kernel/idt.c`
- OSDev Wiki: https://wiki.osdev.org/Interrupt_Descriptor_Table
- x86_64 Rust crate documentation
- AMD64 Architecture Programmer's Manual, Vol. 2: System Programming