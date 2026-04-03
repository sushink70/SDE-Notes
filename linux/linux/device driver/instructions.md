# eBPF Instructions: A Complete, In-Depth Guide
## From the 4096-Instruction Limit to 1 Million — Architecture, Encoding, Verification, and Mastery

---

> **"The verifier is not your enemy — it is the proof that your program is trustworthy."**

---

## Table of Contents

1. [What Is eBPF? — Foundations First](#1-what-is-ebpf--foundations-first)
2. [The eBPF Virtual Machine Architecture](#2-the-ebpf-virtual-machine-architecture)
3. [eBPF Instruction Encoding — The Bit-Level Truth](#3-ebpf-instruction-encoding--the-bit-level-truth)
4. [Instruction Classes — Complete Taxonomy](#4-instruction-classes--complete-taxonomy)
   - 4.1 ALU / ALU64 Instructions
   - 4.2 Jump Instructions (JMP / JMP32)
   - 4.3 Load Instructions (LD / LDX)
   - 4.4 Store Instructions (ST / STX)
   - 4.5 Atomic Instructions
5. [Registers — The 11 Soldiers](#5-registers--the-11-soldiers)
6. [The BPF Verifier — Deep Dive](#6-the-bpf-verifier--deep-dive)
7. [The 4096-Instruction Limit: Why It Existed](#7-the-4096-instruction-limit-why-it-existed)
8. [The 1 Million Instruction Limit: What Changed in 5.2](#8-the-1-million-instruction-limit-what-changed-in-52)
9. [Verifier Complexity and State Pruning](#9-verifier-complexity-and-state-pruning)
10. [BPF-to-BPF Function Calls (bpf2bpf)](#10-bpf-to-bpf-function-calls-bpf2bpf)
11. [BPF Loops — bounded_loops and the Loop Revolution](#11-bpf-loops--bounded_loops-and-the-loop-revolution)
12. [Tail Calls — Chaining Programs](#12-tail-calls--chaining-programs)
13. [BPF Maps — Memory Architecture](#13-bpf-maps--memory-architecture)
14. [Writing eBPF Programs in C — Full Examples](#14-writing-ebpf-programs-in-c--full-examples)
15. [Writing eBPF Programs in Rust (Aya)](#15-writing-ebpf-programs-in-rust-aya)
16. [Instruction Optimization Patterns](#16-instruction-optimization-patterns)
17. [Debugging Instructions — bpftool & llvm-objdump](#17-debugging-instructions--bpftool--llvm-objdump)
18. [Mental Models and Expert Intuition](#18-mental-models-and-expert-intuition)
19. [Quick Reference — All Opcodes](#19-quick-reference--all-opcodes)

---

## 1. What Is eBPF? — Foundations First

### Concept: What is a "Virtual Machine inside the Kernel"?

Imagine you want to run custom logic **inside** the Linux kernel — for example, to drop malicious packets, trace a system call, or profile CPU usage — **without** recompiling the kernel or loading a kernel module (which could crash the system).

**eBPF (extended Berkeley Packet Filter)** is the answer. It is a **register-based virtual machine** embedded in the Linux kernel that:

- Accepts programs written in a restricted instruction set
- **Verifies** them before execution (safety guarantee)
- **JIT-compiles** them to native machine code (performance guarantee)
- Runs them at kernel hook points (network, syscalls, tracing, security)

```
┌─────────────────────────────────────────────────────────────┐
│                      USER SPACE                             │
│                                                             │
│   Your C/Rust Program                                       │
│        │                                                    │
│        │  1. Compile BPF program → ELF bytecode            │
│        │  2. Load via bpf() syscall                        │
│        │  3. Attach to kernel hook                         │
└────────┼────────────────────────────────────────────────────┘
         │ bpf() syscall
┌────────▼────────────────────────────────────────────────────┐
│                      KERNEL SPACE                           │
│                                                             │
│  ┌──────────────┐    ┌─────────────┐    ┌───────────────┐  │
│  │  BPF Program │───▶│  VERIFIER   │───▶│  JIT Compiler │  │
│  │  (bytecode)  │    │  (safety)   │    │  (speed)      │  │
│  └──────────────┘    └─────────────┘    └───────┬───────┘  │
│                                                 │           │
│                                                 ▼           │
│                                        ┌────────────────┐  │
│                                        │ Hook Points:   │  │
│                                        │ - XDP (NIC)    │  │
│                                        │ - TC (traffic) │  │
│                                        │ - kprobe       │  │
│                                        │ - tracepoint   │  │
│                                        │ - cgroup       │  │
│                                        └────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Historical Context: cBPF vs eBPF

| Feature           | cBPF (Classic BPF, 1992)      | eBPF (extended, ~2014)              |
|-------------------|-------------------------------|-------------------------------------|
| Origin            | BSD packet filter             | Linux kernel 3.18+                  |
| Registers         | 2 (A, X accumulator)         | 11 (R0–R10)                         |
| Register width    | 32-bit                        | 64-bit                              |
| Instruction width | 8 bytes                       | 8 bytes (fixed-width)               |
| Maps              | None                          | Rich key-value stores               |
| Helper calls      | None                          | 200+ kernel helper functions        |
| Loops             | None                          | Bounded loops (kernel 5.3+)         |
| Use cases         | tcpdump, seccomp              | XDP, tracing, LSM, networking, etc. |

---

## 2. The eBPF Virtual Machine Architecture

### What is a "Register-Based VM"?

A **virtual machine (VM)** is a software-simulated CPU. In a **register-based VM**, computation happens by moving values between named registers and performing operations on them — exactly like real hardware (x86, ARM).

Contrast this with a **stack-based VM** (like the JVM), where operands are pushed/popped from a stack.

```
Register-Based (eBPF):            Stack-Based (JVM):
                                  
  r1 = 5                            PUSH 5
  r2 = 3                            PUSH 3
  r0 = r1 + r2    ← direct          IADD        ← implicit top-of-stack
                                    POP result
```

eBPF's register-based design maps **directly** to hardware registers on x86_64/ARM64/etc., enabling highly efficient JIT compilation.

### The eBPF Execution Model

```
                    eBPF EXECUTION FLOW
                    
  Hook Event        Program Entry         Execution            Return
  (e.g., packet) ──▶  (R1 = ctx ptr) ──▶  [instructions] ──▶  R0 = verdict
  
  
  MEMORY REGIONS ACCESSIBLE TO eBPF PROGRAM:
  
  ┌─────────────────────────────────────────────────────┐
  │  R10 ──▶ Stack Frame (512 bytes MAX, grows down)    │
  │          [R10 - 8]  [R10 - 16]  [R10 - 512]        │
  ├─────────────────────────────────────────────────────┤
  │  Maps   ──▶ Persistent kernel memory (key/value)    │
  ├─────────────────────────────────────────────────────┤
  │  Context ──▶ Event-specific data (R1 at entry)      │
  │             (e.g., struct xdp_md, struct sk_buff)   │
  ├─────────────────────────────────────────────────────┤
  │  Helpers ──▶ Kernel functions callable from BPF     │
  └─────────────────────────────────────────────────────┘
  
  WHAT eBPF CANNOT DO:
  ✗ Arbitrary pointer dereference (must be verified safe)
  ✗ Unbounded loops (until kernel 5.3 with bounds)
  ✗ Direct kernel function calls (except helpers)
  ✗ Global variables (until kernel 5.2 with .data/.rodata)
  ✗ Stack > 512 bytes
```

---

## 3. eBPF Instruction Encoding — The Bit-Level Truth

### The Fixed-Width 64-bit Instruction

Every eBPF instruction is exactly **8 bytes (64 bits)**. This fixed width is fundamental — it makes the verifier, JIT compiler, and disassembler simple and fast.

```
  63        48 47    44 43   40 39      32 31               0
  ┌───────────┬────────┬───────┬──────────┬──────────────────┐
  │  imm (32) │ offset │  src  │   dst    │    opcode (8)    │
  │           │  (16)  │  (4)  │   (4)    │                  │
  └───────────┴────────┴───────┴──────────┴──────────────────┘
  
  Bit layout in memory (little-endian, LSB first):
  
  Byte 0: opcode         [7:0]   — what to do
  Byte 1: dst_reg[3:0]   [11:8]  — destination register
          src_reg[7:4]   [15:12] — source register
  Byte 2: offset[7:0]    [23:16] — signed 16-bit offset (low byte)
  Byte 3: offset[15:8]   [31:24] — signed 16-bit offset (high byte)
  Byte 4: imm[7:0]       [39:32] — signed 32-bit immediate (low byte)
  Byte 5: imm[15:8]      [47:40]
  Byte 6: imm[23:16]     [55:48]
  Byte 7: imm[31:24]     [63:56]
```

### Opcode Breakdown — The 8-Bit Opcode Field

The 8-bit opcode encodes THREE sub-fields:

```
  OPCODE BYTE (8 bits):
  
  7     3 2   1 0
  ┌──────┬─────┬───┐
  │ code │ src │cls│
  │ (5)  │ (1) │(3)│
  └──────┴─────┴───┘
  
  cls (bits [2:0]) — instruction CLASS:
    0x00 = LD    (load)
    0x01 = LDX   (load from memory via register)
    0x02 = ST    (store immediate to memory)
    0x03 = STX   (store register to memory)
    0x04 = ALU   (32-bit arithmetic/logic)
    0x05 = JMP   (64-bit jumps + calls)
    0x06 = JMP32 (32-bit conditional jumps)  [added in kernel 4.14]
    0x07 = ALU64 (64-bit arithmetic/logic)
  
  src (bit [3]) — SOURCE type (for ALU/JMP):
    0 = BPF_K  (use immediate value `imm`)
    1 = BPF_X  (use source register `src_reg`)
  
  code (bits [7:3]) — OPERATION code:
    (meaning depends on class — see below)
```

### The Special Wide Instruction (16 bytes)

The `BPF_LD | BPF_IMM | BPF_DW` instruction is the **only 16-byte instruction** — it loads a 64-bit immediate. It uses two consecutive 8-byte slots:

```
  Wide Instruction (BPF_LD_IMM64):
  
  Instruction 1 (bytes 0–7):
  ┌──────────┬─────┬─────┬────────┬────────────────────┐
  │  imm_lo  │ src │ dst │ offset │    0x18 (opcode)   │
  │ (32-bit) │     │     │  = 0   │                    │
  └──────────┴─────┴─────┴────────┴────────────────────┘
  
  Instruction 2 (bytes 8–15):  ← "pseudo" instruction
  ┌──────────┬─────┬─────┬────────┬────────────────────┐
  │  imm_hi  │  0  │  0  │   0    │    0x00 (zero)     │
  │ (32-bit) │     │     │        │                    │
  └──────────┴─────┴─────┴────────┴────────────────────┘
  
  Result: dst_reg = (imm_hi << 32) | (uint32_t)imm_lo
  
  ⚠️  This counts as 2 instructions toward the program limit!
```

### C Structure for an eBPF Instruction

```c
/* From linux/bpf.h */
struct bpf_insn {
    __u8    code;        /* opcode: class + source + operation */
    __u8    dst_reg:4;   /* destination register (0-10) */
    __u8    src_reg:4;   /* source register (0-10) */
    __s16   off;         /* signed 16-bit offset (-32768 to 32767) */
    __s32   imm;         /* signed 32-bit immediate value */
};
/* sizeof(struct bpf_insn) == 8 bytes — always */
```

---

## 4. Instruction Classes — Complete Taxonomy

### 4.1 ALU / ALU64 Instructions

**Concept — ALU (Arithmetic Logic Unit):** The part of a CPU that performs math and bitwise operations. `ALU` operates on 32-bit values (zeroing the upper 32 bits of dst). `ALU64` operates on the full 64 bits.

```
  ALU OPERATION FORMAT:
  
  Register mode (BPF_X):  dst_reg OP= src_reg
  Immediate mode (BPF_K): dst_reg OP= imm32
  
  ┌─────────────────────────────────────────────────────────────┐
  │  ALU Operations (code field [7:4])                         │
  ├────────────┬───────────┬──────────────────────────────────┤
  │  Code      │  Mnemonic │  Operation                       │
  ├────────────┼───────────┼──────────────────────────────────┤
  │  0x00      │  ADD      │  dst += src/imm                  │
  │  0x10      │  SUB      │  dst -= src/imm                  │
  │  0x20      │  MUL      │  dst *= src/imm                  │
  │  0x30      │  DIV      │  dst /= src/imm (unsigned)       │
  │  0x40      │  OR       │  dst |= src/imm                  │
  │  0x50      │  AND      │  dst &= src/imm                  │
  │  0x60      │  LSH      │  dst <<= src/imm                 │
  │  0x70      │  RSH      │  dst >>= src/imm (logical)       │
  │  0x80      │  NEG      │  dst = -dst (src field = 0)      │
  │  0x90      │  MOD      │  dst %= src/imm (unsigned)       │
  │  0xa0      │  XOR      │  dst ^= src/imm                  │
  │  0xb0      │  MOV      │  dst = src/imm                   │
  │  0xc0      │  ARSH     │  dst >>= src/imm (arithmetic)    │
  │  0xd0      │  END      │  byte-swap (endianness)          │
  └────────────┴───────────┴──────────────────────────────────┘
  
  Arithmetic shift (ARSH) vs Logical shift (RSH):
  
  Value: 0x8000000000000000 (most significant bit set = negative)
  
  RSH  (logical):  fills with 0s:  0x4000000000000000
  ARSH (arithmetic): fills with 1s: 0xC000000000000000
                                     ↑ preserves sign
```

**Complete opcode construction example:**

```c
/* ALU64 ADD dst=r0, src=r1:   dst += src */
/* opcode = class(ALU64=0x07) | src(BPF_X=0x08) | code(ADD=0x00) */
/* opcode = 0x07 | 0x08 | 0x00 = 0x0f */
struct bpf_insn add_r0_r1 = {
    .code    = BPF_ALU64 | BPF_ADD | BPF_X,  /* 0x07 | 0x00 | 0x08 = 0x0f */
    .dst_reg = BPF_REG_0,
    .src_reg = BPF_REG_1,
    .off     = 0,
    .imm     = 0,
};

/* ALU64 ADD dst=r0, imm=42:   dst += 42 */
struct bpf_insn add_r0_42 = {
    .code    = BPF_ALU64 | BPF_ADD | BPF_K,  /* 0x07 | 0x00 | 0x00 = 0x07 */
    .dst_reg = BPF_REG_0,
    .src_reg = 0,
    .off     = 0,
    .imm     = 42,
};
```

**Endianness (END) instruction — special case:**

```
  BPF_END converts between byte orders:
  
  BPF_TO_LE (imm=16/32/64): convert dst to little-endian
  BPF_TO_BE (imm=16/32/64): convert dst to big-endian
  
  Example: r0 = 0x0102030405060708
  
  After BPF_ALU | BPF_END | BPF_TO_BE, imm=32:
  r0 = 0x0000000005060708 ... actually operates on lower 32 bits:
       lower 32: 0x05060708 → BE32 → 0x08070605
  r0 = 0x0000000008070605
  
  Use case: network packets arrive in big-endian (network byte order).
  Use bpf_htons/bpf_htonl (which compile to BPF_END) to convert.
```

### 4.2 Jump Instructions (JMP / JMP32)

**Concept — What is a "jump"?** In a linear instruction stream, a jump (branch) changes the program counter (PC) to a different instruction. In eBPF, jumps use a **signed 16-bit offset** — the number of instructions to skip **forward or backward** from the instruction **after** the jump.

```
  JUMP FORMAT:
  
  if (dst OP src/imm) goto PC + off + 1
                                    ↑
                             "off" is relative to the NEXT instruction
  
  Example (off = +3):
  
  PC=0:  JEQ r1, 5, off=3    ← if r1 == 5, jump to PC=4
  PC=1:  instruction A        ← only reached if r1 != 5
  PC=2:  instruction B
  PC=3:  instruction C
  PC=4:  instruction D        ← jump target
  PC=5:  instruction E
  
  ┌─────────────────────────────────────────────────────────────┐
  │  Jump Operations (code field)                              │
  ├────────────┬───────────┬──────────────────────────────────┤
  │  Code      │  Mnemonic │  Condition                       │
  ├────────────┼───────────┼──────────────────────────────────┤
  │  0x00      │  JA       │  always (unconditional), JMP only│
  │  0x10      │  JEQ      │  dst == src/imm                  │
  │  0x20      │  JGT      │  dst >  src/imm (unsigned)       │
  │  0x30      │  JGE      │  dst >= src/imm (unsigned)       │
  │  0x40      │  JSET     │  dst &  src/imm != 0             │
  │  0x50      │  JNE      │  dst != src/imm                  │
  │  0x60      │  JSGT     │  dst >  src/imm (signed)         │
  │  0x70      │  JSGE     │  dst >= src/imm (signed)         │
  │  0x80      │  CALL     │  call helper/function (JMP only) │
  │  0x90      │  EXIT     │  return R0 (JMP only)            │
  │  0xa0      │  JLT      │  dst <  src/imm (unsigned)       │
  │  0xb0      │  JLE      │  dst <= src/imm (unsigned)       │
  │  0xc0      │  JSLT     │  dst <  src/imm (signed)         │
  │  0xd0      │  JSLE     │  dst <= src/imm (signed)         │
  └────────────┴───────────┴──────────────────────────────────┘
  
  JMP  = 64-bit comparison
  JMP32 = 32-bit comparison (only lower 32 bits compared)
  
  ⚠️  Backward jumps (off < 0) are ONLY allowed with the verifier's
      bounded loop support (kernel 5.3+). Earlier kernels reject them
      unless in the context of a static jump.
```

**CALL instruction — Helper Functions:**

```
  BPF_CALL encoding:
  
  opcode = BPF_JMP | BPF_CALL   (0x85)
  imm    = helper function ID
  
  Before call:   R1-R5 = arguments (up to 5)
  After call:    R0 = return value
                 R1-R5 = destroyed (caller-saved)
                 R6-R9 = preserved (callee-saved)
  
  Example: call bpf_map_lookup_elem (helper #1)
  
  struct bpf_insn call_lookup = {
      .code = BPF_JMP | BPF_CALL,
      .imm  = BPF_FUNC_map_lookup_elem,  /* = 1 */
  };
```

### 4.3 Load Instructions (LD / LDX)

**Concept — "Load":** Copy data FROM memory INTO a register.

```
  LOAD SIZE field (bits [4:3] of opcode):
  ┌───────┬────────────────────────────────┐
  │ Value │ Size                           │
  ├───────┼────────────────────────────────┤
  │ 0x00  │ W  = 32-bit word               │
  │ 0x08  │ H  = 16-bit halfword           │
  │ 0x10  │ B  = 8-bit byte                │
  │ 0x18  │ DW = 64-bit doubleword         │
  └───────┴────────────────────────────────┘
  
  LOAD MODE field (bits [7:5] of opcode):
  ┌───────┬──────────────────────────────────────────┐
  │ Value │ Mode                                     │
  ├───────┼──────────────────────────────────────────┤
  │ 0x00  │ IMM  = load immediate                    │
  │ 0x20  │ ABS  = absolute offset (cBPF compat)     │
  │ 0x40  │ IND  = indirect (cBPF compat)            │
  │ 0x60  │ MEM  = load from memory [src + offset]   │
  │ 0xc0  │ ATOMIC = atomic operations               │
  └───────┴──────────────────────────────────────────┘
  
  LDX MEM (most common):
  dst_reg = *(size *)(src_reg + offset)
  
  Example: load 4 bytes from [r1 + 12] into r0
  BPF_LDX_MEM(BPF_W, BPF_REG_0, BPF_REG_1, 12)
  
  This reads the 32-bit word at address (r1 + 12) into r0.
  
  ASCII Memory Diagram:
  
  r1 ──▶ ┌──────────┐  offset 0
         │          │
         │          │  offset 4
         │          │
         │          │  offset 8
         │ [4 bytes]│  offset 12  ◀── reads this
         │          │  offset 16
         └──────────┘
```

### 4.4 Store Instructions (ST / STX)

**Concept — "Store":** Copy data FROM a register/immediate INTO memory.

```
  ST  (store immediate): *(size *)(dst_reg + offset) = imm32
  STX (store register):  *(size *)(dst_reg + offset) = src_reg
  
  Example: store r2 (64-bit) at [r10 - 8]   (onto stack)
  BPF_STX_MEM(BPF_DW, BPF_REG_10, BPF_REG_2, -8)
  
  Stack layout after this instruction:
  
  r10 (frame pointer) ──▶ ┌──────────┐  FP + 0  (invalid, above frame)
                          ├──────────┤  FP - 8  ◀── [r2 stored here]
                          │  r2 val  │
                          ├──────────┤  FP - 16
                          │  ...     │
                          ├──────────┤  FP - 512
                          └──────────┘  (maximum stack depth)
  
  ⚠️  Stack accesses MUST be within [FP-512, FP-1].
      The verifier tracks every stack slot's initialization state.
      Reading uninitialized stack memory → verifier REJECTS program.
```

### 4.5 Atomic Instructions

**Concept — "Atomic":** An operation that completes in one indivisible step, with no other CPU able to observe an intermediate state. Critical for multi-core safety.

```
  Added in kernel 5.12 (STX + BPF_ATOMIC mode):
  
  ┌─────────────────┬────────────────────────────────────────┐
  │  imm field      │  Atomic Operation                      │
  ├─────────────────┼────────────────────────────────────────┤
  │  BPF_ADD        │  atomic_add(dst+off, src)              │
  │  BPF_OR         │  atomic_or(dst+off, src)               │
  │  BPF_AND        │  atomic_and(dst+off, src)              │
  │  BPF_XOR        │  atomic_xor(dst+off, src)              │
  │  BPF_ADD|FETCH  │  src = atomic_fetch_add(dst+off, src)  │
  │  BPF_XCHG       │  src = atomic_xchg(dst+off, src)       │
  │  BPF_CMPXCHG    │  R0 = atomic_cmpxchg(dst+off, R0, src) │
  └─────────────────┴────────────────────────────────────────┘
  
  BPF_CMPXCHG (Compare-and-Exchange) logic:
  
  if (*(dst + off) == R0) {
      *(dst + off) = src;
      // R0 now holds the old value (whether swap happened or not)
  } else {
      R0 = *(dst + off);  // load current value into R0
  }
  
  This is the foundation of lock-free data structures.
```

---

## 5. Registers — The 11 Soldiers

Every eBPF program has access to 11 registers, each 64-bit wide.

```
  eBPF REGISTER FILE
  
  ┌─────┬─────────────┬────────────────────────────────────────────┐
  │ Reg │  Role       │  Description                               │
  ├─────┼─────────────┼────────────────────────────────────────────┤
  │ R0  │ Return val  │ Return value from helpers; program result  │
  │ R1  │ Arg 1       │ At entry: pointer to context (ctx)         │
  │ R2  │ Arg 2       │ Function argument 2                        │
  │ R3  │ Arg 3       │ Function argument 3                        │
  │ R4  │ Arg 4       │ Function argument 4                        │
  │ R5  │ Arg 5       │ Function argument 5                        │
  │ R6  │ Callee-saved│ Preserved across BPF helper calls          │
  │ R7  │ Callee-saved│ Preserved across BPF helper calls          │
  │ R8  │ Callee-saved│ Preserved across BPF helper calls          │
  │ R9  │ Callee-saved│ Preserved across BPF helper calls          │
  │ R10 │ Frame ptr   │ READ-ONLY stack frame pointer              │
  └─────┴─────────────┴────────────────────────────────────────────┘
  
  CALLING CONVENTION (for helper functions):
  
  Before call:
  R1 ──▶ arg1  ┐
  R2 ──▶ arg2  │
  R3 ──▶ arg3  ├── Set by programmer
  R4 ──▶ arg4  │
  R5 ──▶ arg5  ┘
  
  After call:
  R0 ──▶ return value
  R1-R5 ──▶ DESTROYED (do not rely on them)
  R6-R9 ──▶ PRESERVED (safe to use across calls)
  
  x86_64 JIT mapping:
  ┌──────┬───────────────────┐
  │  BPF │  x86_64 register  │
  ├──────┼───────────────────┤
  │  R0  │  rax              │
  │  R1  │  rdi              │
  │  R2  │  rsi              │
  │  R3  │  rdx              │
  │  R4  │  rcx              │
  │  R5  │  r8               │
  │  R6  │  rbx              │
  │  R7  │  r13              │
  │  R8  │  r14              │
  │  R9  │  r15              │
  │  R10 │  rbp              │
  └──────┴───────────────────┘
  This 1-to-1 mapping is why JIT compilation is so fast.
```

---

## 6. The BPF Verifier — Deep Dive

### What Is the Verifier?

The **BPF verifier** is a static analysis engine inside the kernel that executes before any BPF program runs. It **proves** that every possible execution path of the program is safe.

Think of it as a theorem prover — it does not run your code, it **reasons** about all possible states your code can reach.

```
  VERIFIER PIPELINE:
  
  BPF bytecode
       │
       ▼
  ┌──────────────────────────────────────────┐
  │  PHASE 1: Structural Check               │
  │  • Count instructions (≤ limit)          │
  │  • No backward jumps (pre-5.3)           │
  │  • All jumps land on valid instructions  │
  │  • Program ends with EXIT                │
  │  • No unreachable code                   │
  └──────────────────┬───────────────────────┘
                     │ pass
                     ▼
  ┌──────────────────────────────────────────┐
  │  PHASE 2: DAG (Directed Acyclic Graph)   │
  │  Check                                   │
  │  • Build control flow graph (CFG)        │
  │  • Verify no cycles (pre-5.3)            │
  │  • All paths eventually reach EXIT       │
  └──────────────────┬───────────────────────┘
                     │ pass
                     ▼
  ┌──────────────────────────────────────────┐
  │  PHASE 3: Abstract Interpretation        │
  │  (Symbolic Execution of ALL paths)       │
  │                                          │
  │  For every instruction on every path:    │
  │  • Track register types:                 │
  │    - NOT_INIT (unread register)          │
  │    - SCALAR_VALUE (unknown number)       │
  │    - PTR_TO_MAP_VALUE                    │
  │    - PTR_TO_STACK                        │
  │    - PTR_TO_CTX                          │
  │    - PTR_TO_PACKET                       │
  │    etc.                                  │
  │  • Track value ranges (min, max)         │
  │  • Check memory accesses are in-bounds   │
  │  • Check null pointer dereferences       │
  │  • Check stack initialization            │
  │  • Verify helper argument types          │
  └──────────────────┬───────────────────────┘
                     │ pass
                     ▼
              Program ACCEPTED
              (loaded into kernel)
```

### Abstract Interpretation — The Core Concept

**Concept:** Instead of running your program with real values, the verifier runs it with **symbolic values** (abstract types + ranges). Each register has a tracked state.

```
  REGISTER STATE EXAMPLE:
  
  Code:
  r1 = ctx;           // r1: PTR_TO_CTX
  r2 = *(r1 + 0);     // load from context → r2: SCALAR_VALUE, range=[0, U64_MAX]
  if (r2 > 100) goto err;
  // Verifier now knows: r2 in [0, 100]
  r3 = r2 * 4;        // r3 in [0, 400]
  r4 = map_ptr + r3;  // r4: PTR_TO_MAP_VALUE with known offset range
  // Safe to access r4[0..3] because 400 < map_size
  
  REGISTER STATE TRACKING:
  
  After "if (r2 > 100) goto err":
  
  TRUE branch  (r2 > 100): r2 ∈ [101, U64_MAX]  → goto err
  FALSE branch (r2 ≤ 100): r2 ∈ [0, 100]        → continue
  
  This is called "range inference" or "tnum tracking"
  (tnum = tracked number, stores known bits + unknown bits).
```

### The tnum (Tracked Number) System

The verifier uses a clever 128-bit structure to track which bits of a value are known:

```
  struct tnum {
      u64 value;   // known bit values
      u64 mask;    // 1 = unknown bit, 0 = known bit
  };
  
  Example:
  mask  = 0xFFFFFFFFFFFFFF00   (lower 8 bits known)
  value = 0x0000000000000042   (lower 8 bits = 0x42 = 66)
  
  Meaning: value is (??? ... ??? 01000010) in binary
                                └────────┘
                                  known: 0x42
  
  TNUM OPERATIONS:
  
  AND: result.mask = a.mask | b.mask | (a.value & b.mask) | (b.value & a.mask)
       ... (complex but enables precise range narrowing)
  
  This allows the verifier to track, e.g., that after masking
  with 0xFF, a value is guaranteed to be in [0, 255].
```

---

## 7. The 4096-Instruction Limit: Why It Existed

### The Original Design Philosophy (pre-kernel 5.2)

When eBPF was extended from cBPF, the kernel developers imposed a **hard limit of 4096 instructions** (BPF_MAXINSNS = 4096). This limit existed for several interrelated reasons:

```
  REASONS FOR THE 4096 LIMIT:
  
  ┌────────────────────────────────────────────────────────────┐
  │  1. VERIFIER COMPLEXITY EXPLOSION                          │
  │                                                            │
  │  The verifier uses "state space exploration":             │
  │  For a program with N instructions and branching,         │
  │  the number of execution paths can be EXPONENTIAL.        │
  │                                                            │
  │  Without pruning:                                          │
  │    4 branches → 2^4 = 16 paths                            │
  │    8 branches → 2^8 = 256 paths                           │
  │    16 branches → 2^16 = 65536 paths                       │
  │                                                            │
  │  With 4096 instructions and lots of branches,             │
  │  verification could already take seconds.                  │
  │  Larger programs → potentially infinite verification time. │
  ├────────────────────────────────────────────────────────────┤
  │  2. DENIAL-OF-SERVICE PREVENTION                          │
  │                                                            │
  │  Any user with CAP_NET_ADMIN (or CAP_SYS_ADMIN) can       │
  │  load a BPF program. A malicious program designed to       │
  │  maximize verifier work could hang the kernel for          │
  │  minutes. 4096 instructions bounded this attack surface.  │
  ├────────────────────────────────────────────────────────────┤
  │  3. STACK SIZE LIMIT INTERACTION                          │
  │                                                            │
  │  eBPF stack is 512 bytes. This limits program complexity   │
  │  organically — functions can't recurse, local data        │
  │  is limited, so 4096 instructions was considered enough.  │
  ├────────────────────────────────────────────────────────────┤
  │  4. "SIMPLICITY OF PROOF"                                 │
  │                                                            │
  │  Original design: BPF programs should be simple filters.  │
  │  Not general-purpose computation engines. 4096 was        │
  │  "enough for a filter, too few for an attack."            │
  └────────────────────────────────────────────────────────────┘
```

### The Pain Points — What Was Impossible with 4096

Real-world use cases that hit the limit:

```
  PROBLEM SCENARIOS (pre-5.2):
  
  1. Large XDP programs with many protocol parsers:
     Parse Ethernet → IPv4/IPv6 → TCP/UDP/ICMP → 
     HTTP/DNS/QUIC → ... 
     Each parser ≈ 100-300 instructions. 
     4 protocols × 300 instructions = 1200 instructions.
     Add error handling, maps, helpers → easily > 4096.
  
  2. Observability programs (tracing):
     Capture kernel function arguments, format them,
     write to ring buffer, handle errors.
     Complex struct traversal alone → hundreds of instructions.
  
  3. Security programs (LSM hooks):
     Parse process credentials, check against policy,
     log decision, update counters → easily 2000+ instructions.
  
  THE WORKAROUND: Tail Calls
  
  Since each tail call creates a new program with its own
  4096-instruction budget:
  
  ┌────────────┐  tail_call  ┌────────────┐  tail_call  ┌────────────┐
  │  Prog A    │────────────▶│  Prog B    │────────────▶│  Prog C    │
  │ (4096 max) │             │ (4096 max) │             │ (4096 max) │
  └────────────┘             └────────────┘             └────────────┘
  
  Max chain depth = 33 tail calls → 33 × 4096 ≈ 135,168 instructions
  But: cumbersome to program, hard to share state,
       performance overhead from each tail call.
```

---

## 8. The 1 Million Instruction Limit: What Changed in 5.2

### The Kernel 5.2 Changes (July 2019)

The commit `c04c0d2b968ac` by Alexei Starovoitov raised `BPF_COMPLEXITY_LIMIT_INSNS` from **4096 to 1,000,000 (1M)**. But this was **not just a number change** — it required fundamental improvements to the verifier's state pruning algorithm to make verification of large programs feasible.

```
  WHAT CHANGED IN KERNEL 5.2:
  
  ┌────────────────────────────────────────────────────────────┐
  │  1. BPF_COMPLEXITY_LIMIT_INSNS: 4096 → 1,000,000          │
  │     (in kernel/bpf/verifier.c)                             │
  ├────────────────────────────────────────────────────────────┤
  │  2. IMPROVED STATE PRUNING                                  │
  │                                                            │
  │  The verifier caches "explored states" at branch points.   │
  │  If the current state is a SUBSET of an already-verified   │
  │  state (more constrained), we can prune the search.        │
  │                                                            │
  │  Old pruning: simple equality check (state A == state B)   │
  │  New pruning: subset check (state A ⊆ state B)             │
  │                                                            │
  │  This dramatically reduces the number of states the        │
  │  verifier must explore for large programs.                 │
  ├────────────────────────────────────────────────────────────┤
  │  3. EQUIVALENT STATE DETECTION                             │
  │                                                            │
  │  Also in 5.2: ability to detect "equivalent" program       │
  │  states even when register values differ, if they differ   │
  │  in ways that don't affect safety (e.g., both are         │
  │  scalar values with sufficient range constraints).        │
  ├────────────────────────────────────────────────────────────┤
  │  4. SECURITY: STILL REQUIRES CAP_SYS_ADMIN (or            │
  │     CAP_BPF in 5.8+) for programs with > 4096 insns        │
  │                                                            │
  │  Unprivileged BPF (kernel.unprivileged_bpf_disabled = 0)  │
  │  STILL has a 4096-instruction limit!                       │
  │  The 1M limit applies only to privileged BPF programs.    │
  └────────────────────────────────────────────────────────────┘
```

### The Actual Constant in the Kernel

```c
/* linux/kernel/bpf/verifier.c */

/* Before 5.2: */
#define BPF_COMPLEXITY_LIMIT_INSNS      4096

/* After 5.2: */
#define BPF_COMPLEXITY_LIMIT_INSNS      1000000 /* 1M */

/* The per-program instruction limit (separate from complexity limit): */
/* linux/include/linux/bpf.h */
#define BPF_MAXINSNS                    4096    /* still 4096 for cBPF compat */

/* But for eBPF specifically: */
/* The program insn_cnt can be up to BPF_COMPLEXITY_LIMIT_INSNS */
```

**Critical distinction:** There are TWO related but different limits:
- **`BPF_MAXINSNS` (4096):** The limit for cBPF programs and a legacy constant
- **`BPF_COMPLEXITY_LIMIT_INSNS` (1M):** The actual verifier limit for eBPF programs

```
  TWO DISTINCT LIMITS:
  
  ┌─────────────────────────────────────────────────────────┐
  │  BPF_MAXINSNS = 4096                                    │
  │  Used for:                                              │
  │  - cBPF programs (tcpdump filters)                      │
  │  - Unprivileged eBPF socket filters                     │
  │  - Some legacy checks                                   │
  ├─────────────────────────────────────────────────────────┤
  │  BPF_COMPLEXITY_LIMIT_INSNS = 1,000,000 (since 5.2)    │
  │  Used for:                                              │
  │  - Privileged eBPF programs                             │
  │  - XDP, kprobe, tracepoint, LSM, etc.                   │
  │  - Programs loaded with CAP_BPF / CAP_SYS_ADMIN         │
  └─────────────────────────────────────────────────────────┘
```

### The Verifier's "Complexity" Counter

The 1M limit is not just "number of instructions in the program file" — it counts **verifier states visited** during analysis:

```
  WHAT THE 1M LIMIT ACTUALLY COUNTS:
  
  The verifier tracks `insn_processed` — the number of
  instructions it has symbolically executed across ALL paths.
  
  Simple linear program (no branches):
    File instructions: 1000
    Verifier processes: ~1000 states
    
  Program with 10 independent if-else branches:
    File instructions: 200
    Verifier processes: up to 200 × 2^10 = 204,800 states
    (without pruning)
  
  With good state pruning (5.2+):
    Same program: might only need ~5000 states
    (due to equivalent-state detection)
  
  This is why a 1M instruction program might verify quickly
  if it's mostly linear, but a 100-instruction program with
  complex branching could FAIL verification due to hitting
  the 1M complexity limit.
  
  ERROR: "BPF program is too large. Processed 1000001 insn"
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
         This error means the verifier gave up, not that
         your program file has 1M+ instructions.
```

---

## 9. Verifier Complexity and State Pruning

### State Pruning — The Key Algorithm

**Concept:** "Pruning" means cutting off branches of a search tree early, when you can prove the remaining work is unnecessary.

```
  STATE PRUNING DECISION TREE:
  
  At a branch point (e.g., after a conditional jump):
  
  Verifier arrives at instruction PC=X with register state S
       │
       ▼
  ┌─────────────────────────────────────────┐
  │  Has PC=X been visited before?          │
  └────────────┬────────────────────────────┘
               │
       ┌───────┴───────┐
      YES              NO
       │               │
       ▼               ▼
  ┌──────────────┐  ┌─────────────────────┐
  │ Retrieve     │  │ Explore this path   │
  │ cached state │  │ (execute verifier)  │
  │ S_cached     │  │ Save state to cache │
  └──────┬───────┘  └─────────────────────┘
         │
         ▼
  ┌─────────────────────────────────────────┐
  │  Is current state S ⊆ S_cached?         │
  │  (S is MORE constrained than cached)    │
  └─────────────────────────────────────────┘
         │
  ┌──────┴──────┐
  YES           NO
  │             │
  ▼             ▼
PRUNE!        Continue
(safe —       exploring
proven by     (add to
cached        worklist)
state)
  
  WHY IS S ⊆ S_cached SAFE TO PRUNE?
  
  If we previously verified that state S_cached (more permissive)
  reaches EXIT safely, then S (more constrained, fewer possible
  values) MUST ALSO reach EXIT safely — it can only do a subset
  of what S_cached can do.
  
  Analogy: If we prove "any adult can enter this building safely,"
  we don't need to re-verify "this specific adult can enter safely."
```

### State Equivalence — The Subset Check in Practice

```c
/* Simplified version of what the verifier checks */
/* For each register, is current state "at least as safe" as cached? */

bool state_is_subsumed(struct bpf_reg_state *curr, 
                       struct bpf_reg_state *cached) {
    /* Same type required */
    if (curr->type != cached->type) return false;
    
    /* For scalar values: */
    /* curr range must be a subset of cached range */
    if (curr->umin_value < cached->umin_value) return false;
    if (curr->umax_value > cached->umax_value) return false;
    if (curr->smin_value < cached->smin_value) return false;
    if (curr->smax_value > cached->smax_value) return false;
    
    /* tnum: all bits known in curr must also be known in cached */
    /* and known values must match */
    if (!tnum_is_subsumed(curr->var_off, cached->var_off)) return false;
    
    return true;  /* curr ⊆ cached → safe to prune */
}
```

### Complexity Optimization Techniques for Programmers

```
  HOW TO WRITE VERIFIER-FRIENDLY PROGRAMS:
  
  ┌──────────────────────────────────────────────────────────┐
  │  TECHNIQUE 1: Early exits on error paths                 │
  │                                                           │
  │  BAD:                          GOOD:                     │
  │  ptr = map_lookup(...);        ptr = map_lookup(...);    │
  │  if (ptr) {                    if (!ptr) return 0;       │
  │    ... 200 instructions ...    ... 200 instructions ...  │
  │  }                             // verifier only tracks   │
  │                                // 1 path here            │
  ├──────────────────────────────────────────────────────────┤
  │  TECHNIQUE 2: Explicit bounds before pointer arithmetic  │
  │                                                           │
  │  u32 idx = some_value;                                   │
  │  if (idx >= MAX_ENTRIES) return 0;  /* MUST have this */ │
  │  value = array[idx];  /* now verifier knows idx < MAX */ │
  ├──────────────────────────────────────────────────────────┤
  │  TECHNIQUE 3: Use __builtin_expect for hot paths         │
  │                                                           │
  │  if (__builtin_expect(!ptr, 0)) return 0;                │
  │  /* Compiler puts common case first → fewer branches     │
  │     for verifier to explore */                           │
  ├──────────────────────────────────────────────────────────┤
  │  TECHNIQUE 4: Avoid re-computing the same condition      │
  │                                                           │
  │  /* Store result in variable to help verifier            │
  │     track state through reuse */                         │
  │  bool valid = (idx < MAX && ptr != NULL);                │
  │  if (valid) { ... }                                      │
  └──────────────────────────────────────────────────────────┘
```

---

## 10. BPF-to-BPF Function Calls (bpf2bpf)

**Concept:** Before kernel 4.16, BPF programs could not call other BPF functions — only kernel helper functions. This forced programmers to either inline everything (expensive) or use tail calls (complex).

**Kernel 4.16** added true intra-program function calls.

```
  BPF2BPF CALL MECHANISM:
  
  Main program:                   Subfunction:
  ┌────────────────┐              ┌────────────────┐
  │  instruction 0 │              │  instruction N  │
  │  instruction 1 │              │  instruction N+1│
  │  ...           │              │  ...           │
  │  BPF_CALL      │──────────────▶ instruction N+K│
  │  (rel offset)  │◀─────────────│  BPF_EXIT      │
  │  instruction J │              └────────────────┘
  │  ...           │
  └────────────────┘
  
  CALL INSTRUCTION FOR BPF2BPF:
  opcode = BPF_JMP | BPF_CALL
  src_reg = BPF_PSEUDO_CALL (= 1)   ← distinguishes from helper call
  imm    = relative PC offset to the subfunction
  
  STACK FRAME ALLOCATION:
  
  Each function gets its OWN 512-byte stack frame:
  
  ┌──────────────────────────────────┐
  │  main() stack frame [512 bytes]  │  ← R10 points here initially
  ├──────────────────────────────────┤
  │  func1() stack frame [512 bytes] │  ← R10 adjusted on call
  ├──────────────────────────────────┤
  │  func2() stack frame [512 bytes] │
  └──────────────────────────────────┘
  
  Max call depth: 8 (each with 512 bytes = 4KB total stack)
  
  ⚠️  Each BPF2BPF function has its OWN 4096-instruction limit
      (pre-5.2) or participates in the 1M overall limit (5.2+).
      In practice, the entire program (main + all subfunctions)
      shares the 1M verifier complexity budget.
```

---

## 11. BPF Loops — bounded_loops and the Loop Revolution

### Pre-5.3: No Loops (Backward Jumps Forbidden)

```
  Before kernel 5.3, this was REJECTED by the verifier:
  
  BPF assembly (pseudocode):
  
  loop_start:
    r1 -= 1
    if r1 > 0 goto loop_start    ← BACKWARD JUMP → REJECTED
  
  Because: backward jump could mean infinite loop
           → kernel hang → denial of service
```

### Kernel 5.3: bounded_loops with bpf_loop() 

Two mechanisms for loops were added:

**Mechanism 1: Verifier-verified bounded loops (for loops with known bounds)**

```
  BOUNDED LOOP REQUIREMENTS (kernel 5.3):
  
  The verifier must be able to PROVE termination:
  
  1. Loop variable must be a scalar (not a pointer)
  2. Loop bound must be provably finite
  3. Loop variable must be monotonically progressing
     (strictly increasing or decreasing)
  4. Number of iterations must be statically bounded
     OR proven bounded by range analysis
  
  ACCEPTED:                          REJECTED:
  
  int i;                             int i = user_input;
  for (i = 0; i < 10; i++) {        while (i > 0) {    ← verifier
    ...                                  i = unknown();     can't prove
  }                                  }                      termination
  (max 10 iterations: proven)
  
  
  VERIFIER'S LOOP ANALYSIS:
  
  Loop entry state:  r1 ∈ [0, 9]
       │
       ▼
  ┌──────────────────┐
  │  Loop body       │
  │  r1 += 1         │
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐
  │  if r1 < 10:     │
  │    goto loop_top │ ← backward jump allowed IF
  │  else: continue  │   verifier proves r1 grows by 1
  └──────────────────┘   each iteration → max 10 iters
  
  Verifier "unrolls" the loop conceptually:
  Iteration 1: r1 ∈ [0,0]
  Iteration 2: r1 ∈ [1,1]
  ...
  Iteration 10: r1 ∈ [9,9]
  Exit check: r1 = 10 → loop exits
  
  This is why large loop bounds are still slow to verify
  (verifier may need to track each iteration state).
```

**Mechanism 2: `bpf_loop()` helper (kernel 5.17)**

```c
/* 
 * bpf_loop() — execute callback up to nr_loops times
 * 
 * int bpf_loop(__u32 nr_loops, 
 *              void *callback_fn,    /* pointer to BPF subprog */
 *              void *callback_ctx,   /* passed to each callback */
 *              __u64 flags);         /* must be 0 */
 * 
 * Callback signature:
 * int callback(u32 index, void *ctx)
 *   return 0 to continue, 1 to stop early
 * 
 * bpf_loop() guarantees termination because nr_loops is bounded.
 * The verifier doesn't need to analyze the loop body for termination.
 */

/* C example using bpf_loop: */
struct search_ctx {
    __u32 target;
    __u32 found_idx;
    bool  found;
};

static int search_callback(u32 index, struct search_ctx *ctx)
{
    u32 *val = bpf_map_lookup_elem(&my_array, &index);
    if (val && *val == ctx->target) {
        ctx->found_idx = index;
        ctx->found = true;
        return 1;  /* stop iteration */
    }
    return 0;  /* continue */
}

SEC("xdp")
int xdp_prog(struct xdp_md *ctx)
{
    struct search_ctx sctx = { .target = 42 };
    bpf_loop(1024, search_callback, &sctx, 0);
    if (sctx.found) {
        /* found at index sctx.found_idx */
    }
    return XDP_PASS;
}
```

---

## 12. Tail Calls — Chaining Programs

**Concept — Tail Call:** A "tail call" is when a function, as its LAST action, calls another function and directly returns that function's result (without doing anything after). In eBPF, `bpf_tail_call()` transfers execution to another eBPF program, **replacing** the current program's stack frame.

```
  TAIL CALL vs REGULAR CALL:
  
  Regular call:                    Tail call:
  ┌──────────┐                    ┌──────────┐
  │ prog A   │                    │ prog A   │
  │   ...    │                    │   ...    │
  │ call B() │──▶┌──────────┐     │ tail B() │──▶┌──────────┐
  │   ...    │◀──│ prog B   │     │ (exit A) │   │ prog B   │
  │ return   │   │ return   │     └──────────┘   │ return   │
  └──────────┘   └──────────┘       A's frame    └──────────┘
                                     replaced!   B returns to
                                                 A's CALLER
  
  TAIL CALL MECHANISM:
  
  bpf_tail_call(ctx, &prog_array_map, index);
  
  ┌──────────────────────────────────────────────────────────┐
  │  1. Look up prog_array_map[index]                       │
  │  2. If not found → return (fall through, not an error)  │
  │  3. If found → JMP to new program's entry point         │
  │     • Current stack frame is REUSED (not a new frame)   │
  │     • R1 (ctx) remains the same                         │
  │     • R6-R9 remain as-is                                │
  │     • Max 33 tail calls per chain (MAX_TAIL_CALL_CNT)   │
  └──────────────────────────────────────────────────────────┘
  
  TAIL CALL CHAIN (the workaround for pre-5.2 4096 limit):
  
  Entry XDP program (≤4096 insns)
       │ bpf_tail_call(ctx, &jmp_table, 0)
       ▼
  Parser program (≤4096 insns)
       │ bpf_tail_call(ctx, &jmp_table, 1)
       ▼
  Action program (≤4096 insns)
       │ return verdict
       ▼
  (back to network stack)
  
  Counter: BPF_MAX_TAIL_CALL_CNT = 33
  Stack:   NOT duplicated (same frame, different code)
```

---

## 13. BPF Maps — Memory Architecture

**Concept — "Map":** In eBPF, a "map" is a generic kernel data structure that acts as shared memory between:
- BPF programs (kernel space) ↔ BPF programs
- BPF programs (kernel space) ↔ Userspace programs

```
  BPF MAP TYPES (selection):
  
  ┌────────────────────────┬──────────┬─────────────────────────┐
  │  Type                  │  Access  │  Use case               │
  ├────────────────────────┼──────────┼─────────────────────────┤
  │  HASH                  │  O(1)    │  Per-flow state         │
  │  ARRAY                 │  O(1)    │  Config, counters       │
  │  PROG_ARRAY            │  O(1)    │  Tail call targets      │
  │  PERCPU_HASH           │  O(1)    │  High-freq counters     │
  │  PERCPU_ARRAY          │  O(1)    │  High-freq per-CPU data │
  │  LRU_HASH              │  O(1)    │  Connection tracking    │
  │  RINGBUF               │  O(1)    │  High-perf event output │
  │  STACK_TRACE           │  O(1)    │  Profiling              │
  │  CGROUP_ARRAY          │  O(1)    │  cgroup programs        │
  │  SK_STORAGE            │  O(1)    │  Per-socket state       │
  │  INODE_STORAGE         │  O(1)    │  Per-inode state        │
  └────────────────────────┴──────────┴─────────────────────────┘
  
  MAP LIFECYCLE:
  
  User space:           Kernel/BPF:
  
  fd = bpf_map_create() ──▶ kernel allocates map
       │                          │
       │                    bpf programs can:
       │                    bpf_map_lookup_elem()
       │                    bpf_map_update_elem()
       │                    bpf_map_delete_elem()
       │
  bpf_map_lookup_fd()  ──▶ user space reads results
  bpf_map_update_fd()  ──▶ user space writes config
  close(fd)            ──▶ map freed when refcount = 0
  
  MAP MEMORY IS NOT ON THE BPF STACK:
  Map values can be arbitrarily large (configured at creation).
  Pointer to map value = PTR_TO_MAP_VALUE (tracked by verifier).
  Access beyond map value size → verifier rejects.
```

---

## 14. Writing eBPF Programs in C — Full Examples

### Setup and Headers

```c
/* Include path: linux kernel source or libbpf headers */
#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

/* The SEC() macro marks functions with ELF section names.
 * The loader uses these to determine the program type and
 * which hook to attach to. */
#define SEC(name) __attribute__((section(name), used))
```

### Example 1: Minimal XDP Program (Instruction Counting Demo)

```c
/* minimal_xdp.bpf.c
 * 
 * This is the SMALLEST possible valid XDP program.
 * Instruction count: 2
 * 
 * Instruction 0: r0 = XDP_PASS (= 2)
 * Instruction 1: BPF_EXIT (return r0)
 */
SEC("xdp")
int xdp_pass(struct xdp_md *ctx)
{
    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";

/* Compiled BPF bytecode:
 * 
 * 0: (b7) r0 = 2           ; MOV64_IMM r0, XDP_PASS
 * 1: (95) exit             ; BPF_EXIT
 * 
 * Opcode breakdown for instruction 0:
 * code = BPF_ALU64 | BPF_MOV | BPF_K = 0x07 | 0xb0 | 0x00 = 0xb7
 * dst  = 0 (r0)
 * src  = 0
 * off  = 0
 * imm  = 2 (XDP_PASS)
 */
```

### Example 2: Packet Counter with Map (Demonstrating State)

```c
/* packet_counter.bpf.c
 * 
 * Counts incoming packets using a per-CPU array map.
 * Demonstrates: map access, pointer validation,
 * atomic operations, verifier range constraints.
 */
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

/* Map definition: per-CPU array with 1 element (the counter) */
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, __u64);
} pkt_count SEC(".maps");

SEC("xdp")
int count_packets(struct xdp_md *ctx)
{
    __u32 key = 0;
    __u64 *count;
    
    /* bpf_map_lookup_elem returns NULL or pointer to value.
     * The verifier tracks this as PTR_TO_MAP_VALUE_OR_NULL.
     * We MUST null-check before dereferencing. */
    count = bpf_map_lookup_elem(&pkt_count, &key);
    if (!count) {
        /* This path: verifier knows count == NULL.
         * Returning here prevents the verifier from needing
         * to explore the null-dereference path. */
        return XDP_PASS;
    }
    
    /* Here: verifier knows count != NULL → PTR_TO_MAP_VALUE.
     * Safe to dereference. */
    __sync_fetch_and_add(count, 1);  /* atomic increment */
    /* Compiles to BPF_ATOMIC ADD instruction */
    
    return XDP_PASS;
}

/* 
 * BPF DISASSEMBLY (approximate):
 * 
 *  0: (18) r1 = 0x<map_fd>         ; load map file descriptor (wide insn, 2 slots)
 *  2: (85) call map_lookup_elem#1  ; helper call
 *     ; Before: r1=map_ptr, r2=&key (stack)
 *     ; After:  r0=ptr_to_value_or_null
 *  3: (15) if r0 == 0 goto +2     ; null check (JEQ r0, 0, +2)
 *  4: (07) r1 = 1                  ; MOV r1, 1 (atomic add value)
 *  5: (db) *(u64 *)(r0+0) += r1   ; ATOMIC ADD [r0+0], r1
 *  6: (b7) r0 = 2                  ; MOV r0, XDP_PASS
 *  7: (95) exit
 *  ; null path:
 *  8: (b7) r0 = 2                  ; MOV r0, XDP_PASS
 *  9: (95) exit
 * 
 * Total: 10 instruction slots (the wide insn uses 2)
 * Verifier processes: ~12 states (both branches)
 */

char _license[] SEC("license") = "GPL";
```

### Example 3: TCP Port Filter — Demonstrating Boundary Checks

```c
/* tcp_filter.bpf.c
 * 
 * Drop TCP packets to port 8080.
 * Demonstrates: packet bounds checking, protocol parsing,
 * verifier-required boundary validation.
 * 
 * CRITICAL INSIGHT: Every packet pointer access must be
 * validated against ctx->data_end. The verifier will REJECT
 * any program that might read past packet end.
 */
#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

SEC("xdp")
int tcp_port_filter(struct xdp_md *ctx)
{
    /* ctx->data and ctx->data_end are offsets into the packet.
     * The verifier tracks these as PTR_TO_PACKET and
     * PTR_TO_PACKET_END respectively. */
    void *data     = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;
    
    /* BOUNDARY CHECK PATTERN:
     * Always check: if (ptr + sizeof(header) > data_end) return
     * 
     * The verifier requires EXPLICIT bounds checks.
     * After this check, it knows eth+sizeof(*eth) ≤ data_end.
     * Therefore accessing eth->h_proto is safe. */
    
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;  /* packet too short */
    
    /* Only handle IPv4 */
    if (eth->h_proto != bpf_htons(ETH_P_IP))
        return XDP_PASS;
    
    /* IP header */
    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end)
        return XDP_PASS;
    
    /* Only handle TCP */
    if (ip->protocol != IPPROTO_TCP)
        return XDP_PASS;
    
    /* Variable-length IP header: ihl field gives length in 32-bit words.
     * ihl * 4 = byte length. Min=20 (ihl=5), Max=60 (ihl=15).
     * 
     * VERIFIER CHALLENGE: ip->ihl is a packet field (untrusted).
     * We must constrain it before using as an offset. */
    __u8 ip_hlen = ip->ihl * 4;
    if (ip_hlen < 20)
        return XDP_PASS;  /* invalid IP header */
    
    /* TCP header */
    struct tcphdr *tcp = (void *)ip + ip_hlen;
    /* Boundary check: MUST happen after computing tcp pointer */
    if ((void *)(tcp + 1) > data_end)
        return XDP_PASS;
    
    /* Drop packets to port 8080 */
    if (tcp->dest == bpf_htons(8080))
        return XDP_DROP;
    
    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";

/*
 * VERIFIER TRACE (simplified) for the tcp section:
 * 
 * State at "struct tcphdr *tcp = ...":
 *   r6 = PTR_TO_PACKET (ip + ihl), ihl ∈ [20, 60]
 *   r6.offset ∈ [34, 74] (14 eth + 20..60 ip)
 * 
 * State at bounds check "(void *)(tcp + 1) > data_end":
 *   TRUE branch: (offset + 20 > pkt_len) → return XDP_PASS
 *   FALSE branch: safe, tcp accessible
 * 
 * State at "tcp->dest":
 *   Verifier knows: PTR_TO_PACKET, offset ∈ [34,74],
 *   offset + 20 ≤ pkt_len → access to [offset+2, offset+4) safe ✓
 */
```

### Example 4: BPF2BPF Function Calls — Demonstrating 1M Budget

```c
/* bpf2bpf_example.bpf.c
 * 
 * Demonstrates sub-functions (bpf2bpf calls).
 * These are essential for writing programs that approach
 * the 1M instruction complexity limit — without them,
 * code would be monolithic and unverifiable.
 */
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

/* Sub-function: compute a hash of input value.
 * This is a separate BPF function (not inlined).
 * It has its own 512-byte stack frame. */
static __noinline __u64 compute_hash(__u64 value)
{
    /* FNV-1a hash — simple, verifier-friendly */
    __u64 hash = 14695981039346656037ULL;
    int i;
    
    /* This loop is verifier-safe: bounded by constant 8 */
    for (i = 0; i < 8; i++) {
        hash ^= (value & 0xFF);
        hash *= 1099511628211ULL;
        value >>= 8;
    }
    return hash;
}

/* Another sub-function: classify packet size */
static __noinline int classify_size(__u32 size)
{
    if (size < 64)   return 0;  /* small */
    if (size < 512)  return 1;  /* medium */
    if (size < 1500) return 2;  /* large */
    return 3;                   /* jumbo */
}

struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 4);
    __type(key, __u32);
    __type(value, __u64);
} size_buckets SEC(".maps");

SEC("xdp")
int categorize_packets(struct xdp_md *ctx)
{
    __u32 pkt_size = ctx->data_end - ctx->data;
    
    /* BPF2BPF call: classify_size gets its own stack frame */
    int bucket = classify_size(pkt_size);
    
    /* BPF2BPF call: compute_hash gets its own stack frame */
    __u64 hash = compute_hash((__u64)pkt_size);
    
    __u32 key = (__u32)bucket;
    __u64 *count = bpf_map_lookup_elem(&size_buckets, &key);
    if (count)
        __sync_fetch_and_add(count, 1);
    
    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";

/*
 * CALL FRAME LAYOUT during compute_hash():
 * 
 * Memory addresses (conceptual):
 * 
 * High address:
 * ┌────────────────────────────────────┐
 * │  categorize_packets() frame        │  [FP - 512 to FP]
 * │  local vars: pkt_size, bucket,     │
 * │              hash, key, count      │
 * ├────────────────────────────────────┤
 * │  compute_hash() frame              │  [FP2 - 512 to FP2]
 * │  local vars: hash, i, value        │
 * │  (separate 512-byte allocation)    │
 * └────────────────────────────────────┘
 * Low address
 * 
 * Total stack: 2 × 512 = 1024 bytes (for this 2-deep call)
 * Max depth: 8 calls × 512 bytes = 4096 bytes total stack
 */
```

### Example 5: Tracepoint Program — Syscall Monitoring

```c
/* syscall_monitor.bpf.c
 * 
 * Monitors execve() system calls.
 * Demonstrates: tracepoint context, ring buffer,
 * string copying helpers.
 */
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

/* Event structure sent to userspace */
struct execve_event {
    __u32 pid;
    __u32 uid;
    char  comm[16];    /* process name */
    char  filename[64];
};

/* Ring buffer map: efficient event output to userspace */
struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 4096 * 1024);  /* 4MB ring buffer */
} events SEC(".maps");

/* Tracepoint format: sys_enter_execve
 * Arguments from /sys/kernel/debug/tracing/events/syscalls/
 *               sys_enter_execve/format */
struct sys_enter_execve_args {
    __u64 unused;           /* common fields */
    int   syscall_nr;
    const char __user *filename;
    const char __user *const __user *argv;
    const char __user *const __user *envp;
};

SEC("tracepoint/syscalls/sys_enter_execve")
int trace_execve(struct sys_enter_execve_args *ctx)
{
    struct execve_event *event;
    __u64 pid_tgid = bpf_get_current_pid_tgid();
    
    /* Reserve space in ring buffer.
     * BPF_RINGBUF_RESERVE returns NULL on failure (buffer full). */
    event = bpf_ringbuf_reserve(&events, sizeof(*event), 0);
    if (!event)
        return 0;
    
    /* Fill event fields */
    event->pid = (__u32)(pid_tgid >> 32);   /* upper 32 bits = tgid */
    event->uid = (__u32)bpf_get_current_uid_gid();
    
    /* bpf_get_current_comm: fills buffer with current process name */
    bpf_get_current_comm(event->comm, sizeof(event->comm));
    
    /* bpf_probe_read_user_str: safely reads string from user space.
     * Returns negative errno on failure, or length including null. */
    bpf_probe_read_user_str(event->filename, sizeof(event->filename),
                            ctx->filename);
    
    /* Submit event to ring buffer (wakes up userspace reader) */
    bpf_ringbuf_submit(event, 0);
    
    return 0;
}

char _license[] SEC("license") = "GPL";
```

### Building and Loading (C Workflow)

```bash
# Compile BPF program
clang -O2 -g -target bpf \
    -D__TARGET_ARCH_x86 \
    -I/usr/include/x86_64-linux-gnu \
    -c packet_counter.bpf.c \
    -o packet_counter.bpf.o

# Inspect generated instructions
llvm-objdump -d packet_counter.bpf.o

# Generate skeleton (libbpf skeleton)
bpftool gen skeleton packet_counter.bpf.o > packet_counter.skel.h

# Count instructions
bpftool prog show

# Load and inspect with bpftool
bpftool prog load packet_counter.bpf.o /sys/fs/bpf/pkt_counter
bpftool prog dump xlated pinned /sys/fs/bpf/pkt_counter
```

---

## 15. Writing eBPF Programs in Rust (Aya)

### What is Aya?

**Aya** is a pure-Rust eBPF library. Unlike libbpf (C), Aya does not depend on libbpf or any C BPF libraries. It handles:
- BPF program compilation (via `aya-bpf` crate for kernel-side code)
- Program loading, verification, and attachment (via `aya` crate for userspace)
- Map management in both kernel and user space

```
  AYA PROJECT STRUCTURE:
  
  my-ebpf-project/
  ├── Cargo.toml                    (workspace)
  ├── my-ebpf/                      (kernel-side BPF code)
  │   ├── Cargo.toml
  │   └── src/
  │       └── main.rs               (BPF programs, compiled to BPF bytecode)
  └── my-ebpf-userspace/            (userspace controller)
      ├── Cargo.toml
      └── src/
          └── main.rs               (loads BPF, reads maps, attaches hooks)
```

### Setup

```toml
# my-ebpf/Cargo.toml (kernel-side)
[package]
name = "my-ebpf"
version = "0.1.0"
edition = "2021"

[[bin]]
name = "my-ebpf"
path = "src/main.rs"

[dependencies]
aya-bpf = { version = "0.1", features = ["macros"] }
aya-log-ebpf = "0.1"

[profile.dev]
opt-level = 3       # BPF needs optimization for verifier

[profile.release]
opt-level = 3
lto = true

# my-ebpf-userspace/Cargo.toml
[dependencies]
aya = { version = "0.12", features = ["async_tokio"] }
aya-log = "0.2"
tokio = { version = "1", features = ["full"] }
anyhow = "1"
```

### Example 1: XDP Packet Counter in Rust

```rust
// my-ebpf/src/main.rs
// Kernel-side BPF code — compiled to eBPF bytecode by rustc + LLVM

#![no_std]
#![no_main]

use aya_bpf::{
    bindings::xdp_action,
    macros::{map, xdp},
    maps::PerCpuArray,
    programs::XdpContext,
};
use aya_log_ebpf::info;

/// Define a per-CPU array map for packet counting.
/// `#[map]` macro generates the BPF map definition ELF section.
#[map(name = "PKT_COUNT")]
static PKT_COUNT: PerCpuArray<u64> = PerCpuArray::with_max_entries(1, 0);

/// `#[xdp]` macro sets the ELF section to "xdp/<function_name>"
/// XdpContext wraps struct xdp_md and provides safe accessors.
#[xdp]
pub fn count_packets(ctx: XdpContext) -> u32 {
    // match_or_return: idiomatic Aya error handling pattern
    match unsafe { try_count_packets(&ctx) } {
        Ok(action) => action,
        Err(_) => xdp_action::XDP_PASS,
    }
}

/// Unsafe inner function — BPF pointer arithmetic is inherently unsafe
/// in Rust (the verifier provides safety, not the type system).
/// Returning Result<u32, ()> lets us use ? operator.
unsafe fn try_count_packets(ctx: &XdpContext) -> Result<u32, ()> {
    // PerCpuArray::get_ptr_mut: returns *mut u64 or None
    // index 0: only one counter
    let count = PKT_COUNT
        .get_ptr_mut(0)
        .ok_or(())?;  // None → Err(()) → returns XDP_PASS
    
    // Safe: verifier ensures the pointer is valid (map value pointer)
    // *count is a u64 in kernel memory
    *count += 1;
    // Note: for multi-CPU safety, use atomic (percpu maps avoid this)
    
    Ok(xdp_action::XDP_PASS)
}

/// Required by eBPF — identifies GPL licensing for helper access
#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {
    unsafe { core::hint::unreachable_unchecked() }
}
```

### Example 2: TCP Filter in Rust

```rust
// my-ebpf/src/main.rs — TCP port filter

#![no_std]
#![no_main]

use aya_bpf::{
    bindings::xdp_action,
    macros::xdp,
    programs::XdpContext,
};
use core::mem;

// Network protocol constants
const ETH_P_IP: u16    = 0x0800;
const IPPROTO_TCP: u8  = 6;
const TARGET_PORT: u16 = 8080;

/// Safe packet bounds check helper.
/// Returns pointer to T at offset, or Err if out of bounds.
/// This is the critical pattern for verifier acceptance.
#[inline(always)]
unsafe fn ptr_at<T>(ctx: &XdpContext, offset: usize) -> Result<*const T, ()> {
    let start = ctx.data();
    let end   = ctx.data_end();
    let len   = mem::size_of::<T>();
    
    // The verifier will verify this check:
    // ptr (start + offset) and ptr + len must both be ≤ end
    if start + offset + len > end {
        return Err(());
    }
    
    Ok((start + offset) as *const T)
}

#[repr(C, packed)]
struct EthHdr {
    h_dest:   [u8; 6],
    h_source: [u8; 6],
    h_proto:  u16,       // big-endian
}

#[repr(C)]
struct IpHdr {
    version_ihl: u8,    // version(4) + ihl(4)
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

#[repr(C)]
struct TcpHdr {
    source:  u16,       // source port (big-endian)
    dest:    u16,       // dest port (big-endian)
    seq:     u32,
    ack_seq: u32,
    // ... rest of header
    _rest:   [u8; 12],
}

#[xdp]
pub fn tcp_filter(ctx: XdpContext) -> u32 {
    match unsafe { try_tcp_filter(&ctx) } {
        Ok(action) => action,
        Err(_)     => xdp_action::XDP_PASS,
    }
}

unsafe fn try_tcp_filter(ctx: &XdpContext) -> Result<u32, ()> {
    // --- Parse Ethernet header ---
    let eth: *const EthHdr = ptr_at(ctx, 0)?;
    
    // u16::from_be: convert from big-endian (network) to host byte order
    if u16::from_be((*eth).h_proto) != ETH_P_IP {
        return Ok(xdp_action::XDP_PASS);
    }
    
    // --- Parse IP header ---
    let ip: *const IpHdr = ptr_at(ctx, mem::size_of::<EthHdr>())?;
    
    if (*ip).protocol != IPPROTO_TCP {
        return Ok(xdp_action::XDP_PASS);
    }
    
    // Extract IP header length: lower 4 bits of version_ihl, × 4
    let ihl = ((*ip).version_ihl & 0x0F) as usize * 4;
    if ihl < 20 {
        return Err(());  // invalid
    }
    
    // --- Parse TCP header ---
    let tcp_offset = mem::size_of::<EthHdr>() + ihl;
    let tcp: *const TcpHdr = ptr_at(ctx, tcp_offset)?;
    
    // Check destination port
    if u16::from_be((*tcp).dest) == TARGET_PORT {
        return Ok(xdp_action::XDP_DROP);
    }
    
    Ok(xdp_action::XDP_PASS)
}

#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {
    unsafe { core::hint::unreachable_unchecked() }
}
```

### Example 3: Userspace Controller in Rust (Reading Maps)

```rust
// my-ebpf-userspace/src/main.rs
// Loads BPF program, attaches to interface, reads counter

use aya::{
    include_bytes_aligned,
    maps::PerCpuArray,
    programs::{Xdp, XdpFlags},
    Bpf,
};
use aya_log::BpfLogger;
use std::time::Duration;
use tokio::time::sleep;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // include_bytes_aligned!: embeds compiled BPF ELF at compile time
    // Path relative to workspace root
    let bpf_bytes = include_bytes_aligned!("../../target/bpfel-unknown-none/release/my-ebpf");
    
    // Load BPF ELF — parses sections, creates maps, loads programs
    let mut bpf = Bpf::load(bpf_bytes)?;
    
    // Initialize BPF logging (routes bpf_printk to tracing crate)
    BpfLogger::init(&mut bpf)?;
    
    // Get the XDP program by name (must match SEC("xdp/<name>") in BPF)
    let program: &mut Xdp = bpf.program_mut("count_packets").unwrap().try_into()?;
    
    // Load program into kernel (triggers BPF verifier)
    // If verifier rejects → error here with detailed message
    program.load()?;
    
    // Attach to network interface "eth0"
    // XdpFlags::default() = SKB_MODE (software XDP, always works)
    // XdpFlags::DRV_MODE  = driver-mode (requires driver support, faster)
    // XdpFlags::HW_MODE   = hardware offload (requires NIC support, fastest)
    program.attach("eth0", XdpFlags::default())?;
    println!("XDP program attached to eth0");
    
    // Access the PKT_COUNT map
    let pkt_count: PerCpuArray<_, u64> = PerCpuArray::try_from(
        bpf.map_mut("PKT_COUNT").unwrap()
    )?;
    
    // Poll the counter every second
    loop {
        sleep(Duration::from_secs(1)).await;
        
        // PerCpuArray::get returns Vec<u64> (one per CPU)
        let counts = pkt_count.get(&0, 0)?;
        let total: u64 = counts.iter().sum();
        println!("Packets received: {}", total);
    }
}
```

### Building Rust eBPF (Aya)

```bash
# Install bpf target
rustup target add bpfel-unknown-none

# Install cargo-bpf helper (optional, for skeleton generation)
cargo install bpf-linker

# Build kernel-side BPF code
cargo build --package my-ebpf \
    --target bpfel-unknown-none \
    -Z build-std=core \
    --release

# Build userspace code (normal target)
cargo build --package my-ebpf-userspace --release

# Run (requires root for BPF loading)
sudo ./target/release/my-ebpf-userspace
```

---

## 16. Instruction Optimization Patterns

### Pattern 1: Minimize Verifier State Explosion

```
  STATE EXPLOSION EXAMPLE:
  
  Bad (exponential states):          Good (linear states):
  
  if (a > 0) {                       int status = 0;
    if (b > 0) {                     if (a > 0) status |= 1;
      if (c > 0) {                   if (b > 0) status |= 2;
        if (d > 0) {                 if (c > 0) status |= 4;
          action();                  if (d > 0) status |= 8;
        }                            if (status == 0xF) action();
      }                              
    }                                /* Verifier: tracks status ∈ [0,15]
  }                                   * No nested branching
  /* 2^4 = 16 paths for verifier */   * ~4 paths for verifier */
```

### Pattern 2: Use `__always_inline` for Instruction Budget

```c
/* __always_inline forces inlining — avoids bpf2bpf call overhead
 * BUT uses instruction budget of calling function.
 * Use when the function is small and called from one place. */
static __always_inline int fast_lookup(__u32 key)
{
    /* ~5 instructions, inline everywhere */
    __u64 *v = bpf_map_lookup_elem(&my_map, &key);
    return v ? *v : -1;
}

/* __noinline forces bpf2bpf call — separate stack frame, separate
 * instruction budget. Use for large functions called from many places. */
static __noinline int complex_parse(void *data, void *data_end)
{
    /* ~500 instructions, called from 5 places
     * Without __noinline: 5 × 500 = 2500 instructions
     * With    __noinline: 500 + 5 call-sites × 1 = 505 instructions */
    /* ... */
}
```

### Pattern 3: Exploit Tnum Range Knowledge

```c
/* Tell the verifier a value is bounded: use masking */

__u32 untrusted_idx;  /* packet field — verifier doesn't know its range */
/* WRONG: verifier rejects (idx could be UINT_MAX, out of array bounds) */
__u64 *v = bpf_map_lookup_elem(&array_1024, &untrusted_idx);

/* RIGHT: mask to known range first */
__u32 safe_idx = untrusted_idx & 1023;  /* verifier knows: safe_idx ∈ [0, 1023] */
__u64 *v = bpf_map_lookup_elem(&array_1024, &safe_idx);

/* After the mask, verifier's tnum for safe_idx:
 * mask  = 0xFFFFFFFFFFFFFC00  (upper bits unknown, lower 10 known)
 * value = 0x0000000000000000  (lower 10 bits could be anything in [0,1023])
 * → verifier knows safe_idx < 1024 → array access is valid */
```

### Pattern 4: Early Return on Fast Path

```c
/* Design programs with the common (fast) case first.
 * Fewer paths → faster verification + better branch prediction. */
SEC("xdp")
int optimized_filter(struct xdp_md *ctx)
{
    /* Fast path: check most common case first */
    void *data     = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;
    
    /* Most packets: Ethernet (14 bytes) + IP (20 bytes min) = 34 bytes */
    if (data + 34 > data_end)   /* FAST: single comparison, early exit */
        return XDP_PASS;
    
    struct ethhdr *eth = data;
    if (eth->h_proto != bpf_htons(ETH_P_IP))  /* ~70% of packets: IPv4 */
        return XDP_PASS;                        /* exit early */
    
    /* Only IPv4 TCP continues here */
    struct iphdr *ip = data + 14;
    if (ip->protocol != IPPROTO_TCP)
        return XDP_PASS;
    
    /* Now we're in the detailed processing path */
    /* ... */
    return XDP_PASS;
}
```

---

## 17. Debugging Instructions — bpftool & llvm-objdump

### Reading BPF Assembly with llvm-objdump

```bash
# Disassemble BPF object file
llvm-objdump -d my_program.bpf.o

# Expected output format:
# <section_name>:
# <insn_offset>:  <raw_bytes>    <mnemonic>   <operands>

# Example output:
# xdp_prog:
# 0:   85 00 00 00 01 00 00 00    call 1        ; helper #1
# 8:   15 00 02 00 00 00 00 00    if r0 == 0 goto +2
# 10:  07 01 00 00 01 00 00 00    r1 += 1
# 18:  db 10 00 00 00 00 00 00    *(u64 *)(r0 + 0) += r1
# 20:  b7 00 00 00 02 00 00 00    r0 = 2
# 28:  95 00 00 00 00 00 00 00    exit
```

### Inspecting Loaded Programs with bpftool

```bash
# List all loaded BPF programs
bpftool prog show

# Output:
# 42: xdp  name count_packets  tag 3b185187f1855c4c  gpl
#    loaded_at 2024-01-15T10:30:00+0000  uid 0
#    xlated 80B  jited 56B  memlock 4096B  map_ids 5
#    btf_id 42

# Dump translated (verified) BPF bytecode
bpftool prog dump xlated id 42

# Dump JIT-compiled native code
bpftool prog dump jited id 42

# Show verifier log for a program load
bpftool prog load my_prog.bpf.o /sys/fs/bpf/my_prog \
    --debug 2>&1 | head -100
# The --debug flag prints the full verifier log

# Check instruction count
bpftool prog show id 42 | grep xlated
# xlated 80B → 80 bytes / 8 bytes per insn = 10 instructions
```

### Verifier Log Format

```
  VERIFIER LOG EXAMPLE (with -d flag):
  
  0: (18) r1 = 0xffff888100000000  ; load map ptr
  2: (85) call unknown#1            ; map_lookup_elem
  3: R0=map_value_or_null(id=1,off=0,ks=4,vs=8)
  ; ^^^ Register state after instruction
  ;     R0 is pointer to map value, possibly NULL
  ;     id=1 (map fd 1), off=0, key_size=4, val_size=8
  
  3: (15) if r0 == 0x0 goto pc+2   ; null check
  
  ; After jump (null branch, R0 == NULL):
  from 3 to 6: R0=inv(id=0)        ; R0 is now "invalid" (null)
  6: (b7) r0 = 2
  7: (95) exit
  
  ; After no-jump (non-null branch, R0 != NULL):
  4: (07) r1 = 1
  5: (db) *(u64 *)(r0+0) += r1    ; safe: R0 is map_value, not NULL
  
  COMMON VERIFIER ERRORS:
  
  "R1 type=inv expected=fp"
      → Argument to helper must be stack pointer, but R1 is unknown
      
  "invalid indirect read from stack off -8+0 size 8"
      → Reading from stack before writing to it
      
  "math between fp pointer and register with unbounded min value"
      → Using unbounded value as stack offset (must mask first)
      
  "the call stack of 8 frames is too deep !"
      → BPF2BPF call depth exceeded 8 levels
      
  "back-edge from insn X to Y"
      → Detected loop without verifier-provable termination
      
  "BPF program is too large. Processed 1000001 insn"
      → Exceeded 1M verifier complexity limit
```

---

## 18. Mental Models and Expert Intuition

### Mental Model 1: The Verifier as a Type Checker

Think of the verifier as a **dependent type system** for memory safety:

```
  REGULAR TYPE SYSTEM:        BPF VERIFIER (extended type system):
  
  int x;                      r1: SCALAR, range=[0, 65535]
  char *p;                    r2: PTR_TO_MAP_VALUE, offset=0, size=8
  void *q;                    r3: PTR_TO_STACK, offset=-8
                              r4: PTR_TO_PACKET, verified_to=data+14
  
  int y = *p;   (safe)        *(u32 *)(r2 + 4)   (safe: 4+4=8 ≤ val_size)
  int z = *q;   (unsafe)      *(u32 *)(r2 + 6)   (UNSAFE: 6+4=10 > 8)
  
  The verifier does what a compiler does for types,
  but for MEMORY SAFETY with VALUE RANGES.
```

### Mental Model 2: Instructions as a Currency

```
  PRE-5.2 BUDGET: 4,096 instructions
  POST-5.2 BUDGET: 1,000,000 verifier states (not just instructions)
  
  Cost table (approximate):
  
  ┌─────────────────────────────────────┬────────────────────┐
  │  Operation                          │  Cost              │
  ├─────────────────────────────────────┼────────────────────┤
  │  Simple ALU (add, mov, etc.)        │  1 instruction     │
  │  64-bit immediate load (BPF_IMM64)  │  2 instructions    │
  │  Map lookup/update helper call      │  1 insn + overhead │
  │  Bounds check + pointer deref       │  2-3 instructions  │
  │  Protocol header parse (Ethernet)   │  ~5 instructions   │
  │  Protocol header parse (IP + var)   │  ~10 instructions  │
  │  BPF2BPF function call              │  1 insn (not inline)│
  │  Tail call                          │  1 insn            │
  │  Atomic operation                   │  1 instruction     │
  └─────────────────────────────────────┴────────────────────┘
  
  BUDGET USAGE FOR COMMON PROGRAMS:
  
  Simple counter:       ~10 instructions     (0.001% of 1M)
  Packet classifier:    ~200 instructions    (0.02% of 1M)
  Full TCP parser:      ~500 instructions    (0.05% of 1M)
  L7 HTTP inspector:    ~5000 instructions   (0.5% of 1M)
  Complex LSM policy:   ~50000 instructions  (5% of 1M)
  Kernel-bypass proxy:  ~200000 instructions (20% of 1M)
```

### Mental Model 3: The CFG (Control Flow Graph) View

```
  Every BPF program is a DAG (Directed Acyclic Graph) pre-5.3,
  or a CFG with provably-bounded cycles in 5.3+.
  
  Example CFG for the TCP filter:
  
  [Entry]
     │
     ▼
  [Eth bounds check]
     │ fail          │ pass
     ▼               ▼
  [PASS]      [Proto == IP?]
               │ no        │ yes
               ▼           ▼
             [PASS]  [IP bounds check]
                       │ fail     │ pass
                       ▼          ▼
                    [PASS]  [Proto == TCP?]
                              │ no      │ yes
                              ▼         ▼
                           [PASS]  [TCP bounds check]
                                    │ fail     │ pass
                                    ▼          ▼
                                 [PASS]  [Port == 8080?]
                                           │ yes    │ no
                                           ▼        ▼
                                        [DROP]   [PASS]
  
  The verifier walks ALL paths in this graph.
  Each node = a program state to verify.
  Total nodes ≈ 12 for this program.
  With state pruning: might be even fewer.
```

### Cognitive Principle: Chunking for eBPF

**Chunking** (cognitive science) means grouping related concepts into a single mental unit that can be recalled as one piece.

Build these eBPF chunks:

```
  CHUNK 1: "Bounds Check Pattern"
  ptr = data + offset;
  if (ptr + sizeof(T) > data_end) return PASS;
  access *ptr safely;
  → Memorize this as ONE pattern, not 3 separate lines.
  
  CHUNK 2: "Map Lookup Pattern"  
  key = compute_key();
  val = bpf_map_lookup_elem(&map, &key);
  if (!val) return PASS;
  use *val;
  → Same 4-line pattern every time. Recognize it instantly.
  
  CHUNK 3: "Ring Buffer Event Pattern"
  event = bpf_ringbuf_reserve(&rb, sizeof(*event), 0);
  if (!event) return 0;
  fill_event(event, ...);
  bpf_ringbuf_submit(event, 0);
  → Emit events to userspace: always this 4-step sequence.
```

---

## 19. Quick Reference — All Opcodes

### ALU/ALU64 Opcode Table

```
  FORMAT: opcode = cls | src | code
  cls: ALU=0x04, ALU64=0x07
  src: K(imm)=0x00, X(reg)=0x08
  
  ┌────────┬─────────────────────────────────────────────────────────┐
  │ code   │ ALU_K  ALU_X  ALU64_K  ALU64_X   Operation             │
  ├────────┼─────────────────────────────────────────────────────────┤
  │ 0x00   │ 0x04   0x0c   0x07     0x0f      dst += src/imm        │
  │ 0x10   │ 0x14   0x1c   0x17     0x1f      dst -= src/imm        │
  │ 0x20   │ 0x24   0x2c   0x27     0x2f      dst *= src/imm        │
  │ 0x30   │ 0x34   0x3c   0x37     0x3f      dst /= src/imm        │
  │ 0x40   │ 0x44   0x4c   0x47     0x4f      dst |= src/imm        │
  │ 0x50   │ 0x54   0x5c   0x57     0x5f      dst &= src/imm        │
  │ 0x60   │ 0x64   0x6c   0x67     0x6f      dst <<= src/imm       │
  │ 0x70   │ 0x74   0x7c   0x77     0x7f      dst >>= src/imm (log) │
  │ 0x80   │ 0x84   0x8c   0x87     0x8f      dst = -dst            │
  │ 0x90   │ 0x94   0x9c   0x97     0x9f      dst %= src/imm        │
  │ 0xa0   │ 0xa4   0xac   0xa7     0xaf      dst ^= src/imm        │
  │ 0xb0   │ 0xb4   0xbc   0xb7     0xbf      dst = src/imm         │
  │ 0xc0   │ 0xc4   0xcc   0xc7     0xcf      dst >>= src/imm (arith)│
  │ 0xd0   │ 0xd4   0xdc   0xd7     0xdf      endian swap           │
  └────────┴─────────────────────────────────────────────────────────┘
```

### JMP/JMP32 Opcode Table

```
  cls: JMP=0x05, JMP32=0x06
  src: K=0x00, X=0x08
  
  ┌────────┬─────────────────────────────────────────────────────────┐
  │ code   │ JMP_K  JMP_X  JMP32_K  JMP32_X   Condition             │
  ├────────┼─────────────────────────────────────────────────────────┤
  │ 0x00   │ 0x05   n/a    n/a      n/a        always (JA)           │
  │ 0x10   │ 0x15   0x1d   0x16     0x1e       dst == src/imm (JEQ)  │
  │ 0x20   │ 0x25   0x2d   0x26     0x2e       dst >  src/imm (JGT)  │
  │ 0x30   │ 0x35   0x3d   0x36     0x3e       dst >= src/imm (JGE)  │
  │ 0x40   │ 0x45   0x4d   0x46     0x4e       dst &  src/imm (JSET) │
  │ 0x50   │ 0x55   0x5d   0x56     0x5e       dst != src/imm (JNE)  │
  │ 0x60   │ 0x65   0x6d   0x66     0x6e       dst >  src/imm signed │
  │ 0x70   │ 0x75   0x7d   0x76     0x7e       dst >= src/imm signed │
  │ 0x80   │ 0x85   n/a    n/a      n/a        call (CALL)           │
  │ 0x90   │ 0x95   n/a    n/a      n/a        exit (EXIT)           │
  │ 0xa0   │ 0xa5   0xad   0xa6     0xae       dst <  src/imm (JLT)  │
  │ 0xb0   │ 0xb5   0xbd   0xb6     0xbe       dst <= src/imm (JLE)  │
  │ 0xc0   │ 0xc5   0xcd   0xc6     0xce       dst <  src/imm signed │
  │ 0xd0   │ 0xd5   0xdd   0xd6     0xde       dst <= src/imm signed │
  └────────┴─────────────────────────────────────────────────────────┘
```

### Memory Instruction Opcode Table

```
  Load/Store: opcode = cls | size | mode
  
  CLASS:
    LD  = 0x00, LDX = 0x01, ST  = 0x02, STX = 0x03
  
  SIZE:
    W  = 0x00 (32-bit)
    H  = 0x08 (16-bit)
    B  = 0x10 (8-bit)
    DW = 0x18 (64-bit)
  
  MODE:
    IMM    = 0x00  (load immediate)
    ABS    = 0x20  (cBPF absolute — legacy)
    IND    = 0x40  (cBPF indirect — legacy)
    MEM    = 0x60  (register+offset memory access)
    ATOMIC = 0xc0  (atomic operations)
  
  COMMON COMBINATIONS:
  ┌──────────────────┬────────┬────────────────────────────────┐
  │  Macro           │ Opcode │ Meaning                        │
  ├──────────────────┼────────┼────────────────────────────────┤
  │ BPF_LDX_MEM W   │  0x61  │ r_dst = *(u32*)(r_src + off)   │
  │ BPF_LDX_MEM H   │  0x69  │ r_dst = *(u16*)(r_src + off)   │
  │ BPF_LDX_MEM B   │  0x71  │ r_dst = *(u8 *)(r_src + off)   │
  │ BPF_LDX_MEM DW  │  0x79  │ r_dst = *(u64*)(r_src + off)   │
  │ BPF_STX_MEM W   │  0x63  │ *(u32*)(r_dst + off) = r_src   │
  │ BPF_STX_MEM H   │  0x6b  │ *(u16*)(r_dst + off) = r_src   │
  │ BPF_STX_MEM B   │  0x73  │ *(u8 *)(r_dst + off) = r_src   │
  │ BPF_STX_MEM DW  │  0x7b  │ *(u64*)(r_dst + off) = r_src   │
  │ BPF_ST_MEM  W   │  0x62  │ *(u32*)(r_dst + off) = imm32   │
  │ BPF_ST_MEM  DW  │  0x7a  │ *(u64*)(r_dst + off) = imm32   │
  │ BPF_LD_IMM64    │  0x18  │ r_dst = imm64  (wide, 2 slots) │
  └──────────────────┴────────┴────────────────────────────────┘
```

---

## Summary: The Evolution of BPF Instruction Limits

```
  TIMELINE OF BPF INSTRUCTION LIMIT EVOLUTION:
  
  1992  ┌─────────────────────────────────────────────┐
  cBPF  │  cBPF: 2 registers, 32-bit, no maps         │
        │  Limit: BPF_MAXINSNS = 4096 (socket filter) │
        └─────────────────────────────────────────────┘
  
  2014  ┌─────────────────────────────────────────────┐
  3.18  │  eBPF: 11 registers, 64-bit, maps, helpers   │
        │  Limit: 4096 instructions (inherited)        │
        │  No loops, no bpf2bpf                        │
        └─────────────────────────────────────────────┘
  
  2017  ┌─────────────────────────────────────────────┐
  4.14  │  JMP32 added (32-bit conditional jumps)      │
        │  Limit: still 4096                           │
        └─────────────────────────────────────────────┘
  
  2018  ┌─────────────────────────────────────────────┐
  4.16  │  BPF2BPF function calls                      │
        │  Each function: 4096 insns                   │
        │  Limit: 4096 per subprog                     │
        └─────────────────────────────────────────────┘
  
  2019  ┌─────────────────────────────────────────────┐
  5.2   │  BPF_COMPLEXITY_LIMIT_INSNS: 4096 → 1,000,000│
  ★★★  │  Improved state pruning (subset check)       │
        │  Global variables (.data, .rodata sections)  │
        │  Still: CAP_SYS_ADMIN required for > 4096    │
        └─────────────────────────────────────────────┘
  
  2019  ┌─────────────────────────────────────────────┐
  5.3   │  Bounded loops (verifier-verified)           │
        │  Backward jumps allowed if provably bounded  │
        └─────────────────────────────────────────────┘
  
  2020  ┌─────────────────────────────────────────────┐
  5.8   │  CAP_BPF capability (separate from          │
        │  CAP_SYS_ADMIN for privileged BPF)           │
        └─────────────────────────────────────────────┘
  
  2021  ┌─────────────────────────────────────────────┐
  5.12  │  Atomic operations (XCHG, CMPXCHG, FETCH)   │
        └─────────────────────────────────────────────┘
  
  2022  ┌─────────────────────────────────────────────┐
  5.17  │  bpf_loop() helper (callback-based loops)    │
        └─────────────────────────────────────────────┘
  
  TODAY ┌─────────────────────────────────────────────┐
        │  1M verifier complexity limit               │
        │  Effectively: 100K-500K instructions         │
        │  depending on branching complexity           │
        └─────────────────────────────────────────────┘
```

---

## Further Reading

- **Linux kernel source:** `kernel/bpf/verifier.c` — the verifier (heavily commented)
- **Linux kernel source:** `include/linux/bpf.h` — all constants and structs
- **Linux kernel source:** `include/uapi/linux/bpf.h` — userspace API
- **Cilium BPF Reference:** https://docs.cilium.io/en/latest/bpf/
- **eBPF.io:** https://ebpf.io/what-is-ebpf/
- **Aya Book:** https://aya-rs.dev/book/
- **BPF Performance Tools (Gregg):** ISBN 978-0-13-655482-1
- **Kernel docs:** `Documentation/bpf/` in the kernel tree

---

*Guide compiled for deep systems mastery. Every byte counts — and now, up to 8 million of them.*

Here is your complete guide. Here's what's covered across 19 deep sections:

**Architecture & Encoding**
The guide starts from first principles — what a register-based VM is, why eBPF exists, and then drills into the exact 64-bit instruction encoding at the bit level. Every field (opcode, dst, src, off, imm) is explained with binary diagrams. The only 16-byte wide instruction (`BPF_LD_IMM64`) is explained with its dual-slot layout.

**All Instruction Classes**
Every class (ALU, ALU64, JMP, JMP32, LD, LDX, ST, STX, Atomic) is covered with full opcode tables, ASCII memory diagrams, arithmetic vs logical shift distinction, and the `tnum` (tracked number) system the verifier uses internally.

**The 4096 → 1M Transition (the core of your question)**
Four reasons why 4096 existed (verifier complexity explosion, DoS prevention, stack interaction, design philosophy), what was impossible with it (XDP parsers, tracing programs, LSM policies), and exactly what changed in 5.2 — including the critical distinction between `BPF_MAXINSNS` (still 4096 for cBPF) and `BPF_COMPLEXITY_LIMIT_INSNS` (raised to 1M). The "1M" is **verifier states visited**, not file instructions — a key insight most guides miss.

**Verifier Deep Dive**
Abstract interpretation, register state types, the subset pruning algorithm, and the `tnum` 128-bit tracking structure — explained with decision trees and code.

**C & Rust (Aya) Implementations**
Five full C examples with disassembly annotations and verifier state comments. Three full Rust/Aya examples including userspace map reading with Tokio. Build commands for both ecosystems.

**Expert Patterns**
State explosion prevention, `__always_inline` vs `__noinline` tradeoffs, tnum range exploitation via masking, and CFG-aware program design.