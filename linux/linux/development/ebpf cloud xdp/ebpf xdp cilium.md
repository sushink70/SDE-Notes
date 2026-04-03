# Complete Guide & Roadmap: eBPF, XDP, and Cilium
> From kernel internals to cloud-native networking — a first-principles, in-depth reference.
> Languages: C, Go, Rust (Aya)

---

## Table of Contents

1. [The Mental Model — Why This Stack Exists](#1-the-mental-model)
2. [Prerequisites — What You Must Know First](#2-prerequisites)
3. [eBPF — Complete Deep Dive](#3-ebpf-complete-deep-dive)
   - 3.1 What is eBPF
   - 3.2 The BPF Virtual Machine
   - 3.3 BPF Instruction Set Architecture
   - 3.4 The Verifier
   - 3.5 JIT Compiler
   - 3.6 BPF Maps — The Memory System
   - 3.7 Helper Functions
   - 3.8 Program Types
   - 3.9 BTF — BPF Type Format
   - 3.10 CO-RE — Compile Once Run Everywhere
   - 3.11 libbpf
   - 3.12 The bpf() Syscall
   - 3.13 BPF Object Lifecycle & Pinning
4. [XDP — eXpress Data Path](#4-xdp-express-data-path)
   - 4.1 What is XDP and Why It Exists
   - 4.2 XDP Execution Model
   - 4.3 XDP Modes
   - 4.4 XDP Return Codes (Actions)
   - 4.5 XDP Programming — C
   - 4.6 XDP Maps in Practice
   - 4.7 AF_XDP — Zero Copy to Userspace
   - 4.8 XDP vs DPDK
5. [Cilium — Complete Deep Dive](#5-cilium-complete-deep-dive)
   - 5.1 What is Cilium
   - 5.2 Architecture Overview
   - 5.3 Cilium Agent
   - 5.4 Cilium Datapath — eBPF in Action
   - 5.5 CNI Integration
   - 5.6 Identity-Based Security Model
   - 5.7 Network Policy
   - 5.8 Load Balancing with eBPF
   - 5.9 Hubble — Observability Layer
   - 5.10 ClusterMesh
   - 5.11 WireGuard Integration
6. [Aya — Rust eBPF Framework](#6-aya-rust-ebpf-framework)
   - 6.1 Why Aya
   - 6.2 Architecture
   - 6.3 Writing an XDP Program in Rust/Aya
   - 6.4 Maps in Aya
   - 6.5 TC Programs in Aya
7. [Go eBPF — cilium/ebpf library](#7-go-ebpf)
8. [The Complete Roadmap](#8-complete-roadmap)
9. [Real Projects to Build](#9-real-projects-to-build)
10. [Reference: Key Kernel Source Paths](#10-reference)

---

## 1. The Mental Model

Before writing a single line, understand **why this entire stack exists**.

### The Core Problem

The Linux networking stack was designed in the 1990s. It is general-purpose, correct, and safe — but it has a fundamental cost: **every packet traverses a long path through kernel space**.

```
NIC receives packet
        |
        v
[Hardware Interrupt]
        |
        v
[Driver Ring Buffer]
        |
        v
[sk_buff allocation]          <-- memory allocation per packet
        |
        v
[netif_receive_skb]
        |
        v
[Protocol Stack: L2 → L3 → L4]  <-- many function calls, cache misses
        |
        v
[Socket Buffer]
        |
        v
[Userspace application]        <-- context switch (kernel → user)
```

At 10 Gbps, a server receives ~14.8 million 64-byte packets per second. The traditional path cannot keep up at high packet rates because:

- Each `sk_buff` allocation is ~240 bytes of metadata overhead
- Multiple memory copies
- Context switches between kernel and userspace
- Cache thrashing across many subsystems

### The Solution Spectrum

```
Problem: Need to process/filter/redirect packets FAST

Solution A: Userspace networking (DPDK)
  → Bypass kernel entirely
  → Poll the NIC from userspace
  → Zero kernel involvement
  + Extremely fast
  - Application owns the NIC (no other process can use it)
  - Must reimplement TCP/IP stack in userspace
  - Loses all kernel network features

Solution B: eBPF + XDP
  → Run custom code INSIDE the kernel, at the earliest hook point
  → Kernel verifies your code for safety before running it
  → You still have full kernel network stack available
  + Fast (near-DPDK speeds for filter/redirect workloads)
  + Safe (verifier guarantees no crashes, no infinite loops)
  + Programmable (change behavior without kernel patches or reboots)
  + Composable (still uses kernel's TCP/IP, routing, etc.)
  - Restricted instruction set (no unbounded loops, limited stack)
```

eBPF is the programmability layer. XDP is the hook point. Cilium is the orchestration system that uses both to implement Kubernetes networking at scale.

---

## 2. Prerequisites

These are non-negotiable. You must understand these before eBPF makes sense.

### 2.1 Linux Networking Fundamentals

**What is sk_buff?**

`sk_buff` (socket buffer) is the kernel's universal packet representation. Every packet in the Linux network stack is wrapped in one. It is defined in `include/linux/skbuff.h` and contains:

```c
struct sk_buff {
    /* packet boundaries */
    unsigned char    *head;    // start of allocated buffer
    unsigned char    *data;    // start of actual packet data
    unsigned char    *tail;    // end of packet data
    unsigned char    *end;     // end of allocated buffer

    /* metadata */
    __u32            len;      // total packet length
    __u16            protocol; // L3 protocol (ETH_P_IP, ETH_P_IPV6, etc.)
    __u8             pkt_type; // PACKET_HOST, PACKET_BROADCAST, etc.

    /* network layer pointers */
    struct iphdr     *nh;      // network header
    struct tcphdr    *th;      // transport header

    /* ... 200+ more fields */
};
```

**The Network Stack Layers:**

```
Layer       Data Unit    Kernel Structure       Header
L2 (Link)   Frame        sk_buff               struct ethhdr
L3 (Net)    Packet       sk_buff               struct iphdr / ipv6hdr
L4 (Trans)  Segment      sk_buff               struct tcphdr / udphdr
L7 (App)    Message      user buffer           application-defined
```

**Key network hook points (Netfilter):**

```
[NIC] --> PREROUTING --> [routing decision] --> FORWARD --> POSTROUTING --> [NIC]
                                   |
                                   v
                                 INPUT
                                   |
                                   v
                              [local process]
                                   |
                                   v
                                 OUTPUT
```

eBPF programs can attach to many of these hook points, and XDP runs even BEFORE PREROUTING.

### 2.2 What is a System Call

A **syscall** is the only legal way for a userspace program to ask the kernel to do something. When you call `open()`, `read()`, `write()` — these are wrappers around syscalls.

The `bpf()` syscall (number 321 on x86_64) is the single entry point for ALL eBPF operations: loading programs, creating maps, attaching programs, querying info.

```
Userspace                        Kernel
---------                        ------
bpf(BPF_PROG_LOAD, ...)  ---->  sys_bpf()
                                    |
                                    +--> verifier (checks safety)
                                    +--> JIT compiler (compiles to native)
                                    +--> returns file descriptor
```

### 2.3 File Descriptors and Reference Counting

In Linux, almost everything is a file descriptor (fd). eBPF programs and maps are kernel objects referenced by fds. When all fds to an object are closed, the object is garbage collected — unless it is **pinned** to the BPF filesystem.

### 2.4 Kernel Data Structures You Must Know

- **RCU (Read-Copy-Update):** Lock-free synchronization used in BPF maps for concurrent access
- **percpu variables:** Variables with one copy per CPU core — avoid cache coherency traffic between cores
- **kprobes/tracepoints:** Dynamic instrumentation hooks the kernel exports for eBPF to attach to
- **cgroups:** Control groups — used for BPF program attachment to process groups
- **netns (network namespaces):** Isolated network stacks — fundamental to container networking

---

## 3. eBPF — Complete Deep Dive

### 3.1 What is eBPF

**eBPF** stands for **extended Berkeley Packet Filter**.

The original BPF (1992, McCanne & Jacobson) was a minimal packet filter — a small register-based VM that let you write packet filter expressions (like tcpdump filters) that run inside the kernel.

Linux extended it (eBPF, ~2014, Alexei Starovoitov) into a general-purpose in-kernel execution engine with:

- 11 registers (vs 2 in classic BPF)
- 512-byte stack
- Access to kernel helper functions
- Persistent storage (Maps)
- Multiple program types beyond packet filtering
- A safety verifier
- JIT compilation to native machine code

**The fundamental contract of eBPF:**

```
YOU write a program.
The KERNEL verifier checks it for safety.
If safe, the JIT compiler turns it into native machine code.
The kernel runs your code at a hook point — inside the kernel — without a context switch.
Your code is as fast as kernel code.
Your code cannot crash the kernel (verifier guarantees this).
```

This is revolutionary. Before eBPF, to add new behavior to the kernel you had to:
1. Write a kernel module (dangerous — one bug = kernel panic)
2. Patch the kernel source and recompile (slow, requires reboot)
3. Process packets in userspace (slow, requires copy)

eBPF is none of these. It is **safe, dynamic, in-kernel programmability**.

### 3.2 The BPF Virtual Machine

The BPF VM has a specific, fixed architecture:

**Registers:**

```
Register   Role                          Notes
--------   ----                          -----
r0         Return value                  Function return value / program exit code
r1         Argument 1                    First argument to helper functions
r2         Argument 2                    Second argument
r3         Argument 3                    Third argument
r4         Argument 4                    Fourth argument
r5         Argument 5                    Fifth argument
r6-r9      Callee-saved                  Preserved across helper calls
r10        Frame pointer (read-only)     Points to top of 512-byte stack
```

**Stack:**

Every BPF program gets exactly 512 bytes of stack. This is fixed and enforced by the verifier. No dynamic allocation. No recursion.

```
r10 (frame pointer)
 |
 v
[    512 bytes of stack    ]
 ^
 |
 stack grows downward (r10 - 8, r10 - 16, etc.)
```

**The Context Pointer:**

When the kernel calls your BPF program, it passes a **context pointer** in `r1`. The type of this pointer depends on the program type:

```
Program Type          Context Type
XDP                   struct xdp_md *
TC (traffic control)  struct __sk_buff *
kprobe                struct pt_regs *
tracepoint            varies per tracepoint
socket filter         struct __sk_buff *
cgroup/skb            struct __sk_buff *
```

This is your only window into the world. Everything you know about the packet (or kernel event) comes through this pointer.

### 3.3 BPF Instruction Set Architecture

BPF has its own ISA (Instruction Set Architecture) — a fixed-width 64-bit encoding.

Each instruction is exactly **8 bytes**:

```
Bits 63-32: immediate value (imm, 32-bit signed)
Bits 31-28: offset (16-bit signed, for memory ops)  
Bits 27-24: source register (src_reg, 4 bits)
Bits 23-20: destination register (dst_reg, 4 bits)
Bits 19-16: reserved
Bits  15-8: opcode class + instruction-specific bits
Bits   7-0: opcode
```

**Instruction classes:**

```
BPF_LD    (0x00)  load from memory
BPF_LDX   (0x01)  load from register + offset
BPF_ST    (0x02)  store immediate to memory
BPF_STX   (0x03)  store register to memory
BPF_ALU   (0x04)  32-bit arithmetic
BPF_JMP   (0x05)  jump (conditional and unconditional)
BPF_JMP32 (0x06)  32-bit jump
BPF_ALU64 (0x07)  64-bit arithmetic
```

**Example — minimal XDP program in BPF assembly:**

```asm
; This drops every packet (returns XDP_DROP = 1)
; Equivalent C: return XDP_DROP;

mov64 r0, 1    ; r0 = XDP_DROP (return value)
exit           ; end program, return r0
```

You never write BPF assembly manually. You write C (or Rust), compile with Clang to BPF bytecode, and the loader feeds bytecode to the kernel.

### 3.4 The Verifier

The verifier is the most important component of eBPF. It is what makes eBPF **safe** despite running in kernel space.

**Location in kernel:** `kernel/bpf/verifier.c` (~20,000 lines)

**What the verifier checks:**

```
CONTROL FLOW CHECKS:
  - Program must terminate (no infinite loops*)
  - No unreachable instructions
  - All branches must converge to a single exit
  - No backward jumps (unless bounded loop with known iteration count)

  * Since Linux 5.3: bounded loops ARE allowed if the verifier can prove
    they terminate within a bounded number of iterations

MEMORY SAFETY CHECKS:
  - No out-of-bounds stack access
  - No out-of-bounds map value access
  - Pointer arithmetic is tracked — you cannot create an invalid pointer
  - NULL pointer dereferences are caught before they happen

TYPE SAFETY CHECKS:
  - Every register has a tracked type at every instruction
  - You cannot use a packet pointer after the packet was modified
  - You cannot pass a pointer to the wrong helper function

PRIVILEGE CHECKS:
  - Certain program types require CAP_BPF or CAP_NET_ADMIN
  - Unprivileged BPF is restricted to socket filters
```

**How the verifier works (abstract algorithm):**

The verifier does a **symbolic execution** of your program. It tracks the state of every register and stack slot at every instruction, considering all possible paths through the program.

```
State = {
  r0: type=UNKNOWN, value=0
  r1: type=PTR_TO_CTX  (set by kernel before calling your program)
  r2: type=UNKNOWN
  ...
  r10: type=FRAME_PTR
  stack: all zeros
}

For each instruction in topological order:
  1. Check if current state is valid
  2. Update state based on instruction semantics
  3. If branch: fork state, follow both paths
  4. At join points: merge states (take pessimistic view)
  5. If state was already seen: prune (avoid re-checking)
```

**The verifier's type system:**

```
NOT_INIT          = register not yet written (reading = error)
SCALAR_VALUE      = integer, arithmetic allowed
PTR_TO_CTX        = pointer to program context (xdp_md, sk_buff, etc.)
PTR_TO_MAP_KEY    = pointer to map key buffer
PTR_TO_MAP_VALUE  = pointer to map value (may be NULL — must check!)
PTR_TO_STACK      = pointer into BPF stack
PTR_TO_PACKET     = pointer into packet data
PTR_TO_PACKET_END = pointer to end of packet data
```

**Why NULL checks are mandatory:**

```c
// This will be REJECTED by the verifier:
int *val = bpf_map_lookup_elem(&my_map, &key);
*val = 42;  // ERROR: val might be NULL, verifier rejects this

// This is ACCEPTED:
int *val = bpf_map_lookup_elem(&my_map, &key);
if (val == NULL)
    return XDP_DROP;
*val = 42;  // OK: verifier knows val is not NULL here
```

After the NULL check, the verifier tracks that `val` has type `PTR_TO_MAP_VALUE` (non-null), and allows the dereference.

### 3.5 JIT Compiler

After the verifier approves the program, the JIT (Just-In-Time) compiler translates BPF bytecode into native machine code for your architecture (x86_64, arm64, riscv64, etc.).

**Location:** `arch/x86/net/bpf_jit_comp.c`

```
BPF bytecode                    x86_64 native code
-----------                     ------------------
mov64 r0, XDP_PASS    →         mov  $2, %rax
exit                  →         ret
```

**Why JIT matters:**

Without JIT, the kernel would interpret BPF bytecode instruction-by-instruction — extremely slow. With JIT, your BPF program runs at native speed, indistinguishable from compiled C code in the kernel.

Enable JIT (default on modern kernels):

```bash
# Check if JIT is enabled
cat /proc/sys/net/core/bpf_jit_enable
# 0 = disabled, 1 = enabled, 2 = enabled + verbose

# Enable
echo 1 > /proc/sys/net/core/bpf_jit_enable

# See the JIT output for a loaded program
cat /proc/sys/net/core/bpf_jit_kallsyms
```

### 3.6 BPF Maps — The Memory System

Maps are the **persistent, shared memory** of eBPF. They are the only way for:
- A BPF program to remember state across invocations
- BPF program ↔ userspace communication
- BPF program ↔ BPF program communication

Maps are kernel objects, referenced by file descriptors from userspace, referenced by index from BPF programs.

**Map Types:**

```
BPF_MAP_TYPE_HASH
  → Generic hash table (key → value)
  → O(1) average lookup
  → Use: connection tracking, IP-to-action tables

BPF_MAP_TYPE_ARRAY
  → Fixed-size array indexed by u32
  → O(1) lookup (direct index)
  → Values are pre-allocated and zero-initialized
  → Use: counters, stats, configuration

BPF_MAP_TYPE_PERCPU_HASH
  → Like HASH but one copy per CPU core
  → No lock needed for reads/writes
  → Use: high-performance per-CPU counters

BPF_MAP_TYPE_PERCPU_ARRAY
  → Like ARRAY but per-CPU
  → Use: packet counters, statistics

BPF_MAP_TYPE_LRU_HASH
  → Hash with LRU eviction when full
  → Use: connection tracking with bounded memory

BPF_MAP_TYPE_PERF_EVENT_ARRAY
  → Ring buffer for sending events to userspace
  → Use: logging, tracing, alerts

BPF_MAP_TYPE_RINGBUF (recommended over perf_event_array)
  → More efficient ring buffer
  → Available since Linux 5.8
  → Use: logging, event streaming

BPF_MAP_TYPE_PROG_ARRAY
  → Array of BPF program file descriptors
  → Used for tail calls (jump to another BPF program)
  → Use: implementing switch/dispatch tables in BPF

BPF_MAP_TYPE_SOCKMAP / BPF_MAP_TYPE_SOCKHASH
  → Map of sockets
  → Used to redirect socket data between sockets
  → Use: transparent proxying, service mesh

BPF_MAP_TYPE_CPUMAP
  → Redirect packets to specific CPUs
  → Use: RSS (Receive Side Scaling) with XDP

BPF_MAP_TYPE_XSKMAP
  → Map of AF_XDP sockets (zero-copy to userspace)
  → Use: kernel bypass with XDP

BPF_MAP_TYPE_LPM_TRIE
  → Longest Prefix Match trie
  → Use: routing table lookups, CIDR matching

BPF_MAP_TYPE_BLOOM_FILTER
  → Probabilistic membership test
  → Use: fast pre-filtering before expensive lookups
```

**Defining a map in C (using BTF-based map definition):**

```c
// Modern style using BTF (preferred — gives verifier type info)
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 1024);
    __type(key, __u32);          // key type: IPv4 address
    __type(value, __u64);        // value type: packet count
} packet_count SEC(".maps");

// In your BPF program:
SEC("xdp")
int count_packets(struct xdp_md *ctx) {
    __u32 src_ip = /* extract from packet */;
    __u64 *count = bpf_map_lookup_elem(&packet_count, &src_ip);
    if (count) {
        __sync_fetch_and_add(count, 1);  // atomic increment
    } else {
        __u64 initial = 1;
        bpf_map_update_elem(&packet_count, &src_ip, &initial, BPF_NOEXIST);
    }
    return XDP_PASS;
}
```

**Map operations (from BPF program):**

```c
// Lookup — returns pointer to value, or NULL
void *bpf_map_lookup_elem(void *map, const void *key);

// Update — BPF_ANY: create or update, BPF_NOEXIST: create only, BPF_EXIST: update only
long bpf_map_update_elem(void *map, const void *key, const void *value, u64 flags);

// Delete
long bpf_map_delete_elem(void *map, const void *key);

// Push/pop (for stack/queue maps)
long bpf_map_push_elem(void *map, const void *value, u64 flags);
long bpf_map_pop_elem(void *map, void *value);
```

**Map operations (from userspace in C):**

```c
#include <bpf/libbpf.h>

int map_fd = bpf_object__find_map_fd_by_name(obj, "packet_count");

// Lookup
__u32 key = 0xC0A80001;  // 192.168.0.1
__u64 value;
bpf_map_lookup_elem(map_fd, &key, &value);

// Update
__u64 new_value = 0;
bpf_map_update_elem(map_fd, &key, &new_value, BPF_ANY);

// Iterate all keys
__u32 prev_key, curr_key;
while (bpf_map_get_next_key(map_fd, &prev_key, &curr_key) == 0) {
    bpf_map_lookup_elem(map_fd, &curr_key, &value);
    // process value
    prev_key = curr_key;
}
```

### 3.7 Helper Functions

Helper functions are the kernel's API surface for BPF programs. They are the **only** way BPF programs can call kernel functionality.

Every helper has a signature like a regular C function, but the BPF verifier type-checks every call at load time.

**Complete helper catalog (selected most important):**

```c
// --- MAPS ---
void *bpf_map_lookup_elem(struct bpf_map *map, const void *key)
long  bpf_map_update_elem(struct bpf_map *map, const void *key, const void *value, u64 flags)
long  bpf_map_delete_elem(struct bpf_map *map, const void *key)

// --- PACKET MANIPULATION (XDP / TC) ---
long bpf_xdp_adjust_head(struct xdp_buff *xdp_md, int delta)
    // Grow or shrink the packet header space
    // Use: adding/removing encapsulation headers (VXLAN, GRE, etc.)

long bpf_xdp_adjust_tail(struct xdp_buff *xdp_md, int delta)
    // Grow or shrink the packet tail
    // Use: adding padding or trailers

long bpf_xdp_adjust_meta(struct xdp_buff *xdp_md, int delta)
    // Adjust metadata space before packet data
    // Use: passing metadata between XDP and TC programs

long bpf_skb_store_bytes(struct sk_buff *skb, u32 offset, const void *from, u32 len, u64 flags)
long bpf_skb_load_bytes(const struct sk_buff *skb, u32 offset, void *to, u32 len)

long bpf_l3_csum_replace(struct sk_buff *skb, u32 offset, u64 from, u64 to, u64 flags)
long bpf_l4_csum_replace(struct sk_buff *skb, u32 offset, u64 from, u64 to, u64 flags)
    // Update IP/TCP/UDP checksums after modifying packet fields

// --- PACKET REDIRECT (XDP) ---
long bpf_redirect(u32 ifindex, u64 flags)
    // Redirect packet to another interface
    // XDP_REDIRECT must be returned after this call

long bpf_redirect_map(struct bpf_map *map, u32 key, u64 flags)
    // Redirect packet using a map (DEVMAP, CPUMAP, XSKMAP)

// --- NETWORKING ---
u32  bpf_get_route_realm(struct sk_buff *skb)
long bpf_fib_lookup(void *ctx, struct bpf_fib_lookup *params, int plen, u32 flags)
    // Perform a FIB (Forwarding Information Base) lookup
    // Use: custom routing decisions in XDP/TC

long bpf_clone_redirect(struct sk_buff *skb, u32 ifindex, u64 flags)

// --- SOCKETS ---
struct bpf_sock *bpf_sk_lookup_tcp(void *ctx, struct bpf_sock_tuple *tuple, ...)
struct bpf_sock *bpf_sk_lookup_udp(void *ctx, struct bpf_sock_tuple *tuple, ...)
    // Look up a socket by 5-tuple
    // Use: implementing load balancing, NAT

long bpf_sk_assign(struct sk_buff *skb, struct bpf_sock *sk, u64 flags)
    // Assign a socket to a packet (used with sk_lookup programs)

// --- TIME ---
u64 bpf_ktime_get_ns(void)
    // Current time in nanoseconds (CLOCK_MONOTONIC)

u64 bpf_ktime_get_boot_ns(void)
    // Time since boot in nanoseconds

// --- TRACING & EVENTS ---
long bpf_trace_printk(const char *fmt, u32 fmt_size, ...)
    // Write to /sys/kernel/debug/tracing/trace_pipe
    // DEBUG ONLY — very slow, not for production

long bpf_perf_event_output(void *ctx, struct bpf_map *map, u64 flags, void *data, u64 size)
    // Write event data to perf ring buffer (userspace reads this)

long bpf_ringbuf_output(void *ringbuf, void *data, u64 size, u64 flags)
    // Write to BPF ring buffer (preferred over perf_event_output)

void *bpf_ringbuf_reserve(void *ringbuf, u64 size, u64 flags)
void  bpf_ringbuf_submit(void *data, u64 flags)
    // Reserve + submit pattern (zero-copy ring buffer write)

// --- RANDOM ---
u32 bpf_get_prandom_u32(void)
    // Pseudo-random number — use for sampling, load balancing

// --- PROCESS / CGROUP ---
u64 bpf_get_current_pid_tgid(void)
    // Returns (tgid << 32) | pid of calling process

u64 bpf_get_current_uid_gid(void)
long bpf_get_current_comm(void *buf, u32 size_of_buf)
    // Get current process name (comm)

// --- CPU ---
u32 bpf_get_smp_processor_id(void)
    // Returns current CPU ID — critical for percpu maps

// --- TAIL CALLS ---
long bpf_tail_call(void *ctx, struct bpf_map *prog_array_map, u32 index)
    // Jump to another BPF program (does not return)
    // Maximum chain depth: 33 programs
```

### 3.8 Program Types

Each BPF program type defines:
- Where in the kernel it attaches
- What context type is passed in r1
- What return values mean
- Which helpers are available

```
PROGRAM TYPE                  ATTACH POINT                    USE CASE
----------------------------  ------------------------------  ----------------------
BPF_PROG_TYPE_XDP             NIC driver (pre-stack)          Packet filter/redirect
BPF_PROG_TYPE_SCHED_CLS       TC (traffic control) ingress    Packet mangling, LB
BPF_PROG_TYPE_SCHED_ACT       TC egress                       Egress packet mangling
BPF_PROG_TYPE_SOCKET_FILTER   Socket (recv path)              Per-socket filtering
BPF_PROG_TYPE_KPROBE          Any kernel function             Tracing, debugging
BPF_PROG_TYPE_TRACEPOINT      Kernel tracepoints              Structured tracing
BPF_PROG_TYPE_PERF_EVENT      Hardware PMU events             Profiling
BPF_PROG_TYPE_CGROUP_SKB      cgroup ingress/egress           Container-level policy
BPF_PROG_TYPE_CGROUP_SOCK     cgroup socket creation          Socket policy
BPF_PROG_TYPE_LWT_IN/OUT      Lightweight tunnels             Custom encapsulation
BPF_PROG_TYPE_SOCK_OPS        TCP state machine events        TCP tuning, monitoring
BPF_PROG_TYPE_SK_SKB          Socket map redirect             Transparent proxy
BPF_PROG_TYPE_SK_MSG          Sendmsg redirect                Accelerated service mesh
BPF_PROG_TYPE_RAW_TRACEPOINT  Raw tracepoints (no args copy)  High-performance tracing
BPF_PROG_TYPE_FLOW_DISSECTOR  Flow key extraction             Custom RSS hashing
BPF_PROG_TYPE_SK_LOOKUP       Socket lookup override          Load balancing
BPF_PROG_TYPE_STRUCT_OPS      Kernel struct function tables   Custom TCP congestion
BPF_PROG_TYPE_LSM             Linux Security Module hooks     Security policy
```

### 3.9 BTF — BPF Type Format

**BTF (BPF Type Format)** is a compact binary format that encodes C type information alongside BPF programs.

**Why BTF exists:**

Before BTF, a BPF program compiled on kernel 5.4 would fail on kernel 5.8 if any kernel struct changed (e.g., a field moved or was added). You had to recompile for every kernel version.

BTF solves this by embedding type information in the BPF object file, and the kernel exposing its own BTF in `/sys/kernel/btf/vmlinux`.

```
Your BPF program          Kernel
-------------------       ------
includes vmlinux.h        /sys/kernel/btf/vmlinux
  (generated from BTF)          |
        |                       | BTF describes all kernel types
        v                       v
  compiled with BTF     kernel can relocate your accesses
                         to match actual field offsets
```

**Generating vmlinux.h (the kernel's header from BTF):**

```bash
# Generate a single header file with ALL kernel types
bpftool btf dump file /sys/kernel/btf/vmlinux format c > vmlinux.h

# This gives you access to ALL kernel structs without including kernel headers
# struct sk_buff, struct iphdr, struct task_struct — everything
```

### 3.10 CO-RE — Compile Once, Run Everywhere

CO-RE (Compile Once, Run Everywhere) is the capability, enabled by BTF, to compile a BPF program once and run it on different kernel versions.

**How CO-RE relocations work:**

```c
// You write this (accessing a kernel struct field):
struct task_struct *task = bpf_get_current_task();
pid_t pid = BPF_CORE_READ(task, pid);
//          ^^^^^^^^^^^^^ CO-RE macro

// BPF_CORE_READ expands to something like:
// __builtin_preserve_access_index(...)
// This emits a relocation record in the BPF object file

// At load time, libbpf:
// 1. Reads the kernel's BTF from /sys/kernel/btf/vmlinux
// 2. Finds where 'pid' is actually located in 'task_struct' on THIS kernel
// 3. Patches the field offset in your BPF bytecode
// Your program now accesses the right offset regardless of kernel version
```

**CO-RE macros:**

```c
#include <bpf/bpf_core_read.h>

// Read a field (handles pointer chasing, endianness, etc.)
BPF_CORE_READ(src, a, b, c)  // equivalent to src->a->b->c

// Read into a local variable
BPF_CORE_READ_INTO(&dest, src, a, b)

// Existence check — does this field exist on this kernel?
bpf_core_field_exists(struct_type, field)

// Size of a field
bpf_core_field_size(struct_type, field)

// Enum value existence and value
bpf_core_enum_value_exists(enum_type, value_name)
bpf_core_enum_value(enum_type, value_name)
```

### 3.11 libbpf

`libbpf` is the canonical C library for loading and managing BPF programs from userspace.

**What libbpf does:**

```
BPF Object File (.o)
        |
        v
  [libbpf: bpf_object__open()]
        |
        +--> parse ELF sections
        +--> extract program bytecode
        +--> extract map definitions
        +--> extract BTF info
        |
        v
  [libbpf: bpf_object__load()]
        |
        +--> create maps (bpf() syscall: BPF_MAP_CREATE)
        +--> apply CO-RE relocations (patch field offsets)
        +--> load programs (bpf() syscall: BPF_PROG_LOAD) → kernel verifier
        +--> attach programs to hook points
        |
        v
  Running BPF program in kernel
```

**Minimal libbpf C userspace program:**

```c
#include <stdio.h>
#include <bpf/libbpf.h>

int main(void) {
    // Open and parse the .o file
    struct bpf_object *obj = bpf_object__open("my_prog.bpf.o");
    if (libbpf_get_error(obj)) {
        fprintf(stderr, "Failed to open BPF object\n");
        return 1;
    }

    // Load all programs and maps into kernel
    if (bpf_object__load(obj)) {
        fprintf(stderr, "Failed to load BPF object\n");
        return 1;
    }

    // Find a specific program
    struct bpf_program *prog = bpf_object__find_program_by_name(obj, "xdp_filter");

    // Get the program's file descriptor
    int prog_fd = bpf_program__fd(prog);

    // Attach to interface (e.g., eth0 = ifindex 2)
    int ifindex = if_nametoindex("eth0");
    bpf_xdp_attach(ifindex, prog_fd, XDP_FLAGS_UPDATE_IF_NOEXIST, NULL);

    // Keep running, read map data...
    // bpf_map__fd(), bpf_map_lookup_elem(), etc.

    bpf_object__close(obj);
    return 0;
}
```

**BPF Skeleton (generated code — modern approach):**

```bash
# Generate a skeleton from your BPF object file
bpftool gen skeleton my_prog.bpf.o > my_prog.skel.h
```

```c
// Using the generated skeleton (much simpler)
#include "my_prog.skel.h"

int main(void) {
    // Open + load + attach in one call
    struct my_prog *skel = my_prog__open_and_load();

    // Attach
    my_prog__attach(skel);

    // Access maps directly through the skeleton
    int err = bpf_map__lookup_elem(
        skel->maps.packet_count,
        &key, sizeof(key),
        &value, sizeof(value),
        0
    );

    // Cleanup
    my_prog__destroy(skel);
}
```

### 3.12 The bpf() Syscall

Everything in eBPF goes through one syscall: `bpf(int cmd, union bpf_attr *attr, unsigned int size)`.

```c
// Key commands:
BPF_MAP_CREATE      // Create a new map → returns map fd
BPF_MAP_LOOKUP_ELEM // Look up a key in a map
BPF_MAP_UPDATE_ELEM // Insert or update a key-value pair
BPF_MAP_DELETE_ELEM // Delete a key
BPF_MAP_GET_NEXT_KEY // Iterate map keys

BPF_PROG_LOAD       // Load BPF program → runs verifier → returns prog fd
BPF_PROG_ATTACH     // Attach program to cgroup/sockmap/etc.
BPF_PROG_DETACH     // Detach program
BPF_PROG_QUERY      // Query programs attached to a hook

BPF_OBJ_PIN         // Pin an object (map/program) to BPF filesystem
BPF_OBJ_GET         // Get fd from pinned BPF filesystem path

BPF_LINK_CREATE     // Create a persistent program attachment (BPF link)
BPF_LINK_UPDATE     // Replace the program in a BPF link
BPF_LINK_GET_FD_BY_ID

BPF_BTF_LOAD        // Load BTF type information
BPF_BTF_GET_FD_BY_ID

BPF_PROG_TEST_RUN   // Test-run a BPF program with supplied input
```

### 3.13 BPF Object Lifecycle and Pinning

```
Create map/prog (bpf syscall)
        |
        v
  Kernel object created
  Reference count = 1
  File descriptor returned to process
        |
        |-- Process holds fd → object lives
        |
        |-- Process exits → fd closed → ref count = 0 → object DELETED
        |
        v
  To make objects PERSIST across process exit:
  Pin to BPF filesystem

# BPF filesystem is mounted at /sys/fs/bpf/
# (or manually: mount -t bpf bpf /sys/fs/bpf)

bpf(BPF_OBJ_PIN, {pathname: "/sys/fs/bpf/my_map", bpf_fd: map_fd})
  → creates a filesystem entry that holds a reference
  → object now persists even if all processes die

bpf(BPF_OBJ_GET, {pathname: "/sys/fs/bpf/my_map"})
  → returns a new fd to the pinned object
  → another process can access the same map
```

**BPF Links** (preferred over direct attachment):

```
BPF Link = a kernel object that represents a program attachment
         = has its own reference count
         = can be pinned independently of the program

Advantage over direct attachment:
  - Cleaner lifecycle management
  - Can update the program behind a link atomically
  - Multiple processes can manage the same link
```

---

## 4. XDP — eXpress Data Path

### 4.1 What is XDP and Why It Exists

XDP is a high-performance, programmable packet processing framework that runs BPF programs at the **earliest possible point** in the receive path — inside the NIC driver, before any sk_buff allocation.

```
Traditional receive path:
NIC → [IRQ] → driver → sk_buff alloc → netif_receive_skb → protocol stack → socket → userspace
                ^
                |
         THIS IS EXPENSIVE
         (memory allocation, many function calls)

XDP receive path:
NIC → [IRQ] → driver → [XDP PROGRAM RUNS HERE] → decision
                              ^
                              |
                   No sk_buff allocated yet
                   Working directly on DMA buffer
                   Maximum performance
```

**Performance numbers (approximate, hardware dependent):**

```
Traditional iptables DROP:     ~1.5 Mpps  (million packets per second)
nftables DROP:                 ~3 Mpps
XDP generic DROP:              ~10 Mpps
XDP native DROP:               ~24 Mpps
XDP offloaded DROP (SmartNIC): ~100+ Mpps
```

### 4.2 XDP Execution Model

When a packet arrives:

```
1. NIC DMA engine writes packet bytes into a pre-allocated ring buffer page
   (No sk_buff, just raw bytes in a page frame)

2. Driver interrupt fires

3. Driver sets up struct xdp_buff pointing to the DMA buffer:
   struct xdp_buff {
       void *data;          // pointer to start of packet data
       void *data_end;      // pointer to end of packet data
       void *data_meta;     // pointer to metadata area (before data)
       void *data_hard_start; // start of the entire page
       struct xdp_rxq_info *rxq; // receive queue info
   };

4. Driver calls the attached XDP BPF program with xdp_buff

5. BPF program executes and returns an action code (XDP_DROP, XDP_PASS, etc.)

6. Driver acts on the return code immediately
```

**The xdp_md context (what your program sees):**

```c
// This is what the verifier presents to your BPF program
// (kernel converts xdp_buff to xdp_md at the BPF boundary)
struct xdp_md {
    __u32 data;           // offset to packet data start
    __u32 data_end;       // offset to packet data end
    __u32 data_meta;      // offset to metadata area
    __u32 ingress_ifindex; // interface the packet arrived on
    __u32 rx_queue_index; // RX queue index
    __u32 egress_ifindex; // for XDP_REDIRECT
};

// In BPF code, you access data as:
void *data     = (void *)(long)ctx->data;
void *data_end = (void *)(long)ctx->data_end;

// ALWAYS bounds check before reading:
struct ethhdr *eth = data;
if ((void *)(eth + 1) > data_end)
    return XDP_DROP;  // malformed/truncated packet
```

### 4.3 XDP Modes

```
NATIVE XDP (xdpdrv)
  → Runs inside the NIC driver
  → Requires driver support (Intel i40e, mlx5, ixgbe, virtio_net, etc.)
  → Fastest: no sk_buff, no memory allocation
  → Check support: ethtool -i eth0 (look for driver name, then check kernel source)

GENERIC XDP (xdpgeneric)
  → Fallback when driver has no native XDP support
  → Runs AFTER sk_buff is allocated (in netif_receive_skb)
  → Slower than native (sk_buff already paid for), but works on ANY NIC
  → Good for development and testing

OFFLOADED XDP (xdpoffload)
  → Program is compiled and runs ON THE NIC HARDWARE
  → CPU is completely bypassed for matching packets
  → Requires SmartNIC (Netronome Agilio, etc.)
  → Fastest possible — no CPU involvement at all
  → Most restricted BPF subset
```

**Attaching XDP programs:**

```bash
# Native XDP
ip link set dev eth0 xdpdrv obj prog.o sec xdp

# Generic XDP (any NIC)
ip link set dev eth0 xdpgeneric obj prog.o sec xdp

# Offloaded XDP
ip link set dev eth0 xdpoffload obj prog.o sec xdp

# Remove XDP
ip link set dev eth0 xdp off

# Check what's attached
ip link show eth0
# Look for: prog/xdp id 42 tag abc123def456 jited
```

### 4.4 XDP Return Codes (Actions)

The return value from your XDP program determines the packet's fate:

```c
enum xdp_action {
    XDP_ABORTED = 0,  // Bug/error in program
                      // Packet dropped + xdp:xdp_exception tracepoint fired
                      // Use: should never happen in production

    XDP_DROP    = 1,  // Drop the packet silently
                      // The DMA buffer is immediately recycled
                      // Fastest possible action — zero work done

    XDP_PASS    = 2,  // Pass packet to normal kernel network stack
                      // sk_buff is NOW allocated (the usual path continues)
                      // Use: for packets you don't want to handle in XDP

    XDP_TX      = 3,  // Transmit the packet back OUT THE SAME INTERFACE
                      // The packet can be modified before TX
                      // Use: hairpin NAT, ping responder, reflector

    XDP_REDIRECT = 4, // Redirect packet elsewhere
                      // Destination set by bpf_redirect() or bpf_redirect_map()
                      // Use: load balancing, forwarding, AF_XDP
};
```

### 4.5 XDP Programming — Complete C Example

**Example: Layer 3 packet counter + IP blocklist**

BPF program (`xdp_filter.bpf.c`):

```c
// SPDX-License-Identifier: GPL-2.0
#include "vmlinux.h"           // all kernel types (generated from BTF)
#include <bpf/bpf_helpers.h>   // BPF_CORE_READ, SEC(), etc.
#include <bpf/bpf_endian.h>    // bpf_ntohs(), bpf_htonl()

// -------------------------------------------------------
// MAP DEFINITIONS
// -------------------------------------------------------

// Blocklist: blocked source IPs → u64 hit counter
struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __uint(max_entries, 10000);
    __type(key, __u32);    // IPv4 address in network byte order
    __type(value, __u64);  // number of blocked packets from this IP
} blocklist SEC(".maps");

// Stats: global counters indexed by XDP action
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 5);    // one per XDP action (0-4)
    __type(key, __u32);
    __type(value, __u64);
} stats SEC(".maps");

// -------------------------------------------------------
// HELPER: increment a stat counter
// -------------------------------------------------------
static __always_inline void count_action(__u32 action) {
    __u64 *counter = bpf_map_lookup_elem(&stats, &action);
    if (counter)
        __sync_fetch_and_add(counter, 1);
}

// -------------------------------------------------------
// XDP PROGRAM ENTRY POINT
// -------------------------------------------------------
SEC("xdp")
int xdp_filter(struct xdp_md *ctx) {
    // Get raw pointers to packet data
    void *data     = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;

    // ---- Parse Ethernet header ----
    struct ethhdr *eth = data;

    // CRITICAL: bounds check before any field access
    // Verifier REQUIRES this. Without it: program rejected.
    if ((void *)(eth + 1) > data_end) {
        count_action(XDP_ABORTED);
        return XDP_ABORTED;
    }

    // Only process IPv4 packets
    if (eth->h_proto != bpf_htons(ETH_P_IP)) {
        count_action(XDP_PASS);
        return XDP_PASS;
    }

    // ---- Parse IPv4 header ----
    struct iphdr *ip = (void *)(eth + 1);

    if ((void *)(ip + 1) > data_end) {
        count_action(XDP_ABORTED);
        return XDP_ABORTED;
    }

    // Validate IP header length
    // ihl is in 32-bit words, minimum valid is 5 (= 20 bytes)
    if (ip->ihl < 5) {
        count_action(XDP_DROP);
        return XDP_DROP;
    }

    __u32 src_ip = ip->saddr;  // source IP in network byte order

    // ---- Check blocklist ----
    __u64 *blocked_count = bpf_map_lookup_elem(&blocklist, &src_ip);
    if (blocked_count) {
        // This IP is blocked — increment hit counter and drop
        __sync_fetch_and_add(blocked_count, 1);
        count_action(XDP_DROP);
        return XDP_DROP;
    }

    count_action(XDP_PASS);
    return XDP_PASS;
}

// All BPF programs in GPL-licensed kernel infrastructure
// must declare their license for helper access
char LICENSE[] SEC("license") = "GPL";
```

**Userspace control program (`xdp_filter.c`):**

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <net/if.h>
#include <bpf/libbpf.h>
#include <bpf/bpf.h>
#include "xdp_filter.skel.h"  // generated by: bpftool gen skeleton

static int libbpf_print(enum libbpf_print_level level, const char *fmt, va_list args) {
    if (level == LIBBPF_DEBUG) return 0;  // suppress debug
    return vfprintf(stderr, fmt, args);
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <ifname> [block_ip1 block_ip2 ...]\n", argv[0]);
        return 1;
    }

    const char *ifname = argv[1];
    int ifindex = if_nametoindex(ifname);
    if (!ifindex) {
        fprintf(stderr, "Interface %s not found\n", ifname);
        return 1;
    }

    libbpf_set_print(libbpf_print);

    // Open, load (verify + JIT), and attach the BPF program
    struct xdp_filter *skel = xdp_filter__open_and_load();
    if (!skel) {
        fprintf(stderr, "Failed to load BPF skeleton\n");
        return 1;
    }

    // Attach XDP program to the interface
    struct bpf_link *link = bpf_program__attach_xdp(skel->progs.xdp_filter, ifindex);
    if (libbpf_get_error(link)) {
        fprintf(stderr, "Failed to attach XDP program\n");
        xdp_filter__destroy(skel);
        return 1;
    }

    printf("XDP filter attached to %s (ifindex %d)\n", ifname, ifindex);

    // Add blocked IPs from command line arguments
    for (int i = 2; i < argc; i++) {
        struct in_addr addr;
        if (inet_aton(argv[i], &addr) == 0) {
            fprintf(stderr, "Invalid IP: %s\n", argv[i]);
            continue;
        }
        __u32 key = addr.s_addr;  // network byte order
        __u64 value = 0;
        int err = bpf_map__update_elem(skel->maps.blocklist,
                                       &key, sizeof(key),
                                       &value, sizeof(value), BPF_NOEXIST);
        if (err)
            fprintf(stderr, "Failed to block %s: %s\n", argv[i], strerror(-err));
        else
            printf("Blocked: %s\n", argv[i]);
    }

    // Poll stats every second
    printf("\nStats (Ctrl+C to stop):\n");
    printf("%-12s %-12s %-12s %-12s %-12s\n",
           "ABORTED", "DROP", "PASS", "TX", "REDIRECT");

    while (1) {
        sleep(1);

        // For PERCPU_ARRAY, we read per-CPU values and sum them
        __u64 total[5] = {0};
        int ncpus = libbpf_num_possible_cpus();
        __u64 *percpu_values = calloc(ncpus, sizeof(__u64));

        for (__u32 action = 0; action < 5; action++) {
            bpf_map__lookup_elem(skel->maps.stats,
                                 &action, sizeof(action),
                                 percpu_values, sizeof(__u64) * ncpus, 0);
            for (int cpu = 0; cpu < ncpus; cpu++)
                total[action] += percpu_values[cpu];
        }
        free(percpu_values);

        printf("\r%-12llu %-12llu %-12llu %-12llu %-12llu",
               total[0], total[1], total[2], total[3], total[4]);
        fflush(stdout);
    }

    bpf_link__destroy(link);
    xdp_filter__destroy(skel);
    return 0;
}
```

**Build system (`Makefile`):**

```makefile
CLANG ?= clang
BPFTOOL ?= bpftool
ARCH := $(shell uname -m | sed 's/x86_64/x86/' | sed 's/aarch64/arm64/')

# Generate vmlinux.h from running kernel's BTF
vmlinux.h:
	$(BPFTOOL) btf dump file /sys/kernel/btf/vmlinux format c > vmlinux.h

# Compile BPF program to BPF bytecode (ELF .o)
xdp_filter.bpf.o: xdp_filter.bpf.c vmlinux.h
	$(CLANG) -g -O2 -target bpf -D__TARGET_ARCH_$(ARCH) \
		-I/usr/include/$(shell uname -m)-linux-gnu \
		-c $< -o $@

# Generate skeleton header
xdp_filter.skel.h: xdp_filter.bpf.o
	$(BPFTOOL) gen skeleton $< > $@

# Compile userspace program
xdp_filter: xdp_filter.c xdp_filter.skel.h
	cc -g -O2 -o $@ $< -lbpf -lelf -lz

clean:
	rm -f vmlinux.h *.o *.skel.h xdp_filter

.PHONY: clean
```

### 4.6 XDP Maps in Practice

**DEVMAP — redirect to another interface:**

```c
// Map definition in BPF program
struct {
    __uint(type, BPF_MAP_TYPE_DEVMAP);
    __uint(max_entries, 256);
    __type(key, __u32);       // index
    __type(value, __u32);     // ifindex of target interface
} tx_ports SEC(".maps");

// In XDP program
return bpf_redirect_map(&tx_ports, target_ifindex, 0);
```

**CPUMAP — distribute packets across CPUs:**

```c
struct {
    __uint(type, BPF_MAP_TYPE_CPUMAP);
    __uint(max_entries, 12);  // max 12 CPUs
    __type(key, __u32);       // CPU id
    __type(value, struct bpf_cpumap_val);
} cpumap SEC(".maps");

// Round-robin across CPUs using a hash of the 5-tuple
__u32 cpu = bpf_get_hash_recalc(ctx) % ncpus;
return bpf_redirect_map(&cpumap, cpu, 0);
```

### 4.7 AF_XDP — Zero Copy to Userspace

AF_XDP (Address Family XDP) allows XDP to redirect packets directly to a userspace memory region — **bypassing the kernel network stack entirely** while keeping the kernel's XDP hook.

```
Normal packet path:
  NIC → kernel → copy → userspace buffer     (one memory copy)

AF_XDP path:
  NIC → DMA into UMEM (userspace memory)     (zero copies)
  XDP program → bpf_redirect_map(&xsks_map, queue_id, 0)
  Userspace polls UMEM ring directly
```

**UMEM (User Memory):**

```
UMEM is a contiguous memory region you allocate in userspace.
You register it with the kernel via setsockopt(AF_XDP, XDP_UMEM_REG).
The kernel and NIC can DMA-write packets directly into this region.

UMEM is divided into fixed-size FRAMES (e.g., 4096 bytes each).
Four rings manage frame ownership:

  FILL ring:   userspace → kernel  (give frames to kernel for RX)
  RX ring:     kernel → userspace  (kernel says: frame N has a packet)
  TX ring:     userspace → kernel  (ask kernel to transmit frame N)
  COMPLETION:  kernel → userspace  (kernel says: frame N TX done)
```

**Go implementation using AF_XDP (using `asavie/xdp` library):**

```go
package main

import (
    "fmt"
    "net"
    "github.com/asavie/xdp"
)

func main() {
    ifname := "eth0"
    iface, _ := net.InterfaceByName(ifname)

    // Create AF_XDP socket on queue 0
    sock, err := xdp.NewSocket(iface.Index, 0, nil)
    if err != nil {
        panic(err)
    }

    // Load XDP program with XSKMAP
    prog, err := xdp.NewProgram(1 /* num queues */)
    if err != nil {
        panic(err)
    }
    prog.Attach(iface.Index)

    // Register the AF_XDP socket in the XSKMAP
    prog.Register(0 /* queue id */, sock.FD())

    for {
        // Poll for received packets
        if n, _ := sock.Poll(100 /* ms timeout */); n > 0 {
            descs := sock.Receive(n)
            for _, desc := range descs {
                // Get packet bytes — zero copy, direct access to UMEM
                frame := sock.GetFrame(desc)
                fmt.Printf("Received %d bytes\n", len(frame))
                // Process frame here
            }
            sock.FillAll() // return frames to kernel
        }
    }
}
```

### 4.8 XDP vs DPDK

```
Property              XDP                      DPDK
--------------------  -----------------------  -----------------------
Kernel involvement    Yes (eBPF runs in kernel) No (full bypass)
NIC sharing           Yes (NIC still usable)   No (exclusive NIC ownership)
TCP/IP stack          Available (XDP_PASS)     Must reimplement
Speed (filtering)     ~24 Mpps native          ~80+ Mpps
Speed (forwarding)    ~14 Mpps                 ~40+ Mpps
Safety                Verifier guarantees      Your code, your bugs
Observability         Full kernel tools         Custom only
Portability           Any Linux kernel ≥ 4.8   Requires specific NICs
Use case              Cloud/Kubernetes          Telco/NFV/custom appliances
```

For cloud-native networking (Cilium, K8s), XDP is the right choice. DPDK is for telco/NFV where you need every last bit of performance and are willing to sacrifice integration.

---

## 5. Cilium — Complete Deep Dive

### 5.1 What is Cilium

Cilium is a **cloud-native networking, security, and observability** project for Kubernetes, built on eBPF.

It replaces:

```
Traditional K8s networking stack:
  kube-proxy          → iptables rules (thousands of them)
  CNI plugins         → iptables + VXLAN (e.g., Flannel, Calico)
  Service mesh sidecar → Envoy proxy per pod (e.g., Istio)
  Network policy      → iptables
  Observability       → sidecar agents

Cilium replaces ALL of this with:
  eBPF programs in the kernel
  No iptables
  No sidecar proxies (optional: eBPF-based service mesh)
  Identity-based security (not IP-based)
  Real-time deep observability
```

### 5.2 Architecture Overview

```
Kubernetes Control Plane
        |
        | (watches K8s API: Pods, Services, NetworkPolicies, etc.)
        |
        v
  [Cilium Operator]          -- cluster-wide tasks (IPAM, CRD management)
        |
        v
  [cilium-agent]             -- runs as DaemonSet on every node
  (one per node)
        |
        +---> [BPF compiler] --> generates & loads BPF programs per-endpoint
        |
        +---> [Policy engine] --> translates K8s NetworkPolicy to BPF maps
        |
        +---> [IPAM]           --> assigns pod IPs
        |
        +---> [Hubble server]  --> observability event pipeline
        |
        v
  [BPF programs in kernel]   -- datapath (does the actual packet processing)
        |
        +---> TC ingress/egress hooks per veth interface
        +---> XDP hook on physical NIC (optional)
        +---> cgroup hooks (socket-level policy)
        +---> kprobe/tracepoint hooks (observability)
        |
        v
  [BPF Maps]                 -- shared state between agent and datapath
        (policy maps, connection tracking, load balancer maps, etc.)
```

**Key Kubernetes objects Cilium manages:**

```
K8s Object              Cilium Action
-----------             -------------
Pod created             → assign IP, create endpoint, compile+load BPF program
Service created         → update BPF load balancer map
NetworkPolicy created   → update BPF policy map for affected endpoints
Node joins cluster      → establish tunnel or BGP route
```

### 5.3 Cilium Agent

The `cilium-agent` is a Go daemon running on each node. Its responsibilities:

```
1. ENDPOINT MANAGEMENT
   → Watches K8s API for pod creation/deletion
   → Assigns each pod a numeric "endpoint ID"
   → Regenerates BPF programs when pod config changes

2. IDENTITY MANAGEMENT
   → Assigns each unique set of labels a numeric "security identity"
   → e.g., all pods with labels {app=frontend, env=prod} share identity 42
   → Identities are cluster-wide (shared via KVStore or CRDs)

3. POLICY COMPILATION
   → Translates CiliumNetworkPolicy / K8s NetworkPolicy
   → Computes which identities are allowed to talk to which identities
   → Writes results into BPF policy maps

4. BPF PROGRAM MANAGEMENT
   → Compiles endpoint-specific BPF programs from templates
   → Loads programs via libbpf
   → Attaches to veth interfaces

5. LOAD BALANCER
   → Watches K8s Services
   → Writes backend information into BPF maps
   → XDP/TC programs do load balancing in kernel

6. IPAM (IP Address Management)
   → Allocates pod IPs from the node's CIDR
   → Supports: Cluster Scope, Kubernetes Host Scope, AWS ENI, Azure, etc.

7. HUBBLE
   → Exposes gRPC server for flow data
   → BPF programs send events to perf ring buffers
   → Agent reads and exports to Hubble Relay
```

### 5.4 Cilium Datapath — eBPF in Action

For every pod, Cilium creates a **veth pair**:

```
Pod netns                      Host netns
-----------                    ----------
eth0 (pod's interface)  <--->  lxcXXXXXX (veth on host side)
                                    |
                              [BPF programs attached here]
                                    |
                              host network stack / physical NIC
```

**TC (Traffic Control) hook points Cilium uses:**

```
Packet FROM pod TO network:
  Pod eth0 → veth lxcXXXXXX
  TC EGRESS on lxcXXXXXX runs: bpf_lxc.c / from-container
    - Apply egress network policy
    - Assign/verify source identity
    - Lookup destination: local pod? → redirect to dest veth
                          remote pod? → encapsulate (VXLAN/Geneve) or route
                          Service? → DNAT to backend

Packet FROM network TO pod:
  lxcXXXXXX TC INGRESS runs: bpf_lxc.c / to-container
    - Apply ingress network policy
    - Verify source identity
    - Pass to pod
```

**The identity concept in the datapath:**

```c
// Simplified view of what Cilium's BPF programs do

// When sending a packet from a pod, stamp the security identity:
// (In practice this goes into the packet's encapsulation header or
//  is carried in an ipcache map lookup)

struct endpoint_info {
    __u32 ifindex;
    __u32 lxc_id;     // endpoint ID
    __u32 sec_label;  // security identity
    __u8  mac[6];
};

// Policy check (grossly simplified):
struct policy_key {
    __u32 sec_label;   // source identity
    __u16 dport;       // destination port
    __u8  protocol;    // TCP/UDP/ICMP
    __u8  egress;      // 0=ingress, 1=egress
};

struct policy_entry {
    __u32 proxy_port;  // 0 = allow, nonzero = redirect to proxy
    __u8  deny;        // 1 = deny
};

// Lookup in policy map
struct policy_entry *entry = bpf_map_lookup_elem(&policy_map, &key);
if (!entry || entry->deny)
    return DROP_POLICY;  // drop due to policy
```

### 5.5 CNI Integration

**What is CNI?** The Container Network Interface is a specification for how container runtimes (containerd, CRI-O) ask CNI plugins to set up networking for a pod.

```
Pod creation sequence:

kubelet
  → calls containerd: "create pod X"
  → containerd creates network namespace for pod
  → containerd calls CNI plugin (Cilium): "set up networking in this netns"
  → Cilium CNI binary:
      1. Create veth pair (lxcXXXX ↔ eth0)
      2. Move pod-side into pod netns
      3. Assign IP address from IPAM
      4. Configure routes inside pod netns
      5. Notify cilium-agent via API: "new endpoint created"
  → cilium-agent:
      6. Creates endpoint object
      7. Assigns security identity
      8. Compiles and loads BPF programs for this endpoint
      9. Attaches BPF programs to lxcXXXX veth
```

### 5.6 Identity-Based Security Model

This is Cilium's most important conceptual innovation over traditional networking.

**Traditional IP-based model (iptables):**

```
Rule: "allow traffic from 10.0.1.5 to 10.0.2.8 on port 80"

Problems:
- Pod IPs are ephemeral (pod dies, new pod gets different IP)
- Must constantly update iptables rules
- Rules scale as O(n*m) for n sources and m destinations
- At 10,000 pods: 100 million iptables rules
```

**Cilium's identity-based model:**

```
Each unique combination of labels → one numeric identity

Pods with {app=frontend, env=prod}  → identity 1234
Pods with {app=backend, env=prod}   → identity 5678

Policy: "identity 1234 may talk to identity 5678 on port 8080"

No matter how many pods have these labels, there are only
two identities. Policy maps stay small regardless of scale.

When a pod is created:
  → cilium-agent looks at its labels
  → assigns the corresponding identity (creating one if new)
  → stores mapping: (pod IP → identity) in ipcache BPF map

When a packet arrives:
  → BPF program does: ipcache lookup(src_ip) → src_identity
  → policy lookup(src_identity, dst_port, proto) → allow/deny
  → O(1) lookup regardless of cluster size
```

**CiliumNetworkPolicy (CRD):**

```yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: allow-frontend-to-backend
spec:
  endpointSelector:           # applies to pods with these labels (destination)
    matchLabels:
      app: backend
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: frontend         # allow from frontend pods
    toPorts:
    - ports:
      - port: "8080"
        protocol: TCP
      rules:
        http:                 # L7 HTTP policy!
        - method: GET
          path: /api/.*       # regex match on URL path
```

Cilium can enforce **L7 policies** (HTTP, gRPC, Kafka, DNS) without sidecars by redirecting traffic to an embedded Envoy proxy or using native BPF sk_msg programs.

### 5.7 Network Policy

**Policy evaluation logic:**

```
Default behavior (no policy): ALLOW ALL
When ANY policy selects an endpoint: DENY ALL, then apply rules

Ingress to Pod A is allowed if:
  ANY fromEndpoints rule matches the source identity AND port
  OR any fromCIDR rule matches the source IP
  OR any fromEntities rule matches (world, cluster, host, etc.)

Egress from Pod A is allowed if:
  ANY toEndpoints/toCIDR/toFQDN/toServices rule matches
```

**Entities (special policy targets):**

```
world     → traffic outside the cluster
cluster   → all endpoints in the cluster
host      → the node's host network namespace
kube-apiserver → K8s API server
health    → Cilium health check endpoints
```

**DNS-based egress policy (powerful feature):**

```yaml
egress:
- toFQDNs:
  - matchName: api.stripe.com
  toPorts:
  - ports:
    - port: "443"
      protocol: TCP
```

Cilium intercepts DNS responses, extracts resolved IPs, and dynamically updates BPF CIDR maps — so you can write policy based on domain names, not IPs.

### 5.8 Load Balancing with eBPF

Cilium replaces `kube-proxy` entirely with BPF-based load balancing.

**How kube-proxy works (old way):**

```
Service VIP: 10.96.0.50:80
Backends: 10.0.1.5:8080, 10.0.1.6:8080, 10.0.1.7:8080

kube-proxy writes iptables rules:
  -A KUBE-SVC-XXX -m statistic --mode random --probability 0.33 -j KUBE-SEP-A
  -A KUBE-SVC-XXX -m statistic --mode random --probability 0.5  -j KUBE-SEP-B
  -A KUBE-SVC-XXX -j KUBE-SEP-C
  (plus many more rules for MASQUERADE, DNAT, etc.)

Problem: iptables is O(n) — every packet traverses rules linearly
At 10,000 services: each packet checks thousands of rules
```

**How Cilium does it (new way):**

```
BPF map: service_map
  key:   {VIP: 10.96.0.50, port: 80, proto: TCP}
  value: {backend_count: 3, flags: ...}

BPF map: backend_map
  key:   {service_id: X, slot: 0}  → {backend: 10.0.1.5:8080}
  key:   {service_id: X, slot: 1}  → {backend: 10.0.1.6:8080}
  key:   {service_id: X, slot: 2}  → {backend: 10.0.1.7:8080}

BPF program on socket connect():
  1. Lookup service_map[{VIP, port}] → get backend count
  2. Pick random slot: slot = bpf_get_prandom_u32() % count
  3. Lookup backend_map[{svc_id, slot}] → get backend IP:port
  4. Rewrite socket destination (DNAT at socket level)

Result: O(1) load balancing, no packet enters the stack with VIP address
        The DNAT happens at the socket layer before any packet is sent
```

**Socket-level load balancing (eBPF sockops):**

```c
// This BPF program runs at connect() syscall time
// Before the TCP SYN is even sent
SEC("cgroup/connect4")
int sock_connect4(struct bpf_sock_addr *ctx) {
    __u32 vip = ctx->user_ip4;   // destination IP (in host byte order)
    __u16 port = ctx->user_port; // destination port

    struct lb4_key key = {
        .address = vip,
        .dport   = port,
    };

    struct lb4_service *svc = bpf_map_lookup_elem(&cilium_lb4_services_v2, &key);
    if (!svc)
        return 1;  // not a known service, pass through

    // Select backend
    __u32 slot = bpf_get_prandom_u32() % svc->count;
    struct lb4_key backend_key = {.backend_slot = slot, ...};
    struct lb4_backend *backend = bpf_map_lookup_elem(&cilium_lb4_backends_v3, &backend_key);
    if (!backend)
        return 1;

    // Rewrite destination — happens in socket layer, no packet mangling
    ctx->user_ip4  = backend->address;
    ctx->user_port = backend->port;

    return 1;  // continue with connect()
}
```

### 5.9 Hubble — Observability Layer

Hubble is Cilium's observability system. It provides **deep network visibility** using eBPF.

```
Architecture:

[eBPF programs in kernel]
  → perf_event / ringbuf events
  → capture: connection open/close, policy drop, DNS query, HTTP request

[Hubble server (in cilium-agent)]
  → reads events from BPF ring buffers
  → enriches with K8s metadata (pod name, namespace, labels)
  → serves via gRPC

[Hubble Relay]
  → aggregates from all nodes
  → single cluster-wide view

[Hubble UI / CLI]
  → visualize flows
  → query: "show me all connections from namespace A to namespace B"
  → policy troubleshooting: "why was this packet dropped?"
```

**Hubble CLI usage:**

```bash
# Observe all flows in real time
hubble observe

# Filter by namespace
hubble observe --namespace production

# Filter by pod
hubble observe --pod frontend-5d8c7b-xxxx

# Show only dropped flows (policy violations)
hubble observe --verdict DROPPED

# Show HTTP flows
hubble observe --protocol http

# Show DNS queries
hubble observe --protocol dns

# Count flows between namespaces
hubble observe --namespace frontend --to-namespace backend --output json | jq
```

**What a Hubble flow record looks like:**

```json
{
  "time": "2026-04-03T10:00:00.123456Z",
  "verdict": "FORWARDED",
  "source": {
    "id": 1234,
    "identity": 9876,
    "namespace": "production",
    "labels": ["app=frontend", "env=prod"],
    "pod_name": "frontend-5d8c7b-xxxx"
  },
  "destination": {
    "id": 5678,
    "identity": 5432,
    "namespace": "production",
    "labels": ["app=backend", "env=prod"],
    "pod_name": "backend-7c9d4f-yyyy",
    "port": 8080
  },
  "l4": {"TCP": {"source_port": 49152, "destination_port": 8080, "flags": {"SYN": true}}},
  "l7": {"http": {"method": "GET", "url": "/api/v1/users", "code": 200}},
  "type": "L7",
  "node_name": "node-1"
}
```

### 5.10 ClusterMesh

ClusterMesh connects multiple Kubernetes clusters into a single logical network.

```
Cluster A (us-east-1)          Cluster B (eu-west-1)
-----------------------        -----------------------
Pod: frontend (10.0.1.5)  ←──→  Pod: backend (10.0.2.8)

Without ClusterMesh: pods cannot directly address each other
                     must go through ingress/API gateway

With ClusterMesh:
  → Cross-cluster pod-to-pod connectivity
  → Global services (single VIP across multiple clusters)
  → Cross-cluster network policy
  → Shared identity management
```

**Implementation:**

```
Each cluster runs an etcd store for identity/policy data.
cilium-agents in each cluster connect to the remote etcd stores.
BPF maps are synchronized with remote cluster state.
Tunnel (VXLAN/Geneve) or direct routing for cross-cluster traffic.
```

**Global service (load balance across clusters):**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: backend
  annotations:
    service.cilium.io/global: "true"   # enable ClusterMesh global service
    service.cilium.io/shared: "true"   # share this service with other clusters
spec:
  selector:
    app: backend
  ports:
  - port: 8080
```

### 5.11 WireGuard Integration

Cilium can transparently encrypt all pod-to-pod traffic using WireGuard (kernel-native, eBPF-friendly VPN protocol).

```bash
# Enable WireGuard encryption in Cilium
helm upgrade cilium cilium/cilium \
  --set encryption.enabled=true \
  --set encryption.type=wireguard

# Each node gets a WireGuard keypair
# Cilium manages key distribution via K8s API
# All pod-to-pod traffic encrypted transparently
# No application changes required
# Performance: ~10% overhead vs ~30% for IPSec
```

---

## 6. Aya — Rust eBPF Framework

### 6.1 Why Aya

Aya is a Rust framework for writing and loading eBPF programs. It is written entirely in Rust (no C dependencies, no libbpf dependency).

```
C approach (libbpf):
  BPF program: C + clang + bpf-linker
  Loader:      C + libbpf (libelf, libz dependencies)
  Problem:     Two languages, complex build, C unsafe

Aya approach:
  BPF program: Rust (aya-bpf crate) + rustc (bpf target)
  Loader:      Rust (aya crate) — pure Rust, no C deps
  Advantage:   One language, Cargo build, Rust safety
```

**When to choose Aya:**

- You're building tools/infrastructure in Rust
- You want a single-language codebase
- You want Rust's safety guarantees in userspace code
- You're building Cilium-adjacent tooling

### 6.2 Architecture

```
aya-bpf crate         → for BPF-side code (no_std, runs in kernel)
  - macros: #[xdp], #[map], #[classifier]
  - map types: HashMap, Array, PerfEventArray, RingBuf, etc.
  - helper bindings: bpf_printk!, bpf_redirect, etc.

aya crate             → for userspace code (loads, attaches, reads maps)
  - Ebpf::load()
  - program.attach()
  - Map::try_from()

aya-log crate         → structured logging from BPF programs to userspace
aya-obj crate         → BPF ELF object parsing (internal)
```

### 6.3 Writing an XDP Program in Rust/Aya

**Setup:**

```bash
# Install bpf-linker
cargo install bpf-linker

# Install aya-tool (for generating bindings from BTF)
cargo install aya-tool

# Create a new Aya project
cargo generate --git https://github.com/aya-rs/aya-template
# Select: xdp program type
```

**Project structure:**

```
my-xdp-filter/
├── Cargo.toml                  # workspace
├── my-xdp-filter/              # userspace crate
│   ├── Cargo.toml
│   └── src/main.rs
├── my-xdp-filter-ebpf/         # eBPF crate (runs in kernel)
│   ├── Cargo.toml
│   └── src/main.rs
└── my-xdp-filter-common/       # shared types (maps, events)
    ├── Cargo.toml
    └── src/lib.rs
```

**Common types (`my-xdp-filter-common/src/lib.rs`):**

```rust
// #![no_std] because this runs in both kernel (no_std) and userspace
#![no_std]

// Shared between BPF program and userspace loader
#[repr(C)]
#[derive(Clone, Copy)]
pub struct PacketStats {
    pub packets: u64,
    pub bytes: u64,
}

// Required for aya map types
#[cfg(feature = "user")]
unsafe impl aya::Pod for PacketStats {}
```

**BPF program (`my-xdp-filter-ebpf/src/main.rs`):**

```rust
#![no_std]
#![no_main]

use aya_bpf::{
    bindings::xdp_action,
    macros::{map, xdp},
    maps::HashMap,
    programs::XdpContext,
};
use aya_log_ebpf::info;
use core::mem;
use my_xdp_filter_common::PacketStats;

// Network protocol header definitions
// (these would normally come from vmlinux bindings)
#[repr(C)]
struct EthHdr {
    h_dest:   [u8; 6],
    h_source: [u8; 6],
    h_proto:  u16,
}

#[repr(C)]
struct Ipv4Hdr {
    version_ihl: u8,
    tos:         u8,
    tot_len:     u16,
    id:          u16,
    frag_off:    u16,
    ttl:         u8,
    protocol:    u8,
    check:       u16,
    saddr:       u32,   // source IP
    daddr:       u32,   // destination IP
}

const ETH_P_IP: u16 = 0x0800;
const ETH_HDR_LEN: usize = mem::size_of::<EthHdr>();
const IPV4_HDR_LEN: usize = mem::size_of::<Ipv4Hdr>();

// Define maps using Aya macros
#[map(name = "BLOCKLIST")]
static mut BLOCKLIST: HashMap<u32, u64> =
    HashMap::<u32, u64>::with_max_entries(10240, 0);

// The XDP program — attached by the macro
#[xdp]
pub fn xdp_filter(ctx: XdpContext) -> u32 {
    match unsafe { try_xdp_filter(ctx) } {
        Ok(ret) => ret,
        Err(_)  => xdp_action::XDP_ABORTED,
    }
}

// Inline helper: safe bounds-checked pointer access
#[inline(always)]
unsafe fn ptr_at<T>(ctx: &XdpContext, offset: usize) -> Result<*const T, ()> {
    let start = ctx.data();
    let end   = ctx.data_end();
    let len   = mem::size_of::<T>();

    if start + offset + len > end {
        return Err(());
    }
    Ok((start + offset) as *const T)
}

unsafe fn try_xdp_filter(ctx: XdpContext) -> Result<u32, ()> {
    // Parse Ethernet header
    let eth = ptr_at::<EthHdr>(&ctx, 0)?;

    // Convert from big-endian (network) to host byte order
    if u16::from_be((*eth).h_proto) != ETH_P_IP {
        return Ok(xdp_action::XDP_PASS);
    }

    // Parse IPv4 header
    let ip = ptr_at::<Ipv4Hdr>(&ctx, ETH_HDR_LEN)?;
    let src = u32::from_be((*ip).saddr);

    // Check blocklist
    if let Some(count) = BLOCKLIST.get_ptr_mut(&src) {
        *count += 1;
        info!(&ctx, "BLOCKED: {:i} (hits: {})", src, *count);
        return Ok(xdp_action::XDP_DROP);
    }

    Ok(xdp_action::XDP_PASS)
}

// Panic handler (required for no_std)
#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {
    unsafe { core::hint::unreachable_unchecked() }
}
```

**Userspace loader (`my-xdp-filter/src/main.rs`):**

```rust
use anyhow::Context;
use aya::{
    include_bytes_aligned,
    maps::HashMap,
    programs::{Xdp, XdpFlags},
    Ebpf,
};
use aya_log::EbpfLogger;
use clap::Parser;
use log::{info, warn};
use std::net::Ipv4Addr;
use tokio::signal;

#[derive(Parser)]
struct Opt {
    #[clap(short, long, default_value = "eth0")]
    iface: String,
    
    #[clap(short, long, num_args = 0..)]
    block: Vec<Ipv4Addr>,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let opt = Opt::parse();
    env_logger::init();

    // Load the compiled BPF object (embedded at compile time)
    // include_bytes_aligned! ensures proper alignment for BPF ELF
    let mut ebpf = Ebpf::load(include_bytes_aligned!(
        "../../target/bpfel-unknown-none/release/my-xdp-filter"
    ))?;

    // Set up logging from BPF programs to userspace
    if let Err(e) = EbpfLogger::init(&mut ebpf) {
        warn!("failed to initialize eBPF logger: {}", e);
    }

    // Get the XDP program and attach it
    let program: &mut Xdp = ebpf
        .program_mut("xdp_filter")
        .unwrap()
        .try_into()?;
    
    program.load()?;
    program
        .attach(&opt.iface, XdpFlags::default())
        .context(format!("failed to attach XDP program to {}", opt.iface))?;
    
    info!("XDP filter attached to {}", opt.iface);

    // Populate the blocklist
    let mut blocklist: HashMap<_, u32, u64> =
        HashMap::try_from(ebpf.map_mut("BLOCKLIST").unwrap())?;

    for ip in &opt.block {
        let key = u32::from(*ip).to_be(); // network byte order
        blocklist.insert(key, 0, 0)?;
        info!("Blocking: {}", ip);
    }

    // Wait for Ctrl+C
    info!("Waiting for Ctrl-C...");
    signal::ctrl_c().await?;
    info!("Exiting...");

    Ok(())
}
```

**Build and run:**

```bash
# Build the BPF program (targeting BPF architecture)
cargo build --package my-xdp-filter-ebpf \
    --release \
    --target bpfel-unknown-none \
    -Z build-std=core

# Build the userspace program
cargo build --package my-xdp-filter --release

# Run (requires root or CAP_BPF + CAP_NET_ADMIN)
sudo ./target/release/my-xdp-filter \
    --iface eth0 \
    --block 192.168.1.100 \
    --block 10.0.0.1
```

### 6.4 Maps in Aya

```rust
// HashMap
#[map] static mut CONNECTIONS: HashMap<u32, ConnectionState> = HashMap::with_max_entries(65536, 0);

// LruHashMap
#[map] static mut LRU_CACHE: LruHashMap<u32, u64> = LruHashMap::with_max_entries(1024, 0);

// Array
#[map] static mut COUNTERS: Array<u64> = Array::with_max_entries(16, 0);

// PerCpuArray (one copy per CPU core, no locking)
#[map] static mut PER_CPU_STATS: PerCpuArray<u64> = PerCpuArray::with_max_entries(16, 0);

// PerfEventArray (send events to userspace)
#[map] static mut EVENTS: PerfEventArray<PacketEvent> = PerfEventArray::new(0);

// RingBuf (preferred over PerfEventArray for new code)
#[map] static mut RING: RingBuf = RingBuf::with_byte_size(4096 * 4096, 0);

// ProgramArray (tail calls)
#[map] static mut JUMP_TABLE: ProgramArray = ProgramArray::with_max_entries(8, 0);
```

### 6.5 TC Programs in Aya

```rust
use aya_bpf::{macros::classifier, programs::TcContext};
use aya_bpf::bindings::TC_ACT_OK;
use aya_bpf::bindings::TC_ACT_SHOT;

#[classifier]
pub fn tc_ingress(ctx: TcContext) -> i32 {
    match unsafe { try_tc_ingress(ctx) } {
        Ok(ret) => ret,
        Err(_)  => TC_ACT_SHOT,
    }
}

unsafe fn try_tc_ingress(ctx: TcContext) -> Result<i32, ()> {
    // TC context gives you sk_buff access
    // You can read/write arbitrary bytes in the packet
    let proto = u16::from_be(ctx.load::<u16>(12)?);  // ethertype at offset 12
    
    if proto != 0x0800 {  // not IPv4
        return Ok(TC_ACT_OK);
    }

    // Read source IP (at offset 14 + 12 = 26 in ethernet frame)
    let src_ip = u32::from_be(ctx.load::<u32>(26)?);
    
    // Process...
    Ok(TC_ACT_OK)
}
```

---

## 7. Go eBPF — cilium/ebpf Library

The `github.com/cilium/ebpf` library is the canonical Go library for eBPF. It is what Cilium itself uses internally.

**Key packages:**

```
cilium/ebpf               → core: load programs, manage maps
cilium/ebpf/link          → attach programs (xdp, tc, kprobe, etc.)
cilium/ebpf/ringbuf       → read from BPF ring buffers
cilium/ebpf/perf          → read from perf event arrays
cilium/ebpf/rlimit        → manage memlock limits
cilium/ebpf/btf           → BTF type inspection
```

**Complete Go XDP loader:**

```go
package main

import (
    "encoding/binary"
    "fmt"
    "log"
    "net"
    "os"
    "os/signal"
    "syscall"
    "time"

    "github.com/cilium/ebpf"
    "github.com/cilium/ebpf/link"
    "github.com/cilium/ebpf/rlimit"
)

// bpfObjects is generated by bpf2go:
// go generate will run:
//   bpf2go -cc clang XdpFilter xdp_filter.bpf.c
// and generate xdp_filter_bpfel.go with:
//   type xdpFilterObjects struct {
//       xdpFilterPrograms
//       xdpFilterMaps
//   }
//go:generate go run github.com/cilium/ebpf/cmd/bpf2go -cc clang XdpFilter xdp_filter.bpf.c

func main() {
    ifname := "eth0"
    if len(os.Args) > 1 {
        ifname = os.Args[1]
    }

    iface, err := net.InterfaceByName(ifname)
    if err != nil {
        log.Fatalf("Interface %s not found: %v", ifname, err)
    }

    // Remove the memlock limit (required for BPF on older kernels)
    // On kernels >= 5.11, BPF memory is charged to cgroup memory
    if err := rlimit.RemoveMemlock(); err != nil {
        log.Fatal("Failed to remove memlock:", err)
    }

    // Load pre-compiled BPF programs and maps into the kernel
    objs := xdpFilterObjects{}
    if err := loadXdpFilterObjects(&objs, nil); err != nil {
        log.Fatalf("Loading BPF objects: %v", err)
    }
    defer objs.Close()

    // Attach the XDP program to the network interface
    xdpLink, err := link.AttachXDP(link.XDPOptions{
        Program:   objs.XdpFilter,
        Interface: iface.Index,
    })
    if err != nil {
        log.Fatalf("Attaching XDP: %v", err)
    }
    defer xdpLink.Close()

    log.Printf("XDP program attached to %s", ifname)

    // Add some IPs to the blocklist
    blockIPs := []string{"192.168.1.100", "10.0.0.1"}
    for _, ipStr := range blockIPs {
        ip := net.ParseIP(ipStr).To4()
        key := binary.BigEndian.Uint32(ip) // network byte order
        var value uint64 = 0
        if err := objs.Blocklist.Put(key, value); err != nil {
            log.Printf("Failed to block %s: %v", ipStr, err)
        } else {
            log.Printf("Blocked: %s", ipStr)
        }
    }

    // Poll stats every second
    ticker := time.NewTicker(time.Second)
    defer ticker.Stop()

    sig := make(chan os.Signal, 1)
    signal.Notify(sig, syscall.SIGINT, syscall.SIGTERM)

    fmt.Printf("%-12s %-12s %-12s %-12s %-12s\n",
        "ABORTED", "DROP", "PASS", "TX", "REDIRECT")

    for {
        select {
        case <-ticker.C:
            // Read per-CPU stats and aggregate
            var allCpuValues []uint64
            var totals [5]uint64
            for action := uint32(0); action < 5; action++ {
                // For PerCpuArray, Get returns values for all CPUs
                if err := objs.Stats.LookupWithFlags(
                    action,
                    &allCpuValues,
                    ebpf.LookupLock,
                ); err == nil {
                    for _, v := range allCpuValues {
                        totals[action] += v
                    }
                }
            }
            fmt.Printf("\r%-12d %-12d %-12d %-12d %-12d",
                totals[0], totals[1], totals[2], totals[3], totals[4])

        case <-sig:
            fmt.Println("\nExiting...")
            return
        }
    }
}
```

**Ring buffer reading (Go):**

```go
import "github.com/cilium/ebpf/ringbuf"

// Create a ring buffer reader
reader, err := ringbuf.NewReader(objs.Events)
if err != nil {
    log.Fatal(err)
}
defer reader.Close()

// Read events in a goroutine
go func() {
    for {
        record, err := reader.Read()
        if err != nil {
            if errors.Is(err, ringbuf.ErrClosed) {
                return
            }
            continue
        }
        
        // Parse the event (must match the C struct layout)
        var event PacketEvent
        if err := binary.Read(
            bytes.NewReader(record.RawSample),
            binary.LittleEndian,
            &event,
        ); err != nil {
            continue
        }
        
        fmt.Printf("Event: src=%s dst=%s\n",
            net.IP(event.SrcIP[:]).String(),
            net.IP(event.DstIP[:]).String())
    }
}()
```

---

## 8. Complete Roadmap

### Phase 0 — Kernel & Systems Foundation (Weeks 1-2)

You have this from your kernel build work. Make sure you understand:

```
[ ] Linux network stack: sk_buff, netif_receive_skb, protocol layers
[ ] Kernel modules: writing, loading (.ko files)
[ ] System calls: strace, how syscalls work
[ ] Memory: virtual vs physical, DMA, page cache
[ ] Concurrency: spinlocks, RCU, per-CPU variables
[ ] cgroups and namespaces (container primitives)
[ ] QEMU-based kernel debugging with GDB
```

### Phase 1 — BPF Core (Weeks 3-6)

```
[ ] Install BPF tools:
    sudo apt install -y bpftools linux-headers-$(uname -r) libbpf-dev clang llvm

[ ] Read and understand:
    - kernel/bpf/verifier.c (understand the logic, not every line)
    - tools/lib/bpf/libbpf.c (understand the loading flow)
    - samples/bpf/ in kernel source (reference programs)

[ ] Build these programs yourself (no copy-paste):
    - Hello World: kprobe on sys_execve, print comm to trace_pipe
    - Syscall counter: count calls per PID using a hash map
    - Packet counter: XDP program counting packets by protocol
    - Connection tracker: track TCP connections using sock_ops

[ ] Tools mastery:
    bpftool prog list          # list loaded programs
    bpftool prog show id X     # inspect a program
    bpftool prog dump xlated id X  # disassemble BPF bytecode
    bpftool prog dump jited id X   # disassemble JIT-compiled native code
    bpftool map list
    bpftool map dump id X
    bpftool net list           # show XDP/TC attachments

[ ] Understand verifier errors:
    - Load a program that the verifier rejects
    - Read the rejection message
    - Fix it
    - Repeat until you can predict verifier behavior
```

### Phase 2 — XDP Mastery (Weeks 7-10)

```
[ ] Build these XDP programs:
    - Packet counter (per-protocol, per-IP)
    - IP blocklist (with LRU map, userspace management)
    - ICMP echo responder (XDP_TX, modify packet in place)
    - Simple L3 router (parse IP, lookup route, redirect)
    - SYN cookie responder (SYN flood mitigation)
    - Port knocking implementation

[ ] Understand performance:
    - Use pktgen or moongen to generate traffic
    - Measure pps with and without your XDP program
    - Profile using perf stat, flamegraphs

[ ] Advanced topics:
    - AF_XDP: zero-copy packet processing to userspace
    - DEVMAP: multi-interface redirect
    - Tail calls: split complex programs across multiple BPF progs
    - BPF-to-BPF function calls

[ ] Real-world XDP project:
    Build a stateless load balancer:
      - One XDP program per frontend server
      - Parse L4 5-tuple
      - Hash to select backend
      - Rewrite dst IP+MAC
      - bpf_redirect to backend interface
```

### Phase 3 — Cilium Internals (Weeks 11-16)

```
[ ] Setup:
    - Install kind (Kubernetes in Docker) or minikube
    - Install Cilium: helm install cilium cilium/cilium
    - Install Hubble CLI
    - Verify: cilium status, cilium connectivity test

[ ] Explore the datapath:
    bpftool prog list | grep cilium        # see all cilium BPF programs
    bpftool net list                        # see attachments
    ls /sys/fs/bpf/tc/globals/             # see pinned maps
    bpftool map list | grep cilium         # see all maps
    bpftool map dump pinned /sys/fs/bpf/tc/globals/cilium_ipcache

[ ] Read Cilium source code (cilium/cilium on GitHub):
    bpf/bpf_lxc.c      → per-endpoint datapath (most important file)
    bpf/bpf_host.c     → host network datapath
    bpf/bpf_xdp.c      → XDP layer
    bpf/lib/lb.h       → load balancer implementation
    bpf/lib/policy.h   → policy enforcement
    bpf/lib/nat.h      → NAT implementation
    bpf/lib/conntrack.h → connection tracking

[ ] Understand the maps:
    cilium_ipcache      → IP address → security identity
    cilium_policy       → (identity, port, proto) → allow/deny
    cilium_lb4_services → service VIP → service metadata
    cilium_lb4_backends → service id → backend list
    cilium_ct4_global   → connection tracking table

[ ] Contribute:
    - Find a "good first issue" on Cilium GitHub
    - Fix a documentation issue
    - Write a test for an existing feature
    - Implement a small BPF optimization

[ ] Advanced Cilium topics:
    - Bandwidth Manager (BPF-based tc-qdisc rate limiting)
    - Egress Gateway (NAT for egress traffic)
    - BGP Control Plane
    - Service Mesh without sidecars (BPF-based mTLS)
    - SNAT / Masquerading implementation
```

### Phase 4 — Aya & Rust eBPF (Weeks 17-20)

```
[ ] Setup Aya environment:
    rustup target add bpfel-unknown-none
    cargo install bpf-linker
    cargo install aya-tool

[ ] Port your XDP programs from C to Rust/Aya
[ ] Build a Cilium-compatible component in Rust
[ ] Understand the Rust/Aya ecosystem:
    - aya (core loader)
    - aya-bpf (kernel-side)
    - aya-log (logging)
    - retis (packet capture using Aya)
    - pulsar (security monitoring using Aya)
```

### Phase 5 — Cloud Native Integration (Weeks 21-26)

```
[ ] Kubernetes networking deep dive:
    - How CNI works (read: github.com/containernetworking/cni)
    - Pod networking model
    - Service ClusterIP, NodePort, LoadBalancer
    - Ingress and Gateway API

[ ] Observability stack:
    - Hubble → Prometheus → Grafana pipeline
    - Custom Hubble exporters
    - OpenTelemetry integration with eBPF

[ ] Service mesh:
    - Understand Cilium's sidecarless service mesh
    - Compare with Istio (sidecar) approach
    - mTLS with eBPF

[ ] Projects to build:
    - Custom network policy enforcer using cilium/ebpf + Go
    - Real-time DDoS mitigation using XDP + Cilium integration
    - Custom Hubble plugin for L7 protocol
    - eBPF-based container security monitor (like Falco but custom)

[ ] Contribute to the ecosystem:
    - cilium/cilium
    - cilium/ebpf (Go library)
    - aya-rs/aya
    - bpftrace (scripting language for eBPF)
```

---

## 9. Real Projects to Build

These are concrete projects that develop real skills and are portfolio-worthy:

### Project 1: eBPF Firewall (C + Go)
```
BPF side: XDP program with:
  - IP blocklist (LRU hash map)
  - Port blocklist
  - Rate limiting per source IP (token bucket in BPF)
  - Event reporting via ring buffer

Userspace (Go): REST API to:
  - Add/remove blocked IPs
  - Query stats
  - Stream events via WebSocket
  - Persist config to JSON

Skills: XDP, maps, ring buffer, Go eBPF, REST API
```

### Project 2: Connection Tracker
```
BPF side: sock_ops + sk_skb programs tracking:
  - TCP connection open/close
  - Bytes transferred per connection
  - RTT samples
  - Retransmit count

Userspace: connection table with process-to-connection mapping

Skills: sock_ops, socket maps, process introspection via kprobes
```

### Project 3: Custom Metrics Exporter for Prometheus
```
BPF side: TC programs on pod veth interfaces measuring:
  - Packets in/out per pod
  - Bytes in/out per pod
  - Dropped packets

Userspace (Go): Prometheus exporter reading BPF per-CPU maps
                Runs as a DaemonSet in K8s

Skills: TC programs, per-CPU maps, Kubernetes DaemonSet, Prometheus
```

### Project 4: XDP Load Balancer
```
BPF side (XDP): Stateless L4 load balancer
  - Parse L3/L4 headers
  - Consistent hash on 5-tuple
  - DNAT to backend
  - MAC rewrite
  - Redirect via DEVMAP

Userspace (Go): Health checking, backend management

Skills: XDP redirect, DEVMAP, packet modification, checksum updates
```

### Project 5: eBPF-based Security Monitor (Rust/Aya)
```
BPF side:
  - LSM hooks: monitor file access, network connect, exec
  - Tracepoints: sys_enter_execve, sys_enter_connect
  - Kprobes: key kernel functions

Userspace (Rust): Rule engine, alert system, audit log

Skills: LSM BPF, kprobes, tracepoints, Aya, security engineering
```

---

## 10. Reference: Key Kernel Source Paths

```
BPF Core:
  kernel/bpf/                  → verifier, syscall, map implementations
  kernel/bpf/verifier.c        → THE verifier (~20k lines)
  kernel/bpf/syscall.c         → bpf() syscall handler
  kernel/bpf/core.c            → BPF interpreter
  arch/x86/net/bpf_jit_comp.c  → x86_64 JIT compiler

BPF Maps:
  kernel/bpf/hashtab.c         → BPF_MAP_TYPE_HASH
  kernel/bpf/arraymap.c        → BPF_MAP_TYPE_ARRAY
  kernel/bpf/lpm_trie.c        → BPF_MAP_TYPE_LPM_TRIE
  kernel/bpf/ringbuf.c         → BPF_MAP_TYPE_RINGBUF

XDP:
  net/core/filter.c            → BPF helpers for networking
  net/core/dev.c               → netif_receive_skb, XDP dispatch
  drivers/net/virtio_net.c     → virtio XDP native support (good reference)
  drivers/net/ethernet/intel/  → Intel NIC XDP support

Cilium-relevant kernel features:
  net/sched/cls_bpf.c          → TC BPF classifier
  net/sched/act_bpf.c          → TC BPF action
  kernel/bpf/sockmap.c         → socket maps, SK_SKB
  net/ipv4/udp.c               → sk_lookup integration

Headers (read these — they define the public BPF API):
  include/uapi/linux/bpf.h     → ALL BPF types, map types, prog types
  include/uapi/linux/bpf_common.h
  include/linux/bpf.h          → kernel-internal BPF types

Tools and samples:
  tools/lib/bpf/               → libbpf source
  tools/bpf/bpftool/           → bpftool source
  samples/bpf/                 → official kernel BPF samples
  tools/testing/selftests/bpf/ → BPF kernel self-tests (excellent reference)
```

---

## Essential Reading

**Papers:**
- "The BSD Packet Filter: A New Architecture for User-level Packet Capture" (McCanne, Jacobson 1992) — original BPF
- "Fast Packet Processing with eBPF and XDP" — comprehensive academic overview

**Documentation:**
- `Documentation/bpf/` in the Linux kernel source tree
- `https://docs.kernel.org/bpf/`
- Cilium documentation: `https://docs.cilium.io`
- BPF reference guide: `https://cilium.io/blog/2021/05/11/cni-benchmark/`

**Key people to follow (GitHub/blogs):**
- Alexei Starovoitov (eBPF creator, Meta) — kernel commits
- Daniel Borkmann (eBPF co-maintainer, Isovalent) — kernel commits + talks
- Thomas Graf (Cilium creator, Isovalent) — architecture posts
- Brendan Gregg (Netflix) — BPF performance tools, bpftrace

**Conferences:**
- Linux Plumbers Conference (LPC) — BPF track
- KubeCon — Cilium/eBPF talks
- eBPF Summit (free, online) — focused eBPF content

---

*This document covers the full stack from kernel BPF internals to production Cilium deployments. Each section deserves weeks of focused study. Follow the roadmap phases in order — each builds on the previous. The key insight is that eBPF, XDP, and Cilium are not separate technologies — they are one unified programmability layer built into the Linux kernel, and Cilium is the most sophisticated production user of that layer.*

This will be a large, multi-section document. Building it now — this covers everything from kernel internals to production Cilium deployments.Here's what's inside — ~610 lines across 10 major sections:

**Structure of the guide:**

Section 1-2 builds the mental model — why the traditional network stack fails at scale and why eBPF/XDP/Cilium exist as a unified answer, not separate tools.

Section 3 (eBPF) covers the full kernel machinery: the BPF VM with all 11 registers, the verifier's symbolic execution algorithm, why NULL checks are mandatory, the JIT compiler, every map type with when to use each, all key helper functions categorized, BTF and CO-RE with concrete macro examples, libbpf loading pipeline, BPF skeleton pattern, the bpf() syscall, and object pinning.

Section 4 (XDP) covers the execution model showing exactly where XDP runs vs the traditional path, all three modes (native/generic/offload) with performance numbers, all 5 return codes with their semantics, a complete working C program (XDP IP blocklist + stats counter with full Makefile), and AF_XDP zero-copy with a Go example.

Section 5 (Cilium) covers the full architecture, how the agent works, the eBPF datapath per endpoint, CNI integration sequence, the identity-based security model (why it beats IP-based iptables), CiliumNetworkPolicy including L7 HTTP rules, eBPF load balancing replacing kube-proxy (with socket-level DNAT code), Hubble observability, ClusterMesh, and WireGuard encryption.

Section 6 (Aya/Rust) has a complete Rust XDP program with the full project structure, all map types, and a TC classifier example.

Section 7 (Go/cilium-ebpf) has a complete Go loader using bpf2go and ring buffer reading.

Section 8 is the 26-week roadmap across 5 phases with specific commands to run and programs to build. Section 9 has 5 concrete portfolio projects with full specs.