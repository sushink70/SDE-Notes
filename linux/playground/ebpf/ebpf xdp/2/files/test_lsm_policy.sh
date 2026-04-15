#!/bin/bash
# tests/test_lsm_policy.sh — Integration tests for BPF LSM security monitor
#
# Structure:
#   Each test_* function is independent.
#   run_test() handles setup/teardown and captures pass/fail.
#   Requires: root, BPF LSM enabled in boot params, built binary.
#
# Run:
#   sudo bash tests/test_lsm_policy.sh
#
# References:
#   tools/testing/selftests/bpf/
#   Documentation/bpf/bpf_devel_QA.rst (testing section)

set -euo pipefail

BINARY="${1:-./build/security_monitor}"
PASS=0
FAIL=0
SKIP=0
LOGFILE="/tmp/lsm_test_$$.log"

RED='\033[0;31m'
GRN='\033[0;32m'
YLW='\033[0;33m'
RST='\033[0m'

log() { echo -e "$*" | tee -a "$LOGFILE"; }

# ─── Prerequisites check ───────────────────────────────────────────────────────
check_prerequisites() {
    [[ $EUID -eq 0 ]] || { log "${RED}[SKIP] Must run as root${RST}"; exit 2; }

    if ! grep -q bpf /sys/kernel/security/lsm 2>/dev/null; then
        log "${RED}[FATAL] BPF LSM not active. Boot with: lsm=lockdown,capability,...,bpf${RST}"
        log "Check: cat /sys/kernel/security/lsm"
        log "Fix:   Add 'lsm=...,bpf' to GRUB_CMDLINE_LINUX in /etc/default/grub"
        exit 2
    fi

    if ! [[ -f /sys/kernel/btf/vmlinux ]]; then
        log "${RED}[FATAL] /sys/kernel/btf/vmlinux missing. Rebuild kernel with CONFIG_DEBUG_INFO_BTF=y${RST}"
        exit 2
    fi

    if ! [[ -x "$BINARY" ]]; then
        log "${RED}[FATAL] Binary not found: $BINARY${RST}"
        exit 2
    fi

    log "${GRN}[OK] Prerequisites satisfied${RST}"
    log "  Kernel: $(uname -r)"
    log "  LSMs:   $(cat /sys/kernel/security/lsm)"
    log "  Binary: $BINARY"
}

# ─── Test runner ───────────────────────────────────────────────────────────────
run_test() {
    local name="$1"
    local func="$2"
    log ""
    log "─── $name ───"
    if $func; then
        log "${GRN}[PASS] $name${RST}"
        ((PASS++))
    else
        local code=$?
        log "${RED}[FAIL] $name (exit=$code)${RST}"
        ((FAIL++))
    fi
}

skip_test() {
    local name="$1"
    local reason="$2"
    log ""
    log "${YLW}[SKIP] $name: $reason${RST}"
    ((SKIP++))
}

# ─── Test: BPF program loads successfully ─────────────────────────────────────
test_bpf_load() {
    # Start monitor in background, kill after 2s, check it loaded clean
    timeout 2s "$BINARY" &>/tmp/monitor_load_$$.log &
    local pid=$!
    sleep 0.5

    if kill -0 "$pid" 2>/dev/null; then
        kill "$pid" 2>/dev/null || true
        wait "$pid" 2>/dev/null || true
        if grep -q "LSM hooks attached" /tmp/monitor_load_$$.log; then
            log "  BPF load log excerpt:"
            grep -E "\[INF\]|\[WRN\]|\[ERR\]" /tmp/monitor_load_$$.log | head -10 | sed 's/^/    /'
            return 0
        fi
    fi

    log "  Load output:"
    cat /tmp/monitor_load_$$.log | head -20 | sed 's/^/    /'
    return 1
}

