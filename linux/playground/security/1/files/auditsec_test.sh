#!/usr/bin/env bash
# auditsec_test.sh — test, debug, and troubleshoot the auditsec LSM module
#
# Run inside KVM test VM (never on host/production).
# Requires: root privileges, module already built (.ko present).
#
# Sections:
#   1. Module load/unload
#   2. Sysfs interface smoke tests
#   3. Functional tests (file_open, exec, socket hooks)
#   4. Bug-1 reproduction (NULL dereference trigger)
#   5. Bug-2 reproduction (inverted deny logic)
#   6. Kernel log capture (dmesg + ftrace)
#   7. kasan/UBSAN check
#   8. Performance overhead measurement
#   9. ftrace hook tracing
#  10. bpftrace one-liners
#
# References:
#   Documentation/admin-guide/dynamic-debug-howto.rst
#   Documentation/trace/ftrace.rst
#   Documentation/dev-tools/kasan.rst

set -euo pipefail
MODULE_DIR="$(cd "$(dirname "$0")/security" && pwd)"
MODULE_C="${MODULE_DIR}/auditsec.ko"
MODULE_F="${MODULE_DIR}/auditsec_fixed.ko"
SYSFS="/sys/kernel/auditsec"
DEBUGFS_TRACE="/sys/kernel/debug/tracing"
LOG_DIR="/tmp/auditsec_logs"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

