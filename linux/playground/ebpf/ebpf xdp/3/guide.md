Now I'll build the entire system. Let me create all the code files first, then give you the complete explanation.Now here is the complete world-class explanation, exactly as a senior kernel developer would teach you:

---

## 🧠 CONCEPT MAP — What You Are Building

Before a single line of code, understand the full mental model:

```
╔══════════════════════════════════════════════════════════════════════╗
║                  LINUX NETWORK STACK (SIMPLIFIED)                  ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  [ Physical Wire / NIC ]                                             ║
║          │                                                           ║
║          ▼  (DMA: Direct Memory Access — NIC writes to RAM)         ║
║  ┌───────────────────┐                                               ║
║  │   NIC Ring Buffer │  ← Packet arrives here first                 ║
║  └────────┬──────────┘                                               ║
║           │                                                          ║
║           ▼  ◄════════ XDP HOOK FIRES HERE (earliest possible!)     ║
║  ┌────────────────────────────────────────────────────────────┐      ║
║  │           YOUR xdp_security_prog()                         │      ║
║  │   Reads raw packet bytes. Decides in ~10ns:                │      ║
║  │   XDP_DROP   → Discarded in driver. No kernel overhead.    │      ║
║  │   XDP_PASS   → Continue to kernel network stack.           │      ║
║  │   XDP_TX     → Transmit back out same interface.           │      ║
║  │   XDP_REDIRECT → Send to different iface/CPU/socket.       │      ║
║  └────────────────────────┬───────────────────────────────────┘      ║
║                           │ (only XDP_PASS reaches here)             ║
║                           ▼                                          ║
║  ┌─────────────────────────────────────────────────────────────┐     ║
║  │           struct sk_buff (skb) ALLOCATION                   │     ║
║  │  ← This is expensive! XDP avoids it for dropped packets.   │     ║
║  └────────────────────────┬────────────────────────────────────┘     ║
║                           │                                          ║
║                           ▼                                          ║
║  [ TC (Traffic Control) ]  ← Another BPF hook point                  ║
║  [ Netfilter / iptables ]  ← Traditional firewall layer              ║
║  [ Socket Layer ]                                                     ║
║  [ Application (recv()) ]                                            ║
╚══════════════════════════════════════════════════════════════════════╝

WHY XDP IS REVOLUTIONARY:
  iptables drops a packet: ~3 microseconds (needs full skb, netfilter traversal)
  XDP drops a packet:      ~50 nanoseconds (before skb, before any allocation)
  → XDP is 60x faster for packet filtering
```

---

## 📦 WHAT IS eBPF? — The Foundation

```
KEY CONCEPT: eBPF (extended Berkeley Packet Filter)
═══════════════════════════════════════════════════════════

Traditional way to add kernel functionality:
  Write kernel module → Compile → insmod → ONE BUG = kernel panic

eBPF way:
  Write BPF program → Compile to BPF bytecode → Load via bpf() syscall
  → VERIFIER checks every instruction → JIT compiles to native code
  → Runs IN kernel but CANNOT crash it

Think of eBPF as a "safe sandbox inside the kernel":
  ┌─────────────────────────────────────────────────────────┐
  │                 LINUX KERNEL                            │
  │                                                         │
  │  ┌───────────────────────────────────────────────────┐  │
  │  │            BPF VIRTUAL MACHINE                    │  │
  │  │                                                   │  │
  │  │  • 11 registers (r0-r10)                          │  │
  │  │  • 512-byte stack                                 │  │
  │  │  • Access kernel memory via APPROVED helpers only │  │
  │  │  • No loops unless bounded (verifier counts iters)│  │
  │  │  • No pointer arithmetic outside packet bounds    │  │
  │  │                                                   │  │
  │  │  YOUR CODE RUNS HERE — fast as native code        │  │
  │  │  (JIT: BPF bytecode → x86/ARM instructions)       │  │
  │  └───────────────────────────────────────────────────┘  │
  └─────────────────────────────────────────────────────────┘

The BPF Verifier (linux/kernel/bpf/verifier.c):
  • Runs at LOAD TIME — not at runtime
  • Does static analysis of ALL possible code paths
  • If ANY path is unsafe → REJECT (program never runs)
  • This is why eBPF cannot crash the kernel
```

---

## 🏗️ COMPLETE SYSTEM ARCHITECTURE

