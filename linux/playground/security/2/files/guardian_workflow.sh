#!/bin/bash
# guardian_workflow.sh
# Complete build → load → test → debug workflow for the Guardian LSM.
# Run inside a QEMU virtual machine or a disposable test system.
# NEVER run on a production machine — loading untested kernel code can crash it.
#
# Sections:
#   1. Build the module
#   2. Pre-load checks
#   3. Load the module
#   4. Functional tests
#   5. Debugging techniques
#   6. Unload and cleanup

set -e  # exit immediately if any command fails
set -u  # treat undefined variables as errors

echo "============================================================"
echo " Guardian LSM — Build, Load, Test, Debug Workflow"
echo "============================================================"

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: BUILD
# ─────────────────────────────────────────────────────────────────────────────

echo ""
echo "── SECTION 1: Building the module ──"

# Kernel version we're building for
KVER=$(uname -r)
echo "Kernel version: ${KVER}"
echo "Build dir:      /lib/modules/${KVER}/build"

# Verify the kernel headers are installed
if [ ! -d "/lib/modules/${KVER}/build" ]; then
    echo "ERROR: Kernel headers not found."
    echo "Install with: apt install linux-headers-${KVER}"
    exit 1
fi

# Build the module
# -j$(nproc): use all available CPU cores
make -j"$(nproc)"

echo "Build complete. Module file:"
ls -lh guardian_lsm.ko

# Inspect the module object: nm lists all symbols
echo ""
echo "── Module symbols (nm output) ──"
nm guardian_lsm.ko | grep -E "(guardian|security_add_hooks)" | head -20

# Check modinfo: shows metadata without loading the module
echo ""
echo "── Module metadata (modinfo) ──"
modinfo guardian_lsm.ko

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: PRE-LOAD CHECKS
# ─────────────────────────────────────────────────────────────────────────────

echo ""
echo "── SECTION 2: Pre-load checks ──"

# checkpatch.pl: mandatory kernel coding style checker.
# Checks line length (max 100), whitespace, comment style, error handling.
# EVERY patch submitted upstream must pass this with 0 errors.
echo "Running checkpatch.pl..."
/lib/modules/"${KVER}"/build/scripts/checkpatch.pl --no-tree -f guardian_lsm.c || true

# modprobe --dry-run: simulate loading without actually loading
# This checks that all symbols the module requires are present in the kernel
echo "Running modprobe dry-run (dependency check)..."
modprobe --dry-run --verbose ./guardian_lsm.ko 2>&1 || true

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: LOAD THE MODULE
# ─────────────────────────────────────────────────────────────────────────────

echo ""
echo "── SECTION 3: Loading the module ──"

# Clear the kernel ring buffer so we can see fresh messages
dmesg --clear

# insmod: directly load a .ko file by path.
# modprobe: loads from /lib/modules/ by name, handles dependencies.
# Use insmod during development (direct path control).
# Use modprobe in production (handles dep resolution).
insmod ./guardian_lsm.ko

echo "Module loaded. Checking dmesg..."
sleep 0.2
dmesg | grep guardian | tail -20

# Verify the module appears in the loaded modules list
echo ""
echo "── Loaded modules containing 'guardian' ──"
lsmod | grep guardian

# Verify hooks registered: /proc/security/lsm lists active LSMs
echo ""
echo "── Active LSMs ──"
cat /proc/security/lsm 2>/dev/null || cat /sys/kernel/security/lsm 2>/dev/null || echo "(not available)"

# Verify securityfs entry was created
echo ""
echo "── securityfs entries ──"
ls -la /sys/kernel/security/guardian/ 2>/dev/null || echo "securityfs not mounted?"

# If not mounted, mount it:
# mount -t securityfs securityfs /sys/kernel/security

echo ""
echo "── Current enforcement state ──"
cat /sys/kernel/security/guardian/enabled

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4: FUNCTIONAL TESTS
# ─────────────────────────────────────────────────────────────────────────────

echo ""
echo "── SECTION 4: Functional tests ──"

# Test 1: file_open hook fires on file access
echo "Test 1: file_open hook"
dmesg --clear
cat /etc/hostname >/dev/null
sleep 0.1
echo "  Expected: guardian: file_open message in dmesg"
dmesg | grep "guardian: file_open" | tail -3

# Test 2: inode_create hook blocks non-root in /tmp
echo ""
echo "Test 2: inode_create block in /tmp"
dmesg --clear
# Run as nobody (non-privileged user)
su -s /bin/sh nobody -c "touch /tmp/guardian_test_file" 2>&1 && \
    echo "  FAIL: file creation should have been blocked!" || \
    echo "  PASS: file creation correctly blocked (got EPERM)"
