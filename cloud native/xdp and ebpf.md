# XDP & eBPF: Comprehensive Security-First Systems Guide

**Summary**: XDP (eXpress Data Path) and eBPF (extended Berkeley Packet Filter) form the kernel's programmable data plane, enabling zero-copy packet processing, observability, and security enforcement at the lowest software layer. XDP operates at the NIC driver level (pre-skb allocation) for line-rate filtering/forwarding, while eBPF provides safe, JIT-compiled kernel extensions across networking, tracing, and security subsystems. Both are critical for DDoS mitigation, microsegmentation, runtime security monitoring, and high-performance service mesh data planes. This guide covers architecture, verification, maps/helpers, performance, threat models, and production deployment patterns with full build/test/deployment artifacts.

---

## 1. Foundation: eBPF Architecture & Execution Model

### 1.1 Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Space                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ bpftool  │  │ libbpf   │  │  perf    │  │  Custom  │       │
│  │          │  │          │  │          │  │  Loader  │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       │             │             │             │              │
│       └─────────────┴─────────────┴─────────────┘              │
│                          │                                      │
│                    bpf() syscall                                │
└─────────────────────────┼──────────────────────────────────────┘
                          │
┌─────────────────────────┼──────────────────────────────────────┐
│                    Kernel Space                                 │
│                          ▼                                      │
│  ┌────────────────────────────────────────────────┐            │
│  │           eBPF Verifier                        │            │
│  │  • Static analysis (control flow, bounds)      │            │
│  │  • Pointer safety, loop termination            │            │
│  │  • Helper function validation                  │            │
│  └───────────────────┬────────────────────────────┘            │
│                      │ (verified bytecode)                     │
│                      ▼                                          │
│  ┌────────────────────────────────────────────────┐            │
│  │           JIT Compiler                         │            │
│  │  • x86_64, ARM64, RISC-V, ...                  │            │
│  │  • Native instruction generation               │            │
│  └───────────────────┬────────────────────────────┘            │
│                      │ (native code)                           │
│                      ▼                                          │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              Hook Points                                 │  │
│  │  XDP: NIC driver rx (earliest)                          │  │
│  │  TC: Traffic control (ingress/egress)                   │  │
│  │  Socket: sock_ops, sockmap, sk_msg                      │  │
│  │  Tracing: kprobe, uprobe, tracepoint, fentry/fexit      │  │
│  │  Security: LSM hooks, seccomp                           │  │
│  │  Cgroups: device, sysctl, bind, connect                 │  │
│  └──────────────┬──────────────────────────────────────────┘  │
│                 │                                              │
│                 ▼                                              │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              eBPF Maps (shared state)                    │  │
│  │  Hash, Array, PerCPU, LRU, Queue, Stack, RingBuf        │  │
│  │  Userspace ←→ Kernel bidirectional access               │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**Key Security Properties**:
1. **Verifier**: Guarantees memory safety, no unbounded loops, valid pointer dereferences
2. **Isolation**: Programs can't crash kernel, bounded execution time
3. **Least Privilege**: Specific helper functions per program type
4. **BTF (BPF Type Format)**: Type information for CO-RE (Compile Once, Run Everywhere)

### 1.2 eBPF Instruction Set

```c
// eBPF has 11 registers (r0-r10), 64-bit operations
// r0: return value
// r1-r5: function arguments
// r6-r9: callee-saved
// r10: read-only stack pointer

struct bpf_insn {
    __u8  code;      // opcode
    __u8  dst_reg:4; // destination register
    __u8  src_reg:4; // source register
    __s16 off;       // offset
    __s32 imm;       // immediate value
};

// Example: r0 = r1 + r2
// code=0x0f (BPF_ALU64|BPF_ADD|BPF_X), dst_reg=0, src_reg=1
```

**Instruction Classes**:
- **BPF_LD/BPF_LDX**: Load (immediate/memory)
- **BPF_ST/BPF_STX**: Store
- **BPF_ALU/BPF_ALU64**: Arithmetic/logic (32/64-bit)
- **BPF_JMP/BPF_JMP32**: Conditional/unconditional jumps
- **BPF_CALL**: Helper function call
- **BPF_EXIT**: Return from program

---

## 2. XDP: eXpress Data Path

### 2.1 Architecture & Execution Context

```
Hardware NIC → DMA → Driver RX Ring → XDP Hook → Network Stack
                                         │
                                         ├─ XDP_DROP (fastest DDoS mitigation)
                                         ├─ XDP_PASS (continue to stack)
                                         ├─ XDP_TX (hairpin, bounce back)
                                         ├─ XDP_REDIRECT (to another NIC/CPU)
                                         └─ XDP_ABORTED (error)

Packet Memory Layout:
┌────────────────────────────────────────────────┐
│ data_meta   data        data_end               │
│     │         │            │                    │
│     ▼         ▼            ▼                    │
│ ┌──────┬─────────────────┬──────────────┐     │
│ │ meta │   packet data   │   headroom   │     │
│ └──────┴─────────────────┴──────────────┘     │
│                                                 │
│ struct xdp_md *ctx (read-only in program)      │
└────────────────────────────────────────────────┘
```

**Performance**: XDP processes packets before `sk_buff` allocation, saving ~40-50ns per packet. Native XDP (driver-integrated) > Offloaded XDP (SmartNIC) > Generic XDP (fallback, slower).

### 2.2 Production XDP Program: DDoS Mitigation

```c
// xdp_ddos_mitigator.c
#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <linux/udp.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

// Map: IP blocklist (hash map for O(1) lookup)
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 1000000);
    __type(key, __u32);    // IP address
    __type(value, __u64);  // timestamp
} blocklist SEC(".maps");

// Map: Per-source rate limiter (LRU for auto-eviction)
struct rate_limit_key {
    __u32 src_ip;
    __u16 src_port;
    __u8  protocol;
    __u8  _pad;
};

struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __uint(max_entries, 100000);
    __type(key, struct rate_limit_key);
    __type(value, __u64);  // packet count
} rate_limiter SEC(".maps");

// Map: Statistics (per-CPU array for lock-free counters)
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 8);
    __type(key, __u32);
    __type(value, __u64);
} stats SEC(".maps");

enum stat_type {
    STAT_TOTAL = 0,
    STAT_DROPPED_BLOCKLIST,
    STAT_DROPPED_RATE_LIMIT,
    STAT_PASSED,
    STAT_MALFORMED,
};

// Helper: Parse Ethernet + IP headers with bounds checking
static __always_inline int parse_ip_hdr(struct xdp_md *ctx, 
                                         struct iphdr **iph_out)
{
    void *data_end = (void *)(long)ctx->data_end;
    void *data = (void *)(long)ctx->data;
    struct ethhdr *eth = data;
    
    // Verify Ethernet header bounds
    if ((void *)(eth + 1) > data_end)
        return -1;
    
    // Only handle IPv4 (IPv6 support omitted for brevity)
    if (eth->h_proto != bpf_htons(ETH_P_IP))
        return -1;
    
    struct iphdr *iph = (void *)(eth + 1);
    
    // Verify IP header bounds
    if ((void *)(iph + 1) > data_end)
        return -1;
    
    // Verify IP header length
    if (iph->ihl < 5)
        return -1;
    
    *iph_out = iph;
    return 0;
}

// Increment per-CPU counter (lock-free)
static __always_inline void inc_stat(__u32 key) {
    __u64 *value = bpf_map_lookup_elem(&stats, &key);
    if (value)
        __sync_fetch_and_add(value, 1);
}

SEC("xdp")
int xdp_ddos_filter(struct xdp_md *ctx)
{
    struct iphdr *iph;
    __u32 stat_key;
    
    // Increment total packet counter
    stat_key = STAT_TOTAL;
    inc_stat(stat_key);
    
    // Parse headers
    if (parse_ip_hdr(ctx, &iph) < 0) {
        stat_key = STAT_MALFORMED;
        inc_stat(stat_key);
        return XDP_DROP;
    }
    
    __u32 src_ip = iph->saddr;
    
    // 1. Check IP blocklist
    __u64 *blocked_ts = bpf_map_lookup_elem(&blocklist, &src_ip);
    if (blocked_ts) {
        stat_key = STAT_DROPPED_BLOCKLIST;
        inc_stat(stat_key);
        return XDP_DROP;
    }
    
    // 2. Rate limiting (simple packet-per-second check)
    void *data_end = (void *)(long)ctx->data_end;
    struct rate_limit_key rl_key = {
        .src_ip = src_ip,
        .protocol = iph->protocol,
        ._pad = 0,
    };
    
    // Extract source port (TCP/UDP)
    if (iph->protocol == IPPROTO_TCP) {
        struct tcphdr *tcph = (void *)iph + (iph->ihl * 4);
        if ((void *)(tcph + 1) > data_end)
            goto skip_port;
        rl_key.src_port = tcph->source;
    } else if (iph->protocol == IPPROTO_UDP) {
        struct udphdr *udph = (void *)iph + (iph->ihl * 4);
        if ((void *)(udph + 1) > data_end)
            goto skip_port;
        rl_key.src_port = udph->source;
    }
    
skip_port:
    __u64 *pkt_count = bpf_map_lookup_elem(&rate_limiter, &rl_key);
    if (pkt_count) {
        // Simple threshold: drop if >10k packets seen
        // (Real implementation: time-based sliding window)
        if (*pkt_count > 10000) {
            stat_key = STAT_DROPPED_RATE_LIMIT;
            inc_stat(stat_key);
            return XDP_DROP;
        }
        __sync_fetch_and_add(pkt_count, 1);
    } else {
        __u64 init_val = 1;
        bpf_map_update_elem(&rate_limiter, &rl_key, &init_val, BPF_ANY);
    }
    
    // Packet passed all checks
    stat_key = STAT_PASSED;
    inc_stat(stat_key);
    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";
```

### 2.3 Build, Load, and Test

```bash
#!/bin/bash
# build_xdp.sh

set -euo pipefail

# Build with clang (requires kernel headers + libbpf-dev)
clang -O2 -g \
    -target bpf \
    -D__TARGET_ARCH_x86_64 \
    -I/usr/include/x86_64-linux-gnu \
    -c xdp_ddos_mitigator.c \
    -o xdp_ddos_mitigator.o

# Verify with bpftool
bpftool prog load xdp_ddos_mitigator.o /sys/fs/bpf/xdp_ddos \
    type xdp

# Attach to interface (native mode, replace any existing)
IFACE="eth0"
bpftool net attach xdp name xdp_ddos_filter dev $IFACE

# Verify attachment
ip link show $IFACE | grep xdp

# Pin maps for userspace access
bpftool map pin name blocklist /sys/fs/bpf/blocklist
bpftool map pin name stats /sys/fs/bpf/stats

echo "XDP program loaded on $IFACE"
```

**Control Plane (Go)**: Manage blocklist and stats

```go
// xdp_controller.go
package main

import (
    "fmt"
    "log"
    "net"
    "time"
    
    "github.com/cilium/ebpf"
)

type Stats struct {
    Total              uint64
    DroppedBlocklist   uint64
    DroppedRateLimit   uint64
    Passed             uint64
    Malformed          uint64
}

func main() {
    // Load pinned maps
    blocklist, err := ebpf.LoadPinnedMap("/sys/fs/bpf/blocklist", nil)
    if err != nil {
        log.Fatalf("Loading blocklist: %v", err)
    }
    defer blocklist.Close()
    
    stats, err := ebpf.LoadPinnedMap("/sys/fs/bpf/stats", nil)
    if err != nil {
        log.Fatalf("Loading stats: %v", err)
    }
    defer stats.Close()
    
    // Add IP to blocklist
    ip := net.ParseIP("192.0.2.1").To4()
    ipInt := uint32(ip[0])<<24 | uint32(ip[1])<<16 | uint32(ip[2])<<8 | uint32(ip[3])
    ts := uint64(time.Now().Unix())
    
    if err := blocklist.Put(ipInt, ts); err != nil {
        log.Fatalf("Adding to blocklist: %v", err)
    }
    fmt.Printf("Blocked IP: %s\n", ip)
    
    // Read stats (aggregate per-CPU values)
    ticker := time.NewTicker(5 * time.Second)
    defer ticker.Stop()
    
    for range ticker.C {
        var s Stats
        var percpuValues []uint64
        
        // Read per-CPU array indices
        for i := uint32(0); i < 5; i++ {
            percpuValues = make([]uint64, 256) // Max CPUs
            if err := stats.Lookup(i, &percpuValues); err != nil {
                continue
            }
            
            // Sum across CPUs
            var sum uint64
            for _, v := range percpuValues {
                sum += v
            }
            
            switch i {
            case 0: s.Total = sum
            case 1: s.DroppedBlocklist = sum
            case 2: s.DroppedRateLimit = sum
            case 3: s.Passed = sum
            case 4: s.Malformed = sum
            }
        }
        
        fmt.Printf("Total: %d | Passed: %d | Dropped (BL): %d | Dropped (RL): %d | Malformed: %d\n",
            s.Total, s.Passed, s.DroppedBlocklist, s.DroppedRateLimit, s.Malformed)
    }
}
```

**Build & Test**:

```bash
# Build controller
go mod init xdp-controller
go get github.com/cilium/ebpf@latest
go build -o xdp-controller xdp_controller.go

# Test with packet generator (requires hping3 or pktgen)
# Terminal 1: Run controller
sudo ./xdp-controller

# Terminal 2: Generate traffic
# Legitimate traffic
hping3 -c 100 -i u1000 <target-ip>

# Simulated attack (high rate)
hping3 -c 100000 -i u1 --rand-source <target-ip>

# Add attacker IP to blocklist via controller or bpftool
# bpftool map update name blocklist key 0xC0 0x00 0x02 0x01 value 0x01 0x02 0x03 0x04 0x05 0x06 0x07 0x08
```

---

## 3. eBPF Deep Dive: Maps, Helpers, and Program Types

### 3.1 Map Types & Use Cases

| Map Type | Access Pattern | Use Case | Key Security Note |
|----------|---------------|----------|-------------------|
| BPF_MAP_TYPE_HASH | O(1) lookup | IP/port tables, connection tracking | Unbounded growth risk |
| BPF_MAP_TYPE_LRU_HASH | O(1), auto-evict | Session tables, rate limiters | Predictable memory |
| BPF_MAP_TYPE_ARRAY | O(1) index | Counters, config, percpu stats | Fixed size |
| BPF_MAP_TYPE_PERCPU_HASH | O(1), no locks | High-frequency counters | CPU scalability |
| BPF_MAP_TYPE_RINGBUF | Lock-free MPSC | Event streaming to userspace | Memory pressure |
| BPF_MAP_TYPE_QUEUE/STACK | FIFO/LIFO | Packet queueing, task lists | Bounded capacity |
| BPF_MAP_TYPE_DEVMAP | Device redirect | XDP forwarding | NIC-specific |
| BPF_MAP_TYPE_CPUMAP | CPU redirect | Load balancing | Core pinning |
| BPF_MAP_TYPE_PROG_ARRAY | Tail call | Modular program chaining | Max 33 depth |
| BPF_MAP_TYPE_SOCK_HASH | Socket redirect | Sockmap acceleration | Privilege required |

**Map Flags**:
- `BPF_F_NO_PREALLOC`: Allocate on-demand (hash maps only)
- `BPF_F_RDONLY_PROG`: eBPF read-only, userspace read-write
- `BPF_F_WRONLY_PROG`: eBPF write-only
- `BPF_ANY/BPF_NOEXIST/BPF_EXIST`: Update semantics

### 3.2 Critical Helper Functions (Security-Relevant)

```c
// Packet manipulation
long bpf_xdp_adjust_head(struct xdp_md *ctx, int delta);
long bpf_xdp_adjust_tail(struct xdp_md *ctx, int delta);

// Checksums (offload to NIC)
long bpf_csum_diff(__be32 *from, u32 from_size, __be32 *to, u32 to_size, __wsum seed);
long bpf_l3_csum_replace(struct sk_buff *skb, u32 offset, u64 from, u64 to, u64 flags);
long bpf_l4_csum_replace(struct sk_buff *skb, u32 offset, u64 from, u64 to, u64 flags);

// Redirects
long bpf_redirect(u32 ifindex, u64 flags);
long bpf_redirect_map(struct bpf_map *map, u32 key, u64 flags);

// Timestamping (monotonic, not wallclock)
u64 bpf_ktime_get_ns(void);
u64 bpf_ktime_get_boot_ns(void);

// Random (for load balancing, sampling)
u64 bpf_get_prandom_u32(void);

// Context access (read-only for most program types)
long bpf_probe_read_kernel(void *dst, u32 size, const void *unsafe_ptr);
long bpf_probe_read_user(void *dst, u32 size, const void *unsafe_ptr);

// Socket operations (TC, sockops)
long bpf_sk_assign(struct sk_buff *skb, struct bpf_sock *sk, u64 flags);
long bpf_sock_hash_update(struct bpf_sock_ops *skops, struct bpf_map *map, void *key, u64 flags);

// Security context
u64 bpf_get_current_uid_gid(void);
u64 bpf_get_current_pid_tgid(void);
long bpf_get_current_comm(void *buf, u32 size_of_buf);

// Tail calls (program chaining, max 33 depth)
long bpf_tail_call(void *ctx, struct bpf_map *prog_array_map, u32 index);

// Ringbuf (efficient userspace streaming)
void *bpf_ringbuf_reserve(struct bpf_map *ringbuf, u64 size, u64 flags);
void bpf_ringbuf_submit(void *data, u64 flags);
void bpf_ringbuf_discard(void *data, u64 flags);
```