```
┌──────────────────────────────────────────────────────────────────────┐
│                     FILE STRUCTURE                                   │
│                                                                      │
│  xdp-security/                                                       │
│  ├── kern/                                                           │
│  │   ├── xdp_security.bpf.c   ← YOU WRITE THIS (kernel BPF, C)     │
│  │   ├── xdp_security.bpf.o   ← clang compiles this (BPF ELF)      │
│  │   └── vmlinux.h            ← bpftool generates (kernel structs)  │
│  ├── user/                                                           │
│  │   ├── xdp_security.skel.h  ← bpftool generates (type-safe API)  │
│  │   ├── xdp_loader.c         ← YOU WRITE THIS (userspace C)       │
│  │   └── xdp_loader           ← gcc compiles this (x86 binary)     │
│  ├── rust/                                                           │
│  │   ├── xdp-security-ebpf/   ← Rust BPF kernel program (aya-ebpf) │
│  │   └── xdp-security/        ← Rust userspace loader (aya)        │
│  ├── bugs/                                                           │
│  │   └── xdp_bugs.bpf.c       ← intentional bugs for learning      │
│  ├── tests/                                                          │
│  │   └── run_tests.sh         ← integration test suite              │
│  └── Makefile                 ← orchestrates entire build           │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 BUILD FLOW (Decision Tree + Flowchart)

```
BUILD DECISION FLOWCHART
═════════════════════════════════════════════════════════

START
  │
  ▼
Do you have clang/bpftool installed?
  ├─NO──→ sudo apt install clang llvm libbpf-dev bpftool
  │         linux-headers-$(uname -r)
  └─YES─┐
        │
        ▼
  Step 1: Generate vmlinux.h
  ┌──────────────────────────────────────────────────────┐
  │  make vmlinux                                        │
  │  (bpftool btf dump file /sys/kernel/btf/vmlinux      │
  │   format c > kern/vmlinux.h)                         │
  │                                                      │
  │  KEY CONCEPT — "BTF" (BPF Type Format):              │
  │  The running kernel exports its struct definitions   │
  │  as BTF debug info at /sys/kernel/btf/vmlinux.       │
  │  We dump these as C headers → vmlinux.h.             │
  │  This gives us ALL kernel structs without            │
  │  including the entire kernel source.                 │
  └────────────────────┬─────────────────────────────────┘
                       │
                       ▼
  Step 2: Compile BPF program
  ┌──────────────────────────────────────────────────────┐
  │  clang -target bpf -g -O2                           │
  │        -c kern/xdp_security.bpf.c                   │
  │        -o kern/xdp_security.bpf.o                   │
  │                                                      │
  │  -target bpf  : emit BPF bytecode (not x86)         │
  │  -g           : include BTF info (enables CO-RE)    │
  │  -O2          : optimize (BPF verifier needs it)    │
  │                                                      │
  │  Output: ELF file with sections:                    │
  │    .text      : BPF bytecode instructions           │
  │    .maps      : map definitions                     │
  │    .rodata    : read-only data                      │
  │    .BTF       : type information                    │
  │    license    : GPL string                          │
  └────────────────────┬─────────────────────────────────┘
                       │
                       ▼
  Step 3: Generate skeleton header
  ┌──────────────────────────────────────────────────────┐
  │  bpftool gen skeleton kern/xdp_security.bpf.o        │
  │           > user/xdp_security.skel.h                 │
  │                                                      │
  │  KEY CONCEPT — "Skeleton":                           │
  │  An auto-generated C header that gives you:          │
  │  - Type-safe access to your maps                    │
  │  - Type-safe handle to your programs                │
  │  - Functions: __open(), __load(), __destroy()        │
  │  No more raw bpf() syscalls with integer FDs.        │
  └────────────────────┬─────────────────────────────────┘
                       │
                       ▼
  Step 4: Compile userspace loader
  ┌──────────────────────────────────────────────────────┐
  │  gcc -g -O2 user/xdp_loader.c                       │
  │      -o xdp_loader                                   │
  │      -lbpf -lelf -lz                                 │
  │                                                      │
  │  -lbpf : link libbpf (BPF loading library)          │
  │  -lelf : link libelf (reads ELF object files)       │
  │  -lz   : link zlib  (decompresses BTF data)         │
  └────────────────────┬─────────────────────────────────┘
                       │
                       ▼
  DONE: ./xdp_loader eth0
