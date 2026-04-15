Here is the complete reference system. Let me walk through the entire thing.

---

## Summary

This is a production-grade XDP packet filter implementing an IP blocklist + per-source rate limiter using `BPF_MAP_TYPE_LRU_HASH` and `PERCPU_ARRAY`. The C version uses libbpf + CO-RE (Compile Once, Run Everywhere via BTF); the Rust version uses the `aya` framework with idiomatic Rust ownership on the control plane. Two intentional bugs — a classic operator assignment-as-condition and a network/host byte-order inversion — demonstrate the two most common categories of BPF correctness failures. The full kernel developer workflow from clone → code → selftest → `bpf-next` mailing list is documented. Every diagnostic command maps to a specific failure mode.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Network Interface (eth0)                    │
│           NIC Driver (virtio_net / i40e / mlx5)                 │
└─────────────────────┬───────────────────────────────────────────┘
                      │ DMA ring buffer (raw frame)
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│         XDP Hook (BEFORE skb allocation)                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  xdp_filter_prog(ctx)                                    │   │
│  │  ┌──────────┐  ┌─────────────────┐  ┌────────────────┐  │   │
│  │  │ Parse    │  │ Blocklist Lookup │  │ Rate Limit     │  │   │
│  │  │ eth+ipv4 │→ │ HASH map O(1)   │→ │ LRU_HASH map   │  │   │
│  │  └──────────┘  └─────────────────┘  └────────────────┘  │   │
│  │       ↓              ↓ match              ↓ over limit   │   │
│  │  XDP_PASS       XDP_DROP              XDP_DROP           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  BPF Maps (kernel memory):                                      │
│  ┌──────────────┐ ┌────────────────────┐ ┌──────────────────┐  │
│  │ blocklist    │ │ rate_map (LRU)     │ │ stats (per-CPU)  │  │
│  │ HASH         │ │ src_ip→count+time  │ │ [pass,blk,rt,pe] │  │
│  │ src_ip→flag  │ │ LRU_HASH           │ │ PERCPU_ARRAY     │  │
│  └──────────────┘ └────────────────────┘ └──────────────────┘  │
└──────────────────────────────┬──────────────────────────────────┘
                               │ /sys/fs/bpf/xdp_filter/ (pinned)
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                Userspace Control Plane                          │
│  xdp_filter.c (C/libbpf) │ xdp-filter/src/main.rs (Rust/aya)  │
│  - bpf_xdp_attach()       │ - program.attach(&iface, flags)    │
│  - blocklist CRUD          │ - HashMap<u32,u8> blocklist CRUD   │
│  - per-CPU stats poll      │ - tokio async stats loop           │
└─────────────────────────────────────────────────────────────────┘

Patch submission flow:
  Your fork → git format-patch → bpf@vger.kernel.org
            → Alexei/Daniel review → bpf-next tree
            → net-next → Linus mainline (merge window)
```

---

## End-to-End Build and Load

```bash
# ── 0. Install prerequisites ──────────────────────────────────────────────
sudo apt install -y clang llvm libelf-dev libbpf-dev bpftool \
    linux-headers-$(uname -r) linux-tools-$(uname -r) \
    hping3 iproute2

# ── 1. Generate vmlinux.h from running kernel's BTF ──────────────────────
# (requires CONFIG_DEBUG_INFO_BTF=y — check: zcat /proc/config.gz | grep BTF)
bpftool btf dump file /sys/kernel/btf/vmlinux format c > kernel/vmlinux.h

# ── 2. Compile BPF kernel-side object ────────────────────────────────────
clang -O2 -g -target bpf -D__TARGET_ARCH_x86 \
    -I/usr/include/x86_64-linux-gnu -Ikernel \
    -c kernel/xdp_filter.bpf.c -o kernel/xdp_filter.bpf.o

# ── 3. Generate libbpf skeleton (type-safe C wrapper) ─────────────────────
bpftool gen skeleton kernel/xdp_filter.bpf.o > userspace/xdp_filter.skel.h

# ── 4. Compile userspace loader ───────────────────────────────────────────
gcc -O2 -g -Wall -Iuserspace -Ikernel \
    userspace/xdp_filter.c -o xdp_filter \
    -lbpf -lelf -lz

# ── 5. Attach to interface ────────────────────────────────────────────────
sudo ./xdp_filter --iface eth0 --block 10.0.0.1 --stats

# ── 6. Verify attachment ──────────────────────────────────────────────────
ip link show eth0         # shows: prog/xdp id XX
bpftool prog show type xdp
bpftool map show

# ── 7. Manual detach ──────────────────────────────────────────────────────
sudo ip link set eth0 xdp off

# ── Or use Makefile ───────────────────────────────────────────────────────
make all
make load IFACE=eth0
make unload IFACE=eth0
```

**For Rust/aya:**
```bash
# Install Rust BPF target
rustup target add bpfel-unknown-none
cargo install bpf-linker

# Build BPF crate first (cross-compile to BPF target)
cd rust-aya
cargo build --package xdp-filter-ebpf \
    --target bpfel-unknown-none \
    -Z build-std=core

# Build and run userspace (embeds BPF ELF via include_bytes_aligned!)
sudo cargo run --release -- --iface eth0 --block 192.168.1.100 --stats
```

---

## Kernel Contribution Workflow (How Linus's Tree Works)

Linus's GitHub is a **read-only mirror**. Patches go via **email to mailing lists**. For BPF specifically:

```
Your patch → bpf@vger.kernel.org
           → reviewed by Alexei Starovoitov + Daniel Borkmann
           → merged into git.kernel.org/bpf/bpf-next
           → pulled into net-next during merge window
           → pulled by Linus into mainline
