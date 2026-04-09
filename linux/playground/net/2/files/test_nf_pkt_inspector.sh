#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-only
#
# test_nf_pkt_inspector.sh — functional + stress test suite
#
# This script follows the pattern of tools/testing/selftests/net/
# Tests should pass on any kernel >= 5.15 with the module loaded.
#
# Dependencies: hping3, curl, nc (netcat-openbsd), ip, awk, grep
#
# Usage:
#   chmod +x test_nf_pkt_inspector.sh
#   sudo ./test_nf_pkt_inspector.sh          # run all tests
#   sudo ./test_nf_pkt_inspector.sh t_drop   # run single test
#
# Exit codes:
#   0 = all tests passed
#   1 = one or more tests failed

set -euo pipefail

readonly MOD_NAME="nf_pkt_inspector"
readonly PROC_FILE="/proc/net/nf_pkt_inspector"
readonly KO="./nf_pkt_inspector.ko"
readonly LOOPBACK="127.0.0.1"
readonly DROP_PORT=19999

# ── colour helpers ────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
pass() { printf "${GREEN}PASS${NC} %s\n" "$1"; }
fail() { printf "${RED}FAIL${NC} %s\n" "$1"; FAILURES=$((FAILURES+1)); }
info() { printf "${YELLOW}INFO${NC} %s\n" "$1"; }

FAILURES=0

# ── prerequisite checks ───────────────────────────────────────────────────────
require_root() {
    [[ $EUID -eq 0 ]] || { echo "ERROR: must run as root"; exit 1; }
}

require_tools() {
    for t in hping3 nc ip awk grep dmesg; do
        command -v "$t" &>/dev/null || { echo "missing: $t"; exit 1; }
    done
}

# ── module management ─────────────────────────────────────────────────────────
load_module() {
    local drop_port="${1:-0}"
    if lsmod | grep -q "^${MOD_NAME} "; then
        info "module already loaded, removing first"
        rmmod "$MOD_NAME" 2>/dev/null || true
    fi
    insmod "$KO" "drop_port=${drop_port}" || { echo "insmod failed"; exit 1; }
    sleep 0.1
    info "module loaded (drop_port=${drop_port})"
}

unload_module() {
    rmmod "$MOD_NAME" 2>/dev/null || true
}

# Read a counter from /proc/net/nf_pkt_inspector
# Usage: read_counter pkt_total
read_counter() {
    awk -v key="${1}:" '$1==key {print $2}' "$PROC_FILE" 2>/dev/null
}

# ── individual tests ──────────────────────────────────────────────────────────

# T1: module loads and /proc entry appears
t_load() {
    info "T1: module load and /proc entry"
    load_module 0
    if [[ -r "$PROC_FILE" ]]; then
        pass "t_load: $PROC_FILE exists"
    else
        fail "t_load: $PROC_FILE missing"
    fi
}

# T2: packet counter increments on traffic
t_counters() {
    info "T2: packet counter increment"
    load_module 0
    local before
    before=$(read_counter pkt_total)

    # generate a few packets — curl to localhost (any port that will refuse)
    curl -s --connect-timeout 1 "http://${LOOPBACK}:65432/" &>/dev/null || true
    sleep 0.2

    local after
    after=$(read_counter pkt_total)

    if [[ "$after" -gt "$before" ]]; then
        pass "t_counters: pkt_total $before → $after"
    else
        fail "t_counters: pkt_total did not increase ($before → $after)"
    fi
}

# T3: TCP SYN counter increments when SYNs are sent
t_syn_count() {
    info "T3: TCP SYN counter"
    load_module 0
    local before
    before=$(read_counter pkt_tcp_syn)

    # hping3 -S: send SYN-only packets
    # -c 5: 5 packets, -p 80, --fast: fast mode
    hping3 -S -c 5 -p 80 --fast "$LOOPBACK" &>/dev/null 2>&1 || true
    sleep 0.5

    local after
    after=$(read_counter pkt_tcp_syn)

    if [[ "$after" -ge $((before + 5)) ]]; then
        pass "t_syn_count: pkt_tcp_syn $before → $after (≥ +5)"
    else
        fail "t_syn_count: expected ≥5 new SYNs, got $((after - before))"
    fi
}