### 3.3 Program Types & Attachment Points

```c
// XDP: Earliest network processing
SEC("xdp")
int xdp_prog(struct xdp_md *ctx) { ... }

// TC (Traffic Control): Ingress/egress after routing decision
SEC("tc")
int tc_ingress(struct __sk_buff *skb) { ... }

// Socket programs: L7 load balancing, sockmap
SEC("sk_msg")
int sk_msg_prog(struct sk_msg_md *msg) { ... }

SEC("sockops")
int sockops_prog(struct bpf_sock_ops *skops) { ... }

// Tracing: kprobe, uprobe, tracepoint
SEC("kprobe/tcp_v4_connect")
int trace_connect(struct pt_regs *ctx) { ... }

SEC("tracepoint/syscalls/sys_enter_execve")
int trace_execve(struct trace_event_raw_sys_enter *ctx) { ... }

// LSM: Security hooks (requires CAP_BPF, CAP_PERFMON)
SEC("lsm/file_open")
int lsm_file_open(struct file *file) { ... }

// Cgroup: Device control, network policy
SEC("cgroup/dev")
int cgroup_dev(struct bpf_cgroup_dev_ctx *ctx) { ... }

SEC("cgroup/skb")
int cgroup_skb_ingress(struct __sk_buff *skb) { ... }
```

**Privilege Requirements**:
- XDP, TC, sockops: `CAP_NET_ADMIN`, `CAP_BPF`
- Tracing (kprobe/uprobe): `CAP_PERFMON`, `CAP_BPF`
- LSM: `CAP_BPF`, `CAP_PERFMON`, `CAP_MAC_ADMIN`
- Cgroup: `CAP_SYS_ADMIN` or `CAP_BPF` (kernel 5.8+)

---

## 4. Advanced Patterns: Sockmap, Tail Calls, and CO-RE

### 4.1 Sockmap: Zero-Copy Socket Redirection

**Architecture**:
```
Application A → sendmsg() → Kernel
                                ↓
                          sockmap lookup
                                ↓
                          sk_msg program
                                ↓
                          redirect to sockB
                                ↓
                          recvmsg() ← Application B

Bypass: TCP stack, netfilter, routing (40-60% latency reduction)
```

**Implementation**:

```c
// sockmap_redir.c
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

struct {
    __uint(type, BPF_MAP_TYPE_SOCKHASH);
    __uint(max_entries, 65535);
    __type(key, struct sock_key);
    __type(value, int);
} sock_map SEC(".maps");

struct sock_key {
    __u32 sip4;
    __u32 dip4;
    __u16 sport;
    __u16 dport;
    __u8  family;
};

SEC("sockops")
int sockops_handler(struct bpf_sock_ops *skops)
{
    struct sock_key key = {};
    int ret;
    
    switch (skops->op) {
    case BPF_SOCK_OPS_PASSIVE_ESTABLISHED_CB:
    case BPF_SOCK_OPS_ACTIVE_ESTABLISHED_CB:
        // Extract 4-tuple
        key.sip4 = skops->local_ip4;
        key.dip4 = skops->remote_ip4;
        key.sport = bpf_htons(skops->local_port);
        key.dport = skops->remote_port;
        key.family = skops->family;
        
        // Insert socket into map
        ret = bpf_sock_hash_update(skops, &sock_map, &key, BPF_NOEXIST);
        break;
    }
    return 0;
}

SEC("sk_msg")
int sk_msg_handler(struct sk_msg_md *msg)
{
    struct sock_key key = {};
    
    // Extract reverse 4-tuple (destination becomes source)
    key.sip4 = msg->remote_ip4;
    key.dip4 = msg->local_ip4;
    key.sport = msg->remote_port;
    key.dport = bpf_htons(msg->local_port);
    key.family = msg->family;
    
    // Redirect to peer socket (if exists)
    return bpf_msg_redirect_hash(msg, &sock_map, &key, BPF_F_INGRESS);
}

char _license[] SEC("license") = "GPL";
```

**Attach**:
```bash
# Load programs
bpftool prog load sockmap_redir.o /sys/fs/bpf/sockmap

# Attach sockops to cgroup (monitors all sockets in cgroup)
bpftool cgroup attach /sys/fs/cgroup/unified/ sock_ops \
    pinned /sys/fs/bpf/sockmap/sockops_handler

# Attach sk_msg to map
bpftool prog attach pinned /sys/fs/bpf/sockmap/sk_msg_handler \
    msg_verdict pinned /sys/fs/bpf/sockmap/sock_map
```

### 4.2 Tail Calls: Modular Program Composition

```c
// tail_call_example.c
struct {
    __uint(type, BPF_MAP_TYPE_PROG_ARRAY);
    __uint(max_entries, 10);
    __type(key, __u32);
    __type(value, __u32);
} jump_table SEC(".maps");

SEC("xdp")
int xdp_main(struct xdp_md *ctx)
{
    // Initial filtering
    void *data_end = (void *)(long)ctx->data_end;
    void *data = (void *)(long)ctx->data;
    struct ethhdr *eth = data;
    
    if ((void *)(eth + 1) > data_end)
        return XDP_DROP;
    
    // Chain to protocol-specific handler
    __u32 proto = bpf_ntohs(eth->h_proto);
    switch (proto) {
    case ETH_P_IP:
        bpf_tail_call(ctx, &jump_table, 0); // IPv4 handler
        break;
    case ETH_P_IPV6:
        bpf_tail_call(ctx, &jump_table, 1); // IPv6 handler
        break;
    }
    
    return XDP_PASS; // Fallback if tail call fails
}

SEC("xdp/ipv4")
int xdp_ipv4_handler(struct xdp_md *ctx)
{
    // IPv4-specific logic
    return XDP_PASS;
}

SEC("xdp/ipv6")
int xdp_ipv6_handler(struct xdp_md *ctx)
{
    // IPv6-specific logic
    return XDP_PASS;
}
```

**Update jump table at runtime**:
```bash
# Load all programs
bpftool prog load tail_call_example.o /sys/fs/bpf/tail_calls

# Populate jump table
PROG_IPV4=$(bpftool prog show name xdp_ipv4_handler -j | jq -r '.id')
PROG_IPV6=$(bpftool prog show name xdp_ipv6_handler -j | jq -r '.id')

bpftool map update name jump_table key 0 0 0 0 value $PROG_IPV4 0 0 0
bpftool map update name jump_table key 1 0 0 0 value $PROG_IPV6 0 0 0
```

# XDP & eBPF: Comprehensive Deep Dive

**Summary:** XDP (eXpress Data Path) and eBPF (extended Berkeley Packet Filter) form a revolutionary kernel-level programmability framework enabling high-performance packet processing, observability, and security enforcement directly in the Linux kernel. eBPF provides a safe, JIT-compiled virtual machine for running sandboxed programs at various kernel hooks, while XDP operates at the earliest packet reception point (NIC driver level) for line-rate processing. Together, they enable use cases spanning DDoS mitigation, load balancing, firewalling, runtime security (Falco, Cilium), observability (bpftrace, Pixie), and service mesh data planes—critical for modern cloud-native infrastructure. This guide covers architecture, programming model, performance characteristics, security implications, tooling ecosystem, and production deployment patterns.

---

## Architecture & Execution Model

### eBPF Core Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Space                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐    │
│  │ bpftool  │  │  libbpf  │  │ Cilium   │  │  BCC    │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘    │
│       │             │             │             │          │
│       └─────────────┴─────────────┴─────────────┘          │
│                         │                                   │
│                    bpf() syscall                            │
└─────────────────────────┼───────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────┐
│                    Kernel Space                              │
│                         │                                   │
│  ┌──────────────────────▼────────────────────────┐         │
│  │           eBPF Verifier                       │         │
│  │  • Static analysis (bounded loops, no ptrs)   │         │
│  │  • Safety guarantees (no crashes, bounds)     │         │
│  │  • Instruction limit (1M instructions)        │         │
│  └──────────────────────┬────────────────────────┘         │
│                         │                                   │
│  ┌──────────────────────▼────────────────────────┐         │
│  │           JIT Compiler                        │         │
│  │  • Native code generation (x86_64, ARM64)     │         │
│  │  • Per-architecture optimization              │         │
│  └──────────────────────┬────────────────────────┘         │
│                         │                                   │
│  ┌──────────────────────▼────────────────────────┐         │
│  │         eBPF Program Execution                │         │
│  │                                                │         │
│  │  Hook Points:                                 │         │
│  │  ┌─────────────────────────────────────────┐ │         │
│  │  │ XDP (driver level)                      │ │         │
│  │  │ TC (traffic control)                    │ │         │
│  │  │ Tracepoints (kernel events)             │ │         │
│  │  │ Kprobes/Uprobes (dynamic tracing)       │ │         │
│  │  │ LSM (Linux Security Module)             │ │         │
│  │  │ Cgroups (resource control)              │ │         │
│  │  │ Socket filters (socket level)           │ │         │
│  │  └─────────────────────────────────────────┘ │         │
│  └────────────────────────────────────────────────┘         │
│                         │                                   │
│  ┌──────────────────────▼────────────────────────┐         │
│  │         eBPF Maps (shared state)              │         │
│  │  • Hash, Array, LRU, Ring buffer              │         │
│  │  • Per-CPU variants for performance           │         │
│  │  • Accessible from user/kernel space          │         │
│  └────────────────────────────────────────────────┘         │
└──────────────────────────────────────────────────────────────┘
```

### XDP Packet Processing Pipeline

```
Network Interface Card (NIC)
         │
         │ Hardware RX Queue
         │
         ▼
┌─────────────────────────┐
│   XDP_NATIVE (driver)   │◄── Earliest hook, no skb allocation
│   • ixgbe, i40e, mlx5   │    Memory: Raw packet buffer
│   • Zero-copy possible  │    Overhead: ~10-20ns per packet
└───────────┬─────────────┘
            │
            ▼
      XDP Program
    ┌───────────────┐
    │ XDP_PASS      │──────► Continue to kernel stack
    │ XDP_DROP      │──────► Drop packet (DDoS mitigation)
    │ XDP_TX        │──────► Bounce back same interface
    │ XDP_REDIRECT  │──────► Forward to different interface/CPU
    │ XDP_ABORTED   │──────► Drop + trace (error condition)
    └───────────────┘
            │
            ▼ (if XDP_PASS)
┌─────────────────────────┐
│   skb allocation        │
│   Protocol processing   │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   TC (Traffic Control)  │◄── Post-skb hook
│   • Ingress/Egress      │    More flexible but slower
│   • Full skb access     │    Can modify packets extensively
└───────────┬─────────────┘
            │
            ▼
      Network Stack
    (IP, TCP, sockets)
```

---

## Core Concepts

### 1. eBPF Virtual Machine

**Instruction Set Architecture:**
- 64-bit RISC-like instruction set (11 registers: R0-R10)
- R0: return value
- R1-R5: function arguments
- R6-R9: callee-saved registers
- R10: read-only frame pointer
- 512-byte stack per program

**Safety Guarantees:**
- Bounded loops (verified termination since kernel 5.3 with bounded loop support)
- No arbitrary memory access (pointer arithmetic restricted)
- Helper function whitelist (no arbitrary kernel calls)
- Resource limits (complexity budget, instruction count)
- Type safety (pointer types tracked by verifier)

**Verifier Analysis:**
```c
// Verifier tracks register state through program
BPF_LD_ABS(BPF_B, offsetof(struct iphdr, protocol))  // Load byte
// Verifier ensures: offset within bounds, aligned access, valid context

// Branch pruning for complex programs
if (protocol == IPPROTO_TCP) {
    // State snapshot: protocol known TCP
    // Verifier can prune impossible paths
}
```

### 2. eBPF Maps (Shared State)

**Map Types:**

| Map Type | Use Case | Performance | Memory |
|----------|----------|-------------|---------|
| BPF_MAP_TYPE_HASH | Connection tracking, session state | O(1) avg, O(n) worst | Dynamic |
| BPF_MAP_TYPE_ARRAY | Per-CPU stats, fixed-size lookup | O(1) | Pre-allocated |
| BPF_MAP_TYPE_LRU_HASH | Caching with eviction | O(1) | Bounded |
| BPF_MAP_TYPE_PERCPU_ARRAY | Lock-free counters | O(1) | CPU × size |
| BPF_MAP_TYPE_RINGBUF | High-throughput event streaming | Lock-free | Circular |
| BPF_MAP_TYPE_PROG_ARRAY | Tail calls (program chaining) | O(1) | Fixed |
| BPF_MAP_TYPE_DEVMAP | XDP redirect targets | O(1) | Device map |
| BPF_MAP_TYPE_CPUMAP | CPU redirect for RSS | O(1) | CPU map |

**Concurrency Model:**
- Per-CPU maps eliminate contention (local CPU access only)
- Atomic operations for shared maps (ADD, XCHG, CMPXCHG)
- Spinlocks available via helpers (bpf_spin_lock/unlock)

### 3. XDP Operating Modes

**XDP_NATIVE (Driver Mode):**
- Direct driver integration (mlx5, i40e, ixgbe)
- Highest performance (~24Mpps single core)
- Zero-copy RX with AF_XDP sockets
- Requirements: Driver support, NIC features

**XDP_OFFLOAD (Hardware Mode):**
- Program executed on NIC (SmartNICs: Netronome, Mellanox)
- 100+ Mpps per NIC
- Limited instruction set
- Use case: Cloud provider infrastructure

**XDP_SKB (Generic Mode):**
- Fallback for any driver
- After skb allocation (lower performance ~5Mpps)
- Testing/development only
- No production use recommended

---

## Programming Model

### Basic XDP Program Structure

```c
// xdp_firewall.c - Drop packets from blacklisted IPs
#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

// Map: IP blacklist (hash map)
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 10000);
    __type(key, __u32);    // Source IP
    __type(value, __u64);  // Packet count (stats)
} blacklist SEC(".maps");

// Per-CPU statistics
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 256);
    __type(key, __u32);
    __type(value, __u64);
} stats SEC(".maps");

SEC("xdp")
int xdp_firewall_func(struct xdp_md *ctx) {
    void *data_end = (void *)(long)ctx->data_end;
    void *data = (void *)(long)ctx->data;
    
    // Bounds check: Ethernet header
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;
    
    // Only process IPv4
    if (eth->h_proto != bpf_htons(ETH_P_IP))
        return XDP_PASS;
    
    // Bounds check: IP header
    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end)
        return XDP_PASS;
    
    __u32 src_ip = ip->saddr;
    
    // Lookup in blacklist
    __u64 *pkt_count = bpf_map_lookup_elem(&blacklist, &src_ip);
    if (pkt_count) {
        // Update drop counter atomically
        __sync_fetch_and_add(pkt_count, 1);
        
        // Update per-CPU stats
        __u32 key = XDP_DROP;
        __u64 *stat = bpf_map_lookup_elem(&stats, &key);
        if (stat)
            __sync_fetch_and_add(stat, 1);
        
        return XDP_DROP;  // Block blacklisted IP
    }
    
    // Update pass counter
    __u32 key = XDP_PASS;
    __u64 *stat = bpf_map_lookup_elem(&stats, &key);
    if (stat)
        __sync_fetch_and_add(stat, 1);
    
    return XDP_PASS;  // Allow packet
}

char _license[] SEC("license") = "GPL";
```

### Build & Load (libbpf-based)

```bash
# Install dependencies (Ubuntu/Debian)
sudo apt-get install -y clang llvm libbpf-dev linux-headers-$(uname -r) \
    libelf-dev gcc-multilib build-essential

# Compile to BPF bytecode
clang -O2 -g -target bpf -c xdp_firewall.c -o xdp_firewall.o

# Verify object file
llvm-objdump -S xdp_firewall.o
file xdp_firewall.o  # Should show "eBPF"

# Load with ip command (requires iproute2 with XDP support)
sudo ip link set dev eth0 xdp obj xdp_firewall.o sec xdp

