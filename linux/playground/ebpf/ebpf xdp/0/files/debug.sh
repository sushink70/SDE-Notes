#!/usr/bin/env bash
# scripts/debug.sh — XDP debug, tracing, and troubleshooting runbook
#
# Sections:
#   1. Program and map inspection (bpftool)
#   2. Live packet capture comparison
#   3. Kernel verifier verbose dump
#   4. perf/ftrace event tracing
#   5. BPF CO-RE / BTF validation
#   6. Troubleshooting cookbook

set -euo pipefail
IFACE="${1:-eth0}"

banner() { echo -e "\n\033[1;34m══ $* ══\033[0m"; }

# ── 1. Program Inspection ─────────────────────────────────────────────────
banner "1. BPF Program State"

echo "--- Loaded XDP programs ---"
bpftool prog show type xdp 2>/dev/null || echo "(none)"

echo ""
echo "--- Program attached to $IFACE ---"
ip link show dev "$IFACE" | grep -o 'prog/xdp.*' || echo "(no XDP attached)"

# Dump translated BPF bytecode (kernel's view after JIT)
PROG_ID=$(bpftool prog show | grep xdp_filter_prog | awk '{print $1}' | tr -d ':' | head -1)
if [[ -n "$PROG_ID" ]]; then
    echo ""
    echo "--- BPF bytecode (prog id=$PROG_ID) ---"
    bpftool prog dump xlated id "$PROG_ID" linum 2>/dev/null | head -60

    echo ""
    echo "--- JIT-compiled x86_64 assembly ---"
    bpftool prog dump jited id "$PROG_ID" linum 2>/dev/null | head -40

    echo ""
    echo "--- BTF (type info) ---"
    bpftool prog dump xlated id "$PROG_ID" visual 2>/dev/null > /tmp/xdp_cfg.dot
    echo "CFG dot file: /tmp/xdp_cfg.dot  (view: dot -Tsvg /tmp/xdp_cfg.dot > cfg.svg)"
fi

# ── 2. Map Inspection ────────────────────────────────────────────────────
banner "2. BPF Map State"

echo "--- All maps ---"
bpftool map show 2>/dev/null | head -30

if [[ -f /sys/fs/bpf/xdp_filter/blocklist ]]; then
    echo ""
    echo "--- Blocklist entries ---"
    bpftool map dump pinned /sys/fs/bpf/xdp_filter/blocklist 2>/dev/null || echo "(empty)"

    echo ""
    echo "--- Rate map (first 5 entries) ---"
    bpftool map dump pinned /sys/fs/bpf/xdp_filter/rate_map 2>/dev/null | head -30 || true

    echo ""
    echo "--- Stats (raw per-CPU) ---"
    for idx in 0 1 2 3; do
        label=("PASS" "BLOCK" "RATE_DROP" "PARSE_ERR")
        val=$(bpftool map lookup pinned /sys/fs/bpf/xdp_filter/stats \
                  key $(printf '%02x 00 00 00' "$idx") 2>/dev/null \
              | grep value | awk '{sum=0; for(i=2;i<=NF;i++) sum+=strtonum("0x"$i); print sum}')
        echo "  ${label[$idx]}=$val"
    done
fi

# ── 3. Verifier Verbose (load with BPF_LOG_LEVEL=2) ──────────────────────
banner "3. Verifier Verbose Log"
echo "To get full verifier output for any BPF object:"
cat <<'EOF'
  # Method A: bpftool with verbose flag
  bpftool prog load kernel/xdp_filter.bpf.o /sys/fs/bpf/_test \
      2>&1 | tee /tmp/verifier.log
  rm -f /sys/fs/bpf/_test

  # Method B: via libbpf in your loader (C)
  //  struct bpf_object_open_opts opts = {};
  //  opts.kernel_log_level = 2;  /* BPF_LOG_LEVEL2 — full verifier trace */
  //  struct bpf_object *obj = bpf_object__open_opts("prog.o", &opts);

  # Method C: raw syscall log buffer (most verbose)
  python3 - <<'PYEOF'
  import ctypes, os, struct
  BPF_PROG_LOAD = 5
  # Set log_level=2, log_buf + log_size to capture verifier output
  PYEOF
EOF

# ── 4. Live Packet Tracing with tc/XDP ───────────────────────────────────
banner "4. Live Packet / Event Tracing"
echo "--- Capture packets on $IFACE (tcpdump comparison) ---"
echo "  # In terminal 1: watch drops from XDP perspective"
echo "  watch -n1 'ip -s link show $IFACE | grep -A2 RX'"
echo ""
echo "  # In terminal 2: tcpdump for packets that PASS XDP (already in stack)"
echo "  tcpdump -i $IFACE -nn icmp -c 20"
echo ""
echo "  # XDP drop counter via ethtool (driver must support)"
echo "  ethtool -S $IFACE | grep -i 'xdp\\|drop'"
echo ""

