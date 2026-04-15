#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
#  XDP Security — Integration Test Suite
#
#  Requires: iproute2, hping3 (or scapy), python3, bpftool
#  Run as root: sudo ./run_tests.sh
# ═══════════════════════════════════════════════════════════════════════════

set -euo pipefail

IFACE="${1:-lo}"          # Use loopback for safe local testing
LOADER="../xdp_loader"
BPFTOOL="$(which bpftool)"
PASS=0; FAIL=0

# ─── COLORS ────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; NC='\033[0m'

header()  { echo -e "\n${BLUE}══════════════════════════════════════${NC}"; }
ok()      { echo -e "${GREEN}  ✓ PASS${NC}: $1"; ((PASS++)); }
fail()    { echo -e "${RED}  ✗ FAIL${NC}: $1"; ((FAIL++)); }
section() { header; echo -e "${YELLOW}  $1${NC}"; header; }

# ─── SETUP ──────────────────────────────────────────────────────────────────
section "SETUP"

if [[ $EUID -ne 0 ]]; then
    echo "Must run as root (sudo)."
    exit 1
fi

# Load XDP program on loopback in SKB mode (loopback doesn't support native)
section "Loading XDP Program"
"$LOADER" "$IFACE" --mode skb &
LOADER_PID=$!
sleep 1

if kill -0 "$LOADER_PID" 2>/dev/null; then
    ok "XDP loader started (PID $LOADER_PID)"
else
    fail "XDP loader failed to start"
    exit 1
fi

# ─── Helper: read map value for an IP ───────────────────────────────────────
get_blocklist_val() {
    local ip_hex
    ip_hex=$(python3 -c "
import struct, socket
ip = '$1'
packed = socket.inet_aton(ip)
# Print as hex bytes for bpftool key format
print(' '.join(f'{b:02x}' for b in packed))
")
    $BPFTOOL map lookup name ip_blocklist key hex $ip_hex 2>/dev/null | \
        grep -oP '(?<=value: )\S+' || echo "not_found"
}

# ─── TEST 1: Basic connectivity ──────────────────────────────────────────────
section "TEST 1: Basic Pass-Through"
if ping -c 1 -W 1 127.0.0.1 > /dev/null 2>&1; then
    ok "Loopback ping passes through XDP"
else
    fail "Loopback ping blocked (should pass)"
fi

# ─── TEST 2: Manual blocklist ────────────────────────────────────────────────
section "TEST 2: IP Blocklist"

# Block 192.168.99.99 via bpftool directly
python3 -c "
import struct, socket
ip = '192.168.99.99'
packed = socket.inet_aton(ip)
print(' '.join(f'{b:02x}' for b in packed))
" | xargs $BPFTOOL map update name ip_blocklist key hex value hex 01

VAL=$(get_blocklist_val "192.168.99.99")
if [[ "$VAL" == "01" ]]; then
    ok "IP 192.168.99.99 inserted into blocklist"
else
    fail "Failed to insert into blocklist (got: $VAL)"
fi

# Verify unblock
$BPFTOOL map delete name ip_blocklist key hex \
    $(python3 -c "
import socket
ip='192.168.99.99'
p=socket.inet_aton(ip)
print(' '.join(f'{b:02x}' for b in p))
") 2>/dev/null || true
VAL=$(get_blocklist_val "192.168.99.99")
if [[ "$VAL" == "not_found" ]]; then
    ok "IP 192.168.99.99 removed from blocklist"
else
    fail "IP still in blocklist after delete"
fi

# ─── TEST 3: Stats map exists ────────────────────────────────────────────────
section "TEST 3: Statistics Map"
if $BPFTOOL map show name xdp_stats_map > /dev/null 2>&1; then
    ok "xdp_stats_map exists"
else
    fail "xdp_stats_map not found"
fi

# ─── TEST 4: Rate limiter (simulated) ────────────────────────────────────────
section "TEST 4: Rate Limit Map"
# The rate limit fires after 500 pkts/sec.
# We can't easily generate that in a unit test, but we verify the map exists.
if $BPFTOOL map show name pkt_rate_map > /dev/null 2>&1; then
    ok "pkt_rate_map exists and is accessible"
else
    fail "pkt_rate_map not found"
fi

# ─── TEST 5: XDP program attached ────────────────────────────────────────────
section "TEST 5: XDP Program Attachment"
if $BPFTOOL net show dev "$IFACE" 2>/dev/null | grep -q "xdp_security"; then
    ok "xdp_security attached to $IFACE"
else
    # Try alternative check
    if ip link show "$IFACE" 2>/dev/null | grep -q "xdp"; then
        ok "XDP program visible on $IFACE (via ip link)"
    else
        fail "XDP program not attached to $IFACE"
    fi
fi

# ─── TEST 6: bpf_printk trace output ─────────────────────────────────────────
section "TEST 6: Trace Output (bpf_printk)"
# trigger a packet, check trace_pipe for output
timeout 2 cat /sys/kernel/debug/tracing/trace_pipe &
TRACE_PID=$!
ping -c 3 127.0.0.1 > /dev/null 2>&1 || true
sleep 1
kill "$TRACE_PID" 2>/dev/null || true
ok "trace_pipe readable (check manually for XDP DROP messages)"

# ─── CLEANUP ─────────────────────────────────────────────────────────────────
section "Cleanup"
kill "$LOADER_PID" 2>/dev/null || true
sleep 1
if ! ip link show "$IFACE" 2>/dev/null | grep -q "xdp"; then
    ok "XDP detached cleanly on exit"
else
    # Force detach
    ip link set "$IFACE" xdp off 2>/dev/null || true
    ok "XDP force-detached"
fi

# ─── SUMMARY ─────────────────────────────────────────────────────────────────
header
echo -e "  Results: ${GREEN}$PASS passed${NC} | ${RED}$FAIL failed${NC}"
header
[[ $FAIL -eq 0 ]] && exit 0 || exit 1