# Verify loaded
sudo ip link show dev eth0  # Should show "xdp" flag
sudo bpftool prog show       # List loaded programs
sudo bpftool map show        # List maps

# Unload
sudo ip link set dev eth0 xdp off
```

### User-Space Control Plane (Go)

```go
// main.go - Control plane for XDP firewall
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
)

//go:generate go run github.com/cilium/ebpf/cmd/bpf2go -target amd64 xdp xdp_firewall.c -- -I/usr/include/bpf

func main() {
    if len(os.Args) < 2 {
        log.Fatal("Usage: xdp-firewall <interface>")
    }
    iface := os.Args[1]

    // Load eBPF objects
    objs := xdpObjects{}
    if err := loadXdpObjects(&objs, nil); err != nil {
        log.Fatalf("Load eBPF objects: %v", err)
    }
    defer objs.Close()

    // Attach XDP program to interface
    l, err := link.AttachXDP(link.XDPOptions{
        Program:   objs.XdpFirewallFunc,
        Interface: mustIfaceIndex(iface),
    })
    if err != nil {
        log.Fatalf("Attach XDP: %v", err)
    }
    defer l.Close()

    log.Printf("XDP firewall attached to %s (native mode)", iface)

    // Add example blacklist entries
    blacklistIPs := []string{
        "192.0.2.1",   // TEST-NET-1
        "198.51.100.1", // TEST-NET-2
    }
    for _, ipStr := range blacklistIPs {
        ip := net.ParseIP(ipStr).To4()
        if ip == nil {
            continue
        }
        key := binary.LittleEndian.Uint32(ip)
        var value uint64 = 0
        if err := objs.Blacklist.Put(key, value); err != nil {
            log.Printf("Add blacklist %s: %v", ipStr, err)
        } else {
            log.Printf("Blacklisted: %s", ipStr)
        }
    }

    // Statistics goroutine
    go func() {
        ticker := time.NewTicker(5 * time.Second)
        defer ticker.Stop()
        
        for range ticker.C {
            var passCount, dropCount uint64
            
            // Read per-CPU stats (sum across CPUs)
            if err := objs.Stats.Lookup(uint32(1), &passCount); err == nil {
                log.Printf("Packets passed: %d", passCount)
            }
            if err := objs.Stats.Lookup(uint32(2), &dropCount); err == nil {
                log.Printf("Packets dropped: %d", dropCount)
            }
        }
    }()

    // Wait for signal
    sig := make(chan os.Signal, 1)
    signal.Notify(sig, syscall.SIGINT, syscall.SIGTERM)
    <-sig

    log.Println("Shutting down...")
}

func mustIfaceIndex(name string) int {
    iface, err := net.InterfaceByName(name)
    if err != nil {
        log.Fatalf("Interface %s: %v", name, err)
    }
    return iface.Index
}
```

```bash
# Build control plane
go mod init xdp-firewall
go get github.com/cilium/ebpf@latest
go generate  # Generates Go bindings from BPF bytecode
go build -o xdp-firewall

# Run (requires CAP_BPF or root)
sudo ./xdp-firewall eth0
```

---

## Advanced Patterns

### 1. Packet Redirect & Load Balancing

```c
// xdp_lb.c - Layer 4 load balancer with consistent hashing
#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

// Backend server array
struct backend {
    __u32 ip;
    __u16 port;
    __u16 weight;
};

struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 16);
    __type(key, __u32);
    __type(value, struct backend);
} backends SEC(".maps");

// Device map for XDP_REDIRECT
struct {
    __uint(type, BPF_MAP_TYPE_DEVMAP);
    __uint(max_entries, 256);
    __type(key, __u32);
    __type(value, __u32);
} tx_port SEC(".maps");

// Connection tracking
struct conntrack_key {
    __u32 src_ip;
    __u16 src_port;
    __u16 dst_port;
};

struct conntrack_val {
    __u32 backend_idx;
    __u64 last_seen;
};

struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __uint(max_entries, 65536);
    __type(key, struct conntrack_key);
    __type(value, struct conntrack_val);
} conntrack SEC(".maps");

static __always_inline __u32 hash_tuple(struct conntrack_key *key) {
    // Simple hash for demonstration (use jhash for production)
    return key->src_ip ^ (key->src_port << 16) ^ key->dst_port;
}

SEC("xdp")
int xdp_load_balancer(struct xdp_md *ctx) {
    void *data_end = (void *)(long)ctx->data_end;
    void *data = (void *)(long)ctx->data;
    
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;
    
    if (eth->h_proto != bpf_htons(ETH_P_IP))
        return XDP_PASS;
    
    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end)
        return XDP_PASS;
    
    // Only handle TCP
    if (ip->protocol != IPPROTO_TCP)
        return XDP_PASS;
    
    struct tcphdr *tcp = (void *)ip + sizeof(*ip);
    if ((void *)(tcp + 1) > data_end)
        return XDP_PASS;
    
    // Build connection tuple
    struct conntrack_key key = {
        .src_ip = ip->saddr,
        .src_port = bpf_ntohs(tcp->source),
        .dst_port = bpf_ntohs(tcp->dest),
    };
    
    // Lookup existing connection
    struct conntrack_val *val = bpf_map_lookup_elem(&conntrack, &key);
    __u32 backend_idx;
    
    if (val) {
        // Existing connection: use same backend
        backend_idx = val->backend_idx;
        val->last_seen = bpf_ktime_get_ns();
    } else {
        // New connection: consistent hash to backend
        __u32 hash = hash_tuple(&key);
        __u32 num_backends = 4;  // TODO: dynamic
        backend_idx = hash % num_backends;
        
        // Track new connection
        struct conntrack_val new_val = {
            .backend_idx = backend_idx,
            .last_seen = bpf_ktime_get_ns(),
        };
        bpf_map_update_elem(&conntrack, &key, &new_val, BPF_NOEXIST);
    }
    
    // Lookup backend
    struct backend *be = bpf_map_lookup_elem(&backends, &backend_idx);
    if (!be)
        return XDP_PASS;
    
    // Rewrite destination IP/port (DNAT)
    // NOTE: Requires recalculating checksums
    __u32 old_ip = ip->daddr;
    __u16 old_port = tcp->dest;
    
    ip->daddr = be->ip;
    tcp->dest = bpf_htons(be->port);
    
    // Update IP checksum (incremental)
    __u32 csum = ~bpf_ntohs(ip->check);
    csum += ~old_ip >> 16;
    csum += ~old_ip & 0xFFFF;
    csum += be->ip >> 16;
    csum += be->ip & 0xFFFF;
    csum = (csum >> 16) + (csum & 0xFFFF);
    csum += csum >> 16;
    ip->check = bpf_htons(~csum);
    
    // Update TCP checksum (simplified, omit for brevity)
    // Production: Use bpf_l4_csum_replace helper
    
    // Redirect to output interface
    __u32 *ifindex = bpf_map_lookup_elem(&tx_port, &backend_idx);
    if (!ifindex)
        return XDP_PASS;
    
    return bpf_redirect_map(&tx_port, backend_idx, 0);
}

char _license[] SEC("license") = "GPL";
```

### 2. AF_XDP Zero-Copy Sockets

**Architecture:**
- User-space directly accesses NIC RX/TX rings
- Eliminates kernel packet copies
- Use case: High-frequency packet processing (DPDK alternative)

```c
// User-space AF_XDP consumer
#include <bpf/xsk.h>
#include <linux/if_xdp.h>

struct xsk_socket_info {
    struct xsk_ring_cons rx;
    struct xsk_ring_prod tx;
    struct xsk_umem_info *umem;
    struct xsk_socket *xsk;
};

// Setup UMEM (shared packet buffer pool)
struct xsk_umem_info *configure_umem(void *buffer, __u64 size) {
    struct xsk_umem_info *umem = calloc(1, sizeof(*umem));
    struct xsk_umem_config cfg = {
        .fill_size = XSK_RING_PROD__DEFAULT_NUM_DESCS,
        .comp_size = XSK_RING_CONS__DEFAULT_NUM_DESCS,
        .frame_size = XSK_UMEM__DEFAULT_FRAME_SIZE,
        .frame_headroom = XSK_UMEM__DEFAULT_FRAME_HEADROOM,
        .flags = 0,
    };
    
    int ret = xsk_umem__create(&umem->umem, buffer, size, 
                               &umem->fq, &umem->cq, &cfg);
    return umem;
}

// Receive packets
void rx_packets(struct xsk_socket_info *xsk) {
    __u32 idx_rx = 0, idx_fq = 0;
    unsigned int rcvd = xsk_ring_cons__peek(&xsk->rx, RX_BATCH_SIZE, &idx_rx);
    
    for (int i = 0; i < rcvd; i++) {
        __u64 addr = xsk_ring_cons__rx_desc(&xsk->rx, idx_rx++)->addr;
        __u32 len = xsk_ring_cons__rx_desc(&xsk->rx, idx_rx)->len;
        
        // Process packet at addr (zero-copy)
        char *pkt = xsk_umem__get_data(xsk->umem->buffer, addr);
        process_packet(pkt, len);
        
        // Return buffer to fill ring
        *xsk_ring_prod__fill_addr(&xsk->umem->fq, idx_fq++) = addr;
    }
    
    xsk_ring_cons__release(&xsk->rx, rcvd);
    xsk_ring_prod__submit(&xsk->umem->fq, rcvd);
}
```

---

## Tracing & Observability

### Kprobes/Uprobes for Dynamic Tracing

```c
// kprobe_tcp_connect.c - Trace TCP connection attempts
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

struct event {
    __u32 pid;
    __u32 saddr;
    __u32 daddr;
    __u16 dport;
    char comm[16];
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);
} events SEC(".maps");

SEC("kprobe/tcp_v4_connect")
int BPF_KPROBE(trace_tcp_connect, struct sock *sk) {
    struct event *e;
    
    e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e)
        return 0;
    
    e->pid = bpf_get_current_pid_tgid() >> 32;
    bpf_get_current_comm(&e->comm, sizeof(e->comm));
    
    // Read socket address from kernel struct
    BPF_CORE_READ_INTO(&e->saddr, sk, __sk_common.skc_rcv_saddr);
    BPF_CORE_READ_INTO(&e->daddr, sk, __sk_common.skc_daddr);
    BPF_CORE_READ_INTO(&e->dport, sk, __sk_common.skc_dport);
    
    bpf_ringbuf_submit(e, 0);
    return 0;
}

char _license[] SEC("license") = "GPL";
```

### bpftrace One-Liners

```bash
# Trace file opens by process
sudo bpftrace -e 'tracepoint:syscalls:sys_enter_openat { 
    printf("%s(%d) opened %s\n", comm, pid, str(args->filename)); 
}'

# TCP connection latency histogram
sudo bpftrace -e '
    kprobe:tcp_v4_connect { @start[tid] = nsecs; }
    kretprobe:tcp_v4_connect /@start[tid]/ {
        @latency_ns = hist(nsecs - @start[tid]);
        delete(@start[tid]);
    }'

# Distribution of read() sizes
sudo bpftrace -e 'tracepoint:syscalls:sys_exit_read /args->ret > 0/ { 
    @bytes = hist(args->ret); 
}'

# Count syscalls by process
sudo bpftrace -e 'tracepoint:raw_syscalls:sys_enter { 
    @syscalls[comm] = count(); 
}'
```

---

## Security Implications

### Threat Model

**Attack Surface:**
1. **Malicious eBPF Programs:**
   - Privilege escalation via verifier bypass
   - Kernel information leakage (Spectre-style)
   - Denial of service (resource exhaustion)

2. **Side Channels:**
   - Timing attacks via map operations
   - Speculative execution leaks (BPF_SPECULATION_BARRIER)
   - Cache-based attacks

3. **Map Poisoning:**
   - User-space writes malicious map data
   - XDP program uses unvalidated map values
   - Result: incorrect packet forwarding, crashes

**Mitigations:**

```c
// Defense 1: Validate ALL map data
struct backend *be = bpf_map_lookup_elem(&backends, &idx);
if (!be)
    return XDP_DROP;  // Fail closed

// Defense 2: Bounds checking even after map lookup
if (be->ip == 0 || be->port == 0)
    return XDP_DROP;

// Defense 3: Use verifier-enforced constraints
#define MAX_BACKENDS 32
if (backend_idx >= MAX_BACKENDS)  // Verifier can prove bounds
    return XDP_DROP;
```

### LSM eBPF for Runtime Security

```c
// lsm_file_open.c - Enforce file access policy
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

SEC("lsm/file_open")
int BPF_PROG(restrict_file_open, struct file *file, int ret) {
    // Only called if default LSM (SELinux, AppArmor) allows
    if (ret != 0)
        return ret;  // Already denied
    
    const char *filename = BPF_CORE_READ(file, f_path.dentry, d_name.name);
    
    // Block access to sensitive files
    char secret[] = "/etc/shadow";
    if (bpf_strncmp(filename, sizeof(secret), secret) == 0) {
        bpf_printk("Blocked access to %s by PID %d\n", 
                   filename, bpf_get_current_pid_tgid() >> 32);
        return -EPERM;
    }
    
    return 0;  // Allow
}

char _license[] SEC("license") = "GPL";
```

**Capabilities Required:**
- `CAP_BPF` (kernel 5.8+): Load/attach eBPF programs
- `CAP_NET_ADMIN`: XDP attachment
- `CAP_PERFMON`: Tracing/perf events
- `CAP_SYS_ADMIN`: Legacy fallback (all operations)

**Production Hardening:**
```bash
# Restrict BPF to admins only
sudo sysctl kernel.unprivileged_bpf_disabled=1

# Enable BPF JIT hardening (constant blinding)
sudo sysctl net.core.bpf_jit_harden=2

# Limit BPF JIT kallsyms exposure
sudo sysctl net.core.bpf_jit_kallsyms=0

# Audit BPF program loads
sudo auditctl -a always,exit -F arch=b64 -S bpf
```

---

## Performance Characteristics

### XDP Benchmark Results

**Test Setup:**
- CPU: Intel XeonGold 6248R (24 cores, 3.0GHz)
- NIC: Mellanox ConnectX-5 (100Gbps)
- Packet size: 64 bytes (minimum Ethernet)
- Test: Single-core packet drop (XDP_DROP)

| Mode | Throughput | Latency (p99) | CPU Usage |
|------|-----------|---------------|-----------|
| Kernel stack (no XDP) | 1.2 Mpps | 850 ns | 100% |
| XDP_SKB (generic) | 5.1 Mpps | 420 ns | 100% |
| XDP_NATIVE (driver) | 24.2 Mpps | 45 ns | 100% |
| XDP_OFFLOAD (SmartNIC) | 148 Mpps | 12 ns | 5% |

**AF_XDP vs DPDK (Zero-copy):**
- AF_XDP: 45 Mpps (single core, mlx5)
- DPDK: 48 Mpps (single core, same NIC)
- Winner: Effectively tied, AF_XDP has kernel integration benefits

### Optimization Techniques

```c
// 1. Avoid repeated map lookups (cache in registers)
struct backend *be = bpf_map_lookup_elem(&backends, &idx);
if (!be) return XDP_DROP;
__u32 ip = be->ip;  // Cache in register, not repeated reads

// 2. Use per-CPU maps to eliminate lock contention
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    ...
} stats;  // Each CPU has its own copy, no synchronization

// 3. Unroll loops (verifier limitation < 1M instructions)
#pragma unroll
for (int i = 0; i < 8; i++) {
    // Process up to 8 headers
}

// 4. Use BPF_CORE_READ for portable CO-RE (Compile Once, Run Everywhere)
__u32 daddr = BPF_CORE_READ(sk, __sk_common.skc_daddr);
// vs manual offset calculation (brittle across kernel versions)

// 5. Minimize helper calls (each has overhead)
// BAD:
for (int i = 0; i < 100; i++) {
    bpf_ktime_get_ns();  // Expensive, called 100 times
}
// GOOD:
__u64 now = bpf_ktime_get_ns();  // Once
```

---

## Tooling Ecosystem

### Core Tools

**bpftool (swiss army knife):**
```bash
# List all loaded programs
sudo bpftool prog show

# Dump program instructions
sudo bpftool prog dump xlated id 42

# Show JIT-compiled native code
sudo bpftool prog dump jited id 42

# Pin program to filesystem (persist across reboots)
sudo bpftool prog pin id 42 /sys/fs/bpf/my_prog

# Dump map contents
sudo bpftool map dump id 5

# Create map from user space
sudo bpftool map create /sys/fs/bpf/mymap type hash key 4 value 8 entries 1024
```

**BCC (BPF Compiler Collection):**
- Python/Lua frontend for rapid prototyping
- Built-in tools: execsnoop, tcpconnect, biolatency
- Use case: One-off debugging, performance analysis

```python
# BCC example: trace all file opens
from bcc import BPF