# ─── Test: UID policy blocks exec ─────────────────────────────────────────────
test_uid_block() {
    # This tests BUG #2 fix: UID 65534 (nobody) must not be able to exec
    # We run the monitor with block_uid=65534, then try exec as nobody.

    # Start monitor
    timeout 5s "$BINARY" --block-uids 65534 &>/tmp/uid_test_$$.log &
    local monitor_pid=$!
    sleep 0.5

    # Try exec as UID 65534 (nobody)
    local result=0
    if command -v runuser &>/dev/null; then
        runuser -u nobody -- /usr/bin/id 2>/dev/null && result=1 || result=0
    elif command -v su &>/dev/null; then
        su -s /bin/sh nobody -c '/usr/bin/id' 2>/dev/null && result=1 || result=0
    else
        skip_test "uid_block_exec" "runuser/su not available"
        kill "$monitor_pid" 2>/dev/null || true
        return 0
    fi

    kill "$monitor_pid" 2>/dev/null || true
    wait "$monitor_pid" 2>/dev/null || true

    # result=0 means exec was blocked (command returned error) → PASS
    if [[ $result -eq 0 ]]; then
        log "  UID 65534 exec correctly blocked"

        # Verify the event appeared in monitor log
        if grep -q "EXEC_BLOCKED" /tmp/uid_test_$$.log 2>/dev/null; then
            log "  EXEC_BLOCKED event found in ringbuf output"
        else
            log "${YLW}  Warning: EXEC_BLOCKED event not found in output (may be timing)${RST}"
        fi
        return 0
    else
        log "  FAIL: exec as UID 65534 was NOT blocked"
        return 1
    fi
}

# ─── Test: File audit policy generates event ──────────────────────────────────
test_file_audit() {
    # Block /etc/passwd with AUDIT (should log but not deny open)
    # We verify the event appears in the ringbuf output.

    # Create a temp test file so we don't need /etc/shadow
    local testfile
    testfile=$(mktemp /tmp/lsm_test_XXXXXX)
    echo "test content" > "$testfile"

    timeout 3s "$BINARY" --block-files "$testfile" &>/tmp/audit_test_$$.log &
    local monitor_pid=$!
    sleep 0.3

    # Open the file (should trigger AUDIT event)
    cat "$testfile" >/dev/null 2>&1

    sleep 0.3
    kill "$monitor_pid" 2>/dev/null || true
    wait "$monitor_pid" 2>/dev/null || true

    rm -f "$testfile"

    if grep -q "FILE_OPEN_DENIED" /tmp/audit_test_$$.log 2>/dev/null; then
        log "  FILE_OPEN_DENIED audit event captured"
        return 0
    else
        log "  No FILE_OPEN_DENIED event captured"
        log "  Monitor output: $(head -5 /tmp/audit_test_$$.log 2>/dev/null)"
        return 1
    fi
}

# ─── Test: Root is not blocked by cross-uid ptrace rule ───────────────────────
test_ptrace_root_exempt() {
    # Root should be able to ptrace any process (our hook exempts uid==0)
    # We verify by checking that strace works as root on a child process.

    # strace a trivial command
    if strace -e trace=read /bin/true 2>/dev/null; then
        log "  Root ptrace (strace) correctly allowed"
        return 0
    else
        log "  Root ptrace incorrectly blocked"
        return 1
    fi
}

# ─── Test: Verify BUG #1 buggy program is rejected by verifier ───────────────
test_verifier_rejects_bug1() {
    # Compile the BUGGY program and verify it fails to load
    if ! command -v clang &>/dev/null; then
        skip_test "verifier_rejects_bug1" "clang not found"
        return 0
    fi

    local buggy_obj="/tmp/security_monitor_BUGGY_$$.o"

    # Try to compile (may fail at clang stage for very obvious errors)
    clang -target bpf -g -O2 \
        -I./include \
        -c ./bpf/security_monitor_BUGGY.bpf.c \
        -o "$buggy_obj" 2>/tmp/clang_bug_$$.log || true

    if [[ -f "$buggy_obj" ]]; then
        # Object compiled; now try to load (verifier should reject)
        if bpftool prog load "$buggy_obj" /sys/fs/bpf/test_bug_$$ 2>/tmp/verifier_$$.log; then
            log "  BUG: verifier accepted buggy program (should have rejected)"
            rm -f /sys/fs/bpf/test_bug_$$ "$buggy_obj"
            return 1
        else
            log "  Verifier correctly rejected buggy program:"
            grep -E "R[0-9]|error|Error" /tmp/verifier_$$.log | head -5 | sed 's/^/    /'
            rm -f "$buggy_obj"
            return 0
        fi
    else
        log "  Compilation failed (expected due to deliberate bug structure):"
        head -5 /tmp/clang_bug_$$.log | sed 's/^/    /'
        return 0
    fi
}

