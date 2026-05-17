#!/bin/bash
# ============================================================
# netlab-check.sh — Linux Kernel Network Lab Setup Verifier
# Run this on your Dell G3 Ubuntu Desktop HOST machine
# ============================================================

RED='\033[0;31m'; YEL='\033[1;33m'; GRN='\033[0;32m'
BLU='\033[1;34m'; DIM='\033[2m'; NC='\033[0m'; BOLD='\033[1m'

PASS=0; WARN=0; FAIL=0
REPORT=()

pass() { echo -e "  ${GRN}✔${NC} $1"; PASS=$((PASS+1)); REPORT+=("PASS: $1"); }
warn() { echo -e "  ${YEL}⚠${NC} $1"; WARN=$((WARN+1)); REPORT+=("WARN: $1"); }
fail() { echo -e "  ${RED}✘${NC} $1"; FAIL=$((FAIL+1)); REPORT+=("FAIL: $1"); }
info() { echo -e "  ${DIM}→${NC} $1"; }
section() { echo; echo -e "${BLU}${BOLD}━━ $1 ━━${NC}"; }

# ----- PATHS (edit if yours differ) -----
LAB_ROOT="$HOME/Documents/clion/opensource_sushink70/linux_kernel_net_playground"
KERNEL_SRC="$LAB_ROOT/linux-7.0.6"
KERNEL_TAR="$LAB_ROOT/linux-7.0.6.tar.xz"
ISO_FILE="$LAB_ROOT/ubuntu-24.04.4-live-server-amd64.iso"
VM_DISK="$HOME/vms/netlab.qcow2"
DEB_DIR="$LAB_ROOT"          # bindeb-pkg drops .deb files here

echo
echo -e "${BOLD}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║   Linux Kernel Net Lab — Setup Verifier        ║${NC}"
echo -e "${BOLD}╚════════════════════════════════════════════════╝${NC}"
echo -e "  Host: $(hostname)  |  $(date '+%Y-%m-%d %H:%M')"

# ============================================================
section "1. Hardware & CPU Virtualisation"
# ============================================================

CPU_VMX=$(egrep -c '(vmx|svm)' /proc/cpuinfo 2>/dev/null)
if [ "$CPU_VMX" -gt 0 ]; then
    CPU_TYPE=$(grep -m1 -o 'vmx\|svm' /proc/cpuinfo)
    pass "Hardware virtualisation: ${CPU_TYPE} supported (${CPU_VMX} cores)"
else
    fail "Hardware virtualisation (vmx/svm) NOT found in /proc/cpuinfo — KVM will not work. Enable in BIOS."
fi

RAM_GB=$(free -g | awk '/^Mem:/{print $2}')
if [ "$RAM_GB" -ge 8 ]; then
    pass "RAM: ${RAM_GB}GB (enough to give VM 4GB and keep host comfortable)"
elif [ "$RAM_GB" -ge 6 ]; then
    warn "RAM: ${RAM_GB}GB — workable, but give VM only 2GB instead of 4GB"
else
    fail "RAM: ${RAM_GB}GB — very tight. VM + kernel build will be slow or OOM"
fi

CORES=$(nproc)
if [ "$CORES" -ge 4 ]; then
    pass "CPU cores: ${CORES} (kernel build will use all of them)"
elif [ "$CORES" -ge 2 ]; then
    warn "CPU cores: ${CORES} — build will work but take longer (60-90 min)"
else
    warn "CPU cores: ${CORES} — single core build will be very slow"
fi

# ============================================================
section "2. KVM / libvirt Stack"
# ============================================================

for mod in kvm kvm_intel kvm_amd; do
    if lsmod | grep -q "^$mod "; then
        pass "Kernel module loaded: ${mod}"
    fi
done
# at least one of kvm_intel or kvm_amd must be present
if ! lsmod | grep -qE 'kvm_intel|kvm_amd'; then
    fail "Neither kvm_intel nor kvm_amd module is loaded — run: sudo modprobe kvm_intel   (or kvm_amd for AMD)"
fi

if [ -c /dev/kvm ]; then
    pass "/dev/kvm device exists"
else
    fail "/dev/kvm missing — KVM kernel modules not loaded properly"
fi

if systemctl is-active --quiet libvirtd 2>/dev/null; then
    pass "libvirtd service is running"
elif systemctl is-active --quiet virtqemud 2>/dev/null; then
    pass "virtqemud service is running (modular libvirt)"