prog = """
int trace_open(struct pt_regs *ctx, const char __user *filename) {
    char fn[256];
    bpf_probe_read_user_str(fn, sizeof(fn), filename);
    bpf_trace_printk("open: %s\\n", fn);
    return 0;
}
"""

b = BPF(text=prog)
b.attach_kprobe(event="do_sys_openat2", fn_name="trace_open")
b.trace_print()
```

**libbpf-tools (CO-RE-based):**
- Modern replacement for BCC tools
- Portable across kernel versions (BTF-based)
- Lower overhead, no LLVM runtime dependency

### Debugging

```bash
# Enable verifier logging
sudo bpftool prog load xdp_prog.o /sys/fs/bpf/prog \
    log_level 2 log_size 1048576

# Trace eBPF program execution
sudo bpftrace -e 'tracepoint:bpf:bpf_prog_* { 
    printf("%s id=%d\n", probe, args->id); 
}'

# Check for verifier errors
dmesg | grep -i bpf

# Profile eBPF program performance
sudo perf record -e bpf:bpf_prog_run -a -g
sudo perf report
```

---

## Production Deployment

### Cilium (Service Mesh Data Plane)

**Architecture:**
```
┌─────────────────────────────────────────────────┐
│              Kubernetes Cluster                  │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐   │
│  │   Pod A   │  │   Pod B   │  │   Pod C   │   │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘   │
│        │              │              │          │
│        └──────────────┴──────────────┘          │
│                       │                         │
│         ┌─────────────▼─────────────┐           │
│         │  Cilium Agent (per node)  │           │
│         │  • eBPF programs          │           │
│         │  • Identity management    │           │
│         │  • Policy enforcement     │           │
│         └─────────────┬─────────────┘           │
│                       │                         │
│         ┌─────────────▼─────────────┐           │
│         │  eBPF Hooks:              │           │
│         │  • XDP (ingress)          │           │
│         │  • TC (egress/ingress)    │           │
│         │  • Socket (L7 proxy)      │           │
│         │  • Cgroup (resource ctrl) │           │
│         └────────────────────────────┘           │
└──────────────────────────────────────────────────┘
```

**Key Features:**
- Identity-based networking (vs IP-based)
- L3/L4/L7 policy enforcement
- Transparent encryption (WireGuard/IPsec)
- Hubble observability (Flow logs via eBPF)

```bash
# Install Cilium (Kubernetes)
cilium install --version 1.14.5

# Enable Hubble for flow monitoring
cilium hubble enable --ui

# Apply network policy (eBPF-enforced)
kubectl apply -f - <<EOF
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: allow-frontend-to-backend
spec:
  endpointSelector:
    matchLabels:
      role: backend
  ingress:
  - fromEndpoints:
    - matchLabels:
        role: frontend
    toPorts:
    - ports:
      - port: "8080"
        protocol: TCP
EOF

# Monitor flows
hubble observe --namespace default
```

### Katran (Layer 4 Load Balancer - Facebook/Meta)

- XDP-based L4 LB (replacement for LVS)
- Consistent hashing for backend selection
- 10M+ concurrent connections per server
- Used in Meta production since 2017

```bash
# Build Katran
git clone https://github.com/facebookincubator/katran
cd katran
./build_katran.sh

# Configure VIP (Virtual IP)
katran_goclient -A -t 203.0.113.10:80 -r 192.168.1.10:8080 -w 100
katran_goclient -A -t 203.0.113.10:80 -r 192.168.1.11:8080 -w 100

# Monitor stats
katran_goclient -stats
```

### Falco (Runtime Security)

- eBPF-based threat detection
- Detects anomalous behavior (file access, network, process)
- Rules engine for security policies

```yaml
# /etc/falco/falco_rules.yaml
- rule: Unauthorized Process in Container
  desc: Detect processes not in allowlist
  condition: >
    container and proc.name not in (allowed_processes)
  output: >
    Unexpected process in container (user=%user.name command=%proc.cmdline 
    container=%container.name)
  priority: WARNING
```

---

## Testing & Validation

### Unit Testing eBPF Programs

```c
// xdp_test.c - Test harness using BPF_PROG_TEST_RUN
#include <linux/bpf.h>
#include <bpf/libbpf.h>

int test_xdp_drop() {
    struct bpf_object *obj;
    struct bpf_program *prog;
    int prog_fd, err;
    
    // Load program
    obj = bpf_object__open_file("xdp_firewall.o", NULL);
    bpf_object__load(obj);
    prog = bpf_object__find_program_by_name(obj, "xdp_firewall_func");
    prog_fd = bpf_program__fd(prog);
    
    // Craft test packet (blacklisted IP)
    char pkt[128] = { /* Ethernet + IP headers */ };
    struct iphdr *ip = (struct iphdr *)(pkt + 14);
    ip->saddr = htonl(0xC0000201);  // 192.0.2.1 (blacklisted)
    
    // Run test
    __u32 retval, duration;
    struct bpf_test_run_opts opts = {
        .data_in = pkt,
        .data_size_in = sizeof(pkt),
        .repeat = 1,
    };
    
    err = bpf_prog_test_run_opts(prog_fd, &opts);
    
    // Verify XDP_DROP returned
    assert(opts.retval == XDP_DROP);
    
    bpf_object__close(obj);
    return 0;
}
```

### Fuzzing

```bash
# Syzkaller (kernel fuzzer with eBPF support)
git clone https://github.com/google/syzkaller
cd syzkaller
make

# Configure eBPF syscall fuzzing
cat > syzkaller.cfg <<EOF
{
    "target": "linux/amd64",
    "http": "127.0.0.1:56741",
    "workdir": "/tmp/syzkaller",
    "kernel_obj": "/path/to/linux",
    "syzkaller": "/path/to/syzkaller",
    "enable_syscalls": ["bpf"],
    "reproduce": true
}
EOF

# Run fuzzer (finds verifier bypasses, crashes)
./bin/syz-manager -config syzkaller.cfg
```

### Performance Benchmarking

```bash
# pktgen (kernel packet generator)
modprobe pktgen
echo "add_device eth0" > /proc/net/pktgen/kpktgend_0
cat > /proc/net/pktgen/eth0 <<EOF
pkt_size 64
count 100000000
dst 203.0.113.1
dst_mac 00:11:22:33:44:55
EOF
echo "start" > /proc/net/pktgen/pgctrl

# TRex (realistic traffic generator)
./t-rex-64 -f cap2/dns.yaml -m 100Gbps -d 60

# XDP-bench (XDP-specific microbenchmarks)
xdp-bench drop eth0  # Measure maximum drop rate
xdp-bench tx eth0    # Measure redirect throughput
```

---

## Rollout Plan

### Phase 1: Development & Testing (Week 1-2)
```bash
# Step 1: Setup development environment
sudo apt install -y linux-headers-$(uname -r) clang llvm libbpf-dev

# Step 2: Build & test XDP firewall (from earlier example)
clang -O2 -target bpf -c xdp_firewall.c -o xdp_firewall.o
sudo ip link set dev lo xdp obj xdp_firewall.o sec xdp  # Test on loopback

# Step 3: Unit test with crafted packets
./xdp_test  # Run test harness

# Step 4: Performance baseline
xdp-bench drop lo
```

### Phase 2: Staging Deployment (Week 3)
```bash
# Step 1: Deploy to staging NIC (non-production traffic)
sudo ip link set dev eth1 xdp obj xdp_firewall.o sec xdp

# Step 2: Monitor metrics (Prometheus + Grafana)
# Expose map stats via /metrics endpoint (using cilium/ebpf)

# Step 3: Stress test with TRex
./t-rex-64 -f malicious-traffic.yaml -d 300

# Step 4: Validate drop accuracy (compare logs)
diff expected_drops.txt actual_drops.txt
```

### Phase 3: Canary Production (Week 4)
```bash
# Step 1: Deploy to 5% of production hosts
ansible-playbook -i inventory/prod_canary deploy_xdp.yml

# Step 2: Monitor error rates (CloudWatch/Datadog)
# Alert on: packet loss, connection errors, CPU spikes

# Step 3: Gradual rollout: 5% → 25% → 50% → 100%
# Each stage: 24hr bake time + validation
```

### Rollback Procedure
```bash
# Emergency rollback (< 30 seconds)
sudo ip link set dev eth0 xdp off

# Automated health check (runs every 10s)
#!/bin/bash
if ! curl -f http://localhost:8080/health; then
    echo "Health check failed, rolling back XDP"
    ip link set dev eth0 xdp off
    systemctl restart networking
fi
```

---

## Threat Model & Mitigations

| Threat | Impact | Likelihood | Mitigation |
|--------|--------|-----------|-----------|
| Verifier bypass → RCE | Critical | Low | Keep kernel updated (CVE monitoring), fuzz verifier |
| Map poisoning → incorrect forwarding | High | Medium | Validate all map data, fail closed |
| Resource exhaustion (CPU) | Medium | Medium | Limit per-prog instruction count, CPU pinning |
| Side-channel leaks | Low | Low | Disable unprivileged BPF, use speculation barriers |
| Incorrect policy → outage | High | Medium | Staged rollout, automated rollback, comprehensive testing |

**Defense-in-Depth:**
1. **Least Privilege:** CAP_BPF only, no CAP_SYS_ADMIN
2. **Monitoring:** Audit all `bpf()` syscalls, alert on anomalies
3. **Validation:** Formal verification (research: eBPF verifier proofs)
4. **Isolation:** Separate control plane (user-space) from data plane (kernel)

---

## Next 3 Steps

1. **Build & Deploy XDP Firewall:**
   - Implement the basic firewall from earlier examples
   - Test on loopback interface, then staging NIC
   - Measure baseline performance: `xdp-bench drop <interface>`
   - Expected: 20+ Mpps single-core on modern hardware

2. **Integrate with Existing Monitoring:**
   - Export map statistics to Prometheus using Go control plane
   - Create Grafana dashboard: packets passed/dropped, latency histogram
   - Setup alerts: drop rate spike, connection errors
   - Command: `promtool check rules xdp_alerts.yml`

3. **Explore Cilium for K8s Networking:**
   - Deploy Cilium in test cluster: `cilium install`
   - Enable Hubble: `cilium hubble enable`
   - Replace kube-proxy with eBPF: `cilium config set kube-proxy-replacement strict`
   - Observe flow logs: `hubble observe --namespace default`

---

## References

**Official Documentation:**
- Linux kernel BPF docs: https://docs.kernel.org/bpf/
- Cilium eBPF reference: https://docs.cilium.io/en/stable/bpf/
- XDP tutorial: https://github.com/xdp-project/xdp-tutorial

**Books:**
- "Linux Observability with BPF" (Calavera & Lorenzo, O'Reilly)
- "BPF Performance Tools" (Gregg, Addison-Wesley)

**Papers:**
- "The BSD Packet Filter: A New Architecture for User-level Packet Capture" (McCanne & Jacobson, USENIX 1993)
- "Fast Packet Processing with eBPF and XDP" (Høiland-Jørgensen et al., CoNEXT 2018)

**Security:**
- CVE database: https://cve.mitre.org (search "eBPF verifier")
- Kernel self-protection: https://kernsec.org/wiki/index.php/Kernel_Self_Protection_Project

**Tools:**
- bpftool source: https://github.com/torvalds/linux/tree/master/tools/bpf/bpftool
- libbpf: https://github.com/libbpf/libbpf
- Cilium/eBPF Go library: https://github.com/cilium/ebpf

This guide covers the essential concepts, practical implementation, security considerations, and production deployment patterns for XDP and eBPF. Focus on the hands-on examples and build real systems to solidify understanding.

# BPF CO-RE, libbpf, and bpftrace: Comprehensive Technical Guide

**Summary**: BPF CO-RE (Compile Once – Run Everywhere) eliminates kernel version dependencies by embedding BTF (BPF Type Format) metadata, enabling portable eBPF programs across kernel versions. libbpf is the canonical user-space library for loading, verifying, and managing BPF programs with CO-RE support. bpftrace provides a high-level scripting language for rapid observability and troubleshooting. Together, they form the modern eBPF stack for production observability, security enforcement, and performance optimization. This guide covers architecture, development workflows, security boundaries, CO-RE relocation mechanics, and production deployment patterns.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Space                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  bpftrace    │  │   libbpf     │  │  Custom C/   │          │
│  │  (HLL)       │  │   loader     │  │  Rust/Go     │          │
│  │              │  │              │  │  programs    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                    │
│         └─────────────────┴─────────────────┘                    │
│                           │                                      │
│                    ┌──────▼──────┐                               │
│                    │   libbpf    │                               │
│                    │   API       │                               │
│                    └──────┬──────┘                               │
│                           │                                      │
│         ┌─────────────────┴─────────────────┐                   │
│         │                                   │                    │
│  ┌──────▼──────┐                    ┌──────▼──────┐            │
│  │ BPF ELF     │                    │  BTF Data   │            │
│  │ Object      │                    │  (vmlinux.h)│            │
│  │ (.o file)   │                    │             │            │
│  └──────┬──────┘                    └──────┬──────┘            │
│         │                                   │                    │
│         └─────────────────┬─────────────────┘                   │
│                           │                                      │
│                    ┌──────▼──────┐                               │
│                    │  bpf()      │                               │
│                    │  syscall    │                               │
│                    └──────┬──────┘                               │
└───────────────────────────┼──────────────────────────────────────┘
                            │
════════════════════════════╪════════════════════════════════════════
                            │
┌───────────────────────────┼──────────────────────────────────────┐
│                    Kernel Space                                   │
├───────────────────────────┼──────────────────────────────────────┤
│                    ┌──────▼──────┐                               │
│                    │ BPF Verifier│                               │
│                    │  - Safety   │                               │
│                    │  - CO-RE    │                               │
│                    │  Relocation │                               │
│                    └──────┬──────┘                               │
│                           │                                      │
│                    ┌──────▼──────┐                               │
│                    │   BPF JIT   │                               │
│                    │  Compiler   │                               │
│                    └──────┬──────┘                               │
│                           │                                      │
│         ┌─────────────────┴─────────────────┐                   │
│         │                                   │                    │
│  ┌──────▼──────┐  ┌──────────┐  ┌──────────▼──────┐            │
│  │ BPF Maps    │  │ BPF      │  │ Hook Points:    │            │
│  │ (shared     │◄─┤ Programs │◄─┤ - kprobes       │            │
│  │  state)     │  │ (running)│  │ - tracepoints   │            │
│  │             │  │          │  │ - LSM hooks     │            │
│  └─────────────┘  └──────────┘  │ - XDP/TC        │            │
│                                  │ - cgroup hooks  │            │
│                                  └─────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. BPF CO-RE (Compile Once – Run Everywhere)

### 1.1 Core Concepts

**Problem CO-RE Solves**: Traditional BPF programs break when kernel data structures change across versions. CO-RE enables single-binary portability through BTF metadata and runtime relocations.

**Key Components**:
- **BTF (BPF Type Format)**: Compact type information embedded in kernel and BPF objects
- **vmlinux.h**: Single header with all kernel types, generated from kernel BTF
- **Relocations**: libbpf rewrites field offsets at load time based on target kernel's BTF
- **Preserve Access Index**: `__builtin_preserve_access_index()` intrinsic records field access patterns

### 1.2 BTF Deep Dive

BTF encoding:
```c
// Kernel structure
struct task_struct {
    volatile long state;
    void *stack;
    pid_t pid;
    // ... 200+ more fields
};

// BTF records:
// - Type ID
// - Field names
// - Field offsets
// - Field types
// - Nested structure layout
```

BTF in kernel:
```bash
# Check kernel BTF support
zgrep CONFIG_DEBUG_INFO_BTF /proc/config.gz

# Dump kernel BTF
bpftool btf dump file /sys/kernel/btf/vmlinux format c > vmlinux.h

# View specific type
bpftool btf dump file /sys/kernel/btf/vmlinux format c | grep -A 20 "^struct task_struct"
```

### 1.3 CO-RE Relocation Mechanics

**Relocation Types**:
1. **Field Existence**: Check if field exists in target kernel
2. **Field Offset**: Compute byte offset of field
3. **Field Size**: Get size of field
4. **Type Existence**: Verify type exists
5. **Enum Value**: Resolve enum constant

Example with relocations:
```c
// bpf_program.bpf.c
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_core_read.h>

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 10240);
    __type(key, u32);
    __type(value, u64);
} pid_map SEC(".maps");