# T4: drop_port blocks connections
t_drop() {
    info "T4: drop_port=$DROP_PORT blocks TCP"
    load_module "$DROP_PORT"

    # Start a listener on DROP_PORT
    nc -l -p "$DROP_PORT" &>/dev/null &
    local nc_pid=$!
    sleep 0.1

    local before_drop
    before_drop=$(read_counter pkt_dropped)

    # This connect should be dropped at netfilter — nc will time out
    timeout 2 nc -zv "$LOOPBACK" "$DROP_PORT" &>/dev/null 2>&1 || true
    sleep 0.3

    local after_drop
    after_drop=$(read_counter pkt_dropped)

    kill "$nc_pid" 2>/dev/null || true

    if [[ "$after_drop" -gt "$before_drop" ]]; then
        pass "t_drop: drop counter $before_drop → $after_drop"
    else
        fail "t_drop: drop counter unchanged — packets not dropped"
    fi
}

# T5: SYN ring log has entries after SYNs
t_syn_ring() {
    info "T5: SYN ring log populated"
    load_module 0
    hping3 -S -c 3 -p 443 --fast "$LOOPBACK" &>/dev/null 2>&1 || true
    sleep 0.5

    if grep -qE "[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+" "$PROC_FILE"; then
        pass "t_syn_ring: ring has IP entries"
    else
        fail "t_syn_ring: no IP entries in SYN log"
    fi
}

# T6: module unloads cleanly — no kernel oops
t_unload() {
    info "T6: clean unload"
    load_module 0
    local dmesg_before
    dmesg_before=$(dmesg | wc -l)

    unload_module
    sleep 0.1

    # Check for oops / BUG in new dmesg lines
    if dmesg | tail -n +$((dmesg_before+1)) | grep -qiE "oops|BUG:|kernel bug|general protection"; then
        fail "t_unload: kernel oops on unload"
    else
        pass "t_unload: clean unload, no oops"
    fi
}

# T7: stress — 1000 SYNs should not crash the kernel
t_stress() {
    info "T7: stress 1000 SYNs"
    load_module 0

    # Send 1000 SYNs quickly
    hping3 -S -c 1000 -p 80 --faster "$LOOPBACK" &>/dev/null 2>&1 || true
    sleep 1

    local total
    total=$(read_counter pkt_tcp_syn)
    if [[ "$total" -ge 1000 ]]; then
        pass "t_stress: handled ≥1000 SYNs (got $total)"
    else
        fail "t_stress: only counted $total SYNs (expected ≥1000)"
    fi

    # Kernel still responsive?
    if echo test > /dev/null && [[ -r /proc/net/dev ]]; then
        pass "t_stress: kernel still responsive"
    else
        fail "t_stress: kernel may be unresponsive"
    fi
}

# ── regression: dmesg scan for anything concerning ────────────────────────────
t_dmesg_clean() {
    info "T8: dmesg regression scan"
    if dmesg | grep -qE "KASAN|UBSAN|use-after-free|out-of-bounds|double-free" ; then
        fail "t_dmesg_clean: KASAN/UBSAN report found in dmesg!"
        dmesg | grep -E "KASAN|UBSAN|use-after-free|out-of-bounds|double-free" | head -10
    else
        pass "t_dmesg_clean: no memory safety issues in dmesg"
    fi
}

# ── main ──────────────────────────────────────────────────────────────────────
main() {
    require_root
    require_tools

    info "=== nf_pkt_inspector test suite ==="

    if [[ $# -gt 0 ]]; then
        # Run named test(s)
        for t in "$@"; do
            "$t"
        done
    else
        # Run all
        t_load
        t_counters
        t_syn_count
        t_drop
        t_syn_ring
        t_unload
        t_stress
        t_dmesg_clean
    fi

    unload_module

    echo ""
    if [[ $FAILURES -eq 0 ]]; then
        printf "${GREEN}All tests passed.${NC}\n"
        exit 0
    else
        printf "${RED}${FAILURES} test(s) FAILED.${NC}\n"
        exit 1
    fi
}

main "$@"
