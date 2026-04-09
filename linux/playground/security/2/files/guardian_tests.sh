#!/bin/bash
# guardian_tests.sh
# Systematic test suite for the Guardian LSM.
# Each test follows: ARRANGE → ACT → ASSERT pattern.
#
# Also includes: kernel panic analysis, KASAN output interpretation,
# and common troubleshooting scenarios.

PASS=0
FAIL=0
SKIP=0

pass() { echo "  [PASS] $1"; ((PASS++)); }
fail() { echo "  [FAIL] $1"; ((FAIL++)); }
skip() { echo "  [SKIP] $1"; ((SKIP++)); }

require_root() {
    [ "$(id -u)" -eq 0 ] || { echo "ERROR: Must run as root"; exit 1; }
}

require_module() {
    lsmod | grep -q guardian_lsm || { echo "ERROR: guardian_lsm not loaded"; exit 1; }
}

require_root
require_module

# ─────────────────────────────────────────────────────────────────────────────
# TEST SUITE
# ─────────────────────────────────────────────────────────────────────────────

echo "============================================================"
echo " Guardian LSM Test Suite"
echo "============================================================"

echo ""
echo "── Test Group 1: Module State ──"

# T1.1: Module loaded
lsmod | grep -q guardian_lsm && pass "T1.1: module is loaded" || fail "T1.1: module not loaded"

# T1.2: securityfs entry exists
[ -f /sys/kernel/security/guardian/enabled ] && \
    pass "T1.2: securityfs /enabled file exists" || \
    fail "T1.2: securityfs entry missing"

# T1.3: Default enforcement state = enabled (1)
STATE=$(cat /sys/kernel/security/guardian/enabled 2>/dev/null)
[ "${STATE}" = "1" ] && pass "T1.3: default enforcement = 1" || fail "T1.3: expected 1, got '${STATE}'"

echo ""
echo "── Test Group 2: file_open hook ──"

# T2.1: Opening a file produces a log entry
dmesg --clear
cat /etc/hostname >/dev/null
sleep 0.1
dmesg | grep -q "guardian: file_open" && \
    pass "T2.1: file_open hook fires on file access" || \
    fail "T2.1: no log from file_open hook"

# T2.2: file_open does not block legitimate access
cat /etc/hostname >/dev/null 2>&1 && \
    pass "T2.2: file_open does not block access" || \
    fail "T2.2: file_open incorrectly blocked access"

echo ""
echo "── Test Group 3: inode_create hook ──"

# T3.1: Non-root cannot create files in /tmp
su -s /bin/sh nobody -c "touch /tmp/guardian_test_nonroot_$$" 2>/dev/null && {
    rm -f /tmp/guardian_test_nonroot_$$
    fail "T3.1: non-root SHOULD be blocked in /tmp"
} || pass "T3.1: non-root correctly blocked in /tmp"

# T3.2: Root CAN create files in /tmp
touch /tmp/guardian_test_root_$$ 2>/dev/null && {
    rm -f /tmp/guardian_test_root_$$
    pass "T3.2: root can create files in /tmp"
} || fail "T3.2: root incorrectly blocked in /tmp"

# T3.3: Non-root CAN create in home directory (not in /tmp)
TMPDIR=$(mktemp -d /home/nobody/guardian_test.XXXXXX 2>/dev/null || mktemp -d /var/tmp/guardian_test.XXXXXX)
su -s /bin/sh nobody -c "touch ${TMPDIR}/test" 2>/dev/null && {
    pass "T3.3: non-root can create files outside /tmp"
} || skip "T3.3: could not test (nobody home dir not accessible)"
rm -rf "${TMPDIR}"

# T3.4: Blocked attempt appears in dmesg
dmesg --clear
su -s /bin/sh nobody -c "touch /tmp/guardian_block_test_$$" 2>/dev/null || true
sleep 0.1
dmesg | grep -q "guardian: BLOCKED" && \
    pass "T3.4: blocked attempt logged to dmesg" || \
    fail "T3.4: no BLOCKED log found"

echo ""
echo "── Test Group 4: Enforcement toggle ──"

# T4.1: Can disable enforcement
echo 0 > /sys/kernel/security/guardian/enabled
STATE=$(cat /sys/kernel/security/guardian/enabled)
[ "${STATE}" = "0" ] && pass "T4.1: can disable enforcement" || fail "T4.1: disable failed"

# T4.2: Non-root allowed when enforcement disabled
su -s /bin/sh nobody -c "touch /tmp/guardian_disabled_$$" 2>/dev/null && {
    rm -f /tmp/guardian_disabled_$$
    pass "T4.2: non-root allowed when enforcement=0"
} || fail "T4.2: non-root still blocked when enforcement=0"

# T4.3: Re-enable works
echo 1 > /sys/kernel/security/guardian/enabled
STATE=$(cat /sys/kernel/security/guardian/enabled)
[ "${STATE}" = "1" ] && pass "T4.3: re-enable enforcement works" || fail "T4.3: re-enable failed"