# ── 5. perf + BPF tracing ────────────────────────────────────────────────
banner "5. perf BPF event profiling"
cat <<'EOF'
  # Record XDP program execution (requires perf + kernel ≥ 5.5)
  perf stat -e 'xdp:*' -- sleep 5

  # Trace with bpftrace (alternative to bpf_printk)
  bpftrace -e 'tracepoint:xdp:xdp_exception { printf("exception: %s action=%d\n", str(args->name), args->act); }'

  # Trace kfree_skb for drops (shows why kernel dropped packets)
  bpftrace -e 'kprobe:kfree_skb { @[kstack()] = count(); }'

  # Monitor BPF map operations (debug map misses)
  bpftrace -e 'kretprobe:htab_map_lookup_elem { @hits = count(); }'
EOF

# ── 6. BTF / CO-RE Validation ─────────────────────────────────────────────
banner "6. BTF and CO-RE validation"
echo "--- Check kernel BTF is available ---"
ls -la /sys/kernel/btf/vmlinux 2>/dev/null || echo "ERROR: kernel BTF not available (recompile with CONFIG_DEBUG_INFO_BTF=y)"

echo ""
echo "--- Validate BPF object BTF ---"
if [[ -f kernel/xdp_filter.bpf.o ]]; then
    bpftool btf dump file kernel/xdp_filter.bpf.o format c 2>/dev/null | head -20
fi

# ── 7. Common Failure Diagnostics ─────────────────────────────────────────
banner "7. Troubleshooting Cookbook"
cat <<'EOF'

SYMPTOM: "libbpf: failed to load program: Operation not permitted"
   CAUSE:  Missing CAP_BPF or CAP_SYS_ADMIN
   FIX:    Run as root, or: setcap cap_bpf,cap_net_admin+eip ./xdp_filter

SYMPTOM: "libbpf: BTF is required, but is missing or corrupted"
   CAUSE:  Kernel compiled without CONFIG_DEBUG_INFO_BTF=y
   CHECK:  zcat /proc/config.gz | grep CONFIG_DEBUG_INFO_BTF
   FIX:    Recompile kernel, or use pahole + dwarf-to-BTF conversion

SYMPTOM: "xdp: NIC does not support XDP" or attach fails
   CAUSE:  Driver does not support native XDP (DRV_MODE)
   FIX:    Use --skb-mode flag for generic/SKB fallback
   CHECK:  ethtool -i eth0 | grep driver  # check driver name
           # Drivers with native XDP: mlx5, i40e, ixgbe, virtio_net, veth

SYMPTOM: Blocklist entries added but IPs not being dropped (BUG #2 pattern)
   CAUSE:  Byte-order mismatch between BPF key and userspace key
   DEBUG:  bpftool map dump pinned /sys/fs/bpf/xdp_filter/blocklist
           # Look at raw hex key vs expected IP bytes
           # 192.168.1.100 in network order = c0 a8 01 64
           # If you see 64 01 a8 c0 — you have a host-order bug

SYMPTOM: Verifier error "invalid access to map value"
   CAUSE:  Missing bounds check after bpf_map_lookup_elem
   FIX:    Always check `if (!ptr) return XDP_PASS;` before dereferencing

SYMPTOM: High CPU usage on XDP path
   DEBUG:  perf top -p $(pgrep kswapd) --call-graph dwarf
           perf stat -e cycles,instructions -a -- sleep 5
   FIX:    Ensure driver supports native XDP; avoid per-packet bpf_printk

SYMPTOM: "BPF program too large" verifier error
   CAUSE:  Exceeded 1M instructions limit (kernel ≥ 5.2) or
           too many inlined functions
   FIX:    Remove __always_inline from non-hot helpers
           Increase BPF_COMPLEXITY_LIMIT via BPF_F_ANY_ALIGNMENT

SYMPTOM: CO-RE relocation fails at load time
   CAUSE:  vmlinux.h generated from different kernel version
   FIX:    Regenerate: bpftool btf dump file /sys/kernel/btf/vmlinux format c > vmlinux.h
           Rebuild BPF object on the target machine

SYMPTOM: XDP program suddenly stops counting (stats frozen)
   CAUSE:  LRU eviction causing rate_map entries to be dropped
   FIX:    Increase max_entries in rate_map, or use PERCPU_HASH variant

EOF

echo "Debug session complete."