```

The **critical rule**: every BPF submission requires a corresponding selftest in `tools/testing/selftests/bpf/prog_tests/`. No selftest = immediate rejection. The `xdp_filter_test.c` file here is formatted to drop directly into that directory.

---

## The Two Bugs — Detection and Fix

**Bug #1 (Code Bug):** `if (ip->ihl = 5)` — assignment in condition. Effect: IHL is overwritten to 5 in the live packet, the guard is bypassed entirely, all subsequent logic (blocklist, rate limiter) is skipped. The compiler warns with `-Wparentheses` but still produces a binary. The BPF verifier does not detect this — it's a logical correctness issue, not a safety violation.

```bash
# Reproduce: build buggy, load, send from blocked IP → STAT_BLOCK stays 0
clang -O2 -g -target bpf -Wno-parentheses \
    -c kernel/xdp_filter.bpf.BUGGY.c -o kernel/xdp_filter.bpf.BUGGY.o
bpftool prog load kernel/xdp_filter.bpf.BUGGY.o /sys/fs/bpf/_test
# Fix: change `=` to `<`
```

**Bug #2 (Logic Bug):** `bpf_ntohl(ip->saddr)` converts the already-network-order source IP to host order before using it as the map key. The userspace loader uses `inet_addr()` which returns network order. On little-endian x86_64, 192.168.1.100 (0xc0a80164) becomes 0x6401a8c0 — they never match. The blocklist is populated but completely ineffective.

```bash
# Detect with bpf_printk instrumentation:
bpf_printk("lookup_key=%08x", src_ip);
cat /sys/kernel/debug/tracing/trace_pipe
# Shows: 6401a8c0 but map has c0a80164 → mismatch confirmed
# Fix: remove bpf_ntohl(), use src_ip = ip->saddr directly
# Prevention: annotate with __be32 and run: make C=2 CF="-D__CHECK_ENDIAN__"
```

---

## Threat Model

| Threat | BPF surface | Mitigation |
|---|---|---|
| Malicious BPF bytecode | Kernel verifier | Verifier enforces type safety, bounds, loop termination; never loads unverified code |
| Map poisoning from userspace | Map FDs require `CAP_BPF` | Drop caps after load; pin maps with restrictive perms `chmod 600` |
| IP spoofing bypasses blocklist | XDP sees L3 header only | Combine with conntrack or use L4 tuple; blocklist is anti-DDoS, not authentication |
| LRU eviction flushes rate entries | `LRU_HASH` evicts under pressure | Monitor `bpftool map show` for entry counts; use `PERCPU_LRU_HASH` for higher scale |
| Verifier bypass via JIT spray | JIT produces non-executable memory by default | `sysctl net.core.bpf_jit_harden=2` enables constant blinding |
| BPF program pinned in sysfs | Persistent across restarts | Audit `/sys/fs/bpf/` in your seccomp/LSM policy; use `bpf_token` (kernel ≥ 6.7) |

---

## Roll-out and Rollback

```bash
# Staged rollout: test on loopback first (always available, no NIC needed)
sudo ./xdp_filter --iface lo --skb-mode --stats

# Canary: attach to a TAP/veth in a network namespace
ip netns add test-ns
ip link add veth0 type veth peer name veth1
ip link set veth1 netns test-ns
sudo ./xdp_filter --iface veth0 --stats

# Production attach (native mode)
sudo ./xdp_filter --iface eth0 --stats

# ROLLBACK — immediate, zero-downtime
sudo ip link set eth0 xdp off
# All packets resume normal kernel stack processing immediately.
# Pinned maps remain in /sys/fs/bpf/xdp_filter/ (state preserved for reload)

# Full state wipe:
rm -rf /sys/fs/bpf/xdp_filter/
```

---

## Elite Kernel Developer Roadmap (Condensed)

The roadmap file has the complete phase-by-phase breakdown, but the key inflection points are:

1. **Phase 0**: Clone `bpf-next`, not `torvalds/linux`. That's where all BPF work actually lands. Configure with `CONFIG_DEBUG_INFO_BTF=y CONFIG_KASAN=y CONFIG_KCSAN=y`. Test in QEMU with virtio_net (native XDP support).

2. **Phase 1**: Study `tools/testing/selftests/bpf/prog_tests/` exhaustively. Every accepted feature in the kernel has a selftest here. These are your canonical examples, not samples/bpf/.

3. **Phase 2**: Read `kernel/bpf/verifier.c` top-to-bottom once. It's 14,000 lines but teaches you exactly what is and isn't valid BPF. Understanding the verifier is what separates an eBPF user from a kernel BPF developer.

4. **Phase 3**: Submit a patch. Even a documentation fix. The process of `checkpatch`, `get_maintainer`, `format-patch`, email to `bpf@vger.kernel.org`, and responding to Alexei or Daniel's review is a skill in itself.

---

## Next 3 Steps

1. **Build and verify the clean C version locally in QEMU** — run `make all`, confirm `bpftool prog show type xdp` shows the loaded program, then build and load the BUGGY version and use `bpf_prog_test_run` from the selftest to confirm blocklist misses. This gives you the end-to-end hands-on loop.

2. **Add a `BPF_MAP_TYPE_LPM_TRIE` for CIDR-based blocking** (`kernel/bpf/lpm_trie.c`) — replace the exact-match hash with a longest-prefix-match trie so you can block `10.0.0.0/8` rather than individual IPs. This is the next real-world feature and teaches the most complex BPF map type.

3. **Run the full kernel selftest suite** — `cd tools/testing/selftests/bpf && make -j$(nproc) && sudo ./test_progs -j8` — and find one failing or flaky test, bisect it with `git bisect`, and send a fix patch to `bpf@vger.kernel.org`. That is the actual rite of passage.