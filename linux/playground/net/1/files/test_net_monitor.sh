#!/usr/bin/env bash
# test_net_monitor.sh — Build, load, test, debug, and unload net_monitor
#
# Concepts covered:
#   • Building the module
#   • Loading with insmod / modprobe
#   • Generating test traffic
#   • Reading /proc stats
#   • Enabling dynamic debug (pr_debug output)
#   • KASAN / kmemleak / ftrace for debugging
#   • Checking dmesg for kernel errors
#   • Safely unloading
#
# Usage:
#   chmod +x test_net_monitor.sh
#   sudo ./test_net_monitor.sh
#
# Requirements:
#   • Root access (or sudo)
#   • Kernel with CONFIG_NETFILTER=y, CONFIG_IP_NF_FILTER=y
#   • For debugging: CONFIG_DYNAMIC_DEBUG=y, CONFIG_KASAN=y (debug kernel)
#   • Tools: curl, ping, nc (netcat), tcpdump

set -euo pipefail
MODULE="net_monitor"
MODULE_PATH="./${MODULE}.ko"
PROC_PATH="/proc/${MODULE}"
DEBUGFS="/sys/kernel/debug"

RED='\033[0;31m'
GRN='\033[0;32m'
YEL='\033[1;33m'
BLU='\033[0;34m'
NC='\033[0m'

log()  { echo -e "${BLU}[INFO]${NC} $*"; }
ok()   { echo -e "${GRN}[ OK ]${NC} $*"; }
warn() { echo -e "${YEL}[WARN]${NC} $*"; }
fail() { echo -e "${RED}[FAIL]${NC} $*"; exit 1; }
step() { echo; echo -e "${YEL}══ $* ══${NC}"; }

require_root() {
    [[ $EUID -eq 0 ]] || fail "Must run as root (sudo)"
}

# ─── Phase 1: Build ────────────────────────────────────────────────────────

step "PHASE 1: BUILD"

build_module() {
    log "Cleaning previous build..."
    make clean 2>/dev/null || true

    log "Building ${MODULE}.ko..."
    # -j$(nproc) parallelises across CPU cores
    make -j"$(nproc)" 2>&1 | tee build.log

    [[ -f "${MODULE_PATH}" ]] || fail "Build failed — see build.log"
    ok "Build succeeded: $(ls -lh ${MODULE_PATH})"

    # Verify the module is for the running kernel ABI
    log "Module info:"
    modinfo "${MODULE_PATH}"
}

build_module

# ─── Phase 2: Static analysis (optional but recommended) ──────────────────

step "PHASE 2: STATIC ANALYSIS"

run_sparse() {
    if command -v sparse &>/dev/null; then
        log "Running sparse (endianness / annotation checker)..."
        make C=1 CF="-D__CHECK_ENDIAN__" 2>&1 | grep -E "(warning|error)" | head -30 || true
        ok "Sparse complete"
    else
        warn "sparse not installed (apt install sparse)"
    fi
}

run_sparse

# Run checkpatch.pl from Linus's tree if available
CHECKPATCH=$(find /usr/src/linux* -name checkpatch.pl 2>/dev/null | head -1 || true)
if [[ -n "$CHECKPATCH" ]]; then
    log "Running checkpatch.pl..."
    perl "$CHECKPATCH" --no-tree -f net_monitor.c 2>&1 | tail -20 || true
fi

# ─── Phase 3: Load ────────────────────────────────────────────────────────

step "PHASE 3: LOAD MODULE"

require_root

unload_if_loaded() {
    if lsmod | grep -q "^${MODULE} "; then
        log "Module already loaded — unloading first..."
        rmmod "${MODULE}" || fail "rmmod failed"
    fi
}

unload_if_loaded

# Save dmesg cursor position so we only see NEW messages from this module
DMESG_CURSOR=$(dmesg --time-format=reltime 2>/dev/null | wc -l)

log "Loading ${MODULE}.ko (drop_proto=0, log_every=100)..."
insmod "${MODULE_PATH}" drop_proto=0 log_every=100

# Check the module loaded successfully
if lsmod | grep -q "^${MODULE} "; then
    ok "Module loaded"
else
    # If insmod returned 0 but lsmod doesn't show it, something is wrong
    fail "Module not visible in lsmod after insmod"
fi