dmesg | grep "guardian: BLOCKED" | tail -3

# Test 3: root can still create in /tmp
echo ""
echo "Test 3: root creation in /tmp (should succeed)"
touch /tmp/guardian_root_test && echo "  PASS: root can create files" || echo "  FAIL"
rm -f /tmp/guardian_root_test

# Test 4: disable enforcement via securityfs
echo ""
echo "Test 4: disable enforcement"
echo 0 > /sys/kernel/security/guardian/enabled
cat /sys/kernel/security/guardian/enabled
# Now non-root should be allowed
su -s /bin/sh nobody -c "touch /tmp/guardian_disabled_test" 2>&1 && \
    echo "  PASS: enforcement disabled, creation allowed" || \
    echo "  FAIL: should be allowed when disabled"
rm -f /tmp/guardian_disabled_test

# Re-enable
echo 1 > /sys/kernel/security/guardian/enabled
echo "  Enforcement re-enabled"

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5: DEBUGGING TECHNIQUES
# ─────────────────────────────────────────────────────────────────────────────

echo ""
echo "── SECTION 5: Debugging techniques ──"

echo ""
echo "5a. dmesg with timestamps"
dmesg -T | grep guardian | tail -10

echo ""
echo "5b. Dynamic debug — enable pr_debug() output at runtime"
# pr_debug() calls are compiled in but disabled by default.
# You can enable them for specific files/functions WITHOUT rebuilding.
echo "guardian_lsm guardian_file_open +p" > /sys/kernel/debug/dynamic_debug/control 2>/dev/null \
    && echo "  pr_debug enabled for guardian_file_open" \
    || echo "  (dynamic_debug requires CONFIG_DYNAMIC_DEBUG=y)"

echo ""
echo "5c. ftrace — trace specific kernel functions"
# ftrace is the kernel's built-in function tracer.
# Concept: ftrace instruments function entry/exit points.
# It writes call events to a ring buffer you can read at any time.
FTRACE=/sys/kernel/debug/tracing
if [ -d "${FTRACE}" ]; then
    # Enable function tracing for our hook
    echo guardian_file_open_rust > "${FTRACE}/set_ftrace_filter" 2>/dev/null || true
    echo function > "${FTRACE}/current_tracer"
    echo 1 > "${FTRACE}/tracing_on"
    # Trigger a file open
    cat /etc/hostname >/dev/null
    echo 0 > "${FTRACE}/tracing_on"
    echo "  ftrace output (last 5 lines):"
    tail -5 "${FTRACE}/trace" | sed 's/^/    /'
    # Reset
    echo nop > "${FTRACE}/current_tracer"
    echo > "${FTRACE}/set_ftrace_filter"
else
    echo "  (ftrace not available — needs CONFIG_FTRACE=y and debugfs mounted)"
fi

echo ""
echo "5d. /proc/kallsyms — verify your symbols are in the kernel"
# kallsyms: a file that lists ALL kernel symbols (functions + global vars).
# If your module loaded, its exported functions appear here.
grep guardian /proc/kallsyms | head -10

echo ""
echo "5e. GDB over QEMU (run this from the HOST, not the guest)"
cat <<'GDB_INSTRUCTIONS'
  # On the host machine (not inside QEMU):
  gdb vmlinux
  (gdb) target remote :1234          # Connect to QEMU gdbserver
  (gdb) hbreak guardian_file_open    # Hardware breakpoint (survives module reload)
  (gdb) continue
  # In QEMU guest: cat /etc/hostname
  # GDB will stop at guardian_file_open, showing:
  #   - file->f_path.dentry->d_name.name (the filename)
  #   - current->pid (the process ID)
  #   - the full call stack with `bt`
  (gdb) p file->f_path.dentry->d_name.name   # print filename
  (gdb) p current->pid                        # print pid
  (gdb) bt                                    # backtrace
GDB_INSTRUCTIONS

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6: UNLOAD
# ─────────────────────────────────────────────────────────────────────────────

echo ""
echo "── SECTION 6: Unloading the module ──"

# rmmod: unloads a module by name (not path)
# The kernel calls module_exit() (or Drop for Rust) before unloading
rmmod guardian_lsm

sleep 0.2
echo "Unload messages:"
dmesg | grep guardian | tail -5

# Verify it's gone
echo ""
echo "Module no longer in lsmod:"
lsmod | grep guardian || echo "  (correctly absent)"

echo ""
echo "============================================================"
echo " Workflow complete."
echo "============================================================"