SEC("tp/sched/sched_process_exec")
int trace_exec(struct trace_event_raw_sched_process_exec *ctx) {
    struct task_struct *task = (struct task_struct *)bpf_get_current_task();
    
    // CO-RE: reads pid regardless of task_struct layout changes
    u32 pid = BPF_CORE_READ(task, pid);
    u64 start_time = BPF_CORE_READ(task, start_time);
    
    bpf_map_update_elem(&pid_map, &pid, &start_time, BPF_ANY);
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
```

**BPF_CORE_READ Macro Expansion**:
```c
// What BPF_CORE_READ(task, pid) becomes:
({
    typeof(task->pid) __r;
    __builtin_preserve_access_index(({
        __r = task->pid;
    }));
    __r;
})
```

Compiler generates relocation records:
```
RELOCATION RECORD:
- Instruction offset: 42
- Type: FIELD_OFFSET
- Access string: "0:129" (struct index 0, field index 129)
- Target type: task_struct
- Target field: pid
```

At load time, libbpf:
1. Reads target kernel's BTF from `/sys/kernel/btf/vmlinux`
2. Finds `task_struct.pid` offset in target kernel (e.g., offset 1024)
3. Patches instruction immediate value from compile-time offset to 1024
4. Passes patched program to verifier

### 1.4 CO-RE Helpers

```c
// Check if field exists
if (bpf_core_field_exists(task->cgroups)) {
    // Use cgroups field (added in specific kernel version)
}

// Get field size (handles type size changes)
int size = bpf_core_field_size(task->comm);

// Type-based conditional compilation
if (bpf_core_type_exists(struct io_uring_task)) {
    // io_uring-specific logic
}

// Read with fallback for missing fields
int val = BPF_CORE_READ_BITFIELD(task, flags);

// Enum value relocation
enum {
    MY_CONST = 0,
} __attribute__((preserve_access_index));
```

---

## 2. libbpf: Canonical User-Space Library

### 2.1 Architecture and Components

**Core Modules**:
- **ELF Loader**: Parses BPF ELF objects, extracts sections
- **BTF Resolver**: Loads kernel and program BTF, performs type matching
- **Relocation Engine**: Applies CO-RE relocations
- **Program Loader**: Invokes bpf() syscall, attaches to hooks
- **Map Manager**: Creates, manages BPF maps
- **Ring Buffer**: Efficient event streaming from kernel to user-space

### 2.2 Development Workflow

**Build System Setup**:
```bash
# Install dependencies (Ubuntu/Debian)
apt-get install -y clang llvm libbpf-dev linux-headers-$(uname -r) \
                   bpftool linux-tools-common linux-tools-generic

# Generate vmlinux.h (once per development machine)
bpftool btf dump file /sys/kernel/btf/vmlinux format c > vmlinux.h

# Verify BTF availability
ls -lh /sys/kernel/btf/vmlinux
# Should show ~4-8MB file
```

**Project Structure**:
```
project/
├── src/
│   ├── bpf/
│   │   ├── my_program.bpf.c      # BPF C code
│   │   └── my_program.h          # Shared definitions
│   ├── my_program.c              # User-space loader
│   └── my_program.skel.h         # Generated skeleton (auto)
├── vmlinux.h                     # Kernel types
├── Makefile
└── README.md
```

**Makefile**:
```makefile
# Makefile for CO-RE BPF program
CLANG ?= clang
LLVM_STRIP ?= llvm-strip
BPFTOOL ?= bpftool
ARCH := $(shell uname -m | sed 's/x86_64/x86/' | sed 's/aarch64/arm64/')

LIBBPF_INCLUDES := -I/usr/include
BPF_INCLUDES := -I. -I./src/bpf

CFLAGS := -g -O2 -Wall -Werror
BPF_CFLAGS := -g -O2 -target bpf -D__TARGET_ARCH_$(ARCH) \
              $(BPF_INCLUDES) $(LIBBPF_INCLUDES) \
              -Wall -Werror

.PHONY: all clean

all: my_program

# Generate vmlinux.h (run once)
vmlinux.h:
	$(BPFTOOL) btf dump file /sys/kernel/btf/vmlinux format c > vmlinux.h

# Compile BPF program to .o
src/bpf/my_program.bpf.o: src/bpf/my_program.bpf.c vmlinux.h
	$(CLANG) $(BPF_CFLAGS) -c $< -o $@
	$(LLVM_STRIP) -g $@

# Generate skeleton header
src/my_program.skel.h: src/bpf/my_program.bpf.o
	$(BPFTOOL) gen skeleton $< > $@

# Compile user-space loader
my_program: src/my_program.c src/my_program.skel.h
	$(CLANG) $(CFLAGS) $(LIBBPF_INCLUDES) $< -lbpf -lelf -lz -o $@

clean:
	rm -f src/bpf/*.o src/*.skel.h my_program
```

### 2.3 BPF Program Example

**BPF Kernel Code** (`src/bpf/my_program.bpf.c`):
```c
// SPDX-License-Identifier: GPL-2.0
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>

char LICENSE[] SEC("license") = "GPL";

// Map: PID -> execution count
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 10240);
    __type(key, u32);
    __type(value, u64);
} exec_count SEC(".maps");

// Ring buffer for events
struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024); // 256KB
} events SEC(".maps");

// Event structure
struct exec_event {
    u32 pid;
    u32 ppid;
    char comm[16];
    char filename[256];
};

SEC("tp/sched/sched_process_exec")
int trace_exec(struct trace_event_raw_sched_process_exec *ctx) {
    struct task_struct *task = (struct task_struct *)bpf_get_current_task();
    struct exec_event *evt;
    u32 pid;
    u64 *count, one = 1;

    // Read PID with CO-RE
    pid = BPF_CORE_READ(task, pid);
    
    // Update exec count
    count = bpf_map_lookup_elem(&exec_count, &pid);
    if (count) {
        __sync_fetch_and_add(count, 1);
    } else {
        bpf_map_update_elem(&exec_count, &pid, &one, BPF_ANY);
    }

    // Send event to ring buffer
    evt = bpf_ringbuf_reserve(&events, sizeof(*evt), 0);
    if (!evt)
        return 0;

    evt->pid = pid;
    evt->ppid = BPF_CORE_READ(task, real_parent, pid);
    bpf_probe_read_kernel_str(&evt->comm, sizeof(evt->comm), 
                               BPF_CORE_READ(task, comm));
    bpf_probe_read_user_str(&evt->filename, sizeof(evt->filename),
                            (void *)ctx->filename);

    bpf_ringbuf_submit(evt, 0);
    return 0;
}
```

**User-Space Loader** (`src/my_program.c`):
```c
// SPDX-License-Identifier: GPL-2.0
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>
#include <errno.h>
#include <bpf/libbpf.h>
#include "my_program.skel.h"

static volatile bool stop = false;

static void sig_handler(int sig) {
    stop = true;
}

static int handle_event(void *ctx, void *data, size_t data_sz) {
    const struct exec_event *evt = data;
    
    printf("PID: %-6d PPID: %-6d COMM: %-16s FILE: %s\n",
           evt->pid, evt->ppid, evt->comm, evt->filename);
    return 0;
}

int main(int argc, char **argv) {
    struct my_program_bpf *skel;
    struct ring_buffer *rb = NULL;
    int err;

    // Set up libbpf logging
    libbpf_set_print(NULL);

    // Open BPF skeleton
    skel = my_program_bpf__open();
    if (!skel) {
        fprintf(stderr, "Failed to open BPF skeleton\n");
        return 1;
    }

    // Load and verify BPF programs
    err = my_program_bpf__load(skel);
    if (err) {
        fprintf(stderr, "Failed to load BPF skeleton: %d\n", err);
        goto cleanup;
    }

    // Attach BPF programs
    err = my_program_bpf__attach(skel);
    if (err) {
        fprintf(stderr, "Failed to attach BPF programs: %d\n", err);
        goto cleanup;
    }

    // Set up ring buffer polling
    rb = ring_buffer__new(bpf_map__fd(skel->maps.events), 
                          handle_event, NULL, NULL);
    if (!rb) {
        err = -errno;
        fprintf(stderr, "Failed to create ring buffer\n");
        goto cleanup;
    }

    printf("Tracing exec events... Ctrl-C to exit\n");

    signal(SIGINT, sig_handler);
    signal(SIGTERM, sig_handler);

    // Poll for events
    while (!stop) {
        err = ring_buffer__poll(rb, 100); // 100ms timeout
        if (err == -EINTR) {
            err = 0;
            break;
        }
        if (err < 0) {
            fprintf(stderr, "Error polling ring buffer: %d\n", err);
            break;
        }
    }

cleanup:
    ring_buffer__free(rb);
    my_program_bpf__destroy(skel);
    return err < 0 ? -err : 0;
}
```

**Build and Run**:
```bash
# Build
make clean && make

# Run (requires root)
sudo ./my_program

# In another terminal, generate events
ls /tmp
ps aux | head
```

### 2.4 Advanced libbpf Features

**Global Variables**:
```c
// In BPF program
const volatile bool filter_root = false; // Can be set from user-space
const volatile u32 target_pid = 0;

SEC("tp/sched/sched_process_exec")
int trace_exec(struct trace_event_raw_sched_process_exec *ctx) {
    u32 pid = bpf_get_current_pid_tgid() >> 32;
    
    if (target_pid && pid != target_pid)
        return 0;
    
    if (filter_root) {
        u64 uid = bpf_get_current_uid_gid() & 0xFFFFFFFF;
        if (uid == 0)
            return 0;
    }
    
    // ... rest of logic
}

// In user-space
skel = my_program_bpf__open();
skel->rodata->filter_root = true;
skel->rodata->target_pid = 1234;
my_program_bpf__load(skel);
```

**Map Pinning** (persist maps across program restarts):
```c
// In BPF program
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 10240);
    __uint(pinning, LIBBPF_PIN_BY_NAME); // Auto-pin
    __type(key, u32);
    __type(value, u64);
} persistent_map SEC(".maps");

// Maps pinned to /sys/fs/bpf/<map_name>
// User-space: automatic via skeleton
// Manual: bpf_obj_pin(map_fd, "/sys/fs/bpf/my_map")
```

**Tail Calls** (program chaining):
```c
struct {
    __uint(type, BPF_MAP_TYPE_PROG_ARRAY);
    __uint(max_entries, 10);
    __type(key, u32);
    __type(value, u32);
} prog_array SEC(".maps");

SEC("xdp")
int xdp_router(struct xdp_md *ctx) {
    // Parse packet, determine next program
    bpf_tail_call(ctx, &prog_array, next_prog_idx);
    return XDP_PASS; // Fallback if tail call fails
}
```

---

## 3. bpftrace: High-Level Scripting

### 3.1 Language Syntax

bpftrace provides awk-like syntax for rapid BPF development:

```
probe_type:identifier[:filter] { actions }
```

**Basic Script**:
```bash
# Count syscalls by process
bpftrace -e 'tracepoint:raw_syscalls:sys_enter { @[comm] = count(); }'

# Trace file opens
bpftrace -e 'tracepoint:syscalls:sys_enter_openat { 
    printf("%s opened %s\n", comm, str(args->filename)); 
}'

# Histogram of syscall latency
bpftrace -e '
tracepoint:raw_syscalls:sys_enter {
    @start[tid] = nsecs;
}
tracepoint:raw_syscalls:sys_exit /@start[tid]/ {
    @latency_ns = hist(nsecs - @start[tid]);
    delete(@start[tid]);
}'
```

### 3.2 Probe Types

```bash
# Tracepoints (stable kernel API)
tracepoint:sched:sched_switch { }
tracepoint:syscalls:sys_enter_* { }

# kprobes (dynamic kernel function tracing)
kprobe:do_sys_open { }
kretprobe:do_sys_open { }  # Function return

# uprobes (user-space function tracing)
uprobe:/lib/x86_64-linux-gnu/libc.so.6:malloc { }
uretprobe:/lib/x86_64-linux-gnu/libc.so.6:malloc { }

# USDT (user-space static probes)
usdt:/usr/lib/libpthread.so:pthread:pthread_create { }

# kfunc (BPF-specific kernel functions, typed arguments)
kfunc:tcp_sendmsg { }

# Profile (timed sampling)
profile:hz:99 { }  # 99 times per second
interval:s:1 { }   # Every second

# Hardware events
hardware:cpu-cycles:1000000 { }
```

### 3.3 Built-in Variables and Functions

**Variables**:
```bash
pid       # Process ID
tid       # Thread ID
uid       # User ID
gid       # Group ID
comm      # Process name (16 chars)
nsecs     # Nanosecond timestamp
cpu       # CPU ID
func      # Function name (kprobe/uprobe)
retval    # Return value (kretprobe/uretprobe)
arg0-argN # Function arguments
args      # Tracepoint arguments (struct)
```

**Functions**:
```bash
# String operations
str(ptr)              # Convert pointer to string
printf(fmt, ...)      # Print formatted

# Time
nsecs                 # Current timestamp
elapsed               # Nanoseconds since program start

# Stack traces
kstack                # Kernel stack trace
ustack                # User-space stack trace

# Statistics
count()               # Count events
sum(n)                # Sum values
avg(n)                # Average
min(n)/max(n)         # Min/Max
hist(n)               # Power-of-2 histogram
lhist(n, min, max, step) # Linear histogram

# System
system(cmd)           # Execute shell command
exit()                # Exit program
```

### 3.4 Advanced bpftrace Patterns

**Process Monitoring**:
```bash
#!/usr/bin/env bpftrace
# exec_trace.bt - Detailed process execution tracking

BEGIN {
    printf("Tracing process execution... Ctrl-C to end\n");
}

tracepoint:sched:sched_process_exec {
    printf("%s: PID %d (%s) exec: %s\n",
           strftime("%H:%M:%S", nsecs),
           pid, comm, str(args->filename));
    @execs[comm] = count();
}

tracepoint:sched:sched_process_fork {
    printf("%s: PID %d forked to PID %d\n",
           strftime("%H:%M:%S", nsecs),
           args->parent_pid, args->child_pid);
}

tracepoint:sched:sched_process_exit {
    @exits[comm] = count();
}

END {
    printf("\n--- Summary ---\n");
    printf("Execs by command:\n");
    print(@execs);
    printf("\nExits by command:\n");
    print(@exits);
    
    clear(@execs);
    clear(@exits);
}
```

**Network Analysis**:
```bash
#!/usr/bin/env bpftrace
# tcp_life.bt - TCP connection lifetimes

#include <net/sock.h>

kprobe:tcp_set_state {
    $sk = (struct sock *)arg0;
    $state = arg1;
    
    if ($state == TCP_ESTABLISHED) {
        @start[tid] = nsecs;
        @saddr[tid] = $sk->__sk_common.skc_rcv_saddr;
        @daddr[tid] = $sk->__sk_common.skc_daddr;
        @sport[tid] = $sk->__sk_common.skc_num;
        @dport[tid] = $sk->__sk_common.skc_dport;
    }
    
    if ($state == TCP_CLOSE && @start[tid]) {
        $duration_ms = (nsecs - @start[tid]) / 1000000;
        
        printf("%s -> %s:%d (%d ms)\n",
               ntop(AF_INET, @saddr[tid]),
               ntop(AF_INET, @daddr[tid]),
               @dport[tid],
               $duration_ms);
        
        @lifetime_ms = hist($duration_ms);
        
        delete(@start[tid]);
        delete(@saddr[tid]);
        delete(@daddr[tid]);
        delete(@sport[tid]);
        delete(@dport[tid]);
    }
}

END {
    printf("\nTCP Connection Lifetime Distribution (ms):\n");
    print(@lifetime_ms);
}
```

**Memory Allocation Tracking**:
```bash
#!/usr/bin/env bpftrace
# malloc_trace.bt - User-space memory allocations

uprobe:/lib/x86_64-linux-gnu/libc.so.6:malloc {
    @size[tid] = arg0;
    @ts[tid] = nsecs;
}

uretprobe:/lib/x86_64-linux-gnu/libc.so.6:malloc /@ts[tid]/ {
    $latency_us = (nsecs - @ts[tid]) / 1000;
    @allocs[comm, @size[tid]] = count();
    @latency_us[comm] = hist($latency_us);
    
    if (@size[tid] > 1024*1024) {
        printf("Large alloc: %s PID %d: %d bytes\n",
               comm, pid, @size[tid]);
    }
    
    delete(@size[tid]);
    delete(@ts[tid]);
}

uprobe:/lib/x86_64-linux-gnu/libc.so.6:free {
    @frees[comm] = count();
}

interval:s:5 {
    printf("\n=== Last 5 seconds ===\n");
    print(@allocs);
    print(@frees);
    clear(@allocs);
    clear(@frees);
}

END {
    printf("\nMalloc Latency Distribution (us):\n");
    print(@latency_us);
}
```

---

## 4. Security Model and Threat Analysis

### 4.1 BPF Isolation Boundaries

```
┌────────────────────────────────────────────────────────┐
│                    Threat Surface                       │
├────────────────────────────────────────────────────────┤
│                                                         │
│  ┌────────────────┐         ┌────────────────┐        │
│  │ Untrusted      │         │ Privileged     │        │
│  │ User Space     │         │ User Space     │        │
│  │                │         │ (CAP_BPF,      │        │
│  │ - No BPF       │         │  CAP_PERFMON)  │        │
│  │   access       │         │                │        │
│  └────────────────┘         └───────┬────────┘        │
│                                     │                  │
│                              bpf() syscall             │
│                                     │                  │
├─────────────────────────────────────┼──────────────────┤
│                             ┌───────▼────────┐         │
│   Kernel                    │  BPF Verifier  │         │
│   Trust                     │                │         │
│   Boundary                  │  - Type safety │         │
│                             │  - Memory      │         │
│                             │    bounds      │         │
│                             │  - Loop limits │         │
│                             │  - Pointer     │         │
│                             │    leaks       │         │
│                             └───────┬────────┘         │
│                                     │                  │
│                              ┌──────▼──────┐           │
│                              │  BPF JIT    │           │
│                              │  (optional) │           │
│                              └──────┬──────┘           │
│                                     │                  │
│                     ┌───────────────┴────────────┐     │
│                     │                            │     │
│              ┌──────▼──────┐          ┌─────────▼────┐│
│              │ BPF Program │          │ BPF Maps     ││
│              │ Execution   │◄────────►│ (isolated)   ││
│              │             │          │              ││
│              │ - No loops  │          │ - Spinlocks  ││
│              │ - No unbnd  │          │ - Per-CPU    ││
│              │   memory    │          │ - RCU        ││
│              └─────────────┘          └──────────────┘│
└────────────────────────────────────────────────────────┘
```

# BPF CO-RE, libbpf, and bpftrace: Comprehensive Technical Guide

**Summary**: BPF (Berkeley Packet Filter) has evolved from a packet filtering mechanism into a general-purpose in-kernel virtual machine for safe, high-performance observability, tracing, networking, and security. CO-RE (Compile Once – Run Everywhere) solves the kernel version portability problem using BTF (BPF Type Format) and libbpf. libbpf is the canonical userspace library for loading, verifying, and managing BPF programs. bpftrace provides a high-level scripting language for rapid BPF program development. Together, they form the foundation for modern Linux observability, security enforcement (LSM BPF), and programmable networking (XDP, TC).

---

## 1. BPF Fundamentals

### 1.1 Architecture & Evolution

**Classic BPF (cBPF)**:
- Originally designed for tcpdump packet filtering (1992)
- Simple instruction set, limited to packet filtering
- In-kernel JIT compilation for performance
- Filter expressions compiled to bytecode, executed in kernel

**Extended BPF (eBPF)**:
- Modernized in Linux 3.18+ (2014), now referred to simply as "BPF"
- 64-bit registers (r0-r10), 512-byte stack per program
- Rich instruction set: ALU ops, memory access, function calls, maps
- Verifier ensures safety: no loops (except bounded), no unbounded memory access
- JIT compilation to native code (x86_64, ARM64, etc.)
- Helper functions: ~200+ kernel functions callable from BPF
- Maps: shared data structures between kernel BPF programs and userspace

**BPF Virtual Machine**:
```
┌─────────────────────────────────────────────────────┐
│                   Userspace                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │ libbpf   │  │ bpftrace │  │ bpftool  │         │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘         │
│       │             │             │                 │
│       └─────────────┴─────────────┘                 │
│                     │                               │
├─────────────────────┼───────────────────────────────┤
│                Kernel Space                         │
│       ┌─────────────▼─────────────┐                │
│       │   BPF Syscall Interface   │                │
│       └─────────────┬─────────────┘                │
│       ┌─────────────▼─────────────┐                │
│       │      BPF Verifier         │                │
│       │  (Safety checks, bounds)  │                │
│       └─────────────┬─────────────┘                │
│       ┌─────────────▼─────────────┐                │
│       │    JIT Compiler (x86/ARM) │                │
│       └─────────────┬─────────────┘                │
│       ┌─────────────▼─────────────┐                │
│       │   BPF Program Execution   │                │
│       │  ┌────┐ ┌────┐ ┌────┐    │                │
│       │  │Maps│ │Hooks│ │Help│    │                │
│       │  └────┘ └────┘ └────┘    │                │
│       └───────────────────────────┘                │
└─────────────────────────────────────────────────────┘
```

### 1.2 BPF Program Types

**Tracing**:
- `BPF_PROG_TYPE_KPROBE`: Kernel function entry/exit instrumentation
- `BPF_PROG_TYPE_TRACEPOINT`: Static kernel tracepoints
- `BPF_PROG_TYPE_PERF_EVENT`: Hardware/software performance counters
- `BPF_PROG_TYPE_RAW_TRACEPOINT`: Low-overhead tracepoints (no stability guarantee)
- `BPF_PROG_TYPE_RAW_TRACEPOINT_WRITABLE`: Modify tracepoint arguments

**Networking**:
- `BPF_PROG_TYPE_XDP`: eXpress Data Path – earliest possible packet processing
- `BPF_PROG_TYPE_SCHED_CLS` / `BPF_PROG_TYPE_SCHED_ACT`: TC (traffic control) hooks
- `BPF_PROG_TYPE_SOCKET_FILTER`: Socket-level packet filtering
- `BPF_PROG_TYPE_SOCK_OPS`: TCP connection operations
- `BPF_PROG_TYPE_SK_SKB`: Socket buffer redirection (sockmap)
- `BPF_PROG_TYPE_CGROUP_SKB`: Cgroup-level network filtering

**Security**:
- `BPF_PROG_TYPE_LSM`: Linux Security Module hooks (5.7+)
- `BPF_PROG_TYPE_CGROUP_DEVICE`: Device access control
- `BPF_PROG_TYPE_CGROUP_SYSCTL`: Sysctl access control

**Others**:
- `BPF_PROG_TYPE_CGROUP_SOCK`: Socket creation control
- `BPF_PROG_TYPE_LIRC_MODE2`: IR remote control
- `BPF_PROG_TYPE_STRUCT_OPS`: Implement kernel structures (TCP congestion control)

### 1.3 BPF Maps

Maps are key-value data structures shared between kernel and userspace, or between BPF programs.

**Map Types**:

1. **Hash Maps**:
   - `BPF_MAP_TYPE_HASH`: Generic hash table
   - `BPF_MAP_TYPE_LRU_HASH`: LRU eviction for bounded memory
   - `BPF_MAP_TYPE_PERCPU_HASH`: Per-CPU hash (no locking overhead)

2. **Arrays**:
   - `BPF_MAP_TYPE_ARRAY`: Fixed-size array, index as key
   - `BPF_MAP_TYPE_PERCPU_ARRAY`: Per-CPU array
   - `BPF_MAP_TYPE_PROG_ARRAY`: Store BPF program file descriptors (tail calls)
   - `BPF_MAP_TYPE_PERF_EVENT_ARRAY`: Push events to userspace via perf buffer

3. **Specialized**:
   - `BPF_MAP_TYPE_STACK_TRACE`: Store kernel/user stack traces
   - `BPF_MAP_TYPE_CGROUP_ARRAY`: Store cgroup file descriptors
   - `BPF_MAP_TYPE_SOCKHASH` / `BPF_MAP_TYPE_SOCKMAP`: Socket redirection
   - `BPF_MAP_TYPE_RINGBUF`: Low-overhead ring buffer (5.8+, preferred over perf buffer)
   - `BPF_MAP_TYPE_QUEUE` / `BPF_MAP_TYPE_STACK`: FIFO/LIFO structures
   - `BPF_MAP_TYPE_DEVMAP`: XDP device redirect

**Map Flags**:
- `BPF_F_NO_PREALLOC`: Allocate on-demand (hash maps)
- `BPF_F_RDONLY_PROG`: Read-only from BPF programs
- `BPF_F_WRONLY_PROG`: Write-only from BPF programs
- `BPF_F_MMAPABLE`: Memory-map to userspace for zero-copy access

### 1.4 BPF Verifier

The verifier performs static analysis to ensure program safety before execution:

**Checks**:
1. **Control Flow**: All paths must reach `BPF_EXIT`, no unreachable code
2. **Bounded Loops**: Since 5.3, bounded loops allowed (< 1M instructions, provable bounds)
3. **Memory Access**: All memory accesses validated (bounds, alignment, type)
4. **Register State**: Track register types (scalar, pointer, context, etc.)
5. **Helper Function Arguments**: Type and nullability validation
6. **Program Size**: Max 1M verified instructions (after inlining, unrolling)
7. **Stack Usage**: Max 512 bytes per function
8. **Complexity**: Max ~1M verifier steps (configurable via sysctl)

**Verifier Pruning**:
- State pruning: equivalent register states -> skip verification
- Branch pruning: impossible branches eliminated
- Allows complex programs while maintaining verification time

**Common Verifier Errors**:
- "invalid access to packet": bounds check failure
- "unreachable insn": dead code after exit
- "back-edge from insn X to Y": unbounded loop detected
- "R1 pointer arithmetic prohibited": unsafe pointer manipulation
- "max states per insn X exceeded": complexity limit hit

---

## 2. BTF (BPF Type Format)

### 2.1 Purpose & Design

**Problem**: Kernel data structures change between versions – BPF programs compiled for one kernel version would break on another.

**BTF Solution**:
- Compact type information embedded in kernel (`/sys/kernel/btf/vmlinux`) and BPF objects
- Describes kernel structs, unions, enums, function signatures
- Enables CO-RE: relocation of field offsets at load time
- Generated from DWARF debug info via `pahole`

**BTF Encoding**:
- Binary format, ~1-2% of kernel image size
- Type graph: integers, pointers, structs, unions, enums, functions, etc.
- Stored in `.BTF` and `.BTF.ext` ELF sections

### 2.2 BTF Information

**Kernel BTF** (`/sys/kernel/btf/vmlinux`):
- Complete type information for running kernel
- All exported types, internal kernel structs
- Enabled via `CONFIG_DEBUG_INFO_BTF=y` (kernel 5.2+)

**Module BTF** (`/sys/kernel/btf/<module>`):
- Per-module type information
- Reduces duplication, references vmlinux BTF

**BPF Program BTF**:
- Embedded in BPF ELF object (`.BTF` section)
- Type info for program variables, maps, functions
- CO-RE relocations in `.BTF.ext` section

**BTF Dump**:
```
bpftool btf dump file /sys/kernel/btf/vmlinux format c > vmlinux.h
```
Generates header with all kernel types (used by BPF programs).

### 2.3 BTF Use Cases

1. **CO-RE Relocations**: Field offset adjustments
2. **Map Pretty-Printing**: `bpftool map dump` shows structured data
3. **BPF-to-BPF Calls**: Function signatures validated
4. **Kernel Function Tracing**: fentry/fexit require BTF
5. **Type-Based Verification**: Safer pointer arithmetic

---

## 3. CO-RE (Compile Once – Run Everywhere)

### 3.1 The Portability Problem

**Before CO-RE**:
- BPF programs hardcoded struct offsets: `__builtin_preserve_access_index()`
- Different kernel versions = different offsets
- Required recompilation per kernel version or BCC runtime compilation

**BCC Approach** (pre-CO-RE):
- Ship BPF source code
- Compile on target system using kernel headers
- Slow startup, requires toolchain on production systems
- Security risk: compilation on production hosts

### 3.2 CO-RE Mechanism

**Core Components**:

1. **BTF**: Kernel and BPF object type information
2. **Clang BTF Relocations**: Compiler generates relocation records
3. **libbpf Relocation Engine**: Resolves relocations at load time

**CO-RE Relocation Types**:

- **Field Offset**: `struct task_struct___old` vs `struct task_struct___new`
- **Field Existence**: Check if field exists in target kernel
- **Field Size**: Get size of field
- **Field Signedness**: Signed vs unsigned
- **Type Existence**: Check if type exists
- **Enum Value**: Get enum constant value

**BPF Helpers for CO-RE**:

```c
// Preserve access index for CO-RE relocations
#define BPF_CORE_READ(dst, src, a, ...) 
  bpf_core_read(dst, sizeof(*(dst)), &(src)->a)

// Check field existence
#define bpf_core_field_exists(field) 
  __builtin_preserve_field_info(field, BPF_FIELD_EXISTS)

// Get field size
#define bpf_core_field_size(field)
  __builtin_preserve_field_info(field, BPF_FIELD_BYTE_SIZE)
```

**Relocation Example**:

```c
// Source BPF program
struct task_struct *task = (void *)bpf_get_current_task();
pid_t pid = BPF_CORE_READ(task, pid);

// Compiler emits: "read 4 bytes at offset X of task_struct->pid"
// libbpf adjusts X based on target kernel's BTF at load time
```

### 3.3 CO-RE Macros & Patterns

**Core Reading Macros**:
- `BPF_CORE_READ(src, a, b, c)`: Chain field accesses
- `BPF_CORE_READ_INTO(&dst, src, field)`: Read into variable
- `BPF_CORE_READ_STR_INTO(dst, src, field)`: Read string safely

**Struct Flavors** (handle kernel version differences):
```c
struct task_struct___older_v {
    pid_t pid;
    // Old layout
} __attribute__((preserve_access_index));

struct task_struct___newer_v {
    int pid;
    // New layout
} __attribute__((preserve_access_index));

// libbpf picks correct flavor at load time
```

**Conditional Compilation**:
```c
if (bpf_core_field_exists(task->some_new_field)) {
    // Use new field
} else {
    // Fallback for older kernels
}
```

### 3.4 Benefits & Limitations

**Benefits**:
- Compile once, deploy everywhere (kernel 5.2+)
- No runtime compilation overhead
- Smaller binaries (no embedded kernel headers)
- Faster startup times
- Safer for production (no toolchain needed)

**Limitations**:
- Requires BTF in kernel (`CONFIG_DEBUG_INFO_BTF=y`)
- Cannot add new fields (only read existing)
- Complex relocations may fail on very different kernels
- Kernel < 5.2 requires manual offset handling or BCC

---

## 4. libbpf

### 4.1 Architecture & Responsibilities

libbpf is the canonical userspace library for BPF program lifecycle management.

**Core Functions**:

1. **ELF Object Parsing**: Load BPF programs/maps from ELF `.o` files
2. **BTF Loading**: Parse BTF from kernel and BPF objects
3. **CO-RE Relocation**: Resolve field offsets using BTF
4. **Program Loading**: `bpf()` syscall wrapper, verification
5. **Map Management**: Create, pin, share maps
6. **Attachment**: Attach programs to hooks (kprobe, tracepoint, XDP, etc.)
7. **Link Management**: Atomic attach/detach with pinning support
8. **Ring Buffer**: Efficient event streaming to userspace

**Library Structure**:
```
libbpf/
├── bpf.h            # Low-level bpf() syscall wrappers
├── libbpf.h         # High-level API (objects, programs, maps)
├── btf.h            # BTF parsing, dumping
├── bpf_helpers.h    # BPF program helpers (kernel-side)
├── bpf_core_read.h  # CO-RE reading macros
├── bpf_tracing.h    # Tracing-specific macros
└── xsk.h            # AF_XDP socket API
```

### 4.2 ELF Section Naming Conventions

libbpf infers program type and attachment from ELF section names:

**Tracing**:
- `kprobe/function_name`: Kernel function entry probe
- `kretprobe/function_name`: Kernel function exit probe
- `tracepoint/category/name`: Tracepoint
- `raw_tracepoint/name`: Raw tracepoint
- `tp_btf/name`: BTF-based tracepoint (5.5+)
- `fentry/function_name`: Fast entry tracing (5.5+, requires BTF)
- `fexit/function_name`: Fast exit tracing (5.5+, requires BTF)

**Networking**:
- `xdp`: XDP program
- `tc`: TC classifier/action
- `classifier/name`: TC classifier
- `action/name`: TC action
- `socket`: Socket filter
- `sk_skb/stream_parser` / `sk_skb/stream_verdict`: Socket buffer redirect

**Security**:
- `lsm/hook_name`: LSM hook (5.7+)
- `lsm.s/hook_name`: Sleepable LSM hook

**Cgroup**:
- `cgroup/skb`, `cgroup/sock`, `cgroup/dev`, etc.

**Maps Section**: `maps` or `.maps`

### 4.3 Object Lifecycle

**Typical Flow**:

1. **Open**: Parse ELF, load BTF, prepare programs/maps
2. **Configure**: Set program options, map sizes, etc.
3. **Load**: Verify programs, create maps, perform CO-RE relocations
4. **Attach**: Attach programs to hooks, get link FDs
5. **Runtime**: Interact with maps, poll ring buffers
6. **Detach**: Destroy links
7. **Close**: Clean up all resources

**Skeleton Generation** (recommended approach):
```
bpftool gen skeleton myprogram.bpf.o > myprogram.skel.h
```

Generates type-safe C API:
- `myprogram_bpf__open()`: Open object
- `myprogram_bpf__load()`: Load and verify
- `myprogram_bpf__attach()`: Attach all programs
- `myprogram_bpf__destroy()`: Clean up
- Accessors: `skel->maps.mymap`, `skel->progs.myprog`, `skel->bss->global_var`

**Manual API** (lower-level):
```c
struct bpf_object *obj = bpf_object__open_file("program.o", NULL);
bpf_object__load(obj);
struct bpf_program *prog = bpf_object__find_program_by_name(obj, "myprog");
struct bpf_link *link = bpf_program__attach(prog);
// ... use maps, poll events ...
bpf_link__destroy(link);
bpf_object__close(obj);
```

### 4.4 Map Operations

**Creation & Access**:
```c
// From skeleton
int fd = bpf_map__fd(skel->maps.mymap);

// Lookup
int key = 123;
struct value_t val;
bpf_map_lookup_elem(fd, &key, &val);

// Update
bpf_map_update_elem(fd, &key, &val, BPF_ANY);

// Delete
bpf_map_delete_elem(fd, &key);
```

**Iteration**:
```c
int key, next_key;
key = -1;
while (bpf_map_get_next_key(fd, &key, &next_key) == 0) {
    key = next_key;
    // Process key
}
```

**Batch Operations** (5.6+):
```c
bpf_map_lookup_batch(fd, &in_batch, &out_batch, keys, values, &count, NULL);
bpf_map_update_batch(fd, keys, values, &count, NULL);
bpf_map_delete_batch(fd, keys, &count, NULL);
```

**Map Pinning** (share maps between processes):
```c
bpf_map__set_pin_path(skel->maps.mymap, "/sys/fs/bpf/mymap");
bpf_object__load(obj); // Pins map
// Other process: open pinned map
int fd = bpf_obj_get("/sys/fs/bpf/mymap");
```

### 4.5 Ring Buffer

Preferred over perf buffer for event streaming (lower overhead, better ordering guarantees).

**Kernel Side**:
```c
struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);
} events SEC(".maps");

struct event {
    __u32 pid;
    char comm[16];
};

SEC("tp/syscalls/sys_enter_execve")
int handle_exec(struct trace_event_raw_sys_enter *ctx) {
    struct event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e) return 0;
    
    e->pid = bpf_get_current_pid_tgid() >> 32;
    bpf_get_current_comm(e->comm, sizeof(e->comm));
    
    bpf_ringbuf_submit(e, 0);
    return 0;
}
```

**Userspace**:
```c
int handle_event(void *ctx, void *data, size_t len) {
    struct event *e = data;
    printf("PID %d: %s\n", e->pid, e->comm);
    return 0;
}

struct ring_buffer *rb = ring_buffer__new(bpf_map__fd(skel->maps.events),
                                          handle_event, NULL, NULL);
// Poll for events
while (running) {
    ring_buffer__poll(rb, 100 /* timeout ms */);
}
ring_buffer__free(rb);
```

### 4.6 Global Variables & BSS/Data/Rodata

**Kernel Side**:
```c
const volatile bool enable_trace = false; // .rodata (read-only, configurable)
static __u64 counter = 0;                  // .bss (zero-initialized)
static __u32 pid_filter = 0;               // .data (initialized)
```

**Userspace** (skeleton access):
```c
skel->rodata->enable_trace = true; // Set before load
bpf_object__load(obj);
// Read/write after load
__u64 cnt = skel->bss->counter;
skel->data->pid_filter = 1234;
```

**Benefits**:
- Zero-copy access via mmap (if map is mmapable)
- Type-safe in skeleton
- Avoid map lookups for single values

---

## 5. bpftrace

### 5.1 Language Overview

bpftrace is a high-level tracing language inspired by DTrace and awk.

**Structure**:
```
probe_type:probe_location [/filter/] { actions }
```

**Example**:
```
kprobe:do_sys_open /comm == "bash"/ {
    printf("bash opened: %s\n", str(arg1));
}
```

**Probe Types**:
- `kprobe`, `kretprobe`: Kernel function tracing
- `tracepoint`: Static tracepoints
- `usdt`: Userspace static tracepoints
- `uprobe`, `uretprobe`: Userspace function tracing
- `profile`: Timer-based sampling
- `interval`: Periodic execution
- `BEGIN`, `END`: Script start/end
- `software`, `hardware`: Performance counters

### 5.2 Built-in Variables

**Context**:
- `pid`: Process ID
- `tid`: Thread ID
- `uid`, `gid`: User/group ID
- `nsecs`: Nanosecond timestamp
- `cpu`: Current CPU
- `comm`: Process name (16 bytes)
- `kstack`, `ustack`: Kernel/user stack traces
- `func`: Current function name (kprobe)
- `probe`: Full probe name
- `curtask`: Current task_struct pointer
- `cgroup`: Cgroup ID
- `args`: Tracepoint arguments structure

**Function Arguments**:
- `arg0`, `arg1`, ..., `argN`: Function arguments (kprobe, uprobe)
- `retval`: Return value (kretprobe, uretprobe)
- `args->field`: Tracepoint argument access

### 5.3 Actions & Functions

**Output**:
- `printf(fmt, ...)`: Formatted print
- `print(@map)`: Print map contents
- `clear(@map)`: Clear map
- `time(fmt)`: Print timestamp

**Map Operations**:
- `@map[key] = value`: Store value
- `@map[key]++`: Increment counter
- `count()`: Count events
- `sum(x)`: Sum values
- `avg(x)`: Average values
- `min(x)`, `max(x)`: Min/max values
- `hist(x)`: Power-of-2 histogram
- `lhist(x, min, max, step)`: Linear histogram
- `delete(@map[key])`: Delete entry

**String/Memory**:
- `str(ptr)`: Read null-terminated string
- `buf(ptr, len)`: Read buffer as hex
- `ksym(addr)`: Kernel symbol from address
- `usym(addr)`: Userspace symbol from address
- `kaddr(symbol)`: Address from kernel symbol
- `uaddr(symbol)`: Address from userspace symbol
- `ntop(addr)`: IP address to string
- `reg(name)`: Read CPU register

**Stack Traces**:
- `kstack`: Kernel stack trace
- `ustack`: Userspace stack trace
- `kstack(mode)`, `ustack(mode)`: mode = `bpftrace`, `perf`, etc.

**Control Flow**:
- `if (cond) { ... } else { ... }`
- `unroll (N) { ... }`: Bounded loop unrolling
- `return`: Early exit from action
- `exit()`: Terminate script

**Casting & Pointers**:
- `*(type *)addr`: Dereference with cast
- `((struct type *)ptr)->field`: Struct field access

### 5.4 Maps & Aggregations

**Map Types**:
- `@name`: Global map (persist between probes)
- `@name[key]`: Associative array
- `@name[key1, key2]`: Multi-key map

**Statistical Aggregations**:
```bpftrace
kretprobe:vfs_read {
    @bytes = hist(retval);          // Histogram of return values
    @read_size[comm] = lhist(retval, 0, 10000, 100);  // Linear histogram
    @total += retval;                // Sum
    @count++;                        // Count
    @avg = avg(retval);              // Average
}
```

**Printing Maps**:
```bpftrace
END {
    print(@bytes);       // Print histogram
    print(@read_size);   // Print all entries
    print(@total, @count, @avg);  // Print multiple values
}
```

### 5.5 One-Liners & Common Patterns

**Trace syscall frequency per process**:
```bpftrace
tracepoint:raw_syscalls:sys_enter { @[comm] = count(); }
```

**Distribution of read() sizes**:
```bpftrace
kretprobe:vfs_read { @bytes = hist(retval); }
```

**Top processes by syscall latency**:
```bpftrace
tracepoint:raw_syscalls:sys_enter { @start[tid] = nsecs; }
tracepoint:raw_syscalls:sys_exit /@start[tid]/ {
    @latency_us[comm] = hist((nsecs - @start[tid]) / 1000);
    delete(@start[tid]);
}
```

**Trace file opens by process**:
```bpftrace
kprobe:do_sys_open { printf("%s: %s\n", comm, str(arg1)); }
```

**Memory allocations > 1MB**:
```bpftrace
kprobe:__kmalloc /arg0 > 1048576/ {
    printf("Large alloc: %d bytes by %s\n", arg0, comm);
    print(kstack);
}
```

**Network packet tracing**:
```bpftrace
tracepoint:net:netif_receive_skb {
    printf("RX: %s len=%d\n", str(args->name), args->len);
}
```

### 5.6 Advanced Features

**Tuples**:
```bpftrace
BEGIN { $t = (1, 2, "hello"); printf("%d %s\n", $t.1, $t.2); }
```

**Positional Parameters** (`$1`, `$2`, ...):
```bpftrace
kprobe:$1 { @[func] = count(); }
# Run: bpftrace script.bt vfs_read
```

**BTF & CO-RE**:
```bpftrace
// bpftrace uses BTF automatically if available
kprobe:tcp_connect {
    $sk = (struct sock *)arg0;
    printf("Port: %d\n", $sk->__sk_common.skc_dport);
}
```

**USDT (User Statically-Defined Tracing)**:
```bpftrace
usdt:/usr/lib/libpthread.so.0:pthread_create {
    printf("Thread created by %s\n", comm);
}
```

---

## 6. Security Model & Threat Considerations

### 6.1 BPF Security Principles

**Unprivileged BPF** (disabled by default, `kernel.unprivileged_bpf_disabled=1`):
- Restricted program types: socket filters only
- No direct memory access, limited helpers
- Used for seccomp filters, socket filtering

**Privileged BPF** (CAP_BPF + CAP_PERFMON/CAP_NET_ADMIN):
- Full program types, all helpers
- Can read kernel memory (via helpers), trace any function
- Verifier ensures no writes to arbitrary kernel memory

**Isolation Boundaries**:
1. **Verifier**: Ensures program cannot crash kernel, infinite loop, or access invalid memory
2. **Helper Functions**: Only approved kernel functions callable
3. **JIT Hardening**: Constant blinding, retpoline use
4. **Map Permissions**: Maps can be read-only, write-only, or restricted to specific programs

### 6.2 Attack Surface & Mitigations

**Threats**:

1. **Verifier Bypass**: Exploit verifier bugs to run unsafe code
   - **Mitigation**: Extensive fuzzing, formal verification research, upstream review process

2. **JIT Bugs**: Compiler bugs leading to unsafe native code
   - **Mitigation**: Disable JIT (`net.core.bpf_jit_enable=0`), JIT hardening (`net.core.bpf_jit_harden=2`)

3. **Side Channels**: Spectre/Meltdown-style attacks
   - **Mitigation**: Speculative execution barriers in JIT, array_index_nospec() use

4. **Information Disclosure**: Read sensitive kernel memory
   - **Mitigation**: Helpers restrict accessible memory, pointer leaking prohibited

5. **Privilege Escalation**: Unprivileged BPF exploits
   - **Mitigation**: Unprivileged BPF disabled by default (since ~5.16)

**LSM BPF Security**:
- BPF LSM hooks enforce MAC (Mandatory Access Control)
- Loaded programs can deny operations (file access, network, etc.)
- Used in production: Google, Meta use BPF LSM for container security
- Defense-in-depth: Complements existing LSMs (SELinux, AppArmor)

**Audit & Logging**:
- BPF program loads logged (auditd)
- Use `bpf_trace_printk()` sparingly in production (limited buffer)
- Ring buffers for production event streaming (no data loss)

### 6.3 Capability Requirements**CAP_BPF** (5.8+): Load BPF programs, create maps
**CAP_PERFMON** (5.8+): Attach to tracing, read sensitive data
**CAP_NET_ADMIN**: Attach to networking hooks (XDP, TC)
**CAP_SYS_ADMIN**: (legacy, older kernels require this for all BPF)

**Fine-Grained Permissions**:
```
# Load tracing program: CAP_BPF + CAP_PERFMON
# Load XDP program: CAP_BPF + CAP_NET_ADMIN
# Load LSM program: CAP_BPF + CAP_MAC_ADMIN (future)
```

---

## 7. Performance Characteristics

### 7.1 Overhead Analysis

**BPF Program Overhead**:
- JIT compilation: ~10-100 µs per program (one-time)
- Tracing overhead: ~100-500 ns per event (kprobe, tracepoint)
- fentry/fexit: ~50-100 ns (lower than kprobe)
- XDP: ~10-50 ns per packet (inline processing)
- Helper calls: ~10-50 ns each

**Compared to Alternatives**:
- Kernel module: 0 ns (native), but unsafe, hard to update
- SystemTap: ~500-1000 ns per event (interpreter-based)
- DTrace (Linux): variable, often higher than BPF
- ftrace: ~200-400 ns per event (static tracing)

**Optimization Strategies**:

1. **Use fentry/fexit over kprobe**: Lower overhead, BTF-based
2. **Batch map operations**: Use batch APIs for bulk operations
3. **Per-CPU maps**: Avoid atomic operations, cache locality
4. **Ring buffer over perf buffer**: Better batching, ordering
5. **Avoid locks**: Use per-CPU data structures
6. **Minimize helper calls**: Each helper is ~10-50 ns
7. **Use bounded loops**: Verifier can inline, unroll
8. **Tail calls**: Jump to another program (no stack limit)

### 7.2 Scalability

**High-Cardinality Scenarios**:
- Hash map size: Millions of entries (limited by memory)
- LRU maps: Automatic eviction for bounded memory
- Batch operations: Process thousands of entries/second

**Multi-Core Performance**:
- Per-CPU maps: Zero contention
- Ring buffer: Per-CPU sub-buffers
- XDP: RSS (Receive Side Scaling) for parallel packet processing

**Production Use Cases**:
- **Cilium**: 10+ million packets/sec per node with XDP
- **Katran (Facebook)**: 60+ million packets/sec L4 load balancer
- **Falco**: ~100k events/sec security monitoring
- **Pixie**: Continuous profiling with <1% overhead

---

## 8. Ecosystem & Tooling

### 8.1 Development Tools

**bpftool**: Swiss-army knife for BPF
- `bpftool prog list`: List loaded programs
- `bpftool map dump id <id>`: Dump map contents
- `bpftool prog dump xlated id <id>`: Show JIT assembly
- `bpftool prog profile`: Profile program execution
- `bpftool btf dump`: Dump BTF information
- `bpftool gen skeleton`: Generate skeleton code

**Clang/LLVM**: BPF backend (LLVM 10+)
- Compile with `-target bpf -O2 -g -c -o program.o program.c`
- Emit BTF: `-g` (debug info converted to BTF via pahole)

**pahole**: DWARF to BTF converter
- `pahole -J vmlinux` (embed BTF in vmlinux)

**Debugging**:
- `bpf_printk()`: Print to `/sys/kernel/debug/tracing/trace_pipe`
- `bpftool prog tracelog`: Tail trace log
- Verifier log: `bpftool prog load -d` (show verifier steps)

### 8.2 Libraries & Frameworks

**libbpf-based**:
- **libbpf-bootstrap**: Minimal templates for BPF programs
- **libbpf-rs** (Rust): Rust bindings for libbpf
- **libbpfgo** (Go): Go bindings for libbpf

**High-Level Frameworks**:
- **Cilium**: Kubernetes networking, security, observability (uses BPF extensively)
- **Katran**: L4 load balancer
- **Falco**: Runtime security monitoring
- **Pixie**: Kubernetes observability
- **Parca**: Continuous profiling
- **Tetragon**: eBPF-based security observability

**Language Bindings**:
- **Go**: cilium/ebpf (pure Go, no libbpf dependency)
- **Rust**: aya (pure Rust, no libbpf), libbpf-rs
- **Python**: BCC (runtime compilation, older), bpfman (libbpf-based)

### 8.3 Learning Resources

**Official Documentation**:
- Kernel BPF docs: `Documentation/bpf/` in Linux source
- libbpf API docs: https://libbpf.readthedocs.io
- BPF and XDP reference guide: https://docs.cilium.io/en/stable/bpf/

**Books**:
- "BPF Performance Tools" (Brendan Gregg)
- "Learning eBPF" (Liz Rice)
- "Linux Observability with BPF" (David Calavera, Lorenzo Fontana)

**Repositories**:
- libbpf-bootstrap: https://github.com/libbpf/libbpf-bootstrap
- BCC tools: https://github.com/iovisor/bcc
- bpftrace: https://github.com/iovisor/bpftrace
- Cilium: https://github.com/cilium/cilium

---

## 9. Production Deployment Patterns

### 9.1 Lifecycle Management

**Deployment Options**:

1. **Static Binary**: Embed BPF `.o` in executable, load at runtime
2. **Dynamic Loading**: Ship `.o` files separately, load on-demand
3. **Pinned Maps**: Share state across program restarts
4. **BPF Links**: Atomic attach/detach with pinning

**Rolling Updates**:
```
1. Load new BPF program version
2. Create new links for new program
3. Detach old links (atomic swap)
4. Unload old program
5. Old maps can be shared or migrated
```

**Graceful Shutdown**:
```c
// Signal handler
sig_atomic_t exiting = 0;
void sig_handler(int sig) { exiting = 1; }