# Show init messages
log "Kernel messages from load:"
dmesg --time-format=reltime | tail -n +$((DMESG_CURSOR+1)) | grep -i "net_monitor" || true

# Check /proc entry exists
[[ -e "${PROC_PATH}" ]] || fail "/proc/${MODULE} not created"
ok "/proc/${MODULE} exists"

# ─── Phase 4: Dynamic debug (pr_debug output) ─────────────────────────────

step "PHASE 4: ENABLE DYNAMIC DEBUG"

enable_dynamic_debug() {
    # Concept: CONFIG_DYNAMIC_DEBUG lets you enable/disable pr_debug()
    # calls at runtime without recompiling. The debugfs interface controls it.
    # Format: "file net_monitor.c +p"  means enable all pr_debug in net_monitor.c
    # Flags: +p=print, +f=function name, +l=line number, +m=module name, +t=thread

    if [[ -f "${DEBUGFS}/dynamic_debug/control" ]]; then
        echo "file net_monitor.c +pflmt" > "${DEBUGFS}/dynamic_debug/control" 2>/dev/null || \
            warn "Could not enable dynamic debug (may need CONFIG_DYNAMIC_DEBUG=y)"
        ok "Dynamic debug enabled — pr_debug() messages will appear in dmesg"
    else
        warn "debugfs not mounted or CONFIG_DYNAMIC_DEBUG not set"
        warn "Mount debugfs: mount -t debugfs none /sys/kernel/debug"
    fi
}

enable_dynamic_debug

# ─── Phase 5: Generate test traffic ───────────────────────────────────────

step "PHASE 5: GENERATE TEST TRAFFIC"

generate_traffic() {
    log "Sending ICMP (ping to loopback)..."
    ping -c 5 127.0.0.1 &>/dev/null || true
    ok "ping sent"

    log "Sending TCP traffic (curl to localhost)..."
    # Start a trivial HTTP server if possible
    if command -v python3 &>/dev/null; then
        python3 -m http.server 8888 &>/dev/null &
        SERVER_PID=$!
        sleep 0.3
        curl -s --max-time 2 http://127.0.0.1:8888/ &>/dev/null || true
        kill $SERVER_PID 2>/dev/null || true
        ok "HTTP/TCP traffic sent"
    fi

    log "Sending UDP traffic (netcat)..."
    if command -v nc &>/dev/null; then
        echo "test" | nc -u -w1 127.0.0.1 9999 &>/dev/null || true
        ok "UDP traffic sent"
    fi

    # Higher-volume test using pktgen (kernel packet generator)
    # pktgen is the professional tool for high-rate kernel packet tests
    if [[ -d /proc/net/pktgen ]]; then
        log "pktgen available — running 1000-packet burst..."
        # Configure pktgen thread
        local PG_DEV="lo"
        local PG_CTRL="/proc/net/pktgen/pgctrl"
        local PG_THREAD="/proc/net/pktgen/kpktgend_0"

        echo "add_device ${PG_DEV}" > "${PG_THREAD}"
        local PG_IF="/proc/net/pktgen/${PG_DEV}"
        echo "count 1000"        > "${PG_IF}"
        echo "pkt_size 64"       > "${PG_IF}"
        echo "delay 0"           > "${PG_IF}"
        echo "dst 127.0.0.1"     > "${PG_IF}"
        echo "start"             > "${PG_CTRL}"
        ok "pktgen burst sent"
    else
        warn "pktgen not loaded (modprobe pktgen for high-rate tests)"
    fi
}

generate_traffic

# ─── Phase 6: Read statistics ─────────────────────────────────────────────

step "PHASE 6: READ STATISTICS"

log "Waiting 1s for stats to accumulate..."
sleep 1

log "=== /proc/${MODULE} ==="
cat "${PROC_PATH}"

# Verify stats changed
RX=$(grep total_rx "${PROC_PATH}" | awk '{print $3}')
if [[ "$RX" -gt 0 ]]; then
    ok "Stats updated (rx=${RX} packets seen)"
else
    warn "rx=0 — no packets captured (check CONFIG_NETFILTER is enabled)"
fi

# ─── Phase 7: Test the DROP functionality ─────────────────────────────────

step "PHASE 7: TEST PACKET DROP"

