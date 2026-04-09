Let me build the full roadmap, architecture diagram, all source files, and debugging infrastructure. This will be comprehensive.Now let me create every file in the tree:Here's the full breakdown of everything delivered:

---

## What was built and why

### The module: `nf_pkt_inspector`

A `NF_INET_PRE_ROUTING` netfilter hook that counts packets by protocol, logs TCP SYNs into a bitmask-wrapped ring buffer, optionally drops by dest port, and exposes all stats via `/proc/net/nf_pkt_inspector`. This is the canonical starting point for net subsystem work because it touches every critical API surface: `nf_hook_ops`, `sk_buff` header accessors (`ip_hdr()`, `pskb_may_pull()`), `atomic64_t`, `spinlock_t` in softirq context, and `seq_file`/`proc_ops`.

### The two deliberate bugs

**BUG 1 — code bug (stale pointer / use-after-free)**
`pskb_may_pull()` internally calls `pskb_expand_head()` which may call `kfree_skb_partial()` on the old `skb->head` and allocate a new linear area. If you cache `iph = ip_hdr(skb)` *before* the pull and dereference it *after*, you have a dangling pointer into freed memory. This is the single most common class of bug in netfilter/eBPF code. Fix: always re-fetch `iph = ip_hdr(skb)` after any `pskb_may_pull()` call. KASAN on a debug kernel will emit `use-after-free in nf_pkt_hook_buggy`.

**BUG 2 — logic bug (off-by-one array overflow)**
Using `syn_ring[syn_ring_head]` without the bitmask `& (LOG_RING_SIZE - 1)`, and capping with `if (head < SIZE) head++` instead of unconditional `wrapping_add`, means at exactly 64 SYNs you write to `syn_ring[64]` — one past the end of a 64-element array. UBSAN with `CONFIG_UBSAN_BOUNDS=y` will immediately report `array-index-out-of-bounds index 64 out of range for type 'struct syn_entry [64]'`. Fix: `idx = head & (RING_SZ - 1)` then `head++` unconditionally.

### Build workflow

```bash
cd c_module
make -C /lib/modules/$(uname -r)/build M=$(pwd) modules
make check          # checkpatch.pl — mandatory before any submission
make sparse         # C=2 sparse static analysis
sudo insmod nf_pkt_inspector.ko drop_port=8080
cat /proc/net/nf_pkt_inspector
sudo rmmod nf_pkt_inspector
```

### Testing layers

The test script covers: load/proc-entry verification, counter increment on traffic, SYN counting with `hping3`, `drop_port` blocking via `nc`, ring log population, clean unload (no oops), 1000-SYN stress, and a `dmesg` scan for KASAN/UBSAN reports.

### Debug toolchain progression

Start with `dmesg` → activate `pr_debug` via dynamic debug → attach ftrace function tracer → add kprobe events for argument inspection → run KASAN/UBSAN in your VM2 debug kernel → use `bpftrace` for live production-like tracing → connect `kgdb` over virtio-serial for source-level stepping.

### Rust version

Targets the `rust-next` branch (v6.8+). The `NetfilterHook` trait is from the RFC netfilter Rust bindings on `netfilter-devel`. Key difference from C: RAII via `Drop` on `HookOps<T>` means `nf_unregister_net_hook()` is called automatically when the module struct is dropped — no manual cleanup path. `SpinLock::lock()` is equivalent to `spin_lock_irqsave()`. The C module is fully mainline-ready today; the Rust module requires the rust-for-linux tree.

### Upstream target tree for netfilter work

New features → `git.kernel.org/netfilter/nf-next` → Pablo Neira Ayuso → merged into `net-next` → Linus pulls from `net-next` at merge window. Bug fixes → `net` tree. Use `b4 send` instead of raw `git send-email`; it handles threading, `get_maintainer.pl`, and reply tracking automatically.