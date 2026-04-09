#!/usr/bin/env bash
# =============================================================================
# edu_net_devenv.sh — Complete kernel net-subsystem developer workflow
#
# Covers:
#   1. Tree setup (net-next, not Linus mainline)
#   2. Kernel config + build
#   3. virtme-ng / QEMU test VM
#   4. Module load / unload
#   5. Debugging: ftrace, kprobes, dynamic debug, KASAN, kmemleak
#   6. static analysis: sparse, smatch, checkpatch
#   7. Tracing: perf, bpftrace
#   8. Testing: kselftest, pktgen, iperf3
#   9. Patch workflow (get_maintainer, checkpatch, b4, send-email)
#
# Run: bash edu_net_devenv.sh <step>
# =============================================================================

set -euo pipefail

KERNEL_DIR="${HOME}/kernel/net-next"
MODULE_DIR="${HOME}/edu_net"
CCACHE="ccache"          # remove if not installed
JOBS=$(nproc)

# ---------------------------------------------------------------------------
# STEP 0: System prerequisites
# ---------------------------------------------------------------------------
step0_deps() {
  echo "=== Installing build dependencies ==="
  # Debian/Ubuntu
  sudo apt-get install -y \
    git bc bison flex libelf-dev libssl-dev libncurses-dev \
    build-essential pahole dwarves cpio zstd \
    sparse smatch coccinelle \
    qemu-system-x86 qemu-kvm \
    python3-pip python3-venv \
    ccache clang llvm lld \
    linux-tools-common linux-tools-generic  # perf

  # virtme-ng: fast kernel VM (no disk image needed)
  pip3 install --user virtme-ng

  # b4: patch management tool used by kernel developers
  pip3 install --user b4

  # rustup for Rust in-kernel (if building Rust module)
  if ! command -v rustup &>/dev/null; then
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
  fi
  rustup override set $(cat "${KERNEL_DIR}/rust/rust-version" 2>/dev/null || echo "1.73.0")
  cargo install --locked bindgen-cli
}

# ---------------------------------------------------------------------------
# STEP 1: Clone the correct tree
#
# IMPORTANT: Networking patches go through the NET-NEXT tree, maintained by
# Jakub Kicinski (kuba@kernel.org) and Paolo Abeni, NOT directly to Linus.
# Tree hierarchy:
#   Linus mainline (torvalds/linux) ← net-next (netdev/net-next) ← your patch
#
# Linus pulls net-next at each merge window. Day-to-day net dev happens in
# net-next. Bug fixes for current release go to 'net' branch (stable fixes).
# ---------------------------------------------------------------------------
step1_clone() {
  echo "=== Cloning net-next tree ==="
  mkdir -p "${HOME}/kernel"
  cd "${HOME}/kernel"

  # Primary: kernel.org (official)
  git clone --depth=1 \
    git://git.kernel.org/pub/scm/linux/kernel/git/netdev/net-next.git \
    net-next

  # Alternative mirror on GitHub (read-only, same content):
  # git clone https://github.com/torvalds/linux.git   # Linus mainline
  # git clone https://github.com/netdev/net-next.git  # net-next mirror

  cd net-next

  # Set up your identity (required for patches)
  git config user.name  "Your Name"
  git config user.email "you@example.com"

  # Add Linus mainline as remote for rebasing
  git remote add linus \
    git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git

  echo "Tree ready at ${KERNEL_DIR}"
}

# ---------------------------------------------------------------------------
# STEP 2: Place your module in the kernel tree
# ---------------------------------------------------------------------------
step2_integrate() {
  echo "=== Integrating edu_net into kernel tree ==="
  cd "${KERNEL_DIR}"

  # Create driver directory
  mkdir -p drivers/net/edu_net/{c,rust}

  # Copy source files
  cp "${MODULE_DIR}/c/edu_net.c"   drivers/net/edu_net/c/
  cp "${MODULE_DIR}/rust/lib.rs"   drivers/net/edu_net/rust/
  cp "${MODULE_DIR}/Kconfig"       drivers/net/edu_net/
  cp "${MODULE_DIR}/Makefile"      drivers/net/edu_net/

  # Hook into parent Kconfig (append to drivers/net/Kconfig)
  if ! grep -q "edu_net" drivers/net/Kconfig; then
    echo 'source "drivers/net/edu_net/Kconfig"' >> drivers/net/Kconfig
  fi

  # Hook into parent Makefile (append to drivers/net/Makefile)
  if ! grep -q "edu_net" drivers/net/Makefile; then
    echo 'obj-$(CONFIG_EDU_NET) += edu_net/' >> drivers/net/Makefile
  fi

  echo "Integration done. Run: make menuconfig → Device Drivers → Network → edu_net"
}