```

---

## 🔬 BPF VERIFIER — How It Thinks

```
KEY CONCEPT: The Verifier is the heart of eBPF safety.
Understanding it is the difference between amateur and elite.

VERIFIER STATE MACHINE:
════════════════════════════════════════════════════════════

For every instruction, the verifier tracks:
  • Type of each register (scalar, ptr_to_ctx, ptr_to_map_value, ...)
  • Range of each register's value (min/max bounds)
  • Whether a register is NULL or not

Example: Our bounds check
─────────────────────────
C code:                           Verifier tracks:
                                  ─────────────────
eth = data;                       R1 = ptr_to_ctx
                                  eth = ptr(pkt_start)

if ((eth+1) > data_end)           verifier: checks if sizeof(ethhdr)
    return XDP_DROP;                        fits before data_end
                                  ✓ After this check: eth is SAFE

ip = (struct iphdr *)(eth+1);     ip = ptr(pkt_start + 14)

                                  Without bounds check:
ip->saddr   ← BUG!               verifier: "R? invalid mem access 'inv'"
                                            REJECT!

if ((ip+1) > data_end)            After this check:
    return XDP_DROP;              ip is ptr_to_pkt (BOUNDED) → SAFE

ip->saddr   ← CORRECT!           verifier: "bounded pointer read: OK"

VERIFIER ERROR TAXONOMY:
  "invalid mem access 'inv'"     → Unbounded pointer dereference
  "R? stack pointer arithmetic"  → Stack pointer went negative/OOB
  "back-edge from X to Y"        → Unbounded loop (verifier rejects)
  "program too large"            → Exceeded 1M instruction limit
  "cannot call GPL-only function"→ Program license is not GPL
  "BPF_CALL_ARG_INVALID"        → Wrong argument type to helper
```

---

## 🗺️ BPF MAPS — Shared Memory Between Kernel & Userspace

```
KEY CONCEPT: BPF Maps
═════════════════════════════════════════════════════════

Maps are the ONLY way for BPF programs to:
  1. Persist state across invocations
  2. Communicate with userspace

MAP TYPES WE USE AND WHY:
──────────────────────────────────────────────────────────
┌─────────────────────┬──────────────┬────────────────────┐
│ Map Type            │ Use Case     │ Why This Type?     │
├─────────────────────┼──────────────┼────────────────────┤
│ HASH                │ ip_blocklist │ O(1) lookup by IP  │
│                     │ ip_allowlist │ Exact match only   │
├─────────────────────┼──────────────┼────────────────────┤
│ LRU_HASH            │ pkt_rate_map │ Auto-evict old IPs │
│                     │ syn_flood_map│ Prevent memory fill│
├─────────────────────┼──────────────┼────────────────────┤
│ PERCPU_ARRAY        │ xdp_stats    │ No lock contention │
│                     │              │ Each CPU its own   │
│                     │              │ counter slot       │
└─────────────────────┴──────────────┴────────────────────┘

KEY CONCEPT — "LRU" (Least Recently Used):
  When a map with max_entries=100000 is full,
  LRU_HASH evicts the entry that was accessed LEAST recently.
  This prevents a memory exhaustion attack where an attacker
  sends packets from 100001 unique source IPs to fill the map.
  Regular HASH would return -E2BIG and fail silently.

KEY CONCEPT — "PERCPU_ARRAY":
  Problem: Every CPU increments the same stats counter simultaneously.
  Solution: Give each CPU its own copy → no atomic ops needed.
  Cost:     More memory (n_cpus × sizeof(value)).
  Userspace reads: must sum across all CPUs (see print_stats()).

MAP ACCESS FLOW:
  ┌─────────────────┐  bpf_map_lookup_elem()  ┌──────────────┐
  │  BPF Program    │ ──────────────────────► │   BPF Map    │
  │  (kernel side)  │ ◄────────────────────── │  (kernel     │
  └─────────────────┘  returns ptr or NULL    │   memory)    │
                                              └──────┬───────┘
  ┌─────────────────┐  bpf_map_update_elem()         │
  │  Userspace      │ ──────────────────────► via bpf() syscall
  │  (xdp_loader)   │                        (file descriptor)
  └─────────────────┘
