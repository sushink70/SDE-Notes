# Linux Kernel Net Subsystem — Elite Developer Reference

## 1. Mental model: how a Linux kernel developer thinks before writing code

Before touching an editor, a kernel developer asks six questions:

**Q1. What is the exact kernel subsystem boundary?**
Network code lives in three layers. `net/core/` owns the device-agnostic core
(`sk_buff`, socket layer). `net/ipv4/` owns IPv4 routing, TCP, UDP, ICMP.
`net/netfilter/` owns packet filtering hooks. Knowing where your code belongs
determines which APIs you can legally call and which maintainer reviews you.

**Q2. What locking rules apply?**
Network hooks run in softirq context (BH = bottom half). You cannot sleep,
cannot hold a mutex, cannot allocate with GFP_KERNEL. Every variable accessed
from a hook must either be atomic (`atomic64_t`, `READ_ONCE`/`WRITE_ONCE`) or
protected by a spinlock held with `spin_lock_bh()`.

**Q3. What does sk_buff ownership mean here?**
`sk_buff` is reference-counted. In a netfilter hook, you do NOT own the skb.
Do not call `kfree_skb()`. Do not store the skb pointer beyond the hook call.
If you return `NF_STOLEN`, you take ownership and must free it yourself.

**Q4. What is the network namespace impact?**
Modern kernels run multiple isolated network stacks (`struct net`). Code that
accesses `init_net` directly will break container environments. Production code
uses `dev_net(skb->dev)` to get the correct namespace.

**Q5. What are the performance constraints?**
A 10 Gbps link delivers ~14 Mpps. Your hook executes 14 million times per
second per CPU. Every allocation, every lock contention, every cache miss is
multiplied. Design for the hot path to be allocation-free, branch-minimal,
and cache-friendly.

**Q6. What is the upstream path?**
`netdev@vger.kernel.org` is the mailing list. David S. Miller and Jakub
Kicinski are the net maintainers. The `net` tree handles fixes; `net-next`
handles new features. Study `Documentation/process/submitting-patches.rst`
before your first submission.

---

## 2. Core data structures — what every net developer must know cold

### struct sk_buff (include/linux/skbuff.h)

The socket buffer. Every packet in the Linux network stack is this struct.

```
  skb->head ──► [headroom][data.........][tailroom] ◄── skb->end
                           ▲                        ▲
                       skb->data              skb->tail
                           │←────── skb->len ───────►│

  skb->network_header:    byte offset to IP header → access via ip_hdr(skb)
  skb->transport_header:  byte offset to TCP/UDP → access via tcp_hdr(skb)
  skb->mac_header:        byte offset to Ethernet header
```

Key functions:
- `ip_hdr(skb)`       — returns `struct iphdr *`
- `tcp_hdr(skb)`      — returns `struct tcphdr *`
- `udp_hdr(skb)`      — returns `struct udphdr *`
- `skb_put(skb, len)` — extend data area at tail (for TX path)
- `skb_push(skb,len)` — extend data area at head (prepend header)
- `skb_pull(skb,len)` — remove from head (consume a header layer)
- `pskb_may_pull(skb, len)` — ensure `len` bytes are in linear area

### struct iphdr (include/linux/ip.h)

```c
struct iphdr {
    __u8    version_ihl;   // upper nibble=version, lower nibble=IHL
    __u8    tos;
    __be16  tot_len;       // total length in network byte order
    __be16  id;
    __be16  frag_off;
    __u8    ttl;
    __u8    protocol;      // IPPROTO_TCP=6, IPPROTO_UDP=17, IPPROTO_ICMP=1
    __sum16 check;
    __be32  saddr;         // source IP — NETWORK byte order (__be32)
    __be32  daddr;         // destination IP — NETWORK byte order
};
```

CRITICAL: `saddr`/`daddr` are `__be32` (big-endian). To compare with a
human constant: `iph->saddr == htonl(0xC0A80001)` for 192.168.0.1.
Use `%pI4` in printk, not `%u` or `%x`.

### Netfilter hook points (include/linux/netfilter_ipv4.h)

```
NIC RX
  │
  ▼
NF_INET_PRE_ROUTING     ◄── ingress: DNAT, monitoring, filtering
  │
  ├─ local destination? ─► NF_INET_LOCAL_IN  ◄── for local processes
  │
  └─ forwarded? ──────────► NF_INET_FORWARD   ◄── router/bridge
                              │
NF_INET_POST_ROUTING    ◄────┘ and local OUT ◄── SNAT, egress filter
  │
  ▼
NIC TX
```

---

## 3. Key kernel APIs for network modules