# ---------------------------------------------------------------------------
# STEP 3: Configure and build the kernel
# ---------------------------------------------------------------------------
step3_build() {
  echo "=== Building kernel with edu_net ==="
  cd "${KERNEL_DIR}"

  # Start from a minimal config (faster builds for testing)
  make LLVM=1 defconfig      # or: make tinyconfig; make kvmconfig

  # Enable relevant options programmatically
  scripts/config --module  CONFIG_EDU_NET
  scripts/config --enable  CONFIG_NET
  scripts/config --enable  CONFIG_NETDEVICES
  scripts/config --enable  CONFIG_ETHERNET

  # Debug options (disable for perf benchmarks)
  scripts/config --enable  CONFIG_KASAN
  scripts/config --enable  CONFIG_KASAN_INLINE
  scripts/config --enable  CONFIG_UBSAN
  scripts/config --enable  CONFIG_DEBUG_KERNEL
  scripts/config --enable  CONFIG_KMEMLEAK       # detects our Bug #1
  scripts/config --enable  CONFIG_LOCKDEP
  scripts/config --enable  CONFIG_PROVE_LOCKING
  scripts/config --enable  CONFIG_DYNAMIC_DEBUG
  scripts/config --enable  CONFIG_FTRACE
  scripts/config --enable  CONFIG_FUNCTION_TRACER
  scripts/config --enable  CONFIG_KPROBES
  scripts/config --enable  CONFIG_BPF_SYSCALL

  # Rust (only if building Rust module)
  # scripts/config --enable CONFIG_RUST
  # make LLVM=1 rustavailable

  # Resolve any new symbol dependencies
  make LLVM=1 olddefconfig

  # Build (LLVM=1 uses clang + lld — better sanitizer support)
  make LLVM=1 -j${JOBS} CC="${CCACHE} clang" \
    2>&1 | tee /tmp/kernel_build.log

  echo "Build complete. bzImage: arch/x86/boot/bzImage"
}

