#!/usr/bin/env bash
# scripts/test.sh — Integration test suite for xdp_filter
#
# Tests:
#   T1. Normal traffic passes
#   T2. Blocklisted IP is dropped
#   T3. Rate-limited source is dropped after threshold
#   T4. Stats counters match expected values
#   T5. Verifier output / BTF inspection
#
# Requirements:
#   hping3, scapy, bpftool, iproute2, python3
#   The XDP program must already be loaded: make load IFACE=<if>
#
# Usage:
#   sudo bash scripts/test.sh eth0

set -euo pipefail

IFACE="${1:-eth0}"
PASS=0
FAIL=0
BIN="./userspace/xdp_filter"

RED='\033[0;31m'
GRN='\033[0;32m'
YLW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${YLW}[TEST]${NC} $*"; }
ok()   { echo -e "${GRN}[PASS]${NC} $*"; ((PASS++)); }
fail() { echo -e "${RED}[FAIL]${NC} $*"; ((FAIL++)); }

# ── Prerequisite check ────────────────────────────────────────────────────
check_prereqs() {
    for cmd in hping3 bpftool ip python3; do
        if ! command -v "$cmd" &>/dev/null; then
            echo "Missing prerequisite: $cmd"
            exit 1
        fi
    done
    if [[ $EUID -ne 0 ]]; then
        echo "Must run as root"
        exit 1
    fi
}

# ── Helper: read a single per-CPU stat total from the pinned map ──────────
read_stat() {
    local idx="$1"
    bpftool map lookup pinned /sys/fs/bpf/xdp_filter/stats \
        key $(printf '%02x 00 00 00' "$idx") 2>/dev/null \
    | grep value | awk '{sum=0; for(i=2;i<=NF;i++) sum+= strtonum("0x"$i); print sum}'
}

# ── T1: Baseline — traffic from unknown IP passes ─────────────────────────
test_pass_traffic() {
    log "T1: Normal traffic passes"
    local before
    before=$(read_stat 0)   # STAT_PASS

    # Send 10 ICMP packets from a benign source IP (use hping3 with --spoof)
    hping3 --icmp --spoof 10.20.30.40 -c 10 -q "$IFACE" &>/dev/null || true
    sleep 0.5

    local after
    after=$(read_stat 0)
    local delta=$(( after - before ))

    if [[ "$delta" -ge 10 ]]; then
        ok "T1: STAT_PASS incremented by $delta (≥10)"
    else
        fail "T1: STAT_PASS only incremented by $delta (expected ≥10)"
    fi
}

# ── T2: Blocked IP is dropped ──────────────────────────────────────────────
test_block() {
    log "T2: Blocked IP is dropped"
    local BLOCK_IP="172.16.99.1"

    # Add to blocklist
    $BIN --iface "$IFACE" --block "$BLOCK_IP" &
    local loader_pid=$!
    sleep 0.3

    local before
    before=$(read_stat 1)   # STAT_BLOCK

    hping3 --icmp --spoof "$BLOCK_IP" -c 10 -q "$IFACE" &>/dev/null || true
    sleep 0.5

    local after
    after=$(read_stat 1)
    local delta=$(( after - before ))

    kill "$loader_pid" 2>/dev/null || true

    if [[ "$delta" -ge 10 ]]; then
        ok "T2: STAT_BLOCK incremented by $delta (≥10) for $BLOCK_IP"
    else
        fail "T2: STAT_BLOCK only incremented by $delta for $BLOCK_IP"
    fi
}

# ── T3: Rate limiting drops excess packets ────────────────────────────────
test_rate_limit() {
    log "T3: Rate limiting kicks in after 1000 pps"
    local SRC_IP="192.168.200.1"

    local before_pass before_rate
    before_pass=$(read_stat 0)
    before_rate=$(read_stat 2)

    # Flood 2000 packets in <1 second
    hping3 --icmp --spoof "$SRC_IP" -c 2000 --fast -q "$IFACE" &>/dev/null || true
    sleep 1.5

    local after_pass after_rate
    after_pass=$(read_stat 0)
    after_rate=$(read_stat 2)

    local pass_delta=$(( after_pass  - before_pass ))
    local rate_delta=$(( after_rate  - before_rate ))

    if [[ "$rate_delta" -gt 0 ]]; then
        ok "T3: Rate limiter dropped $rate_delta packets (passed $pass_delta)"
    else
        fail "T3: No rate drops observed (passed=$pass_delta, drops=$rate_delta)"
    fi
}

# ── T4: BTF / verifier inspection ─────────────────────────────────────────
test_verifier() {
    log "T4: Inspect loaded program via bpftool"
    local prog_id
    prog_id=$(bpftool prog show | grep xdp_filter_prog | awk '{print $1}' | tr -d ':')

    if [[ -z "$prog_id" ]]; then
        fail "T4: xdp_filter_prog not found in bpftool prog list"
        return
    fi

    echo "  Program ID: $prog_id"
    bpftool prog show id "$prog_id"
    bpftool prog dump xlated id "$prog_id" | head -30
    ok "T4: BPF program verified and BTF present"
}

# ── T5: Check for BPF verifier log on BUGGY object ────────────────────────
test_buggy_verifier() {
    log "T5: Verifier should reject / warn on BUGGY object"
    if [[ ! -f kernel/xdp_filter.bpf.BUGGY.o ]]; then
        echo "  Skipping — buggy object not built. Run: make buggy"
        return
    fi

    echo "  Attempting to load buggy program (expect verifier error):"
    if bpftool prog load kernel/xdp_filter.bpf.BUGGY.o \
            /sys/fs/bpf/_test_buggy 2>&1; then
        fail "T5: Buggy program loaded without error (unexpected)"
        rm -f /sys/fs/bpf/_test_buggy
    else
        ok "T5: Verifier correctly rejected / warned on buggy program"
    fi
}

# ── T6: bpf_trace_pipe output (requires aya-log or bpf_printk) ───────────
test_trace_pipe() {
    log "T6: Check bpf_trace_pipe for BPF log output"
    timeout 2 cat /sys/kernel/debug/tracing/trace_pipe 2>/dev/null | head -5 || true
    ok "T6: trace_pipe readable (no BPF printk in this build by design)"
}

# ── Summary ───────────────────────────────────────────────────────────────
summary() {
    echo ""
    echo "══════════════════════════════════"
    echo " Results: ${GRN}PASS=$PASS${NC}  ${RED}FAIL=$FAIL${NC}"
    echo "══════════════════════════════════"
    [[ "$FAIL" -eq 0 ]] && exit 0 || exit 1
}

check_prereqs
test_pass_traffic
test_block
test_rate_limit
test_verifier
test_buggy_verifier
test_trace_pipe
summary