| API | Header | Purpose |
|-----|--------|---------|
| `nf_register_net_hook()` | netfilter.h | Register a netfilter hook |
| `nf_unregister_net_hook()` | netfilter.h | Unregister hook |
| `ip_hdr(skb)` | ip.h | Get IPv4 header pointer |
| `tcp_hdr(skb)` | tcp.h | Get TCP header pointer |
| `udp_hdr(skb)` | udp.h | Get UDP header pointer |
| `ntohs(x)` / `htons(x)` | byteorder.h | 16-bit byte swap |
| `ntohl(x)` / `htonl(x)` | byteorder.h | 32-bit byte swap |
| `ipv4_is_loopback(addr)` | in.h | Test 127.0.0.0/8 |
| `atomic64_inc(&x)` | atomic.h | Atomic increment |
| `atomic64_read(&x)` | atomic.h | Atomic read |
| `kmalloc(size, GFP_ATOMIC)` | slab.h | Alloc (non-sleeping) |
| `kfree(ptr)` | slab.h | Free kernel memory |
| `proc_create()` | proc_fs.h | Create /proc entry |
| `proc_remove()` | proc_fs.h | Remove /proc entry |
| `seq_printf(m, fmt, ...)` | seq_file.h | Write to /proc output |

---

## 4. Build: from clone to loaded module

### Clone Linus's tree

```bash
# Linus's mainline tree (read-only mirror, updated daily)
git clone https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git

# Preferred for development: net-next tree (new features)
git clone https://git.kernel.org/pub/scm/linux/kernel/git/netdev/net-next.git

# Track upstream remotes for patching
cd linux
git remote add torvalds https://git.kernel.org/torvalds/linux.git
```

### Configure for net development

```bash
# Start from your distro's config (least-surprise approach)
cp /boot/config-$(uname -r) .config
make olddefconfig

# Or a minimal config for qemu testing:
make defconfig
make menuconfig
  # → Networking support → Networking options
  #   [*] Network packet filtering framework (Netfilter)
  #   [*]   IPv4: Netfilter Configuration
  # → Kernel hacking
  #   [*] KASAN: runtime memory debugger
  #   [*] Lock dependency validator (LOCKDEP)
  #   [*] Dynamic printk() support

# Enable Rust support (for Rust modules):
  # → General setup → Rust support
  # Requires: rustup target add x86_64-unknown-none
  #           cargo install --locked bindgen-cli
  make LLVM=1 rustavailable
```

### Build out-of-tree (fastest iteration cycle)

```bash
# Build the running kernel's headers first:
make -C /lib/modules/$(uname -r)/build scripts

# Build your module:
make -C /lib/modules/$(uname -r)/build M=$(pwd) modules

# Load:
sudo insmod net_monitor.ko drop_proto=0

# Reload after edit (one-liner):
sudo rmmod net_monitor; make -j$(nproc) && sudo insmod net_monitor.ko
```

### Build in-tree (required for upstream submission)

```bash
# 1. Copy source:
cp net_monitor.c linux/drivers/net/

# 2. Add to linux/drivers/net/Makefile:
echo 'obj-$(CONFIG_NET_MONITOR) += net_monitor.o' >> linux/drivers/net/Makefile

# 3. Add to linux/drivers/net/Kconfig (before the last endmenu):
cat >> linux/drivers/net/Kconfig << 'EOF'
config NET_MONITOR
    tristate "Net packet monitor (educational)"
    depends on NETFILTER && IP_NF_FILTER
    help
      IPv4 packet monitor via netfilter hooks.
EOF

# 4. Enable and build:
make menuconfig   # enable NET_MONITOR as M
make -j$(nproc) M=drivers/net modules
```

---

## 5. Testing strategy

### Layer 1: Compile-time analysis (zero runtime cost)

```bash
# Sparse — kernel's own type checker; catches __be32 vs u32 bugs
make C=1 CF="-D__CHECK_ENDIAN__" modules

# GCC with extra warnings:
make EXTRA_CFLAGS="-W -Wextra -Wshadow" modules

# checkpatch — enforces kernel coding style
perl scripts/checkpatch.pl --no-tree -f net_monitor.c
```

### Layer 2: Unit-level (module loaded, isolated tests)

```bash
# Ping loopback — generates ICMP:
ping -c 100 127.0.0.1

# TCP traffic:
curl http://localhost/

# UDP traffic:
echo test | nc -u -w1 127.0.0.1 9999

# High-rate test (pktgen):
modprobe pktgen
# See: Documentation/networking/pktgen.rst
```

### Layer 3: QEMU isolation (safe kernel testing)

```bash
# virtme: lightweight kernel test runner
pip install virtme
virtme-run --kdir /path/to/linux --mods=auto

# Or manual QEMU:
qemu-system-x86_64 \
  -kernel arch/x86/boot/bzImage \
  -append "root=/dev/vda console=ttyS0 nokaslr" \
  -drive file=rootfs.img,format=raw \
  -m 512M -nographic \
  -net nic,model=virtio -net user
```

### Layer 4: kselftest (automated kernel regression)

```bash
# Run network selftests:
make -C tools/testing/selftests/net run_tests

# Add your own test:
cp test_net_monitor.sh tools/testing/selftests/net/
# Add to tools/testing/selftests/net/Makefile:
# TEST_PROGS += test_net_monitor.sh
```

---