log()  { echo -e "${GREEN}[+]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
fail() { echo -e "${RED}[FAIL]${NC} $*"; exit 1; }

mkdir -p "$LOG_DIR"

# =============================================================================
# 1. MODULE LOAD
# =============================================================================
section_load() {
    log "=== 1. Module load ==="

    # Ensure previous instance is gone
    if lsmod | grep -q auditsec; then
        warn "auditsec already loaded — removing"
        rmmod auditsec 2>/dev/null || true
    fi

    # Load the BUGGY version for demonstration
    [[ -f "$MODULE_C" ]] || fail "Build the module first: make"
    insmod "$MODULE_C" || fail "insmod failed — check dmesg"

    dmesg | tail -5
    lsmod | grep auditsec || fail "Module not in lsmod"
    log "Module loaded successfully"
}

# =============================================================================
# 2. SYSFS INTERFACE TESTS
# =============================================================================
section_sysfs() {
    log "=== 2. Sysfs interface ==="
    [[ -d "$SYSFS" ]] || fail "Sysfs node $SYSFS missing"

    # Read defaults
    enabled=$(cat "$SYSFS/enabled")
    log "enabled=$enabled  (expected: 1)"
    [[ "$enabled" == "1" ]] || warn "unexpected default"

    # Toggle modes
    echo 0 > "$SYSFS/enabled"; [[ $(cat "$SYSFS/enabled") == "0" ]] && log "disable: OK"
    echo 1 > "$SYSFS/enabled"; [[ $(cat "$SYSFS/enabled") == "1" ]] && log "log-only: OK"
    echo 2 > "$SYSFS/enabled"; [[ $(cat "$SYSFS/enabled") == "2" ]] && log "enforce: OK"
    echo 1 > "$SYSFS/enabled"  # restore

    # Stats readback
    cat "$SYSFS/stats"
    log "Sysfs tests passed"
}

# =============================================================================
# 3. FUNCTIONAL HOOK TESTS
# =============================================================================
section_hooks() {
    log "=== 3. Functional hook tests ==="

    dmesg -C  # clear ring buffer before test run

    # file_open hook
    log "Testing file_open hook..."
    cat /etc/hostname > /dev/null
    dmesg | grep -E "auditsec.*file_open.*hostname" && log "file_open hook: TRIGGERED"

    # bprm_check hook
    log "Testing bprm_check hook..."
    /bin/true
    dmesg | grep -E "auditsec.*bprm_check" && log "bprm_check hook: TRIGGERED"

    # socket_create hook
    log "Testing socket_create hook..."
    python3 -c "import socket; socket.socket(socket.AF_INET, socket.SOCK_STREAM)" 2>/dev/null
    dmesg | grep -E "auditsec.*sock_create" && log "socket_create hook: TRIGGERED"

    # inode_permission (write) hook
    log "Testing inode_permission hook (write)..."
    tmpfile=$(mktemp)
    echo "test" > "$tmpfile"
    dmesg | grep -E "auditsec.*inode_perm" && log "inode_perm hook: TRIGGERED"
    rm -f "$tmpfile"

    # task_kill hook
    log "Testing task_kill hook..."
    sleep 60 &
    SLEEP_PID=$!
    kill -0 $SLEEP_PID
    dmesg | grep -E "auditsec.*task_kill" && log "task_kill hook: TRIGGERED"
    kill $SLEEP_PID 2>/dev/null; wait $SLEEP_PID 2>/dev/null || true

    dmesg | grep auditsec | tee "$LOG_DIR/hooks_test.log"
    log "Functional tests complete — log: $LOG_DIR/hooks_test.log"
}

# =============================================================================
# 4. BUG-1 REPRODUCTION: NULL dereference in file_open
# =============================================================================
section_bug1() {
    log "=== 4. BUG-1 reproduction (NULL dentry) ==="
    warn "This WILL trigger a kernel NULL pointer dereference in the buggy module."
    warn "Run inside KVM with KASAN enabled (CONFIG_KASAN=y) to get a clean report."
    warn "Skipping auto-trigger — uncomment below line manually in KVM test VM."

    # Trigger: pipe() creates a file with NULL dentry
    # python3 -c "import os; r,w = os.pipe(); os.read(r,0)" &
    #
    # Expected oops with buggy module:
    #   BUG: kernel NULL pointer dereference, address: 0000000000000048
    #   RIP: 0010:dentry_path_raw+0x18/0x90
    #   Call Trace:
    #     auditsec_file_open+0x3c/0x80 [auditsec]
    #     security_file_open+0x2d/0x50
    #     do_dentry_open+0x1a3/0x3d0
    #
    # Fix verification:
    #   rmmod auditsec
    #   insmod auditsec_fixed.ko
    #   python3 -c "import os; r,w = os.pipe(); os.read(r,0)"  # no crash

    log "BUG-1 section: manual trigger required. See comments in script."
}

# =============================================================================
# 5. BUG-2 REPRODUCTION: Inverted deny logic
# =============================================================================
section_bug2() {
    log "=== 5. BUG-2 reproduction (inverted uid check) ==="

    # Create test user if not present
    id testuser1 &>/dev/null || useradd -m testuser1
    TEST_UID=$(id -u testuser1)

    # Set enforce mode, deny testuser1
    echo 2 > "$SYSFS/enabled"
    echo "$TEST_UID" > "$SYSFS/denied_uid"
    log "Set enforce mode, denied_uid=$TEST_UID"

    warn "BUGGY module behaviour:"
    warn "  root exec → DENIED  (wrong! root is not the denied uid)"
    warn "  testuser1 exec → ALLOWED (wrong! testuser1 should be denied)"

    # Test root exec (should work, but buggy module denies it)
    if su -c "ls /tmp > /dev/null 2>&1" root; then
        warn "root exec: ALLOWED (only works in fixed version)"
    else
        warn "root exec: DENIED (BUG-2 confirmed — buggy module)"
    fi

    # Test testuser1 exec (should be denied, but buggy module allows it)
    if su -c "ls /tmp > /dev/null 2>&1" testuser1; then
        warn "testuser1 exec: ALLOWED (BUG-2 confirmed — target uid NOT denied)"
    else
        log "testuser1 exec: DENIED (correct — fixed module behaviour)"
    fi

    echo 1 > "$SYSFS/enabled"   # restore log-only
    echo -1 > "$SYSFS/denied_uid"
    log "BUG-2 test complete. Reset to log-only mode."
}

# =============================================================================
# 6. FTRACE — trace LSM hook calls in real time
# =============================================================================
section_ftrace() {
    log "=== 6. ftrace hook tracing ==="
    [[ -d "$DEBUGFS_TRACE" ]] || { warn "debugfs not mounted — skipping ftrace"; return; }

    # Trace all auditsec_* functions using function_graph tracer
    # Reference: Documentation/trace/ftrace.rst
    echo 0 > "$DEBUGFS_TRACE/tracing_on"
    echo function_graph > "$DEBUGFS_TRACE/current_tracer"
    echo "auditsec_*" > "$DEBUGFS_TRACE/set_graph_function"
    echo 1 > "$DEBUGFS_TRACE/tracing_on"

    log "ftrace running. Triggering hooks..."
    cat /etc/hostname > /dev/null
    /bin/true
    sleep 0.1

    echo 0 > "$DEBUGFS_TRACE/tracing_on"
    head -50 "$DEBUGFS_TRACE/trace" | tee "$LOG_DIR/ftrace_output.txt"
    echo nop > "$DEBUGFS_TRACE/current_tracer"

    log "ftrace output saved to $LOG_DIR/ftrace_output.txt"
}

# =============================================================================
# 7. KASAN CHECK — detect memory errors
# =============================================================================
section_kasan() {
    log "=== 7. KASAN / UBSAN notes ==="
    log "For BUG-1 (NULL dereference), build test kernel with:"
    log "  CONFIG_KASAN=y"
    log "  CONFIG_KASAN_OUTLINE=y"
    log "  CONFIG_UBSAN=y"
    log "  CONFIG_UBSAN_SANITIZE_ALL=y"
    log ""
    log "KASAN will output a detailed report before the oops:"
    log "  =================================================================="
    log "  BUG: KASAN: null-ptr-deref in dentry_path_raw+0x18/0x90"
    log "  Read of size 8 at addr 0000000000000048 by task python3/1234"
    log "  =================================================================="
    log ""
    log "Build test kernel for KVM:"
    log "  make -C linux/ kvmconfig"
    log "  scripts/config --enable KASAN --enable KASAN_OUTLINE --enable UBSAN"
    log "  make -j\$(nproc)"
}

# =============================================================================
# 8. PERFORMANCE OVERHEAD
# =============================================================================
section_perf() {
    log "=== 8. Performance overhead measurement ==="
    which perf &>/dev/null || { warn "perf not installed — skipping"; return; }

    log "Measuring file open overhead with/without LSM..."

    # Baseline: count file opens per second
    perf stat -e "syscalls:sys_enter_openat" \
        -a sleep 2 2>&1 | tee "$LOG_DIR/perf_openat.txt"

    # Overhead via perf trace
    perf trace -e security:* --duration 2000 2>&1 | head -20 \
        | tee "$LOG_DIR/perf_security.txt" || true

    log "Perf output in $LOG_DIR/"
}

# =============================================================================
# 9. BPFTRACE ONE-LINERS
# =============================================================================
section_bpftrace() {
    log "=== 9. bpftrace one-liners ==="
    which bpftrace &>/dev/null || { warn "bpftrace not installed — skipping"; return; }

    log "Trace auditsec_file_open calls (5 seconds):"
    # kprobe on our function — works if module is loaded
    timeout 5 bpftrace -e '
        kprobe:auditsec_file_open {
            printf("[bpf] file_open pid=%d comm=%s\n",
                   pid, comm);
        }
    ' 2>/dev/null | head -20 || true

    log "Count LSM hook calls (3 seconds):"
    timeout 3 bpftrace -e '
        kprobe:security_file_open    { @opens  = count(); }
        kprobe:security_bprm_check   { @execs  = count(); }
        kprobe:security_socket_create{ @socks  = count(); }
        END { print(@opens); print(@execs); print(@socks); }
    ' 2>/dev/null || true
}

# =============================================================================
# 10. KGDB SETUP NOTES
# =============================================================================
section_kgdb() {
    log "=== 10. KGDB / GDB remote debug notes ==="
    cat <<'EOF'
  Prerequisites (KVM guest):
    CONFIG_KGDB=y, CONFIG_KGDB_SERIAL_CONSOLE=y, CONFIG_FRAME_POINTER=y
    CONFIG_DEBUG_INFO=y, CONFIG_GDB_SCRIPTS=y

  QEMU launch with serial GDB stub:
    qemu-system-x86_64 \
      -kernel arch/x86/boot/bzImage \
      -append "kgdboc=ttyS0,115200 kgdbwait nokaslr" \
      -serial tcp::1234,server,nowait \
      -nographic ...

  Host GDB session:
    $ gdb vmlinux
    (gdb) set architecture i386:x86-64
    (gdb) target remote :1234
    (gdb) add-symbol-file security/auditsec/auditsec.ko \
              $(grep -m1 text /sys/module/auditsec/sections/.text)
    (gdb) b auditsec_file_open
    (gdb) c

  Inspect task_struct:
    (gdb) p ((struct task_struct *)$current)->comm
    (gdb) p ((struct task_struct *)$current)->pid

  LSM hook list walk:
    (gdb) p security_hook_heads.file_open
EOF
}

# =============================================================================
# MAIN
# =============================================================================
case "${1:-all}" in
    load)     section_load ;;
    sysfs)    section_sysfs ;;
    hooks)    section_hooks ;;
    bug1)     section_bug1 ;;
    bug2)     section_bug2 ;;
    ftrace)   section_ftrace ;;
    kasan)    section_kasan ;;
    perf)     section_perf ;;
    bpftrace) section_bpftrace ;;
    kgdb)     section_kgdb ;;
    all)
        section_load
        section_sysfs
        section_hooks
        section_ftrace
        section_perf
        section_bpftrace
        ;;
    *)
        echo "Usage: $0 {all|load|sysfs|hooks|bug1|bug2|ftrace|kasan|perf|bpftrace|kgdb}"
        exit 1
        ;;
esac

log "Done. Logs in $LOG_DIR/"