```

---

## 🐛 BUG DEMONSTRATION & FIX

```
╔══════════════════════════════════════════════════════════════════════╗
║  BUG #1 — CODE BUG (Verifier Rejects at Load Time)                 ║
╚══════════════════════════════════════════════════════════════════════╝

BEFORE (broken):
─────────────────────────────────────────────────────────
  struct iphdr *ip = (struct iphdr *)(eth + 1);
  // NO BOUNDS CHECK HERE
  __u32 src_ip = ip->saddr;   ← VERIFIER REJECTS THIS

WHAT THE VERIFIER SEES:
  Instruction 13: r3 = *(u32 *)(r2 + 12)   ; reading ip->saddr
  Register R2 is type=pkt_ptr, but its maximum offset is
  only proven up to sizeof(ethhdr) = 14 bytes.
  ip is at offset 14. ip->saddr is at offset 14+12 = 26.
  Verifier cannot prove packet is at least 26 bytes long.
  → ERROR: "R2 invalid mem access 'inv'" → LOAD REJECTED

HOW TO DEBUG:
  $ sudo bpftool prog load xdp_bugs.bpf.o /sys/fs/bpf/test 2>&1
  libbpf: -- BEGIN PROG LOAD LOG --
  0: (61) r1 = *(u32 *)(r1 +4)
  ...
  13: (61) r3 = *(u32 *)(r2 +12)
      R2 invalid mem access 'inv'
  processed 13 insns ... FAILED

AFTER (fixed):
─────────────────────────────────────────────────────────
  struct iphdr *ip = (struct iphdr *)(eth + 1);
  if ((void *)(ip + 1) > data_end)    ← ADD THIS
      return XDP_DROP;
  __u32 src_ip = ip->saddr;           ← NOW SAFE

WHY THIS WORKS:
  After the if-check, the verifier knows:
  "data must be at least eth(14) + iphdr(20) = 34 bytes"
  ip->saddr at offset 26 is within proven range → ACCEPTED


╔══════════════════════════════════════════════════════════════════════╗
║  BUG #2 — LOGIC BUG (Silent Wrong Behavior at Runtime)             ║
╚══════════════════════════════════════════════════════════════════════╝

BEFORE (broken):
─────────────────────────────────────────────────────────
  if (eth->h_proto != ETH_P_IP)     ← WRONG: host byte order
      return XDP_PASS;

BYTE ORDER DIAGRAM:
  IPv4 ethertype value: 0x0800

  In memory (network / big-endian):   0x08  0x00
  In memory (host / little-endian):   0x00  0x08

  ETH_P_IP (C constant, host order):  0x0800 = 2048 decimal
  eth->h_proto (from packet):         0x0008 = 8 decimal (on x86)

  2048 != 8 → condition always TRUE → always XDP_PASS → BLOCKLIST IGNORED

DIAGNOSIS via bpf_printk:
  Add: bpf_printk("proto=%x want=%x\n", eth->h_proto, ETH_P_IP);
  cat /sys/kernel/debug/tracing/trace_pipe
  Output: proto=8 want=2048    ← MISMATCH REVEALED

DIAGNOSIS via bpftool:
  $ sudo bpftool map dump name ip_blocklist
  # Shows IPs in map, but dropped_blocklist counter stays 0
  # Confirms: map has entries but XDP never reaches the check

AFTER (fixed):
─────────────────────────────────────────────────────────
  if (eth->h_proto != bpf_htons(ETH_P_IP))  ← CORRECT
      return XDP_PASS;

  bpf_htons(0x0800) = 0x0008 on little-endian → matches eth->h_proto ✓

MENTAL RULE:
  Network fields → ALWAYS compare with bpf_htons() / bpf_ntohs()
  Map keys derived from packet → store consistently (pick one order, keep it)
```

---

## 🔧 HOW TO LOAD INTO THE KERNEL

```
STEP-BY-STEP LOADING PROCEDURE
═════════════════════════════════════════════════════════

1. Install prerequisites:
   sudo apt update
   sudo apt install -y \
     clang llvm \
     libbpf-dev \
     linux-headers-$(uname -r) \
     linux-tools-$(uname -r) \
     bpftool \
     iproute2

2. Generate vmlinux.h:
   make vmlinux
   # Creates kern/vmlinux.h from running kernel's BTF

