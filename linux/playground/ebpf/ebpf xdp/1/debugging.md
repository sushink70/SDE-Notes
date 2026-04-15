# File: docs/DEBUGGING.md
# eBPF + Kernel Module: Complete Debugging Field Guide

## The Debugging Stack (from easiest to deepest)

```
Level 1: bpf_printk + trace_pipe     ← Start here
Level 2: bpftool prog/map inspect    ← Data correctness
Level 3: bpftrace one-liners         ← Runtime tracing
Level 4: perf + ftrace               ← Performance + control flow
Level 5: kernel oops/BUG() analysis  ← Crash debugging
Level 6: QEMU + GDB                  ← Step-debug the kernel itself
```

---

## Level 1: bpf_printk (printf for BPF)

In your BPF program:
```c
bpf_printk("XDP: proto=%u src=%x pkt_len=%u\n", proto, src_ip, pkt_len);
```

Read in userspace:
```bash
# Enable tracing
echo 1 > /sys/kernel/debug/tracing/tracing_on

# Read continuously
sudo cat /sys/kernel/debug/tracing/trace_pipe

# Or filter:
sudo cat /sys/kernel/debug/tracing/trace_pipe | grep "XDP:"
```

**PITFALL**: bpf_printk only takes 3 arguments max (older kernels).
On kernel ≥ 5.13 use BPF_PRINTK_MAX_ARGS (up to 12).

---

## Level 2: bpftool — The Swiss Army Knife

### Inspect loaded programs
```bash
# List all loaded BPF programs
sudo bpftool prog list
# Example output:
#   42: xdp  name xdp_pkt_counter  tag abc123  gpl
#        loaded_at 2024-01-01T10:00:00  uid 0
#        xlated 512B  jited 256B  memlock 4096B  map_ids 1,2

# Show bytecode (xlated = after verifier, jited = machine code)
sudo bpftool prog dump xlated id 42
sudo bpftool prog dump jited  id 42

# Full verifier log on a failing program
sudo bpftool prog load my_prog.bpf.o /sys/fs/bpf/test 2>&1 | head -100
# The verifier log tells you EXACTLY which instruction failed and why.
```

### Inspect maps
```bash
# List maps
sudo bpftool map list

# Dump all entries (JSON format)
sudo bpftool map dump id 7

# Dump as pretty table
sudo bpftool map dump name proto_stats_map

# Look up a specific key
sudo bpftool map lookup id 7 key 0x06 0x00 0x00 0x00

# Update a map entry from userspace (useful for testing policy changes)
sudo bpftool map update id 7 key 0x06 0x00 0x00 0x00 value 0 0 0 0 0 0 0 0
```

### Show XDP attachment
```bash
sudo bpftool net list
# Shows: XDP programs attached to each interface
# Example:
#   xdp:
#   eth0(2) driver id 42
```

### Show BTF (type info)
```bash
sudo bpftool btf dump id 7
sudo bpftool btf dump file /sys/kernel/btf/vmlinux | grep "struct sk_buff" | head -5
```

---

## Level 3: bpftrace One-Liners

bpftrace = DTrace-style dynamic tracing for Linux, uses eBPF internally.

### Trace every XDP decision
```bash
# Trace XDP actions on all programs
sudo bpftrace -e '
tracepoint:xdp:xdp_exception {
    printf("XDP_EXCEPTION on %s: action=%d\n",
           str(args->name), args->act);
}'

# Trace TCP new connections
sudo bpftrace -e '
kretprobe:inet_csk_accept {
    $sk = (struct sock *)retval;
    if ($sk != 0) {
        printf("New connection: %s:%d → %s:%d\n",
               ntop(AF_INET, $sk->__sk_common.skc_daddr),
               $sk->__sk_common.skc_dport,
               ntop(AF_INET, $sk->__sk_common.skc_rcv_saddr),
               $sk->__sk_common.skc_num);
    }
}'

# Histogram of packet sizes hitting XDP
sudo bpftrace -e '
tracepoint:net:napi_poll {
    @poll_count[str(args->dev_name)] = count();
}'

# Count netfilter hook calls by hook number
sudo bpftrace -e '
kprobe:nf_hook_slow {
    @hooks[arg2] = count();
}
interval:s:5 { print(@hooks); clear(@hooks); }'
```

---

## Level 4: perf + ftrace

### perf: Profile BPF program overhead
```bash
# Profile all events (including BPF JIT code):
sudo perf record -g -a -- sleep 10
sudo perf report --stdio | head -50

# Profile just the XDP program:
sudo perf stat -e bpf:*  -- sleep 5

# Hardware counters while XDP is running:
sudo perf stat -e \
    instructions,cache-misses,branch-misses,page-faults \
    -p $(pgrep loader) sleep 5
```

### ftrace: Trace kernel function calls
```bash
# Find traceable net subsystem functions
sudo grep "^net\|^xdp\|^nf_hook" /sys/kernel/debug/tracing/available_filter_functions | head -30

# Trace the XDP dispatch function
cd /sys/kernel/debug/tracing
echo 0 > tracing_on
echo function_graph > current_tracer
echo xdp_do_filter > set_graph_function
echo 1 > tracing_on
# ... do some network traffic ...
echo 0 > tracing_on
cat trace | head -100

# Trace netfilter hooks
echo nf_hook_slow > set_ftrace_filter
echo function > current_tracer
echo 1 > tracing_on
# ... traffic ...
cat trace
```

