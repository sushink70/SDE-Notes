# Registers, Maps, Bytecode vs Native Instructions & Socket Buffers
## A Complete, In-Depth Technical Guide

---

## Table of Contents

1. [What Is a Register?](#1-what-is-a-register)
2. [Register Width — 8, 16, 32, 64-bit Explained](#2-register-width)
3. [The CPU Register File — Full Anatomy](#3-the-cpu-register-file)
4. [x86-64 Registers In Depth](#4-x86-64-registers-in-depth)
5. [ARM64 Registers In Depth](#5-arm64-registers-in-depth)
6. [eBPF Virtual Registers — Design and Purpose](#6-ebpf-virtual-registers)
7. [How Registers Map to Real CPU Registers (JIT)](#7-how-registers-map-to-real-cpu-registers)
8. [Interpreted Bytecode — What It Is, How It Works](#8-interpreted-bytecode)
9. [Native Instructions — How the CPU Actually Executes Code](#9-native-instructions)
10. [Bytecode vs Native: The Full Comparison](#10-bytecode-vs-native-the-full-comparison)
11. [JIT Compilation — Bridging the Gap](#11-jit-compilation)
12. [eBPF Maps — Complete Reference](#12-ebpf-maps-complete-reference)
13. [Map Internals — How Maps Are Implemented in the Kernel](#13-map-internals)
14. [Socket Buffer (sk_buff) — Complete Anatomy](#14-socket-buffer-sk_buff)
15. [sk_buff Lifecycle — From NIC to Application](#15-sk_buff-lifecycle)
16. [sk_buff and XDP — Why XDP is Faster](#16-sk_buff-and-xdp)
17. [sk_buff Memory Layout and Headroom/Tailroom](#17-sk_buff-memory-layout)
18. [C Implementations](#18-c-implementations)
19. [Rust Implementations](#19-rust-implementations)
20. [Putting It All Together](#20-putting-it-all-together)

---

## 1. What Is a Register?

### The Fundamental Concept

A **register** is the fastest storage that exists in a computer system. It lives directly inside the CPU chip itself — not on the motherboard, not in RAM, not in cache — but in the processor's core logic, built from the same transistors that do the computation.

When the CPU wants to add two numbers, it cannot add them while they sit in RAM. It must first **load** them into registers, perform the operation on the register values, and optionally **store** the result back to RAM. Every arithmetic, logical, and comparison operation happens on register values.

### The Memory Hierarchy

Understanding registers requires understanding the full memory hierarchy:

```
Speed      Size        Location        Latency
──────     ────────    ─────────       ────────
Fastest    ~bytes      CPU Registers   0 cycles (instantaneous)
           ~KB         L1 Cache        4–5 cycles   (~1 ns)
           ~MB         L2 Cache        12–14 cycles (~4 ns)
           ~MB–GB      L3 Cache        40–50 cycles (~15 ns)
           ~GB–TB      DRAM (RAM)      200+ cycles  (~60 ns)
Slowest    ~TB+        SSD/Disk        millions of cycles (~100 µs)
```

Registers are so fast because they are:
1. **Physically adjacent** to the ALU (Arithmetic Logic Unit) — connected by wires micrometers long
2. **Built from flip-flops** (SRAM cells) — not capacitors like DRAM, so no refresh needed
3. **Directly addressed** by the instruction — no address calculation, no cache lookup, no bus transaction

### What Is Stored in a Register?

Registers hold fixed-width binary values. A modern 64-bit general-purpose register holds 64 bits (8 bytes) — a single number that can represent:

- A signed integer: −9,223,372,036,854,775,808 to +9,223,372,036,854,775,807
- An unsigned integer: 0 to 18,446,744,073,709,551,615
- A memory address (pointer): any address in the 64-bit virtual address space
- A floating-point value (in float registers): IEEE 754 double
- Raw binary data (flags, bit masks, encoded structures)

The register itself does not know what it holds — it is just bits. The **instruction** gives meaning to those bits.

---

## 2. Register Width

### What "Width" Means

Register width (also called register size or bit-width) is the number of binary digits (bits) the register can hold simultaneously. This is one of the most fundamental properties of a CPU architecture.

### 8-bit Registers

An 8-bit register holds values from 0 to 255 (unsigned) or -128 to 127 (signed).

```
Bit positions:  7  6  5  4  3  2  1  0
                │  │  │  │  │  │  │  │
                0  1  1  0  1  0  0  1  = 0x69 = 105 (decimal)
```

The original Intel 8080 (1974) and Zilog Z80 processors had 8-bit registers. Modern CPUs like x86-64 still expose 8-bit views of their wider registers (AL, AH, BL, etc.).

**Memory address space**: An 8-bit address bus can address 2^8 = 256 bytes — completely unusable for modern systems.

### 16-bit Registers

A 16-bit register holds 0 to 65,535 (unsigned). The Intel 8086 (1978) was a 16-bit processor. DOS-era programs used 16-bit registers (AX, BX, CX, DX).

**Memory address space**: 2^16 = 65,536 bytes = 64 KB — the infamous "640K barrier" of DOS.

### 32-bit Registers

A 32-bit register holds 0 to 4,294,967,295 (approximately 4 billion). The Intel 386 (1985) introduced 32-bit registers (EAX, EBX, etc.). Windows XP, Linux 2.x, most programs from 1990–2005 are 32-bit.

**Memory address space**: 2^32 = 4,294,967,296 bytes = 4 GB — the "4 GB RAM limit" that plagued 32-bit Windows.

**Key implication for eBPF**: Classic BPF (cBPF) used 32-bit registers. eBPF upgraded to 64-bit, which is why eBPF can hold pointers (memory addresses) in registers, but cBPF could not.

### 64-bit Registers

A 64-bit register holds 0 to 18,446,744,073,709,551,615 (18.4 quintillion). The AMD64/x86-64 architecture (2003) introduced 64-bit registers (RAX, RBX, etc.). All modern desktop, server, and most mobile processors are 64-bit.

**Memory address space**: 2^64 = 16 exabytes — effectively unlimited for any foreseeable future. (Current x86-64 CPUs use 48-bit virtual addresses = 256 TB addressable per process.)

**Key implication for eBPF**: eBPF uses 64-bit registers, which means:
- Pointers to kernel memory fit in a single register
- 64-bit counters (packet counts, byte counts) fit in a single register
- No sign-extension or truncation is needed for most operations

### Width in Practice: Sub-register Access

Modern x86-64 CPUs allow accessing parts of a 64-bit register:

```
64-bit:  RAX  = [63..............................0]
32-bit:  EAX  = [              31..............0]
16-bit:  AX   = [                      15......0]
8-bit:   AH   = [                      15....8 ]   (high byte)
8-bit:   AL   = [                            7..0]  (low byte)
```

When you write to EAX (32-bit), the CPU **zero-extends** to RAX — the upper 32 bits are cleared. This is a deliberate x86-64 design decision to avoid false dependencies in out-of-order execution.

eBPF mirrors this: writing a 32-bit value to register R1 clears the upper 32 bits of R1.

### Why 64-bit Matters for eBPF Specifically

```
Classic BPF (32-bit):
  - Cannot hold a kernel pointer (kernel addresses are 64-bit on x86-64)
  - Cannot count > 4 billion events in one register
  - Cannot represent nanosecond timestamps (2^32 ns = only ~4.3 seconds)

eBPF (64-bit):
  - Pointers fit natively: void *p → u64 → R1
  - Counters never overflow in practice: u64 max = 18 quintillion
  - bpf_ktime_get_ns() returns u64: ~584 years before overflow
  - Map keys and values can be 64-bit natively
```

---

## 3. The CPU Register File

### What the Register File Is

The **register file** is the complete set of registers visible to software on a given CPU architecture. It is a small, extremely fast memory array inside the CPU core, with each slot directly wired to the ALU and other execution units.

### Types of Registers

Not all registers are the same. Modern CPUs have several distinct register sets:

#### General-Purpose Registers (GPRs)

These are the workhorses — integer arithmetic, address calculations, control flow. This is what we mean when we say "the register" in most contexts.

- x86-64: RAX, RBX, RCX, RDX, RSI, RDI, RSP, RBP, R8–R15 (16 registers, 64-bit each)
- ARM64: X0–X30, XZR (31 general purpose + zero register, 64-bit each)

#### Floating-Point / SIMD Registers

Separate registers for floating-point and vector (SIMD) operations:

- x86-64: XMM0–XMM15 (128-bit), YMM0–YMM15 (256-bit, AVX), ZMM0–ZMM31 (512-bit, AVX-512)
- ARM64: V0–V31 (128-bit NEON/SVE registers)

eBPF does **not** have SIMD registers — it works entirely with 64-bit integer registers. Floating-point is not supported in eBPF programs (by design — no FPU state save/restore in kernel hooks).

#### Control and Status Registers

Special registers for CPU control and state:

- **RIP / PC**: Instruction Pointer / Program Counter — holds the address of the next instruction to execute
- **RFLAGS / CPSR**: Flags register — stores results of comparisons (zero flag, carry flag, overflow flag, sign flag)
- **CR0–CR4** (x86-64): Control registers — page table base, protected mode, etc.
- **MSRs**: Model-Specific Registers — CPU features, performance counters, power management

#### Segment Registers (x86 legacy)

CS, DS, ES, FS, GS, SS — vestigial from 16/32-bit x86. Still used in 64-bit mode for thread-local storage (FS/GS base pointers).

### How the Register File Is Implemented in Silicon

The register file is implemented as a multi-ported **SRAM array** inside the CPU:

```
                    Read Port 1   Read Port 2   Write Port
                         │             │             │
                    ┌────▼─────────────▼─────────────▼────┐
Register 0 (RAX) → │  ████████████████████████████████   │
Register 1 (RCX) → │  ████████████████████████████████   │
Register 2 (RDX) → │  ████████████████████████████████   │
...                 │  ...                                 │
Register 15 (R15)→ │  ████████████████████████████████   │
                    └──────────────────────────────────────┘
```

Modern superscalar CPUs use **register renaming** — the 16 architectural registers visible to software are mapped to a much larger physical register file (e.g., 168 physical registers on Intel Skylake). This allows out-of-order execution without write-after-write hazards.

---

## 4. x86-64 Registers In Depth

### The 16 General-Purpose Registers

```
Register    64-bit    32-bit    16-bit    8-bit high    8-bit low
────────    ──────    ──────    ──────    ──────────    ─────────
Accumulator  RAX       EAX       AX          AH           AL
Base         RBX       EBX       BX          BH           BL
Counter      RCX       ECX       CX          CH           CL
Data         RDX       EDX       DX          DH           DL
Source Index RSI       ESI       SI          —            SIL
Dest Index   RDI       EDI       DI          —            DIL
Stack Ptr    RSP       ESP       SP          —            SPL
Base Ptr     RBP       EBP       BP          —            BPL
Extra 8–15   R8–R15    R8D-R15D  R8W-R15W    —            R8B-R15B
```

### Calling Convention (System V AMD64 ABI — Linux)

When a C function is called, the CPU and calling convention define exactly which registers hold which arguments:

```
Argument #     Register    Notes
──────────     ────────    ──────────────────────────────────────
1st integer    RDI         First function argument
2nd integer    RSI         Second function argument
3rd integer    RDX         Third function argument
4th integer    RCX         Fourth function argument
5th integer    R8          Fifth function argument
6th integer    R9          Sixth function argument
7th+           Stack        Additional args pushed onto stack

Return value   RAX         Primary return value
               RDX         Secondary return value (e.g., 128-bit)

Callee-saved   RBX, RBP, R12–R15    Function must preserve these
Caller-saved   RAX, RCX, RDX, RSI, RDI, R8–R11  May be clobbered
```

This is why eBPF's calling convention mirrors this: R1–R5 are argument registers (matching RDI, RSI, RDX, RCX, R8), and R0 is the return value (matching RAX). This makes the JIT translation from eBPF to x86-64 almost trivial for function calls.

### The RFLAGS Register

RFLAGS is a 64-bit register where each bit is a flag:

```
Bit   Flag    Name               Set when...
───   ────    ─────────────────  ─────────────────────────────
0     CF      Carry Flag         Unsigned overflow occurred
2     PF      Parity Flag        Result has even number of set bits
4     AF      Adjust Flag        BCD arithmetic carry
6     ZF      Zero Flag          Result is zero
7     SF      Sign Flag          Result is negative (MSB set)
8     TF      Trap Flag          Single-step debug mode
9     IF      Interrupt Flag     Hardware interrupts enabled
10    DF      Direction Flag     String operation direction
11    OF      Overflow Flag      Signed overflow occurred
```

Every comparison instruction (`cmp`, `test`) updates these flags. Every conditional jump instruction (`je`, `jne`, `jl`, `jg`) reads them.

In eBPF, conditional jumps work the same way conceptually, but the flags are implicit — `JEQ R1, R2, offset` compares R1 and R2 and branches if equal.

### RIP — The Instruction Pointer

RIP always holds the address of the **next** instruction to be fetched. You cannot directly write to RIP in most instructions, but:
- `jmp target` sets RIP = target
- `call func` pushes RIP on stack, sets RIP = func
- `ret` pops RIP from stack
- `syscall` saves RIP to RCX, jumps to syscall handler

The CPU's **fetch-decode-execute** cycle continuously increments RIP (or overwrites it for branches).

### RSP — The Stack Pointer

RSP points to the **top of the current stack** (lowest address of valid stack data, since the stack grows downward on x86):

```c
// What 'push rax' does:
RSP = RSP - 8;
*(uint64_t *)RSP = RAX;

// What 'pop rax' does:
RAX = *(uint64_t *)RSP;
RSP = RSP + 8;

// What 'call func' does:
RSP = RSP - 8;
*(uint64_t *)RSP = RIP;  // save return address
RIP = func;

// What 'ret' does:
RIP = *(uint64_t *)RSP;
RSP = RSP + 8;
```

---

## 5. ARM64 Registers In Depth

ARM64 (AArch64) is the 64-bit ARM architecture used in Apple Silicon, most Android phones, AWS Graviton, Raspberry Pi 4+, and many servers.

### General-Purpose Registers

ARM64 has 31 general-purpose 64-bit registers (X0–X30) plus a special zero register (XZR). Each Xn register can also be accessed as Wn (the lower 32 bits).

```
Register    Purpose                             Notes
────────    ─────────────────────────────────   ─────────────────
X0–X7       Function arguments / return values  Caller-saved
X8          Indirect result register            Struct return pointer
X9–X15      Scratch / temporary                 Caller-saved
X16–X17     Intra-procedure call temporaries    Used by PLT/linker stubs
X18         Platform register                   Reserved on some platforms
X19–X28     Callee-saved                        Must be preserved
X29 (FP)    Frame pointer                       Points to current stack frame
X30 (LR)    Link register                       Return address for BL instruction
SP          Stack pointer                       Not a GPR; separate register
PC          Program counter                     Not directly accessible
XZR         Zero register                       Always reads 0, writes discarded
```

ARM64's zero register (XZR) is elegant: `ADD X1, X2, XZR` adds X2 + 0, effectively moving X2 to X1. No need for a separate MOV instruction in many cases.

### ARM64 Calling Convention (AAPCS64)

```
X0–X7:   First 8 integer arguments (vs x86-64's 6)
X0–X1:   Return values
X19–X28: Callee-saved (function must restore these)
```

ARM64 has **more argument registers** than x86-64 (8 vs 6), meaning fewer function calls spill arguments to the stack.

---

## 6. eBPF Virtual Registers

### The eBPF Register Set

eBPF defines its own **virtual** register set — 11 registers (R0–R10), each 64 bits wide. These are not real CPU registers; they are an abstract specification that the eBPF virtual machine (or JIT compiler) must implement.

```
eBPF Register    Role                            Notes
─────────────    ──────────────────────────────  ──────────────────────────────
R0               Return value                    Function/helper return value; program exit code
R1               Argument 1                      At entry: pointer to program context
R2               Argument 2
R3               Argument 3
R4               Argument 4
R5               Argument 5                      Max 5 args to helper functions
R6               Callee-saved                    Preserved across helper calls
R7               Callee-saved                    Preserved across helper calls
R8               Callee-saved                    Preserved across helper calls
R9               Callee-saved                    Preserved across helper calls
R10              Read-only frame pointer         Points to top of 512-byte stack; NEVER written
```

### Why 11 Registers and This Specific Layout?

The design was deliberate to **mirror the System V AMD64 ABI** (the calling convention used on 64-bit Linux). This makes JIT compilation to x86-64 almost a 1:1 mapping:

```
eBPF    x86-64    ARM64    Notes
────    ──────    ─────    ─────────────────────────────────
R0      RAX       X0       Return value
R1      RDI       X0       Arg 1 (context pointer at program entry)
R2      RSI       X1       Arg 2
R3      RDX       X2       Arg 3
R4      RCX       X3       Arg 4
R5      R8        X4       Arg 5
R6      RBX       X19      Callee-saved
R7      R13       X20      Callee-saved
R8      R14       X21      Callee-saved
R9      R15       X22      Callee-saved
R10     RBP       X25      Frame pointer (read-only in eBPF)
```

With this mapping, a JIT compiler can translate `CALL bpf_helper` almost directly to `CALL helper_function` because the arguments are already in the right registers.

### R1 at Program Entry — The Context Pointer

When an eBPF program is triggered by a kernel event, the kernel puts a pointer to the **context** in R1. The type of this pointer depends on the program type:

```c
// XDP program entry:
// R1 = pointer to struct xdp_md
struct xdp_md {
    __u32 data;        // offset of packet data start
    __u32 data_end;    // offset of packet data end
    __u32 data_meta;   // offset of metadata area
    __u32 ingress_ifindex;  // receiving interface index
    __u32 rx_queue_index;   // receiving queue index
    __u32 egress_ifindex;   // (XDP_REDIRECT target)
};

// kprobe program entry:
// R1 = pointer to struct pt_regs (CPU register state at probe point)
struct pt_regs {
    unsigned long r15, r14, r13, r12;
    unsigned long rbp;
    unsigned long rbx;
    unsigned long r11, r10, r9, r8;
    unsigned long rax, rcx, rdx, rsi, rdi;
    unsigned long orig_rax;
    unsigned long rip;
    unsigned long cs;
    unsigned long eflags;
    unsigned long rsp;
    unsigned long ss;
};

// TC (traffic control) program entry:
// R1 = pointer to struct __sk_buff (the socket buffer)
```

### The Frame Pointer (R10) and the 512-byte Stack

R10 always points to the top of the eBPF program's stack. The stack is 512 bytes, allocated by the kernel when the program is invoked:

```
Memory:
  R10 ──→ [stack base + 512]   ← R10 is fixed here
          [local variable 1 ]  ← R10 - 8
          [local variable 2 ]  ← R10 - 16
          [local variable 3 ]  ← R10 - 24
          ...
          [stack base + 0   ]  ← bottom of stack

// In eBPF bytecode:
STW  [R10 - 4], 42     // store 42 at stack offset -4 from frame pointer
LDW  R1, [R10 - 4]     // load from stack into R1
```

R10 is **read-only** — the verifier enforces this. You can compute addresses relative to R10 to access stack slots, but you cannot change where R10 points.

### Callee-Save Semantics

When an eBPF program calls a helper function, the kernel's calling convention for helpers uses R1–R5 for arguments. These are **caller-saved** — the helper can overwrite them. R6–R9 are **callee-saved** — if the eBPF program stores a value in R6 before a helper call, R6 still holds that value after the helper returns.

```c
// This pattern is common in eBPF programs:
SEC("xdp")
int my_prog(struct xdp_md *ctx) {
    // ctx is in R1 at entry
    // Save it to R6 (callee-saved) before any helper call
    // (because helper calls may use R1–R5 for their own args)

    // In practice, the compiler handles this:
    // mov r6, r1    ← save ctx to callee-saved register

    __u64 pid = bpf_get_current_pid_tgid();  // uses R1-R5 internally
    // After this call, R1 is gone — but R6 still has ctx

    return XDP_PASS;
}
```

---

## 7. How Registers Map to Real CPU Registers (JIT)

### The JIT Register Allocation Problem

The eBPF JIT compiler must translate 11 virtual eBPF registers to real CPU registers. For x86-64, there are 16 GPRs available (though some are reserved for the stack pointer, etc.).

The x86-64 JIT in the Linux kernel (`arch/x86/net/bpf_jit_comp.c`) uses this mapping:

```c
/* From Linux kernel: arch/x86/net/bpf_jit_comp.c */
static const int reg2hex[] = {
    [BPF_REG_0]  = 0,  /* RAX */
    [BPF_REG_1]  = 7,  /* RDI */
    [BPF_REG_2]  = 6,  /* RSI */
    [BPF_REG_3]  = 2,  /* RDX */
    [BPF_REG_4]  = 1,  /* RCX */
    [BPF_REG_5]  = 8,  /* R8  */
    [BPF_REG_6]  = 3,  /* RBX — callee saved */
    [BPF_REG_7]  = 13, /* R13 — callee saved */
    [BPF_REG_8]  = 14, /* R14 — callee saved */
    [BPF_REG_9]  = 15, /* R15 — callee saved */
    [BPF_REG_FP] = 5,  /* RBP — frame pointer */
    [AUX_REG]    = 11, /* R11 — auxiliary (scratch) */
    [X86_REG_R9] = 9,  /* R9  */
};
```

### What JIT Translation Looks Like

Consider this eBPF bytecode:

```asm
; eBPF bytecode
BPF_ALU64_IMM(BPF_ADD, BPF_REG_1, 42)   ; R1 += 42
BPF_EXIT_INSN()                           ; return R0
```

The JIT compiler produces this x86-64 machine code:

```asm
; x86-64 native instructions
add    rdi, 42     ; RDI is the JIT mapping for eBPF R1
ret                ; return to kernel dispatcher
```

The eBPF instruction `ADD R1, 42` directly becomes `add rdi, 42` — a 1:1 translation. This is why the JIT-compiled eBPF runs at native CPU speed.

### The JIT Prologue and Epilogue

The JIT compiler wraps the translated code with standard function prologue/epilogue:

```asm
; JIT Prologue (generated before your eBPF code):
push   rbp           ; save caller's frame pointer
mov    rbp, rsp      ; set up new frame (maps to eBPF R10)
push   rbx           ; save callee-saved regs used by eBPF
push   r13
push   r14
push   r15
sub    rsp, 512      ; allocate eBPF 512-byte stack

; ... your JIT-compiled eBPF instructions here ...

; JIT Epilogue:
add    rsp, 512      ; deallocate eBPF stack
pop    r15
pop    r14
pop    r13
pop    rbx
pop    rbp
ret                  ; return to kernel caller
```

---

## 8. Interpreted Bytecode

### What Is Bytecode?

**Bytecode** is a compact binary representation of a program designed for a **virtual machine**, not for a real CPU. It is called "bytecode" because instructions are often one byte long (though eBPF uses 8-byte instructions).

The key properties of bytecode:

1. **Architecture-independent**: The same bytecode runs on x86-64, ARM64, MIPS, RISC-V — anywhere the virtual machine is implemented.
2. **Compact**: Bytecode is typically more compact than native machine code.
3. **Safe to execute**: A bytecode runtime can enforce constraints (bounds checking, type safety) at the virtual machine level.
4. **Not directly executed by the CPU**: The CPU executes the **virtual machine interpreter**, which reads bytecode and performs the corresponding operations.

### The Interpretation Loop

An interpreter is a program that reads bytecode instructions one by one and executes them. Here is a simplified eBPF interpreter loop (similar to what's in `kernel/bpf/core.c`):

```c
// Simplified eBPF interpreter (illustrative — not exact kernel code)
int bpf_interpreter(struct bpf_prog *prog, void *ctx)
{
    const struct bpf_insn *insn = prog->insnsi; // pointer to bytecode
    u64 regs[11] = {0};   // the 11 eBPF virtual registers
    u64 stack[64] = {0};  // 512-byte stack (64 × 8-byte slots)

    regs[BPF_REG_1]  = (u64)ctx;   // R1 = context pointer
    regs[BPF_REG_10] = (u64)(stack + 64); // R10 = frame pointer (top of stack)

    // The fetch-decode-execute loop
    for (;;) {
        u8  opcode = insn->code;
        u8  dst    = insn->dst_reg;
        u8  src    = insn->src_reg;
        s16 off    = insn->off;
        s32 imm    = insn->imm;

        switch (opcode) {

        // ALU operations
        case BPF_ALU64 | BPF_ADD | BPF_K:
            regs[dst] += imm;     // dst_reg += immediate value
            break;

        case BPF_ALU64 | BPF_ADD | BPF_X:
            regs[dst] += regs[src]; // dst_reg += src_reg
            break;

        case BPF_ALU64 | BPF_MOV | BPF_K:
            regs[dst] = imm;      // dst_reg = immediate
            break;

        // Memory load: dst_reg = *(u64 *)(src_reg + offset)
        case BPF_LDX | BPF_MEM | BPF_DW:
            regs[dst] = *(u64 *)(regs[src] + off);
            break;

        // Memory store: *(u64 *)(dst_reg + offset) = src_reg
        case BPF_STX | BPF_MEM | BPF_DW:
            *(u64 *)(regs[dst] + off) = regs[src];
            break;

        // Conditional jump: if dst_reg == src_reg, jump by offset
        case BPF_JMP | BPF_JEQ | BPF_X:
            if (regs[dst] == regs[src])
                insn += off; // advance instruction pointer by offset
            break;

        // Helper function call
        case BPF_JMP | BPF_CALL:
            // imm encodes which helper function to call
            regs[BPF_REG_0] = bpf_helper_table[imm](
                regs[1], regs[2], regs[3], regs[4], regs[5]
            );
            break;

        // Program exit: return R0
        case BPF_JMP | BPF_EXIT:
            return (int)regs[BPF_REG_0];

        // ... ~100 more opcodes
        }

        insn++; // advance to next instruction (unless we jumped)
    }
}
```

### The Overhead of Interpretation

Every single eBPF bytecode instruction requires:
1. **Fetch**: `insn++` and read `insn->code`, `insn->dst_reg`, etc. — 4 memory reads
2. **Decode**: the `switch(opcode)` dispatch — a branch prediction challenge
3. **Execute**: the actual operation (e.g., `regs[dst] += imm`)

For a simple eBPF `ADD` instruction:
- JIT-compiled: `add rdi, 42` — **1 CPU instruction**, ~0.3 ns
- Interpreted: the entire switch-case loop body — **~20–50 CPU instructions**, ~10–20 ns

This is a 30–50× overhead per instruction. For an eBPF program with 100 instructions running on 1 million packets/second, the difference is:
- JIT: 100 × 0.3 ns × 1,000,000 = 30 ms/s = 3% of one CPU core
- Interpreted: 100 × 15 ns × 1,000,000 = 1500 ms/s = 150% of one CPU core (impossible!)

This is why **JIT is mandatory** in practice for any real workload.

### Python's Bytecode — A Familiar Analogy

Python uses bytecode too. When you run `python3 script.py`:

1. Python compiles `script.py` → `script.cpython-311.pyc` (Python bytecode)
2. The CPython interpreter reads `.pyc` and executes it in a loop similar to the above
3. No JIT by default (PyPy adds JIT compilation to Python)

This is why Python is slow for CPU-bound tasks. The equivalent of Python's `for i in range(1000000): total += i` runs millions of interpreter dispatch cycles instead of a single tight native loop.

### Java Bytecode vs eBPF Bytecode

Both Java and eBPF use bytecodes, but with different goals:

```
                Java Bytecode           eBPF Bytecode
────────────    ─────────────────       ──────────────────────────
Purpose         Application portability Kernel-safe execution
Instruction     Variable (1–3 bytes)    Fixed (8 bytes always)
VM location     Userspace (JVM)         Kernel space (kernel BPF VM)
JIT             HotSpot JIT (adaptive)  Kernel JIT (at load time)
Safety          Runtime checks          Static verification (before run)
Loops           Unrestricted            Must be provably bounded
Memory alloc    Yes (garbage collected) No — only maps and stack
```

---

## 9. Native Instructions

### What "Native" Means

**Native instructions** are the binary machine code that the CPU directly decodes and executes in its hardware execution units. There is no intermediary — no interpreter, no virtual machine. The CPU fetches bytes from memory, decodes them as instructions specific to its architecture (x86-64, ARM64, etc.), and executes them.

### The CPU's Execution Pipeline

A modern out-of-order CPU executes instructions through a deep pipeline. Here is a simplified view of an Intel Core pipeline:

```
Stage             What Happens
─────────────     ─────────────────────────────────────────────────────
1. Fetch          Read 16–32 bytes from L1 instruction cache at RIP
2. Predecode      Identify instruction boundaries (x86 is variable-length!)
3. Decode         Decode 4–6 instructions into micro-ops (µops)
4. Rename         Map architectural registers to physical registers (renaming)
5. Dispatch       Place µops in the reorder buffer (ROB) and reservation stations
6. Execute        Up to 8 execution ports fire per cycle:
                  - Port 0: Integer ALU, branch
                  - Port 1: Integer ALU, integer multiply
                  - Port 2/3: Memory load
                  - Port 4: Memory store
                  - Port 5: SIMD/vector ALU
                  - Port 6: Integer ALU, branch
                  - Port 7: Memory store address
7. Writeback      Write results back to the physical register file
8. Retire         Commit results in program order, update architectural state
```

### Native Instruction Encoding

x86-64 instructions are **variable length** (1 to 15 bytes). This is complex but legacy-compatible (x86 has been extended since 1978).

```
Instruction       Encoding (hex bytes)    Length
───────────       ─────────────────────   ──────
nop               90                      1 byte
ret               C3                      1 byte
xor eax, eax      31 C0                   2 bytes
mov rax, 1        48 C7 C0 01 00 00 00    7 bytes
add rdi, 42       48 83 C7 2A             4 bytes
jmp short +5      EB 05                   2 bytes
movabs rax, addr  48 B8 xx xx xx xx xx    10 bytes
                       xx xx xx
```

ARM64 instructions are **fixed 32 bits** (4 bytes each) — much simpler to decode.

```
ARM64 Instruction    Encoding (binary)                        Hex
─────────────────    ────────────────────────────────────     ────────
add x0, x1, x2      10001011000000100000000000100000          8B020020
ret                  11010110010111110000001111000000          D65F03C0
mov x0, #42         11010010100000000000010101000000          D2800540
```

### How a Simple Function Executes Natively

```c
// C source code
int add(int a, int b) {
    return a + b;
}
```

Compiled to x86-64 native code:

```asm
; System V AMD64 ABI: a in EDI, b in ESI, return in EAX
add:
    lea eax, [rdi + rsi]   ; EAX = EDI + ESI (address arithmetic trick for add)
    ret
```

Compiled to ARM64 native code:

```asm
; AAPCS64: a in W0, b in W1, return in W0
add:
    add w0, w0, w1    ; W0 = W0 + W1
    ret
```

The CPU decodes these as electrical signals to specific functional units. `add w0, w0, w1` on ARM64:
- Fetched as 4 bytes: `0x0B010000`
- Decoded: "integer ADD, 32-bit, source registers W0 and W1, destination W0"
- Dispatched to integer ALU
- Executed: ALU inputs = physical register contents; output written back
- No interpreter, no dispatch table, no switch-case — pure silicon

---

## 10. Bytecode vs Native: The Full Comparison

### Execution Model Comparison

```
Dimension           Interpreted Bytecode        Native Code
─────────────────   ──────────────────────      ─────────────────────────
Who executes it     Virtual machine (software)  CPU hardware directly
Portability         Single binary, any arch      One binary per architecture
Speed               10–100× slower              Baseline
Startup             Fast (no compilation)        Requires ahead-of-time compile
Safety              VM can enforce bounds        No inherent safety; trust required
Instruction count   Few bytecodes = many ops     Direct 1:1 with CPU instructions
Code size           Usually smaller              Larger per operation
Debugging           VM can inspect state         Requires external debugger
JIT option          Some VMs add JIT             N/A (already native)
```

### Concrete Speed Comparison

Benchmarking a packet classifier (100 instructions):

```
Mode                    Throughput          Latency/packet
──────────────────      ──────────────      ─────────────────
eBPF interpreter        ~2M pkts/sec        ~500 ns
eBPF JIT-compiled       ~60M pkts/sec       ~17 ns
Hand-written C (native) ~70M pkts/sec       ~14 ns
```

The JIT-compiled eBPF is within 20% of hand-written C — the overhead is the JIT prologue/epilogue, not the instruction execution itself.

### Why Interpreted Bytecode Still Matters

Despite being slower, interpreted bytecode has irreplaceable advantages:

1. **Portability**: A `.class` file (Java), `.pyc` file (Python), or eBPF `.o` file runs anywhere the VM exists. No recompilation per architecture.

2. **Safety**: The VM can enforce memory safety, type safety, and resource limits at every step. This is why eBPF has an interpreter at all — it serves as the fallback for architectures without JIT support, and it was the original safe execution model.

3. **Introspection**: The interpreter can be paused, inspected, and debugged at the bytecode level.

4. **Hot-patching**: Bytecode can be replaced at runtime more easily than native code.

### The JIT Spectrum

In reality, "interpreted vs native" is a spectrum, not a binary:

```
Pure Interpretation    Bytecode + JIT         AOT Compilation
─────────────────      ──────────────────      ────────────────────
Python (CPython)       Java (HotSpot JVM)      C, C++, Rust
Ruby (MRI)             JavaScript (V8)         Go (AOT)
eBPF interpreter       eBPF JIT               Linux kernel C code
                       Python (PyPy)

← Slower, safer, portable     →     Faster, arch-specific →
```

eBPF spans this spectrum: it's bytecode verified statically, then JIT-compiled at load time to native code for production performance.

---

## 11. JIT Compilation

### What JIT Compilation Is

JIT (**Just-In-Time**) compilation converts bytecode to native machine code **at runtime**, just before execution. It is distinct from:

- **AOT (Ahead-Of-Time) compilation**: `gcc -O2 prog.c -o prog` — compiled before execution
- **Interpretation**: Bytecode executed step-by-step by a software VM
- **JIT**: Bytecode compiled to native code at runtime, then native code executed

### How eBPF JIT Works

When `bpf(BPF_PROG_LOAD, ...)` is called with JIT enabled:

```
Input: eBPF bytecode (array of struct bpf_insn)

Step 1: First pass — determine output size
  For each eBPF instruction:
    Estimate how many x86 bytes it compiles to
    Record position in output buffer

Step 2: Allocate executable memory
  kalloc(total_size, GFP_KERNEL | __GFP_EXEC)
  This memory is marked executable (NX bit cleared)

Step 3: Second pass — emit native code
  For each eBPF instruction, emit corresponding x86-64 bytes:

  eBPF: BPF_ALU64 | BPF_ADD | BPF_K, dst=R1, imm=42
  x86:  REX.W + 83 /0 2A  →  "add rdi, 42"  (4 bytes)

  eBPF: BPF_JMP | BPF_JEQ | BPF_X, dst=R0, src=R1, off=3
  x86:  48 39 F8  →  "cmp rax, rdi"         (3 bytes)
        0F 84 xx xx xx xx  →  "je target"    (6 bytes)

Step 4: Fix up jumps
  eBPF jumps use instruction-count offsets; x86 jumps use byte offsets
  Walk through emitted code and patch jump targets

Step 5: Install
  Replace bpf_prog->bpf_func (interpreter entry) with JIT function pointer
  Flush instruction cache (required on ARM, others)
  Mark memory read-only + executable (W^X security policy)
```

### JIT Hardening

For security, the kernel applies additional hardening to JIT-compiled eBPF:

1. **Constant blinding**: Immediate values in BPF instructions are XORed with a random key to prevent using JIT-compiled BPF as a gadget for return-oriented programming (ROP) attacks.

   ```asm
   ; Without blinding (vulnerable):
   mov rax, 0xdeadbeef

   ; With blinding (secure):
   mov rax, 0xdeadbeef ^ RANDOM_KEY
   xor rax, RANDOM_KEY
   ; Result is the same but the literal 0xdeadbeef never appears
   ```

2. **W^X (Write XOR Execute)**: JIT memory is writable during code generation, then the write bit is removed before the code executes. Code cannot be modified after installation.

3. **Guard pages**: Unmapped pages surround the JIT buffer to catch out-of-bounds execution.

### Adaptive JIT vs Load-Time JIT

eBPF uses **load-time JIT** — the entire program is compiled once when loaded. This differs from JVM/V8 style **adaptive JIT** which:
- Starts interpreting
- Profiles which code is hot
- JIT-compiles only the hot paths
- May recompile with more optimization

eBPF's load-time JIT is simpler and avoids the profiling overhead, which is appropriate for kernel code where any overhead is unacceptable.

---

## 12. eBPF Maps — Complete Reference

### What eBPF Maps Are

eBPF maps are **generic, typed, kernel-resident data structures** that serve as the primary mechanism for:

1. **State storage**: The eBPF program (which has no persistent variables) stores state in maps between invocations.
2. **Inter-CPU communication**: Multiple CPUs running the same eBPF program share maps.
3. **Kernel-to-userspace communication**: Maps are the bridge for sending data to userspace tools.
4. **Userspace-to-kernel communication**: Userspace configures eBPF behavior by writing to maps.

### Map Properties

Every map is characterized by:

```c
struct {
    __uint(type,        BPF_MAP_TYPE_HASH);  // Which map type
    __uint(max_entries, 1024);               // Maximum number of entries
    __type(key,   __u32);                    // Key type (and size)
    __type(value, __u64);                    // Value type (and size)
    __uint(map_flags, BPF_F_NO_PREALLOC);   // Allocation flags
} my_map SEC(".maps");
```

The kernel allocates map memory when the program is loaded. The `max_entries` limit is **hard** — attempting to insert beyond capacity fails.

### Complete Map Type Reference

---

#### `BPF_MAP_TYPE_HASH`

**Implementation**: A generic hash table using a fixed-size bucket array with chaining (linked lists within buckets). Each entry is a `(key, value)` pair.

**Properties**:
- O(1) average lookup, O(n) worst case (hash collision chain)
- Dynamically allocated entries (one `kmalloc` per entry)
- Concurrent access protected by per-bucket spinlocks
- Key can be any fixed-size byte sequence (struct, integer, etc.)

**Use cases**: Connection tracking tables, per-IP counters, pid → metadata mappings.

```
Bucket array (size = max_entries / HASH_MAP_DEFAULT_N_BUCKETS):

  [0] → {key=0x1234, value=42} → {key=0x5678, value=99} → NULL
  [1] → NULL
  [2] → {key=0xABCD, value=7} → NULL
  ...
```

**When to use**: When keys are sparse or arbitrary. When you don't know all keys at compile time.

---

#### `BPF_MAP_TYPE_ARRAY`

**Implementation**: A plain C array. Index is the key (must be `u32`, range 0 to `max_entries-1`). Values are stored at `array[key * value_size]`.

**Properties**:
- O(1) lookup always (just array indexing)
- **Pre-allocated**: The entire array is allocated at map creation time — zero lookup latency for existence check
- Cannot delete entries (only zero them out)
- Values are **zero-initialized** at creation
- No per-entry spinlock — reads/writes of aligned word-size values are atomic on modern CPUs

**Use cases**: Per-protocol counters (indexed by protocol number), fixed-size lookup tables, configuration arrays.

**Important detail**: Because the array is pre-allocated and all entries always exist, `bpf_map_lookup_elem` on an array **never returns NULL** (as long as the key is in range). The verifier knows this and allows direct use of the returned pointer.

```
max_entries = 4, value_size = 8:

Memory layout:
  Offset 0:   value[0]  (8 bytes)
  Offset 8:   value[1]  (8 bytes)
  Offset 16:  value[2]  (8 bytes)
  Offset 24:  value[3]  (8 bytes)
```

---

#### `BPF_MAP_TYPE_PERCPU_HASH` and `BPF_MAP_TYPE_PERCPU_ARRAY`

**Implementation**: Like their non-per-CPU counterparts, but each entry has **N copies** — one per CPU core. `bpf_map_lookup_elem` returns a pointer to the current CPU's copy.

**Why this exists**: Consider a counter updated on every packet:

```c
// Non-per-CPU: SLOW on multi-core
__u64 *count = bpf_map_lookup_elem(&counter_map, &key);
if (count)
    __sync_fetch_and_add(count, 1);
// __sync_fetch_and_add is an atomic operation
// On a 32-core server, this causes cache-line bouncing:
//   Core 0 updates, Core 1 wants to update, must wait for cache invalidation
//   At 10M pps, this atomic becomes a bottleneck
```

```c
// Per-CPU: FAST on multi-core
__u64 *count = bpf_map_lookup_elem(&percpu_counter_map, &key);
if (count)
    (*count)++;  // NO atomic needed! Only this CPU touches this slot
// No cache bouncing. Each CPU has its own cache line.
```

**Userspace aggregation**: From userspace, you read all per-CPU values and sum them:

```c
// Userspace C code to read per-CPU array
int nr_cpus = libbpf_num_possible_cpus();
__u64 values[nr_cpus];
__u32 key = PROTO_TCP;

bpf_map_lookup_elem(map_fd, &key, values);  // reads ALL CPUs at once

__u64 total = 0;
for (int i = 0; i < nr_cpus; i++)
    total += values[i];
```

---

#### `BPF_MAP_TYPE_LRU_HASH`

**Implementation**: A hash map with LRU (Least Recently Used) eviction. When the map is full and a new entry is inserted, the least recently accessed entry is automatically evicted.

**Properties**:
- Same O(1) average lookup as regular hash
- Automatic eviction — never returns "map full" error
- Uses a doubly-linked list to track access order
- Can use a global LRU list (all CPUs) or per-CPU LRU lists (`BPF_MAP_TYPE_LRU_PERCPU_HASH`)

**Use cases**: Connection tracking (millions of connections, limited map space), DNS cache, flow tables.

```
LRU List (doubly linked, most recent at head):

  [HEAD] ← key=192.168.1.1 ↔ key=10.0.0.1 ↔ key=172.16.0.5 → [TAIL]

When inserting a new entry and map is full:
  Evict TAIL (172.16.0.5, least recently used)
  Insert new entry at HEAD
```

---

#### `BPF_MAP_TYPE_RINGBUF` (kernel 5.8+)

This is the most important map type for event-driven observability. Understanding its design is essential.

**Problem it solves**: How do you stream variable-length, high-frequency events from an eBPF program to userspace with minimal overhead?

**Design**:

```
Single shared ring buffer (not per-CPU):

  ┌─────────────────────────────────────────────────────────┐
  │         Ring Buffer Memory (e.g., 16 MB)               │
  │                                                         │
  │  [cons_pos]                          [prod_pos]         │
  │      │                                   │              │
  │      ▼                                   ▼              │
  │  ────●───[event 1]──[event 2]──[event 3]──●────────     │
  │   (read                                (written         │
  │    here)                                here)           │
  └─────────────────────────────────────────────────────────┘

  cons_pos: consumer (userspace) read position
  prod_pos: producer (eBPF) write position
  Both are 64-bit counters that only advance (modulo buffer size)
```

**The reservation model**:

```c
// Step 1: Reserve space atomically
// This advances prod_pos by sizeof(struct event) + header
struct event *e = bpf_ringbuf_reserve(&rb, sizeof(*e), 0);
if (!e)
    return 0;  // buffer full — drop event

// Step 2: Fill in the event data
// (This can be done without any locking — we own this reserved slot)
e->pid  = bpf_get_current_pid_tgid() >> 32;
e->type = EVENT_EXEC;
bpf_get_current_comm(&e->filename, sizeof(e->filename));

// Step 3: Commit — mark the slot as readable by userspace
bpf_ringbuf_submit(e, 0);
// Userspace is now notified (if it's polling)
```

**Why reservation model?**:
- Multiple CPUs can reserve different slots simultaneously (no contention on filling)
- Contention only on the atomic increment of `prod_pos` — nanoseconds
- Data is filled in without locks
- Userspace only sees committed entries (never partial data)

**Userspace consumption** (via `mmap`):

```c
// libbpf ring_buffer__poll() under the hood:
// 1. mmap() the ring buffer memory
// 2. Read cons_pos and prod_pos
// 3. For each committed entry between cons_pos and prod_pos:
//    a. Call user callback with pointer to entry data
//    b. Advance cons_pos past this entry
// Zero copying — the callback gets a pointer directly into the mmap'd memory
```

---

#### `BPF_MAP_TYPE_PROG_ARRAY`

Stores file descriptors to other eBPF programs. Used exclusively with `bpf_tail_call()`.

**Tail calls**: A tail call replaces the current eBPF program's execution context with another program. It does **not** return to the caller:

```c
// Program array: index → eBPF program fd
struct {
    __uint(type, BPF_MAP_TYPE_PROG_ARRAY);
    __uint(max_entries, 8);
    __type(key, __u32);
    __type(value, __u32);  // prog fd
} prog_array SEC(".maps");

// Stage 1 program
SEC("xdp")
int parse_ethernet(struct xdp_md *ctx) {
    // ... parse ethernet header ...

    if (eth_proto == ETH_P_IP) {
        // Tail call to stage 2 — DOES NOT RETURN
        bpf_tail_call(ctx, &prog_array, 1);
    }

    // Only reached if tail call fails
    return XDP_PASS;
}
```

Why tail calls?
- The 512-byte stack is shared across BPF-to-BPF calls
- Tail calls reset the stack — each program gets fresh 512 bytes
- Enables modular pipeline architectures (parse → classify → action)
- Maximum tail call depth: 33 (kernel 5.2+)

---

#### `BPF_MAP_TYPE_SOCKMAP` and `BPF_MAP_TYPE_SOCKHASH`

Stores references to connected sockets. Used with `sk_msg` and `sk_skb` programs for **socket redirection**.

```
Without sockmap (normal send):
  App A → write() → TCP stack → sk_buff → NIC → Network → NIC → sk_buff → TCP stack → read() → App B

With sockmap (same-host zero-copy):
  App A → write() → sk_msg BPF program → bpf_msg_redirect_map() → App B's socket queue → read() → App B
          (skips entire network stack and NIC round-trip)
```

---

#### `BPF_MAP_TYPE_STACK_TRACE`

Stores kernel or userspace call stacks. Each entry is an array of instruction pointers representing the call chain.

```c
struct {
    __uint(type, BPF_MAP_TYPE_STACK_TRACE);
    __uint(max_entries, 10000);
    __uint(key_size, sizeof(__u32));           // stack ID
    __uint(value_size, PERF_MAX_STACK_DEPTH * sizeof(__u64)); // IP array
} stack_traces SEC(".maps");

// Capture kernel stack
__s64 stack_id = bpf_get_stackid(ctx, &stack_traces, 0);
// stack_id is a unique ID for this stack trace
// Userspace can later bpf_map_lookup_elem(stack_traces, stack_id)
// to get the array of instruction pointers, then symbolize them
```

---

#### `BPF_MAP_TYPE_BLOOM_FILTER` (kernel 5.16+)

A probabilistic set — answers "is this element probably in the set?" with:
- **No false negatives**: If element was inserted, lookup always says yes
- **Possible false positives**: Elements not inserted may sometimes appear as yes

```c
// Insert an IP into the bloom filter
__u32 ip = 0xC0A80101;  // 192.168.1.1
bpf_map_push_elem(&bloom_filter, &ip, 0);

// Test membership (in eBPF program, on hot path)
if (bpf_map_peek_elem(&bloom_filter, &src_ip) == 0) {
    // src_ip is PROBABLY in the filter (could be false positive)
    // Do more expensive hash map lookup to confirm
}
// If bpf_map_peek_elem returns error: src_ip is DEFINITELY not in filter
// (Skip expensive hash map lookup entirely)
```

Space efficiency: A bloom filter for 1 million IPs with 1% false positive rate needs only ~1.2 MB, vs ~50 MB for a hash map.

---

#### `BPF_MAP_TYPE_STRUCT_OPS` (kernel 5.6+)

Allows eBPF programs to implement kernel "struct ops" — vtable-like interfaces that the kernel calls for specific subsystem operations.

The most prominent use: **custom TCP congestion control algorithms**:

```c
// Implement a custom TCP congestion control algorithm entirely in eBPF
SEC("struct_ops/ssthresh")
__u32 BPF_PROG(my_tcp_ssthresh, struct sock *sk)
{
    struct tcp_sock *tp = tcp_sk(sk);
    __u32 cwnd = BPF_CORE_READ(tp, snd_cwnd);
    return cwnd / 2;  // halve the window on loss (CUBIC-like)
}

SEC("struct_ops/cong_avoid")
void BPF_PROG(my_tcp_cong_avoid, struct sock *sk, __u32 ack, __u32 acked)
{
    // Custom congestion avoidance logic
}

// Register the struct_ops implementation
SEC(".struct_ops")
struct tcp_congestion_ops my_cc = {
    .ssthresh   = (void *)my_tcp_ssthresh,
    .cong_avoid = (void *)my_tcp_cong_avoid,
    .name       = "my_bpf_cc",
};
```

This mechanism is expanding — timer ops, HID drivers, sched_ext (custom CPU scheduler) all use struct_ops.

---

### Map Concurrency and Synchronization

#### The Problem

eBPF programs run in interrupt/softirq context on multiple CPUs simultaneously. Two CPUs can both be executing the same eBPF program at the same time, both doing `bpf_map_update_elem`. Maps must handle this safely.

#### Solutions by Map Type

```
Map Type              Concurrency Mechanism
────────────────────  ─────────────────────────────────────────────
HASH                  Per-bucket spinlock (fine-grained locking)
ARRAY                 No lock (atomic CPU instructions for word-size)
PERCPU_HASH           Per-CPU: no cross-CPU contention possible
PERCPU_ARRAY          Per-CPU: no cross-CPU contention possible
LRU_HASH              Per-CPU LRU lists + global spinlock fallback
RINGBUF               Lock-free: atomic compare-and-swap on prod_pos
QUEUE/STACK           Single spinlock
```

#### BPF Spinlocks (kernel 5.1+)

For custom concurrency within map values, eBPF programs can use BPF spinlocks:

```c
struct counter {
    struct bpf_spin_lock lock;
    __u64 value;
};

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __type(key, __u32);
    __type(value, struct counter);
    __uint(max_entries, 1024);
} counters SEC(".maps");

SEC("xdp")
int count_packets(struct xdp_md *ctx) {
    __u32 key = 0;
    struct counter *c = bpf_map_lookup_elem(&counters, &key);
    if (!c) return XDP_PASS;

    bpf_spin_lock(&c->lock);
    c->value++;
    bpf_spin_unlock(&c->lock);

    return XDP_PASS;
}
```

---

## 13. Map Internals — How Maps Are Implemented in the Kernel

### The `bpf_map` Struct

The kernel represents every map as a `struct bpf_map` (from `include/linux/bpf.h`):

```c
struct bpf_map {
    const struct bpf_map_ops *ops;  // vtable: lookup, update, delete, alloc_check, ...
    struct bpf_map *inner_map_meta; // for map-in-map types
    void *security;                 // LSM security blob

    enum bpf_map_type map_type;     // HASH, ARRAY, etc.
    u32 key_size;                   // size of keys in bytes
    u32 value_size;                 // size of values in bytes
    u32 max_entries;                // maximum number of entries
    u64 map_flags;                  // BPF_F_* flags

    u32 id;                         // unique map ID (for bpftool)
    int numa_node;                  // NUMA node for allocation
    u32 btf_key_type_id;            // BTF type ID for keys
    u32 btf_value_type_id;          // BTF type ID for values
    struct btf *btf;                // BTF metadata

    struct percpu_ref refcnt;       // reference count
    struct work_struct work;        // deferred cleanup work
    struct mutex freeze_mutex;
    atomic64_t writecnt;

    /* For pinning */
    char name[BPF_OBJ_NAME_LEN];
};
```

### The Map Operations Vtable

Each map type implements a `struct bpf_map_ops` with function pointers:

```c
struct bpf_map_ops {
    /* Called at map creation */
    int (*map_alloc_check)(union bpf_attr *attr);
    struct bpf_map *(*map_alloc)(union bpf_attr *attr);
    void (*map_release)(struct bpf_map *map, struct file *map_file);
    void (*map_free)(struct bpf_map *map);

    /* Called from eBPF programs (performance critical!) */
    void *(*map_lookup_elem)(struct bpf_map *map, void *key);
    int   (*map_update_elem)(struct bpf_map *map, void *key, void *value, u64 flags);
    int   (*map_delete_elem)(struct bpf_map *map, void *key);
    int   (*map_push_elem)(struct bpf_map *map, void *value, u64 flags);
    int   (*map_pop_elem)(struct bpf_map *map, void *value);
    int   (*map_peek_elem)(struct bpf_map *map, void *value);

    /* Called from userspace via bpf() syscall */
    int (*map_get_next_key)(struct bpf_map *map, void *key, void *next_key);
    int (*map_lookup_and_delete_elem)(struct bpf_map *map, void *key, void *value, u64 flags);

    /* Batched operations (kernel 5.6+) */
    int (*map_lookup_batch)(struct bpf_map *map, const union bpf_attr __user *uattr,
                            union bpf_attr __user *uattr_size);
};
```

### Hash Map Implementation Details

The BPF hash map (kernel/bpf/hashtab.c) uses:

```
struct bpf_htab {
    struct bpf_map map;             // embedded base map struct
    struct bucket *buckets;         // bucket array
    void *elems;                    // pre-allocated elements (if BPF_F_NO_PREALLOC not set)
    struct pcpu_freelist freelist;  // free element pool
    struct htab_elem *extra_elems;  // per-CPU spare elements
    u32 n_buckets;                  // number of buckets (power of 2)
    u32 elem_size;                  // size of each element
    u32 hashrnd;                    // random seed for hash function
};

struct bucket {
    struct hlist_nulls_head head;   // linked list of elements in this bucket
    union {
        raw_spinlock_t raw_lock;    // spinlock for this bucket
        struct {
            u8 plock_flags;
            u8 pad[3];
        };
    };
};
```

**Hash function**: The kernel uses `jhash` (Jenkins hash) or `htab_map_hash` (based on the key size) to map keys to bucket indices.

**Pre-allocation vs on-demand**: By default, the hash map pre-allocates all `max_entries` elements at creation time to avoid `kmalloc` in the hot path (which could fail under memory pressure). Pass `BPF_F_NO_PREALLOC` to allocate elements on demand.

---

## 14. Socket Buffer (sk_buff) — Complete Anatomy

### What sk_buff Is

The `struct sk_buff` (socket buffer, often called "skb") is the central data structure of the Linux networking stack. It is the kernel's representation of a **network packet** — the envelope that carries packet data as it flows through the networking stack.

Every TCP segment, UDP datagram, ICMP message, or raw packet that Linux handles is wrapped in an `sk_buff`. Understanding sk_buff is essential to understanding:
- Why XDP is faster than TC (no sk_buff allocation at XDP time)
- How eBPF TC programs modify packets
- Why copying packets to userspace is expensive (it means copying the sk_buff's data)

### The sk_buff Dual Nature

sk_buff serves two purposes simultaneously:

1. **Metadata container**: All the parsed information about the packet — source/dest IP, ports, protocol, network interface, timestamps, checksums, socket reference, netfilter marks, etc.

2. **Data pointer**: A reference to the actual packet bytes (the raw bytes that were received from or will be sent to the network).

The packet data is **not embedded in the sk_buff struct** itself (except for small packets with skb_small_head). Instead, sk_buff contains a pointer to a separate data buffer.

### sk_buff Memory Layout

```
struct sk_buff (metadata, ~240 bytes on x86-64):
┌─────────────────────────────────────────────────────────────┐
│  struct sk_buff *next, *prev      (queue linkage)           │
│  struct sock    *sk               (owning socket, or NULL)  │
│  ktime_t         tstamp           (receive timestamp)       │
│  struct net_device *dev           (network device)          │
│  unsigned char  *head             (start of buffer)    ─────┼──┐
│  unsigned char  *data             (start of valid data)─────┼──┼─┐
│  unsigned char  *tail             (end of valid data)  ─────┼──┼─┼─┐
│  unsigned char  *end              (end of buffer)      ─────┼──┼─┼─┼─┐
│  unsigned int    len              (length of valid data)    │  │ │ │ │
│  unsigned int    data_len         (length in fragments)     │  │ │ │ │
│  __u16           protocol         (e.g., ETH_P_IP = 0x800) │  │ │ │ │
│  __u16           transport_header (offset to L4 header)     │  │ │ │ │
│  __u16           network_header   (offset to L3 header)     │  │ │ │ │
│  __u16           mac_header       (offset to L2 header)     │  │ │ │ │
│  __u32           mark             (fwmark for routing)      │  │ │ │ │
│  __u32           hash             (flow hash)               │  │ │ │ │
│  skb_frag_t      frags[]          (page fragments)          │  │ │ │ │
│  ... 100+ more fields ...                                   │  │ │ │ │
└─────────────────────────────────────────────────────────────┘   │ │ │ │
                                                                   │ │ │ │
Data buffer (allocated separately, typically from SLAB/page):     │ │ │ │
┌──────────────────────────────────────────────────────────────┐  │ │ │ │
│   Headroom   │   Packet Data (Ethernet+IP+TCP+payload)  │ TR │  │ │ │ │
│   (reserved  │                                          │ (t │  │ │ │ │
│    for new   │                                          │ ail│  │ │ │ │
│    headers)  │                                          │ rm)│  │ │ │ │
└──────────────────────────────────────────────────────────────┘  │ │ │ │
 ▲             ▲                                          ▲     ▲  │ │ │ │
 │             │                                          │     │  │ │ │ │
head ──────────┘─────────────────────────────────────────┼─────┘◄─┘ │ │ │
data ──────────────────────────────────────────────────►─┘◄──────── ┘ │ │
tail ────────────────────────────────────────────────────────────────►─┘ │
end  ──────────────────────────────────────────────────────────────────►─┘
```

### The Four Pointers: head, data, tail, end

These four pointers define the sk_buff's data buffer:

| Pointer | Points To | Purpose |
|---|---|---|
| `head` | Start of allocated buffer | The lowest address of the buffer — **never moved** |
| `data` | Start of valid packet data | Moves forward as headers are stripped (e.g., as packet ascends the stack) |
| `tail` | End of valid packet data | Moves forward when data is appended |
| `end` | End of allocated buffer | The highest address of the buffer — **never moved** |

The **headroom** is the space between `head` and `data`: `skb_headroom(skb) = data - head`

The **tailroom** is the space between `tail` and `end`: `skb_tailroom(skb) = end - tail`

### Why Headroom and Tailroom Exist

When a packet is received:
- The NIC DMA's the packet data starting at `data`
- The driver allocates **extra headroom** before `data` so that upper layers can prepend headers without reallocating

When a packet is transmitted:
- A UDP application fills in UDP payload
- The kernel prepends a UDP header by doing: `data -= sizeof(udp_header)` (uses headroom)
- The kernel prepends an IP header: `data -= sizeof(ip_header)`
- The kernel prepends an Ethernet header: `data -= sizeof(eth_header)`
- The NIC transmits from `data` to `tail`

No memory copying is needed for header prepending — the kernel just moves the `data` pointer backward into the pre-allocated headroom!

### Packet Header Offsets

The sk_buff stores the **relative offsets** to each protocol header (relative to `head`):

```c
// Get pointer to IP header from sk_buff:
struct iphdr *ip = (struct iphdr *)skb_network_header(skb);
// Expands to: (struct iphdr *)(skb->head + skb->network_header)

// Get pointer to TCP header:
struct tcphdr *tcp = (struct tcphdr *)skb_transport_header(skb);
// Expands to: (struct tcphdr *)(skb->head + skb->transport_header)

// Get pointer to Ethernet header:
struct ethhdr *eth = (struct ethhdr *)skb_mac_header(skb);
```

As the packet ascends the network stack (L2 → L3 → L4 → socket), the `data` pointer moves forward and the header offsets track where each protocol layer's header begins.

### sk_buff and Fragmentation

For large packets (e.g., from TCP segmentation offload or IP fragmentation), the sk_buff uses a **fragment list**:

```c
// In struct sk_buff:
unsigned int data_len;      // bytes in fragments (not in linear buffer)
__u8         nr_frags:8;    // number of page fragments

skb_frag_t shinfo->frags[MAX_SKB_FRAGS]; // up to 17 page fragments
```

The total packet length is `skb->len = linear_data_len + skb->data_len`.

Functions like `skb_linearize()` can pull all fragment data into the linear buffer (at the cost of a copy).

### Key Fields of struct sk_buff

```c
struct sk_buff {
    /* --- Queue management --- */
    struct sk_buff *next;       // next skb in queue
    struct sk_buff *prev;       // prev skb in queue

    /* --- Ownership --- */
    struct sock  *sk;           // socket that owns this skb (NULL for forwarded pkts)
    struct net   *dev_scratch;  // network namespace

    /* --- Device info --- */
    struct net_device *dev;     // network interface this skb arrived on / will leave from

    /* --- Data pointers (in the linear buffer) --- */
    unsigned char *head;        // start of buffer
    unsigned char *data;        // start of valid data
    unsigned char *tail;        // end of valid data (unsigned char *; on 64-bit often u32 offset)
    unsigned char *end;         // end of buffer

    unsigned int len;           // total length of all data (linear + fragments)
    unsigned int data_len;      // length of data in fragments (non-linear part)
    unsigned int truesize;      // total memory consumed by this skb (for sk_rmem_alloc accounting)

    /* --- Protocol information (set by kernel parsers) --- */
    __be16  protocol;           // L2/L3 protocol: ETH_P_IP=0x800, ETH_P_IPV6=0x86DD, etc.
    __u16   transport_header;   // offset of L4 (TCP/UDP) header from head
    __u16   network_header;     // offset of L3 (IP) header from head
    __u16   mac_header;         // offset of L2 (Ethernet) header from head
    __u16   inner_transport_header; // for tunnels
    __u16   inner_network_header;
    __u16   inner_mac_header;

    /* --- Timestamps --- */
    ktime_t tstamp;             // receive timestamp (nanoseconds)
    u64     skb_mstamp_ns;      // monotonic clock ns (TCP internal)

    /* --- Checksums --- */
    __wsum  csum;               // checksum value
    __u8    ip_summed:2;        // checksum status: NONE, UNNECESSARY, COMPLETE, PARTIAL
    __u8    csum_valid:1;       // checksum already verified

    /* --- Hash and routing --- */
    __u32   hash;               // flow hash (for RSS/RPS/RFS)
    __u32   mark;               // fwmark (used by iptables -j MARK, eBPF bpf_skb_set_mark)
    __u32   priority;           // qdisc priority

    /* --- Flags (packed into bitfields) --- */
    __u8    pkt_type:3;         // PACKET_HOST, PACKET_BROADCAST, PACKET_MULTICAST, etc.
    __u8    fclone:2;           // fast clone status
    __u8    ipvs_property:1;
    __u8    nohdr:1;            // data header-less (e.g., in fragments)
    __u8    nf_trace:1;
    __u8    encapsulation:1;    // inner headers valid
    __u8    tc_at_ingress:1;
    __u8    redirected:1;

    /* --- Netfilter / conntrack --- */
#if IS_ENABLED(CONFIG_NF_CONNTRACK)
    unsigned long  _nfct;       // pointer to nf_conn (connection tracking entry)
#endif
    __u32   nfmark;             // netfilter mark

    /* --- TCP/IP specific --- */
    __u32   secmark;            // SELinux security mark
    union {
        __u32 mark;
        __u32 reserved_tailroom;
    };

    /* --- Shared info (at end of linear buffer) --- */
    /* skb_shared_info is placed AT skb->end: */
    struct skb_shared_info *shinfo; // == (struct skb_shared_info *)skb->end
    // Contains: nr_frags, frags[], gso_size, gso_segs, frag_list
};
```

### sk_buff Shared Info

The `skb_shared_info` structure lives at `skb->end` (the end of the linear data buffer) and holds extra metadata:

```c
struct skb_shared_info {
    __u8         flags;
    __u8         meta_len;
    __u8         nr_frags;          // number of page fragments
    __u8         tx_flags;
    unsigned short gso_size;        // GSO segment size
    unsigned short gso_segs;        // number of GSO segments
    struct sk_buff *frag_list;      // linked list of sk_buffs for IP fragmentation

    skb_frag_t frags[MAX_SKB_FRAGS]; // up to 17 page fragments
    // Each frags[i] = { page, page_offset, size }
};
```

---

## 15. sk_buff Lifecycle — From NIC to Application

### Complete Flow: Receiving a TCP Packet

```
1. NIC HARDWARE
   ├── Packet arrives at the NIC
   ├── NIC DMA's packet bytes into pre-allocated ring buffer slot
   └── NIC raises interrupt (or NAPI poll triggers)

2. DEVICE DRIVER (e.g., ixgbe, mlx5, virtio-net)
   ├── NAPI poll: driver's napi_poll() is called
   ├── alloc_skb() or build_skb(): allocate struct sk_buff
   │   └── kmem_cache_alloc() from skbuff_head_cache slab
   ├── Set skb->data, skb->len, skb->dev
   └── Call netif_receive_skb(skb) or napi_gro_receive(skb)

   [XDP hook fires HERE if XDP program is attached — BEFORE sk_buff allocation
    in native XDP, or AFTER sk_buff in generic XDP]

3. NETWORK CORE (net/core/dev.c)
   ├── __netif_receive_skb_core()
   ├── Run TC ingress BPF programs (if attached)
   ├── Deliver to packet_rcv() if raw socket listener exists
   └── ip_rcv() — hand off to IP stack

4. IP LAYER (net/ipv4/ip_input.c)
   ├── ip_rcv(): validate IP header
   ├── skb->network_header set
   ├── Netfilter PREROUTING hook (iptables NF_INET_PRE_ROUTING)
   └── ip_rcv_finish() → ip_route_input() → routing decision

5. ROUTING DECISION
   ├── Local delivery: ip_local_deliver()
   └── Forwarding: ip_forward()

   For local delivery:
   ├── Netfilter INPUT hook (iptables NF_INET_LOCAL_IN)
   └── ip_local_deliver_finish()

6. TRANSPORT LAYER
   ├── tcp_v4_rcv() (for TCP)
   ├── skb->transport_header set
   ├── TCP header validation, sequence number check
   ├── Connection lookup: __inet_lookup_skb() → find struct sock
   └── tcp_enqueue_data() → add to socket receive queue

7. APPLICATION
   ├── recv()/read() system call
   ├── tcp_recvmsg(): dequeue sk_buff from socket receive queue
   ├── skb_copy_datagram_msg(): copy packet data to userspace buffer
   └── kfree_skb(): free the sk_buff when done
```

### Memory Lifecycle

```
alloc_skb(size):
  1. kmem_cache_alloc(&skbuff_head_cache) → sk_buff struct
  2. kmalloc(size + SKB_DATA_ALIGN(sizeof(skb_shared_info)))
     → data buffer
  3. sk_buff->head = data_buffer
  4. sk_buff->data = data_buffer + NET_SKB_PAD  (NET_SKB_PAD = 64 bytes headroom)
  5. skb_reset_tail_pointer(sk_buff)
  6. sk_buff->end = data_buffer + data_buffer_size - SKB_DATA_ALIGN(sizeof(skb_shared_info))

kfree_skb(skb):
  1. skb_release_head_state(skb): release any socket/dst/conntrack references
  2. skb_release_data(skb): release page fragments, frag_list
  3. kfree_skbmem(skb): return to skbuff_head_cache or kfree the data buffer
```

### The Cost of sk_buff Allocation

Each `alloc_skb()` involves:
- A slab cache lookup (fast, ~30 ns)
- Possible `kmalloc` for the data buffer (~50 ns)
- memset to zero key fields
- Reference counting setup

At 10M packets/second, this is 80 µs/s overhead just for allocation — significant but acceptable for the kernel networking stack. But for a DDoS mitigation dropping 100M pps, it becomes the bottleneck — which is exactly why **XDP runs before sk_buff allocation**.

---

## 16. sk_buff and XDP — Why XDP is Faster

### The Critical Difference

```
Generic XDP (fallback mode):
  NIC → [sk_buff allocated] → [XDP program runs on sk_buff] → [sk_buff freed if DROP]

Native XDP (driver mode):
  NIC → [XDP program runs on raw DMA buffer] → [sk_buff allocated ONLY if PASS]
```

In native XDP:
- The XDP program sees the raw packet bytes via `struct xdp_md`
- `xdp_md->data` and `xdp_md->data_end` are offsets into the DMA ring buffer
- No `sk_buff` is ever allocated if the packet is dropped
- No `kmalloc`, no reference counting, no slab cache operations

**Performance comparison for a drop-all rule**:

```
Method                          Cost per packet     Max throughput (1 core)
──────────────────────────────  ──────────────      ──────────────────────
iptables DROP (netfilter)       ~500 ns             ~2M pps
TC BPF drop (generic)           ~300 ns             ~3M pps
XDP drop (generic mode)         ~150 ns             ~7M pps
XDP drop (native mode)          ~20–40 ns           ~25–50M pps
XDP drop (NIC offload)          ~0 ns (on NIC CPU)  Line rate (100M+ pps)
```

### The `struct xdp_md` vs `struct __sk_buff`

eBPF programs in XDP context see `struct xdp_md` — a thin wrapper:

```c
struct xdp_md {
    __u32 data;             // offset of packet start in the DMA buffer
    __u32 data_end;         // offset of packet end
    __u32 data_meta;        // offset of metadata area (before data)
    __u32 ingress_ifindex;  // interface the packet arrived on
    __u32 rx_queue_index;   // RX queue that received the packet
    __u32 egress_ifindex;   // (only valid after XDP_REDIRECT)
};

// In the XDP program, you access packet data like:
void *data     = (void *)(long)ctx->data;       // raw pointer to packet start
void *data_end = (void *)(long)ctx->data_end;   // raw pointer to packet end
```

No socket reference, no route, no conntrack, no headers parsed — just raw bytes. The XDP program must parse everything itself.

TC programs see `struct __sk_buff` — the user-visible shadow of `struct sk_buff`:

```c
// struct __sk_buff is what eBPF TC programs see
// It mirrors key fields of the real sk_buff
struct __sk_buff {
    __u32 len;              // packet length
    __u32 pkt_type;         // PACKET_HOST, etc.
    __u32 mark;             // fwmark
    __u32 queue_mapping;
    __u32 protocol;         // ETH_P_IP, etc.
    __u32 vlan_present;
    __u32 vlan_tci;
    __u32 vlan_proto;
    __u32 priority;
    __u32 ingress_ifindex;
    __u32 ifindex;
    __u32 tc_index;
    __u32 cb[5];            // control buffer (can be used by eBPF)
    __u32 hash;
    __u32 tc_classid;
    __u32 data;             // pointer to packet data
    __u32 data_end;
    __u32 napi_id;
    __u32 family;
    __u32 remote_ip4;
    __u32 local_ip4;
    __u32 remote_ip6[4];
    __u32 local_ip6[4];
    __u32 remote_port;
    __u32 local_port;
    __u32 data_meta;
    __bpf_md_ptr(struct bpf_flow_keys *, flow_keys);
    __u64 tstamp;
    __u32 wire_len;
    __u32 gso_segs;
    __bpf_md_ptr(struct bpf_sock *, sk);
    __u32 gso_size;
    __u8  tstamp_type;
    __u32 hwtstamp;
};
```

---

## 17. sk_buff Memory Layout and Headroom/Tailroom

### The Contiguous Linear Buffer

```
Physical memory layout of a received Ethernet/IP/TCP packet:

Offset 0:
┌──────────────────────────────────────────────────────────────────────────┐
│  NET_SKB_PAD      │ ETH HDR │ IP HDR │ TCP HDR │ TCP Payload  │ shinfo  │
│  (headroom: 64B)  │ (14B)   │ (20B)  │ (20B)   │ (variable)   │ (320B)  │
│                   │         │        │         │              │         │
│ ◄────────────────►│◄────────────────────────────────────────►│         │
│   skb_headroom()  │              skb->len                    │         │
│                   │                                          │         │
│ head              │data                                 tail │end      │
└──────────────────────────────────────────────────────────────────────────┘
```

### Headroom Operations

```c
// Check available headroom
int room = skb_headroom(skb);  // = skb->data - skb->head

// Prepend a new header (extend data backward into headroom)
// Example: adding a VXLAN tunnel header
int vxlan_hdr_size = sizeof(struct udphdr) + sizeof(struct vxlanhdr);

if (skb_headroom(skb) < vxlan_hdr_size) {
    // Not enough headroom — must reallocate
    if (pskb_expand_head(skb, vxlan_hdr_size, 0, GFP_ATOMIC)) {
        kfree_skb(skb);
        return NET_RX_DROP;
    }
}

// Now advance data pointer backward (uses headroom)
skb_push(skb, vxlan_hdr_size);
// skb->data now points vxlan_hdr_size bytes earlier
// Fill in the new header:
struct vxlanhdr *vxh = (struct vxlanhdr *)skb->data;
vxh->vx_flags = htonl(VXLAN_HF_VNI);
vxh->vx_vni   = htonl(vni << 8);
```

### Tailroom Operations

```c
// Check available tailroom
int room = skb_tailroom(skb);  // = skb->end - skb->tail - sizeof(skb_shared_info)

// Append data to end of packet (extend tail forward)
void *new_data = skb_put(skb, append_size);
// skb->tail advances by append_size
// Returns pointer to newly appended region
memcpy(new_data, extra_bytes, append_size);
```

### `skb_pull` and `skb_push`

```c
// skb_pull: remove bytes from start of data (advance data pointer forward)
// Used as packet ascends the stack (stripping L2 header to expose L3)
void *skb_pull(struct sk_buff *skb, unsigned int len) {
    skb->len -= len;
    return skb->data += len;  // data pointer advances forward
}

// skb_push: add bytes to start of data (move data pointer backward into headroom)
// Used as packet descends the stack (prepending headers)
void *skb_push(struct sk_buff *skb, unsigned int len) {
    skb->data -= len;
    skb->len  += len;
    return skb->data;
}

// skb_put: add bytes to end of data (advance tail pointer)
void *skb_put(struct sk_buff *skb, unsigned int len) {
    void *tmp = skb_tail_pointer(skb);
    skb->tail += len;
    skb->len  += len;
    return tmp;
}

// skb_trim: remove bytes from end of data (retract tail pointer)
void skb_trim(struct sk_buff *skb, unsigned int len) {
    if (skb->len > len)
        __skb_trim(skb, len);
}
```

### The XDP Equivalent of Headroom Operations

In eBPF XDP programs, you adjust the packet head/tail using helper functions that modify the `xdp_md` directly:

```c
// Add headroom (grow packet backward — for adding encapsulation)
bpf_xdp_adjust_head(ctx, -sizeof(struct new_header));
// After this, ctx->data has moved backward by sizeof(struct new_header)
// You MUST re-read void *data = (void *)(long)ctx->data after this call

// Remove headroom (shrink packet forward — for stripping outer header)
bpf_xdp_adjust_head(ctx, +sizeof(struct outer_header));

// Extend packet tail (add trailer)
bpf_xdp_adjust_tail(ctx, +4);  // add 4 bytes at tail

// Shrink packet tail
bpf_xdp_adjust_tail(ctx, -4);  // remove 4 bytes from tail
```

---

## 18. C Implementations

### 18.1 — sk_buff Inspection with TC BPF

This program attaches to the TC ingress hook and prints detailed sk_buff metadata for every packet.

**`skb_inspect.bpf.c`**

```c
// SPDX-License-Identifier: GPL-2.0
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

char LICENSE[] SEC("license") = "GPL";

// Event structure sent to userspace
struct pkt_event {
    __u32 pid;           // PID of process (0 for softirq context)
    __u32 ifindex;       // interface index
    __u32 pkt_len;       // total packet length (sk_buff->len)
    __u32 data_len;      // non-linear data length (fragments)
    __u16 protocol;      // L3 protocol (ETH_P_IP, ETH_P_IPV6, etc.)
    __u16 headroom;      // available headroom in bytes
    __u8  pkt_type;      // PACKET_HOST, PACKET_BROADCAST, etc.
    __u8  ip_summed;     // checksum status
    __u8  pad[2];
    __u32 hash;          // flow hash
    __u32 mark;          // fwmark
    __u64 tstamp_ns;     // receive timestamp in nanoseconds
    __u8  src_mac[6];
    __u8  dst_mac[6];
    __be32 src_ip;       // IPv4 source (if IPv4)
    __be32 dst_ip;       // IPv4 destination (if IPv4)
    __be16 src_port;     // L4 source port (if TCP/UDP)
    __be16 dst_port;     // L4 destination port
    __u8   ip_proto;     // IP protocol number
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 1 << 22);  // 4 MB
} events SEC(".maps");

// Statistics counters (per-CPU for performance)
struct stats {
    __u64 total_packets;
    __u64 total_bytes;
    __u64 ipv4_packets;
    __u64 ipv6_packets;
    __u64 tcp_packets;
    __u64 udp_packets;
    __u64 dropped_events;
};

struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, struct stats);
} stats_map SEC(".maps");

// Ethernet header
struct ethhdr_local {
    unsigned char h_dest[6];
    unsigned char h_source[6];
    __be16 h_proto;
} __attribute__((packed));

// IPv4 header (minimal)
struct iphdr_local {
    __u8  ihl:4, version:4;
    __u8  tos;
    __be16 tot_len;
    __be16 id;
    __be16 frag_off;
    __u8  ttl;
    __u8  protocol;
    __be16 check;
    __be32 saddr;
    __be32 daddr;
} __attribute__((packed));

// TCP/UDP port header (first 4 bytes are src/dst port for both)
struct ports_hdr {
    __be16 sport;
    __be16 dport;
};

SEC("tc")
int skb_inspect(struct __sk_buff *skb)
{
    // Update statistics
    __u32 key = 0;
    struct stats *st = bpf_map_lookup_elem(&stats_map, &key);
    if (st) {
        st->total_packets++;
        st->total_bytes += skb->len;
    }

    // Reserve ring buffer space
    struct pkt_event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e) {
        if (st) st->dropped_events++;
        return TC_ACT_OK;
    }

    // Fill basic sk_buff metadata
    e->pid      = bpf_get_current_pid_tgid() >> 32;
    e->ifindex  = skb->ingress_ifindex;
    e->pkt_len  = skb->len;
    e->data_len = skb->data_len;  // bytes in page fragments
    e->protocol = bpf_ntohs(skb->protocol);
    e->pkt_type = skb->pkt_type;
    e->hash     = skb->hash;
    e->mark     = skb->mark;
    e->tstamp_ns = bpf_ktime_get_ns();

    // The sk_buff->data pointer (accessible as skb->data in __sk_buff)
    // Note: in TC BPF, skb->data/data_end give us the packet start
    void *data     = (void *)(long)skb->data;
    void *data_end = (void *)(long)skb->data_end;

    // Parse Ethernet header
    struct ethhdr_local *eth = data;
    if ((void *)(eth + 1) > data_end)
        goto submit;

    __builtin_memcpy(e->dst_mac, eth->h_dest,   6);
    __builtin_memcpy(e->src_mac, eth->h_source, 6);

    // Handle IPv4
    if (eth->h_proto == bpf_htons(0x0800)) {
        if (st) st->ipv4_packets++;

        struct iphdr_local *ip = (void *)(eth + 1);
        if ((void *)(ip + 1) > data_end)
            goto submit;

        e->src_ip  = ip->saddr;
        e->dst_ip  = ip->daddr;
        e->ip_proto = ip->protocol;

        if (st) {
            if (ip->protocol == 6)  st->tcp_packets++;
            if (ip->protocol == 17) st->udp_packets++;
        }

        // Parse TCP/UDP ports
        if (ip->protocol == 6 || ip->protocol == 17) {
            int ip_hdr_len = (ip->ihl & 0x0f) * 4;
            struct ports_hdr *ports = (void *)ip + ip_hdr_len;
            if ((void *)(ports + 1) <= data_end) {
                e->src_port = ports->sport;
                e->dst_port = ports->dport;
            }
        }
    } else if (eth->h_proto == bpf_htons(0x86DD)) {
        if (st) st->ipv6_packets++;
        // IPv6 parsing omitted for brevity
    }

submit:
    bpf_ringbuf_submit(e, 0);
    return TC_ACT_OK;  // Always pass — we're just observing
}
```

**`skb_inspect.c` (userspace loader)**

```c
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <net/if.h>
#include <linux/if_ether.h>
#include <bpf/libbpf.h>
#include <bpf/bpf.h>
#include "skb_inspect.skel.h"

struct pkt_event {
    __u32 pid;
    __u32 ifindex;
    __u32 pkt_len;
    __u32 data_len;
    __u16 protocol;
    __u16 headroom;
    __u8  pkt_type;
    __u8  ip_summed;
    __u8  pad[2];
    __u32 hash;
    __u32 mark;
    __u64 tstamp_ns;
    __u8  src_mac[6];
    __u8  dst_mac[6];
    __be32 src_ip;
    __be32 dst_ip;
    __be16 src_port;
    __be16 dst_port;
    __u8   ip_proto;
};

struct stats {
    __u64 total_packets;
    __u64 total_bytes;
    __u64 ipv4_packets;
    __u64 ipv6_packets;
    __u64 tcp_packets;
    __u64 udp_packets;
    __u64 dropped_events;
};

static volatile bool running = true;

static void sig_handler(int sig) { running = false; }

static const char *pkt_type_str(__u8 t) {
    switch (t) {
    case 0: return "HOST";
    case 1: return "BROADCAST";
    case 2: return "MULTICAST";
    case 3: return "OTHERHOST";
    case 4: return "OUTGOING";
    default: return "UNKNOWN";
    }
}

static const char *proto_str(__u16 proto) {
    switch (proto) {
    case 0x0800: return "IPv4";
    case 0x86DD: return "IPv6";
    case 0x0806: return "ARP";
    case 0x8100: return "VLAN";
    default: return "OTHER";
    }
}

static int handle_event(void *ctx, void *data, size_t sz)
{
    struct pkt_event *e = data;
    char src_ip[INET_ADDRSTRLEN], dst_ip[INET_ADDRSTRLEN];

    inet_ntop(AF_INET, &e->src_ip, src_ip, sizeof(src_ip));
    inet_ntop(AF_INET, &e->dst_ip, dst_ip, sizeof(dst_ip));

    printf("[%s] len=%-5u proto=%-6s "
           "%02x:%02x:%02x:%02x:%02x:%02x → "
           "%02x:%02x:%02x:%02x:%02x:%02x | "
           "%s:%-5u → %s:%-5u hash=0x%08x mark=0x%x\n",
           pkt_type_str(e->pkt_type),
           e->pkt_len,
           proto_str(e->protocol),
           e->src_mac[0], e->src_mac[1], e->src_mac[2],
           e->src_mac[3], e->src_mac[4], e->src_mac[5],
           e->dst_mac[0], e->dst_mac[1], e->dst_mac[2],
           e->dst_mac[3], e->dst_mac[4], e->dst_mac[5],
           src_ip, ntohs(e->src_port),
           dst_ip, ntohs(e->dst_port),
           e->hash, e->mark);

    return 0;
}

int main(int argc, char **argv)
{
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <interface>\n", argv[0]);
        return 1;
    }

    const char *ifname = argv[1];
    int ifindex = if_nametoindex(ifname);
    if (!ifindex) { perror("if_nametoindex"); return 1; }

    struct skb_inspect_bpf *skel = skb_inspect_bpf__open_and_load();
    if (!skel) { fprintf(stderr, "Failed to load BPF\n"); return 1; }

    // Attach to TC ingress using tc-bpf (requires iproute2 or libbpf TC API)
    DECLARE_LIBBPF_OPTS(bpf_tc_hook, tc_hook,
        .ifindex   = ifindex,
        .attach_point = BPF_TC_INGRESS);

    DECLARE_LIBBPF_OPTS(bpf_tc_opts, tc_opts,
        .handle   = 1,
        .priority = 1,
        .prog_fd  = bpf_program__fd(skel->progs.skb_inspect));

    bpf_tc_hook_create(&tc_hook);
    if (bpf_tc_attach(&tc_hook, &tc_opts)) {
        fprintf(stderr, "Failed to attach TC program\n");
        goto cleanup;
    }

    struct ring_buffer *rb = ring_buffer__new(
        bpf_map__fd(skel->maps.events), handle_event, NULL, NULL);
    if (!rb) { fprintf(stderr, "Failed to create ring buffer\n"); goto cleanup; }

    signal(SIGINT, sig_handler);
    signal(SIGTERM, sig_handler);

    printf("Monitoring %s (TC ingress). Ctrl-C to stop.\n\n", ifname);

    while (running) {
        ring_buffer__poll(rb, 100);
    }

    // Print statistics
    int stats_fd = bpf_map__fd(skel->maps.stats_map);
    int nr_cpus = libbpf_num_possible_cpus();
    struct stats all_stats[nr_cpus];
    __u32 key = 0;
    struct stats totals = {0};

    if (bpf_map_lookup_elem(stats_fd, &key, all_stats) == 0) {
        for (int i = 0; i < nr_cpus; i++) {
            totals.total_packets += all_stats[i].total_packets;
            totals.total_bytes   += all_stats[i].total_bytes;
            totals.ipv4_packets  += all_stats[i].ipv4_packets;
            totals.ipv6_packets  += all_stats[i].ipv6_packets;
            totals.tcp_packets   += all_stats[i].tcp_packets;
            totals.udp_packets   += all_stats[i].udp_packets;
        }
        printf("\n--- Stats ---\n");
        printf("Total packets: %llu (%llu bytes)\n",
               totals.total_packets, totals.total_bytes);
        printf("IPv4: %llu  IPv6: %llu\n",
               totals.ipv4_packets, totals.ipv6_packets);
        printf("TCP: %llu  UDP: %llu\n",
               totals.tcp_packets, totals.udp_packets);
    }

    ring_buffer__free(rb);
    bpf_tc_detach(&tc_hook, &tc_opts);
    bpf_tc_hook_destroy(&tc_hook);

cleanup:
    skb_inspect_bpf__destroy(skel);
    return 0;
}
```

---

### 18.2 — eBPF Map Benchmark in C

This program demonstrates and benchmarks all major map types:

```c
// map_bench.c — userspace benchmark for BPF map types
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>
#include <errno.h>
#include <bpf/bpf.h>
#include <bpf/libbpf.h>
#include <linux/bpf.h>

#define BENCH_ITERATIONS 1000000
#define MAX_ENTRIES      1024

static double ns_per_op(struct timespec *start, struct timespec *end,
                        int iterations)
{
    long long ns = (end->tv_sec - start->tv_sec) * 1000000000LL
                 + (end->tv_nsec - start->tv_nsec);
    return (double)ns / iterations;
}

// Create a map and benchmark lookup/update operations
static void bench_map(const char *name, enum bpf_map_type type,
                      int max_entries, int key_size, int value_size)
{
    union bpf_attr attr = {
        .map_type    = type,
        .key_size    = key_size,
        .value_size  = value_size,
        .max_entries = max_entries,
    };
    strncpy(attr.map_name, name, BPF_OBJ_NAME_LEN - 1);

    int fd = syscall(__NR_bpf, BPF_MAP_CREATE, &attr, sizeof(attr));
    if (fd < 0) {
        fprintf(stderr, "Failed to create %s map: %s\n", name, strerror(errno));
        return;
    }

    // Pre-populate the map
    for (int i = 0; i < max_entries; i++) {
        __u32 k = i;
        __u64 v = i * 42;
        bpf_map_update_elem(fd, &k, &v, BPF_ANY);
    }

    struct timespec t0, t1;
    __u32 key;
    __u64 value;

    // Benchmark lookup
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int i = 0; i < BENCH_ITERATIONS; i++) {
        key = i % max_entries;
        bpf_map_lookup_elem(fd, &key, &value);
    }
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double lookup_ns = ns_per_op(&t0, &t1, BENCH_ITERATIONS);

    // Benchmark update
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int i = 0; i < BENCH_ITERATIONS; i++) {
        key   = i % max_entries;
        value = i;
        bpf_map_update_elem(fd, &key, &value, BPF_ANY);
    }
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double update_ns = ns_per_op(&t0, &t1, BENCH_ITERATIONS);

    printf("%-25s  lookup: %6.1f ns/op   update: %6.1f ns/op\n",
           name, lookup_ns, update_ns);

    close(fd);
}

int main(void)
{
    printf("BPF Map Benchmark (%d iterations, %d entries)\n",
           BENCH_ITERATIONS, MAX_ENTRIES);
    printf("%-25s  %-20s  %-20s\n",
           "Map Type", "Lookup", "Update");
    printf("%s\n", "─────────────────────────────────────────────────────────");

    bench_map("ARRAY",          BPF_MAP_TYPE_ARRAY,        MAX_ENTRIES, 4, 8);
    bench_map("HASH",           BPF_MAP_TYPE_HASH,         MAX_ENTRIES, 4, 8);
    bench_map("LRU_HASH",       BPF_MAP_TYPE_LRU_HASH,     MAX_ENTRIES, 4, 8);
    bench_map("PERCPU_ARRAY",   BPF_MAP_TYPE_PERCPU_ARRAY, MAX_ENTRIES, 4, 8);
    bench_map("PERCPU_HASH",    BPF_MAP_TYPE_PERCPU_HASH,  MAX_ENTRIES, 4, 8);

    return 0;
}
```

**Compile and run:**

```bash
gcc -O2 -o map_bench map_bench.c -lbpf
sudo ./map_bench
```

**Typical output:**

```
BPF Map Benchmark (1000000 iterations, 1024 entries)
Map Type                   Lookup                 Update
─────────────────────────────────────────────────────────────
ARRAY                      lookup:   45.2 ns/op   update:   48.1 ns/op
HASH                       lookup:   82.7 ns/op   update:   95.3 ns/op
LRU_HASH                   lookup:   91.4 ns/op   update:  110.2 ns/op
PERCPU_ARRAY               lookup:   47.8 ns/op   update:   51.2 ns/op
PERCPU_HASH                lookup:   86.1 ns/op   update:   98.9 ns/op
```

---

### 18.3 — Register State Dump with kprobe

Demonstrate reading CPU register state from an eBPF kprobe:

```c
// reg_dump.bpf.c — dump CPU register state at any kernel function
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

char LICENSE[] SEC("license") = "GPL";

struct reg_state {
    __u64 ip;    // instruction pointer at probe point
    __u64 sp;    // stack pointer
    __u64 r0;    // RAX (return value register / first argument in some ABIs)
    __u64 r1;    // RDI (first argument — System V AMD64)
    __u64 r2;    // RSI (second argument)
    __u64 r3;    // RDX (third argument)
    __u64 r4;    // RCX (fourth argument)
    __u64 r5;    // R8  (fifth argument)
    __u64 r6;    // R9  (sixth argument)
    __u64 flags; // RFLAGS
    __u32 pid;
    char  comm[16];
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 1 << 20);
} regs_rb SEC(".maps");

// Probe sys_read — dump all argument registers
SEC("kprobe/ksys_read")
int dump_registers(struct pt_regs *ctx)
{
    struct reg_state *s = bpf_ringbuf_reserve(&regs_rb, sizeof(*s), 0);
    if (!s) return 0;

    // pt_regs fields correspond to the saved CPU state at the probe point
    s->ip    = PT_REGS_IP(ctx);    // RIP — instruction pointer
    s->sp    = PT_REGS_SP(ctx);    // RSP — stack pointer
    s->r1    = PT_REGS_PARM1(ctx); // RDI — fd argument
    s->r2    = PT_REGS_PARM2(ctx); // RSI — buf pointer
    s->r3    = PT_REGS_PARM3(ctx); // RDX — count argument
    s->flags = ctx->eflags;        // CPU flags (zero, carry, overflow, etc.)

    s->pid = bpf_get_current_pid_tgid() >> 32;
    bpf_get_current_comm(&s->comm, sizeof(s->comm));

    bpf_ringbuf_submit(s, 0);
    return 0;
}
```

---

## 19. Rust Implementations

### 19.1 — sk_buff Inspector with Aya

**Kernel-side: `skb-inspect-ebpf/src/main.rs`**

```rust
#![no_std]
#![no_main]

use aya_ebpf::{
    macros::{classifier, map},
    maps::{PerCpuArray, RingBuf},
    programs::TcContext,
    bindings::TC_ACT_OK,
    helpers::bpf_ktime_get_ns,
    EbpfContext,
};
use core::mem;

// Packet event (must match userspace definition)
#[repr(C)]
pub struct PacketEvent {
    pub len:       u32,
    pub data_len:  u32,   // bytes in page fragments
    pub protocol:  u16,   // big-endian ETH_P_IP etc.
    pub pkt_type:  u8,    // HOST/BROADCAST/MULTICAST/etc.
    pub pad:       u8,
    pub hash:      u32,
    pub mark:      u32,
    pub tstamp_ns: u64,
    pub src_ip:    u32,   // big-endian
    pub dst_ip:    u32,   // big-endian
    pub src_port:  u16,   // big-endian
    pub dst_port:  u16,   // big-endian
    pub ip_proto:  u8,
    pub pad2:      [u8; 3],
}

// Statistics counter
#[repr(C)]
#[derive(Copy, Clone)]
pub struct Stats {
    pub total:    u64,
    pub ipv4:     u64,
    pub ipv6:     u64,
    pub tcp:      u64,
    pub udp:      u64,
    pub dropped:  u64,
}

const ETH_P_IP:   u16 = 0x0800u16.to_be();
const ETH_P_IPV6: u16 = 0x86DDu16.to_be();
const ETH_HLEN: usize = 14;
const IP_HLEN:  usize = 20; // minimum

#[repr(C, packed)]
struct EthHdr {
    dst:   [u8; 6],
    src:   [u8; 6],
    proto: u16,  // big-endian
}

#[repr(C, packed)]
struct IpHdr {
    version_ihl: u8,
    tos:         u8,
    tot_len:     u16,
    id:          u16,
    frag_off:    u16,
    ttl:         u8,
    protocol:    u8,
    check:       u16,
    saddr:       u32,
    daddr:       u32,
}

#[repr(C, packed)]
struct PortsHdr {
    sport: u16,
    dport: u16,
}

#[map]
static EVENTS: RingBuf = RingBuf::with_byte_size(1 << 22, 0);

#[map]
static STATS: PerCpuArray<Stats> = PerCpuArray::with_max_entries(1, 0);

#[classifier]
pub fn skb_inspect(ctx: TcContext) -> i32 {
    match try_skb_inspect(ctx) {
        Ok(ret) => ret,
        Err(_)  => TC_ACT_OK as i32,
    }
}

#[inline(always)]
fn ptr_at<T>(ctx: &TcContext, offset: usize) -> Result<*const T, ()> {
    let start = ctx.data();
    let end   = ctx.data_end();
    if start + offset + mem::size_of::<T>() > end {
        return Err(());
    }
    Ok((start + offset) as *const T)
}

fn try_skb_inspect(ctx: TcContext) -> Result<i32, ()> {
    // Update statistics
    if let Some(stats) = unsafe { STATS.get_ptr_mut(0) } {
        unsafe {
            (*stats).total += 1;
        }
    }

    // Reserve ring buffer space
    let mut entry = EVENTS.reserve::<PacketEvent>(0).ok_or(())?;
    let e = entry.as_mut_ptr();

    unsafe {
        let evt = &mut *e;

        // Fill sk_buff-derived fields from TcContext
        evt.len      = ctx.len();
        evt.data_len = ctx.data_len();

        // Read raw __sk_buff fields via ctx offsets
        // These correspond to fields in struct __sk_buff
        let skb_proto: u16 = ctx.skb.protocol;    // network byte order
        let skb_hash:  u32 = ctx.skb.hash;
        let skb_mark:  u32 = ctx.skb.mark;
        let skb_type:  u32 = ctx.skb.pkt_type;

        evt.protocol  = skb_proto;
        evt.hash      = skb_hash;
        evt.mark      = skb_mark;
        evt.pkt_type  = skb_type as u8;
        evt.tstamp_ns = bpf_ktime_get_ns();

        // Parse Ethernet header
        let eth = ptr_at::<EthHdr>(&ctx, 0)?;

        if (*eth).proto == ETH_P_IP as u16 {
            // Parse IPv4
            let ip = ptr_at::<IpHdr>(&ctx, ETH_HLEN)?;

            evt.src_ip   = (*ip).saddr;
            evt.dst_ip   = (*ip).daddr;
            evt.ip_proto = (*ip).protocol;

            // Parse TCP/UDP ports
            let ihl = ((*ip).version_ihl & 0x0f) as usize * 4;
            if (*ip).protocol == 6 || (*ip).protocol == 17 {
                if let Ok(ports) = ptr_at::<PortsHdr>(&ctx, ETH_HLEN + ihl) {
                    evt.src_port = (*ports).sport;
                    evt.dst_port = (*ports).dport;
                }
            }

            if let Some(stats) = STATS.get_ptr_mut(0) {
                (*stats).ipv4 += 1;
                match (*ip).protocol {
                    6  => (*stats).tcp += 1,
                    17 => (*stats).udp += 1,
                    _  => {}
                }
            }
        }
    }

    entry.submit(0);
    Ok(TC_ACT_OK as i32)
}

#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {
    unsafe { core::hint::unreachable_unchecked() }
}
```

**Userspace: `skb-inspect/src/main.rs`**

```rust
use anyhow::Context;
use aya::{
    maps::{PerCpuArray, RingBuf},
    programs::{tc, SchedClassifier, TcAttachType},
    Ebpf,
};
use clap::Parser;
use std::net::Ipv4Addr;
use tokio::signal;

#[repr(C)]
struct PacketEvent {
    len:       u32,
    data_len:  u32,
    protocol:  u16,
    pkt_type:  u8,
    pad:       u8,
    hash:      u32,
    mark:      u32,
    tstamp_ns: u64,
    src_ip:    u32,
    dst_ip:    u32,
    src_port:  u16,
    dst_port:  u16,
    ip_proto:  u8,
    pad2:      [u8; 3],
}

#[repr(C)]
#[derive(Copy, Clone, Default)]
struct Stats {
    total:   u64,
    ipv4:    u64,
    ipv6:    u64,
    tcp:     u64,
    udp:     u64,
    dropped: u64,
}

#[derive(Debug, Parser)]
struct Opt {
    #[clap(short, long, default_value = "eth0")]
    iface: String,
}

fn pkt_type_str(t: u8) -> &'static str {
    match t {
        0 => "HOST",
        1 => "BCAST",
        2 => "MCAST",
        3 => "OTHER",
        _ => "?",
    }
}

fn proto_str(p: u16) -> &'static str {
    match u16::from_be(p) {
        0x0800 => "IPv4",
        0x86DD => "IPv6",
        0x0806 => "ARP",
        _      => "?",
    }
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let opt = Opt::parse();

    let mut ebpf = Ebpf::load(aya::include_bytes_aligned!(concat!(
        env!("OUT_DIR"),
        "/skb-inspect"
    )))?;

    // TC programs need a qdisc first
    tc::qdisc_add_clsact(&opt.iface)
        .context("failed to add clsact qdisc")?;

    let program: &mut SchedClassifier = ebpf
        .program_mut("skb_inspect")
        .unwrap()
        .try_into()?;
    program.load()?;
    program.attach(&opt.iface, TcAttachType::Ingress)?;

    let ring_buf_map = ebpf.map_mut("EVENTS").unwrap();
    let mut ring_buf = RingBuf::try_from(ring_buf_map)?;

    println!("Monitoring {} (TC ingress). Ctrl-C to stop.", opt.iface);
    println!("{:<6} {:<5} {:<6} {:<15} {:<15} {:<6} {:<6}",
             "TYPE", "LEN", "PROTO", "SRC", "DST", "SPORT", "DPORT");

    loop {
        tokio::select! {
            _ = signal::ctrl_c() => break,
            _ = tokio::time::sleep(tokio::time::Duration::from_millis(10)) => {
                while let Some(item) = ring_buf.next() {
                    if item.len() < std::mem::size_of::<PacketEvent>() {
                        continue;
                    }
                    let evt = unsafe {
                        &*(item.as_ptr() as *const PacketEvent)
                    };

                    let src = Ipv4Addr::from(u32::from_be(evt.src_ip));
                    let dst = Ipv4Addr::from(u32::from_be(evt.dst_ip));

                    println!("{:<6} {:<5} {:<6} {:<15} {:<15} {:<6} {:<6}",
                             pkt_type_str(evt.pkt_type),
                             evt.len,
                             proto_str(evt.protocol),
                             src.to_string(),
                             dst.to_string(),
                             u16::from_be(evt.src_port),
                             u16::from_be(evt.dst_port));
                }
            }
        }
    }

    // Print per-CPU stats
    let stats_map = ebpf.map("STATS").unwrap();
    let stats: PerCpuArray<_, Stats> = PerCpuArray::try_from(stats_map)?;

    if let Ok(per_cpu) = stats.get(&0, 0) {
        let mut total = Stats::default();
        for cpu_stats in per_cpu.iter() {
            total.total   += cpu_stats.total;
            total.ipv4    += cpu_stats.ipv4;
            total.ipv6    += cpu_stats.ipv6;
            total.tcp     += cpu_stats.tcp;
            total.udp     += cpu_stats.udp;
            total.dropped += cpu_stats.dropped;
        }
        println!("\n--- Stats ---");
        println!("Total: {}  IPv4: {}  IPv6: {}  TCP: {}  UDP: {}",
                 total.total, total.ipv4, total.ipv6,
                 total.tcp, total.udp);
    }

    Ok(())
}
```

---

### 19.2 — Register-Width Demonstration in Rust

This code demonstrates the exact behavior of register width arithmetic — what happens at 32-bit and 64-bit boundaries:

```rust
// register_width_demo.rs
// Compile with: rustc register_width_demo.rs -o reg_demo

fn main() {
    demonstrate_register_widths();
    demonstrate_overflow_behavior();
    demonstrate_pointer_as_integer();
    demonstrate_sign_extension();
}

fn demonstrate_register_widths() {
    println!("=== Register Width Limits ===\n");

    // 8-bit register (like AL on x86, W0[7:0] on ARM)
    let r8_max: u8 = u8::MAX;    // 0xFF = 255
    let r8_min: i8 = i8::MIN;    // -128
    println!("8-bit  unsigned max: {}  (0x{:02X})", r8_max, r8_max);
    println!("8-bit  signed   min: {}", r8_min);

    // 16-bit register
    let r16_max: u16 = u16::MAX; // 0xFFFF = 65535
    println!("16-bit unsigned max: {}  (0x{:04X})", r16_max, r16_max);

    // 32-bit register (like EAX on x86, W0 on ARM64, eBPF sub-register)
    let r32_max: u32 = u32::MAX; // 0xFFFF_FFFF = 4,294,967,295
    println!("32-bit unsigned max: {}  (0x{:08X})", r32_max, r32_max);
    println!("32-bit = {} GB max addressable", r32_max as f64 / 1e9);

    // 64-bit register (like RAX on x86, X0 on ARM64, eBPF R0)
    let r64_max: u64 = u64::MAX; // 0xFFFF_FFFF_FFFF_FFFF
    println!("64-bit unsigned max: {}  (0x{:016X})", r64_max, r64_max);
    println!("64-bit = {:.2e} (~18 exabytes max addressable)\n", r64_max as f64);
}

fn demonstrate_overflow_behavior() {
    println!("=== Overflow Behavior (wrapping arithmetic) ===\n");

    // 8-bit overflow (wraps around)
    let a: u8 = 255;
    let b: u8 = a.wrapping_add(1);  // In real CPU: ADD AL, 1 with 255 in AL
    println!("u8:  255 + 1 = {} (wrapped around, CF=1 on x86)", b);

    // 16-bit overflow
    let c: u16 = 65535;
    let d: u16 = c.wrapping_add(1);
    println!("u16: 65535 + 1 = {} (wrapped around)", d);

    // 32-bit overflow — this is the "4 GB limit" problem
    let e: u32 = 0xFFFF_FFFF;
    let f: u32 = e.wrapping_add(1);
    println!("u32: 0xFFFF_FFFF + 1 = {} (wrapped to 0)\n", f);

    // Signed overflow (undefined behavior in C! Rust panics in debug mode)
    let g: i32 = i32::MAX;  // 2,147,483,647
    let h: i32 = g.wrapping_add(1);  // -2,147,483,648 (becomes INT_MIN)
    println!("i32 signed: {} + 1 = {} (overflow! OF=1 on x86)\n", g, h);
}

fn demonstrate_pointer_as_integer() {
    println!("=== Pointers and Register Width ===\n");

    // A pointer IS a register-width integer
    let x: u64 = 42;
    let ptr: *const u64 = &x;
    let addr: usize = ptr as usize;

    println!("Variable x at address: 0x{:016X}", addr);
    println!("Address fits in {} bits: {}",
             usize::BITS,
             addr <= usize::MAX as usize);

    // This is why eBPF needs 64-bit registers:
    // Kernel addresses are 64-bit (e.g., 0xFFFF_8888_0000_0000 range on x86-64)
    let kernel_addr: u64 = 0xFFFF_8888_ABCD_1234;

    // Can we store this in a 32-bit register?
    let truncated: u32 = kernel_addr as u32;
    println!("\nKernel address: 0x{:016X}", kernel_addr);
    println!("Truncated to u32: 0x{:08X}  ← CORRUPTED! Classic BPF can't hold this",
             truncated);
    println!("Full u64 holds it:  0x{:016X}  ← eBPF can hold kernel pointers\n",
             kernel_addr);
}

fn demonstrate_sign_extension() {
    println!("=== Sign Extension (important for eBPF sub-register access) ===\n");

    // When writing a 32-bit value to a 64-bit register on x86-64,
    // the upper 32 bits are ZERO-extended (not sign-extended)
    // eBPF mirrors this behavior for 32-bit ALU operations

    let r32_val: u32 = 0x8000_0000;  // bit 31 set (negative if treated as i32)
    let zero_extended: u64 = r32_val as u64;
    let sign_extended: u64 = (r32_val as i32) as i64 as u64;

    println!("32-bit value:    0x{:08X}", r32_val);
    println!("Zero-extended:   0x{:016X}  ← x86-64 MOV EAX behavior", zero_extended);
    println!("Sign-extended:   0x{:016X}  ← (hypothetical, not x86 default)", sign_extended);

    // eBPF ALU32 operations zero-extend their results into the upper 32 bits
    // This is important when working with eBPF sub-register (32-bit) operations
    println!("\nIn eBPF: BPF_ALU32 operations zero-extend upper 32 bits");
    println!("In eBPF: BPF_ALU64 operations use all 64 bits\n");
}
```

---

### 19.3 — BPF Map Explorer in Rust

```rust
// map_explorer.rs — explore and dump BPF maps from userspace
// Uses the bpf crate (aya's bpf-sys or raw syscalls)

use std::fs;
use std::path::Path;
use std::io::{self, Read};

// BPF map info structure (matches kernel's struct bpf_map_info)
#[repr(C)]
#[derive(Debug, Default)]
struct BpfMapInfo {
    map_type:     u32,
    id:           u32,
    key_size:     u32,
    value_size:   u32,
    max_entries:  u32,
    map_flags:    u32,
    name:         [u8; 16],
    ifindex:      u32,
    btf_vmlinux_value_type_id: u32,
    netns_dev:    u64,
    netns_ino:    u64,
    btf_id:       u32,
    btf_key_type_id:   u32,
    btf_value_type_id: u32,
}

fn map_type_name(t: u32) -> &'static str {
    match t {
        0  => "UNSPEC",
        1  => "HASH",
        2  => "ARRAY",
        3  => "PROG_ARRAY",
        4  => "PERF_EVENT_ARRAY",
        5  => "PERCPU_HASH",
        6  => "PERCPU_ARRAY",
        7  => "STACK_TRACE",
        8  => "CGROUP_ARRAY",
        9  => "LRU_HASH",
        10 => "LRU_PERCPU_HASH",
        11 => "LPM_TRIE",
        12 => "ARRAY_OF_MAPS",
        13 => "HASH_OF_MAPS",
        14 => "DEVMAP",
        15 => "SOCKMAP",
        16 => "CPUMAP",
        17 => "XSKMAP",
        18 => "SOCKHASH",
        19 => "CGROUP_STORAGE",
        20 => "REUSEPORT_SOCKARRAY",
        21 => "PERCPU_CGROUP_STORAGE",
        22 => "QUEUE",
        23 => "STACK",
        24 => "SK_STORAGE",
        25 => "DEVMAP_HASH",
        26 => "STRUCT_OPS",
        27 => "RINGBUF",
        28 => "INODE_STORAGE",
        29 => "TASK_STORAGE",
        30 => "BLOOM_FILTER",
        _  => "UNKNOWN",
    }
}

fn list_bpf_maps() {
    println!("{:<6} {:<25} {:<10} {:<10} {:<10} {:<12}",
             "ID", "Type", "Key Size", "Val Size", "Max Ent", "Name");
    println!("{}", "─".repeat(75));

    // Iterate map IDs using BPF_MAP_GET_NEXT_ID syscall
    let mut id: u32 = 0;
    loop {
        // syscall(BPF_MAP_GET_NEXT_ID, &id, sizeof(u32))
        // In real code, use libbpf or aya bindings
        // Here we demonstrate the concept with /proc/sys/kernel/perf_event_paranoia check

        // For this demo, read from /sys/fs/bpf/ if maps are pinned
        break; // Placeholder — real implementation uses bpf() syscall
    }

    println!("(In production, use `bpftool map list` or the aya/libbpf library)");
}

fn analyze_map_types() {
    println!("\n=== BPF Map Type Analysis ===\n");

    struct MapTypeInfo {
        name:       &'static str,
        lookup:     &'static str,
        allocation: &'static str,
        thread_safe: &'static str,
        use_case:   &'static str,
    }

    let types = [
        MapTypeInfo {
            name: "ARRAY",
            lookup: "O(1) - array index",
            allocation: "Pre-allocated",
            thread_safe: "Lock-free (word-size ops)",
            use_case: "Dense integer-keyed counters",
        },
        MapTypeInfo {
            name: "HASH",
            lookup: "O(1) avg - jhash",
            allocation: "On-demand (kmalloc)",
            thread_safe: "Per-bucket spinlock",
            use_case: "Sparse/arbitrary keys",
        },
        MapTypeInfo {
            name: "PERCPU_ARRAY",
            lookup: "O(1) - array index",
            allocation: "Pre-allocated per CPU",
            thread_safe: "No contention (per-CPU)",
            use_case: "High-frequency counters",
        },
        MapTypeInfo {
            name: "LRU_HASH",
            lookup: "O(1) avg",
            allocation: "Fixed pool with LRU eviction",
            thread_safe: "Per-CPU LRU + global lock",
            use_case: "Connection tracking",
        },
        MapTypeInfo {
            name: "RINGBUF",
            lookup: "N/A (stream)",
            allocation: "Single ring (pre-allocated)",
            thread_safe: "Lock-free CAS on prod_pos",
            use_case: "Event streaming to userspace",
        },
    ];

    for t in &types {
        println!("Type: {}", t.name);
        println!("  Lookup:      {}", t.lookup);
        println!("  Allocation:  {}", t.allocation);
        println!("  Thread safe: {}", t.thread_safe);
        println!("  Use case:    {}", t.use_case);
        println!();
    }
}

fn main() {
    println!("BPF Map Explorer\n");
    list_bpf_maps();
    analyze_map_types();
}
```

---

## 20. Putting It All Together

### The Complete Picture: How a Packet Flows Through eBPF

Let's trace a single TCP packet from NIC to application, seeing where registers, maps, bytecode, and sk_buff all come into play:

```
1. NIC hardware DMA's raw bytes into ring buffer memory
   └── No CPU involvement yet

2. NIC raises interrupt → kernel IRQ handler → NAPI poll
   └── CPU registers in use: RSP (kernel stack), RIP (handler address)

3. XDP hook fires (if native XDP attached)
   ├── CPU JIT-executes eBPF bytecode compiled to x86-64 native instructions
   ├── eBPF R1 (→ RDI) = &xdp_md (the 5-field context struct)
   ├── eBPF R10 (→ RBP) = top of 512-byte eBPF stack
   ├── eBPF program reads xdp_md->data, xdp_md->data_end into R2, R3
   ├── Performs bounds-checked Ethernet+IP header parse
   ├── Looks up source IP in BPF_MAP_TYPE_LRU_HASH (blocklist)
   │   └── bpf_map_lookup_elem: function call, R1=&map, R2=&key → R0=result
   ├── Returns XDP_PASS (R0 = 2)
   └── sk_buff NOT YET ALLOCATED

4. sk_buff allocated
   ├── kmem_cache_alloc(skbuff_head_cache)
   ├── head, data, tail, end pointers set up
   ├── NET_SKB_PAD (64 bytes) headroom reserved
   └── Packet bytes already in DMA buffer — just set data pointer

5. TC BPF ingress hook fires (if TC program attached)
   ├── eBPF R1 = &__sk_buff (shadow of sk_buff, type-safe view)
   ├── eBPF program has access to: len, protocol, hash, mark, src/dst IP, ports
   ├── Can MODIFY packet (via bpf_skb_store_bytes, bpf_l3_csum_replace, etc.)
   ├── Can write to BPF maps (counters, flow tables, events)
   ├── Returns TC_ACT_OK to continue
   └── sk_buff continues to IP stack

6. IP stack processing
   ├── ip_rcv(): skb->network_header set, IP header validated
   ├── Routing: skb->dev, skb->sk determined
   └── tcp_v4_rcv(): skb->transport_header set

7. Socket delivery
   ├── sk_buff added to socket receive queue
   ├── Application wakes up (EPOLLIN on socket fd)
   └── Application read(): skb data copied to userspace buffer

8. sk_buff freed
   └── kfree_skb(): slab cache return, page fragment release, conntrack unref
```

### Where Each Concept Fits

| Concept | Where It Appears |
|---|---|
| **64-bit registers** | CPU executes JIT-compiled eBPF; context pointer fits in one register; timestamps fit in u64 |
| **eBPF R1–R5** | Function arguments to helper calls; R1 = context at program entry |
| **eBPF R6–R9** | Save context pointer across helper calls (callee-saved) |
| **R10 frame pointer** | Base for all stack variable access in eBPF |
| **JIT compilation** | eBPF bytecode → native x86/ARM64 before first execution |
| **Bytecode verifier** | Proves all pointer accesses are within bounds before JIT |
| **BPF maps** | Counters, blocklists, events, per-flow state |
| **RINGBUF map** | Stream packet events to userspace (step 5 above) |
| **PERCPU_ARRAY** | Per-interface packet counters without contention |
| **sk_buff head/data/tail/end** | Packet data pointer management through the stack |
| **sk_buff headroom** | Space for header prepending without reallocation |
| **XDP vs sk_buff** | XDP sees raw DMA bytes (step 3); TC sees sk_buff (step 5) |

---

*Document covers Linux kernel 5.x–6.x, libbpf 1.x, Aya 0.12.x.*
*C code targets the libbpf/CO-RE programming model with Clang/LLVM.*
*Rust code targets the Aya framework with the bpfel-unknown-none target.*

Here's your complete guide. Let me give you the core mental models for each concept:

---

**Registers** are the fastest storage on the planet — physically wired to the CPU's arithmetic units, accessed in 0 clock cycles. The *width* (8/16/32/64-bit) is how many bits they hold at once. A 32-bit register maxes out at 4 GB — which is why 32-bit systems had a 4 GB RAM limit and why classic BPF (32-bit registers) *could not hold kernel memory addresses* (which are 64-bit on modern systems). eBPF upgraded to 64-bit registers specifically to hold kernel pointers, 64-bit counters, and nanosecond timestamps.

**Interpreted bytecode** is a compact binary program designed for a software virtual machine — not the real CPU. The interpreter reads each instruction in a loop (`switch(opcode) { case ADD: ... case JMP: ... }`), which costs ~20–50 CPU instructions per eBPF instruction. That's why JIT is essential. **Native code** is the actual machine bytes the CPU's transistors decode and execute directly — an `add rdi, 42` becomes electrical signals in ~0.3 ns.

**Maps** are the kernel-resident data structures that give eBPF programs persistent state between invocations. The key types to remember: `ARRAY` (pre-allocated, O(1), use for dense keys), `HASH` (dynamic, O(1) avg, use for sparse/arbitrary keys), `PERCPU_*` (eliminate lock contention for hot counters), and `RINGBUF` (the modern zero-copy event-stream mechanism to userspace).

**sk_buff** is the kernel's packet envelope. The crucial insight: the `head/data/tail/end` four-pointer design means headers can be prepended or stripped by simply moving the `data` pointer — no memory copying. XDP fires *before* the sk_buff is even allocated, which is why it's 10–25× faster than netfilter rules for packet dropping.