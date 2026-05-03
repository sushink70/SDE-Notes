# eBPF: The Complete In-Depth Guide
## C & Rust Implementation — Architecture, Internals, and Real-World Usage

---

## Table of Contents

1. [What Is eBPF — History & Mental Model](#1-what-is-ebpf)
2. [Linux Kernel Architecture & Where eBPF Lives](#2-linux-kernel-architecture)
3. [The BPF Virtual Machine — Registers, ISA, ABI](#3-bpf-virtual-machine)
4. [eBPF Program Lifecycle](#4-ebpf-program-lifecycle)
5. [The Verifier — Safety Enforcement Engine](#5-the-verifier)
6. [JIT Compilation](#6-jit-compilation)
7. [eBPF Program Types — Complete Reference](#7-ebpf-program-types)
8. [eBPF Maps — Every Type Explained](#8-ebpf-maps)
9. [Helper Functions](#9-helper-functions)
10. [BTF — BPF Type Format](#10-btf-bpf-type-format)
11. [CO-RE — Compile Once Run Everywhere](#11-co-re)
12. [libbpf — The Official Userspace Library](#12-libbpf)
13. [XDP — eXpress Data Path](#13-xdp)
14. [TC — Traffic Control](#14-tc-traffic-control)
15. [Tracing Programs — kprobe, uprobe, tracepoint, perf\_event](#15-tracing-programs)
16. [LSM — Linux Security Module eBPF](#16-lsm-ebpf)
17. [Cgroup eBPF Programs](#17-cgroup-ebpf)
18. [Socket & Sockmap Programs](#18-socket--sockmap)
19. [Ring Buffer vs Perf Buffer](#19-ring-buffer-vs-perf-buffer)
20. [Writing eBPF in C — Full Project Structure](#20-writing-ebpf-in-c)
21. [Writing eBPF in Rust with Aya](#21-writing-ebpf-in-rust-with-aya)
22. [Toolchain Ecosystem — BCC, bpftool, libbpf-bootstrap](#22-toolchain-ecosystem)
23. [Debugging & Observability](#23-debugging--observability)
24. [eBPF Security — Offense & Defense](#24-ebpf-security)
25. [Real-World Use Cases & Full Examples](#25-real-world-use-cases)

---

## 1. What Is eBPF

### 1.1 Origin Story

BPF (Berkeley Packet Filter) was introduced in 1992 by Steven McCanne and Van Jacobson as a mechanism to efficiently filter network packets in the kernel without copying them to userspace. The original BPF was a simple register-based virtual machine with 2 registers, a fixed instruction set, and one primary use: `tcpdump`.

In 2014, Alexei Starovoitov extended BPF into what we now call **eBPF** (extended BPF). The changes were radical:

- 10 general-purpose 64-bit registers (up from 2)
- A new RISC-like instruction set
- Arbitrary map-based storage
- A verifier that proves program safety
- JIT compilation to native machine code
- Hooks into virtually every kernel subsystem

The original BPF is now called **cBPF** (classic BPF) and is automatically translated to eBPF internally.

### 1.2 The Mental Model

Think of eBPF as a **safe, sandboxed co-processor inside the Linux kernel** that you can program at runtime without loading a kernel module. 

```
Traditional approach:
  [Userspace App] ──syscall──> [Kernel] ──> fixed behavior

Kernel Module approach:
  [Kernel Module] ──insmod──> [Kernel] ──> arbitrary behavior, but DANGEROUS
  (any bug = kernel panic, security hole)

eBPF approach:
  [eBPF Program] ──bpf()──> [Verifier proves safety] ──> [JIT] ──> [Kernel hook]
  (sandboxed, verified, cannot crash kernel, no reboot needed)
```

**Key Properties:**
- **Safe**: The verifier rejects any program that could crash the kernel, loop infinitely, or access invalid memory
- **Efficient**: JIT-compiled to native code, runs at hardware speed
- **Dynamic**: Load/unload at runtime, no reboot, no module
- **Portable**: CO-RE makes programs run across kernel versions
- **Observable**: Shared maps expose kernel data to userspace safely

### 1.3 What eBPF Is NOT

- Not a scripting language running in an interpreter (JIT = native speed)
- Not arbitrary kernel code (verifier enforces strict safety)
- Not limited to networking (tracing, security, scheduling, IPC)
- Not only for experts (libbpf + CO-RE makes it accessible)

---

## 2. Linux Kernel Architecture

### 2.1 Where eBPF Programs Execute

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER SPACE                                    │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │  Your App    │  │  bpftool     │  │  libbpf / BCC / Aya      │  │
│  └──────┬───────┘  └──────┬───────┘  └────────────┬─────────────┘  │
│         │                 │                        │                 │
└─────────┼─────────────────┼────────────────────────┼─────────────────┘
          │  read/write maps│                        │ bpf() syscall
══════════╪═════════════════╪════════════════════════╪═════════════════
          │                 │          KERNEL SPACE  │
          │           ┌─────▼─────────────────────┐  │
          │           │      BPF Subsystem         │◄─┘
          │           │  ┌─────────┐ ┌──────────┐ │
          │           │  │Verifier │ │JIT Engine│ │
          │           │  └─────────┘ └──────────┘ │
          │           │  ┌──────────────────────┐  │
          │           │  │    BPF Maps Store    │  │
          │           │  └──────────────────────┘  │
          │           └──────────────┬──────────────┘
          │                          │ attach
          │              ┌───────────┼────────────────┐
          │              │           │                 │
          ▼              ▼           ▼                 ▼
    ┌──────────┐  ┌──────────┐ ┌──────────┐   ┌──────────┐
    │ BPF Maps │  │  XDP /   │ │kprobes / │   │  LSM /   │
    │(via maps │  │  TC Net  │ │tracepoint│   │  cgroup  │
    │ syscall) │  │  hooks   │ │  hooks   │   │  hooks   │
    └──────────┘  └──────────┘ └──────────┘   └──────────┘
                       │            │                │
                  ┌────▼────┐  ┌────▼────┐     ┌────▼────┐
                  │ Network │  │Scheduler│     │Security │
                  │  Stack  │  │ / VFS   │     │Framework│
                  └─────────┘  └─────────┘     └─────────┘
```

### 2.2 Hook Points Across the Kernel

```
Packet arrival
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│ NIC Driver (NAPI)                                        │
│     │                                                    │
│     ▼                                                    │
│  [XDP hook] ◄── Earliest possible, before SKB alloc     │
│     │                                                    │
│     ▼                                                    │
│  SKB allocated                                           │
│     │                                                    │
│     ▼                                                    │
│  [TC ingress hook] ◄── After SKB, full packet access    │
│     │                                                    │
│     ▼                                                    │
│  Netfilter / iptables                                    │
│     │                                                    │
│     ▼                                                    │
│  Socket layer                                            │
│  [sock_ops, sk_msg, sk_skb hooks]                        │
│     │                                                    │
│     ▼                                                    │
│  Application (recv)                                      │
│                                                          │
│  On egress path (reversed):                              │
│  [TC egress] ── [XDP_TX] ── Wire                         │
└─────────────────────────────────────────────────────────┘
```

---

## 3. BPF Virtual Machine

### 3.1 Register File

eBPF has **11 registers**, each 64-bit wide. They also support 32-bit sub-register operations (lower 32 bits of each register, zero-extended on write).

```
┌────────┬──────────────────────────────────────────────────────────┐
│Register│ Purpose                                                   │
├────────┼──────────────────────────────────────────────────────────┤
│  r0    │ Return value from BPF helper calls; program exit value   │
│  r1    │ Function arg 1 (also ctx pointer at program entry)       │
│  r2    │ Function arg 2                                           │
│  r3    │ Function arg 3                                           │
│  r4    │ Function arg 4                                           │
│  r5    │ Function arg 5                                           │
│  r6    │ Callee-saved (preserved across helper calls)             │
│  r7    │ Callee-saved                                             │
│  r8    │ Callee-saved                                             │
│  r9    │ Callee-saved                                             │
│  r10   │ Frame pointer (read-only stack pointer)                  │
└────────┴──────────────────────────────────────────────────────────┘
```

**Critical rules enforced by verifier:**
- `r0` must be initialized before program exit
- `r1`–`r5` are NOT preserved across helper calls (scratch registers)
- `r6`–`r9` ARE preserved (callee-saved by BPF calling convention)
- `r10` is always a valid pointer to the top of the BPF stack frame

### 3.2 Instruction Set Architecture

Each BPF instruction is **exactly 8 bytes (64 bits)**:

```
 63      48 47    40 39  36 35   32 31              0
┌──────────┬────────┬──────┬───────┬─────────────────┐
│  imm     │ offset │ src  │  dst  │    opcode       │
│ (32 bit) │(16 bit)│(4bit)│ (4bit)│    (8 bit)      │
└──────────┴────────┴──────┴───────┴─────────────────┘
```

**Opcode breakdown:**
```
Bits [7:5] — Instruction class
  000 = BPF_LD    (load)
  001 = BPF_LDX   (load indirect)
  010 = BPF_ST    (store immediate)
  011 = BPF_STX   (store register)
  100 = BPF_ALU   (32-bit arithmetic)
  101 = BPF_JMP   (jumps and calls)
  110 = BPF_JMP32 (32-bit jumps)
  111 = BPF_ALU64 (64-bit arithmetic)

Bits [4:0] — Operation within class
  ALU operations: ADD, SUB, MUL, DIV, OR, AND, LSH, RSH, NEG,
                  MOD, XOR, MOV, ARSH, END (byte swap)
  JMP operations: JA, JEQ, JGT, JGE, JSET, JNE, JSGT, JSGE,
                  CALL, EXIT, JLT, JLE, JSLT, JSLE
```

**Load/Store sizes:**
```
BPF_B  = 1 byte
BPF_H  = 2 bytes
BPF_W  = 4 bytes
BPF_DW = 8 bytes
```

### 3.3 Stack Frame

Each eBPF program gets a **512-byte stack**. This is a hard limit enforced by the verifier.

```
  r10 (frame pointer) ──► ┌─────────────────┐ high address
                          │  local var 1     │
                          │  local var 2     │
                          │  ...             │
                          │  (max 512 bytes) │
                          └─────────────────┘ low address
```

For passing large data, use BPF maps (especially per-CPU arrays as scratch space).

### 3.4 BPF Calling Convention

```
Caller:
  r1 = arg1
  r2 = arg2
  r3 = arg3
  r4 = arg4
  r5 = arg5
  call helper_func  // or BPF-to-BPF call
  // r0 = return value
  // r1-r5 may be clobbered
  // r6-r9 preserved by callee
```

BPF helper functions follow the same convention with a maximum of **5 arguments**. This is not arbitrary — it matches the System V AMD64 ABI (rdi, rsi, rdx, rcx, r8) enabling direct native calls after JIT.

---

## 4. eBPF Program Lifecycle

### 4.1 Complete Lifecycle

```
Source Code (.bpf.c)
        │
        ▼
   clang/LLVM ──────────────────────────────────────────────────────┐
        │  Compiles to BPF bytecode                                  │
        ▼                                                            │
   ELF Object File (.bpf.o)                                         │
        │  Multiple sections: .text, maps, prog types                │
        ▼                                                            │
   bpf_object__open() / bpf_object__load()                          │
   (libbpf parses ELF, prepares maps and programs)                   │
        │                                                            │
        ▼                                                            │
   bpf() syscall: BPF_MAP_CREATE                                     │
   (kernel creates each map, returns fd)                             │
        │                                                            │
        ▼                                                            │
   bpf() syscall: BPF_PROG_LOAD                                      │
        │                                                            │
        ▼                                                            │
   ┌──────────────────────────────────┐                              │
   │         VERIFIER                 │                              │
   │  - Check instruction count       │                              │
   │  - Prove all paths terminate     │                              │
   │  - Validate pointer arithmetic   │                              │
   │  - Check helper signatures       │                              │
   │  - Track register types          │                              │
   │  PASS ──────────────────────────►│──────────────────────────┐  │
   │  FAIL: returns -EINVAL + log     │                          │  │
   └──────────────────────────────────┘                          │  │
                                                                 ▼  │
                                                         JIT Compiler│
                                                         (arch-specific│
                                                          native code)│
                                                                 │  │
                                                                 ▼  │
                                                         Program FD  │
                                                         returned    │
                                                                 │  │
        ┌────────────────────────────────────────────────────────┘  │
        │                                                            │
        ▼                                                            │
   Attachment (program type specific):                               │
   - XDP: netlink / libbpf / bpf_set_link_xdp_fd()                  │
   - TC: tc qdisc/filter commands                                    │
   - kprobe: perf_event_open() + ioctl(PERF_EVENT_IOC_SET_BPF)       │
   - tracepoint: same as kprobe                                      │
   - cgroup: BPF_PROG_ATTACH                                         │
        │                                                            │
        ▼                                                            │
   Program runs on every hook trigger                                │
        │                                                            │
        ▼                                                            │
   Detach + close(fd) ──► Reference count drops to 0 ──► Unloaded   │
   (programs are ref-counted; pinning to /sys/fs/bpf keeps them)     │
```

### 4.2 File Descriptor Reference Counting

eBPF objects (programs, maps, links) are managed by file descriptors and reference counts:

```
fd = bpf(BPF_PROG_LOAD, ...)   // refcount = 1
│
├── bpf_link_create()           // refcount = 2 (link holds reference)
│   // Even if you close(fd), program stays loaded while link exists
│
├── bpf_obj_pin(fd, "/sys/fs/bpf/myprog")  // pin to bpffs
│   // Survives process exit; pinned until explicitly deleted
│
└── close(fd)                   // refcount decrements
    // If no other refs (links, pins), program unloaded
```

---

## 5. The Verifier

The verifier is arguably the most complex component of eBPF. It is a **static analyzer** that proves program safety before allowing execution.

### 5.1 What the Verifier Checks

```
┌────────────────────────────────────────────────────────────────┐
│                      VERIFIER PASSES                           │
│                                                                │
│  Pass 1: DAG Check                                             │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ - Build control flow graph (CFG)                        │  │
│  │ - Detect unreachable instructions                       │  │
│  │ - Detect back-edges (loops — must be bounded in older   │  │
│  │   kernels; bounded loops allowed since kernel 5.3)      │  │
│  │ - Max instruction count: 1M (was 4096 before 5.2)       │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  Pass 2: Symbolic Execution                                    │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ - Simulate every possible execution path                │  │
│  │ - Track register TYPES:                                 │  │
│  │     NOT_INIT, SCALAR_VALUE, PTR_TO_CTX,                 │  │
│  │     PTR_TO_MAP_VALUE, PTR_TO_STACK,                     │  │
│  │     PTR_TO_PACKET, PTR_TO_PACKET_END,                   │  │
│  │     PTR_TO_SOCK_COMMON, PTR_TO_SOCKET, ...              │  │
│  │ - Track register VALUE RANGES (min/max/umin/umax)       │  │
│  │ - Validate every memory access has bounds check         │  │
│  │ - Validate pointer arithmetic doesn't escape bounds     │  │
│  │ - Validate helper call signatures & arg types           │  │
│  │ - Prune state space via state caching                   │  │
│  └─────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### 5.2 Register State Tracking

For every point in the program, the verifier tracks each register's state:

```c
struct bpf_reg_state {
    enum bpf_reg_type type;    // What kind of pointer or scalar
    
    // For scalar values — range tracking:
    s64 smin_value;   // signed minimum
    s64 smax_value;   // signed maximum
    u64 umin_value;   // unsigned minimum
    u64 umax_value;   // unsigned maximum
    u32 s32_min_value;
    u32 s32_max_value;
    u32 u32_min_value;
    u32 u32_max_value;
    
    // For pointers:
    s32 off;          // fixed offset from base
    u32 id;           // ID to correlate pointer pairs (null checks)
    
    // For map values:
    struct bpf_map *map_ptr;
    
    // For packet pointers:
    int range;        // validated packet access range
};
```

### 5.3 Why This Code Is Rejected

```c
// REJECTED: verifier doesn't know array index is in bounds
int array[10];
int i = get_user_input(); // unknown value
int val = array[i];       // ERROR: unbounded array access

// ACCEPTED: verifier can prove bounds
int i = get_user_input();
if (i < 0 || i >= 10) return 0;  // bounds check
int val = array[i];               // OK: verifier tracks i is [0,9]
```

```c
// REJECTED: dereference without null check
struct value *v = bpf_map_lookup_elem(&my_map, &key);
int x = v->field;  // ERROR: v might be NULL

// ACCEPTED:
struct value *v = bpf_map_lookup_elem(&my_map, &key);
if (!v) return 0;  // null check required
int x = v->field;  // OK: v is proven non-null
```

### 5.4 Bounded Loops (Kernel 5.3+)

Before 5.3, no loops were allowed. Now bounded loops are supported:

```c
// ACCEPTED: verifier can unroll or bound this loop
for (int i = 0; i < 10; i++) {
    // body
}

// ACCEPTED with pragma unroll for older kernels:
#pragma unroll
for (int i = 0; i < 10; i++) {
    // manually unrolled by compiler
}

// REJECTED: verifier can't prove termination
while (some_external_condition()) { // unbounded
    // body
}
```

### 5.5 Verifier Log

When a program is rejected, the verifier outputs a detailed log. You can retrieve it:

```c
char log_buf[65536];
union bpf_attr attr = {
    .prog_type = BPF_PROG_TYPE_XDP,
    .insns = (__u64)(uintptr_t)insns,
    .insn_cnt = insn_cnt,
    .license = (__u64)(uintptr_t)"GPL",
    .log_buf = (__u64)(uintptr_t)log_buf,
    .log_size = sizeof(log_buf),
    .log_level = 2,  // 1=errors, 2=+stats, 3=+full state dumps
};
int fd = syscall(SYS_bpf, BPF_PROG_LOAD, &attr, sizeof(attr));
if (fd < 0) {
    fprintf(stderr, "Verifier log:\n%s\n", log_buf);
}
```

---

## 6. JIT Compilation

### 6.1 How JIT Works

After verification, the BPF bytecode is JIT-compiled to native machine code:

```
BPF Instruction:
  BPF_ALU64 | BPF_ADD | BPF_K   (r0 += 5)

x86_64 JIT output:
  48 83 c0 05    add    rax, 0x5

BPF Register → x86_64 Register Mapping:
  r0  → rax
  r1  → rdi
  r2  → rsi
  r3  → rdx
  r4  → rcx
  r5  → r8
  r6  → rbx
  r7  → r13
  r8  → r14
  r9  → r15
  r10 → rbp (frame pointer)
```

### 6.2 Enabling JIT

```bash
# Check JIT status
cat /proc/sys/net/core/bpf_jit_enable
# 0 = disabled (interpreter only)
# 1 = JIT enabled
# 2 = JIT enabled + dump JIT code to dmesg

# Enable JIT
sysctl -w net.core.bpf_jit_enable=1

# Enable JIT hardening (against spectre/meltdown)
sysctl -w net.core.bpf_jit_harden=2
# 1 = harden unprivileged programs only
# 2 = harden all programs (constant blinding)
```

### 6.3 Viewing JIT Output

```bash
# Enable JIT dump
sysctl -w net.core.bpf_jit_enable=2

# Load your BPF program, then check dmesg
dmesg | grep -A 50 "flen="

# Or use bpftool to disassemble
bpftool prog dump jited id <prog_id>
bpftool prog dump xlated id <prog_id>  # BPF bytecode
```

### 6.4 JIT Support by Architecture

```
x86_64      : Full JIT since kernel 3.15
arm64       : Full JIT since kernel 3.18
arm32       : Full JIT since kernel 4.4
MIPS        : Full JIT since kernel 4.5
PowerPC     : Full JIT since kernel 4.8
s390        : Full JIT since kernel 4.9
SPARC64     : Full JIT since kernel 4.12
RISC-V 64   : Full JIT since kernel 5.1
RISC-V 32   : Full JIT since kernel 5.7
```

---

## 7. eBPF Program Types

Every eBPF program has a **type** that determines:
- What context structure `ctx` points to
- Which helper functions are available
- What return value semantics mean
- Where it can be attached

### 7.1 Complete Program Type Table

```
┌─────────────────────────────────┬─────────────────────────────────────────────────┐
│ Program Type                    │ Use Case                                        │
├─────────────────────────────────┼─────────────────────────────────────────────────┤
│ BPF_PROG_TYPE_SOCKET_FILTER     │ Socket-level packet filtering (original use)    │
│ BPF_PROG_TYPE_KPROBE            │ Kernel function entry/exit tracing              │
│ BPF_PROG_TYPE_SCHED_CLS         │ TC classifier (ingress/egress)                  │
│ BPF_PROG_TYPE_SCHED_ACT         │ TC action                                       │
│ BPF_PROG_TYPE_TRACEPOINT        │ Static kernel tracepoints                       │
│ BPF_PROG_TYPE_XDP               │ eXpress Data Path (pre-SKB networking)          │
│ BPF_PROG_TYPE_PERF_EVENT        │ Hardware/software perf events                   │
│ BPF_PROG_TYPE_CGROUP_SKB        │ cgroup-level socket filtering                   │
│ BPF_PROG_TYPE_CGROUP_SOCK       │ cgroup socket creation control                  │
│ BPF_PROG_TYPE_LWT_IN/OUT/XMIT   │ Lightweight tunnel hooks                        │
│ BPF_PROG_TYPE_SOCK_OPS          │ TCP connection event callbacks                  │
│ BPF_PROG_TYPE_SK_SKB            │ Socket-to-socket steering (sockmap)             │
│ BPF_PROG_TYPE_CGROUP_DEVICE     │ Device access control per cgroup                │
│ BPF_PROG_TYPE_SK_MSG            │ Message-level socket filtering/redirection      │
│ BPF_PROG_TYPE_RAW_TRACEPOINT    │ Raw tracepoints (no argument rewriting)         │
│ BPF_PROG_TYPE_CGROUP_SOCK_ADDR  │ Override connect()/bind() addresses             │
│ BPF_PROG_TYPE_LWT_SEG6LOCAL     │ SRv6 segment routing                            │
│ BPF_PROG_TYPE_LIRC_MODE2        │ IR (infrared) decoding                          │
│ BPF_PROG_TYPE_SK_REUSEPORT      │ SO_REUSEPORT socket selection                   │
│ BPF_PROG_TYPE_FLOW_DISSECTOR    │ Custom flow key dissection                      │
│ BPF_PROG_TYPE_CGROUP_SYSCTL     │ sysctl read/write control per cgroup            │
│ BPF_PROG_TYPE_RAW_TRACEPOINT_WRITABLE│ Writable raw tracepoints                  │
│ BPF_PROG_TYPE_CGROUP_SOCKOPT    │ Override getsockopt/setsockopt per cgroup       │
│ BPF_PROG_TYPE_TRACING           │ fentry/fexit/fmod_ret — BTF-based tracing       │
│ BPF_PROG_TYPE_STRUCT_OPS        │ Implement kernel struct operations in BPF       │
│ BPF_PROG_TYPE_EXT               │ BPF function replacement/extension              │
│ BPF_PROG_TYPE_LSM               │ Linux Security Module hooks                     │
│ BPF_PROG_TYPE_SK_LOOKUP         │ Custom socket lookup/dispatch                   │
│ BPF_PROG_TYPE_SYSCALL           │ BPF program that can call syscalls              │
│ BPF_PROG_TYPE_NETFILTER         │ Netfilter hook (kernel 6.4+)                    │
└─────────────────────────────────┴─────────────────────────────────────────────────┘
```

### 7.2 Context Structures by Program Type

The `ctx` pointer type is program-type-specific:

```c
// XDP programs receive:
struct xdp_md {
    __u32 data;           // pointer to packet start
    __u32 data_end;       // pointer past packet end
    __u32 data_meta;      // pointer to metadata area
    __u32 ingress_ifindex;// incoming interface index
    __u32 rx_queue_index; // RX queue index
    __u32 egress_ifindex; // egress interface (XDP redirect)
};

// TC programs receive:
struct __sk_buff {
    __u32 len;
    __u32 pkt_type;
    __u32 mark;
    __u32 queue_mapping;
    __u32 protocol;
    __u32 vlan_present;
    __u32 vlan_tci;
    __u32 vlan_proto;
    __u32 priority;
    __u32 ingress_ifindex;
    __u32 ifindex;
    __u32 tc_index;
    __u32 cb[5];
    __u32 hash;
    __u32 tc_classid;
    __u32 data;
    __u32 data_end;
    __u32 napi_id;
    // ... and many more fields
};

// kprobe programs receive:
struct pt_regs {
    // Architecture-specific register state at probe point
    // x86_64: rax, rbx, rcx, rdx, rsi, rdi, rbp, rsp,
    //         r8-r15, rip, eflags, cs, ss, ...
};

// Tracepoint programs receive:
// A struct specific to each tracepoint, defined in BTF
// e.g., for sys_enter_openat:
struct trace_event_raw_sys_enter {
    __u64 __unused;
    long id;        // syscall number
    unsigned long args[6];  // syscall arguments
};

// LSM programs receive the hook-specific arguments
// e.g., bpf_lsm_file_open:
// SEC("lsm/file_open")
// int BPF_PROG(file_open, struct file *file)
```

---

## 8. eBPF Maps

Maps are the **primary data structure in eBPF** — they serve as:
- Communication channel between kernel (BPF) and userspace
- Per-CPU counters, histograms, and statistics
- Configuration data passed into BPF programs
- State maintained across multiple packet/event firings
- Message queues and event streams

### 8.1 Map Anatomy

```
┌────────────────────────────────────────────────────────┐
│                     BPF Map                             │
│                                                         │
│  key_size:   N bytes  (defined at creation)             │
│  value_size: M bytes  (defined at creation)             │
│  max_entries: X       (defined at creation)             │
│  map_type:   enum bpf_map_type                          │
│  map_flags:  BPF_F_NO_PREALLOC, BPF_F_MMAPABLE, ...    │
│                                                         │
│  ┌─────────┬───────────────────────────────────────┐   │
│  │  Key    │  Value                                │   │
│  ├─────────┼───────────────────────────────────────┤   │
│  │  key 1  │  value 1                              │   │
│  │  key 2  │  value 2                              │   │
│  │   ...   │   ...                                 │   │
│  │  key X  │  value X                              │   │
│  └─────────┴───────────────────────────────────────┘   │
│                                                         │
│  Userspace access:  bpf_map_lookup/update/delete_elem   │
│  BPF access:        bpf_map_lookup/update/delete_elem() │
└────────────────────────────────────────────────────────┘
```

### 8.2 All Map Types — In Depth

#### BPF_MAP_TYPE_HASH

General-purpose hash table. Key is hashed, stored in buckets.

```
┌─────────────────────────────────────────────────────┐
│  HASH MAP                                            │
│                                                      │
│  bucket[0]: ── [k1|v1] ──► [k9|v9] ──► NULL         │
│  bucket[1]: ── NULL                                  │
│  bucket[2]: ── [k3|v3] ──► NULL                      │
│  bucket[3]: ── [k2|v2] ──► [k7|v7] ──► NULL         │
│  ...                                                 │
│                                                      │
│  O(1) average lookup, O(n) worst case               │
│  Pre-allocated by default (BPF_F_NO_PREALLOC off)    │
│  Lock-free via per-bucket spinlocks                  │
└─────────────────────────────────────────────────────┘
```

```c
// Definition in BPF program:
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 10000);
    __type(key, __u32);         // 4-byte key (e.g., IP address)
    __type(value, __u64);       // 8-byte value (e.g., packet count)
} pkt_count SEC(".maps");

// Usage in BPF:
__u32 key = ip_src;
__u64 *count = bpf_map_lookup_elem(&pkt_count, &key);
if (count) {
    __sync_fetch_and_add(count, 1);  // atomic increment
} else {
    __u64 init = 1;
    bpf_map_update_elem(&pkt_count, &key, &init, BPF_NOEXIST);
}
```

#### BPF_MAP_TYPE_ARRAY

Fixed-size array. Key is always a 4-byte integer index. Value slots pre-allocated. **Cannot delete entries** (reset to zero instead).

```
┌─────────────────────────────────────────────────────┐
│  ARRAY MAP                                           │
│                                                      │
│  index:  0    1    2    3    ...  max_entries-1      │
│  value: [v0] [v1] [v2] [v3] ... [vN]                │
│                                                      │
│  key is ALWAYS u32 index, key_size must be 4         │
│  Entire array pre-allocated at map creation          │
│  Zero-initialized                                    │
│  Fastest map: O(1) with direct offset calculation    │
│  Ideal for: global counters, config lookup tables    │
└─────────────────────────────────────────────────────┘
```

```c
struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 256);       // 256 slots (e.g., one per protocol)
    __type(key, __u32);
    __type(value, __u64);
} proto_stats SEC(".maps");

// In BPF:
__u32 proto = ctx->protocol;
__u64 *stat = bpf_map_lookup_elem(&proto_stats, &proto);
if (stat)
    __sync_fetch_and_add(stat, 1);
```

#### BPF_MAP_TYPE_PERCPU_HASH / BPF_MAP_TYPE_PERCPU_ARRAY

Per-CPU variants. Each CPU has its own copy of each value. No locking needed. Userspace reads all CPUs and aggregates.

```
┌───────────────────────────────────────────────────────────┐
│  PER-CPU ARRAY (4 CPUs, 3 entries)                         │
│                                                            │
│         CPU0    CPU1    CPU2    CPU3                        │
│  [0]:  [val0]  [val0]  [val0]  [val0]                      │
│  [1]:  [val1]  [val1]  [val1]  [val1]                      │
│  [2]:  [val2]  [val2]  [val2]  [val2]                      │
│                                                            │
│  BPF writes to its own CPU's slot — zero contention        │
│  Userspace reads: value_size * num_cpus bytes per entry    │
└───────────────────────────────────────────────────────────┘
```

```c
// Userspace reading per-CPU map:
int ncpus = libbpf_num_possible_cpus();
__u64 *values = calloc(ncpus, sizeof(__u64));
__u32 key = 0;
bpf_map_lookup_elem(map_fd, &key, values);

__u64 total = 0;
for (int i = 0; i < ncpus; i++)
    total += values[i];
```

#### BPF_MAP_TYPE_LRU_HASH / BPF_MAP_TYPE_LRU_PERCPU_HASH

Like HASH but with **Least Recently Used** eviction. When full, oldest entry is automatically removed. Ideal for connection tracking, caches.

```
┌─────────────────────────────────────────────────────┐
│  LRU HASH (max_entries=3, now inserting 4th)         │
│                                                      │
│  Before:                                             │
│    LRU ──► [k1,v1] ──► [k2,v2] ──► [k3,v3] ◄── MRU │
│                         ↑ oldest                     │
│                                                      │
│  Insert k4:                                          │
│    k1 evicted (LRU), k4 becomes MRU                  │
│    LRU ──► [k2,v2] ──► [k3,v3] ──► [k4,v4] ◄── MRU │
└─────────────────────────────────────────────────────┘
```

#### BPF_MAP_TYPE_PROG_ARRAY

Stores references to other BPF programs. Used for **tail calls** — jumping from one BPF program to another without returning.

```
┌─────────────────────────────────────────────────────────┐
│  TAIL CALL MECHANICS                                     │
│                                                          │
│  prog_array map:                                         │
│    [0] → prog_handle_tcp                                 │
│    [1] → prog_handle_udp                                 │
│    [2] → prog_handle_icmp                                │
│                                                          │
│  XDP main program:                                       │
│    if (protocol == TCP)                                  │
│        bpf_tail_call(ctx, &prog_array, 0)               │
│    // If tail call succeeds, we never return here        │
│    // If prog_array[0] is empty, execution continues     │
│                                                          │
│  Stack depth NOT accumulated across tail calls           │
│  Max 33 tail calls per packet (prevents loops)           │
│  Current stack frame is REUSED (not nested)              │
└─────────────────────────────────────────────────────────┘
```

```c
struct {
    __uint(type, BPF_MAP_TYPE_PROG_ARRAY);
    __uint(max_entries, 8);
    __type(key, __u32);
    __type(value, __u32);  // program fd (at load time)
} jump_table SEC(".maps");

SEC("xdp")
int xdp_main(struct xdp_md *ctx) {
    // Parse protocol, jump to handler
    __u32 idx = get_protocol_index(ctx);
    bpf_tail_call(ctx, &jump_table, idx);
    // Falls through only if tail call fails
    return XDP_PASS;
}
```

#### BPF_MAP_TYPE_PERF_EVENT_ARRAY

Efficient **streaming** of events from BPF to userspace via the perf subsystem. Each CPU has a ring buffer. Older approach; prefer BPF_MAP_TYPE_RINGBUF for new code.

```
┌────────────────────────────────────────────────────────────┐
│  PERF EVENT ARRAY                                           │
│                                                            │
│  map: one slot per CPU                                     │
│    [0] → perf_event_fd(CPU0)                               │
│    [1] → perf_event_fd(CPU1)                               │
│    ...                                                     │
│                                                            │
│  BPF side:                                                 │
│    bpf_perf_event_output(ctx, &events, BPF_F_CURRENT_CPU, │
│                          &data, sizeof(data))              │
│                                                            │
│  Userspace side:                                           │
│    mmap() each perf_event ring, poll for events            │
│    libbpf: perf_buffer__new() / perf_buffer__poll()        │
└────────────────────────────────────────────────────────────┘
```

#### BPF_MAP_TYPE_RINGBUF (kernel 5.8+)

The modern replacement for perf event array. **Single shared ring buffer** across all CPUs. More efficient, simpler userspace API.

```
┌────────────────────────────────────────────────────────────┐
│  RING BUFFER                                               │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Consumer position (userspace reads)               │   │
│  │      ↓                                             │   │
│  │  ╔═══╦═══╦═══╦═══╦═══╦═══╦═══╦═══╦═══╗           │   │
│  │  ║hdr║dat║hdr║dat║hdr║dat║hdr║dat║   ║  ...       │   │
│  │  ╚═══╩═══╩═══╩═══╩═══╩═══╩═══╩═══╩═══╝           │   │
│  │                              ↑                     │   │
│  │  Producer position (BPF writes)                    │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  Features:                                                 │
│  - Memory-mapped: zero-copy reads from userspace           │
│  - Discard support: reserve then conditionally discard     │
│  - Automatic spinlock protection per producer              │
│  - Wakeup via epoll/poll                                   │
└────────────────────────────────────────────────────────────┘
```

```c
// BPF side:
struct event {
    __u32 pid;
    __u64 timestamp;
    char comm[16];
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 1 << 24);  // 16MB ring buffer
} rb SEC(".maps");

SEC("kprobe/do_sys_openat2")
int trace_openat(struct pt_regs *ctx) {
    struct event *e;
    
    // Reserve space (returns NULL if ring is full)
    e = bpf_ringbuf_reserve(&rb, sizeof(*e), 0);
    if (!e) return 0;
    
    e->pid = bpf_get_current_pid_tgid() >> 32;
    e->timestamp = bpf_ktime_get_ns();
    bpf_get_current_comm(e->comm, sizeof(e->comm));
    
    // Submit (or discard if we changed our mind)
    bpf_ringbuf_submit(e, 0);
    return 0;
}

// Userspace:
struct ring_buffer *rb = ring_buffer__new(map_fd, handle_event, NULL, NULL);
while (1)
    ring_buffer__poll(rb, 100 /* timeout ms */);
```

#### BPF_MAP_TYPE_STACK_TRACE

Stores kernel/user stack traces (arrays of instruction pointers). Used with perf events for flame graph generation.

```c
struct {
    __uint(type, BPF_MAP_TYPE_STACK_TRACE);
    __uint(max_entries, 10000);
    __uint(key_size, sizeof(__u32));
    __uint(value_size, PERF_MAX_STACK_DEPTH * sizeof(__u64));
} stack_traces SEC(".maps");

// In BPF:
__u64 stack_id = bpf_get_stackid(ctx, &stack_traces, 0);
// Store stack_id in another map keyed by PID
```

#### BPF_MAP_TYPE_SOCKMAP / BPF_MAP_TYPE_SOCKHASH

Stores references to sockets. Used to redirect socket data, implement transparent proxies, accelerate localhost communication.

```c
struct {
    __uint(type, BPF_MAP_TYPE_SOCKMAP);
    __uint(max_entries, 65535);
    __type(key, int);
    __type(value, int);  // socket fd at creation, sock ptr at runtime
} sock_map SEC(".maps");

// In sk_skb program: redirect to another socket
bpf_sk_redirect_map(skb, &sock_map, target_key, 0);
```

#### BPF_MAP_TYPE_CPUMAP / BPF_MAP_TYPE_DEVMAP / BPF_MAP_TYPE_XSKMAP

Specialized maps for XDP:
- **CPUMAP**: Redirect packet to a different CPU for processing
- **DEVMAP**: Redirect packet to a different network interface
- **XSKMAP**: Redirect packet to an AF_XDP socket (kernel-bypass)

#### BPF_MAP_TYPE_BLOOM_FILTER (kernel 5.16+)

Probabilistic data structure. Fast membership testing with no false negatives, possible false positives.

```c
struct {
    __uint(type, BPF_MAP_TYPE_BLOOM_FILTER);
    __uint(max_entries, 100000);
    __type(value, __u32);  // only value_size, no key
    __uint(map_extra, 3);  // number of hash functions
} ip_blocklist SEC(".maps");

// Add to bloom filter (BPF_MAP_UPDATE_ELEM):
bpf_map_push_elem(&ip_blocklist, &ip, 0);

// Check membership (BPF_MAP_LOOKUP_ELEM):
// key is irrelevant, value is what's checked
if (bpf_map_peek_elem(&ip_blocklist, &ip) == 0) {
    // Probably in filter (may be false positive)
}
```

#### BPF_MAP_TYPE_QUEUE / BPF_MAP_TYPE_STACK

FIFO queue and LIFO stack maps. No keys — push/pop operations only.

```c
struct {
    __uint(type, BPF_MAP_TYPE_QUEUE);
    __uint(max_entries, 1000);
    __type(value, struct work_item);
} work_queue SEC(".maps");

// BPF: push
bpf_map_push_elem(&work_queue, &item, BPF_EXIST /* overwrite if full */);

// Userspace: pop
struct work_item item;
bpf_map_pop_elem(map_fd, &item); // pops front (FIFO)
```

### 8.3 Map Flags

```
BPF_F_NO_PREALLOC     — Don't pre-allocate memory (for large hash maps)
BPF_F_NO_COMMON_LRU   — Per-CPU LRU lists (faster, less sharing)
BPF_F_NUMA_NODE       — Allocate on specific NUMA node
BPF_F_RDONLY          — Read-only from BPF side
BPF_F_WRONLY          — Write-only from BPF side
BPF_F_STACK_BUILD_ID  — Stack trace stores build IDs
BPF_F_ZERO_SEED       — Use zero hash seed (deterministic but less secure)
BPF_F_RDONLY_PROG     — Read-only from BPF programs
BPF_F_WRONLY_PROG     — Write-only from BPF programs
BPF_F_CLONE           — Allow cloning the map
BPF_F_MMAPABLE        — Allow mmap() of array map (zero-copy userspace read)
BPF_F_PRESERVE_ELEMS  — Don't free elements on map deletion
BPF_F_INNER_MAP       — Map of maps inner map template
```

### 8.4 Map of Maps

```c
// Inner map definition (template)
struct inner_map {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 100);
    __type(key, __u32);
    __type(value, __u64);
} inner_map_proto SEC(".maps");

// Outer map containing inner maps
struct {
    __uint(type, BPF_MAP_TYPE_HASH_OF_MAPS);
    __uint(max_entries, 1000);
    __type(key, __u32);           // e.g., network namespace ID
    __array(values, struct inner_map);  // inner map type
} outer_map SEC(".maps") = {
    .values = {[0] = &inner_map_proto},  // template for inner maps
};

// In BPF: look up inner map by netns ID, then look up in inner map
void *inner = bpf_map_lookup_elem(&outer_map, &netns_id);
if (inner) {
    __u64 *val = bpf_map_lookup_elem(inner, &key);
}
```

### 8.5 Userspace Map Operations

```c
#include <bpf/libbpf.h>

// Lookup
__u32 key = 42;
__u64 value;
int err = bpf_map_lookup_elem(map_fd, &key, &value);

// Update
__u64 new_val = 100;
err = bpf_map_update_elem(map_fd, &key, &new_val, BPF_ANY);
// Flags: BPF_ANY (create or update)
//        BPF_NOEXIST (create only, fail if exists)
//        BPF_EXIST (update only, fail if not exists)

// Delete
err = bpf_map_delete_elem(map_fd, &key);

// Iterate all entries (hash maps):
__u32 prev_key, curr_key;
void *value_buf = malloc(value_size);
// Start iteration with NULL prev_key
while (bpf_map_get_next_key(map_fd, &prev_key, &curr_key) == 0) {
    bpf_map_lookup_elem(map_fd, &curr_key, value_buf);
    // process...
    prev_key = curr_key;
}

// Batch operations (kernel 5.6+):
DECLARE_LIBBPF_OPTS(bpf_map_batch_opts, batch_opts);
__u32 keys[100], count = 100;
__u64 values[100];
bpf_map_lookup_batch(map_fd, &in_batch, &out_batch,
                     keys, values, &count, &batch_opts);
```

---

## 9. Helper Functions

Helper functions are the **kernel API for BPF programs** — they allow BPF code to perform operations that require kernel privileges.

### 9.1 Helper Categories

```
┌──────────────────────────────────────────────────────────────────┐
│  MAP HELPERS                                                      │
│  bpf_map_lookup_elem()     — Look up key in map                  │
│  bpf_map_update_elem()     — Create/update map entry             │
│  bpf_map_delete_elem()     — Delete map entry                    │
│  bpf_map_push_elem()       — Push to queue/stack map             │
│  bpf_map_pop_elem()        — Pop from queue/stack map            │
│  bpf_map_peek_elem()       — Peek queue/stack without removing   │
│  bpf_for_each_map_elem()   — Iterate map with callback           │
├──────────────────────────────────────────────────────────────────┤
│  TIME & RANDOM                                                    │
│  bpf_ktime_get_ns()        — Monotonic clock in nanoseconds      │
│  bpf_ktime_get_boot_ns()   — Boot-relative clock                 │
│  bpf_ktime_get_real_ns()   — Wall clock (CLOCK_REALTIME)         │
│  bpf_ktime_get_coarse_ns() — Low-precision but faster            │
│  bpf_get_prandom_u32()     — Pseudo-random 32-bit number         │
├──────────────────────────────────────────────────────────────────┤
│  PROCESS/TASK INFO                                                │
│  bpf_get_current_pid_tgid()— Current PID (lower) and TGID (upper)│
│  bpf_get_current_uid_gid() — Current UID and GID                 │
│  bpf_get_current_comm()    — Current task name (up to 16 bytes)  │
│  bpf_get_current_task()    — Pointer to task_struct              │
│  bpf_get_current_cgroup_id()— Current cgroup ID                  │
│  bpf_get_ns_current_pid_tgid()— PID in specific namespace        │
├──────────────────────────────────────────────────────────────────┤
│  NETWORKING (XDP/TC)                                              │
│  bpf_skb_load_bytes()      — Read bytes from sk_buff             │
│  bpf_skb_store_bytes()     — Write bytes to sk_buff              │
│  bpf_skb_pull_data()       — Ensure data is in linear region     │
│  bpf_skb_change_head()     — Add/remove bytes at start           │
│  bpf_skb_change_tail()     — Add/remove bytes at end             │
│  bpf_skb_adjust_room()     — Grow/shrink sk_buff                 │
│  bpf_l3_csum_replace()     — Update L3 checksum after edit       │
│  bpf_l4_csum_replace()     — Update L4 checksum after edit       │
│  bpf_redirect()            — Redirect packet to different iface  │
│  bpf_redirect_map()        — Redirect via DEVMAP/CPUMAP/XSKMAP   │
│  bpf_clone_redirect()      — Clone packet then redirect          │
│  bpf_xdp_adjust_head()     — Move data pointer (add/remove hdr) │
│  bpf_xdp_adjust_tail()     — Grow/shrink XDP packet             │
│  bpf_xdp_adjust_meta()     — Adjust metadata area               │
│  bpf_fib_lookup()          — Kernel FIB lookup (routing)        │
├──────────────────────────────────────────────────────────────────┤
│  TRACING / OUTPUT                                                 │
│  bpf_trace_printk()        — Debug output to /sys/kernel/debug/  │
│                              tracing/trace_pipe (SLOW, debugging) │
│  bpf_perf_event_output()   — Send event to perf ring buffer      │
│  bpf_ringbuf_reserve()     — Reserve space in ring buffer        │
│  bpf_ringbuf_submit()      — Commit reserved data                │
│  bpf_ringbuf_discard()     — Discard reserved data               │
│  bpf_ringbuf_output()      — Reserve + copy + submit in one      │
│  bpf_get_stackid()         — Capture stack trace                 │
│  bpf_read_branch_records() — Read CPU branch records             │
├──────────────────────────────────────────────────────────────────┤
│  MEMORY / CONTEXT                                                 │
│  bpf_probe_read_kernel()   — Safe read from kernel memory        │
│  bpf_probe_read_user()     — Safe read from user memory          │
│  bpf_probe_read_kernel_str()— Safe read kernel string            │
│  bpf_probe_read_user_str() — Safe read user string               │
│  bpf_dynptr_read/write()   — Read/write via dynamic pointer      │
│  bpf_copy_from_user()      — Sleep-able user memory read         │
│  bpf_snprintf()            — Formatted string output to buffer   │
├──────────────────────────────────────────────────────────────────┤
│  SOCKET / FLOW                                                    │
│  bpf_sk_lookup_tcp/udp()   — Look up socket by 4-tuple          │
│  bpf_sk_release()          — Release socket reference            │
│  bpf_sock_map_update()     — Add socket to sockmap               │
│  bpf_msg_redirect_map()    — Redirect message to sockmap entry   │
│  bpf_sk_redirect_map()     — Redirect sk_buff to sockmap entry   │
├──────────────────────────────────────────────────────────────────┤
│  CONTROL / SIGNALING                                              │
│  bpf_tail_call()           — Jump to another BPF program         │
│  bpf_send_signal()         — Send signal to current task         │
│  bpf_send_signal_thread()  — Send signal to current thread       │
│  bpf_override_return()     — Override kprobe return value        │
│  bpf_get_retval()          — Get return value (fmod_ret/lsm)     │
│  bpf_set_retval()          — Set return value (fmod_ret/lsm)     │
└──────────────────────────────────────────────────────────────────┘
```

### 9.2 Helper Availability by Program Type

Not all helpers are available to all program types. The verifier enforces this:

```
                    │ XDP │ TC │ kprobe │ tp │ LSM │ cgroup │
────────────────────┼─────┼────┼────────┼────┼─────┼────────┤
bpf_map_*           │  ✓  │ ✓  │   ✓    │ ✓  │  ✓  │   ✓    │
bpf_ktime_get_ns    │  ✓  │ ✓  │   ✓    │ ✓  │  ✓  │   ✓    │
bpf_get_current_*   │  ✗  │ ✓  │   ✓    │ ✓  │  ✓  │   ✓    │
bpf_redirect        │  ✓  │ ✓  │   ✗    │ ✗  │  ✗  │   ✗    │
bpf_xdp_adjust_head│  ✓  │ ✗  │   ✗    │ ✗  │  ✗  │   ✗    │
bpf_probe_read_*    │  ✗  │ ✗  │   ✓    │ ✓  │  ✗  │   ✗    │
bpf_override_return │  ✗  │ ✗  │   ✓*   │ ✗  │  ✗  │   ✗    │
bpf_send_signal     │  ✗  │ ✗  │   ✓    │ ✓  │  ✓  │   ✗    │
bpf_set_retval      │  ✗  │ ✗  │   ✗    │ ✗  │  ✓  │   ✓    │

* only on error-injectable functions (ALLOW_ERROR_INJECTION)
```

---

## 10. BTF — BPF Type Format

### 10.1 What is BTF?

BTF (BPF Type Format) is a **compact binary format for describing C types and debug information**, similar to DWARF but specifically designed for BPF. It enables:

1. **CO-RE**: Accessing kernel struct fields by name regardless of kernel version
2. **Pretty-printing**: `bpftool` can display map values using their types
3. **Typed maps**: Maps that know the types of their keys and values
4. **Verifier improvements**: Better error messages with type information

### 10.2 BTF Structure

```
┌───────────────────────────────────────────────────────────────┐
│  BTF Binary Format                                             │
│                                                               │
│  ┌─────────────┐                                              │
│  │  BTF Header │  magic, version, header size                 │
│  ├─────────────┤                                              │
│  │  Type Data  │  Array of btf_type structs                   │
│  │             │  Each describes: INT, PTR, ARRAY, STRUCT,    │
│  │             │  UNION, ENUM, FWD, TYPEDEF, VOLATILE,        │
│  │             │  CONST, RESTRICT, FUNC, FUNC_PROTO,          │
│  │             │  VAR, DATASEC, FLOAT, DECL_TAG,              │
│  │             │  TYPE_TAG, ENUM64                            │
│  ├─────────────┤                                              │
│  │ String Data │  NULL-terminated strings (field names,       │
│  │             │  type names, etc.)                           │
│  └─────────────┘                                              │
│                                                               │
│  Compiled by: clang -g -target bpf ... → .BTF section in ELF │
│  Kernel exports: /sys/kernel/btf/vmlinux                      │
│  Query: bpftool btf dump file /sys/kernel/btf/vmlinux         │
└───────────────────────────────────────────────────────────────┘
```

### 10.3 Generating vmlinux.h

```bash
# vmlinux.h contains ALL kernel types extracted from BTF
# Never include linux kernel headers again!
bpftool btf dump file /sys/kernel/btf/vmlinux format c > vmlinux.h

# Then in your BPF program:
#include "vmlinux.h"
// Now you have access to all kernel structs: task_struct, sk_buff, etc.
```

### 10.4 BTF-based Tracing (fentry/fexit)

BTF enables a newer, more efficient alternative to kprobes:

```c
// kprobe style (older, needs pt_regs gymnastics):
SEC("kprobe/tcp_connect")
int BPF_KPROBE(tcp_connect, struct sock *sk) {
    // sk is extracted from pt_regs
}

// fentry style (BTF-based, direct args, faster):
SEC("fentry/tcp_connect")
int BPF_PROG(fentry_tcp_connect, struct sock *sk) {
    // sk is directly available with full type info
    __u16 dport = BPF_CORE_READ(sk, __sk_common.skc_dport);
}

// fexit style (also captures return value):
SEC("fexit/tcp_connect")
int BPF_PROG(fexit_tcp_connect, struct sock *sk, int ret) {
    // ret = return value of tcp_connect
}
```

---

## 11. CO-RE

### 11.1 The Problem CO-RE Solves

Kernel structs change between versions. Field offsets shift. A BPF program compiled against kernel 5.10 headers may access the wrong memory on kernel 5.15 because a struct was reorganized.

```
Kernel 5.10: struct task_struct {
  ...
  pid_t pid;        // offset 1234
  pid_t tgid;       // offset 1238
  ...
}

Kernel 5.15: struct task_struct {
  ...
  // some new field added here
  pid_t pid;        // offset 1242  ← SHIFTED!
  pid_t tgid;       // offset 1246
  ...
}

Without CO-RE: your BPF program reads offset 1234 on 5.15 → WRONG DATA
With CO-RE:    BPF program records "I want task_struct.pid"
               libbpf uses BTF to relocate to correct offset at load time
```

### 11.2 How CO-RE Works

```
Compile time:
  clang produces BPF object with .BTF section (program types)
  and .BTF.ext section (relocation records)
  
  Each CO-RE access generates a relocation record:
    "At instruction offset X, field Y of type Z, apply relocation"

Load time (libbpf):
  1. Load program BTF (what field we WANT)
  2. Load kernel BTF from /sys/kernel/btf/vmlinux (actual layout)
  3. For each relocation:
     - Find struct in kernel BTF
     - Find field in that struct
     - Get actual offset
     - Patch the BPF instruction with correct offset
  4. Load patched program into kernel
```

### 11.3 CO-RE Access Macros

```c
#include "vmlinux.h"
#include <bpf/bpf_core_read.h>

SEC("kprobe/do_sys_openat2")
int BPF_KPROBE(trace_openat, int dfd, const char *filename) {
    struct task_struct *task = (struct task_struct *)bpf_get_current_task();
    
    // CO-RE read — handles layout differences across kernel versions
    pid_t pid = BPF_CORE_READ(task, pid);
    pid_t tgid = BPF_CORE_READ(task, tgid);
    
    // Nested struct access:
    unsigned int ino = BPF_CORE_READ(task, mm, exe_file, f_inode, i_ino);
    
    // Array access:
    __u64 start = BPF_CORE_READ(task, mm, saved_auxv[AT_RANDOM]);
    
    // Bitfield access (CO-RE handles bit extraction):
    unsigned int in_execve = BPF_CORE_READ_BITFIELD(task, in_execve);
    
    // Check if field exists in this kernel version:
    if (bpf_core_field_exists(task->thread_info.syscall_work)) {
        // field exists in this kernel
    }
    
    return 0;
}
```

### 11.4 CO-RE Relocations Types

```
BPF_CORE_FIELD_BYTE_OFFSET  — Field byte offset in struct
BPF_CORE_FIELD_BYTE_SIZE    — Field byte size
BPF_CORE_FIELD_EXISTS       — Does field exist? (0 or 1)
BPF_CORE_FIELD_SIGNED       — Is field signed?
BPF_CORE_FIELD_LSHIFT_U64   — For bitfield extraction
BPF_CORE_FIELD_RSHIFT_U64   — For bitfield extraction
BPF_CORE_TYPE_ID_LOCAL      — Type ID in local BTF
BPF_CORE_TYPE_ID_TARGET     — Type ID in target BTF
BPF_CORE_TYPE_EXISTS        — Does type exist?
BPF_CORE_TYPE_SIZE          — Size of type
BPF_CORE_ENUMVAL_EXISTS     — Does enum value exist?
BPF_CORE_ENUMVAL_VALUE      — Value of named enum constant
```

---

## 12. libbpf

libbpf is the **official, canonical C userspace library** for loading and managing eBPF programs. It handles ELF parsing, BTF loading, CO-RE relocation, map creation, program loading, and attachment.

### 12.1 libbpf Object Model

```
bpf_object (represents an ELF .bpf.o file)
  │
  ├── bpf_map[] (one per map definition in BPF source)
  │     ├── map_fd
  │     ├── map_name
  │     └── map_def (type, key_size, value_size, max_entries)
  │
  └── bpf_program[] (one per SEC() in BPF source)
        ├── prog_fd
        ├── prog_name
        ├── prog_type
        └── bpf_link* (after attachment)

bpf_link (represents an attachment)
  ├── link_fd
  └── detach() / destroy()
```

### 12.2 libbpf Skeleton — The Modern Approach

libbpf-bootstrap generates a **skeleton** — a type-safe C header that wraps your BPF object:

```bash
# During build:
bpftool gen skeleton myprogram.bpf.o > myprogram.skel.h
```

```c
// myprogram.skel.h (auto-generated):
struct myprogram_bpf {
    struct bpf_object_skeleton *skeleton;
    struct bpf_object *obj;
    struct {
        struct bpf_map *my_hash_map;
        struct bpf_map *rb;
    } maps;
    struct {
        struct bpf_program *handle_xdp;
        struct bpf_program *trace_openat;
    } progs;
    struct {
        struct bpf_link *handle_xdp;
        struct bpf_link *trace_openat;
    } links;
    // Direct access to global variables in BPF program:
    struct myprogram_bpf__rodata {
        __u32 target_pid;
    } *rodata;
    struct myprogram_bpf__bss {
        __u64 total_bytes;
    } *bss;
};

// Open/load/attach helpers:
struct myprogram_bpf *myprogram_bpf__open(void);
int myprogram_bpf__load(struct myprogram_bpf *obj);
int myprogram_bpf__attach(struct myprogram_bpf *obj);
void myprogram_bpf__destroy(struct myprogram_bpf *obj);
```

```c
// userspace main.c:
#include "myprogram.skel.h"

int main() {
    // Open ELF object, parse maps/programs
    struct myprogram_bpf *skel = myprogram_bpf__open();
    
    // Set global variable before load:
    skel->rodata->target_pid = getpid();
    
    // Load: create maps, relocate CO-RE, load programs
    myprogram_bpf__load(skel);
    
    // Attach all programs (auto-detects attachment type from SEC()):
    myprogram_bpf__attach(skel);
    
    // Set up ring buffer:
    struct ring_buffer *rb = ring_buffer__new(
        bpf_map__fd(skel->maps.rb), handle_event, NULL, NULL);
    
    // Event loop:
    while (!stop) {
        ring_buffer__poll(rb, 100);
    }
    
    // Cleanup:
    ring_buffer__free(rb);
    myprogram_bpf__destroy(skel);
}
```

### 12.3 Global Variables in BPF Programs

Global variables are backed by array maps and provide a clean way to pass configuration:

```c
// In .bpf.c:
const volatile __u32 target_pid = 0;   // rodata (read-only in BPF)
const volatile bool filter_by_pid = false;

__u64 total_events = 0;                // bss (zero-initialized)
__u64 dropped_events = 0;

// In BPF program:
if (filter_by_pid && bpf_get_current_pid_tgid() >> 32 != target_pid)
    return 0;
__sync_fetch_and_add(&total_events, 1);

// In userspace (via skeleton):
skel->rodata->target_pid = 1234;   // set before load
// After running:
printf("total: %llu\n", skel->bss->total_events);
```

---

## 13. XDP

XDP (eXpress Data Path) hooks into the **earliest possible point** in the network receive path, before memory allocation for socket buffers (sk_buff) occurs.

### 13.1 XDP Architecture

```
NIC receives packet
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│  NIC Driver (NAPI poll)                                        │
│                                                               │
│  DMA: packet placed in RX ring buffer                         │
│                                ┌──────────────────────────┐  │
│  XDP program called ─────────► │  struct xdp_md           │  │
│  (before ANY allocation)       │  data:     packet start  │  │
│                                │  data_end: packet end    │  │
│                                │  data_meta: metadata     │  │
│                                └──────────────────────────┘  │
│                                         │                     │
│                              XDP program returns:             │
│                                         │                     │
│          ┌──────────┬─────────┬─────────┼──────────────┐     │
│          │          │         │         │              │     │
│          ▼          ▼         ▼         ▼              ▼     │
│      XDP_DROP  XDP_PASS  XDP_TX  XDP_REDIRECT  XDP_ABORTED  │
│      (drop it) (kernel  (reflect  (to iface/   (drop+trace) │
│                 stack)  back out)  CPU/XSK)                  │
└───────────────────────────────────────────────────────────────┘
          │                │         │         │
          ▼                │         │         │
      Packet freed         │         │         │
                           │         │         │
                    ┌──────▼──┐ ┌────▼──┐ ┌───▼──────┐
                    │ sk_buff │ │  NIC  │ │ CPU/iface│
                    │ alloc   │ │  TX   │ │ redirect │
                    └─────────┘ └───────┘ └──────────┘
```

### 13.2 XDP Modes

```
┌─────────────────────────────────────────────────────────────────┐
│ NATIVE XDP (offloaded to driver)                                 │
│  - Requires driver support (mlx5, ixgbe, i40e, virtio, etc.)    │
│  - Runs BEFORE sk_buff allocation                                │
│  - Fastest: ~25 million packets/second per core                  │
│  - Set: ip link set dev eth0 xdp obj prog.o                     │
├─────────────────────────────────────────────────────────────────┤
│ GENERIC XDP (SKB-based, in kernel network stack)                 │
│  - Works on ANY network driver                                   │
│  - Runs AFTER sk_buff allocation (slower)                        │
│  - Good for testing without hardware support                     │
│  - Set: ip link set dev eth0 xdpgeneric obj prog.o              │
├─────────────────────────────────────────────────────────────────┤
│ OFFLOADED XDP (runs on SmartNIC)                                 │
│  - Program compiled to NIC-specific instruction set              │
│  - Runs entirely on NIC hardware, zero CPU usage                 │
│  - Requires SmartNIC (Netronome, etc.)                           │
│  - Set: ip link set dev eth0 xdpoffload obj prog.o              │
└─────────────────────────────────────────────────────────────────┘
```

### 13.3 Complete XDP DDoS Protection Example

```c
// ddos_protect.bpf.c
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

#define ETH_P_IP    0x0800
#define IPPROTO_TCP 6
#define IPPROTO_UDP 17

struct pkt_5tuple {
    __u32 src_ip;
    __u32 dst_ip;
    __u16 src_port;
    __u16 dst_port;
    __u8  proto;
} __attribute__((packed));

struct rate_limit {
    __u64 packets;
    __u64 bytes;
    __u64 last_reset;
};

// Blocklist: IPs to always drop
struct {
    __uint(type, BPF_MAP_TYPE_LPM_TRIE);
    __uint(max_entries, 10000);
    __uint(map_flags, BPF_F_NO_PREALLOC);
    __type(key, struct bpf_lpm_trie_key);  // prefix length + IP
    __type(value, __u32);  // action
} blocklist SEC(".maps");

// Per-IP rate limiting
struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __uint(max_entries, 1000000);
    __type(key, __u32);             // source IP
    __type(value, struct rate_limit);
} rate_limits SEC(".maps");

// Stats
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 4);
    __type(key, __u32);
    __type(value, __u64);
} stats SEC(".maps");

#define STAT_PASS    0
#define STAT_DROP    1
#define STAT_RATELIM 2

static __always_inline void count_stat(__u32 idx) {
    __u64 *cnt = bpf_map_lookup_elem(&stats, &idx);
    if (cnt) __sync_fetch_and_add(cnt, 1);
}

static __always_inline int parse_headers(struct xdp_md *ctx,
                                          struct ethhdr **eth,
                                          struct iphdr **ip,
                                          void **l4) {
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;
    
    // Bounds check ethernet header (REQUIRED by verifier)
    *eth = data;
    if ((void *)((*eth) + 1) > data_end) return -1;
    
    if (bpf_ntohs((*eth)->h_proto) != ETH_P_IP) return -1;
    
    // Bounds check IP header
    *ip = (struct iphdr *)((*eth) + 1);
    if ((void *)((*ip) + 1) > data_end) return -1;
    
    // Variable IHL
    __u8 ihl = (*ip)->ihl * 4;
    if (ihl < 20) return -1;
    
    *l4 = (void *)*ip + ihl;
    if (*l4 + 4 > data_end) return -1;  // at least 4 bytes of L4
    
    return 0;
}

#define MAX_PACKETS_PER_SEC 10000
#define NANOSEC_PER_SEC 1000000000ULL

static __always_inline int check_rate_limit(__u32 src_ip) {
    struct rate_limit *rl = bpf_map_lookup_elem(&rate_limits, &src_ip);
    __u64 now = bpf_ktime_get_ns();
    
    if (!rl) {
        struct rate_limit new_rl = {
            .packets = 1,
            .bytes = 0,
            .last_reset = now,
        };
        bpf_map_update_elem(&rate_limits, &src_ip, &new_rl, BPF_NOEXIST);
        return 0;  // allow
    }
    
    // Reset counter if more than 1 second has passed
    if (now - rl->last_reset > NANOSEC_PER_SEC) {
        rl->packets = 0;
        rl->last_reset = now;
    }
    
    rl->packets++;
    
    if (rl->packets > MAX_PACKETS_PER_SEC) {
        return 1;  // rate limited
    }
    return 0;
}

SEC("xdp")
int xdp_ddos_protect(struct xdp_md *ctx) {
    struct ethhdr *eth;
    struct iphdr *ip;
    void *l4;
    
    if (parse_headers(ctx, &eth, &ip, &l4) < 0) {
        count_stat(STAT_PASS);
        return XDP_PASS;
    }
    
    __u32 src_ip = ip->saddr;
    
    // Check blocklist (LPM trie supports CIDR blocks)
    struct {
        __u32 prefixlen;
        __u32 data;
    } lpm_key = {
        .prefixlen = 32,
        .data = src_ip,
    };
    
    if (bpf_map_lookup_elem(&blocklist, &lpm_key)) {
        count_stat(STAT_DROP);
        return XDP_DROP;
    }
    
    // Rate limit check
    if (check_rate_limit(src_ip)) {
        count_stat(STAT_RATELIM);
        return XDP_DROP;
    }
    
    count_stat(STAT_PASS);
    return XDP_PASS;
}

char LICENSE[] SEC("license") = "GPL";
```

### 13.4 XDP Packet Modification

```c
// Swap ethernet addresses and TX back (ARP responder pattern):
SEC("xdp")
int xdp_swap_eth(struct xdp_md *ctx) {
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;
    struct ethhdr *eth = data;
    
    if ((void *)(eth + 1) > data_end)
        return XDP_DROP;
    
    // Swap src and dst MAC
    __u8 tmp[6];
    __builtin_memcpy(tmp, eth->h_dest, 6);
    __builtin_memcpy(eth->h_dest, eth->h_source, 6);
    __builtin_memcpy(eth->h_source, tmp, 6);
    
    return XDP_TX;  // Transmit modified packet back out
}

// Adding a header (encapsulation):
SEC("xdp")
int xdp_encap(struct xdp_md *ctx) {
    // Extend packet by VXLAN header size at the front
    if (bpf_xdp_adjust_head(ctx, -(int)sizeof(struct vxlan_header)) < 0)
        return XDP_DROP;
    
    // Now write VXLAN header at the new data start
    void *data = (void *)(long)ctx->data;
    struct vxlan_header *vxlan = data;
    // ... fill in vxlan header
    
    return XDP_TX;
}
```

---

## 14. TC — Traffic Control

TC programs hook into the kernel's traffic control subsystem. Unlike XDP, they have access to the full `sk_buff` structure and run on **both ingress and egress**.

### 14.1 TC Architecture

```
Ingress path:
  Packet ──► [NIC driver] ──► [XDP] ──► [skb alloc] ──► [TC INGRESS] ──► [netfilter] ──► socket

Egress path:
  Socket ──► [networking stack] ──► [netfilter] ──► [TC EGRESS] ──► [NIC driver] ──► wire

TC classifier types:
  - u32 (by IP/port)
  - flower (match fields)
  - bpf (our eBPF program)
  - matchall (all packets)
```

### 14.2 TC Return Values

```
TC_ACT_OK       (0)  — Pass packet to next action/handler
TC_ACT_RECLASSIFY   — Re-classify from the top
TC_ACT_SHOT     (2)  — Drop packet
TC_ACT_PIPE     (3)  — Pass to next action in chain
TC_ACT_STOLEN   (4)  — Consume packet (don't free)
TC_ACT_QUEUED   (5)  — Queue for later
TC_ACT_REPEAT   (6)  — Repeat current action
TC_ACT_REDIRECT (7)  — Redirect (used with bpf_redirect())
TC_ACT_TRAP     (8)  — Trap to userspace via netlink
```

### 14.3 TC Program Example — Network Policy

```c
// tc_policy.bpf.c
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>
#include <linux/pkt_cls.h>

struct policy_key {
    __u32 src_ip;
    __u32 dst_ip;
    __u16 dst_port;
    __u8  proto;
};

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 100000);
    __type(key, struct policy_key);
    __type(value, __u32);  // action: 0=allow, 1=deny
} policy_map SEC(".maps");

SEC("tc")
int tc_ingress_policy(struct __sk_buff *skb) {
    // Load IP header fields directly (TC can access skb data)
    __u32 src_ip, dst_ip;
    __u16 dst_port = 0;
    __u8  proto;
    
    // bpf_skb_load_bytes: safe memory access from skb
    // ETH_HLEN = 14 bytes ethernet header
    if (bpf_skb_load_bytes(skb, ETH_HLEN + offsetof(struct iphdr, saddr),
                           &src_ip, 4) < 0)
        return TC_ACT_OK;
    if (bpf_skb_load_bytes(skb, ETH_HLEN + offsetof(struct iphdr, daddr),
                           &dst_ip, 4) < 0)
        return TC_ACT_OK;
    if (bpf_skb_load_bytes(skb, ETH_HLEN + offsetof(struct iphdr, protocol),
                           &proto, 1) < 0)
        return TC_ACT_OK;
    
    if (proto == IPPROTO_TCP || proto == IPPROTO_UDP) {
        __u8 ihl;
        bpf_skb_load_bytes(skb, ETH_HLEN + 0, &ihl, 1);
        ihl = (ihl & 0x0f) * 4;
        bpf_skb_load_bytes(skb, ETH_HLEN + ihl + 2, &dst_port, 2);
    }
    
    struct policy_key key = {
        .src_ip = src_ip,
        .dst_ip = dst_ip,
        .dst_port = dst_port,
        .proto = proto,
    };
    
    __u32 *action = bpf_map_lookup_elem(&policy_map, &key);
    if (action && *action == 1)
        return TC_ACT_SHOT;
    
    return TC_ACT_OK;
}

char LICENSE[] SEC("license") = "GPL";
```

```bash
# Attach TC program:
tc qdisc add dev eth0 clsact
tc filter add dev eth0 ingress bpf da obj tc_policy.bpf.o sec tc
tc filter add dev eth0 egress  bpf da obj tc_policy.bpf.o sec tc

# List TC filters:
tc filter show dev eth0 ingress

# Remove:
tc filter del dev eth0 ingress
tc qdisc del dev eth0 clsact
```

---

## 15. Tracing Programs

### 15.1 kprobes — Dynamic Kernel Instrumentation

kprobes can be attached to **any non-inlined kernel function**. When the target function is called, the CPU executes a breakpoint, the kernel dispatches to your BPF program, then resumes.

```
Normal execution:
  [caller] ──CALL──► [function entry] ──► [function body] ──► [RET] ──► [caller]

With kprobe:
  [caller] ──CALL──► [INT3 breakpoint] ──► [kprobe handler]
                                                │
                                                ▼
                                        [your BPF program]
                                        (reads args from pt_regs)
                                                │
                                                ▼
                                     [resume: function entry]
                                                │
                                     [function body] ──► [RET]
                                                          │
                                              [kretprobe] (if attached)
                                                          │
                                              [your BPF return handler]
                                              (reads return value)
```

```c
// kprobe.bpf.c — trace execve system calls
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>

struct event {
    __u32 pid;
    __u32 ppid;
    __u32 uid;
    __u64 ts;
    char  comm[TASK_COMM_LEN];
    char  filename[256];
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 1 << 24);
} events SEC(".maps");

// Attach to __x64_sys_execve (syscall entry)
SEC("kprobe/__x64_sys_execve")
int BPF_KPROBE(trace_execve, const struct pt_regs *regs) {
    struct event *e;
    struct task_struct *task;
    
    e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e) return 0;
    
    task = (struct task_struct *)bpf_get_current_task();
    
    e->pid  = bpf_get_current_pid_tgid() >> 32;
    e->ppid = BPF_CORE_READ(task, real_parent, tgid);
    e->uid  = bpf_get_current_uid_gid();
    e->ts   = bpf_ktime_get_ns();
    bpf_get_current_comm(e->comm, sizeof(e->comm));
    
    // Read filename from user space (argument to execve)
    // PT_REGS_PARM1 gets first argument from pt_regs
    const char *filename = (const char *)PT_REGS_PARM1_CORE(regs);
    bpf_probe_read_user_str(e->filename, sizeof(e->filename), filename);
    
    bpf_ringbuf_submit(e, 0);
    return 0;
}

// Attach to return of do_execveat_common to get result
SEC("kretprobe/__x64_sys_execve")
int BPF_KRETPROBE(trace_execve_ret, long ret) {
    // ret = return value of execve
    // 0 on success (exec happened), negative on error
    bpf_printk("execve returned: %ld\n", ret);
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
```

### 15.2 uprobes — Userspace Function Tracing

uprobes work like kprobes but attach to **userspace functions**. They instrument the ELF binary on disk.

```c
// uprobe.bpf.c — trace SSL_write in OpenSSL (plaintext capture)
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

struct ssl_event {
    __u32 pid;
    __u32 len;
    __u8  buf[1024];
    __u8  rw;  // 0=write, 1=read
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 1 << 24);
} ssl_events SEC(".maps");

// Store SSL_write args between entry and return
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 10000);
    __type(key, __u32);  // tid
    __type(value, struct { void *buf; int num; });
} active_ssl_write SEC(".maps");

// uprobe: SSL_write(SSL *ssl, const void *buf, int num)
// Attach path: /path/to/libssl.so, symbol: SSL_write
SEC("uprobe/SSL_write")
int trace_ssl_write_entry(struct pt_regs *ctx) {
    __u32 tid = bpf_get_current_pid_tgid();
    
    struct { void *buf; int num; } args = {
        .buf = (void *)PT_REGS_PARM2(ctx),
        .num = (int)PT_REGS_PARM3(ctx),
    };
    
    bpf_map_update_elem(&active_ssl_write, &tid, &args, BPF_ANY);
    return 0;
}

SEC("uretprobe/SSL_write")
int trace_ssl_write_exit(struct pt_regs *ctx) {
    __u32 tid = bpf_get_current_pid_tgid();
    int ret = (int)PT_REGS_RC(ctx);
    
    struct { void *buf; int num; } *args;
    args = bpf_map_lookup_elem(&active_ssl_write, &tid);
    if (!args || ret <= 0) {
        bpf_map_delete_elem(&active_ssl_write, &tid);
        return 0;
    }
    
    struct ssl_event *e = bpf_ringbuf_reserve(&ssl_events, sizeof(*e), 0);
    if (!e) return 0;
    
    e->pid = bpf_get_current_pid_tgid() >> 32;
    e->len = ret;
    e->rw  = 0;
    
    __u32 read_len = ret < 1024 ? ret : 1024;
    bpf_probe_read_user(e->buf, read_len, args->buf);
    
    bpf_ringbuf_submit(e, 0);
    bpf_map_delete_elem(&active_ssl_write, &tid);
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
```

```bash
# Userspace attachment (via libbpf):
# Find SSL_write offset in libssl.so
NM_OFFSET=$(nm -D /usr/lib/x86_64-linux-gnu/libssl.so | grep SSL_write | awk '{print $1}')
# libbpf handles this with bpf_program__attach_uprobe():
```

```c
// Userspace attachment code:
struct bpf_link *link = bpf_program__attach_uprobe(
    prog,           // BPF program
    false,          // is_retprobe
    -1,             // pid (-1 = all processes)
    "/usr/lib/x86_64-linux-gnu/libssl.so.3",  // binary path
    0x12345         // function offset (or use bpf_program__attach_uprobe_opts
                    // with func_name for automatic symbol resolution)
);
```

### 15.3 Tracepoints — Static Kernel Probes

Tracepoints are **compile-time stable hooks** in the kernel. Unlike kprobes, they are not affected by function inlining and have stable argument structures documented by BTF.

```
Kernel source code:
  trace_sched_process_exec(p, old_pid, bprm);
         │
         ▼
  This expands to:
    if (static_key_false(&sched_process_exec_key)) {
        // call registered handlers, including BPF programs
    }

Benefits over kprobes:
  - Stable API (won't break between kernel versions)
  - Lower overhead (static key, no breakpoint)
  - Arguments are well-typed via BTF
  - Listed in /sys/kernel/debug/tracing/events/
```

```c
// Find all tracepoints:
ls /sys/kernel/debug/tracing/events/
ls /sys/kernel/debug/tracing/events/syscalls/
cat /sys/kernel/debug/tracing/events/syscalls/sys_enter_openat/format

// Tracepoint BPF program:
SEC("tp/syscalls/sys_enter_openat")
int handle_sys_enter_openat(struct trace_event_raw_sys_enter *ctx) {
    // ctx is strongly typed via BTF:
    long id = ctx->id;           // syscall number
    // For openat: args[0]=dfd, args[1]=filename, args[2]=flags, args[3]=mode
    char *filename = (char *)ctx->args[1];
    
    char fname[256];
    bpf_probe_read_user_str(fname, sizeof(fname), filename);
    bpf_printk("openat: %s\n", fname);
    return 0;
}
```

### 15.4 Raw Tracepoints

Raw tracepoints skip argument rewriting (more efficient, get arguments as raw kernel values):

```c
SEC("raw_tp/sched_process_exec")
int raw_trace_exec(struct bpf_raw_tracepoint_args *ctx) {
    // ctx->args[0] = struct task_struct *
    // ctx->args[1] = pid_t old_pid
    // ctx->args[2] = struct linux_binprm *
    struct task_struct *task = (struct task_struct *)ctx->args[0];
    
    char comm[16];
    bpf_probe_read_kernel_str(comm, sizeof(comm),
                              BPF_CORE_READ(task, comm));
    bpf_printk("exec: %s\n", comm);
    return 0;
}
```

### 15.5 fentry/fexit — BTF-based Tracing (Fastest)

```c
// fentry: called at function ENTRY, args directly available
SEC("fentry/tcp_sendmsg")
int BPF_PROG(fentry_tcp_sendmsg, struct sock *sk, struct msghdr *msg, size_t size) {
    // sk, msg, size are directly passed as typed arguments
    // NO pt_regs gymnastics needed
    __u32 pid = bpf_get_current_pid_tgid() >> 32;
    bpf_printk("tcp_sendmsg: pid=%u size=%zu\n", pid, size);
    return 0;
}

// fexit: called at function EXIT, has both args AND return value
SEC("fexit/tcp_sendmsg")
int BPF_PROG(fexit_tcp_sendmsg, struct sock *sk, struct msghdr *msg,
             size_t size, int ret) {
    // ret = return value of tcp_sendmsg
    if (ret < 0)
        bpf_printk("tcp_sendmsg failed: %d\n", ret);
    return 0;
}

// fmod_ret: can modify return value
SEC("fmod_ret/security_file_open")
int BPF_PROG(fmod_file_open, struct file *file) {
    // Return 0 to proceed, or -EPERM to deny
    char name[64];
    bpf_probe_read_kernel_str(name, sizeof(name),
                              BPF_CORE_READ(file, f_path.dentry, d_name.name));
    if (__builtin_memcmp(name, "secret", 6) == 0)
        return -EPERM;
    return 0;
}
```

### 15.6 perf_event Programs

Attach to hardware performance counters or software events:

```c
SEC("perf_event")
int profile_cpu(struct bpf_perf_event_data *ctx) {
    __u64 ip = PT_REGS_IP(&ctx->regs);  // instruction pointer
    __u32 pid = bpf_get_current_pid_tgid() >> 32;
    
    // Capture stack trace
    __u64 stack_id = bpf_get_stackid(ctx, &stack_traces,
                                      BPF_F_USER_STACK);
    
    // Record sample in histogram map
    struct sample_key key = { .pid = pid, .stack_id = stack_id };
    __u64 *count = bpf_map_lookup_elem(&samples, &key);
    if (count) (*count)++;
    else {
        __u64 init = 1;
        bpf_map_update_elem(&samples, &key, &init, BPF_NOEXIST);
    }
    
    return 0;
}
```

```c
// Userspace: create perf event, attach BPF program
struct perf_event_attr attr = {
    .type        = PERF_TYPE_HARDWARE,
    .config      = PERF_COUNT_HW_CPU_CYCLES,
    .sample_period = 1000000,   // sample every 1M cycles
    .inherit     = 1,
};
int pfd = syscall(SYS_perf_event_open, &attr, -1, cpu, -1, 0);
ioctl(pfd, PERF_EVENT_IOC_SET_BPF, prog_fd);
ioctl(pfd, PERF_EVENT_IOC_ENABLE, 0);
```

---

## 16. LSM eBPF

LSM (Linux Security Module) BPF programs implement security policies using the same hooks as SELinux and AppArmor, but programmatically via eBPF.

### 16.1 LSM Hook Architecture

```
System call / kernel operation
          │
          ▼
  Kernel does the work...
          │
          ▼
  Calls LSM hook: security_*()
          │
          ├──► SELinux policy check
          │
          ├──► AppArmor policy check
          │
          └──► BPF LSM programs   ◄── Your code runs here
                    │
                    ▼
          if any returns non-zero → operation DENIED
          if all return 0 → operation ALLOWED
```

### 16.2 Available LSM Hooks (selected)

```
Filesystem:
  bpf_lsm_inode_create        — File/dir creation
  bpf_lsm_inode_rename        — File rename
  bpf_lsm_inode_unlink        — File deletion
  bpf_lsm_file_open           — File open
  bpf_lsm_file_permission     — File permission check
  bpf_lsm_inode_setxattr      — Set extended attribute

Process:
  bpf_lsm_bprm_check_security — Before exec
  bpf_lsm_bprm_committed_creds— After exec credential commit
  bpf_lsm_task_alloc          — New task created
  bpf_lsm_task_kill           — Send signal
  bpf_lsm_task_fix_setuid     — setuid() operation

Network:
  bpf_lsm_socket_create       — Socket creation
  bpf_lsm_socket_connect      — Socket connect
  bpf_lsm_socket_bind         — Socket bind
  bpf_lsm_socket_sendmsg      — Send message
  bpf_lsm_socket_recvmsg      — Receive message

IPC:
  bpf_lsm_ipc_permission      — IPC access check
  bpf_lsm_shm_shmat           — Shared memory attach

System:
  bpf_lsm_capable             — Capability check
  bpf_lsm_settime             — Clock set
  bpf_lsm_syslog              — Syslog access
```

### 16.3 LSM BPF Example — Container Escape Prevention

```c
// lsm_container.bpf.c
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>

// Map of allowed PIDs/namespaces
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 10000);
    __type(key, __u32);   // pid namespace inode
    __type(value, __u8);  // 1 = containerized, restricted
} container_ns SEC(".maps");

static __always_inline int is_containerized(void) {
    struct task_struct *task = (struct task_struct *)bpf_get_current_task();
    // Get pid namespace inode (unique per namespace)
    __u32 ns_ino = BPF_CORE_READ(task, nsproxy, pid_ns_for_children, ns.inum);
    return bpf_map_lookup_elem(&container_ns, &ns_ino) != NULL;
}

// Prevent mounting filesystems from containers
SEC("lsm/sb_mount")
int BPF_PROG(lsm_prevent_mount, const char *dev_name, const struct path *path,
             const char *type, unsigned long flags, void *data) {
    if (is_containerized()) {
        bpf_printk("LSM: blocking mount from container\n");
        return -EPERM;
    }
    return 0;
}

// Prevent loading kernel modules from containers
SEC("lsm/kernel_module_request")
int BPF_PROG(lsm_prevent_module_load, char *kmod_name) {
    if (is_containerized())
        return -EPERM;
    return 0;
}

// Block ptrace across namespace boundaries
SEC("lsm/ptrace_access_check")
int BPF_PROG(lsm_ptrace_check, struct task_struct *child, unsigned int mode) {
    struct task_struct *tracer = (struct task_struct *)bpf_get_current_task();
    
    // Get PID namespaces
    __u32 tracer_ns = BPF_CORE_READ(tracer, nsproxy, pid_ns_for_children, ns.inum);
    __u32 child_ns  = BPF_CORE_READ(child,  nsproxy, pid_ns_for_children, ns.inum);
    
    // Block cross-namespace ptrace from containers
    if (tracer_ns != child_ns && bpf_map_lookup_elem(&container_ns, &tracer_ns))
        return -EPERM;
    
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
```

---

## 17. Cgroup eBPF

Cgroup BPF programs enforce policies at the **cgroup level**, applying to all processes in a cgroup hierarchy.

### 17.1 Cgroup BPF Program Types

```
BPF_PROG_TYPE_CGROUP_SKB
  - BPF_CGROUP_INET_INGRESS: filter incoming packets
  - BPF_CGROUP_INET_EGRESS:  filter outgoing packets

BPF_PROG_TYPE_CGROUP_SOCK
  - BPF_CGROUP_INET_SOCK_CREATE:  filter socket creation
  - BPF_CGROUP_INET_SOCK_RELEASE: cleanup on socket close

BPF_PROG_TYPE_CGROUP_SOCK_ADDR
  - BPF_CGROUP_INET4_BIND:    override IPv4 bind address
  - BPF_CGROUP_INET6_BIND:    override IPv6 bind address
  - BPF_CGROUP_INET4_CONNECT: override IPv4 connect address
  - BPF_CGROUP_INET6_CONNECT: override IPv6 connect address

BPF_PROG_TYPE_CGROUP_SYSCTL
  - BPF_CGROUP_SYSCTL: control sysctl access per cgroup

BPF_PROG_TYPE_CGROUP_SOCKOPT
  - BPF_CGROUP_GETSOCKOPT: intercept getsockopt()
  - BPF_CGROUP_SETSOCKOPT: intercept setsockopt()

BPF_PROG_TYPE_CGROUP_DEVICE
  - BPF_CGROUP_DEVICE: control /dev access per cgroup
```

### 17.2 Cgroup BPF Example — Per-Container Network Policy

```c
// cgroup_policy.bpf.c — block outgoing connections to certain ports
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>

// Blocked destination ports
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 1000);
    __type(key, __u16);    // destination port (host byte order)
    __type(value, __u8);
} blocked_ports SEC(".maps");

SEC("cgroup/connect4")
int cgroup_connect4(struct bpf_sock_addr *ctx) {
    __u16 dport = bpf_ntohs(ctx->user_port);
    
    if (bpf_map_lookup_elem(&blocked_ports, &dport))
        return 0;  // block: return 0 = deny
    
    return 1;  // allow: return 1 = proceed
}

// Transparent proxy: redirect all connections to a proxy
SEC("cgroup/connect4")
int cgroup_redirect_to_proxy(struct bpf_sock_addr *ctx) {
    // Redirect to local proxy at 127.0.0.1:8080
    ctx->user_ip4    = bpf_htonl(0x7f000001);  // 127.0.0.1
    ctx->user_port   = bpf_htons(8080);
    return 1;  // proceed with modified address
}

char LICENSE[] SEC("license") = "GPL";
```

```c
// Attach to cgroup:
int cgroup_fd = open("/sys/fs/cgroup/docker/container_id", O_RDONLY);
bpf_prog_attach(prog_fd, cgroup_fd, BPF_CGROUP_INET4_CONNECT,
                BPF_F_ALLOW_MULTI);
```

---

## 18. Socket & Sockmap

Sockmap enables **direct socket-to-socket data steering** in the kernel, bypassing the entire TCP/IP stack for localhost communication. This provides near-zero-copy IPC.

### 18.1 Sockmap Architecture

```
Without sockmap (traditional):
  app1 write() ──► kernel buffer ──► TCP stack ──► NIC (loopback)
                ──► NIC (loopback) ──► TCP stack ──► kernel buffer ──► app2 read()

With sockmap (sk_skb redirect):
  app1 write() ──► kernel buffer ──► [BPF sk_skb program]
                                              │
                                              └──► directly to app2's socket buffer
  (skips TCP/IP stack entirely for localhost)
  Latency improvement: 5-10x for localhost connections
```

```c
// sockmap.bpf.c — stream parser + redirect
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>
#include <linux/bpf.h>

// Sockmap: stores sockets indexed by port
struct {
    __uint(type, BPF_MAP_TYPE_SOCKMAP);
    __uint(max_entries, 65535);
    __type(key, __u32);
    __type(value, __u32);
} sock_map SEC(".maps");

// Stream parser: tells the kernel how much data to expect per message
SEC("sk_skb/stream_parser")
int skb_stream_parser(struct __sk_buff *skb) {
    // For HTTP/1.1 with Content-Length header, parse it
    // Simplified: assume fixed 8-byte header with length field
    if (skb->len < 8) return skb->len;  // wait for more data
    
    __u32 msg_len;
    bpf_skb_load_bytes(skb, 4, &msg_len, 4);
    return bpf_ntohl(msg_len) + 8;  // total message length
}

// Stream verdict: decide what to do with each parsed message
SEC("sk_skb/stream_verdict")
int skb_stream_verdict(struct __sk_buff *skb) {
    // Extract destination from message header
    __u32 dest_key;
    bpf_skb_load_bytes(skb, 0, &dest_key, 4);
    
    // Redirect to the appropriate socket
    return bpf_sk_redirect_map(skb, &sock_map, dest_key, 0);
}

char LICENSE[] SEC("license") = "GPL";
```

---

## 19. Ring Buffer vs Perf Buffer

### 19.1 Comparison

```
┌────────────────────────┬──────────────────────┬──────────────────────┐
│ Feature                │ Perf Buffer          │ Ring Buffer          │
├────────────────────────┼──────────────────────┼──────────────────────┤
│ Introduced             │ Kernel 4.4           │ Kernel 5.8           │
│ Buffers                │ One per CPU          │ Single shared buffer │
│ Memory overhead        │ N_CPU × size         │ 1 × size             │
│ Memory ordering        │ Per-CPU only         │ Global ordering      │
│ Userspace API          │ perf_buffer__*()     │ ring_buffer__*()     │
│ Zero-copy              │ No                   │ Yes (mmap)           │
│ Reserve/discard        │ No                   │ Yes                  │
│ Epoll support          │ No                   │ Yes                  │
│ Recommended for        │ Legacy, high-freq    │ All new code         │
│ Dropped event handling │ Lost samples counter │ Discard API          │
└────────────────────────┴──────────────────────┴──────────────────────┘
```

### 19.2 Ring Buffer API (Complete)

```c
// BPF side:

// Method 1: Reserve → fill → submit/discard (zero extra copy)
struct event *e = bpf_ringbuf_reserve(&rb, sizeof(*e), 0);
if (!e) {
    // Ring is full — drop or handle
    return 0;
}
e->pid = bpf_get_current_pid_tgid() >> 32;
// ... fill fields ...

// Submit: makes event visible to userspace
bpf_ringbuf_submit(e, 0);

// OR discard: frees the reservation without submitting
bpf_ringbuf_discard(e, 0);

// Method 2: Output (copy-based, simpler)
struct event e = { .pid = ... };
bpf_ringbuf_output(&rb, &e, sizeof(e), 0);

// Query available space:
__u64 avail = bpf_ringbuf_query(&rb, BPF_RB_AVAIL_DATA);
__u64 ring_size = bpf_ringbuf_query(&rb, BPF_RB_RING_SIZE);
__u64 cons_pos = bpf_ringbuf_query(&rb, BPF_RB_CONS_POS);
__u64 prod_pos = bpf_ringbuf_query(&rb, BPF_RB_PROD_POS);
```

```c
// Userspace side (libbpf):
static int handle_event(void *ctx, void *data, size_t size) {
    struct event *e = data;
    printf("pid=%u\n", e->pid);
    return 0;
}

struct ring_buffer *rb = ring_buffer__new(
    bpf_map__fd(skel->maps.rb),
    handle_event,
    NULL,   // context passed to handle_event
    NULL    // ring_buffer_opts
);

// Poll with timeout (milliseconds):
while (!stop) {
    int n = ring_buffer__poll(rb, 100);
    if (n < 0 && errno != EINTR) {
        fprintf(stderr, "ring_buffer__poll: %s\n", strerror(errno));
        break;
    }
}

// Or consume all available events without blocking:
ring_buffer__consume(rb);

ring_buffer__free(rb);
```

---

## 20. Writing eBPF in C

### 20.1 Project Structure (libbpf-bootstrap)

```
my_ebpf_project/
├── Makefile
├── vmlinux.h              ← generated: bpftool btf dump ... format c
├── src/
│   ├── myprogram.bpf.c    ← BPF kernel-side code
│   ├── myprogram.c        ← Userspace loader/handler
│   └── myprogram.h        ← Shared structures (between BPF and userspace)
└── include/
    └── bpf/               ← libbpf headers
```

### 20.2 Complete Example: Process Monitor

```c
// myprogram.h — shared between BPF and userspace
#pragma once
#define TASK_COMM_LEN 16
#define MAX_FILENAME_LEN 512

struct event {
    int pid;
    int ppid;
    int uid;
    int gid;
    char comm[TASK_COMM_LEN];
    char filename[MAX_FILENAME_LEN];
    bool is_exit;
    int exit_code;
    unsigned long long start_time;
};
```

```c
// myprogram.bpf.c — kernel-side BPF code
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>
#include "myprogram.h"

// Configuration from userspace
const volatile int  target_pid  = 0;   // 0 = trace all
const volatile bool trace_exit  = true;

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);
} rb SEC(".maps");

// Track process start times
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 8192);
    __type(key, __u32);    // PID
    __type(value, __u64);  // start timestamp
} start_times SEC(".maps");

static __always_inline bool should_trace(__u32 pid) {
    if (target_pid == 0) return true;
    return pid == (__u32)target_pid;
}

SEC("tp/sched/sched_process_exec")
int handle_exec(struct trace_event_raw_sched_process_exec *ctx) {
    __u32 pid  = bpf_get_current_pid_tgid() >> 32;
    __u32 tid  = bpf_get_current_pid_tgid();
    
    // Only trace main thread (pid == tid means main thread)
    if (pid != tid) return 0;
    if (!should_trace(pid)) return 0;
    
    struct event *e = bpf_ringbuf_reserve(&rb, sizeof(*e), 0);
    if (!e) return 0;
    
    struct task_struct *task = (struct task_struct *)bpf_get_current_task();
    
    e->pid  = pid;
    e->ppid = BPF_CORE_READ(task, real_parent, tgid);
    e->uid  = bpf_get_current_uid_gid();
    e->gid  = bpf_get_current_uid_gid() >> 32;
    e->is_exit = false;
    bpf_get_current_comm(e->comm, sizeof(e->comm));
    
    // Read filename from trace event context
    // ctx->__data_loc_filename is the offset to variable-length data
    unsigned int fname_off = ctx->__data_loc_filename & 0xFFFF;
    bpf_probe_read_kernel_str(e->filename, sizeof(e->filename),
                              (void *)ctx + fname_off);
    
    e->start_time = bpf_ktime_get_ns();
    
    // Store start time
    bpf_map_update_elem(&start_times, &pid, &e->start_time, BPF_ANY);
    
    bpf_ringbuf_submit(e, 0);
    return 0;
}

SEC("tp/sched/sched_process_exit")
int handle_exit(struct trace_event_raw_sched_process_template *ctx) {
    if (!trace_exit) return 0;
    
    __u32 pid = bpf_get_current_pid_tgid() >> 32;
    __u32 tid = bpf_get_current_pid_tgid();
    
    if (pid != tid) return 0;  // ignore thread exits
    if (!should_trace(pid)) return 0;
    
    struct event *e = bpf_ringbuf_reserve(&rb, sizeof(*e), 0);
    if (!e) return 0;
    
    e->pid     = pid;
    e->is_exit = true;
    // Get exit code from task_struct
    struct task_struct *task = (struct task_struct *)bpf_get_current_task();
    e->exit_code = BPF_CORE_READ(task, exit_code) >> 8;
    bpf_get_current_comm(e->comm, sizeof(e->comm));
    
    __u64 *start = bpf_map_lookup_elem(&start_times, &pid);
    if (start)
        e->start_time = *start;
    
    bpf_map_delete_elem(&start_times, &pid);
    bpf_ringbuf_submit(e, 0);
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
```

```c
// myprogram.c — userspace loader
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>
#include <time.h>
#include <bpf/libbpf.h>
#include "myprogram.skel.h"
#include "myprogram.h"

static volatile sig_atomic_t stop = 0;

static void sig_handler(int sig) { stop = 1; }

// libbpf logging callback
static int libbpf_print_fn(enum libbpf_print_level level,
                            const char *format, va_list args) {
    if (level == LIBBPF_DEBUG) return 0;  // suppress debug logs
    return vfprintf(stderr, format, args);
}

static int handle_event(void *ctx, void *data, size_t size) {
    const struct event *e = data;
    struct tm *tm;
    char ts[32];
    time_t t;
    
    time(&t);
    tm = localtime(&t);
    strftime(ts, sizeof(ts), "%H:%M:%S", tm);
    
    if (e->is_exit) {
        printf("%-8s %-5s %-16s EXIT  code=%-4d\n",
               ts, "EXIT", e->comm, e->exit_code);
    } else {
        printf("%-8s %-5d %-16s EXEC  %s\n",
               ts, e->pid, e->comm, e->filename);
    }
    return 0;
}

int main(int argc, char **argv) {
    struct myprogram_bpf *skel;
    struct ring_buffer *rb = NULL;
    int err;
    
    // Set libbpf callback
    libbpf_set_print(libbpf_print_fn);
    
    // Open BPF object
    skel = myprogram_bpf__open();
    if (!skel) {
        fprintf(stderr, "Failed to open BPF skeleton\n");
        return 1;
    }
    
    // Customize before load
    if (argc > 1)
        skel->rodata->target_pid = atoi(argv[1]);
    skel->rodata->trace_exit = true;
    
    // Load BPF programs and maps
    err = myprogram_bpf__load(skel);
    if (err) {
        fprintf(stderr, "Failed to load BPF skeleton: %d\n", err);
        goto cleanup;
    }
    
    // Attach all programs
    err = myprogram_bpf__attach(skel);
    if (err) {
        fprintf(stderr, "Failed to attach BPF skeleton: %d\n", err);
        goto cleanup;
    }
    
    // Set up ring buffer
    rb = ring_buffer__new(bpf_map__fd(skel->maps.rb),
                          handle_event, NULL, NULL);
    if (!rb) {
        err = -1;
        fprintf(stderr, "Failed to create ring buffer\n");
        goto cleanup;
    }
    
    signal(SIGINT, sig_handler);
    signal(SIGTERM, sig_handler);
    
    printf("%-8s %-5s %-16s %s\n", "TIME", "PID", "COMM", "EVENT");
    
    while (!stop) {
        err = ring_buffer__poll(rb, 100);
        if (err == -EINTR) { err = 0; break; }
        if (err < 0) { fprintf(stderr, "Error: %d\n", err); break; }
    }
    
cleanup:
    ring_buffer__free(rb);
    myprogram_bpf__destroy(skel);
    return err < 0 ? -err : 0;
}
```

### 20.3 Makefile for libbpf-bootstrap

```makefile
# Makefile
CLANG      := clang
BPFTOOL    := bpftool
CC         := gcc
ARCH       := $(shell uname -m | sed 's/x86_64/x86/' | sed 's/aarch64/arm64/')

LIBBPF_DIR := ./libbpf/src
INCLUDES   := -I$(LIBBPF_DIR) -I./include
CFLAGS     := -g -Wall
LDFLAGS    := -lelf -lz

BPF_CFLAGS := -g -O2 -target bpf -D__TARGET_ARCH_$(ARCH)

APP        := myprogram

$(APP): $(APP).bpf.o $(APP).skel.h $(APP).c
	$(CC) $(CFLAGS) $(INCLUDES) $(APP).c -o $@ \
		$(LIBBPF_DIR)/libbpf.a $(LDFLAGS)

$(APP).skel.h: $(APP).bpf.o
	$(BPFTOOL) gen skeleton $< > $@

$(APP).bpf.o: $(APP).bpf.c vmlinux.h
	$(CLANG) $(BPF_CFLAGS) $(INCLUDES) -c $< -o $@

vmlinux.h:
	$(BPFTOOL) btf dump file /sys/kernel/btf/vmlinux format c > $@

clean:
	rm -f $(APP) *.o *.skel.h vmlinux.h

.PHONY: clean
```

---

## 21. Writing eBPF in Rust with Aya

Aya is the leading Rust eBPF library. It is **pure Rust** (no C dependencies), supports CO-RE, and provides a safe, idiomatic API.

### 21.1 Aya Architecture

```
┌────────────────────────────────────────────────────────────────┐
│  AYA ECOSYSTEM                                                  │
│                                                                │
│  aya              — Userspace library (loads, manages programs) │
│  aya-bpf          — BPF-side library (types, helpers, macros)  │
│  aya-bpf-macros   — Proc macros: #[map], #[kprobe], #[xdp]... │
│  aya-log           — Logging from BPF programs                  │
│  aya-log-ebpf      — BPF-side logging implementation           │
│                                                                │
│  cargo-generate template:                                       │
│  cargo generate --git https://github.com/aya-rs/aya-template   │
└────────────────────────────────────────────────────────────────┘
```

### 21.2 Aya Project Structure

```
my-aya-project/
├── Cargo.toml               ← workspace
├── my-ebpf/                 ← BPF kernel-side crate
│   ├── Cargo.toml
│   └── src/
│       └── main.rs          ← BPF programs
├── my-ebpf-common/          ← Shared types (no_std)
│   ├── Cargo.toml
│   └── src/
│       └── lib.rs
└── my-ebpf-userspace/       ← Userspace crate
    ├── Cargo.toml
    └── src/
        └── main.rs
```

### 21.3 BPF-side Rust Code (aya-bpf)

```rust
// my-ebpf/src/main.rs
#![no_std]
#![no_main]

use aya_bpf::{
    bindings::xdp_action,
    macros::{map, xdp, kprobe, tracepoint},
    maps::{HashMap, RingBuf, PerCpuArray},
    programs::{XdpContext, ProbeContext, TracePointContext},
    helpers::{bpf_get_current_pid_tgid, bpf_get_current_comm,
               bpf_ktime_get_ns, bpf_probe_read_user_str_bytes},
    BpfContext,
};
use aya_log_ebpf::info;
use my_ebpf_common::{PacketEvent, ExecEvent, MAX_PATH};
use core::mem;

// ─── Maps ────────────────────────────────────────────────────────────────────

#[map]
static EVENTS: RingBuf = RingBuf::with_byte_size(256 * 1024, 0);

#[map]
static PACKET_COUNT: PerCpuArray<u64> = PerCpuArray::with_max_entries(1, 0);

#[map]
static IP_BLOCKLIST: HashMap<u32, u32> = HashMap::with_max_entries(10000, 0);

// ─── XDP Program ─────────────────────────────────────────────────────────────

#[xdp]
pub fn xdp_firewall(ctx: XdpContext) -> u32 {
    match try_xdp_firewall(ctx) {
        Ok(ret) => ret,
        Err(_) => xdp_action::XDP_PASS,
    }
}

fn try_xdp_firewall(ctx: XdpContext) -> Result<u32, ()> {
    // Parse ethernet header
    let ethhdr: *const EthHdr = ptr_at(&ctx, 0)?;
    let proto = unsafe { (*ethhdr).ether_type };
    
    if proto != u16::from_be(ETH_P_IP as u16) {
        return Ok(xdp_action::XDP_PASS);
    }
    
    // Parse IP header
    let iphdr: *const IpHdr = ptr_at(&ctx, EthHdr::LEN)?;
    let src_addr = u32::from_be(unsafe { (*iphdr).src_addr });
    
    // Check blocklist
    if unsafe { IP_BLOCKLIST.get(&src_addr).is_some() } {
        // Increment drop counter
        if let Some(count) = PACKET_COUNT.get_ptr_mut(0) {
            unsafe { *count += 1 };
        }
        return Ok(xdp_action::XDP_DROP);
    }
    
    Ok(xdp_action::XDP_PASS)
}

// Safe pointer-from-offset with bounds checking
#[inline(always)]
fn ptr_at<T>(ctx: &XdpContext, offset: usize) -> Result<*const T, ()> {
    let start = ctx.data();
    let end = ctx.data_end();
    let len = mem::size_of::<T>();
    
    if start + offset + len > end {
        return Err(());
    }
    Ok((start + offset) as *const T)
}

// ─── kprobe Program ──────────────────────────────────────────────────────────

#[kprobe]
pub fn kprobe_execve(ctx: ProbeContext) -> u32 {
    match try_kprobe_execve(ctx) {
        Ok(ret) => ret,
        Err(ret) => ret,
    }
}

fn try_kprobe_execve(ctx: ProbeContext) -> Result<u32, u32> {
    let pid = bpf_get_current_pid_tgid() >> 32;
    let mut comm = [0u8; 16];
    bpf_get_current_comm(&mut comm).map_err(|_| 0u32)?;
    
    info!(&ctx, "execve called by pid={} comm={}", pid,
          core::str::from_utf8(&comm).unwrap_or("?"));
    
    // Reserve ring buffer space
    let mut entry = match EVENTS.reserve::<ExecEvent>(0) {
        Some(e) => e,
        None => return Err(0),
    };
    
    let event = entry.as_mut_ptr();
    unsafe {
        (*event).pid = pid as u32;
        (*event).timestamp = bpf_ktime_get_ns();
        (*event).comm = comm;
    }
    
    entry.submit(0);
    Ok(0)
}

// ─── Tracepoint Program ───────────────────────────────────────────────────────

#[tracepoint]
pub fn tp_sys_enter_openat(ctx: TracePointContext) -> u32 {
    let pid = bpf_get_current_pid_tgid() >> 32;
    
    // Read filename argument (args[1] for openat)
    // TracePointContext provides read() to safely access args
    let filename_ptr: u64 = unsafe {
        ctx.read_at(24).unwrap_or(0)  // offset to args[1]
    };
    
    let mut fname = [0u8; MAX_PATH];
    let _ = unsafe {
        bpf_probe_read_user_str_bytes(filename_ptr as *const u8, &mut fname)
    };
    
    info!(&ctx, "openat: pid={}", pid);
    0
}

// ─── Panic handler (required for no_std) ─────────────────────────────────────

#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {
    unsafe { core::hint::unreachable_unchecked() }
}
```

### 21.4 Shared Types (no_std compatible)

```rust
// my-ebpf-common/src/lib.rs
#![no_std]

pub const MAX_PATH: usize = 256;
pub const TASK_COMM_LEN: usize = 16;

#[repr(C)]
#[derive(Clone, Copy)]
pub struct ExecEvent {
    pub pid: u32,
    pub ppid: u32,
    pub uid: u32,
    pub timestamp: u64,
    pub comm: [u8; TASK_COMM_LEN],
    pub filename: [u8; MAX_PATH],
}

#[repr(C)]
#[derive(Clone, Copy)]
pub struct PacketEvent {
    pub src_ip: u32,
    pub dst_ip: u32,
    pub src_port: u16,
    pub dst_port: u16,
    pub proto: u8,
    pub action: u8,
}

// Required for userspace (std is available there)
#[cfg(feature = "user")]
unsafe impl aya::Pod for ExecEvent {}
#[cfg(feature = "user")]
unsafe impl aya::Pod for PacketEvent {}
```

### 21.5 Userspace Rust Code

```rust
// my-ebpf-userspace/src/main.rs
use aya::{
    include_bytes_aligned,
    maps::{HashMap, RingBuf},
    programs::{Xdp, XdpFlags, KProbe, TracePoint},
    Bpf, BpfLoader, Btf,
};
use aya_log::BpfLogger;
use clap::Parser;
use log::{info, warn};
use my_ebpf_common::ExecEvent;
use std::net::Ipv4Addr;
use tokio::signal;

#[derive(Parser)]
struct Opt {
    #[clap(short, long, default_value = "eth0")]
    iface: String,
    
    #[clap(short, long)]
    pid: Option<u32>,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let opt = Opt::parse();
    env_logger::init();
    
    // Bump memory lock limit (needed for BPF maps)
    let rlim = libc::rlimit { rlim_cur: libc::RLIM_INFINITY,
                               rlim_max: libc::RLIM_INFINITY };
    unsafe { libc::setrlimit(libc::RLIMIT_MEMLOCK, &rlim) };
    
    // Load BPF object (embedded at compile time)
    // The bytes are the compiled .bpf.o file
    let mut bpf = BpfLoader::new()
        .btf(Btf::from_sys_fs().ok().as_ref())  // CO-RE support
        .load(include_bytes_aligned!(
            "../../target/bpfel-unknown-none/release/my-ebpf"
        ))?;
    
    // Initialize eBPF logger
    if let Err(e) = BpfLogger::init(&mut bpf) {
        warn!("Failed to init eBPF logger: {}", e);
    }
    
    // Load and attach XDP program
    let xdp_prog: &mut Xdp = bpf.program_mut("xdp_firewall").unwrap().try_into()?;
    xdp_prog.load()?;
    xdp_prog.attach(&opt.iface, XdpFlags::default())?;
    info!("XDP program attached to {}", opt.iface);
    
    // Load and attach kprobe
    let kprobe: &mut KProbe = bpf.program_mut("kprobe_execve").unwrap().try_into()?;
    kprobe.load()?;
    kprobe.attach("__x64_sys_execve", 0)?;
    info!("kprobe attached to execve");
    
    // Load and attach tracepoint
    let tp: &mut TracePoint = bpf.program_mut("tp_sys_enter_openat")
        .unwrap().try_into()?;
    tp.load()?;
    tp.attach("syscalls", "sys_enter_openat")?;
    
    // Populate blocklist from userspace
    let mut blocklist: HashMap<_, u32, u32> =
        HashMap::try_from(bpf.map_mut("IP_BLOCKLIST").unwrap())?;
    
    let block_ip: u32 = u32::from(Ipv4Addr::new(1, 2, 3, 4));
    blocklist.insert(block_ip, 0, 0)?;
    
    // Read events from ring buffer
    let mut ring_buf = RingBuf::try_from(bpf.map_mut("EVENTS").unwrap())?;
    
    tokio::spawn(async move {
        loop {
            // Process all available events
            while let Some(item) = ring_buf.next() {
                let event = unsafe { &*(item.as_ptr() as *const ExecEvent) };
                println!("EXEC: pid={} comm={}",
                    event.pid,
                    std::str::from_utf8(&event.comm)
                        .unwrap_or("?")
                        .trim_end_matches('\0')
                );
            }
            tokio::time::sleep(tokio::time::Duration::from_millis(10)).await;
        }
    });
    
    info!("Waiting for Ctrl+C...");
    signal::ctrl_c().await?;
    info!("Exiting");
    Ok(())
}
```

### 21.6 Aya Build Configuration

```toml
# Cargo.toml (workspace root)
[workspace]
members = ["my-ebpf", "my-ebpf-common", "my-ebpf-userspace"]
resolver = "2"

# my-ebpf/Cargo.toml (BPF crate)
[package]
name = "my-ebpf"
version = "0.1.0"
edition = "2021"

[dependencies]
aya-bpf      = { version = "0.1" }
aya-log-ebpf = { version = "0.1" }
my-ebpf-common = { path = "../my-ebpf-common" }

[profile.release]
opt-level = 3
lto = true

# my-ebpf-userspace/Cargo.toml
[dependencies]
aya         = { version = "0.12", features = ["async_tokio"] }
aya-log     = { version = "0.1" }
my-ebpf-common = { path = "../my-ebpf-common", features = ["user"] }
anyhow      = "1"
clap        = { version = "4", features = ["derive"] }
env_logger  = "0.10"
log         = "0.4"
tokio       = { version = "1", features = ["full"] }
libc        = "0.2"
```

```bash
# Build BPF target (cross-compile to BPF architecture)
cargo build --package my-ebpf \
    --release \
    --target bpfel-unknown-none \
    -Z build-std=core

# Build userspace
cargo build --package my-ebpf-userspace --release

# Or use xtask (recommended pattern):
cargo xtask build-ebpf
cargo xtask run
```

---

## 22. Toolchain Ecosystem

### 22.1 bpftool — Swiss Army Knife

```bash
# ──── Programs ────────────────────────────────────────────────
bpftool prog list                          # List all loaded programs
bpftool prog show id 42                    # Show program details
bpftool prog dump xlated id 42            # Dump BPF bytecode
bpftool prog dump jited id 42             # Dump JIT-compiled native code
bpftool prog dump jited id 42 opcodes     # With opcodes
bpftool prog pin id 42 /sys/fs/bpf/myprog # Pin to bpffs
bpftool prog load prog.o /sys/fs/bpf/prog # Load and pin
bpftool prog profile id 42 duration 10 cycles instructions # Profile

# ──── Maps ────────────────────────────────────────────────────
bpftool map list                          # List all maps
bpftool map show id 10                    # Show map details
bpftool map dump id 10                    # Dump all entries
bpftool map lookup id 10 key 01 00 00 00 # Lookup specific key
bpftool map update id 10 key 01 00 00 00 value 02 00 00 00 00 00 00 00
bpftool map delete id 10 key 01 00 00 00
bpftool map pin id 10 /sys/fs/bpf/mymap

# ──── BTF ─────────────────────────────────────────────────────
bpftool btf list
bpftool btf dump id 1
bpftool btf dump file /sys/kernel/btf/vmlinux format c > vmlinux.h
bpftool btf dump file prog.o                           # BTF from ELF

# ──── Links ───────────────────────────────────────────────────
bpftool link list
bpftool link show id 5
bpftool link pin id 5 /sys/fs/bpf/mylink
bpftool link detach id 5

# ──── Skeleton Generation ─────────────────────────────────────
bpftool gen skeleton prog.bpf.o > prog.skel.h
bpftool gen min_core_btf /sys/kernel/btf/vmlinux vmlinux.min.btf prog.bpf.o

# ──── Feature Detection ───────────────────────────────────────
bpftool feature probe                      # Probe kernel BPF features
bpftool feature probe kernel               # Kernel features
bpftool feature probe dev eth0             # NIC XDP features

# ──── Network ─────────────────────────────────────────────────
bpftool net list                           # List all network attachments
bpftool net attach xdp id 42 dev eth0     # Attach XDP
bpftool net detach xdp dev eth0           # Detach XDP
```

### 22.2 BCC — BPF Compiler Collection

BCC embeds Clang/LLVM and compiles BPF C code **at runtime from Python/Lua**. Great for prototyping, less suitable for production:

```python
#!/usr/bin/python3
# trace_execve.py — BCC version (easier to write, slower startup)
from bcc import BPF

bpf_code = """
#include <uapi/linux/ptrace.h>
#include <linux/sched.h>

struct data_t {
    u32 pid;
    char comm[TASK_COMM_LEN];
    char filename[256];
};

BPF_PERF_OUTPUT(events);

int trace_execve(struct pt_regs *ctx, const char *filename,
                 const char *const argv[], const char *const envp[]) {
    struct data_t data = {};
    data.pid = bpf_get_current_pid_tgid() >> 32;
    bpf_get_current_comm(&data.comm, sizeof(data.comm));
    bpf_probe_read_user_str(data.filename, sizeof(data.filename), filename);
    events.perf_submit(ctx, &data, sizeof(data));
    return 0;
}
"""

b = BPF(text=bpf_code)
b.attach_kprobe(event=b.get_syscall_fnname("execve"), fn_name="trace_execve")

def print_event(cpu, data, size):
    event = b["events"].event(data)
    print(f"PID={event.pid} COMM={event.comm.decode()} FILE={event.filename.decode()}")

b["events"].open_perf_buffer(print_event)
while True:
    b.perf_buffer_poll()
```

### 22.3 bpftrace — High-Level Tracing Language

bpftrace is a **one-liner tracing tool** for quick investigations:

```bash
# Trace all execve calls:
bpftrace -e 'tracepoint:syscalls:sys_enter_execve { printf("%s %s\n", comm, str(args->filename)); }'

# Syscall count by program:
bpftrace -e 'tracepoint:raw_syscalls:sys_enter { @[comm] = count(); }'

# Latency histogram for read() syscall:
bpftrace -e '
tracepoint:syscalls:sys_enter_read { @start[tid] = nsecs; }
tracepoint:syscalls:sys_exit_read  /@start[tid]/
{
  @latency = hist(nsecs - @start[tid]);
  delete(@start[tid]);
}'

# Trace block I/O latency:
bpftrace -e '
kprobe:blk_account_io_start    { @start[arg0] = nsecs; }
kprobe:blk_account_io_done     /@start[arg0]/
{
  @io_latency = hist(nsecs - @start[arg0]);
  delete(@start[arg0]);
}'

# List available probes:
bpftrace -l 'tracepoint:syscalls:*'
bpftrace -l 'kprobe:tcp_*'
bpftrace -l 'uprobe:/usr/lib/libssl.so:SSL_*'

# Flame graph data:
bpftrace -e 'profile:hz:99 { @[kstack] = count(); }' | flamegraph.pl > out.svg
```

### 22.4 Kernel Config Requirements

```bash
# Minimum required kernel config options:
CONFIG_BPF=y
CONFIG_BPF_SYSCALL=y
CONFIG_BPF_JIT=y
CONFIG_BPF_JIT_DEFAULT_ON=y      # JIT on by default
CONFIG_HAVE_EBPF_JIT=y
CONFIG_BPF_EVENTS=y               # kprobe/tracepoint support
CONFIG_KPROBES=y
CONFIG_UPROBES=y
CONFIG_TRACEPOINTS=y
CONFIG_BPF_LSM=y                  # LSM programs
CONFIG_DEBUG_INFO_BTF=y           # BTF + CO-RE (REQUIRED for modern eBPF)
CONFIG_DEBUG_INFO_BTF_MODULES=y   # BTF for kernel modules

# Networking:
CONFIG_XDP_SOCKETS=y              # AF_XDP
CONFIG_NET_CLS_BPF=m              # TC BPF programs
CONFIG_NET_ACT_BPF=m              # TC BPF actions
CONFIG_CGROUP_BPF=y               # cgroup BPF

# Check current kernel:
cat /boot/config-$(uname -r) | grep -E "CONFIG_BPF|CONFIG_DEBUG_INFO_BTF"
# Or:
grep CONFIG_DEBUG_INFO_BTF /proc/config.gz 2>/dev/null | zcat
```

---

## 23. Debugging & Observability

### 23.1 bpf_trace_printk

```c
// Debug output to /sys/kernel/debug/tracing/trace_pipe
// SLOW — only use for debugging, not production
bpf_printk("pid=%d, val=%llu\n", pid, value);

// Read output:
// cat /sys/kernel/debug/tracing/trace_pipe
// sudo cat /sys/kernel/debug/tracing/trace  (non-streaming)

// Limitations:
// - Only 3 format args max (pre-kernel 5.13)
// - Up to 6 args in kernel 5.13+
// - Performance overhead: avoid in hot paths
```

### 23.2 Verifier Debugging Workflow

```bash
# Step 1: Compile with debug info
clang -g -O2 -target bpf -c prog.bpf.c -o prog.bpf.o

# Step 2: Check what the verifier sees
bpftool prog load prog.bpf.o /sys/fs/bpf/test 2>&1 | head -100

# Step 3: View BTF info (types available to verifier)
bpftool btf dump file prog.bpf.o

# Step 4: View BPF bytecode
llvm-objdump -S prog.bpf.o

# Step 5: After loading, view JIT output
bpftool prog dump jited name my_prog_func

# Step 6: Check verifier stats
bpftool prog show name my_prog_func
# Look for: complexity N (number of states explored)
# High complexity = approaching verifier limits

# Step 7: Enable verbose verifier logs in code
// Set log_level = 2 in BPF_PROG_LOAD attrs
// Or with libbpf:
LIBBPF_OPTS(bpf_object_open_opts, opts,
    .kernel_log_level = 2,
);
```

### 23.3 strace for BPF syscalls

```bash
# Trace all bpf() syscalls made by a program:
strace -e bpf ./my_bpf_program

# Decode bpf() calls verbosely:
strace -v -e bpf ./my_bpf_program 2>&1 | head -200

# Example output:
# bpf(BPF_MAP_CREATE, {map_type=BPF_MAP_TYPE_RINGBUF, key_size=0,
#       value_size=0, max_entries=262144, ...}, 128) = 4
# bpf(BPF_PROG_LOAD, {prog_type=BPF_PROG_TYPE_TRACEPOINT, ...}, 128) = 5
```

### 23.4 Performance Analysis

```bash
# Check BPF program complexity (instruction count, peak states):
bpftool prog show id <ID>
# Output: "processed X insns (limit: 1000000) max_states_per_insn N
#          total_states N peak_states N mark_read N"

# Profile BPF program performance:
bpftool prog profile id <ID> duration 10 cycles instructions llc_misses

# Check tail call chain depth:
bpftool prog show | grep tail_calls

# Map access statistics (via kernel /proc/):
cat /proc/net/psched           # TC schedulers
cat /sys/fs/bpf/               # pinned objects
ls -la /sys/fs/bpf/

# BPF-related kernel stats:
cat /proc/net/dev               # packet counters
cat /sys/kernel/debug/tracing/trace_stat/  # perf stats
```

---

## 24. eBPF Security

### 24.1 eBPF as an Attack Surface

eBPF programs running in the kernel have significant power. Attack vectors:

```
1. Exploiting verifier bugs:
   - Historically: CVE-2021-3490 (ALU32 sign extension),
     CVE-2021-31440 (pointer arithmetic),
     CVE-2022-23222 (null pointer)
   - These allowed privilege escalation to root
   - Defense: restrict BPF to root/CAP_BPF, disable unprivileged BPF

2. Malicious BPF programs (rootkits):
   - Hide processes by filtering /proc reads
   - Keylog via uprobe on readline, sshd, pam
   - Exfiltrate data via DNS/ICMP
   - Backdoor via kprobe overriding auth functions
   - Bypass network security by XDP-dropping audit traffic

3. Side channels:
   - BPF programs can time cache accesses
   - Spectre-style attacks via speculation in BPF
   - Defense: BPF JIT hardening (constant blinding)

4. Map data leaks:
   - BPF maps containing sensitive data accessible by fd
   - Defense: BPF_F_RDONLY, proper permissions
```

### 24.2 Privilege Requirements

```
CAP_SYS_ADMIN          — Full BPF access (historical)
CAP_BPF (kernel 5.8+)  — Load and use BPF programs
CAP_NET_ADMIN          — Attach XDP, TC programs  
CAP_PERFMON            — Attach to perf events, tracepoints
CAP_SYS_PTRACE         — Access other process memory via probes

# Unprivileged BPF (CAP_BPF not needed):
# Historically limited socket filters were allowed unprivileged
# Most kernels now disable this:
cat /proc/sys/kernel/unprivileged_bpf_disabled
# 0 = allow, 1 = disable (except for socket filters), 2 = fully disable
sysctl -w kernel.unprivileged_bpf_disabled=2
```

### 24.3 Defensive eBPF — Runtime Security

```c
// Security monitoring with LSM + BPF:
// Detect privilege escalation attempts

SEC("lsm/capable")
int BPF_PROG(lsm_capable, const struct cred *cred,
             struct user_namespace *ns, int cap, unsigned int opts) {
    // Log attempts to use CAP_SYS_ADMIN, CAP_NET_ADMIN, etc.
    __u32 pid = bpf_get_current_pid_tgid() >> 32;
    
    if (cap == CAP_SYS_ADMIN || cap == CAP_NET_ADMIN || cap == CAP_BPF) {
        struct cap_event e = {
            .pid = pid,
            .cap = cap,
            .result = 0,  // will be set by real LSM check
        };
        bpf_get_current_comm(e.comm, sizeof(e.comm));
        bpf_ringbuf_output(&events, &e, sizeof(e), 0);
    }
    return 0;  // don't block, just audit
}
```

### 24.4 Detecting Malicious BPF Programs

```bash
# List all loaded BPF programs (as root):
bpftool prog list

# Check for suspicious programs:
bpftool prog list | grep -E "kprobe|uprobe|lsm|xdp"

# Dump program code (look for suspicious helpers):
bpftool prog dump xlated id <ID> | grep -E "call|helper"

# Check what functions are probed:
bpftool prog show id <ID>
# Look at: attach_type, loaded_at, name, tag

# Find programs by type:
bpftool prog list type kprobe      # All kprobe programs
bpftool prog list type xdp         # All XDP programs

# Check what maps a suspicious program uses:
bpftool prog show id <ID> | grep map_ids

# Dump map contents:
bpftool map dump id <MAP_ID>

# Find programs attached to specific interfaces:
bpftool net list
ip link show                        # XDP shown as "xdp" in output

# Find TC programs:
tc filter show dev eth0 ingress
tc filter show dev eth0 egress

# Check cgroup BPF:
bpftool cgroup tree
```

### 24.5 eBPF Rootkit Techniques (for detection/research)

**These are documented here for defensive knowledge — detection, not offense:**

```
1. Process hiding via TC/XDP:
   - Filter /proc/PID reads by intercepting getdents64
   - kprobe on filldir/filldir64 to skip entries

2. Network backdoor:
   - XDP program listening for magic packet sequence
   - Executes command when magic bytes received
   - Detection: audit XDP programs on all interfaces

3. Credential stealing:
   - uprobe on PAM authentication functions
   - SSL/TLS plaintext via uprobe on SSL_read/SSL_write
   - Detection: check for uprobes on sensitive libraries

4. Persistence:
   - Pin programs to /sys/fs/bpf/
   - Set up via systemd or rc.local
   - Detection: audit /sys/fs/bpf/ directory

5. Audit evasion:
   - kprobe on audit_log_* to suppress logs
   - XDP to drop packets going to SIEM
   - Detection: check kprobes on audit functions
```

---

## 25. Real-World Use Cases

### 25.1 Cilium — Kubernetes Network Policy

Cilium replaces iptables with eBPF for Kubernetes networking:

```
Traditional k8s networking:
  Pod A ──► veth ──► iptables (100+ rules) ──► veth ──► Pod B
  Latency: O(n) where n = number of rules

Cilium eBPF networking:
  Pod A ──► veth ──► TC BPF (O(1) hash lookup) ──► veth ──► Pod B
  Or: Pod A ──► sockmap (bypass kernel stack entirely) ──► Pod B

Benefits:
  - 2-5x lower latency
  - 10x higher throughput
  - O(1) policy enforcement regardless of number of policies
  - Native service load balancing without kube-proxy
  - Network observability via Hubble (eBPF-based)
```

### 25.2 Falco — Runtime Security

Falco uses eBPF to detect suspicious behavior:

```c
// Simplified Falco-like rule implementation:
// Detect: container spawning shell (possible breakout)

SEC("tp/sched/sched_process_exec")
int detect_shell_exec(struct trace_event_raw_sched_process_exec *ctx) {
    char comm[16];
    bpf_get_current_comm(comm, sizeof(comm));
    
    // Check if process is a shell
    bool is_shell = 
        (comm[0]=='b' && comm[1]=='a' && comm[2]=='s' && comm[3]=='h') ||
        (comm[0]=='s' && comm[1]=='h' && comm[2]==0) ||
        (comm[0]=='z' && comm[1]=='s' && comm[2]=='h');
    
    if (!is_shell) return 0;
    
    // Check if we're in a container (has parent init in different ns)
    struct task_struct *task = (struct task_struct *)bpf_get_current_task();
    __u32 pid_ns = BPF_CORE_READ(task, nsproxy, pid_ns_for_children, ns.inum);
    
    // Initial PID namespace has a well-known inode number
    // If different, we're in a container
    // (simplified — real Falco has more sophisticated detection)
    
    struct alert_event *e = bpf_ringbuf_reserve(&alerts, sizeof(*e), 0);
    if (!e) return 0;
    e->type = ALERT_SHELL_IN_CONTAINER;
    e->pid  = bpf_get_current_pid_tgid() >> 32;
    bpf_ringbuf_submit(e, 0);
    return 0;
}
```

### 25.3 CPU Profiler (like perf/pyspy)

```c
// Continuous profiling via perf_event:

SEC("perf_event")
int cpu_profiler(struct bpf_perf_event_data *ctx) {
    __u32 pid = bpf_get_current_pid_tgid() >> 32;
    
    // Skip kernel threads (pid 0)
    if (pid == 0) return 0;
    
    struct sample_key {
        __u32 pid;
        __s64 kernel_stack_id;
        __s64 user_stack_id;
    } key = {
        .pid = pid,
        .kernel_stack_id = bpf_get_stackid(ctx, &stack_traces, 0),
        .user_stack_id   = bpf_get_stackid(ctx, &stack_traces,
                                            BPF_F_USER_STACK),
    };
    
    __u64 *cnt = bpf_map_lookup_elem(&counts, &key);
    if (cnt) {
        (*cnt)++;
    } else {
        __u64 init = 1;
        bpf_map_update_elem(&counts, &key, &init, BPF_NOEXIST);
    }
    
    return 0;
}

// Userspace: collect samples, resolve symbols, build flame graph
// Use addr2line, /proc/PID/maps, libdwarf for symbol resolution
```

### 25.4 Network Observability — Complete Flow Tracking

```c
// Track TCP connections like ss/netstat but from eBPF

struct tcp_event {
    __u32 saddr, daddr;
    __u16 sport, dport;
    __u32 pid;
    __u64 ts;
    __u8  type;  // 0=connect, 1=accept, 2=close
    char  comm[16];
};

// Trace tcp_connect (outbound connections)
SEC("fentry/tcp_connect")
int BPF_PROG(trace_tcp_connect, struct sock *sk) {
    struct tcp_event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e) return 0;
    
    e->type  = 0;
    e->pid   = bpf_get_current_pid_tgid() >> 32;
    e->ts    = bpf_ktime_get_ns();
    e->saddr = BPF_CORE_READ(sk, __sk_common.skc_rcv_saddr);
    e->daddr = BPF_CORE_READ(sk, __sk_common.skc_daddr);
    e->sport = BPF_CORE_READ(sk, __sk_common.skc_num);
    e->dport = bpf_ntohs(BPF_CORE_READ(sk, __sk_common.skc_dport));
    bpf_get_current_comm(e->comm, sizeof(e->comm));
    
    bpf_ringbuf_submit(e, 0);
    return 0;
}

// Trace inet_csk_accept (inbound connections)
SEC("fexit/inet_csk_accept")
int BPF_PROG(trace_tcp_accept, struct sock *sk, int flags, int *err,
             bool kern, struct sock *ret) {
    if (!ret) return 0;  // accept failed
    
    struct tcp_event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e) return 0;
    
    e->type  = 1;
    e->pid   = bpf_get_current_pid_tgid() >> 32;
    e->ts    = bpf_ktime_get_ns();
    e->saddr = BPF_CORE_READ(ret, __sk_common.skc_rcv_saddr);
    e->daddr = BPF_CORE_READ(ret, __sk_common.skc_daddr);
    e->sport = BPF_CORE_READ(ret, __sk_common.skc_num);
    e->dport = bpf_ntohs(BPF_CORE_READ(ret, __sk_common.skc_dport));
    bpf_get_current_comm(e->comm, sizeof(e->comm));
    
    bpf_ringbuf_submit(e, 0);
    return 0;
}
```

### 25.5 Load Balancer with Consistent Hashing (XDP)

```c
// XDP load balancer using Maglev consistent hashing

#define MAX_BACKENDS 64
#define MAGLEV_TABLE_SIZE 65537  // prime number

struct backend {
    __u32 ip;
    __u16 port;
    __u8  weight;
};

struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, MAGLEV_TABLE_SIZE);
    __type(key, __u32);
    __type(value, __u32);  // backend index
} maglev_table SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, MAX_BACKENDS);
    __type(key, __u32);
    __type(value, struct backend);
} backends SEC(".maps");

SEC("xdp")
int xdp_lb(struct xdp_md *ctx) {
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;
    
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end) return XDP_PASS;
    
    if (eth->h_proto != bpf_htons(ETH_P_IP)) return XDP_PASS;
    
    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end) return XDP_PASS;
    
    if (ip->protocol != IPPROTO_TCP) return XDP_PASS;
    
    struct tcphdr *tcp = (void *)ip + ip->ihl * 4;
    if ((void *)(tcp + 1) > data_end) return XDP_PASS;
    
    // Compute consistent hash of 5-tuple
    __u32 hash = jhash_2words(ip->saddr, ip->daddr,
                              (tcp->source << 16) | tcp->dest);
    __u32 idx = hash % MAGLEV_TABLE_SIZE;
    
    // Look up backend
    __u32 *backend_idx = bpf_map_lookup_elem(&maglev_table, &idx);
    if (!backend_idx) return XDP_PASS;
    
    struct backend *be = bpf_map_lookup_elem(&backends, backend_idx);
    if (!be) return XDP_PASS;
    
    // DNAT: rewrite destination IP and port
    ip->daddr = be->ip;
    tcp->dest = bpf_htons(be->port);
    
    // Recalculate checksums
    // (ip->check, tcp->check update required)
    
    return XDP_TX;
}
```

---

## Appendix A: eBPF Section Name Reference

The `SEC()` macro tells libbpf how to auto-attach a program:

```c
// XDP
SEC("xdp")                           // Generic XDP
SEC("xdp.frags")                     // XDP with packet fragments

// TC
SEC("tc")                            // TC classifier
SEC("tc/ingress")                    // Explicit ingress
SEC("tc/egress")                     // Explicit egress
SEC("classifier")                    // Alias for tc

// kprobes / kretprobes
SEC("kprobe/function_name")
SEC("kretprobe/function_name")
SEC("kprobe.multi/pattern*")         // Multi-attach kprobe

// fentry / fexit (BTF-based, faster)
SEC("fentry/function_name")
SEC("fexit/function_name")
SEC("fmod_ret/function_name")        // Modify return value

// Tracepoints
SEC("tp/category/name")              // e.g., tp/syscalls/sys_enter_openat
SEC("tracepoint/category/name")      // Alias
SEC("raw_tp/name")                   // Raw tracepoint
SEC("raw_tracepoint/name")           // Alias

// Uprobes
SEC("uprobe/path:func")
SEC("uretprobe/path:func")

// LSM
SEC("lsm/hook_name")                 // e.g., lsm/file_open
SEC("lsm.s/hook_name")               // Sleepable LSM

// cgroup
SEC("cgroup_skb/ingress")
SEC("cgroup_skb/egress")
SEC("cgroup/bind4")
SEC("cgroup/bind6")
SEC("cgroup/connect4")
SEC("cgroup/connect6")
SEC("cgroup/sendmsg4")
SEC("cgroup/recvmsg4")
SEC("cgroup/sock_create")
SEC("cgroup/sysctl")
SEC("cgroup/getsockopt")
SEC("cgroup/setsockopt")
SEC("cgroup/dev")

// Perf
SEC("perf_event")

// Socket
SEC("sk_skb/stream_parser")
SEC("sk_skb/stream_verdict")
SEC("sk_msg")
SEC("sock_ops")
SEC("sk_lookup")
SEC("sk_reuseport")

// Struct ops
SEC("struct_ops/name")               // e.g., struct_ops/tcp_cong_ops
```

---

## Appendix B: Common Verifier Errors and Fixes

```
"invalid indirect read from stack"
→ You're passing stack memory to a helper without initializing all bytes
→ Fix: memset the entire struct before filling fields:
   struct my_struct s = {};  // zero-initialize

"R0 !read_ok" or "R0 is not a known value"
→ Using r0 (return value) without checking for NULL after map lookup
→ Fix: always check if (ptr == NULL) return 0; after bpf_map_lookup_elem

"math between pkt pointer and register with unbounded min value is not allowed"
→ Using a variable offset to access packet data without bounds check
→ Fix: bound-check the variable before using it as packet offset:
   if (offset >= data_end - data) return XDP_DROP;

"back-edge from insn X to Y"
→ Verifier detected a loop (in kernels < 5.3)
→ Fix: use #pragma unroll or rewrite without loops

"BPF stack limit of 512 bytes is exceeded"
→ Stack variables too large
→ Fix: move large arrays to per-CPU map used as scratch space:
   struct { __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
            __uint(max_entries, 1);
            __type(value, struct large_struct); } scratch SEC(".maps");

"cannot pass in arena pointer"
→ Trying to pass wrong pointer type to helper
→ Fix: check helper's accepted argument types in kernel docs

"combined stack size of X calls is Y. Too large"
→ BPF-to-BPF function calls have too much total stack usage
→ Fix: reduce local variable sizes; use maps for large data

"!read_ok" on map value
→ Reading from map value without checking for NULL
→ Fix: always null-check result of bpf_map_lookup_elem
```

---

## Appendix C: Key Kernel Version Features

```
3.18  — eBPF first merged, maps, socket filter
4.1   — BPF JIT for all architectures
4.4   — perf_event programs
4.7   — tracepoint programs
4.8   — cgroup programs, XDP
4.10  — BPF tail calls
4.11  — SO_REUSEPORT programs
4.15  — sockmap, sk_msg
4.17  — BPF raw tracepoints
4.18  — BTF support begins
5.0   — spin locks in BPF
5.2   — instruction limit raised to 1M, new helpers
5.3   — bounded loops allowed
5.5   — BPF_PROG_TYPE_TRACING (fentry/fexit)
5.7   — BPF LSM programs
5.8   — BPF ring buffer, BPF iterators
5.11  — BPF timer (bpf_timer_*)
5.13  — bpf_trace_printk up to 6 args, bpf_snprintf
5.15  — BPF cookie (bpf_get_attach_cookie)
5.17  — bpf_kptr_xchg, kernel pointer storage in maps
6.0   — BPF memory allocator (bpf_obj_new/drop)
6.1   — BPF arena (huge page-backed shared memory)
6.4   — BPF netfilter programs
6.6   — BPF struct_ops extensions
```

---

## Appendix D: Performance Benchmarks Reference

```
Operation                          Throughput / Latency
─────────────────────────────────────────────────────────
XDP DROP (native mode)             ~100 Mpps per core (100GbE line rate)
XDP PASS                           ~30-50 Mpps per core
TC program (simple)                ~15-25 Mpps per core
iptables (equivalent rules)        ~2-5 Mpps per core
BPF hash map lookup                ~100-200 ns
BPF array map lookup               ~10-30 ns (cache warm)
BPF percpu array lookup            ~5-15 ns
Ring buffer event output           ~50-100 ns
perf event output                  ~150-300 ns
kprobe overhead                    ~100-500 ns per hit
fentry overhead                    ~50-150 ns per hit (no INT3)
tracepoint overhead (disabled)     ~0 ns (static key)
tracepoint overhead (enabled)      ~50-200 ns per hit

Note: numbers are approximate and hardware-dependent.
Measure with: bpftool prog profile id X duration 10 cycles
```

---

*This document covers eBPF as of Linux kernel 6.x. The eBPF subsystem evolves rapidly — always check kernel release notes and the kernel BPF documentation at https://docs.kernel.org/bpf/ for the latest additions.*