---

## Level 5: Kernel Oops/BUG() Analysis

When a kernel module crashes, you see an "Oops" in dmesg.

### Example Oops (from our module with a use-after-free):
```
BUG: kernel NULL pointer dereference, address: 0000000000000018
PGD 0 P4D 0
Oops: 0000 [#1] SMP PTI
CPU: 2 PID: 1234 Comm: loader Tainted: G     OE  5.15.0
RIP: 0010:netdev_event_handler+0x42/0x80 [netdev_module]
RSP: 0018:ffffab12c0987d80 EFLAGS: 00010286
Call Trace:
 notifier_call_chain+0x47/0x70
 raw_notifier_call_chain+0x14/0x20
 call_netdevice_notifiers_info+0x2a/0x60
 __dev_notify_flags+0x3e/0xb0
```

### How to decode it:
```bash
# 1. Find the offset (+0x42) in the function:
objdump -d netdev_module.ko | grep -A5 "netdev_event_handler"
# Look for the instruction at offset 0x42

# 2. Use addr2line for precise source location:
addr2line -e netdev_module.ko 0x42

# 3. Decode the full call trace with scripts:
# (In kernel source tree)
scripts/decode_stacktrace.sh vmlinux < oops.txt
```

### Common causes for module crashes:
| Symptom | Cause | Fix |
|---------|-------|-----|
| NULL deref in notifier | Wrong unregister order | Unregister in reverse order |
| Use-after-free on rmmod | Module unloaded while IRQ in handler | Use SRCU or rcu_read_lock |
| "scheduling while atomic" | sleep() in IRQ/softirq context | Use GFP_ATOMIC allocs |
| Hung task warning | spinlock held too long | Use mutex or review critical section |

---

## Level 6: QEMU + GDB Kernel Debugging

For the deepest debugging (stepping through kernel code):

### Setup (one-time):
```bash
# Build a custom kernel with debug info
git clone --depth 1 https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git
cd linux
make defconfig
scripts/config -e CONFIG_DEBUG_INFO
scripts/config -e CONFIG_GDB_SCRIPTS
scripts/config -e CONFIG_KGDB
make -j$(nproc)

# Install QEMU
apt install qemu-system-x86

# Create a minimal rootfs
# (use buildroot, debootstrap, or a cloud image)
```

### Launch kernel under QEMU with GDB stub:
```bash
qemu-system-x86_64 \
    -kernel arch/x86/boot/bzImage \
    -append "root=/dev/sda1 console=ttyS0 nokaslr kgdboc=ttyS1" \
    -drive file=rootfs.qcow2,format=qcow2 \
    -serial mon:stdio \
    -serial tcp::1234,server,nowait \
    -nographic \
    -m 2G \
    -smp 2
```

### Connect GDB:
```bash
gdb vmlinux
(gdb) target remote :1234
(gdb) hbreak netdev_event_handler    # hardware breakpoint
(gdb) c                              # continue
# Now trigger the notifier (e.g., ip link set eth0 up in QEMU)
(gdb) bt                             # backtrace at breakpoint
(gdb) p *dev                         # print net_device struct
(gdb) p dev->name                    # print interface name
(gdb) x/16xb dev->dev_addr           # hex dump MAC address
```

---

## Endianness Bug Detection Checklist

Before any network field comparison, ask:

```
Is this a multi-byte field from a network header?
  YES → Does it come from: ethhdr, iphdr, tcphdr, udphdr?
    YES → Must convert with bpf_ntohs() / bpf_ntohl()
    NO  → BPF map keys/values are host-order (no conversion)
```

Quick reference:
| Field | Type | Need conversion? |
|-------|------|-----------------|
| eth->h_proto | __be16 | YES: bpf_ntohs() |
| iph->saddr / daddr | __be32 | YES: bpf_ntohl() |
| tcph->source / dest | __be16 | YES: bpf_ntohs() |
| iph->protocol | __u8 | NO (single byte) |
| iph->ttl | __u8 | NO |
| BPF map key | __u32 | NO |

---

## Verifier Error Quick Reference

| Error Message | Cause | Fix |
|---------------|-------|-----|
| `invalid mem access 'pkt_ptr'` | Missing bounds check | Add `if ((void*)(ptr+1) > data_end)` |
| `R1 type=inv expected=ctx` | Wrong function argument type | Check function signature |
| `jump out of range` | Loop not bounded | Add `#pragma unroll` or bound loop |
| `back-edge detected` | Unbounded loop | Use bpf_loop() (kernel 5.17+) |
| `RX pointer arithmetic on map_value` | Invalid map pointer math | Use explicit index |
| `cannot call GPL-only function` | Non-GPL license | Add `GPL` license section |
| `Stack frame too large` | Stack >512 bytes | Move large data to BPF maps |
| `program too large` | >1M instructions | Split into multiple tail-call programs |