// Main loop
signal(SIGINT, sig_handler);
signal(SIGTERM, sig_handler);
while (!exiting && ring_buffer__poll(rb, 100) >= 0) {}

// Cleanup
bpf_link__destroy(link);
ring_buffer__free(rb);
bpf_object__close(obj);
```

### 9.2 Monitoring & Observability

**Program Statistics**:
```
bpftool prog show id <id>
  -> run_time_ns, run_cnt
```

**Map Usage**:
```
bpftool map show id <id>
  -> max_entries, memlock (bytes)
```

**Verifier Complexity**:
```
bpftool prog load -d program.o /sys/fs/bpf/myprog
  -> Log shows verification steps, complexity
```

**Metrics to Track**:
- Program run count, duration (via bpftool or custom metrics)
- Map size, utilization
- Ring buffer drops (events lost)
- Verifier rejections (at load time)

### 9.3 Failure Modes & Recovery

**Common Failures**:

1. **Verifier Rejection**: Program too complex, unsafe access
   - **Recovery**: Simplify program, split into smaller programs (tail calls)

2. **Map Full (non-LRU)**: Hash map reaches max_entries
   - **Recovery**: Use LRU maps, increase size, periodic cleanup

3. **Ring Buffer Overrun**: Events produced faster than consumed
   - **Recovery**: Increase buffer size, optimize consumer, rate-limit events

4. **BTF Mismatch**: Kernel BTF missing or incompatible
   - **Recovery**: Fallback to non-CO-RE (manual offsets), provide multiple flavors

5. **Permission Denied**: Insufficient capabilities
   - **Recovery**: Check capabilities (CAP_BPF, CAP_PERFMON), adjust permissions

**Resilience Patterns**:
- **Graceful Degradation**: If BPF load fails, continue with limited functionality
- **Fallback Paths**: Provide non-BPF alternatives (e.g., ptrace, netlink polling)
- **Rate Limiting**: Avoid overwhelming userspace consumer
- **Bounded Maps**: Use LRU to prevent memory exhaustion

---

## 10. Advanced Topics

### 10.1 BPF-to-BPF Calls & Subprograms

**Before BPF-to-BPF Calls**:
- Inline all functions (code bloat)
- 512-byte stack limit per program
- Complex programs hit instruction limit

**With BPF-to-BPF Calls** (4.16+):
- Functions can call other functions
- Each function has own 512-byte stack (stacked)
- Total stack depth: 8 levels (512 * 8 = 4KB max)
- BTF required for function signatures

**Usage**:
```c
static __always_inline int helper_func(int x) {
    return x * 2;
}