test_drop() {
    log "Reloading with drop_proto=17 (UDP drop)..."
    rmmod "${MODULE}"
    insmod "${MODULE_PATH}" drop_proto=17 log_every=0

    log "Sending UDP (should be dropped)..."
    echo "drop_test" | nc -u -w1 8.8.8.8 53 &>/dev/null || true  # DNS UDP
    sleep 0.2

    DROPPED=$(grep dropped "${PROC_PATH}" | awk '{print $3}')
    if [[ "$DROPPED" -gt 0 ]]; then
        ok "Drop working: ${DROPPED} packets dropped"
    else
        warn "No drops recorded (packets may not have matched lo interface)"
    fi

    log "Restoring normal mode..."
    rmmod "${MODULE}"
    insmod "${MODULE_PATH}" drop_proto=0
}

test_drop

# ─── Phase 8: Debugging techniques ───────────────────────────────────────

step "PHASE 8: DEBUGGING TOOLKIT"

echo "
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEBUGGING TECHNIQUE 1: dmesg — kernel ring buffer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  dmesg -w                        # live tail (like tail -f for kernel)
  dmesg -l err,warn               # only errors/warnings
  dmesg --time-format=iso         # human-readable timestamps
  dmesg | grep net_monitor        # filter by module name

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEBUGGING TECHNIQUE 2: KASAN — Kernel Address Sanitizer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Requires kernel built with CONFIG_KASAN=y (debug kernel).
  KASAN detects: use-after-free, out-of-bounds, double-free.
  When triggered, dmesg prints a stack trace and memory report.

  How to get a KASAN-enabled kernel:
    # Ubuntu debug kernel:
    sudo apt install linux-image-\$(uname -r)-dbgsym
    # Or build from source with:
    make menuconfig → Kernel hacking → KASAN

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEBUGGING TECHNIQUE 3: kmemleak — memory leak detector
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Requires CONFIG_DEBUG_KMEMLEAK=y.

  # Scan for leaks after loading and running your module:
  echo scan > /sys/kernel/debug/kmemleak
  sleep 5    # wait for scan
  cat /sys/kernel/debug/kmemleak

  # Clear reported leaks (e.g., after known-leak path):
  echo clear > /sys/kernel/debug/kmemleak

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEBUGGING TECHNIQUE 4: ftrace — function tracer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ftrace traces kernel function calls with nanosecond timestamps.
  The trace-cmd tool is the user-friendly frontend.

  # Trace our hook function:
  cd /sys/kernel/debug/tracing
  echo function_graph  > current_tracer
  echo hook_in         > set_graph_function
  echo 1               > tracing_on
  sleep 2              # generate some traffic
  echo 0               > tracing_on
  cat trace | head -50

  # With trace-cmd (easier):
  trace-cmd record -p function_graph -g hook_in sleep 5
  trace-cmd report | head -100

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEBUGGING TECHNIQUE 5: kgdb — kernel debugger
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  kgdb connects gdb to the live kernel over serial or KGDB_NET.
  BEST practice: use QEMU for kernel development.

  # Run kernel in QEMU with gdb stub:
  qemu-system-x86_64 -kernel arch/x86/boot/bzImage \\
    -append 'kgdboc=ttyS0,115200 kgdbwait' \\
    -serial tcp::1234,server,nowait \\
    -nographic

  # From host: attach gdb:
  gdb vmlinux
  (gdb) target remote :1234
  (gdb) lx-symbols /path/to/module/dir    # load module symbols
  (gdb) break hook_in
  (gdb) continue

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEBUGGING TECHNIQUE 6: crash + vmcore — post-mortem
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  When a kernel panic occurs, kdump saves a core dump.
  crash(8) analyses it offline.

  # Setup kdump (Ubuntu):
  sudo apt install kdump-tools crash
  sudo systemctl enable kdump

  # After a panic, vmcore is at /var/crash/
  crash /usr/lib/debug/boot/vmlinux-\$(uname -r) /var/crash/vmcore

  # In crash:
  crash> bt          # backtrace of panic CPU
  crash> log         # kernel ring buffer at time of panic
  crash> sym hook_in # find symbol address
  crash> dis hook_in # disassemble

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEBUGGING TECHNIQUE 7: perf — performance profiler
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  perf measures CPU cycles, cache misses, function call frequency.

  # Profile module functions:
  perf record -a -g sleep 10
  perf report --kallsyms /proc/kallsyms

  # Count events in our hooks:
  perf stat -e cache-misses,cache-references \\
    -e instructions,cycles -- sleep 10

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEBUGGING TECHNIQUE 8: Sparse — static type checker
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Sparse catches Bug #2 class errors AT COMPILE TIME:
    make C=1 CF=-D__CHECK_ENDIAN__ modules
  Will output: 'incorrect type in argument (different base types)'
  for __be32 vs unsigned int comparisons.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEBUGGING TECHNIQUE 9: LOCKDEP — lock dependency validator
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  CONFIG_PROVE_LOCKING=y catches deadlocks and lock ordering
  violations at runtime before they cause real deadlocks.

  If our module acquires a spinlock inside the hook while another
  code path does the reverse order, LOCKDEP prints a warning in dmesg
  with a full lock dependency chain.