# T4.4: Policy re-enforced after re-enable
su -s /bin/sh nobody -c "touch /tmp/guardian_reenable_$$" 2>/dev/null && {
    rm -f /tmp/guardian_reenable_$$
    fail "T4.4: should be blocked after re-enable"
} || pass "T4.4: policy re-enforced after re-enable"

echo ""
echo "────────────────────────────────────────────────────────────"
printf " Results: %d passed, %d failed, %d skipped\n" "${PASS}" "${FAIL}" "${SKIP}"
echo "────────────────────────────────────────────────────────────"

# ─────────────────────────────────────────────────────────────────────────────
# TROUBLESHOOTING GUIDE
# ─────────────────────────────────────────────────────────────────────────────

cat <<'TROUBLESHOOTING'

============================================================
 TROUBLESHOOTING GUIDE
============================================================

PROBLEM: insmod fails with "Operation not permitted"
  CAUSE:  Secure Boot is enabled. The kernel requires signed modules.
  FIX:    Either disable Secure Boot in BIOS/UEFI, or sign the module:
            openssl req -new -x509 -newkey rsa:2048 -keyout signing_key.pem \
                        -out signing_cert.pem -days 365 -subj "/CN=Guardian LSM/"
            /lib/modules/$(uname -r)/build/scripts/sign-file sha256 \
                signing_key.pem signing_cert.pem guardian_lsm.ko
          Then insmod again.

PROBLEM: insmod fails with "Unknown symbol in module"
  CAUSE:  Your module calls a kernel function that is not exported.
  FIX:    Check which functions are exported:
            grep EXPORT_SYMBOL /lib/modules/$(uname -r)/build/Module.symvers | grep symbol_name
          If the function exists but is not exported, you may need to:
            - Add EXPORT_SYMBOL_GPL(function_name) to the kernel source (requires recompile)
            - OR find an alternative exported function.

PROBLEM: Module loads but hooks don't fire
  CAUSE 1: LSM stacking order — your LSM might be registered AFTER a denying LSM.
  CHECK:   cat /proc/security/lsm
           cat /sys/kernel/security/lsm
  FIX:     Adjust CONFIG_LSM in kernel config to list "guardian" before blocking LSMs.
           Or change your module's .order to LSM_ORDER_FIRST.

  CAUSE 2: security_add_hooks() not called (check your init function ran).
  CHECK:   dmesg | grep "guardian: LSM initialized"
  FIX:     Add pr_err() calls to every failure path in guardian_init().

PROBLEM: Kernel oops / panic after loading
  READ the oops: dmesg will show:
    BUG: kernel NULL pointer dereference, address: 0000000000000000
    RIP: 0010:guardian_file_open+0x2a/0x80  ← exact function + offset
    Call Trace:
      security_file_open
      do_open
      path_openat
      ...
  INTERPRET:
    - "NULL pointer dereference" = you dereferenced a NULL pointer
    - RIP = exact instruction (offset 0x2a into guardian_file_open)
    - To find which C line corresponds to offset 0x2a:
        addr2line -e guardian_lsm.ko 0x2a
        OR: objdump -d guardian_lsm.ko | grep -A5 "2a:"

PROBLEM: KASAN (Kernel Address Sanitizer) report
  OUTPUT LOOKS LIKE:
    BUG: KASAN: stack-out-of-bounds in guardian_file_open+0x4a
    Write of size 1 at addr ffff888... by task bash/1234
  MEANING: You wrote out of bounds of a stack or heap buffer.
  FIX:     Find the line with addr2line, check your buffer sizes.

PROBLEM: "sleeping function called from invalid context"
  CAUSE:   You called a function that can sleep (kmalloc with GFP_KERNEL,
           mutex_lock, etc.) from an atomic context (inside spinlock, 
           interrupt handler, or with preemption disabled).
  FIX:     In atomic contexts, use GFP_ATOMIC for allocations (never sleeps,
           but can fail). Or restructure to avoid sleeping in that context.

PROBLEM: Module cannot be unloaded (rmmod fails with "Resource busy")
  CAUSE:  Something is still using the module (open file descriptor, etc.)
          OR the module has no module_exit() function.
  FIX:    Check: cat /proc/modules | grep guardian (shows use count)
          Ensure you have module_exit(guardian_exit) at the bottom.
          In Rust: ensure your struct's Drop implementation is complete.

TOOLS SUMMARY:
  dmesg -T          — kernel messages with timestamps
  /proc/kallsyms    — all kernel symbols (check your hooks are there)
  /proc/modules     — loaded modules and use counts
  /proc/security/lsm — active LSM order
  /sys/kernel/debug/tracing — ftrace interface
  /sys/kernel/debug/dynamic_debug/control — enable pr_debug
  gdb vmlinux + QEMU -s -S — full kernel debugger
  make C=2          — sparse static analysis
  KASAN             — runtime memory error detection
  syzkaller         — coverage-guided kernel fuzzer

TROUBLESHOOTING