SEC("kprobe/my_kprobe")
int my_prog(struct pt_regs *ctx) {
    int val = helper_func(123);
    return 0;
}
```

### 10.2 Tail Calls

**Purpose**: Jump to another BPF program (no return)
- Avoid stack limit (tail call resets stack)
- Chain complex logic across multiple programs
- Max 33 tail calls per execution

**Program Array Map**:
```c
struct {
    __uint(type, BPF_MAP_TYPE_PROG_ARRAY);
    __uint(max_entries, 10);
    __uint(key_size, sizeof(__u32));
    __uint(value_size, sizeof(__u32));
} prog_array SEC(".maps");

SEC("kprobe/start")
int start_prog(struct pt_regs *ctx) {
    bpf_tail_call(ctx, &prog_array, 1); // Jump to program at index 1
    return 0; // Only if tail call fails
}
```

**Userspace**:
```c
int prog_fd = bpf_program__fd(skel->progs.next_prog);
int key = 1;
bpf_map_update_elem(bpf_map__fd(skel->maps.prog_array), &key, &prog_fd, BPF_ANY);
```

### 10.3 BPF Iterators (5.8+)

**Purpose**: Iterate kernel data structures safely from BPF

**Supported Targets**:
- `bpf_iter/task`: All tasks
- `bpf_iter/task_file`: All open files in tasks
- `bpf_iter/tcp`, `udp`, `unix`: Network sockets
- `bpf_iter/bpf_map_elem`: Map elements
- Custom iterators via `bpf_iter_create()`

**Example** (iterate all tasks):
```c
SEC("iter/task")
int dump_tasks(struct bpf_iter__task *ctx) {
    struct task_struct *task = ctx->task;
    if (!task) return 0;
    
    bpf_seq_printf(ctx->meta->seq, "PID: %d COMM: %s\n",
                   task->pid, task->comm);
    return 0;
}
```

**Userspace**:
```c
// Attach iterator
struct bpf_link *link = bpf_program__attach_iter(prog, NULL);
int iter_fd = bpf_iter_create(bpf_link__fd(link));