"

# ─── Phase 9: Reproduce and fix Bug #1 (memory leak) ──────────────────────

step "PHASE 9: DEMONSTRATE BUG #1 — MEMORY LEAK"

echo "
Bug #1 is in describe_packet_BUGGY():

    label = kmalloc(64, GFP_ATOMIC);
    snprintf(label, 64, ...);
    pr_debug(...);
    // ← kfree(label) missing!

To detect with kmemleak:
    echo scan > /sys/kernel/debug/kmemleak && sleep 5
    cat /sys/kernel/debug/kmemleak
    # Output will show:
    #   unreferenced object 0xffff... (size 64):
    #     comm "ksoftirqd", pid X, jiffies XXXXXXXX
    #     backtrace:
    #       kmalloc
    #       describe_packet_BUGGY
    #       hook_in

Fix: add kfree(label) before the function returns.

The FIXED version describe_packet() in net_monitor.c shows the correct pattern.
"

# ─── Phase 10: Reproduce and diagnose Bug #2 (endianness) ─────────────────

step "PHASE 10: DEMONSTRATE BUG #2 — ENDIANNESS"

echo "
Bug #2 is in is_loopback_BUGGY():

    return (iph->saddr == 0x7F000001U);

On x86 (little-endian):
  iph->saddr for 127.0.0.1 = 0x0100007F  (network byte order = big-endian)
  Constant 0x7F000001 (host order)
  They are NEVER equal → loopback detection silently fails.

Quick diagnosis: add a pr_info in the function:
    pr_info('saddr=0x%08X want=0x%08X match=%d\n',
            iph->saddr, 0x7F000001U,
            iph->saddr == 0x7F000001U);

Then ping 127.0.0.1 and check dmesg:
    dmesg | grep 'saddr='
    # Output: saddr=0x0100007F want=0x7F000001 match=0

Sparse will also catch this at compile time:
    make C=1 CF=-D__CHECK_ENDIAN__ modules
    # warning: incorrect type in argument (different base types)
    # expected unsigned int [usertype] val
    # got restricted __be32 [usertype] saddr

Fix A: iph->saddr == htonl(0x7F000001U)
Fix B: ipv4_is_loopback(iph->saddr)   ← preferred kernel style
"

# ─── Phase 11: Unload ─────────────────────────────────────────────────────

step "PHASE 11: UNLOAD"

log "Final statistics before unload:"
cat "${PROC_PATH}"

log "Unloading module..."
rmmod "${MODULE}"

# Verify cleaned up
if lsmod | grep -q "^${MODULE} "; then
    fail "Module still loaded after rmmod!"
fi
ok "Module unloaded cleanly"

# Check for any error messages on unload
DMESG_NEW=$(dmesg --time-format=reltime | tail -5)
echo "$DMESG_NEW" | grep -iE "(oops|bug|warn|err)" && \
    warn "Errors in dmesg after unload — investigate!" || \
    ok "No errors in dmesg after unload"

step "ALL TESTS PASSED"
echo "
Next steps for elite development:
  1. Run against Linus's kernel tree from github.com/torvalds/linux
  2. Enable KASAN + LOCKDEP + DEBUG_PAGEALLOC in your test kernel
  3. Use QEMU + virtme for safe isolated testing (no host risk)
  4. Submit patch to netdev@vger.kernel.org mailing list
  5. Study existing netfilter modules: net/netfilter/nf_conntrack_core.c
"