else
    fail "libvirtd / virtqemud is NOT running — run: sudo systemctl start libvirtd"
fi

if groups | grep -q libvirt; then
    pass "Current user is in 'libvirt' group (can manage VMs without sudo)"
else
    warn "User not in 'libvirt' group — you'll need sudo for virsh commands. Fix: sudo usermod -aG libvirt $USER && newgrp libvirt"
fi

if groups | grep -q kvm; then
    pass "Current user is in 'kvm' group"
else
    warn "User not in 'kvm' group. Fix: sudo usermod -aG kvm $USER && newgrp kvm"
fi

# virbr0 (NAT network)
if ip link show virbr0 &>/dev/null; then
    VIRBR_IP=$(ip -4 addr show virbr0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
    pass "virbr0 bridge is up — VM NAT network at ${VIRBR_IP:-192.168.122.1}"
else
    warn "virbr0 not found — libvirt default NAT network may not be started. Run: virsh net-start default && virsh net-autostart default"
fi

# ============================================================
section "3. Required Host Packages"
# ============================================================

REQUIRED_PKGS=(
    build-essential libncurses-dev bison flex
    libssl-dev libelf-dev dwarves bc cpio pahole
    qemu-kvm libvirt-daemon-system virt-manager
    bridge-utils virtinst qemu-utils
    gdb crash
    linux-tools-common trace-cmd
    cscope exuberant-ctags tmux
    git devscripts dpkg-dev xorriso
)

MISSING_PKGS=()
for pkg in "${REQUIRED_PKGS[@]}"; do
    if dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null | grep -q "install ok installed"; then
        : # installed
    else
        MISSING_PKGS+=("$pkg")
    fi
done

if [ ${#MISSING_PKGS[@]} -eq 0 ]; then
    pass "All required host packages are installed (${#REQUIRED_PKGS[@]} packages)"
else
    fail "Missing packages (${#MISSING_PKGS[@]}): ${MISSING_PKGS[*]}"
    info "Fix: sudo apt install -y ${MISSING_PKGS[*]}"
fi

# optional but very useful
OPTIONAL_PKGS=(kernelshark wireshark gdb-multiarch bpftrace)
MISSING_OPT=()
for pkg in "${OPTIONAL_PKGS[@]}"; do
    dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null | grep -q "install ok installed" || MISSING_OPT+=("$pkg")
done
[ ${#MISSING_OPT[@]} -gt 0 ] && warn "Optional packages not installed: ${MISSING_OPT[*]}"

# ============================================================
section "4. Lab Directory & Downloaded Files"
# ============================================================

if [ -d "$LAB_ROOT" ]; then
    pass "Lab root exists: $LAB_ROOT"
else
    fail "Lab root NOT found: $LAB_ROOT — check your path at the top of this script"
fi

if [ -f "$KERNEL_TAR" ]; then
    TAR_SIZE=$(du -h "$KERNEL_TAR" | cut -f1)
    pass "Kernel tarball present: linux-7.0.6.tar.xz (${TAR_SIZE})"
else
    fail "Kernel tarball NOT found: $KERNEL_TAR"
    info "Download from: https://cdn.kernel.org/pub/linux/kernel/v7.x/linux-7.0.6.tar.xz"
fi

if [ -f "$ISO_FILE" ]; then
    ISO_SIZE=$(du -h "$ISO_FILE" | cut -f1)
    pass "Ubuntu Server ISO present: ubuntu-24.04.4-live-server-amd64.iso (${ISO_SIZE})"
else
    fail "Ubuntu Server ISO NOT found: $ISO_FILE"
    info "Download from: https://releases.ubuntu.com/24.04/ubuntu-24.04.4-live-server-amd64.iso"
fi

DISK_FREE_G=$(df -BG "$LAB_ROOT" 2>/dev/null | awk 'NR==2{gsub(/G/,"",$4);print $4}')
if [ -n "$DISK_FREE_G" ] && [ "$DISK_FREE_G" -ge 40 ]; then
    pass "Disk free in lab dir: ${DISK_FREE_G}GB (plenty for kernel build + VM)"
elif [ -n "$DISK_FREE_G" ] && [ "$DISK_FREE_G" -ge 20 ]; then
    warn "Disk free in lab dir: ${DISK_FREE_G}GB — tight. Kernel build needs ~15GB, VM disk 40GB. Consider cleaning up."
elif [ -n "$DISK_FREE_G" ]; then
    fail "Disk free in lab dir: ${DISK_FREE_G}GB — NOT enough. Need at least 20GB for kernel build alone."
fi

# ============================================================
section "5. Kernel Source Extraction"
# ============================================================

if [ -d "$KERNEL_SRC" ]; then
    pass "Kernel source extracted: $KERNEL_SRC"
    SRC_SIZE=$(du -sh "$KERNEL_SRC" 2>/dev/null | cut -f1)
    info "Source tree size: ${SRC_SIZE}"
else
    warn "Kernel source NOT extracted yet — run from $LAB_ROOT:"
    info "tar -xf linux-7.0.6.tar.xz"
fi

if [ -f "$KERNEL_SRC/Makefile" ]; then
    KV=$(head -5 "$KERNEL_SRC/Makefile" | grep -E '^VERSION|^PATCHLEVEL|^SUBLEVEL' | awk -F= '{print $2}' | tr -d ' ' | tr '\n' '.' | sed 's/\.$//')
    pass "Kernel Makefile found — version: linux-${KV}"
else
    [ -d "$KERNEL_SRC" ] && fail "Makefile missing inside $KERNEL_SRC — extraction may be incomplete or corrupted"
fi

# ============================================================
section "6. Kernel .config — Debug Options"
# ============================================================

CONFIG="$KERNEL_SRC/.config"
if [ ! -f "$CONFIG" ]; then
    warn "No .config found in $KERNEL_SRC"
    info "Create one: cd $KERNEL_SRC && cp /boot/config-\$(uname -r) .config && make olddefconfig"
else
    pass ".config file exists"

    check_config() {
        local key="$1" want="$2" label="$3"
        local val
        val=$(grep -E "^${key}=" "$CONFIG" 2>/dev/null | cut -d= -f2)
        if [ "$val" = "$want" ]; then
            pass "CONFIG: ${label} = ${want}"
        elif [ -z "$val" ]; then
            # check if it's commented out as 'not set'
            if grep -q "# ${key} is not set" "$CONFIG"; then
                fail "CONFIG: ${label} is explicitly DISABLED — run: scripts/config --enable ${key}"
            else
                fail "CONFIG: ${label} NOT set — run: scripts/config --enable ${key}"
            fi
        else
            fail "CONFIG: ${label} = ${val} (expected ${want}) — run: scripts/config --enable ${key}"
        fi
    }

    check_config CONFIG_DEBUG_INFO              y  "DEBUG_INFO (GDB symbols)"
    check_config CONFIG_DEBUG_KERNEL            y  "DEBUG_KERNEL"
    check_config CONFIG_FRAME_POINTER           y  "FRAME_POINTER (stack traces)"
    check_config CONFIG_KALLSYMS                y  "KALLSYMS (symbol table)"
    check_config CONFIG_KALLSYMS_ALL            y  "KALLSYMS_ALL"
    check_config CONFIG_KGDB                    y  "KGDB (remote GDB)"
    check_config CONFIG_KGDB_SERIAL_CONSOLE     y  "KGDB_SERIAL_CONSOLE"
    check_config CONFIG_GDB_SCRIPTS             y  "GDB_SCRIPTS"
    check_config CONFIG_FTRACE                  y  "FTRACE (function tracer)"
    check_config CONFIG_FUNCTION_TRACER         y  "FUNCTION_TRACER"
    check_config CONFIG_FUNCTION_GRAPH_TRACER   y  "FUNCTION_GRAPH_TRACER"
    check_config CONFIG_DYNAMIC_FTRACE          y  "DYNAMIC_FTRACE (zero overhead when off)"
    check_config CONFIG_DYNAMIC_DEBUG           y  "DYNAMIC_DEBUG (per-file pr_debug)"
    check_config CONFIG_BPF_SYSCALL             y  "BPF_SYSCALL (eBPF/bpftrace)"
    check_config CONFIG_BPF_JIT                 y  "BPF_JIT"
    check_config CONFIG_DEBUG_INFO_BTF          y  "DEBUG_INFO_BTF (bpftrace struct access)"
    check_config CONFIG_VIRTIO_NET              y  "VIRTIO_NET (VM NIC driver)"
    check_config CONFIG_VHOST_NET               y  "VHOST_NET (host side of virtio)"
    check_config CONFIG_NET_SCHED               y  "NET_SCHED (TC/qdisc)"

    # KASLR should be OFF for debug VM
    KASLR=$(grep -E "^CONFIG_RANDOMIZE_BASE=" "$CONFIG" 2>/dev/null | cut -d= -f2)
    if [ "$KASLR" = "n" ] || grep -q "# CONFIG_RANDOMIZE_BASE is not set" "$CONFIG"; then
        pass "CONFIG: KASLR disabled (stable addresses for GDB)"
    else
        warn "CONFIG: KASLR is ON — GDB breakpoints may be unstable. Disable: scripts/config --disable CONFIG_RANDOMIZE_BASE"
    fi
fi

# ============================================================
section "7. Kernel Build Output (.deb packages)"
# ============================================================

DEBS_IMAGE=$(ls "$DEB_DIR"/linux-image-*-netlab*.deb 2>/dev/null | head -1)
DEBS_HDRS=$(ls "$DEB_DIR"/linux-headers-*-netlab*.deb 2>/dev/null | head -1)
BUILD_LOG="$DEB_DIR/linux-7.0.6/build.log"

if [ -n "$DEBS_IMAGE" ]; then
    DEB_DATE=$(stat -c '%y' "$DEBS_IMAGE" | cut -d' ' -f1)
    DEB_SIZE=$(du -h "$DEBS_IMAGE" | cut -f1)
    pass "Kernel .deb (image) built: $(basename $DEBS_IMAGE) [${DEB_SIZE}, ${DEB_DATE}]"
else
    warn "Kernel .deb NOT built yet — kernel image not in $DEB_DIR"
    info "Build: cd $KERNEL_SRC && make -j\$(nproc) bindeb-pkg LOCALVERSION=-netlab"
fi

if [ -n "$DEBS_HDRS" ]; then
    pass "Kernel .deb (headers) built: $(basename $DEBS_HDRS)"
else
    [ -n "$DEBS_IMAGE" ] && warn "Headers .deb missing (needed for building kernel modules in VM)"
fi

if [ -f "$BUILD_LOG" ]; then
    ERRORS=$(grep -c "^.*error:" "$BUILD_LOG" 2>/dev/null || echo 0)
    if [ "$ERRORS" -gt 0 ]; then
        fail "build.log contains ${ERRORS} error(s) — check: grep 'error:' $BUILD_LOG | head -20"
    else
        pass "build.log exists, no error lines found"
    fi
fi

# ============================================================
section "8. KVM Virtual Machine"
# ============================================================

if command -v virsh &>/dev/null; then
    pass "virsh command available"

    VM_STATUS=$(virsh list --all 2>/dev/null | grep netlab | awk '{print $3,$4}')
    if [ -n "$VM_STATUS" ]; then
        pass "VM 'netlab' exists — state: ${VM_STATUS}"

        VM_RUNNING=$(virsh list 2>/dev/null | grep -c netlab)
        if [ "$VM_RUNNING" -gt 0 ]; then
            pass "VM 'netlab' is currently RUNNING"

            VM_IP=$(virsh domifaddr netlab 2>/dev/null | grep -oP '(\d+\.){3}\d+' | head -1)
            if [ -n "$VM_IP" ]; then
                pass "VM IP address: ${VM_IP}"

                if ssh -o ConnectTimeout=3 -o StrictHostKeyChecking=no "netlab@${VM_IP}" 'uname -r' &>/dev/null; then
                    KERNEL_VER=$(ssh -o ConnectTimeout=3 -o StrictHostKeyChecking=no "netlab@${VM_IP}" 'uname -r' 2>/dev/null)
                    if echo "$KERNEL_VER" | grep -q "netlab"; then
                        pass "VM is running your custom kernel: ${KERNEL_VER}"
                    else
                        warn "VM running but NOT your custom kernel yet: ${KERNEL_VER}"
                        info "Install your .deb in VM and reboot"
                    fi
                else
                    warn "VM running but SSH not reachable on ${VM_IP} — check SSH is installed in VM, or VM still booting"
                fi
            else
                warn "VM running but no IP yet — may still be booting"
            fi
        else
            warn "VM 'netlab' exists but is NOT running — start it: virsh start netlab"
        fi
    else
        warn "VM 'netlab' does NOT exist yet"
        info "Create: follow Phase 2 in your setup notes (virt-install command)"
        info "ISO: $ISO_FILE"
    fi
else
    fail "virsh not installed — install: sudo apt install libvirt-clients"
fi

if [ -f "$VM_DISK" ]; then
    VM_DISK_SIZE=$(du -h "$VM_DISK" | cut -f1)
    pass "VM disk image found: $VM_DISK (${VM_DISK_SIZE})"
else
    warn "VM disk not found at $VM_DISK"
    info "Create: qemu-img create -f qcow2 ~/vms/netlab.qcow2 40G"
fi

# ============================================================
section "9. Debugging Infrastructure"
# ============================================================

# check if ser2net or socat is available for KGDB
for tool in gdb socat screen minicom; do
    if command -v $tool &>/dev/null; then
        pass "${tool} is available (for KGDB / serial debugging)"
    fi
done

# check tracing filesystem on host
if mount | grep -q debugfs; then
    pass "debugfs is mounted (/sys/kernel/debug accessible)"
else
    warn "debugfs not mounted — mount it: sudo mount -t debugfs none /sys/kernel/debug"
fi

# bpftrace on host (optional but useful for testing)
if command -v bpftrace &>/dev/null; then
    pass "bpftrace available on host: $(bpftrace --version 2>/dev/null | head -1)"
else
    info "bpftrace not on host (it's fine — you'll use it inside the VM)"
fi

# check vmlinux exists (needed for GDB)
if [ -f "$KERNEL_SRC/vmlinux" ]; then
    VMLINUX_SIZE=$(du -h "$KERNEL_SRC/vmlinux" | cut -f1)
    pass "vmlinux found (${VMLINUX_SIZE}) — needed for KGDB debugging"
else
    warn "vmlinux not present — it's built alongside the kernel. Run the build first."
fi

# ============================================================
section "10. Git & Code Organisation"
# ============================================================

if [ -d "$KERNEL_SRC/.git" ]; then
    pass "Kernel source has git repo initialised"
    GIT_STAT=$(cd "$KERNEL_SRC" && git status --short 2>/dev/null | wc -l)
    if [ "$GIT_STAT" -gt 0 ]; then
        info "Uncommitted changes in kernel source: ${GIT_STAT} files modified"
        info "To save patches: cd $KERNEL_SRC && git diff > ../patches/my-changes.patch"
    else
        pass "Kernel source is clean (no uncommitted changes)"
    fi
else
    warn "No git in $KERNEL_SRC — initialise to track your changes:"
    info "cd $KERNEL_SRC && git init && git add -A && git commit -m 'vanilla 7.0.6 base'"
fi

# ============================================================
section "11. Network Connectivity (kernel.org reachable)"
# ============================================================

if curl -s --connect-timeout 5 https://www.kernel.org > /dev/null; then
    pass "kernel.org reachable — can download kernel tarballs/patches"
else
    warn "kernel.org NOT reachable — check your internet connection"
fi

# ============================================================
# SUMMARY
# ============================================================

echo
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}  SUMMARY${NC}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo
echo -e "  ${GRN}${BOLD}PASS${NC} : ${PASS}"
echo -e "  ${YEL}${BOLD}WARN${NC} : ${WARN}"
echo -e "  ${RED}${BOLD}FAIL${NC} : ${FAIL}"
echo

if [ $FAIL -eq 0 ] && [ $WARN -eq 0 ]; then
    echo -e "  ${GRN}${BOLD}✔ Everything is ready! Start your lab.${NC}"
elif [ $FAIL -eq 0 ]; then
    echo -e "  ${YEL}${BOLD}⚠ Almost ready — review warnings above.${NC}"
else
    echo -e "  ${RED}${BOLD}✘ Fix the failures above before proceeding.${NC}"
fi

echo
echo -e "${DIM}  Next steps (in order):"
echo -e "  1. Fix any FAIL items above"
echo -e "  2. Address WARN items (most are optional but recommended)"
echo -e "  3. If kernel not built: cd $KERNEL_SRC"
echo -e "        make -j\$(nproc) bindeb-pkg LOCALVERSION=-netlab"
echo -e "  4. If VM not created: run Phase 2 (virt-install) from your setup notes"
echo -e "  5. If VM exists but old kernel: scp .deb files into VM, dpkg -i, reboot"
echo -e "  6. Inside VM: sudo apt install tshark trace-cmd bpftrace gdb tmux${NC}"
echo