## 6. Bug catalogue and detection methods

### Bug class 1: Memory management

| Bug | Detection | Fix |
|-----|-----------|-----|
| Missing kfree() | kmemleak, valgrind on UML | Add kfree() on every exit path |
| Use-after-free | KASAN, KFENCE | Verify ownership before access |
| Double-free | KASAN | Single-owner pattern or refcount |
| Stack overflow | CONFIG_STACK_VALIDATION | Reduce local variable size |
| Sleeping in atomic | WARN_ON_ONCE(in_atomic()) | Use GFP_ATOMIC, avoid mutex |

### Bug class 2: Concurrency

| Bug | Detection | Fix |
|-----|-----------|-----|
| Data race | KCSAN (race detector) | atomic_t or spinlock |
| Deadlock | LOCKDEP | Consistent lock ordering |
| IRQ context lock | LOCKDEP | spin_lock_irqsave() |
| CPU hotplug unsafe | CPUHP validator | per-cpu ref counting |

### Bug class 3: Network-specific

| Bug | Detection | Fix |
|-----|-----------|-----|
| Byte-order confusion | Sparse + __CHECK_ENDIAN__ | Use htonl/ntohl or helpers |
| Wrong GFP flag | lockdep + might_sleep() | GFP_ATOMIC in hooks |
| skb linear check skip | WARN_ON + pskb_may_pull | Always call pskb_may_pull |
| net_ns unaware | netns test suite | Use dev_net() not init_net |

---

## 7. Submitting your patch upstream

```bash
# 1. Write a clean, single-purpose commit
git add net_monitor.c
git commit -s -m "net: add educational IPv4 packet monitor module

A simple netfilter-based IPv4 packet monitor for demonstration.
Registers hooks at PRE_ROUTING and POST_ROUTING, exposes stats
via /proc/net_monitor, and supports configurable per-protocol drop.

Signed-off-by: Your Name <you@example.com>"

# 2. Run checkpatch (MUST be clean before submission)
perl scripts/checkpatch.pl HEAD

# 3. Generate patch
git format-patch HEAD~1 --subject-prefix="PATCH net-next"

# 4. Check patch with get_maintainer.pl
perl scripts/get_maintainer.pl 0001-net-add*.patch
# Output: maintainers + mailing lists to CC

# 5. Send via git send-email
git send-email \
  --to=netdev@vger.kernel.org \
  --cc=davem@davemloft.net \
  --cc=kuba@kernel.org \
  0001-net-add*.patch

# 6. Monitor patchwork: https://patchwork.kernel.org/project/netdevbpf/
```

---

## 8. Complete documentation reference

### Primary: must read in order

1. **Documentation/process/submitting-patches.rst** — how to submit code
2. **Documentation/process/coding-style.rst** — mandatory code style
3. **Documentation/networking/netfilter-sysctl.rst** — netfilter runtime config
4. **Documentation/networking/packet_mmap.rst** — zero-copy packet capture
5. **Documentation/networking/pktgen.rst** — packet generator tool
6. **include/linux/skbuff.h** — sk_buff structure (read every field comment)
7. **include/linux/netfilter.h** — hook ops, verdict values
8. **include/linux/netfilter_ipv4.h** — IPv4 hook points and priorities
9. **net/netfilter/core.c** — netfilter hook registration internals
10. **net/ipv4/netfilter/** — existing IPv4 netfilter modules to model from

### Secondary: essential background

11. **Documentation/core-api/memory-allocation.rst** — kmalloc, GFP flags
12. **Documentation/core-api/atomic_ops.rst** — atomic_t, atomic64_t
13. **Documentation/locking/spinlocks.rst** — BH-safe spinlocks
14. **Documentation/filesystems/proc.rst** — /proc file creation
15. **Documentation/trace/kmemleak.rst** — memory leak detector
16. **Documentation/dev-tools/kasan.rst** — address sanitizer
17. **Documentation/dev-tools/sparse.rst** — static type checker
18. **Documentation/trace/ftrace.rst** — function tracer

### Online resources

- **LWN.net** — https://lwn.net — weekly deep-dives, subscribe
- **The Linux Kernel documentation** — https://www.kernel.org/doc/html/latest/
- **Elixir cross-reference** — https://elixir.bootlin.com — browse kernel source
- **netdev mailing list archive** — https://lore.kernel.org/netdev/
- **Kernel Newbies** — https://kernelnewbies.org/KernelHacking
- **Rust in Linux** — https://rust-for-linux.com

### Reference implementations (study these codepaths)

```
net/netfilter/nf_conntrack_core.c   — connection tracking (complex, full-featured)
net/netfilter/xt_LOG.c              — packet logging module (simple, clean)
net/ipv4/netfilter/nf_reject_ipv4.c — sending ICMP rejects
net/core/skbuff.c                   — sk_buff allocation and management
net/ipv4/ip_input.c                 — ip_rcv() — how packets enter the stack
drivers/net/loopback.c              — the simplest net_device driver
```