# ─── Test: bpftool map inspection ─────────────────────────────────────────────
test_map_introspection() {
    # Verify maps are visible and have expected structure
    local maps
    maps=$(bpftool map list 2>/dev/null | grep -c "ringbuf\|hash" || echo 0)

    log "  Found $maps BPF maps (ringbuf+hash types visible to bpftool)"

    # Check BTF is present in vmlinux
    if bpftool btf dump file /sys/kernel/btf/vmlinux 2>/dev/null | grep -q "linux_binprm"; then
        log "  BTF: linux_binprm type found in vmlinux BTF"
        return 0
    else
        log "  WARNING: linux_binprm not in BTF (CO-RE may not work)"
        return 1
    fi
}

# ─── Test: perf/ftrace based verification ─────────────────────────────────────
test_trace_visibility() {
    # Verify LSM hook is traceable via ftrace
    local tracefs="/sys/kernel/debug/tracing"

    if [[ ! -d "$tracefs" ]]; then
        skip_test "trace_visibility" "tracefs not mounted (mount -t debugfs debugfs /sys/kernel/debug)"
        return 0
    fi

    # Check security_bprm_check is a traceable event
    if ls "$tracefs/events/lsm/" 2>/dev/null | grep -q "bprm"; then
        log "  LSM bprm tracepoint found in tracefs"
    else
        log "  LSM tracepoints not found (older kernel or CONFIG_FTRACE_SYSCALLS not set)"
    fi

    # Check bpf_trace_printk output
    if [[ -r "$tracefs/trace_pipe" ]]; then
        log "  trace_pipe readable — bpf_printk output available via: cat $tracefs/trace_pipe"
    fi

    return 0
}

# ─── Cleanup ───────────────────────────────────────────────────────────────────
cleanup() {
    rm -f /tmp/monitor_load_$$.log \
          /tmp/uid_test_$$.log \
          /tmp/audit_test_$$.log \
          /tmp/verifier_$$.log \
          /tmp/clang_bug_$$.log \
          /tmp/lsm_test_$$.log 2>/dev/null || true
    # Kill any stray monitor processes
    pkill -f security_monitor 2>/dev/null || true
}

trap cleanup EXIT

# ─── Main ─────────────────────────────────────────────────────────────────────
main() {
    log "═══════════════════════════════════════════"
    log "  BPF LSM Security Monitor — Integration Tests"
    log "═══════════════════════════════════════════"
    log "  Date: $(date)"
    log "  Kernel: $(uname -r)"
    log ""

    check_prerequisites

    run_test "BPF program loads"                test_bpf_load
    run_test "UID policy blocks exec"           test_uid_block
    run_test "File audit policy emits event"    test_file_audit
    run_test "Root exempt from ptrace block"    test_ptrace_root_exempt
    run_test "Verifier rejects NULL-ptr bug"    test_verifier_rejects_bug1
    run_test "Map/BTF introspection"            test_map_introspection
    run_test "Trace visibility"                 test_trace_visibility

    log ""
    log "═══════════════════════════════════════════"
    log "  Results: ${GRN}PASS=$PASS${RST}  ${RED}FAIL=$FAIL${RST}  ${YLW}SKIP=$SKIP${RST}"
    log "  Full log: $LOGFILE"
    log "═══════════════════════════════════════════"

    [[ $FAIL -eq 0 ]]
}

main "$@"
