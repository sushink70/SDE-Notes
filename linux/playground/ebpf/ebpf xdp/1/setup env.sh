#!/usr/bin/env bash
# File: scripts/setup_env.sh
#
# Sets up a complete eBPF + kernel module development environment.
# Tested on Ubuntu 22.04 / 24.04 (x86_64 and aarch64).
#
# USAGE:
#   chmod +x setup_env.sh
#   sudo ./setup_env.sh
#
# WHAT IT INSTALLS:
#   1. Kernel development headers and tools
#   2. LLVM/Clang with BPF target support
#   3. libbpf + bpftool
#   4. Rust + Aya toolchain for Rust eBPF
#   5. Testing utilities (netcat, hping3, tcpdump, wireshark-cli)
#   6. Debugging tools (perf, ftrace helpers, bcc)

set -euo pipefail

KERNEL_VER="$(uname -r)"
ARCH="$(uname -m)"

log()  { echo -e "\033[1;32m[+]\033[0m $*"; }
warn() { echo -e "\033[1;33m[!]\033[0m $*"; }
err()  { echo -e "\033[1;31m[✗]\033[0m $*" >&2; exit 1; }

# ─── Root check ──────────────────────────────────────────────────────────────

[[ $EUID -eq 0 ]] || err "Run with sudo: sudo $0"

# ─── 1. Kernel headers + build tools ─────────────────────────────────────────

log "Installing kernel headers and build tools..."
apt-get update -qq
apt-get install -y --no-install-recommends \
    linux-headers-${KERNEL_VER} \
    linux-tools-${KERNEL_VER} \
    linux-tools-common \
    linux-tools-generic \
    build-essential \
    pkg-config \
    libelf-dev \
    zlib1g-dev \
    libssl-dev \
    flex \
    bison \
    bc \
    dwarves \
    pahole

# ─── 2. LLVM/Clang (minimum version 14, prefer 17+) ─────────────────────────

log "Installing LLVM/Clang..."
LLVM_VER=17
apt-get install -y --no-install-recommends \
    clang-${LLVM_VER} \
    llvm-${LLVM_VER} \
    llvm-${LLVM_VER}-dev \
    lld-${LLVM_VER} || {
    warn "LLVM ${LLVM_VER} not in apt; installing from llvm.org..."
    wget -qO- https://apt.llvm.org/llvm.sh | bash -s -- ${LLVM_VER}
    apt-get install -y clang-${LLVM_VER} llvm-${LLVM_VER}
}

# Set as default if not already
update-alternatives --install /usr/bin/clang clang /usr/bin/clang-${LLVM_VER} 100 || true
update-alternatives --install /usr/bin/llc   llc   /usr/bin/llc-${LLVM_VER}   100 || true
update-alternatives --install /usr/bin/llvm-objdump llvm-objdump \
    /usr/bin/llvm-objdump-${LLVM_VER} 100 || true

log "Clang version: $(clang --version | head -1)"

# ─── 3. libbpf ───────────────────────────────────────────────────────────────

log "Installing libbpf..."
apt-get install -y libbpf-dev || {
    warn "libbpf-dev not in apt; building from source..."
    git clone --depth 1 https://github.com/libbpf/libbpf.git /tmp/libbpf
    cd /tmp/libbpf/src
    make install
    ldconfig
    cd -
}

# ─── 4. bpftool ──────────────────────────────────────────────────────────────

log "Installing bpftool..."
if ! command -v bpftool &>/dev/null; then
    apt-get install -y linux-tools-${KERNEL_VER} 2>/dev/null || {
        # Build from kernel source
        apt-get install -y libbpf-dev libcap-dev
        git clone --depth 1 https://github.com/libbpf/bpftool.git /tmp/bpftool
        cd /tmp/bpftool/src
        make
        cp bpftool /usr/local/bin/
        cd -
    }
fi
log "bpftool: $(bpftool version 2>&1 | head -1)"

# ─── 5. Debugging & testing tools ────────────────────────────────────────────

log "Installing debugging and testing tools..."
apt-get install -y --no-install-recommends \
    perf \
    strace \
    ltrace \
    tcpdump \
    tshark \
    hping3 \
    iproute2 \
    netcat-openbsd \
    iperf3 \
    python3 \
    python3-pip \
    jq \
    tmux \
    vim