// Read output
char buf[4096];
while (read(iter_fd, buf, sizeof(buf)) > 0) {
    printf("%s", buf);
}
```

### 10.4 Sleepable BPF (5.10+)

**Purpose**: Allow BPF programs to sleep (call sleeping kernel functions)

**Program Types**:
- `lsm.s/hook_name`: Sleepable LSM
- `iter.s/target`: Sleepable iterator
- `fentry.s/func`, `fexit.s/func`: Sleepable fentry/fexit

**Use Cases**:
- Blocking I/O (copy_from_user, copy_to_user)
- Memory allocation with GFP_KERNEL
- Mutex locking

**Restrictions**:
- Cannot use bpf_spin_lock
- Cannot use some helpers (e.g., bpf_get_smp_processor_id)

### 10.5 BPF Type Format (BTF) Extensions

**BTF for Kernel Modules**:
- Each module has its own BTF in `/sys/kernel/btf/<module>`
- Allows CO-RE to work with module types

**BTF Relocations for Enums**:
```c
enum { SOME_CONST = 10 };
int val = bpf_core_enum_value(enum my_enum, SOME_CONST);
// libbpf adjusts if enum value changed in target kernel
```

**BTF for User Types** (future):
- BTF for userspace programs (libraries, applications)
- Enable CO-RE for uprobe/uretprobe across userspace versions

---

## 11. Security Use Cases (LSM BPF, Runtime Enforcement)

### 11.1 LSM BPF Hooks

**Available Hooks** (100+ from LSM framework):
- File operations: `file_open`, `file_permission`, `file_ioctl`
- Process: `task_alloc`, `task_kill`, `bprm_check_security`
- Network: `socket_connect`, `socket_bind`, `socket_sendmsg`
- IPC: `msg_queue_msgrcv`, `shm_shmat`
- Capability: `capable`

**Return Values**:
- 0: Allow operation
- -EPERM, -EACCES: Deny operation

**Example** (restrict outbound connections):
```c
SEC("lsm/socket_connect")
int BPF_PROG(restrict_connect, struct socket *sock, struct sockaddr *addr, int addrlen) {
    if (addr->sa_family != AF_INET) return 0;
    
    struct sockaddr_in *addr_in = (struct sockaddr_in *)addr;
    __u32 dst_ip = addr_in->sin_addr.s_addr;
    
    // Block connections to 192.168.1.1
    if (dst_ip == 0x0101A8C0) { // Network byte order
        return -EPERM;
    }
    return 0;
}
```

### 11.2 Container Security

**Cgroup-Based Filtering**:
```c
__u64 cgroup_id = bpf_get_current_cgroup_id();
// Check if cgroup is allowed
if (bpf_map_lookup_elem(&allowed_cgroups, &cgroup_id))
    return 0; // Allow
return -EPERM; // Deny
```

**Use Cases**:
- Prevent container escape (restrict syscalls, files)
- Network segmentation (restrict outbound connections)
- Resource access control (deny device access)

**Production Examples**:
- **Google**: BPF LSM for container isolation
- **Meta**: BPF for workload security (replaced some AppArmor/SELinux)

---

## 12. Networking Use Cases (XDP, TC)

### 12.1 XDP (eXpress Data Path)

**Attachment Points**:
- **Native/Driver mode**: Earliest point (NIC driver), requires driver support
- **Offload mode**: NIC hardware (SmartNICs), highest performance
- **Generic mode**: Fallback, software-only (lower performance)

**Actions**:
- `XDP_PASS`: Pass packet to network stack
- `XDP_DROP`: Drop packet (DDoS mitigation)
- `XDP_TX`: Bounce packet back on same interface
- `XDP_REDIRECT`: Redirect to another interface or CPU
- `XDP_ABORTED`: Error, drop packet

**Example** (drop all ICMP):
```c
SEC("xdp")
int drop_icmp(struct xdp_md *ctx) {
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;
    
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end) return XDP_PASS;
    
    if (eth->h_proto == bpf_htons(ETH_P_IP)) {
        struct iphdr *ip = data + sizeof(*eth);
        if ((void *)(ip + 1) > data_end) return XDP_PASS;
        
        if (ip->protocol == IPPROTO_ICMP)
            return XDP_DROP;
    }
    return XDP_PASS;
}
```

**Performance**: 10-50 ns per packet, 10M+ pps per core

### 12.2 TC (Traffic Control)

**Attachment Points**:
- Ingress: After XDP, before network stack
- Egress: Before NIC transmission

**Actions**:
- `TC_ACT_OK`: Pass packet
- `TC_ACT_SHOT`: Drop packet
- `TC_ACT_REDIRECT`: Redirect to another interface
- `TC_ACT_STOLEN`: Consume packet (no further processing)

**Use Cases**:
- Bandwidth shaping, QoS
- Packet encapsulation (tunneling)
- Load balancing
- DDoS mitigation

---

## 13. Common Patterns & Best Practices

### 13.1 Development Workflow

1. **Write BPF program** (`.bpf.c`):
   - Use CO-RE macros for portability
   - Define maps, global variables
   - Add `SEC()` annotations

2. **Compile**:
   ```
   clang -target bpf -O2 -g -c program.bpf.c -o program.bpf.o
   ```

3. **Generate skeleton**:
   ```
   bpftool gen skeleton program.bpf.o > program.skel.h
   ```

4. **Write userspace** (`.c`):
   - Include skeleton header
   - Open, load, attach
   - Poll ring buffers or interact with maps

5. **Compile userspace**:
   ```
   gcc -o program program.c -lbpf -lelf -lz
   ```

6. **Test**:
   ```
   sudo ./program
   ```

### 13.2 Debugging Checklist

- [ ] Check verifier log: `bpftool prog load -d`
- [ ] Use `bpf_printk()` for debug output (trace_pipe)
- [ ] Verify BTF availability: `bpftool btf list`
- [ ] Check capabilities: `capsh --print` (CAP_BPF, CAP_PERFMON)
- [ ] Inspect loaded programs: `bpftool prog list`
- [ ] Dump map contents: `bpftool map dump id <id>`
- [ ] Profile program: `bpftool prog profile id <id> cycles`
- [ ] Test on older kernels: VMs with different kernel versions

### 13.3 Performance Tuning

- Use per-CPU maps for high-throughput scenarios
- Batch map operations when possible
- Prefer ring buffer over perf buffer
- Use LRU maps for bounded memory
- Minimize helper calls (each adds latency)
- Avoid locks (use per-CPU data)
- Profile with `perf record -e bpf:bpf_map_*`

### 13.4 Security Hardening

- Disable unprivileged BPF: `sysctl kernel.unprivileged_bpf_disabled=1`
- Enable JIT hardening: `sysctl net.core.bpf_jit_harden=2`
- Audit BPF loads: Monitor auditd for BPF syscalls
- Restrict map permissions: Use read-only/write-only flags
- Use LSM BPF for enforcement, not just monitoring
- Review BPF programs in CI/CD (static analysis)

---

## Architecture View: BPF Stack

```
┌────────────────────────────────────────────────────────────┐
│                      Application Layer                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  bpftrace   │  │   Cilium    │  │   Falco     │        │
│  │  (tracing)  │  │ (networking)│  │  (security) │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
├─────────┼─────────────────┼─────────────────┼──────────────┤
│         │            Library Layer         │               │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐       │
│  │   libbpf    │  │ cilium/ebpf │  │  libbpf-rs  │       │
│  │  (C/C++)    │  │    (Go)     │  │   (Rust)    │       │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘       │
├─────────┼─────────────────┼─────────────────┼──────────────┤
│         │       Kernel Interface (bpf syscall)             │
│  ┌──────▼────────────────────────────────────────────┐    │
│  │              BPF Subsystem (Kernel)                │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐        │    │
│  │  │ Verifier │  │  BTF     │  │   Maps   │        │    │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘        │    │
│  │  ┌────▼──────────────▼──────────────▼─────┐      │    │
│  │  │          JIT Compiler (x86/ARM)         │      │    │
│  │  └────┬────────────────────────────────────┘      │    │
│  │  ┌────▼────────────────────────────────────┐      │    │
│  │  │       BPF Program Execution             │      │    │
│  │  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐  │      │    │
│  │  │  │kprobe│ │  XDP │ │  TC  │ │ LSM  │  │      │    │
│  │  │  └──────┘ └──────┘ └──────┘ └──────┘  │      │    │
│  │  └─────────────────────────────────────────┘      │    │
│  └────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────┘
```

---

## Threat Model

**Assets**:
- Kernel memory integrity
- System stability (no crashes)
- Confidential data (kernel addresses, sensitive data)

**Threat Actors**:
- Malicious local user (unprivileged or privileged)
- Compromised application loading BPF programs
- Supply chain attack (malicious BPF in container image)

**Attack Vectors**:
1. **Verifier Bypass**: Exploit bugs to run unsafe code
2. **Side Channels**: Leak kernel addresses, data via timing
3. **Resource Exhaustion**: Load many programs, exhaust memory
4. **Information Disclosure**: Read kernel memory via helpers

**Mitigations**:
- Verifier: Static analysis ensures safety
- Unprivileged BPF disabled by default
- JIT hardening: Constant blinding, retpoline
- Capability checks: CAP_BPF, CAP_PERFMON
- Audit logging: All BPF loads logged
- Upstream review: All BPF changes reviewed by maintainers
- Fuzzing: syzkaller, others fuzz verifier continuously

**Residual Risks**:
- Zero-day verifier bugs (rare, but possible)
- Side channels (difficult to fully mitigate)
- Privileged user abuse (if CAP_BPF granted)

---

## Next 3 Steps

1. **Experiment with libbpf-bootstrap**: Clone repo, build and run examples (`minimal`, `kprobe`, `uprobe`). Modify examples to trace different functions, observe verifier logs with `-d`.

2. **Write custom bpftrace scripts**: Start with one-liners (syscall tracing, file opens), then progress to multi-probe scripts with maps and histograms. Profile your own applications.

3. **Build CO-RE-enabled BPF program**: Use vmlinux.h, CO-RE macros, test on multiple kernel versions (5.2, 5.10, 6.x). Understand relocation process by examining `.BTF.ext` section and libbpf debug output.

---

## References

**Kernel Documentation**:
- `Documentation/bpf/` (Linux source)
- `/proc/sys/kernel/bpf_*`, `/proc/sys/net/core/bpf_*` (sysctl)

**Specifications**:
- BPF ISA: `Documentation/bpf/instruction-set.rst`
- BTF Format: `Documentation/bpf/btf.rst`
- Map Types: `include/uapi/linux/bpf.h`

**Libraries**:
- libbpf: https://github.com/libbpf/libbpf
- cilium/ebpf: https://github.com/cilium/ebpf
- aya: https://github.com/aya-rs/aya
- bpftrace: https://github.com/iovisor/bpftrace

**Production Systems**:
- Cilium (Kubernetes networking): https://cilium.io
- Katran (L4 LB): https://github.com/facebookincubator/katran
- Falco (security): https://falco.org
- Pixie (observability): https://px.dev

**Papers & Talks**:
- "BPF: Tracing and more" (LPC 2014) – Alexei Starovoitov
- "eBPF and IO Visor" (2015) – Brendan Gregg
- "Production BPF" (LPC 2020+) – various speakers

**Books**:
- "BPF Performance Tools" (Brendan Gregg, 2019)
- "Learning eBPF" (Liz Rice, 2023)

This guide provides a comprehensive foundation for understanding and building with BPF CO-RE, libbpf, and bpftrace. The focus is on production-grade patterns, security considerations, and real-world deployment at scale.