3. Build everything:
   make all

4. (Safe) Test on loopback with SKB mode:
   sudo make load IFACE=lo
   # Loopback doesn't support native XDP → use --mode skb

5. (Production) Native driver mode on real interface:
   sudo ./xdp_loader eth0
   # Requires NIC driver with XDP native support
   # Supported: Intel ixgbe/i40e, Mellanox mlx4/mlx5, virtio-net

6. Verify attachment:
   sudo bpftool net show dev eth0
   # Output:
   # xdp:
   #         xdp_security prog_id 42 mode native

7. Block an IP manually:
   sudo ./xdp_loader eth0 --block 192.168.1.100

8. Watch stats:
   # The loader prints stats every 2s with live display

9. Check debug trace:
   sudo cat /sys/kernel/debug/tracing/trace_pipe
   # Shows bpf_printk() output from XDP program

10. Detach:
    sudo ip link set eth0 xdp off
    # OR: kill the loader (it detaches on exit via SIGINT handler)
```

---

## 🦀 RUST vs C — Key Differences

```
C (libbpf) Approach                    Rust (aya) Approach
═══════════════════════════════════════════════════════════
clang → .bpf.o (BPF ELF)              cargo build → BPF ELF (embedded in bin)
bpftool gen skeleton → .skel.h         aya macros (#[map], #[xdp])
gcc + libbpf → x86 loader binary       cargo build → x86 Rust binary

Kernel side:
  #include <linux/bpf.h>               #![no_std] #![no_main]
  SEC("xdp") int func(xdp_md *ctx)    #[xdp] pub fn func(ctx: XdpContext)
  BPF_MAP_TYPE_HASH struct { ... }     #[map] static MAP: HashMap<u32, u8>

Safety:
  Unsafe by default (C pointers)       unsafe{} required for raw pointers
  Verifier is the safety net           Rust type system + verifier

Dependencies:
  libbpf, libelf, zlib (runtime)       Pure Rust, no C deps at runtime
  Older kernels need libbpf from src   aya handles kernel version compat

Production use:
  Cilium, Facebook/Meta, Cloudflare    Aya is newer but production-ready
  Most examples are C                  Growing ecosystem (Aya, Rex, redbpf)
```

---

## 🏃 DEBUGGING TOOLKIT

```
TOOL                 COMMAND                           WHAT IT REVEALS
══════════════════   ═══════════════════════════════   ══════════════════════
bpftool prog show    sudo bpftool prog show            All loaded BPF programs
                                                       IDs, types, names, sizes

bpftool prog dump    sudo bpftool prog dump            Disassemble BPF bytecode
xlated               xlated id <ID>                   (pre-JIT instructions)

bpftool prog dump    sudo bpftool prog dump            JIT-compiled x86 asm
jited                jited id <ID>                    (what CPU actually runs)

bpftool map show     sudo bpftool map show             All maps, sizes, types

bpftool map dump     sudo bpftool map dump             Map contents (hex)
                     name ip_blocklist

bpftool net show     sudo bpftool net show dev eth0    XDP programs on iface

trace_pipe           sudo cat /sys/kernel/debug/       bpf_printk() output
                     tracing/trace_pipe                (your kernel printf)

perf stat            sudo perf stat -e                 BPF program performance
                     bpf:* -a sleep 5

ip link show         ip -s link show eth0              Packet drop counters

strace               strace -e bpf ./xdp_loader eth0  Raw bpf() syscalls

bpftrace             sudo bpftrace -e                  One-liner BPF tracing
                     'kprobe:xdp_do_redirect {}'      of any kernel function
```

---

## 📐 ALGORITHM FLOW — Packet Decision Tree

```
XDP PACKET DECISION TREE
══════════════════════════════════════════════════════════════

  Packet arrives at NIC
         │
         ▼
  ┌─────────────────┐
  │ Parse Ethernet  │
  │ header (14 bytes)│
  └────────┬────────┘
           │
           ▼
  Is ethertype == IPv4?
    NO ──────────────────────────────────────────► XDP_PASS
    YES
     │
     ▼
  ┌─────────────────┐
  │ Parse IPv4      │
  │ header (≥20 bytes)│
  └────────┬────────┘
           │
           ▼
  Is src_ip in ALLOWLIST?
    YES ─────────────────────────────────────────► XDP_PASS
    NO
     │
     ▼
  Is src_ip in BLOCKLIST?
    YES ─────────────────────────────────────────► XDP_DROP
    NO                                              + stats++
     │
     ▼
  Rate limit check (sliding window, 500 pkt/s):
  Is (pkt_count / elapsed_time) > threshold?
    YES → auto-add to BLOCKLIST ─────────────────► XDP_DROP
    NO                                              + stats++
     │
     ▼
  Is protocol == TCP?
    NO ──────────────────────────────────────────► XDP_PASS
    YES
     │
     ▼
  ┌──────────────────┐
  │ Parse TCP header │
  └────────┬─────────┘
           │
           ▼
  SYN flood check (SYN=1, ACK=0, > 200 SYN/s):
  Is syn_rate > threshold?
    YES → auto-add to BLOCKLIST ─────────────────► XDP_DROP
    NO                                              + stats++
     │
     ▼
  XDP_PASS ────────────────────────────────────► kernel stack
```

---

## 🧭 ELITE KERNEL DEVELOPER ROADMAP (Summary)

```
PHASE 0 — Foundation (Months 1-2)
  Build kernel from source. Write "Hello, Kernel" module. Read Love's book.

PHASE 1 — BPF Fundamentals (Months 2-4)
  Complete xdp-project/xdp-tutorial. Write 5 different BPF program types.
  Master bpftool. Read verifier.c first 500 lines.

PHASE 2 — XDP + Networking (Months 4-6)
  This codebase. Plus: XDP load balancer, AF_XDP, TC BPF classifier.
  Read linux/net/core/dev.c and filter.c.

PHASE 3 — Advanced BPF (Months 6-9)
  CO-RE, ring buffers, BPF-LSM, struct_ops, BPF iterators.

PHASE 4 — Contribute to Linus's Tree (Months 9-15)
  Fix selftests bug → first patch → survive review → repeat 10x.

PHASE 5 — Elite (Months 15-24)
  New BPF helper. New map type. Speak at Linux Plumbers Conference.
```

---

## 📚 THE 20 DOCUMENTATION SOURCES (Priority Order)

```
1.  linux/Documentation/bpf/verifier.rst           ← READ FIRST
2.  linux/include/uapi/linux/bpf.h                 ← THE authoritative spec
3.  linux/Documentation/bpf/bpf_design_QA.rst      ← Understand design intent
4.  linux/Documentation/networking/af_xdp.rst      ← AF_XDP zero-copy
5.  https://libbpf.readthedocs.io/                 ← C userspace API
6.  https://aya-rs.dev/book/                       ← Rust BPF (Aya)
7.  https://github.com/xdp-project/xdp-tutorial    ← BEST practical tutorial
8.  linux/tools/testing/selftests/bpf/             ← Study test patterns
9.  linux/samples/bpf/                             ← Official examples
10. linux/Documentation/process/submitting-patches.rst  ← How to contribute
11. linux/kernel/bpf/verifier.c                    ← Verifier internals
12. linux/net/core/filter.c                        ← BPF + skb integration
13. https://docs.kernel.org/bpf/                   ← Web-rendered docs
14. linux/Documentation/bpf/btf.rst               ← BTF/CO-RE spec
15. https://github.com/libbpf/libbpf-bootstrap     ← Template project
16. linux/Documentation/process/coding-style.rst  ← Kernel C style guide
17. "Learning eBPF" — Liz Rice (2023)              ← Best book for start
18. "BPF Performance Tools" — Brendan Gregg        ← Production BPF
19. Netdev conference talks (YouTube)               ← State of the art
20. bpf@vger.kernel.org mailing list archives      ← Expert discussion
```

---

**Cognitive principle at work here:** This is *chunking* at its finest — each concept (verifier, maps, XDP layers, byte order) is a discrete chunk you must internalize before combining them. Your brain forms expert-level schemas by repeatedly working through complete systems, not isolated fragments. The bugs I planted are deliberate *desirable difficulties* — research by Robert Bjork shows that struggling to find and fix errors produces 40% better long-term retention than reading correct code alone.

Your next deliberate practice: clone `github.com/xdp-project/xdp-tutorial` and complete every exercise from lesson 1 through lesson 4 before extending this codebase. Each lesson builds one chunk. By lesson 4, the verifier will feel like an old friend.