# ─── 6. BCC (BPF Compiler Collection) ────────────────────────────────────────

log "Installing BCC tools..."
apt-get install -y bpfcc-tools python3-bpfcc 2>/dev/null || \
    warn "BCC not available; install manually from https://github.com/iovisor/bcc"

# ─── 7. Rust + Aya toolchain ─────────────────────────────────────────────────

log "Setting up Rust + Aya eBPF toolchain..."

# Install Rust as the calling user, not root
REAL_USER="${SUDO_USER:-$(logname 2>/dev/null || echo root)}"
REAL_HOME=$(getent passwd "${REAL_USER}" | cut -d: -f6)

if [[ ! -f "${REAL_HOME}/.cargo/bin/rustup" ]]; then
    su - "${REAL_USER}" -c \
        'curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --no-modify-path'
fi

# Install nightly + BPF target
CARGO="${REAL_HOME}/.cargo/bin/cargo"
RUSTUP="${REAL_HOME}/.cargo/bin/rustup"

su - "${REAL_USER}" -c "${RUSTUP} toolchain install nightly --component rust-src"
su - "${REAL_USER}" -c "${RUSTUP} target add bpfel-unknown-none --toolchain nightly"
su - "${REAL_USER}" -c "${CARGO} install bpf-linker"
su - "${REAL_USER}" -c "${CARGO} install cargo-generate"

log "Rust BPF toolchain ready"

# ─── 8. Kernel configuration checks ─────────────────────────────────────────

log "Checking kernel config for BPF/XDP support..."
KCONFIG="/boot/config-${KERNEL_VER}"

check_config() {
    local opt="$1"
    local expected="$2"
    local val
    val=$(grep "^${opt}=" "${KCONFIG}" 2>/dev/null | cut -d= -f2)
    if [[ "${val}" == "${expected}" ]]; then
        echo "  ✓ ${opt}=${val}"
    else
        echo "  ✗ ${opt}=${val} (expected ${expected})"
    fi
}

check_config CONFIG_BPF y
check_config CONFIG_BPF_SYSCALL y
check_config CONFIG_BPF_JIT y
check_config CONFIG_XDP_SOCKETS y
check_config CONFIG_NET_CLS_BPF m
check_config CONFIG_NET_SCH_INGRESS m
check_config CONFIG_DEBUG_INFO_BTF y  # needed for CO-RE
check_config CONFIG_NETFILTER y

# ─── 9. Enable BTF / debug filesystem ────────────────────────────────────────

log "Mounting debug filesystem..."
mount -t debugfs none /sys/kernel/debug 2>/dev/null || true
mount -t tracefs none /sys/kernel/tracing 2>/dev/null || true

# Enable tracing (needed for bpf_printk output)
echo 1 > /sys/kernel/debug/tracing/tracing_on 2>/dev/null || true

# ─── 10. Verify btf vmlinux ──────────────────────────────────────────────────

log "Checking BTF availability..."
if [[ -f /sys/kernel/btf/vmlinux ]]; then
    log "vmlinux BTF available at /sys/kernel/btf/vmlinux ✓"
    # Generate vmlinux.h for CO-RE programs
    bpftool btf dump file /sys/kernel/btf/vmlinux format c > /usr/local/include/vmlinux.h
    log "Generated /usr/local/include/vmlinux.h"
else
    warn "vmlinux BTF not found. CO-RE programs won't work."
    warn "Rebuild kernel with CONFIG_DEBUG_INFO_BTF=y"
fi

# ─── Summary ─────────────────────────────────────────────────────────────────

echo ""
log "═══════════════════════════════════════════════════════"
log "  eBPF Development Environment Ready!"
log "═══════════════════════════════════════════════════════"
echo ""
echo "  Kernel:       ${KERNEL_VER} (${ARCH})"
echo "  Clang:        $(clang --version 2>&1 | head -1)"
echo "  bpftool:      $(bpftool version 2>&1 | head -1)"
echo "  libbpf:       $(pkg-config --modversion libbpf 2>/dev/null || echo 'see /usr/include/bpf')"
echo ""
echo "  Next steps:"
echo "    cd ebpf-net-guide/c && make all"
echo "    sudo make verify"
echo "    sudo ./scripts/load_xdp.sh eth0"