# ---------------------------------------------------------------------------
# STEP 4: Build just the module (faster iteration)
# ---------------------------------------------------------------------------
step4_build_module() {
  echo "=== Building edu_net module only ==="
  cd "${KERNEL_DIR}"

  # In-tree module build — only compiles drivers/net/edu_net/
  make LLVM=1 -j${JOBS} M=drivers/net/edu_net modules

  # OR: out-of-tree build from MODULE_DIR
  # cd "${MODULE_DIR}"
  # make KDIR="${KERNEL_DIR}" LLVM=1

  ls -lh drivers/net/edu_net/*.ko 2>/dev/null || \
    ls -lh drivers/net/edu_net/c/*.ko 2>/dev/null
}

# ---------------------------------------------------------------------------
# STEP 5: Boot in virtme-ng (no disk image, uses host filesystem)
# ---------------------------------------------------------------------------
step5_virtme() {
  echo "=== Booting test kernel in virtme-ng ==="
  cd "${KERNEL_DIR}"

  # virtme-ng boots the kernel with 9p virtio for root fs
  # --script-sh runs a shell script inside the VM
  vng --build   # builds the kernel if needed
  vng --run \
    --kimg arch/x86/boot/bzImage \
    --qemu-opts "-m 2G -smp 2 -enable-kvm" \
    -- bash -c "
      modprobe edu_net || insmod /mnt/edu_net.ko
      ip link set edu_net0 up
      ip addr add 192.168.99.1/24 dev edu_net0
      ping -c 3 -I edu_net0 192.168.99.1
      cat /proc/net/dev | grep edu
      ip -s link show edu_net0
    "
}

# ---------------------------------------------------------------------------
# STEP 6: Manual insmod / rmmod + verification
# ---------------------------------------------------------------------------
step6_insmod() {
  echo "=== Loading module ==="
  # Check module info before loading
  modinfo drivers/net/edu_net/edu_net.ko

  # Load
  sudo insmod drivers/net/edu_net/edu_net.ko

  # Verify device appeared
  ip link show edu_net0
  cat /proc/net/dev | grep edu

  # Enable and assign address
  sudo ip link set edu_net0 up
  sudo ip addr add 10.0.99.1/24 dev edu_net0

  # Send traffic (loopback mode reflects TX as RX)
  ping -c 5 10.0.99.1 -I edu_net0

  # Read stats (netlink path → ndo_get_stats64)
  ip -s link show edu_net0

  # Unload
  sudo rmmod edu_net

  # Verify clean removal
  dmesg | tail -20
}

# ---------------------------------------------------------------------------
# STEP 7: Debugging — ftrace + kprobes
# ---------------------------------------------------------------------------
step7_ftrace() {
  echo "=== ftrace on edu_net_xmit ==="
  TRACEFS=/sys/kernel/tracing

  # Enable function tracer on our TX function
  echo 0 > ${TRACEFS}/tracing_on
  echo "edu_net_xmit" > ${TRACEFS}/set_ftrace_filter
  echo function > ${TRACEFS}/current_tracer
  echo 1 > ${TRACEFS}/tracing_on

  # Generate traffic
  ping -c 10 10.0.99.1 -I edu_net0 &>/dev/null

  echo 0 > ${TRACEFS}/tracing_on
  cat ${TRACEFS}/trace | head -50

  # Cleanup
  echo nop > ${TRACEFS}/current_tracer
  echo > ${TRACEFS}/set_ftrace_filter

  # kprobe on edu_net_xmit — print skb->len on entry
  echo "p:edu_xmit edu_net_xmit skb_len=+0x70(%di):u32" \
    > ${TRACEFS}/kprobe_events
  echo 1 > ${TRACEFS}/events/kprobes/edu_xmit/enable
  echo 1 > ${TRACEFS}/tracing_on
  ping -c 5 10.0.99.1 -I edu_net0 &>/dev/null
  echo 0 > ${TRACEFS}/tracing_on
  cat ${TRACEFS}/trace
  echo 0 > ${TRACEFS}/events/kprobes/edu_xmit/enable
}

# ---------------------------------------------------------------------------
# STEP 7b: Dynamic debug — pr_debug() without recompile
# ---------------------------------------------------------------------------
step7_dyndbg() {
  # Enable all pr_debug in edu_net module
  echo "module edu_net +p" > /sys/kernel/debug/dynamic_debug/control
  dmesg -w &   # watch in background
  ping -c 5 10.0.99.1 -I edu_net0
  kill %1
}

# ---------------------------------------------------------------------------
# STEP 8: KASAN — catches Bug #1 (use-after-free / memory leak)
# ---------------------------------------------------------------------------
step8_kasan() {
  echo "=== KASAN test with buggy module ==="
  sudo insmod edu_net_buggy.ko

  # Flood with small packets to saturate the RX ring
  # Ring full → Bug #1 triggers → KASAN will report use-after-free
  # (if we did the double-free variant) or kmemleak (leak variant)
  ip link set edu_net_buggy0 up 2>/dev/null || true
  cat /dev/urandom | nc -u -w1 127.0.0.1 9 &>/dev/null || true

  # Check KASAN output
  dmesg | grep -A 20 "KASAN\|BUG:" | head -60

  sudo rmmod edu_net_buggy
}

# ---------------------------------------------------------------------------
# STEP 8b: kmemleak — find the skb leak in Bug #1
# ---------------------------------------------------------------------------
step8_kmemleak() {
  echo "=== kmemleak for Bug #1 ==="
  # Trigger the leak
  sudo insmod edu_net_buggy.ko
  ip link set edu_net_buggy0 up 2>/dev/null || true

  # Flood to fill ring and trigger the leak path
  python3 -c "
import socket, time
s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
# send 300 frames to overflow 256-entry ring
for i in range(300):
    s.sendto(b'\\xff'*6 + b'\\x00'*6 + b'\\x08\\x00' + b'A'*46, ('edu_net_buggy0', 0))
  " 2>/dev/null || true

  # Trigger kmemleak scan
  echo scan > /sys/kernel/debug/kmemleak
  sleep 5
  cat /sys/kernel/debug/kmemleak

  sudo rmmod edu_net_buggy
}

# ---------------------------------------------------------------------------
# STEP 9: Static analysis
# ---------------------------------------------------------------------------
step9_static() {
  echo "=== sparse / smatch / checkpatch ==="
  cd "${KERNEL_DIR}"

  # sparse — C type checker, catches endian issues, lock annotations
  make C=2 CF="-D__CHECK_ENDIAN__" \
    M=drivers/net/edu_net 2>&1 | tee /tmp/sparse.log

  # smatch — interprocedural checker; detects our Bug #1 (skb not freed)
  # Install: git clone https://repo.or.cz/smatch.git && make
  # smatch --project=kernel -p=kernel \
  #   drivers/net/edu_net/edu_net.c 2>&1 | tee /tmp/smatch.log

  # checkpatch — style + semantic checks required before submission
  scripts/checkpatch.pl --no-tree \
    --file drivers/net/edu_net/c/edu_net.c

  # coccinelle — semantic patches; finds common patterns like our Bug #2
  scripts/coccicheck.sh MODE=report \
    COCCI=scripts/coccinelle/locks/ \
    M=drivers/net/edu_net 2>&1 | head -40

  # Clang static analyzer
  scan-build make LLVM=1 M=drivers/net/edu_net modules \
    2>&1 | tee /tmp/clang_sa.log
}

# ---------------------------------------------------------------------------
# STEP 10: Performance benchmarks
# ---------------------------------------------------------------------------
step10_perf() {
  echo "=== Performance benchmark ==="

  # pktgen — kernel packet generator, accurate TX benchmarks
  modprobe pktgen
  cat > /tmp/pktgen.sh <<'EOF'
function pgset() { echo $1 > $PGDEV; }
PGDEV=/proc/net/pktgen/pgctrl
pgset "reset"
PGDEV=/proc/net/pktgen/kpktgend_0
pgset "rem_device_all"
pgset "add_device edu_net0"
PGDEV=/proc/net/pktgen/edu_net0
pgset "count 1000000"
pgset "pkt_size 1400"
pgset "dst_mac ff:ff:ff:ff:ff:ff"
PGDEV=/proc/net/pktgen/pgctrl
pgset "start"
cat /proc/net/pktgen/edu_net0
EOF
  sudo bash /tmp/pktgen.sh

  # perf stat on xmit function
  sudo perf stat -e cycles,instructions,cache-misses \
    -p $(pgrep -f pktgen) -- sleep 3

  # perf record for flamegraph
  sudo perf record -g -F 99 -a -- sleep 10
  sudo perf script | stackcollapse-perf.pl | flamegraph.pl > /tmp/edu_net.svg
}

# ---------------------------------------------------------------------------
# STEP 11: kselftest integration
# ---------------------------------------------------------------------------
step11_kselftest() {
  echo "=== kselftest for net ==="
  cd "${KERNEL_DIR}"

  # Run existing network selftests (our module participates via netdev)
  make TARGETS=net kselftest 2>&1 | tee /tmp/kselftest.log

  # Run virtme kselftest (isolated VM)
  vng --run -- make TARGETS=net kselftest
}

# ---------------------------------------------------------------------------
# STEP 12: Patch submission workflow
# ---------------------------------------------------------------------------
step12_patch() {
  echo "=== Preparing patch for submission ==="
  cd "${KERNEL_DIR}"

  # Check who to CC
  git diff HEAD~1 | scripts/get_maintainer.pl

  # Run checkpatch on your commits
  git format-patch -1 HEAD
  scripts/checkpatch.pl 0001-*.patch

  # b4 shazam: fetches patch series from lore.kernel.org
  # b4 am <message-id>

  # Send via git send-email
  # git send-email \
  #   --to netdev@vger.kernel.org \
  #   --cc kuba@kernel.org \
  #   --cc pabeni@redhat.com \
  #   0001-net-edu_net-add-educational-virtual-NIC.patch
}

# ---------------------------------------------------------------------------
# Main dispatcher
# ---------------------------------------------------------------------------
case "${1:-help}" in
  deps)    step0_deps ;;
  clone)   step1_clone ;;
  integrate) step2_integrate ;;
  build)   step3_build ;;
  module)  step4_build_module ;;
  virtme)  step5_virtme ;;
  insmod)  step6_insmod ;;
  ftrace)  step7_ftrace ;;
  dyndbg)  step7_dyndbg ;;
  kasan)   step8_kasan ;;
  kmemleak) step8_kmemleak ;;
  static)  step9_static ;;
  perf)    step10_perf ;;
  kselftest) step11_kselftest ;;
  patch)   step12_patch ;;
  *)
    echo "Usage: $0 {deps|clone|integrate|build|module|virtme|insmod|"
    echo "           ftrace|dyndbg|kasan|kmemleak|static|perf|kselftest|patch}"
    ;;
esac
