# eBPF: The Complete, In-Depth Guide
> Extended Berkeley Packet Filter — from Linux internals to production-grade C and Rust programs

---

## Table of Contents

1. [Conceptual Foundation — Correcting Your Mental Model](#1-conceptual-foundation)
2. [History: BPF → eBPF](#2-history-bpf--ebpf)
3. [Linux Kernel Architecture & Where eBPF Lives](#3-linux-kernel-architecture--where-ebpf-lives)
4. [The eBPF Virtual Machine](#4-the-ebpf-virtual-machine)
5. [The Verifier — The Gatekeeper](#5-the-verifier--the-gatekeeper)
6. [JIT Compilation](#6-jit-compilation)
7. [eBPF Program Types & Attachment Points](#7-ebpf-program-types--attachment-points)
8. [eBPF Maps — The Data Layer](#8-ebpf-maps--the-data-layer)
9. [Helper Functions](#9-helper-functions)
10. [BTF — BPF Type Format](#10-btf--bpf-type-format)
11. [CO-RE — Compile Once, Run Everywhere](#11-co-re--compile-once-run-everywhere)
12. [The eBPF Toolchain Ecosystem](#12-the-ebpf-toolchain-ecosystem)
13. [Writing eBPF Programs in C (libbpf)](#13-writing-ebpf-programs-in-c-libbpf)
14. [Writing eBPF Programs in Rust (Aya)](#14-writing-ebpf-programs-in-rust-aya)
15. [Networking with eBPF](#15-networking-with-ebpf)
16. [Observability with eBPF](#16-observability-with-ebpf)
17. [Security with eBPF](#17-security-with-ebpf)
18. [eBPF in the Linux Kernel Source](#18-ebpf-in-the-linux-kernel-source)
19. [Performance Considerations](#19-performance-considerations)
20. [Production Patterns & Best Practices](#20-production-patterns--best-practices)
21. [Limitations & Gotchas](#21-limitations--gotchas)
22. [The eBPF Ecosystem: Tools and Projects](#22-the-ebpf-ecosystem-tools-and-projects)

---

## 1. Conceptual Foundation

### Your Understanding — Partially Right, Partially Wrong

You said:
> "Before loading eBPF, the kernel works as configured. Once eBPF is loaded, what eBPF tells the kernel is what Linux obeys."

This is **partially correct but misleading in an important way**. Let's dissect it precisely.

### The Truth: eBPF Does Not Replace Kernel Logic

eBPF programs **do not replace or override** the kernel's normal execution path. They are **hooks** — small, sandboxed programs that are **attached to specific events** inside the kernel and run **alongside** the normal kernel code, not instead of it.

Think of it this way:

```
Without eBPF:
  [Event occurs in kernel] ──→ [Kernel handles it normally] ──→ [Done]

With eBPF (most program types):
  [Event occurs in kernel] ──→ [eBPF program runs (observer/side-effect)]
                           └──→ [Kernel still handles it normally] ──→ [Done]

With eBPF (XDP / TC / LSM — action-capable types):
  [Event occurs in kernel] ──→ [eBPF program runs]
                                    │
                    ┌───────────────┼──────────────────┐
                    ▼               ▼                  ▼
               [PASS/DROP]    [REDIRECT]          [MODIFY then continue]
```

### The Correct Mental Model

1. **Most eBPF programs are observers** — they run when a kernel event fires, can read data, write to maps, emit events to userspace, but the kernel continues its normal work regardless.

2. **Some eBPF programs are actors** — types like XDP (eXpress Data Path), TC (Traffic Control), LSM (Linux Security Module hooks), and cgroup hooks can **influence** kernel behavior: dropping packets, modifying syscall arguments, enforcing access control.

3. **eBPF never directly calls or replaces kernel functions** — it attaches to defined hook points. The kernel's own code always runs first or the eBPF program is called via a well-defined interface.

4. **The kernel verifier ensures safety** — unlike a kernel module, eBPF code is proven safe before it ever runs. It cannot crash the kernel, loop infinitely, or access arbitrary memory.

5. **eBPF is additive, not substitutive** — you layer eBPF capabilities on top of a running kernel. The kernel doesn't "obey" eBPF; eBPF is a guest that participates in kernel events.

### Analogy

Think of the Linux kernel as a factory floor. eBPF programs are **sensors and actuators** attached to machines on that floor. The sensors watch what happens and report metrics. Some actuators can flip switches (like routing a packet differently). But the factory's core machinery — scheduling, memory management, the VFS, the TCP stack — keeps running as designed. eBPF adds intelligence on top without rewiring the factory.

---

## 2. History: BPF → eBPF

### Classic BPF (cBPF) — 1992

Steven McCanne and Van Jacobson introduced BPF (Berkeley Packet Filter) in their 1992 USENIX paper. It was designed to answer one question: **how do you efficiently filter network packets in the kernel without copying them all to userspace?**

Classic BPF defined:
- A simple register-based virtual machine with 2 registers (`A` accumulator, `X` index register)
- A small instruction set (32 instructions)
- A fixed-size program (limited to ~4096 instructions)
- Used by `tcpdump`, `libpcap`, seccomp filters

When you run `tcpdump tcp port 80`, libpcap compiles that filter expression into cBPF bytecode and attaches it to a socket. The kernel runs that bytecode on each received packet to decide whether to pass it to userspace.

### Extended BPF (eBPF) — 2014

Alexei Starovoitov proposed eBPF for Linux 3.18 (merged 2014). The redesign was sweeping:

| Feature | cBPF | eBPF |
|---|---|---|
| Registers | 2 (A, X) | 11 (R0–R10) |
| Register width | 32-bit | 64-bit |
| Stack | None | 512 bytes |
| Maps | None | Rich map types |
| Program types | Socket filter only | 30+ types |
| Helper functions | None | 200+ |
| JIT | Partial | Full, multi-arch |
| Verifier | Basic | Full safety proof |
| Max instructions | ~4096 | 1M (kernel 5.2+) |
| Tail calls | No | Yes |
| BTF/CO-RE | No | Yes |

eBPF was no longer just a packet filter. It became a **general-purpose, kernel-resident, event-driven programming platform**.

### Key Milestones

| Year | Kernel | Milestone |
|---|---|---|
| 2014 | 3.18 | eBPF merged (socket filters, maps) |
| 2015 | 4.1 | kprobes, TC classifier, JIT for x86-64 |
| 2016 | 4.7 | tracepoints, perf events |
| 2016 | 4.8 | XDP (eXpress Data Path) |
| 2017 | 4.10 | cgroup BPF programs |
| 2018 | 4.17 | BTF (BPF Type Format) |
| 2019 | 5.2 | 1M instruction limit, bounded loops |
| 2020 | 5.7 | LSM BPF hooks, ringbuf map |
| 2021 | 5.13 | CO-RE stabilized, BPF iterators |
| 2022 | 5.15–5.19 | BPF timers, global subprogs, kfuncs |
| 2023 | 6.0+ | BPF token, struct_ops expansion |

---

## 3. Linux Kernel Architecture & Where eBPF Lives

### The Linux Kernel in Brief

The Linux kernel manages hardware and provides abstractions to userspace. Its major subsystems are:

```
┌─────────────────────────────────────────────────────────┐
│                     User Space                          │
│  Applications │ libc │ System Libraries │ Shell        │
├─────────────────────────────────────────────────────────┤
│                  System Call Interface                  │
├──────────────┬──────────────┬──────────────────────────┤
│   Process    │   Memory     │   Virtual File System    │
│  Scheduler   │  Manager     │   (VFS)                 │
├──────────────┴──────────────┴──────────────────────────┤
│     Networking Stack    │   Device Drivers             │
│  (sk_buff, TCP/IP/      │   Block Layer                │
│   netfilter, XDP)       │   IPC                        │
├─────────────────────────────────────────────────────────┤
│                 Hardware Abstraction                    │
└─────────────────────────────────────────────────────────┘
```

### Where eBPF Hooks Into the Kernel

eBPF does not live in one place — it is **woven throughout the kernel** at dozens of hook points:

```
Kernel Subsystem            Hook Points
─────────────────────────────────────────────────────────
Networking
  ├── NIC Driver (XDP)      ──→ Earliest possible, pre-skb
  ├── TC Ingress/Egress     ──→ Traffic Control layer
  ├── Socket level          ──→ sk_filter, sock_ops
  ├── cgroup socket         ──→ bind/connect/sendmsg/recvmsg
  └── Netfilter             ──→ (via nftables BPF integration)

Tracing & Observability
  ├── kprobes               ──→ Any kernel function entry/return
  ├── uprobes               ──→ Any userspace function entry/return
  ├── tracepoints           ──→ Static kernel trace events
  ├── perf_event            ──→ HW counters, sampling
  └── fentry/fexit          ──→ Fast trampoline-based probes (5.5+)

Security
  ├── LSM hooks             ──→ 200+ security decision points
  └── seccomp BPF           ──→ Syscall filtering

Process/cgroup
  ├── cgroup device         ──→ /dev access control
  ├── cgroup net            ──→ per-cgroup network policy
  └── cgroup sysctl         ──→ sysctl access control
```

### The `bpf()` System Call

Everything eBPF goes through a single system call: `bpf(2)`. It was added in Linux 3.18.

```c
#include <linux/bpf.h>

int bpf(int cmd, union bpf_attr *attr, unsigned int size);
```

Commands include:

| Command | Purpose |
|---|---|
| `BPF_PROG_LOAD` | Load and verify an eBPF program |
| `BPF_MAP_CREATE` | Create a BPF map |
| `BPF_MAP_LOOKUP_ELEM` | Read a map entry |
| `BPF_MAP_UPDATE_ELEM` | Write a map entry |
| `BPF_MAP_DELETE_ELEM` | Delete a map entry |
| `BPF_PROG_ATTACH` | Attach program to hook |
| `BPF_PROG_DETACH` | Detach program |
| `BPF_OBJ_PIN` | Pin object to BPF filesystem |
| `BPF_OBJ_GET` | Retrieve pinned object |
| `BPF_BTF_LOAD` | Load BTF metadata |
| `BPF_LINK_CREATE` | Create a persistent link |

The BPF filesystem is mounted at `/sys/fs/bpf/` and allows programs and maps to persist beyond the lifetime of the process that loaded them.

---

## 4. The eBPF Virtual Machine

### Architecture

eBPF is a register-based virtual machine. It has:

- **11 registers** (R0–R10), each 64-bit wide
- **512-byte stack**
- **64-bit instruction set** (each instruction is 8 bytes)
- **Little-endian** (on all current architectures)

### Registers and Their Roles

| Register | Role |
|---|---|
| R0 | Return value from helper calls; program exit value |
| R1–R5 | Function arguments (R1 = first arg, etc.) |
| R6–R9 | Callee-saved, general purpose |
| R10 | Read-only frame pointer (stack base) |
| R1 at program entry | Pointer to the context (e.g., `struct xdp_md *`, `struct __sk_buff *`) |

### Instruction Format

Each eBPF instruction is 64 bits:

```
 63      48 47    40 39    32 31          16 15          0
┌──────────┬────────┬────────┬──────────────┬─────────────┐
│  imm     │ offset │  src   │     dst      │    opcode   │
│ (32 bits)│(16 bits│(4 bits)│   (4 bits)   │   (8 bits)  │
└──────────┴────────┴────────┴──────────────┴─────────────┘
```

### Instruction Classes

```
BPF_LD    (0x00) – Load
BPF_LDX   (0x01) – Load from register
BPF_ST    (0x02) – Store immediate
BPF_STX   (0x03) – Store from register
BPF_ALU   (0x04) – 32-bit arithmetic
BPF_JMP   (0x05) – Jump
BPF_JMP32 (0x06) – 32-bit jump
BPF_ALU64 (0x07) – 64-bit arithmetic
```

### Sample eBPF Bytecode (conceptual)

This is what a simple eBPF program looks like at the bytecode level:

```
; Load the packet length into R0 from context
lddw  r1, 0x0          ; load pointer offset 0 from ctx
ldxw  r0, [r1+0]       ; dereference

; Check if length > 1500
jgt   r0, 1500, +2     ; if r0 > 1500, jump 2 instructions

; Return 1 (pass)
mov   r0, 1
exit

; Return 0 (drop)
mov   r0, 0
exit
```

### The Context Pointer

When an eBPF program is called, `R1` always holds a pointer to its **context** — a data structure specific to the program type:

| Program Type | Context Type |
|---|---|
| XDP | `struct xdp_md *` |
| TC/socket filter | `struct __sk_buff *` |
| kprobe | `struct pt_regs *` |
| tracepoint | Pointer to tracepoint args struct |
| LSM | Varies per hook |
| cgroup | `struct bpf_sock *` or similar |

The context gives the eBPF program access to the data relevant to the event. For XDP, it's the raw packet data. For a kprobe, it's the CPU register state at the time the function was called.

---

## 5. The Verifier — The Gatekeeper

This is arguably the most important component of the entire eBPF system. The verifier is what makes eBPF **safe to run in kernel space without crashing the system**.

### What the Verifier Does

Before any eBPF bytecode is JIT-compiled and executed, the kernel's verifier performs a complete **static analysis** of the program. This is not runtime protection — it happens once at load time, and if the program passes, it is certified safe for all future executions.

The verifier checks:

1. **Control Flow Graph (CFG) validation** — Builds a DAG of all basic blocks. Ensures there are no unreachable instructions, and that all paths through the program terminate.

2. **Bounded loops** — Historically, loops were forbidden entirely. Since kernel 5.3, bounded loops (where the verifier can statically prove termination) are allowed. The verifier tracks loop iteration counts.

3. **Type safety on pointers** — Every register has a tracked type. If R1 holds a packet pointer, the verifier knows this. Arithmetic on packet pointers is tracked to detect out-of-bounds access.

4. **Memory access bounds checking** — Every memory dereference is checked. You cannot read beyond a packet's valid range, beyond a map value's size, or outside the 512-byte stack.

5. **Uninitialized data** — The verifier tracks which stack slots and registers have been written before being read.

6. **Helper function argument validation** — Every call to a BPF helper function is checked: argument types, pointer safety, size correctness.

7. **Return value range** — For programs that return a verdict (like XDP or seccomp), the verifier ensures the return value is one of the valid constants.

8. **Privilege checks** — Unprivileged eBPF is limited to socket filters. Most eBPF program types require `CAP_BPF` (kernel 5.8+) or `CAP_SYS_ADMIN`.

### Verifier Internals: Abstract Interpretation

The verifier works by **simulating every possible execution path** through the program simultaneously. It maintains a **verifier state** that tracks, for each register and stack slot:

- The **type** (scalar integer, pointer to map value, pointer to packet, null, etc.)
- For scalar integers: a **value range** (min, max, min32, max32) — the set of values this register could possibly hold
- **Liveness** information — has this register been read since last written?

This is called **abstract interpretation** — instead of running the program with concrete values, the verifier runs it with abstract ranges, proving properties that hold for all concrete values.

```
Example:
  r1 = packet_data     ; type: PTR_TO_PACKET, offset 0
  r2 = packet_end      ; type: PTR_TO_PACKET_END
  r3 = r1 + 14         ; type: PTR_TO_PACKET, offset 14

  ; Bounds check: is r1+14 still within packet?
  if r3 > r2: goto drop
  ; ← After this branch, verifier knows: r3 <= r2
  ; so dereferencing [r3, r3+1] is safe

  r4 = *(u16 *)(r3)    ; ALLOWED: verifier proved bounds
```

Without the explicit bounds check `if r3 > r2`, the dereference would be **rejected** by the verifier.

### Verifier Complexity and the "Instruction Limit"

Older kernels (< 5.2) had a hard limit of 4096 instructions. This was raised to **1 million instructions** in kernel 5.2. But the real constraint is **verifier complexity** — the number of states the verifier must explore. Complex programs with many branches and loops can hit the verifier's state limit even if they are logically correct.

### When the Verifier Rejects Programs

The verifier will reject:

```c
// Unguarded pointer dereference — REJECTED
int xdp_prog(struct xdp_md *ctx) {
    void *data = (void *)(long)ctx->data;
    __u8 byte = *((__u8 *)data);  // no bounds check!
    return XDP_PASS;
}

// Infinite loop — REJECTED (pre-5.3)
int prog(struct xdp_md *ctx) {
    for (;;) { /* ... */ }
    return XDP_PASS;
}

// Null pointer dereference — REJECTED
int prog(struct pt_regs *ctx) {
    struct task_struct *t = NULL;
    return t->pid;  // null dereference!
}
```

The correct pattern for the first example:

```c
int xdp_prog(struct xdp_md *ctx) {
    void *data     = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;

    if (data + 1 > data_end) return XDP_DROP;  // bounds check

    __u8 byte = *((__u8 *)data);  // ALLOWED: verifier knows it's safe
    return XDP_PASS;
}
```

---

## 6. JIT Compilation

After verification, eBPF bytecode is translated to **native machine code** by the JIT (Just-In-Time) compiler. This is what makes eBPF fast — after loading, programs run as native instructions on the CPU, not as interpreted bytecode.

### Supported Architectures

| Architecture | JIT Support |
|---|---|
| x86-64 | Full (since 3.18) |
| ARM64 | Full (since 3.18) |
| s390 | Full |
| PowerPC 64 | Full |
| MIPS | Partial |
| RISC-V 64 | Full (since 5.1) |
| ARM 32-bit | Partial |

### Enabling JIT

```bash
# Check current JIT status
cat /proc/sys/net/core/bpf_jit_enable

# Enable JIT (0=disabled, 1=enabled, 2=enabled+debug)
echo 1 > /proc/sys/net/core/bpf_jit_enable

# On modern kernels, JIT is enabled by default and mandatory for security
# (JIT hardening closes timing side-channel attacks on BPF interpreter)
```

### JIT vs Interpreter Performance

The eBPF interpreter adds significant overhead per instruction (roughly 20–30 ns overhead per instruction at function call boundary). The JIT-compiled version runs at native CPU speed — for XDP programs, this can mean packet processing at **tens of millions of packets per second** on a single CPU core.

The JIT compiler also performs optimizations:
- Register allocation (eBPF R0–R10 → real CPU registers)
- Immediate operand folding
- Constant propagation for known helper call arguments
- Tail call trampolines

---

## 7. eBPF Program Types & Attachment Points

Each program type has a specific purpose, context structure, and set of allowed helper functions. Here is a comprehensive breakdown:

### 7.1 XDP — eXpress Data Path

**The fastest packet processing hook in Linux.**

XDP programs run in the **network driver interrupt handler**, before a socket buffer (`sk_buff`) is even allocated. This makes them extraordinarily efficient for high-throughput packet processing.

```
NIC Receive Queue
       │
       ▼
[XDP Program runs HERE — raw packet memory, no sk_buff]
       │
   ┌───┴───────────────┐
   │ Return code       │
   ├───────────────────┤
   │ XDP_DROP          │  Discard packet immediately (DDoS mitigation)
   │ XDP_PASS          │  Pass to normal kernel networking stack
   │ XDP_TX            │  Retransmit out the same interface
   │ XDP_REDIRECT      │  Redirect to another interface or CPU/socket
   │ XDP_ABORTED       │  Drop with tracepoint error
   └───────────────────┘
```

**XDP Modes:**
- **Native XDP**: Driver-level, maximum performance. Requires driver support.
- **Generic XDP**: Works on all drivers via `sk_buff`, slower (but portable).
- **Offloaded XDP**: Program runs on the **NIC's own CPU** — completely CPU-free for the host.

### 7.2 TC — Traffic Control BPF

TC programs attach to the **`cls_bpf`** classifier in Linux's `tc` (traffic control) infrastructure. They run at the TC ingress and egress hooks, **after** `sk_buff` allocation but before/after the main network stack.

```
Ingress:  NIC → [TC Ingress BPF] → Network Stack → Socket
Egress:   Socket → Network Stack → [TC Egress BPF] → NIC
```

Return codes:
- `TC_ACT_OK (0)` — Continue processing
- `TC_ACT_SHOT (2)` — Drop
- `TC_ACT_REDIRECT (7)` — Redirect packet
- `TC_ACT_UNSPEC (-1)` — Continue with next classifier

TC programs can both read **and modify** packet contents, making them powerful for network function virtualization (NAT, load balancing, tunneling).

### 7.3 Socket Filter (`BPF_PROG_TYPE_SOCKET_FILTER`)

The original eBPF use case. Attached to sockets via `setsockopt(SO_ATTACH_BPF)`. Filters which packets are delivered to the socket. Used by `tcpdump`, Wireshark, and packet capture tools.

### 7.4 kprobes and kretprobes

**kprobes** dynamically instrument any kernel function. The kernel's kprobe infrastructure replaces the first byte of the target function with a breakpoint instruction. When the CPU hits it, the kprobe handler calls your eBPF program.

- **kprobe**: Fires at function **entry**. Context: `struct pt_regs *` — you can read function arguments.
- **kretprobe**: Fires at function **return**. Context: `struct pt_regs *` — you can read the return value.

```
sys_read() called
     │
     ▼
[kprobe eBPF program fires: can see fd, buf, count arguments]
     │
     ▼
sys_read() executes normally
     │
     ▼
[kretprobe eBPF program fires: can see return value (bytes read)]
     │
     ▼
Returns to caller
```

**Caution**: kprobes are unstable ABI. Kernel function names and signatures can change across kernel versions.

### 7.5 fentry/fexit (Fprobe/BPF trampolines — kernel 5.5+)

The modern replacement for kprobes/kretprobes. They use a **static trampoline** injected by the kernel's ftrace infrastructure — much lower overhead than kprobes (no int3 breakpoint, no TRAP handler).

- More than **10× faster** than kprobes in some benchmarks
- Require BTF for type-safe argument access
- Cannot attach to all functions (only those with `ALLOW_ERROR_INJECTION` or BTF info)

### 7.6 Tracepoints

**Static instrumentation points** explicitly placed in the kernel source. They are stable ABI — they persist across kernel versions and their argument structures are documented.

```c
// In kernel source: include/trace/events/sched.h
TRACE_EVENT(sched_process_fork, ...)

// Your eBPF program attaches to: tracepoint/sched/sched_process_fork
```

Tracepoints are preferable to kprobes when you want **stable, portable** instrumentation. The kernel exposes all tracepoints via:

```bash
cat /sys/kernel/debug/tracing/events/sched/sched_process_fork/format
```

### 7.7 perf_event

Attach eBPF to hardware performance counters (CPU cycles, cache misses, branch mispredictions), software perf events (context switches, page faults), and hardware breakpoints. Enables **CPU profiling** with eBPF.

### 7.8 LSM BPF — Linux Security Module Hooks (kernel 5.7+)

Attach eBPF programs to any of the 200+ LSM hooks in the kernel. This is the hook point for security enforcement:

```c
// Deny file open based on custom logic
SEC("lsm/file_open")
int BPF_PROG(file_open_hook, struct file *file) {
    // Return 0 to allow, negative errno to deny
    return 0;
}
```

LSM BPF (also called KRSI — Kernel Runtime Security Instrumentation) enables building **custom, programmable security policies** that run in kernel space.

### 7.9 cgroup BPF

Programs attached to cgroups (control groups) to enforce per-process-group policies:

| Type | Purpose |
|---|---|
| `BPF_CGROUP_INET_INGRESS` | Filter incoming traffic for cgroup |
| `BPF_CGROUP_INET_EGRESS` | Filter outgoing traffic for cgroup |
| `BPF_CGROUP_SOCK_OPS` | TCP socket events, tune TCP params |
| `BPF_CGROUP_DEVICE` | Allow/deny /dev access |
| `BPF_CGROUP_SYSCTL` | Allow/deny sysctl reads/writes |
| `BPF_CGROUP_INET4_CONNECT` | Intercept connect() calls |
| `BPF_CGROUP_SENDMSG` | Intercept sendmsg() calls |

This is how Kubernetes CNI plugins like Cilium implement per-pod network policies.

### 7.10 sk_msg and sk_skb (Sockmap)

Programs that intercept messages between sockets using the **sockmap** infrastructure. Enable **zero-copy socket-to-socket redirection** and transparent proxying without leaving the kernel.

### 7.11 BPF Iterators (kernel 5.8+)

Programs that iterate over kernel objects (tasks, files, maps, cgroups) and produce output via `seq_file`. Allow building efficient `procfs`-like tools entirely in eBPF.

---

## 8. eBPF Maps — The Data Layer

Maps are the **persistent storage** and **communication channel** of eBPF. They are kernel data structures accessible from both the eBPF program (running in kernel context) and userspace via the `bpf()` syscall.

### Map Operations

```
eBPF Program (kernel) ←──────→ Map ←──────→ Userspace Process
   bpf_map_lookup_elem()               bpf(BPF_MAP_LOOKUP_ELEM)
   bpf_map_update_elem()               bpf(BPF_MAP_UPDATE_ELEM)
   bpf_map_delete_elem()               bpf(BPF_MAP_DELETE_ELEM)
```

### Map Types

#### `BPF_MAP_TYPE_HASH`

A generic hash map. O(1) average case for lookup/insert/delete. The key and value sizes are fixed at creation time.

```c
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 1024);
    __type(key, __u32);      // 4-byte key
    __type(value, __u64);    // 8-byte value
} my_map SEC(".maps");
```

#### `BPF_MAP_TYPE_ARRAY`

Array indexed by integer key (0 to max_entries-1). Faster than hash maps for dense integer keys. Values are **zero-initialized** and **cannot be deleted** (only overwritten). The entire array is pre-allocated.

```c
struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 256);
    __type(key, __u32);
    __type(value, __u64);
} counters SEC(".maps");
```

#### `BPF_MAP_TYPE_PERCPU_HASH` and `BPF_MAP_TYPE_PERCPU_ARRAY`

Per-CPU variants of hash and array maps. Each CPU core has its own copy of the map. This **eliminates lock contention** for high-frequency counter updates — each CPU updates its own copy. Userspace must aggregate values across CPUs.

This is essential for performance-critical counters (packet counts per source IP, syscall counts per process).

#### `BPF_MAP_TYPE_LRU_HASH`

Like `BPF_MAP_TYPE_HASH` but with LRU eviction when full. Essential for connection tracking tables where you don't want to manage capacity manually.

#### `BPF_MAP_TYPE_PERF_EVENT_ARRAY`

Used for sending **variable-length events** from eBPF programs to userspace via the `perf` ring buffer mechanism. Legacy approach — `BPF_MAP_TYPE_RINGBUF` is preferred for new code.

#### `BPF_MAP_TYPE_RINGBUF` (kernel 5.8+)

The modern event-streaming mechanism. A single ring buffer shared across all CPUs (unlike perf_event_array's per-CPU buffers). Benefits:

- **Better memory efficiency** — one buffer, not one per CPU
- **Ordering** — events are ordered across CPUs
- **Reservation model** — reserve space, fill it, then submit atomically
- **Zero-copy** — userspace can mmap and read directly without copying

```c
// eBPF side
struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 1 << 24);  // 16 MB
} rb SEC(".maps");

// Reserve and submit an event
struct event *e = bpf_ringbuf_reserve(&rb, sizeof(*e), 0);
if (!e) return 0;
e->pid = bpf_get_current_pid_tgid() >> 32;
bpf_ringbuf_submit(e, 0);
```

#### `BPF_MAP_TYPE_PROG_ARRAY`

Stores file descriptors of other eBPF programs. Used for **tail calls** — jumping to another eBPF program without returning. Enables program chaining and modular eBPF architectures.

#### `BPF_MAP_TYPE_STACK_TRACE`

Stores kernel or userspace stack traces (arrays of instruction pointers). Used for profiling.

#### `BPF_MAP_TYPE_SOCKMAP` and `BPF_MAP_TYPE_SOCKHASH`

Stores references to sockets. Used with `sk_msg` and `sk_skb` programs for socket redirection.

#### `BPF_MAP_TYPE_DEVMAP` and `BPF_MAP_TYPE_CPUMAP`

Used with XDP redirect. DEVMAP maps interface indices to XDP programs for multi-NIC routing. CPUMAP redirects packets to other CPUs for parallel processing.

#### `BPF_MAP_TYPE_STRUCT_OPS` (kernel 5.6+)

Allows eBPF programs to **implement kernel interfaces** (struct ops). The most prominent use case is custom TCP congestion control algorithms written entirely in eBPF.

#### `BPF_MAP_TYPE_BLOOM_FILTER` (kernel 5.16+)

A probabilistic set membership structure. No false negatives, possible false positives. Extremely space-efficient for "have I seen this IP before?" type queries.

### Map Pinning

Maps can be **pinned** to the BPF filesystem to persist beyond the lifetime of the creating process:

```c
// Pin a map
bpf_obj_pin(map_fd, "/sys/fs/bpf/my_map");

// Retrieve the map later (even from a different process)
int map_fd = bpf_obj_get("/sys/fs/bpf/my_map");
```

---

## 9. Helper Functions

eBPF programs cannot call arbitrary kernel functions. Instead, they call **helper functions** — a stable API defined by the kernel. As of Linux 6.x, there are over 200 helper functions.

### Why Helpers?

Allowing arbitrary kernel function calls would:
- Break the stable ABI (helper function signatures are stable, internal functions are not)
- Complicate the verifier (it would need to analyze all transitive calls)
- Enable unsafe operations

Helpers are individually reviewed for safety and are part of the stable eBPF API.

### Key Helper Functions

#### Packet Manipulation
```c
// Adjust packet headroom (e.g., add/remove encapsulation header)
long bpf_xdp_adjust_head(struct xdp_md *xdp_md, int delta);

// Adjust packet tail (truncate or extend)
long bpf_xdp_adjust_tail(struct xdp_md *xdp_md, int delta);

// Redirect packet to a different interface
long bpf_redirect(u32 ifindex, u64 flags);
```

#### Map Operations
```c
// Look up a value in a map
void *bpf_map_lookup_elem(struct bpf_map *map, const void *key);

// Insert or update a map element
long bpf_map_update_elem(struct bpf_map *map, const void *key,
                         const void *value, u64 flags);

// Delete a map element
long bpf_map_delete_elem(struct bpf_map *map, const void *key);
```

#### Process/Task Information
```c
// Get current PID and TGID (tgid << 32 | pid)
u64 bpf_get_current_pid_tgid(void);

// Get current UID and GID
u64 bpf_get_current_uid_gid(void);

// Get current process name (comm)
long bpf_get_current_comm(void *buf, u32 size_of_buf);

// Get a pointer to the current task_struct
struct task_struct *bpf_get_current_task(void);
```

#### Timing
```c
// Get nanosecond timestamp (CLOCK_MONOTONIC)
u64 bpf_ktime_get_ns(void);

// Get nanosecond timestamp (CLOCK_BOOTTIME)
u64 bpf_ktime_get_boot_ns(void);
```

#### Memory and Probing
```c
// Read from kernel memory (safer than direct dereference for sleeping contexts)
long bpf_probe_read_kernel(void *dst, u32 size, const void *unsafe_ptr);

// Read from userspace memory
long bpf_probe_read_user(void *dst, u32 size, const void *unsafe_ptr);

// Read a string from userspace
long bpf_probe_read_user_str(void *dst, u32 size, const void *unsafe_str);
```

#### Output and Debugging
```c
// Send data to userspace via perf ring buffer
long bpf_perf_event_output(void *ctx, struct bpf_map *map, u64 flags,
                            void *data, u64 size);

// Debug printing (goes to /sys/kernel/debug/tracing/trace_pipe)
long bpf_trace_printk(const char *fmt, u32 fmt_size, ...);
```

#### Tail Calls
```c
// Jump to another eBPF program (does not return)
long bpf_tail_call(void *ctx, struct bpf_map *prog_array_map, u32 index);
```

#### Checksums
```c
// Compute internet checksum
u64 bpf_csum_diff(const void *from, u32 from_size, const void *to,
                  u32 to_size, u32 seed);

// Store a checksum into a packet
long bpf_l3_csum_replace(struct sk_buff *skb, u32 offset, u64 from,
                         u64 to, u64 flags);
```

### kfuncs — Kernel Functions (kernel 5.13+)

Beyond stable helpers, specific kernel functions can be exported to eBPF via the **kfunc** mechanism. Unlike helpers, kfuncs are not part of a stable API, but they are explicitly whitelisted and type-safe via BTF. They allow eBPF access to more kernel internals without requiring a new helper function.

---

## 10. BTF — BPF Type Format

BTF (BPF Type Format) is a **compact binary encoding of type information** for eBPF programs and the kernel itself. It is conceptually similar to DWARF debug information, but much more compact and designed for the eBPF use case.

### What BTF Encodes

- C struct/union/enum definitions
- Function signatures (argument types, return types)
- Type relationships (pointers, arrays, typedefs)
- Source file line information (for verifier error messages)

### BTF in the Kernel

Since kernel 5.4, the kernel is built with its own BTF information embedded in the running kernel at `/sys/kernel/btf/vmlinux`. This is a machine-readable description of **every** struct, function, and type in the running kernel.

You can inspect it:

```bash
# List all struct types in the kernel BTF
bpftool btf dump file /sys/kernel/btf/vmlinux format raw | grep 'struct'

# Pretty-print a specific type
bpftool btf dump file /sys/kernel/btf/vmlinux format c | grep -A 20 'struct task_struct'
```

### BTF and the Verifier

BTF enables the verifier to perform **type-aware checking**:

- When you write `task->comm`, the verifier can verify that `comm` is actually a field of `struct task_struct` at the correct offset
- When you call an `fentry` program on `sys_read`, BTF tells the verifier the exact types of the arguments
- Error messages become human-readable (field names instead of byte offsets)

### BTF-enabled Programs

Programs annotated with BTF use **typed eBPF programs** — where arguments are directly typed C structs, not raw register access:

```c
// Old style (kprobe, raw register access)
SEC("kprobe/sys_read")
int old_style(struct pt_regs *ctx) {
    int fd = PT_REGS_PARM1(ctx);   // cast and hope
    ...
}

// New style (fentry, BTF-typed)
SEC("fentry/ksys_read")
int BPF_PROG(new_style, unsigned int fd, char __user *buf, size_t count) {
    // fd, buf, count are the ACTUAL typed arguments
    ...
}
```

---

## 11. CO-RE — Compile Once, Run Everywhere

One of the historical pain points of eBPF was **portability**. An eBPF program compiled on kernel 5.15 that accesses `task->pid` at byte offset 1234 would silently read garbage on a different kernel where `pid` is at byte offset 1238 (due to different config/version).

CO-RE solves this.

### The CO-RE Mechanism

CO-RE works by recording **field access patterns** in the eBPF object file using BTF relocations. At load time, `libbpf` reads both the program's BTF (describing what the program was compiled against) and the **running kernel's BTF** (at `/sys/kernel/btf/vmlinux`), and **patches** the eBPF bytecode to use the correct offsets for the running kernel.

```
Compilation time:
  Source code compiled against vmlinux.h (generated from BTF)
  BTF relocation entries embedded in .o file:
    "Access field 'pid' of struct task_struct"

Load time (on any kernel with BTF):
  libbpf reads kernel's /sys/kernel/btf/vmlinux
  libbpf finds where 'pid' is in THIS kernel's task_struct
  libbpf patches the field offset in the bytecode
  Kernel verifies and loads patched program
```

### The `vmlinux.h` Header

The `vmlinux.h` file is a single massive auto-generated header containing all kernel type definitions, generated from a kernel's BTF:

```bash
bpftool btf dump file /sys/kernel/btf/vmlinux format c > vmlinux.h
```

This replaces the need to `#include` dozens of kernel headers. One file, all types, for any kernel that supports BTF.

### CO-RE Macros

libbpf provides macros for CO-RE-safe field access:

```c
#include "vmlinux.h"
#include <bpf/bpf_core_read.h>

SEC("kprobe/wake_up_new_task")
int trace_new_task(struct pt_regs *ctx) {
    struct task_struct *task = (struct task_struct *)PT_REGS_PARM1(ctx);

    // BPF_CORE_READ: safely read task->pid with CO-RE relocation
    pid_t pid = BPF_CORE_READ(task, pid);

    // BPF_CORE_READ_INTO: read into a local variable
    char comm[16];
    BPF_CORE_READ_STR_INTO(&comm, task, comm);

    return 0;
}
```

`BPF_CORE_READ(task, pid)` compiles to a BTF relocation saying "read field 'pid' from struct task_struct via this pointer". At load time, libbpf resolves the actual offset.

---

## 12. The eBPF Toolchain Ecosystem

### Compilation Pipeline

```
Your .c file
     │
     ▼
[Clang/LLVM — with -target bpf]
     │
     ▼
eBPF object file (.o)  — contains eBPF bytecode + BTF + relocations
     │
     ▼
[libbpf / aya / bcc — loader library]
     │  • Reads .o file
     │  • Processes BTF relocations (CO-RE)
     │  • Creates maps via bpf() syscall
     │  • Loads program via BPF_PROG_LOAD
     │  • Attaches to hook point
     ▼
Running eBPF program in kernel
```

### Major Toolchains

#### libbpf (C)
The **official, upstream** C library for eBPF. Maintained in the Linux kernel repository and mirrored at github.com/libbpf/libbpf. The reference implementation for CO-RE.

#### BCC (BPF Compiler Collection)
Python/Lua/C++ toolkit. Embeds the entire LLVM/Clang toolchain and compiles eBPF programs **at runtime**. Easy to use but has a large binary footprint. Good for rapid prototyping. Not ideal for production (requires kernel headers on the target system).

#### bpftrace
A high-level tracing language for eBPF, similar to DTrace's D language. One-liners for ad-hoc system introspection:

```bash
# Trace all open() calls with filenames
bpftrace -e 'tracepoint:syscalls:sys_enter_openat { printf("%s %s\n", comm, str(args->filename)); }'

# Profile CPU usage by stack trace
bpftrace -e 'profile:99 { @[kstack] = count(); }'

# Trace TCP connections
bpftrace -e 'kprobe:tcp_connect { printf("connect: %s\n", comm); }'
```

#### Aya (Rust)
The premier Rust eBPF framework. Write both the kernel-side and userspace-side in Rust. Full CO-RE support.

#### libbpf-rs
Rust bindings to libbpf, using C libbpf under the hood via FFI.

#### ebpf-go (Go)
Full-featured Go eBPF library used by Cilium. No CGo dependency.

---

## 13. Writing eBPF Programs in C (libbpf)

### Project Setup

```
my-ebpf-project/
├── Makefile
├── include/
│   └── vmlinux.h           # Generated: bpftool btf dump ... format c
├── src/
│   ├── my_prog.bpf.c       # eBPF kernel-side code
│   └── my_prog.c           # Userspace loader
└── README.md
```

### Installing Dependencies

```bash
# Ubuntu/Debian
apt-get install clang llvm libbpf-dev linux-headers-$(uname -r) bpftool

# Fedora/RHEL
dnf install clang llvm libbpf-devel kernel-devel bpftool

# Generate vmlinux.h
bpftool btf dump file /sys/kernel/btf/vmlinux format c > include/vmlinux.h
```

---

### Example 1: Tracing execve() with tracepoints

**Kernel-side: `execve_trace.bpf.c`**

```c
// SPDX-License-Identifier: GPL-2.0 OR BSD-3-Clause
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>

// License declaration is mandatory
char LICENSE[] SEC("license") = "Dual BSD/GPL";

// Event structure for userspace communication
struct event {
    u32  pid;
    u32  ppid;
    u32  uid;
    char comm[16];
    char filename[256];
};

// Ring buffer for events to userspace
struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 1 << 24);  // 16 MB
} rb SEC(".maps");

// Attach to the sys_enter_execve tracepoint
// Args struct is auto-generated from kernel BTF
SEC("tracepoint/syscalls/sys_enter_execve")
int tracepoint__syscalls__sys_enter_execve(struct trace_event_raw_sys_enter *ctx)
{
    // Reserve space in the ring buffer
    struct event *e = bpf_ringbuf_reserve(&rb, sizeof(*e), 0);
    if (!e)
        return 0;

    // Get process identity
    u64 id    = bpf_get_current_pid_tgid();
    u64 uid_g = bpf_get_current_uid_gid();

    e->pid = id >> 32;
    e->uid = (u32)uid_g;

    // Get parent PID via CO-RE read on task_struct
    struct task_struct *task = (struct task_struct *)bpf_get_current_task();
    e->ppid = BPF_CORE_READ(task, real_parent, tgid);

    // Get the command name
    bpf_get_current_comm(&e->comm, sizeof(e->comm));

    // Read the filename argument from the tracepoint context
    // ctx->args[0] is the first syscall argument (const char __user *filename)
    const char *filename = (const char *)ctx->args[0];
    bpf_probe_read_user_str(e->filename, sizeof(e->filename), filename);

    // Submit the event to userspace
    bpf_ringbuf_submit(e, 0);
    return 0;
}
```

**Userspace: `execve_trace.c`**

```c
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>
#include <bpf/libbpf.h>
#include "execve_trace.skel.h"  // Auto-generated by bpftool gen skeleton

// Event structure must match the one in the BPF program
struct event {
    __u32 pid;
    __u32 ppid;
    __u32 uid;
    char  comm[16];
    char  filename[256];
};

// Callback for ring buffer events
static int handle_event(void *ctx, void *data, size_t size)
{
    struct event *e = data;
    printf("%-8d %-8d %-8d %-16s %s\n",
           e->pid, e->ppid, e->uid, e->comm, e->filename);
    return 0;
}

static volatile bool running = true;

static void sig_handler(int sig)
{
    running = false;
}

int main(void)
{
    struct execve_trace_bpf *skel;
    struct ring_buffer *rb;
    int err;

    // Set up libbpf error and debug info callback
    libbpf_set_print(NULL);  // or provide a custom print function

    // Open the BPF skeleton (loads .o file)
    skel = execve_trace_bpf__open();
    if (!skel) {
        fprintf(stderr, "Failed to open BPF skeleton\n");
        return 1;
    }

    // Load & verify the BPF program
    err = execve_trace_bpf__load(skel);
    if (err) {
        fprintf(stderr, "Failed to load BPF skeleton: %d\n", err);
        goto cleanup;
    }

    // Attach to the tracepoint
    err = execve_trace_bpf__attach(skel);
    if (err) {
        fprintf(stderr, "Failed to attach BPF skeleton: %d\n", err);
        goto cleanup;
    }

    // Set up ring buffer polling
    rb = ring_buffer__new(bpf_map__fd(skel->maps.rb), handle_event, NULL, NULL);
    if (!rb) {
        fprintf(stderr, "Failed to create ring buffer\n");
        goto cleanup;
    }

    signal(SIGINT,  sig_handler);
    signal(SIGTERM, sig_handler);

    printf("%-8s %-8s %-8s %-16s %s\n",
           "PID", "PPID", "UID", "COMM", "FILENAME");

    // Main event loop
    while (running) {
        err = ring_buffer__poll(rb, 100 /* ms timeout */);
        if (err == -EINTR) break;
        if (err < 0) {
            fprintf(stderr, "ring_buffer__poll error: %d\n", err);
            break;
        }
    }

    ring_buffer__free(rb);

cleanup:
    execve_trace_bpf__destroy(skel);
    return err < 0 ? -err : 0;
}
```

**Makefile**

```makefile
CLANG    ?= clang
ARCH     := $(shell uname -m | sed 's/x86_64/x86/' | sed 's/aarch64/arm64/')
BPF_CFLAGS := -g -O2 -target bpf -D__TARGET_ARCH_$(ARCH)

# Generate skeleton from BPF object
%.skel.h: %.bpf.o
	bpftool gen skeleton $< > $@

# Compile BPF program
%.bpf.o: %.bpf.c vmlinux.h
	$(CLANG) $(BPF_CFLAGS) -c $< -o $@

# Compile userspace loader
execve_trace: execve_trace.c execve_trace.skel.h
	$(CC) -Wall -O2 $< -lbpf -lelf -lz -o $@

vmlinux.h:
	bpftool btf dump file /sys/kernel/btf/vmlinux format c > $@

clean:
	rm -f *.o *.skel.h execve_trace vmlinux.h
```

---

### Example 2: XDP Packet Counter with Per-CPU Maps

**Kernel-side: `xdp_counter.bpf.c`**

```c
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

char LICENSE[] SEC("license") = "GPL";

// Protocol counters: key = IP protocol number, value = packet count
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 256);   // 0-255 IP protocol numbers
    __type(key, __u32);
    __type(value, __u64);
} proto_counters SEC(".maps");

// Drop set: IPs to drop (simple hash map)
struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __uint(max_entries, 100000);
    __type(key, __u32);    // IPv4 source address
    __type(value, __u8);   // dummy value
} blocked_ips SEC(".maps");

// Ethernet header (14 bytes)
struct ethhdr_local {
    unsigned char h_dest[6];
    unsigned char h_source[6];
    __be16 h_proto;
};

// IPv4 header
struct iphdr_local {
    __u8  ihl:4,
          version:4;
    __u8  tos;
    __be16 tot_len;
    __be16 id;
    __be16 frag_off;
    __u8  ttl;
    __u8  protocol;
    __be16 check;
    __be32 saddr;
    __be32 daddr;
};

SEC("xdp")
int xdp_prog(struct xdp_md *ctx)
{
    void *data     = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;

    // Parse Ethernet header
    struct ethhdr_local *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;

    // Only process IPv4
    if (bpf_ntohs(eth->h_proto) != 0x0800)
        return XDP_PASS;

    // Parse IP header
    struct iphdr_local *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end)
        return XDP_PASS;

    // Check blocked IP set
    __u32 src_ip = ip->saddr;
    if (bpf_map_lookup_elem(&blocked_ips, &src_ip))
        return XDP_DROP;  // Drop packets from blocked IPs

    // Count by protocol
    __u32 proto = ip->protocol;
    __u64 *count = bpf_map_lookup_elem(&proto_counters, &proto);
    if (count)
        __sync_fetch_and_add(count, 1);  // Atomic increment

    return XDP_PASS;
}
```

**Userspace: `xdp_counter.c`**

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <net/if.h>
#include <bpf/libbpf.h>
#include <bpf/bpf.h>
#include "xdp_counter.skel.h"

#define PROTO_TCP  6
#define PROTO_UDP  17
#define PROTO_ICMP 1

// Aggregate per-CPU values for an array map
static __u64 map_array_sum(int map_fd, __u32 key, int nr_cpus)
{
    __u64 values[nr_cpus];
    __u64 sum = 0;

    if (bpf_map_lookup_elem(map_fd, &key, values))
        return 0;

    for (int i = 0; i < nr_cpus; i++)
        sum += values[i];

    return sum;
}

int main(int argc, char **argv)
{
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <interface>\n", argv[0]);
        return 1;
    }

    const char *ifname = argv[1];
    int ifindex = if_nametoindex(ifname);
    if (!ifindex) {
        perror("if_nametoindex");
        return 1;
    }

    struct xdp_counter_bpf *skel = xdp_counter_bpf__open_and_load();
    if (!skel) {
        fprintf(stderr, "Failed to open/load BPF skeleton\n");
        return 1;
    }

    // Attach XDP program to the network interface
    // XDP_FLAGS_DRV_MODE = native XDP (driver-level)
    // XDP_FLAGS_SKB_MODE = generic XDP (sk_buff level, always works)
    int prog_fd = bpf_program__fd(skel->progs.xdp_prog);
    if (bpf_xdp_attach(ifindex, prog_fd, XDP_FLAGS_SKB_MODE, NULL)) {
        perror("bpf_xdp_attach");
        goto cleanup;
    }

    int map_fd    = bpf_map__fd(skel->maps.proto_counters);
    int nr_cpus   = libbpf_num_possible_cpus();

    printf("XDP attached to %s. Monitoring (Ctrl-C to stop)...\n\n", ifname);

    while (1) {
        sleep(1);
        printf("\rTCP: %-10llu UDP: %-10llu ICMP: %-10llu",
               map_array_sum(map_fd, PROTO_TCP,  nr_cpus),
               map_array_sum(map_fd, PROTO_UDP,  nr_cpus),
               map_array_sum(map_fd, PROTO_ICMP, nr_cpus));
        fflush(stdout);
    }

    // Detach XDP on exit
    bpf_xdp_detach(ifindex, XDP_FLAGS_SKB_MODE, NULL);

cleanup:
    xdp_counter_bpf__destroy(skel);
    return 0;
}
```

---

### Example 3: LSM Hook — File Open Audit

```c
// file_audit.bpf.c
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>

char LICENSE[] SEC("license") = "GPL";

struct audit_event {
    __u32 pid;
    __u32 uid;
    char  comm[16];
    char  filepath[256];
    int   denied;
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 1 << 22);
} audit_rb SEC(".maps");

// Deny list: inode numbers to protect
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 1024);
    __type(key, __u64);    // inode number
    __type(value, __u8);
} protected_inodes SEC(".maps");

SEC("lsm/file_open")
int BPF_PROG(audit_file_open, struct file *file)
{
    struct audit_event *e = bpf_ringbuf_reserve(&audit_rb, sizeof(*e), 0);
    if (!e)
        return 0;

    u64 pid_tgid = bpf_get_current_pid_tgid();
    e->pid = pid_tgid >> 32;
    e->uid = (u32)bpf_get_current_uid_gid();
    bpf_get_current_comm(&e->comm, sizeof(e->comm));

    // Read the file path using CO-RE
    struct dentry *dentry = BPF_CORE_READ(file, f_path.dentry);
    struct qstr   dname   = BPF_CORE_READ(dentry, d_name);
    bpf_probe_read_kernel_str(e->filepath, sizeof(e->filepath),
                              BPF_CORE_READ(dentry, d_name.name));

    // Check if this inode is protected
    __u64 ino = BPF_CORE_READ(file, f_inode, i_ino);
    e->denied = bpf_map_lookup_elem(&protected_inodes, &ino) ? 1 : 0;

    bpf_ringbuf_submit(e, 0);

    // Return -EPERM to deny access, 0 to allow
    return e->denied ? -1 : 0;
}
```

---

## 14. Writing eBPF Programs in Rust (Aya)

**Aya** is a pure-Rust eBPF library. Unlike libbpf-rs (which wraps C libbpf), Aya reimplements everything from scratch in Rust:

- No C dependency (no libbpf, no libc for the kernel-side code)
- Uses Rust's `no_std` environment for kernel-side programs
- Full CO-RE support
- Async-first userspace (tokio integration)

### Project Setup

```bash
# Install required tools
cargo install bpf-linker
rustup target add bpfel-unknown-none  # BPF little-endian target

# Create a new aya project
cargo install cargo-generate
cargo generate --git https://github.com/aya-rs/aya-template
```

### Aya Project Structure

```
my-aya-project/
├── Cargo.toml                    # Workspace manifest
├── my-prog/                      # Userspace crate
│   ├── Cargo.toml
│   └── src/
│       └── main.rs
└── my-prog-ebpf/                 # Kernel-side crate (no_std)
    ├── Cargo.toml
    └── src/
        └── main.rs
```

---

### Example 1: Tracing execve() with Aya

**Kernel-side: `my-prog-ebpf/src/main.rs`**

```rust
#![no_std]
#![no_main]

use aya_ebpf::{
    helpers::{bpf_get_current_comm, bpf_get_current_pid_tgid, bpf_probe_read_user_str_bytes},
    macros::{map, tracepoint},
    maps::RingBuf,
    programs::TracePointContext,
    EbpfContext,
};
use aya_log_ebpf::info;

// Shared data structure (must match userspace definition)
#[repr(C)]
pub struct ExecEvent {
    pub pid:      u32,
    pub uid:      u32,
    pub comm:     [u8; 16],
    pub filename: [u8; 256],
}

// Ring buffer map for events
#[map]
static EVENTS: RingBuf = RingBuf::with_byte_size(1 << 24, 0);

/// Attach to the sys_enter_execve tracepoint
#[tracepoint]
pub fn tracepoint_execve(ctx: TracePointContext) -> u32 {
    match try_execve(ctx) {
        Ok(ret)  => ret,
        Err(_)   => 1,
    }
}

fn try_execve(ctx: TracePointContext) -> Result<u32, i64> {
    // Reserve space in the ring buffer
    let mut entry = EVENTS.reserve::<ExecEvent>(0).ok_or(1i64)?;
    let event = entry.as_mut_ptr();

    // Safety: event points to reserved ring buffer memory
    unsafe {
        let e = &mut *event;

        // Get PID and UID
        let pid_tgid = bpf_get_current_pid_tgid();
        e.pid = (pid_tgid >> 32) as u32;
        e.uid = aya_ebpf::helpers::bpf_get_current_uid_gid() as u32;

        // Get process name
        let comm = bpf_get_current_comm().map_err(|e| e as i64)?;
        e.comm.copy_from_slice(&comm);

        // Read filename argument (first tracepoint arg)
        // Offset 16 = offset of args[0] in trace_event_raw_sys_enter
        let filename_ptr: *const u8 = ctx.read_at(16).map_err(|e| e as i64)?;
        let filename_slice = core::slice::from_raw_parts_mut(
            e.filename.as_mut_ptr(), 256
        );
        let _ = bpf_probe_read_user_str_bytes(filename_ptr, filename_slice);
    }

    // Submit the event to userspace
    entry.submit(0);
    Ok(0)
}

/// Required panic handler for no_std
#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {
    unsafe { core::hint::unreachable_unchecked() }
}
```

**Userspace: `my-prog/src/main.rs`**

```rust
use anyhow::Context;
use aya::{
    maps::RingBuf,
    programs::TracePoint,
    Ebpf,
};
use aya_log::EbpfLogger;
use clap::Parser;
use log::{info, warn};
use std::os::fd::AsFd;
use tokio::signal;

// Shared data structure — must exactly match kernel-side definition
#[repr(C)]
struct ExecEvent {
    pid:      u32,
    uid:      u32,
    comm:     [u8; 16],
    filename: [u8; 256],
}

#[derive(Debug, Parser)]
struct Opt {
    #[clap(short, long, default_value = "eth0")]
    iface: String,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    env_logger::init();

    // Load the compiled eBPF object file
    // The bytes are embedded at compile time via include_bytes_aligned!
    let mut ebpf = Ebpf::load(aya::include_bytes_aligned!(concat!(
        env!("OUT_DIR"),
        "/my-prog"
    )))?;

    // Set up eBPF logging
    if let Err(e) = EbpfLogger::init(&mut ebpf) {
        warn!("failed to initialize eBPF logger: {}", e);
    }

    // Get the tracepoint program
    let program: &mut TracePoint = ebpf
        .program_mut("tracepoint_execve")
        .unwrap()
        .try_into()?;

    // Load and attach the program to the tracepoint
    program.load()?;
    program.attach("syscalls", "sys_enter_execve")?;

    // Get the ring buffer map
    let ring_buf = ebpf.map_mut("EVENTS").unwrap();
    let mut ring_buf = RingBuf::try_from(ring_buf)?;

    println!("{:<8} {:<8} {:<16} {}", "PID", "UID", "COMM", "FILENAME");

    // Async event loop with Ctrl-C handling
    loop {
        tokio::select! {
            _ = signal::ctrl_c() => {
                info!("Exiting...");
                break;
            }
            _ = tokio::task::spawn_blocking(|| std::thread::sleep(
                    std::time::Duration::from_millis(100)
            )) => {
                // Poll ring buffer
                while let Some(item) = ring_buf.next() {
                    if item.len() < std::mem::size_of::<ExecEvent>() {
                        continue;
                    }
                    let event: &ExecEvent = unsafe {
                        &*(item.as_ptr() as *const ExecEvent)
                    };

                    let comm = std::str::from_utf8(&event.comm)
                        .unwrap_or("?")
                        .trim_end_matches('\0');
                    let filename = std::str::from_utf8(&event.filename)
                        .unwrap_or("?")
                        .trim_end_matches('\0');

                    println!("{:<8} {:<8} {:<16} {}",
                             event.pid, event.uid, comm, filename);
                }
            }
        }
    }

    Ok(())
}
```

**`my-prog/Cargo.toml`**

```toml
[package]
name    = "my-prog"
version = "0.1.0"
edition = "2021"

[dependencies]
aya           = { version = "0.12", features = ["async_tokio"] }
aya-log       = "0.2"
anyhow        = "1"
clap          = { version = "4", features = ["derive"] }
env_logger    = "0.11"
log           = "0.4"
tokio         = { version = "1", features = ["full"] }

[build-dependencies]
aya-build = "0.1"
```

**`my-prog-ebpf/Cargo.toml`**

```toml
[package]
name    = "my-prog-ebpf"
version = "0.1.0"
edition = "2021"

[dependencies]
aya-ebpf     = "0.1"
aya-log-ebpf = "0.1"

[profile.release]
opt-level     = 3
lto           = true
codegen-units = 1
```

---

### Example 2: XDP Packet Filter in Rust (Aya)

**Kernel-side: `xdp-filter-ebpf/src/main.rs`**

```rust
#![no_std]
#![no_main]

use aya_ebpf::{
    bindings::xdp_action,
    macros::{map, xdp},
    maps::HashMap,
    programs::XdpContext,
};
use core::mem;

// Ethernet header
#[repr(C)]
struct EthHdr {
    h_dest:   [u8; 6],
    h_source: [u8; 6],
    h_proto:  u16,
}

// IPv4 header
#[repr(C)]
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

const ETH_P_IP: u16 = 0x0800u16.to_be();
const ETH_HDR_LEN: usize = mem::size_of::<EthHdr>();
const IP_HDR_LEN:  usize = mem::size_of::<IpHdr>();

// Block list: u32 source IP → u8 dummy
#[map]
static BLOCKLIST: HashMap<u32, u8> = HashMap::with_max_entries(10_000, 0);

#[xdp]
pub fn xdp_firewall(ctx: XdpContext) -> u32 {
    match try_xdp_firewall(ctx) {
        Ok(ret) => ret,
        Err(_)  => xdp_action::XDP_ABORTED,
    }
}

#[inline(always)]
fn ptr_at<T>(ctx: &XdpContext, offset: usize) -> Result<*const T, ()> {
    let start = ctx.data();
    let end   = ctx.data_end();
    let len   = mem::size_of::<T>();

    if start + offset + len > end {
        return Err(());
    }
    Ok((start + offset) as *const T)
}

fn try_xdp_firewall(ctx: XdpContext) -> Result<u32, ()> {
    // Parse Ethernet header
    let eth: *const EthHdr = ptr_at(&ctx, 0)?;

    // Only handle IPv4
    if unsafe { (*eth).h_proto } != ETH_P_IP {
        return Ok(xdp_action::XDP_PASS);
    }

    // Parse IP header
    let ip: *const IpHdr = ptr_at(&ctx, ETH_HDR_LEN)?;
    let src_addr = unsafe { (*ip).saddr };

    // Check blocklist
    if unsafe { BLOCKLIST.get(&src_addr).is_some() } {
        return Ok(xdp_action::XDP_DROP);
    }

    Ok(xdp_action::XDP_PASS)
}

#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {
    unsafe { core::hint::unreachable_unchecked() }
}
```

**Userspace: `xdp-filter/src/main.rs`**

```rust
use anyhow::Context;
use aya::{
    maps::HashMap,
    programs::{Xdp, XdpFlags},
    Ebpf,
};
use clap::Parser;
use std::net::Ipv4Addr;
use tokio::signal;

#[derive(Debug, Parser)]
struct Opt {
    #[clap(short, long, default_value = "eth0")]
    iface: String,
    /// IP addresses to block (comma-separated)
    #[clap(short, long, value_delimiter = ',')]
    block: Vec<Ipv4Addr>,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let opt = Opt::parse();

    let mut ebpf = Ebpf::load(aya::include_bytes_aligned!(concat!(
        env!("OUT_DIR"),
        "/xdp-filter"
    )))?;

    let program: &mut Xdp = ebpf
        .program_mut("xdp_firewall")
        .unwrap()
        .try_into()?;

    program.load()?;
    program.attach(&opt.iface, XdpFlags::SKB_MODE)
        .context("failed to attach XDP program")?;

    // Populate the blocklist map
    let mut blocklist: HashMap<_, u32, u8> =
        HashMap::try_from(ebpf.map_mut("BLOCKLIST").unwrap())?;

    for ip in &opt.block {
        // XDP sees packets in network byte order
        let ip_u32 = u32::from(*ip).to_be();
        blocklist.insert(ip_u32, 1u8, 0)?;
        println!("Blocking {}", ip);
    }

    println!("XDP firewall running on {}. Ctrl-C to stop.", opt.iface);
    signal::ctrl_c().await?;

    Ok(())
}
```

**Building and Running**

```bash
# Build the eBPF program
cargo build --package xdp-filter-ebpf \
            --target bpfel-unknown-none \
            -Z build-std=core

# Build the userspace program
cargo build --package xdp-filter --release

# Run (requires root or CAP_BPF)
sudo ./target/release/xdp-filter --iface eth0 --block 192.168.1.100,10.0.0.1
```

---

## 15. Networking with eBPF

### The Full Linux Networking Stack with eBPF Hooks

```
     Physical NIC
          │
     (DMA to ring buffer)
          │
          ▼
     ┌─────────────────────────────────┐
     │  XDP Hook (native)              │← eBPF XDP: DROP/PASS/TX/REDIRECT
     │  (inside driver NAPI poll loop) │
     └─────────────────────────────────┘
          │ (XDP_PASS)
          ▼
     sk_buff allocated
          │
          ▼
     ┌─────────────────────────────────┐
     │  TC Ingress Hook                │← eBPF TC: modify/drop/redirect
     └─────────────────────────────────┘
          │
          ▼
     Netfilter PREROUTING
          │
          ▼
     IP Routing Decision
          │
     ┌────┴────┐
     │         │
  Local?    Forward?
     │         │
     ▼         ▼
  Netfilter  Netfilter
  INPUT      FORWARD
     │         │
     ▼         └──────────────────────┐
  Transport                           │
  Layer (TCP/UDP)                     │
     │                                ▼
  Socket                         Netfilter POSTROUTING
  Receive                             │
  Buffer                             ▼
     │                          TC Egress Hook ← eBPF TC
     ▼                               │
  Application                        ▼
                                   Physical NIC (TX)
```

### XDP Use Cases

#### 1. DDoS Mitigation

XDP programs can drop packets at **line rate** — for a 10 Gbps NIC, this is up to ~14.88 million 64-byte packets per second. Traditional netfilter rules cannot match this performance.

A typical DDoS mitigation pipeline:
1. Detect attack source IPs (via eBPF counters, anomaly detection)
2. Populate a BPF LRU hash map with attacker IPs
3. XDP program drops all packets from those IPs before sk_buff allocation

This is used in production by Cloudflare, Facebook, and others to absorb multi-Tbps attacks.

#### 2. Load Balancing (Katran/Cilium)

Facebook's **Katran** is an L4 load balancer built on XDP. It:
- Receives incoming TCP/UDP connections
- Looks up the destination backend in a BPF consistent hashing map
- Uses XDP_TX or XDP_REDIRECT to forward the packet to the chosen backend
- All of this happens before any packet enters the TCP stack

This replaces traditional LVS/IPVS load balancers with dramatically higher performance.

#### 3. Kubernetes Networking (Cilium)

**Cilium** replaces `kube-proxy` entirely with eBPF:
- Service IP → Pod IP NAT done in TC BPF programs
- Network policies enforced in TC/XDP layers
- Transparent encryption via eBPF + WireGuard
- Per-pod observability via BPF maps

### TC BPF: The Workhorse

While XDP is the fastest, TC BPF has access to full `sk_buff` metadata (socket cookies, cgroup IDs, etc.) and can both read and **write** packet contents. This makes it suitable for:

- NAT (Network Address Translation)
- Packet encapsulation/decapsulation (VXLAN, Geneve, WireGuard)
- QoS shaping
- Service mesh sidecar-less proxying

### Sockmap & Socket Redirection

For east-west traffic (pod-to-pod on the same host), eBPF sockmap enables **zero-copy kernel bypass**: data from one socket is redirected directly to another socket in the kernel, completely bypassing the network stack and even the NIC.

```
Application A writes to socket
     │
     ▼
sk_msg BPF program fires
     │
     ▼
bpf_msg_redirect_map() — redirect data to Application B's socket
     │
     ▼
Application B reads from socket
     (data never went to NIC, never traversed TCP stack twice)
```

---

## 16. Observability with eBPF

### The Observability Stack

eBPF has transformed Linux observability. It enables:
- **Zero-overhead tracing** (when probe doesn't fire, cost is zero)
- **Application-transparent profiling** (no instrumentation code in app)
- **Kernel and userspace correlation** (stack traces spanning both)
- **Dynamic, ad-hoc instrumentation** (attach/detach at runtime)

### Flame Graphs with eBPF

CPU profiling via `perf_event` attachment:

```c
SEC("perf_event")
int profile(struct bpf_perf_event_data *ctx)
{
    // Capture kernel + userspace stack
    __u64 id = bpf_get_current_pid_tgid();

    struct {
        __u64 pid;
        __u64 kernel_stack_id;
        __u64 user_stack_id;
    } key = {};

    key.pid = id >> 32;
    key.kernel_stack_id = bpf_get_stackid(ctx, &stack_traces,
                                          BPF_F_REUSE_STACKID);
    key.user_stack_id   = bpf_get_stackid(ctx, &stack_traces,
                                          BPF_F_REUSE_STACKID |
                                          BPF_F_USER_STACK);

    __u32 *count = bpf_map_lookup_elem(&counts, &key);
    if (count)
        __sync_fetch_and_add(count, 1);
    else {
        __u32 one = 1;
        bpf_map_update_elem(&counts, &key, &one, BPF_NOEXIST);
    }

    return 0;
}
```

This is the basis of **BPF-based CPU profilers** like `profile` in BCC and `bpftrace`'s `profile` probe.

### Network Latency Tracking

Track TCP round-trip time by probing `tcp_rcv_established` and correlating with socket operations:

```c
SEC("kprobe/tcp_sendmsg")
int trace_tcp_send(struct pt_regs *ctx)
{
    struct sock *sk = (struct sock *)PT_REGS_PARM1(ctx);
    __u64 ts = bpf_ktime_get_ns();
    bpf_map_update_elem(&send_timestamps, &sk, &ts, BPF_ANY);
    return 0;
}

SEC("kprobe/tcp_recvmsg")
int trace_tcp_recv(struct pt_regs *ctx)
{
    struct sock *sk = (struct sock *)PT_REGS_PARM1(ctx);
    __u64 *tsp = bpf_map_lookup_elem(&send_timestamps, &sk);
    if (tsp) {
        __u64 latency_ns = bpf_ktime_get_ns() - *tsp;
        // Store in histogram map
        __u32 slot = log2(latency_ns / 1000);  // microseconds, log2 bucket
        __u64 *count = bpf_map_lookup_elem(&latency_hist, &slot);
        if (count) __sync_fetch_and_add(count, 1);
        bpf_map_delete_elem(&send_timestamps, &sk);
    }
    return 0;
}
```

### bpftrace One-Liners for Observability

```bash
# File I/O latency histogram (microseconds)
bpftrace -e '
kprobe:vfs_read  { @start[tid] = nsecs; }
kretprobe:vfs_read /@start[tid]/ {
    @usecs = hist((nsecs - @start[tid]) / 1000);
    delete(@start[tid]);
}'

# Top 10 processes by syscall count
bpftrace -e 'tracepoint:raw_syscalls:sys_enter { @[comm] = count(); }
             END { print(@, 10); }'

# TCP retransmit reasons
bpftrace -e 'kprobe:tcp_retransmit_skb { @[kstack] = count(); }'

# Disk I/O latency by device
bpftrace -e '
tracepoint:block:block_rq_issue   { @start[args->dev, args->sector] = nsecs; }
tracepoint:block:block_rq_complete
/@start[args->dev, args->sector]/ {
    @ms[args->dev] = hist((nsecs - @start[args->dev, args->sector]) / 1e6);
    delete(@start[args->dev, args->sector]);
}'

# OOM killer invocations
bpftrace -e 'kprobe:oom_kill_process { printf("OOM kill: %s (pid %d)\n", comm, pid); }'
```

---

## 17. Security with eBPF

### seccomp-BPF: Syscall Filtering

**seccomp** (Secure Computing mode) uses BPF programs to filter system calls. Docker and container runtimes use this to restrict what syscalls containerized processes can make.

```c
// Classic BPF seccomp filter (cBPF syntax via libseccomp)
// This is generated by libseccomp from high-level rules

// Allow only read, write, exit, sigreturn, and exit_group
scmp_filter_ctx ctx = seccomp_init(SCMP_ACT_KILL);
seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(read),    0);
seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(write),   0);
seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(exit),    0);
seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(exit_group), 0);
seccomp_load(ctx);
```

The underlying BPF program inspects `seccomp_data.nr` (the syscall number) and returns:
- `SECCOMP_RET_ALLOW` — allow the syscall
- `SECCOMP_RET_KILL_PROCESS` — kill the entire process
- `SECCOMP_RET_ERRNO(n)` — return error `n` to the caller
- `SECCOMP_RET_TRACE` — notify a ptrace tracer (used for container monitors)

### LSM BPF: Policy Enforcement

LSM BPF (kernel 5.7+) allows building custom MAC (Mandatory Access Control) policies entirely in eBPF, without patching the kernel or writing a kernel module. This supersedes complex SELinux policies for custom runtime security needs.

Example: Block execution of unsigned binaries

```c
SEC("lsm/bprm_check_security")
int BPF_PROG(check_exec, struct linux_binprm *bprm)
{
    struct file *file = BPF_CORE_READ(bprm, file);
    struct inode *inode = BPF_CORE_READ(file, f_inode);
    __u64 ino = BPF_CORE_READ(inode, i_ino);
    __u32 dev = BPF_CORE_READ(inode, i_sb, s_dev);

    // Check if this inode is in our "trusted" set
    struct dev_ino key = { .dev = dev, .ino = ino };
    if (!bpf_map_lookup_elem(&trusted_binaries, &key)) {
        // Log the attempt
        struct exec_event *e = bpf_ringbuf_reserve(&rb, sizeof(*e), 0);
        if (e) {
            e->pid = bpf_get_current_pid_tgid() >> 32;
            bpf_get_current_comm(&e->comm, sizeof(e->comm));
            bpf_ringbuf_submit(e, 0);
        }
        return -EPERM;  // Deny execution
    }
    return 0;  // Allow
}
```

### Falco (CNCF) — eBPF-based Runtime Security

Falco is a CNCF project that uses eBPF probes to detect anomalous behavior at runtime:
- Unexpected file access patterns
- Shell spawned inside a container
- Unexpected network connections
- Privilege escalation attempts

It uses BCC or its own kernel module/eBPF driver, evaluating a rule engine against events streamed via ring buffers.

### Network Security

eBPF enables network security enforcement at the lowest possible layer:

```c
// Rate limiting: drop if more than N packets/sec from a source IP
SEC("xdp")
int rate_limit(struct xdp_md *ctx)
{
    // Parse src IP (omitted for brevity)
    __u32 src_ip = /* ... */;

    struct rate_entry {
        __u64 last_ns;
        __u32 count;
    };

    struct rate_entry *entry = bpf_map_lookup_elem(&rate_map, &src_ip);
    __u64 now = bpf_ktime_get_ns();

    if (entry) {
        // Reset counter every second
        if (now - entry->last_ns > 1000000000ULL) {
            entry->count   = 1;
            entry->last_ns = now;
        } else {
            entry->count++;
            if (entry->count > 10000)  // 10k pps limit
                return XDP_DROP;
        }
    } else {
        struct rate_entry new_entry = { .last_ns = now, .count = 1 };
        bpf_map_update_elem(&rate_map, &src_ip, &new_entry, BPF_NOEXIST);
    }

    return XDP_PASS;
}
```

---

## 18. eBPF in the Linux Kernel Source

### Key Source Files

For those reading the Linux kernel source (https://github.com/torvalds/linux):

```
kernel/bpf/
├── core.c              # BPF interpreter, eBPF → native execution
├── verifier.c          # The verifier (12,000+ lines)
├── syscall.c           # bpf() syscall implementation
├── helpers.c           # Generic helper functions
├── hashtab.c           # Hash map implementation
├── arraymap.c          # Array map implementation
├── ringbuf.c           # Ring buffer implementation
├── trampoline.c        # fentry/fexit trampoline mechanism
├── btf.c               # BTF type parsing and management
├── bpf_lsm.c           # LSM BPF infrastructure
├── cgroup.c            # cgroup BPF programs
└── cpumap.c            # XDP CPU map

arch/x86/net/bpf_jit_comp.c        # x86-64 JIT compiler
arch/arm64/net/bpf_jit_comp.c      # ARM64 JIT compiler
net/core/filter.c                   # sk_filter, XDP, TC infrastructure
net/sched/cls_bpf.c                 # TC BPF classifier
drivers/net/ethernet/*/             # Native XDP in drivers
include/linux/bpf.h                 # Core BPF data structures
include/linux/bpf_types.h           # Program type definitions
include/uapi/linux/bpf.h            # User-facing BPF API (maps, helpers)
```

### How BPF_PROG_LOAD Works (kernel/bpf/syscall.c)

When you call `bpf(BPF_PROG_LOAD, ...)`, the kernel:

```
1. bpf_prog_load()
   ├── bpf_prog_alloc()          — allocate struct bpf_prog
   ├── copy_from_user()           — copy eBPF bytecode from userspace
   ├── bpf_check()                — RUN THE VERIFIER
   │    ├── check_cfg()           — build and validate CFG
   │    ├── do_check_main()       — abstract interpretation
   │    │    ├── check_mem_access()  — bounds check every load/store
   │    │    ├── check_helper_call() — validate helper args
   │    │    └── check_func_call()   — handle BPF-to-BPF calls
   │    └── resolve_pseudo_ldimm64() — fix up map FD references
   ├── bpf_prog_select_runtime()  — JIT compile or select interpreter
   │    └── bpf_int_jit_compile()  — arch-specific JIT
   ├── bpf_prog_kallsyms_add()    — register in /proc/kallsyms
   └── return fd                  — file descriptor for the program
```

### The `struct bpf_prog` Type

This is the kernel's representation of a loaded eBPF program:

```c
struct bpf_prog {
    u16                  pages;         // Number of pages
    u16                  jited:1,       // Is JIT-compiled?
                         jit_requested:1,
                         undo_set_mem:1,
                         gpl_compatible:1, // GPL license?
                         cb_access:1,
                         dst_needed:1,
                         blinding_requested:1,
                         blinding_done:1,
                         seq_num:1,
                         ...;

    enum bpf_prog_type   type;          // XDP, KPROBE, SOCKET_FILTER, etc.
    enum bpf_attach_type expected_attach_type;

    u32                  len;           // Number of instructions
    u32                  jited_len;     // JIT output size

    u8                   tag[BPF_TAG_SIZE]; // SHA-1 tag for dedup
    struct bpf_prog_aux *aux;           // Auxiliary info (maps, BTF, etc.)
    struct sock_fprog_kern *orig_prog;  // cBPF original (if translated)

    unsigned int         (*bpf_func)(const void *ctx,
                                     const struct bpf_insn *insn);
    // ^ This is the JIT-compiled function pointer (or interpreter entry)

    union {
        struct sock_filter    insns[0]; // cBPF instructions
        struct bpf_insn       insnsi[0]; // eBPF instructions
    };
};
```

### Kernel Configuration for eBPF

```bash
# Check your kernel's eBPF configuration
zcat /proc/config.gz | grep -i BPF

# Key config options
CONFIG_BPF=y                    # BPF syscall
CONFIG_BPF_SYSCALL=y            # BPF programs via syscall
CONFIG_BPF_JIT=y                # JIT compiler
CONFIG_BPF_JIT_ALWAYS_ON=y      # Always use JIT (security)
CONFIG_BPF_EVENTS=y             # Perf events
CONFIG_BPF_LSM=y                # LSM BPF hooks
CONFIG_DEBUG_INFO_BTF=y         # BTF in kernel image
CONFIG_DEBUG_INFO_BTF_MODULES=y # BTF for kernel modules
CONFIG_XDP_SOCKETS=y            # AF_XDP sockets
CONFIG_NET_CLS_BPF=y            # TC BPF classifier
CONFIG_NET_ACT_BPF=y            # TC BPF actions
CONFIG_CGROUP_BPF=y             # cgroup BPF programs
```

---

## 19. Performance Considerations

### Overhead Model

The overhead of an eBPF program consists of:

1. **Hook overhead**: The cost of entering the eBPF execution context from the hook point
   - fentry/fexit: ~5–10 ns (trampoline-based)
   - kprobe/kretprobe: ~100–300 ns (int3 trap + handler)
   - tracepoint: ~20–50 ns (static call site)
   - XDP: essentially zero (already in hot path)

2. **JIT-compiled instruction overhead**: After JIT, ~1 ns/instruction (native speed)

3. **Map access overhead**:
   - Array (integer key): ~10–30 ns (pointer arithmetic + dereference)
   - Hash map: ~50–100 ns (hash function + linked list traversal)
   - Per-CPU map: eliminates lock overhead for concurrent access

4. **Helper function overhead**: Varies by helper (10–1000 ns)
   - `bpf_get_current_pid_tgid()`: ~10 ns (read current task)
   - `bpf_probe_read_kernel()`: ~100 ns (safe memory read)
   - `bpf_perf_event_output()`: ~200–500 ns (ring buffer write)

### Per-CPU Maps for High-Frequency Counters

For event counters updated on every packet (millions/sec), per-CPU maps are critical:

```c
// WRONG: Hash map with atomic (slow)
__sync_fetch_and_add(count, 1);  // Cache line bouncing

// RIGHT: Per-CPU array (fast, no contention)
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, __u64);
} pkt_count SEC(".maps");

// In eBPF program:
__u32 key = 0;
__u64 *cnt = bpf_map_lookup_elem(&pkt_count, &key);
if (cnt) (*cnt)++;  // No atomic needed! Only this CPU touches this entry.
```

### Tail Calls for Complex Logic

The maximum stack depth for eBPF is 512 bytes, and BPF-to-BPF function calls share this stack. For complex logic that exceeds stack limits, tail calls allow chaining programs:

```c
// Program array for tail calls
struct {
    __uint(type, BPF_MAP_TYPE_PROG_ARRAY);
    __uint(max_entries, 10);
    __type(key, __u32);
    __type(value, __u32);
} prog_array SEC(".maps");

SEC("xdp")
int stage_1(struct xdp_md *ctx)
{
    // Parse headers...

    // Chain to stage 2 (does not return)
    bpf_tail_call(ctx, &prog_array, 1);

    // Reached only if tail call fails (e.g., index out of range)
    return XDP_PASS;
}
```

### Ringbuf vs Perf_Event_Array

For high-volume event streaming to userspace:

| | `PERF_EVENT_ARRAY` | `RINGBUF` |
|---|---|---|
| Memory | N buffers (1 per CPU) | 1 shared buffer |
| Ordering | Per-CPU FIFO (no global order) | Total order |
| Overhead | Per-CPU, no coordination | Single shared buffer |
| Wakeup | Per-CPU | Shared fd |
| Recommended | Legacy | New code (5.8+) |

---

## 20. Production Patterns & Best Practices

### 1. Always Validate Pointer Arithmetic

The verifier requires explicit bounds checks. Always follow the pattern:

```c
// For packet data:
void *data     = (void *)(long)ctx->data;
void *data_end = (void *)(long)ctx->data_end;
struct ethhdr *eth = data;

if ((void *)(eth + 1) > data_end)
    return XDP_DROP;  // Not enough data for an Ethernet header

// For map values:
struct my_val *v = bpf_map_lookup_elem(&my_map, &key);
if (!v)
    return 0;  // ALWAYS check for NULL
// Now v is safe to dereference
```

### 2. Use `bpf_loop()` for Bounded Iteration (kernel 5.17+)

```c
// Instead of manually unrolled loops, use bpf_loop:
static long count_cb(u32 index, void *ctx)
{
    // callback body
    return 0;  // 0 = continue, 1 = stop
}

bpf_loop(1000, count_cb, NULL, 0);
```

### 3. Prefer fentry/fexit Over kprobes

```c
// Prefer this (stable, low overhead, type-safe):
SEC("fentry/tcp_sendmsg")
int BPF_PROG(fentry_tcp_sendmsg, struct sock *sk,
             struct msghdr *msg, size_t size) { ... }

// Over this (unstable ABI, higher overhead):
SEC("kprobe/tcp_sendmsg")
int kprobe_tcp_sendmsg(struct pt_regs *ctx) {
    struct sock *sk = (struct sock *)PT_REGS_PARM1(ctx);
    ...
}
```

### 4. Pin Programs and Maps for Persistence

```c
// In userspace (C)
bpf_obj_pin(prog_fd, "/sys/fs/bpf/my_prog");
bpf_obj_pin(map_fd,  "/sys/fs/bpf/my_map");

// Use BPF links instead of direct attachment for cleaner lifecycle:
struct bpf_link *link = bpf_program__attach(prog);
bpf_link__pin(link, "/sys/fs/bpf/my_link");
```

### 5. Handle Kernel Version Differences with CO-RE

```c
// Use BPF_CORE_READ_BITFIELD_PROBED for bitfields
BPF_CORE_READ_BITFIELD_PROBED(task, flags);

// Use feature detection for conditional behavior
#if defined(BPF_FEAT_AVAILABLE)
// Use new kernel feature
#else
// Fallback
#endif
```

### 6. Error Handling in eBPF Programs

```c
// Never silently ignore errors
struct event *e = bpf_ringbuf_reserve(&rb, sizeof(*e), 0);
if (!e) {
    // Increment a "dropped events" counter
    __u32 key = 0;
    __u64 *drops = bpf_map_lookup_elem(&dropped_events, &key);
    if (drops) __sync_fetch_and_add(drops, 1);
    return 0;
}
```

### 7. Use BPF Skeleton for Clean Lifecycle Management

The skeleton API (generated by `bpftool gen skeleton`) wraps the entire open/load/attach/destroy lifecycle:

```c
struct my_prog_bpf *skel = NULL;

skel = my_prog_bpf__open();          // Open (parse .o file)
if (!skel) return -errno;

skel->rodata->my_pid = getpid();     // Set read-only data before load

err = my_prog_bpf__load(skel);       // Load+verify programs, create maps
if (err) goto cleanup;

err = my_prog_bpf__attach(skel);     // Attach all programs
if (err) goto cleanup;

// ... run event loop ...

cleanup:
    my_prog_bpf__destroy(skel);      // Detach, close fds, free memory
```

---

## 21. Limitations & Gotchas

### 1. No Dynamic Memory Allocation

eBPF programs cannot call `kmalloc()` or any dynamic allocator. All memory comes from:
- The 512-byte stack
- BPF maps (pre-allocated at load time)
- Ring buffer reservations (which are pre-allocated in the ring buffer)

### 2. No Sleeping

Most eBPF programs run in atomic context and **cannot sleep or block**. This means no mutexes, no semaphores, no memory allocation. Map operations use spinlocks internally but are non-blocking from the eBPF program's perspective.

Exception: `BPF_PROG_TYPE_SLEEPABLE` (kernel 5.10+) allows certain programs (LSM, fentry/fexit on certain functions) to call sleepable helpers like `bpf_copy_from_user()`.

### 3. Limited Stack

512 bytes of stack is easily exhausted when dealing with large structs. Use maps to store large data:

```c
// WRONG: Large struct on stack
struct big_struct data;  // If this is > ~400 bytes, verifier may reject

// RIGHT: Use a per-CPU array map as stack extension
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, struct big_struct);
} scratch SEC(".maps");

__u32 key = 0;
struct big_struct *data = bpf_map_lookup_elem(&scratch, &key);
if (!data) return 0;
// Use data freely
```

### 4. No Global Variables (Read/Write)

eBPF programs cannot have mutable global variables in the traditional C sense. What appear to be global variables are either:
- **Read-only `rodata`**: Initialized once, never written by the eBPF program
- **BPF maps**: The correct way to store per-program state

### 5. Verifier False Negatives

The verifier is conservative. Correct programs may be rejected if the verifier cannot prove their safety. This happens with:
- Complex conditional logic
- Programs that are too large (verifier state explosion)
- Pointer arithmetic patterns the verifier doesn't recognize

Solution: Simplify the logic, add explicit bounds checks, or restructure using `bpf_loop()`.

### 6. kprobe Fragility

kprobes depend on stable function names and calling conventions. A kernel update can:
- Rename a function
- Inline a function (making kprobe impossible)
- Change argument types

Always prefer tracepoints (stable ABI) or fentry/fexit (BTF-typed) over kprobes in production.

### 7. Privilege Requirements

Most eBPF program types require:
- Linux kernel ≥ 5.8: `CAP_BPF` + `CAP_PERFMON` for tracing, `CAP_NET_ADMIN` for networking
- Older kernels: `CAP_SYS_ADMIN`

Unprivileged eBPF (socket filters only) requires `kernel.unprivileged_bpf_disabled=0`, which is disabled on many distributions for security.

---

## 22. The eBPF Ecosystem: Tools and Projects

### Observability

| Tool | Description |
|---|---|
| **BCC** | BPF Compiler Collection: Python scripts for system tracing |
| **bpftrace** | High-level tracing language for ad-hoc queries |
| **BCC Tools** | 100+ pre-built tools: `tcptop`, `execsnoop`, `opensnoop`, `biolatency`, etc. |
| **Pixie** | Kubernetes observability without instrumentation |
| **Parca** | Continuous profiling using eBPF |
| **Coroot** | eBPF-based infrastructure monitoring |
| **Hubble** | Network observability built on Cilium |
| **Retina** | Microsoft's eBPF-based network observability for Kubernetes |

### Networking

| Tool | Description |
|---|---|
| **Cilium** | Kubernetes CNI plugin, fully eBPF-based networking and security |
| **Katran** | Facebook's L4 load balancer |
| **bpfilter** | eBPF-based iptables replacement |
| **tc-bpf** | Linux tc framework with BPF classifier |
| **AF_XDP** | Kernel bypass socket using XDP redirect |
| **Calico eBPF** | eBPF dataplane for Calico CNI |

### Security

| Tool | Description |
|---|---|
| **Falco** | CNCF runtime security using eBPF |
| **Tetragon** | eBPF-based security observability and enforcement (Isovalent/Cilium) |
| **KubeArmor** | eBPF-based runtime security for containers |
| **seccomp-bpf** | Syscall filtering for containers (used by Docker, systemd) |

### Development Tools

| Tool | Description |
|---|---|
| **libbpf** | Official C library for loading eBPF programs |
| **Aya** | Pure Rust eBPF framework |
| **ebpf-go** | Go eBPF library (used by Cilium) |
| **bpftool** | Swiss-army knife: inspect programs, maps, BTF, generate skeletons |
| **llvm/clang** | The only compiler with a BPF backend |
| **libbpf-bootstrap** | Template project for libbpf-based eBPF programs |

### Inspecting with `bpftool`

```bash
# List all loaded eBPF programs
bpftool prog list

# Dump eBPF bytecode of a program
bpftool prog dump xlated id 42

# Dump JIT-compiled machine code
bpftool prog dump jited id 42

# List all eBPF maps
bpftool map list

# Dump contents of a map
bpftool map dump id 7

# List all eBPF links (attachments)
bpftool link list

# Show BTF types
bpftool btf show

# Generate a vmlinux.h
bpftool btf dump file /sys/kernel/btf/vmlinux format c > vmlinux.h

# Generate a BPF skeleton
bpftool gen skeleton my_prog.bpf.o > my_prog.skel.h

# Profile a command with eBPF
bpftool prog profile id 42 duration 5 cycles instructions
```

---

## Summary

eBPF is a revolutionary technology that transforms the Linux kernel into a **programmable, event-driven platform**. To summarize the key points:

1. **eBPF does not replace the kernel** — it hooks into it at well-defined points, running alongside normal kernel execution, not instead of it.

2. **The verifier is the cornerstone** — it mathematically proves program safety before any execution, making eBPF safe for production use without kernel module risk.

3. **JIT compilation delivers native performance** — once loaded and JIT-compiled, eBPF programs run as fast as hand-written kernel code.

4. **BTF + CO-RE solves portability** — programs compiled once work across different kernel versions by patching field offsets at load time.

5. **Maps are the universal data layer** — they bridge kernel-side eBPF programs and userspace processes, and provide persistent state storage.

6. **Program types define capability** — from read-only tracing (kprobes, tracepoints) to full packet processing (XDP, TC) to security enforcement (LSM), each type has precise semantics.

7. **The ecosystem is mature and production-proven** — Cloudflare, Meta, Google, Netflix, and the entire cloud-native Kubernetes ecosystem run eBPF in production at scale.

eBPF represents the next evolution of the Linux kernel itself — a platform that can be extended at runtime, safely, efficiently, and portably, without touching kernel source code.

---

*Document covers Linux kernel 5.x–6.x, libbpf 1.x, Aya 0.12.x.*
*All C examples target the libbpf/CO-RE programming model.*
*All Rust examples target the Aya framework.*

Now let me write the comprehensive eBPF guide directly.Here's your full guide. Let me also directly address your original question first:

---

**Your understanding was close but had an important inaccuracy.** eBPF does not make the kernel "obey" it or override normal behavior. The correct model is:

- **eBPF programs are hooks, not replacements.** They attach to specific kernel events (a packet arriving, a syscall being called, a function executing) and run *alongside* the normal kernel path.
- **Most eBPF programs are pure observers** — they read data, populate maps, emit events to userspace, but the kernel continues doing exactly what it always did.
- **Only specific program types can influence behavior** — XDP can drop/redirect packets, LSM hooks can deny operations, cgroup hooks can intercept socket calls. Even then, they do so via defined return codes, not by "commanding" the kernel.
- **The verifier guarantees safety** — before any eBPF program ever runs, the kernel statically proves it cannot crash, loop forever, or access illegal memory. This is what makes it fundamentally different from a kernel module.

---

The guide covers all 22 major topics including:

- **The full mental model correction** with precise execution flow diagrams
- **History from cBPF (1992) to eBPF (2014+)** with every major kernel milestone
- **The Verifier in depth** — abstract interpretation, how it tracks pointer types and value ranges, why it rejects certain programs
- **All 10+ program types** — XDP, TC, kprobes, fentry/fexit, tracepoints, LSM, cgroup, sockmap, and more
- **All map types** — including the new `RINGBUF`, per-CPU maps, bloom filters, struct_ops
- **Complete C examples** with libbpf + CO-RE: execve tracer, XDP packet counter with per-CPU maps, LSM file audit
- **Complete Rust examples** with Aya: execve tracer, XDP firewall with blocklist
- **BTF and CO-RE** explained in full — how compile-once-run-everywhere actually works mechanically
- **Linux kernel internals** — key source files, how `BPF_PROG_LOAD` works step by step, `struct bpf_prog` layout
- **Production patterns, performance model, and all major gotchas**