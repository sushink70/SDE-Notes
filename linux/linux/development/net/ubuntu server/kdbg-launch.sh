#!/usr/bin/env bash
# =============================================================================
# kdbg-launch.sh — QEMU Kernel Debug Launch Script
# Full debug stack: KGDB + KASAN + ftrace + kprobes + eBPF + netconsole
# Usage: ./kdbg-launch.sh [mode]
#   Modes: install | boot | debug | netlog | kunit | fuzz | help
# =============================================================================

set -euo pipefail

# =============================================================================
# CONFIGURATION — Edit these to match your setup
# =============================================================================

KERNEL_SRC="${HOME}/linux-6.12"                          # kernel source dir
KERNEL_IMG="${KERNEL_SRC}/arch/x86/boot/bzImage"         # compiled kernel

DISK_24="${HOME}/Downloads/ubuntu24-test.qcow2"          # Ubuntu 24.04 disk image
DISK_26="${HOME}/Downloads/ubuntu26-test.qcow2"          # Ubuntu 26.04 disk image

ISO_24="${HOME}/Downloads/ubuntu-24.04.4-live-server-amd64.iso"
ISO_26="${HOME}/Downloads/ubuntu-26.04-live-server-amd64.iso"

HOST_IP="10.0.2.2"        # QEMU default host IP (reachable from guest)
NETCONS_PORT="6666"       # netconsole UDP port (logs from guest → host)
GDB_PORT="1234"           # GDB remote stub port
MONITOR_PORT="4444"       # QEMU monitor port (telnet)
SSH_HOST_PORT="2222"      # SSH from host into guest: ssh -p 2222 user@localhost

RAM="2G"
CPUS="2"

# Shared folder between host and guest (9p virtio)
SHARED_DIR="${HOME}/qemu-shared"

# =============================================================================
# COLORS
# =============================================================================

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

log()  { echo -e "${GREEN}[+]${NC} $*"; }
info() { echo -e "${BLUE}[i]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
err()  { echo -e "${RED}[x]${NC} $*"; exit 1; }
hdr()  { echo -e "\n${BOLD}${CYAN}=== $* ===${NC}"; }

# =============================================================================
# PREFLIGHT CHECKS
# =============================================================================

check_deps() {
    hdr "Checking dependencies"
    local missing=()

    for cmd in qemu-system-x86_64 qemu-img gdb nc python3; do
        if command -v "$cmd" &>/dev/null; then
            log "$cmd found: $(command -v $cmd)"
        else
            missing+=("$cmd")
            warn "$cmd NOT found"
        fi
    done

    if [[ ${#missing[@]} -gt 0 ]]; then
        warn "Installing missing deps..."
        sudo apt install -y \
            qemu-system-x86 qemu-kvm qemu-utils \
            gdb gdb-multiarch \
            netcat-openbsd \
            python3 python3-pip \
            bpftrace linux-tools-common \
            2>/dev/null || true
    fi

    # Check KVM
    if [[ -e /dev/kvm ]]; then
        log "KVM available — hardware acceleration enabled"
        KVM_FLAG="-enable-kvm"
    else
        warn "KVM not available — running in software emulation (slow)"
        KVM_FLAG=""
    fi

    # Check kernel image
    [[ -f "$KERNEL_IMG" ]] || warn "Kernel image not found: $KERNEL_IMG (needed for debug/boot modes)"

    # Create shared dir
    mkdir -p "$SHARED_DIR"
    log "Shared dir: $SHARED_DIR (mount inside guest: mount -t 9p host_share /mnt/share)"
}

# =============================================================================
# KERNEL CONFIG — Apply all debug options
# =============================================================================

configure_kernel() {
    hdr "Configuring kernel debug options"
    [[ -d "$KERNEL_SRC" ]] || err "Kernel source not found: $KERNEL_SRC"
    cd "$KERNEL_SRC"

    log "Starting from current running kernel config..."
    cp /boot/config-$(uname -r) .config 2>/dev/null || make defconfig

    log "Applying debug configuration..."

    local opts=(
        # Core debug
        CONFIG_DEBUG_KERNEL=y
        CONFIG_DEBUG_INFO=y
        CONFIG_DEBUG_INFO_DWARF5=y
        CONFIG_GDB_SCRIPTS=y
        CONFIG_FRAME_POINTER=y
        CONFIG_KALLSYMS=y
        CONFIG_KALLSYMS_ALL=y
        CONFIG_DEBUG_BUGVERBOSE=y
        CONFIG_MAGIC_SYSRQ=y
        CONFIG_MAGIC_SYSRQ_DEFAULT_ENABLE=1

        # KGDB
        CONFIG_KGDB=y
        CONFIG_KGDB_SERIAL_CONSOLE=y
        CONFIG_KGDB_KDB=y
        CONFIG_KDB_KEYBOARD=y

        # Memory sanitizers
        CONFIG_KASAN=y
        CONFIG_KASAN_INLINE=y
        CONFIG_KFENCE=y
        CONFIG_UBSAN=y
        CONFIG_UBSAN_BOUNDS=y
        CONFIG_KMSAN=y
        CONFIG_DEBUG_SLAB=y
        CONFIG_SLUB_DEBUG=y
        CONFIG_DEBUG_PAGEALLOC=y
        CONFIG_PAGE_POISONING=y
        CONFIG_DEBUG_OBJECTS=y
        CONFIG_DEBUG_OBJECTS_FREE=y
        CONFIG_DEBUG_OBJECTS_TIMERS=y
        CONFIG_DEBUG_OBJECTS_WORK=y

        # Lock debugging
        CONFIG_PROVE_LOCKING=y
        CONFIG_LOCKDEP=y
        CONFIG_DEBUG_LOCKDEP=y
        CONFIG_LOCK_STAT=y
        CONFIG_DEBUG_SPINLOCK=y
        CONFIG_DEBUG_MUTEXES=y
        CONFIG_DEBUG_RWSEMS=y
        CONFIG_DEBUG_ATOMIC_SLEEP=y

        # Concurrency
        CONFIG_KCSAN=y

        # RCU
        CONFIG_PROVE_RCU=y
        CONFIG_RCU_TRACE=y
        CONFIG_RCU_EQS_DEBUG=y

        # Stack
        CONFIG_DEBUG_STACK_USAGE=y
        CONFIG_UNWINDER_FRAME_POINTER=y

        # Ftrace / tracing
        CONFIG_FTRACE=y
        CONFIG_FUNCTION_TRACER=y
        CONFIG_FUNCTION_GRAPH_TRACER=y
        CONFIG_DYNAMIC_FTRACE=y
        CONFIG_STACK_TRACER=y
        CONFIG_IRQSOFF_TRACER=y
        CONFIG_PREEMPT_TRACER=y
        CONFIG_TRACER_SNAPSHOT=y
        CONFIG_HIST_TRIGGERS=y
        CONFIG_TRACE_EVENT_INJECT=y
        CONFIG_TRACEPOINTS=y
        CONFIG_TRACING=y
        CONFIG_KPROBE_EVENTS=y
        CONFIG_UPROBE_EVENTS=y

        # kprobes / uprobes
        CONFIG_KPROBES=y
        CONFIG_UPROBES=y

        # eBPF
        CONFIG_BPF=y
        CONFIG_BPF_SYSCALL=y
        CONFIG_BPF_JIT=y
        CONFIG_BPF_JIT_ALWAYS_ON=y
        CONFIG_BPF_EVENTS=y
        CONFIG_DEBUG_INFO_BTF=y

        # perf
        CONFIG_PERF_EVENTS=y

        # Network debug
        CONFIG_NET_DROP_MONITOR=y
        CONFIG_NETCONSOLE=y
        CONFIG_NETCONSOLE_DYNAMIC=y
        CONFIG_DEBUG_NET=y
        CONFIG_NF_LOG_ALL_NETNS=y

        # KUnit testing
        CONFIG_KUNIT=y
        CONFIG_KUNIT_DEBUGFS=y

        # Fuzzing
        CONFIG_KCOV=y
        CONFIG_KCOV_ENABLE_COMPARISONS=y

        # Panic behavior
        CONFIG_PANIC_ON_OOPS=y
        CONFIG_SOFTLOCKUP_DETECTOR=y
        CONFIG_HARDLOCKUP_DETECTOR=y
        CONFIG_DETECT_HUNG_TASK=y
    )

    for opt in "${opts[@]}"; do
        key="${opt%%=*}"
        val="${opt##*=}"
        scripts/config --set-val "$key" "$val" 2>/dev/null || true
    done

    # Disable options that interfere with debugging
    scripts/config --disable CONFIG_RANDOMIZE_BASE   # disable KASLR
    scripts/config --disable CONFIG_CC_OPTIMIZE_FOR_PERFORMANCE
    scripts/config --enable  CONFIG_CC_OPTIMIZE_FOR_DEBUGGING

    log "Resolving config dependencies..."
    make olddefconfig

    log "Config ready. Build with:"
    echo -e "  ${CYAN}cd $KERNEL_SRC && make -j\$(nproc)${NC}"
}

# =============================================================================
# CREATE DISK IMAGES
# =============================================================================

create_disks() {
    hdr "Creating disk images"

    for disk in "$DISK_24" "$DISK_26"; do
        if [[ -f "$disk" ]]; then
            warn "Disk already exists: $disk (skipping)"
        else
            log "Creating 20G disk: $disk"
            qemu-img create -f qcow2 "$disk" 20G
            log "Created: $disk"
        fi
    done
}

# =============================================================================
# INSTALL MODE — Boot from ISO into disk image
# =============================================================================

mode_install() {
    hdr "Install Mode"
    local iso=""
    local disk=""

    echo ""
    echo "Which ISO to install?"
    echo "  1) Ubuntu 24.04.4 → $DISK_24"
    echo "  2) Ubuntu 26.04   → $DISK_26"
    read -rp "Choice [1/2]: " choice

    case "$choice" in
        1) iso="$ISO_24"; disk="$DISK_24" ;;
        2) iso="$ISO_26"; disk="$DISK_26" ;;
        *) err "Invalid choice" ;;
    esac

    [[ -f "$iso" ]]  || err "ISO not found: $iso"
    [[ -f "$disk" ]] || { warn "Disk not found, creating..."; qemu-img create -f qcow2 "$disk" 20G; }

    log "Booting installer: $iso → $disk"
    info "Complete the install normally, then power off the VM"

    qemu-system-x86_64 \
        $KVM_FLAG \
        -m "$RAM" \
        -smp "$CPUS" \
        -hda "$disk" \
        -cdrom "$iso" \
        -boot order=dc \
        -netdev user,id=net0,hostfwd=tcp::"$SSH_HOST_PORT"-:22 \
        -device virtio-net-pci,netdev=net0 \
        -vga virtio \
        -display gtk \
        -monitor telnet:127.0.0.1:"$MONITOR_PORT",server,nowait \
        -name "Ubuntu-Install"

    log "Install complete. Now run: $0 boot"
}

# =============================================================================
# BOOT MODE — Normal boot with custom kernel, all debug enabled
# =============================================================================

mode_boot() {
    hdr "Boot Mode — Custom Kernel + Full Debug Stack"

    local disk=""
    echo ""
    echo "Which disk?"
    echo "  1) Ubuntu 24.04 ($DISK_24)"
    echo "  2) Ubuntu 26.04 ($DISK_26)"
    read -rp "Choice [1/2]: " choice
    case "$choice" in
        1) disk="$DISK_24" ;;
        2) disk="$DISK_26" ;;
        *) err "Invalid" ;;
    esac

    [[ -f "$disk" ]]       || err "Disk not found: $disk  (run: $0 install)"
    [[ -f "$KERNEL_IMG" ]] || err "Kernel image not found: $KERNEL_IMG  (run: make -j\$(nproc) in kernel src)"

    log "Booting with custom kernel + full debug..."
    info "SSH:     ssh -p $SSH_HOST_PORT user@localhost"
    info "Monitor: telnet 127.0.0.1 $MONITOR_PORT"
    info "Shared:  $SHARED_DIR → /mnt/share (inside guest)"

    KERNEL_APPEND=(
        "root=/dev/sda1"
        "rw"
        "console=ttyS0,115200"
        "console=tty0"

        # Disable KASLR — required for GDB symbol matching
        "nokaslr"

        # Show all printk levels
        "loglevel=8"
        "ignore_loglevel"

        # Dynamic debug — enable net subsystem debug prints at boot
        "dyndbg='^file net/ipv4/.*$|^file net/core/.*$|^file net/ethernet/.*$ +p'"

        # Panic behavior
        "oops=panic"
        "panic=10"
        "softlockup_panic=1"
        "hardlockup_panic=1"

        # Disable CPU mitigations (faster in VM, never do in production)
        "mitigations=off"
        "nopti"
        "nospectre_v2"

        # Disable SMEP/SMAP for easier kernel exploit testing
        "nosmep"
        "nosmap"

        # KFENCE sample interval (ms) — lower = more frequent checks
        "kfence.sample_interval=100"

        # Netconsole — send kernel logs to host
        # Format: src_port@src_ip/iface,dst_port@dst_ip/dst_mac
        "netconsole=6665@10.0.2.15/eth0,$NETCONS_PORT@$HOST_IP/"
    )

    qemu-system-x86_64 \
        $KVM_FLAG \
        -m "$RAM" \
        -smp "$CPUS" \
        -hda "$disk" \
        -kernel "$KERNEL_IMG" \
        -append "${KERNEL_APPEND[*]}" \
        \
        -netdev user,id=net0,\
hostfwd=tcp::"$SSH_HOST_PORT"-:22,\
hostfwd=udp::"$NETCONS_PORT"-:"$NETCONS_PORT" \
        -device virtio-net-pci,netdev=net0 \
        \
        -virtfs local,path="$SHARED_DIR",mount_tag=host_share,\
security_model=mapped-xattr,id=share0 \
        \
        -serial mon:stdio \
        -monitor telnet:127.0.0.1:"$MONITOR_PORT",server,nowait \
        -vga virtio \
        -display gtk \
        -name "KernelDebug-Boot"
}

# =============================================================================
# DEBUG MODE — KGDB over serial, GDB auto-connects
# =============================================================================

mode_debug() {
    hdr "Debug Mode — KGDB + GDB"

    [[ -f "$KERNEL_IMG" ]] || err "Kernel image not found: $KERNEL_IMG"

    local disk="$DISK_24"
    [[ -f "$DISK_26" ]] && disk="$DISK_26"
    [[ -f "$disk" ]]    || err "No disk image found. Run: $0 install"

    local vmlinux="${KERNEL_SRC}/vmlinux"
    [[ -f "$vmlinux" ]] || err "vmlinux not found: $vmlinux (need kernel built with debug info)"

    KERNEL_APPEND=(
        "root=/dev/sda1"
        "rw"
        "console=ttyS0,115200"
        "nokaslr"
        "loglevel=8"
        "ignore_loglevel"
        "oops=panic"
        "panic=0"           # don't reboot on panic in debug mode
        "mitigations=off"

        # KGDB — wait for debugger before booting
        "kgdboc=ttyS1,115200"
        "kgdbwait"          # halt at boot until GDB connects — remove after first setup
    )

    log "Starting QEMU with KGDB on port $GDB_PORT..."
    log "GDB serial mapped: localhost:$GDB_PORT"

    # Launch QEMU in background
    qemu-system-x86_64 \
        $KVM_FLAG \
        -m "$RAM" \
        -smp "$CPUS" \
        -hda "$disk" \
        -kernel "$KERNEL_IMG" \
        -append "${KERNEL_APPEND[*]}" \
        \
        -serial mon:stdio \
        -serial tcp::$GDB_PORT,server,nowait \   # ttyS1 → GDB
        \
        -netdev user,id=net0,hostfwd=tcp::"$SSH_HOST_PORT"-:22 \
        -device virtio-net-pci,netdev=net0 \
        -monitor telnet:127.0.0.1:"$MONITOR_PORT",server,nowait \
        -display none \
        -name "KernelDebug-KGDB" &

    QEMU_PID=$!
    log "QEMU PID: $QEMU_PID"

    sleep 3

    log "Launching GDB..."
    info "Useful GDB commands:"
    info "  (gdb) break tcp_rcv_established   — set breakpoint"
    info "  (gdb) break ip_rcv                — break on IP receive"
    info "  (gdb) continue                    — run"
    info "  (gdb) bt                          — backtrace"
    info "  (gdb) p skb->len                  — print variable"
    info "  (gdb) p *tcp_hdr(skb)             — print struct"
    info "  (gdb) x/16xb skb->data            — hex dump"
    info "  (gdb) info locals                 — all local vars"
    info "  (gdb) lx-dmesg                    — kernel log (needs GDB scripts)"
    info "  (gdb) lx-ps                       — process list"
    info "  (gdb) apropos lx                  — all kernel GDB helpers"

    gdb "$vmlinux" \
        -ex "set architecture i386:x86-64" \
        -ex "set print pretty on" \
        -ex "set pagination off" \
        -ex "add-auto-load-safe-path ${KERNEL_SRC}" \
        -ex "source ${KERNEL_SRC}/scripts/gdb/vmlinux-gdb.py" \
        -ex "target remote :${GDB_PORT}" \
        -ex "echo Connected to kernel. Type 'continue' to boot.\n"
}

# =============================================================================
# NETLOG MODE — Listen for netconsole kernel logs on host
# =============================================================================

mode_netlog() {
    hdr "Netconsole Log Listener"
    info "Listening for kernel logs from guest on UDP port $NETCONS_PORT"
    info "Kernel messages will appear here in real time"
    info "Press Ctrl+C to stop"
    echo ""
    echo -e "${CYAN}--- Kernel Log Stream ---${NC}"

    # Listen with timestamp prefix
    nc -u -l -p "$NETCONS_PORT" | while IFS= read -r line; do
        echo "[$(date '+%H:%M:%S.%3N')] $line"
    done
}

# =============================================================================
# KUNIT MODE — Run in-kernel unit tests for net subsystem
# =============================================================================

mode_kunit() {
    hdr "KUnit Test Mode"

    [[ -d "$KERNEL_SRC" ]] || err "Kernel source not found: $KERNEL_SRC"
    cd "$KERNEL_SRC"

    info "Available net KUnit tests:"
    find . -name "*_test.c" -path "*/net/*" | sed 's|./||'

    echo ""
    log "Running KUnit tests via UML (User Mode Linux) — no VM needed"

    # Build UML (runs kernel as a normal process)
    make ARCH=um -j$(nproc) \
        KCONFIG_CONFIG=.config \
        O=build-uml \
        2>&1 | tail -20

    # Run all net KUnit tests
    ./build-uml/linux \
        mem=512M \
        kunit.enable=1 \
        2>&1 | grep -E "PASSED|FAILED|ERROR|kunit|net" | head -100

    log "Done. For specific test suite:"
    echo "  ./linux kunit.filter_glob='net.*'"
}

# =============================================================================
# FUZZ MODE — Boot with KCOV + syzkaller-style setup
# =============================================================================

mode_fuzz() {
    hdr "Fuzz Mode — KCOV + Coverage Tracing"

    [[ -f "$KERNEL_IMG" ]] || err "Kernel image not found: $KERNEL_IMG"

    local disk="$DISK_24"

    KERNEL_APPEND=(
        "root=/dev/sda1"
        "rw"
        "console=ttyS0,115200"
        "nokaslr"
        "loglevel=7"
        "oops=panic"
        "panic=1"          # fast reboot on crash during fuzzing
        "mitigations=off"

        # KCOV settings
        "kcov.enable=1"
    )

    log "Booting in fuzz mode with KCOV coverage..."
    info "From inside guest — use KCOV interface:"
    info "  fd = open('/sys/kernel/debug/kcov', O_RDWR)"
    info "  ioctl(fd, KCOV_INIT_TRACE, 1024*1024)"
    info "  ioctl(fd, KCOV_ENABLE, KCOV_TRACE_PC)"
    info "  ... do syscalls ..."
    info "  ioctl(fd, KCOV_DISABLE, 0)"

    qemu-system-x86_64 \
        $KVM_FLAG \
        -m "$RAM" \
        -smp "$CPUS" \
        -hda "$disk" \
        -kernel "$KERNEL_IMG" \
        -append "${KERNEL_APPEND[*]}" \
        -netdev user,id=net0,hostfwd=tcp::"$SSH_HOST_PORT"-:22 \
        -device virtio-net-pci,netdev=net0 \
        -serial mon:stdio \
        -display none \
        -name "KernelDebug-Fuzz"
}

# =============================================================================
# FTRACE HELPER — Enable specific net traces from host via SSH
# =============================================================================

mode_ftrace() {
    hdr "ftrace Quick Setup (run inside guest)"

    cat << 'FTRACE_SCRIPT'
#!/bin/bash
# Run this INSIDE the QEMU guest after boot
# Or copy via: scp -P 2222 this_script user@localhost:~/

TRACE=/sys/kernel/debug/tracing
echo nop > $TRACE/current_tracer
echo > $TRACE/trace
echo > $TRACE/set_ftrace_filter

echo "Choose trace mode:"
echo "  1) TCP send path"
echo "  2) TCP receive path"
echo "  3) IP layer"
echo "  4) Full net stack (verbose)"
echo "  5) Packet drops"
echo "  6) Custom function"
read -p "Choice: " choice

case $choice in
  1)
    echo 'tcp_sendmsg tcp_push tcp_write_xmit tcp_transmit_skb' > $TRACE/set_ftrace_filter
    ;;
  2)
    echo 'tcp_v4_rcv tcp_v4_do_rcv tcp_rcv_established tcp_data_queue tcp_ack' > $TRACE/set_ftrace_filter
    ;;
  3)
    echo 'ip_rcv ip_rcv_finish ip_local_deliver ip_output ip_queue_xmit' > $TRACE/set_ftrace_filter
    ;;
  4)
    echo 'tcp_* ip_* udp_* dev_* netif_*' > $TRACE/set_ftrace_filter
    ;;
  5)
    echo 'kfree_skb nf_hook_slow' > $TRACE/set_ftrace_filter
    ;;
  6)
    read -p "Function pattern: " fn
    echo "$fn" > $TRACE/set_ftrace_filter
    ;;
esac

echo function_graph > $TRACE/current_tracer
echo 1 > $TRACE/options/func-stacktrace
echo 1 > $TRACE/tracing_on

echo "[ftrace] Tracing active. Do network activity now."
echo "Press Enter to stop and show results..."
read

echo 0 > $TRACE/tracing_on
echo ""
echo "=== TRACE OUTPUT ==="
cat $TRACE/trace | head -200
FTRACE_SCRIPT
}

# =============================================================================
# SYSRQ HELPERS — Fire from QEMU monitor
# =============================================================================

mode_sysrq() {
    hdr "SysRq via QEMU Monitor"
    info "Connect to monitor: telnet 127.0.0.1 $MONITOR_PORT"
    echo ""
    echo "Commands to run in QEMU monitor:"
    echo ""
    echo "  sendkey alt-sysrq-h   # help"
    echo "  sendkey alt-sysrq-t   # dump thread state"
    echo "  sendkey alt-sysrq-l   # backtrace all CPUs"
    echo "  sendkey alt-sysrq-d   # show all lock holders"
    echo "  sendkey alt-sysrq-w   # tasks in uninterruptible sleep"
    echo "  sendkey alt-sysrq-m   # memory info"
    echo "  sendkey alt-sysrq-g   # enter KGDB"
    echo "  sendkey alt-sysrq-c   # trigger crash / kdump"
    echo "  sendkey alt-sysrq-b   # immediate reboot"
    echo ""
    info "Or enable from inside guest:"
    echo "  echo 1 > /proc/sys/kernel/sysrq"
    echo "  echo g > /proc/sysrq-trigger   # enter KGDB"
    echo "  echo t > /proc/sysrq-trigger   # dump threads"
}

# =============================================================================
# GUEST SETUP SCRIPT — Copy & run inside VM after first boot
# =============================================================================

gen_guest_setup() {
    hdr "Generating guest setup script"

    cat > "$SHARED_DIR/guest-setup.sh" << 'GUEST_EOF'
#!/usr/bin/env bash
# Run this ONCE inside the QEMU guest after install
# Sets up all debug/trace tools inside the VM

set -e
echo "[+] Installing kernel debug tools..."

sudo apt update -qq
sudo apt install -y \
    bpftrace \
    linux-tools-common \
    linux-tools-generic \
    bpfcc-tools \
    python3-bpfcc \
    trace-cmd \
    kernelshark \
    strace \
    ltrace \
    netcat-openbsd \
    gdb \
    crash \
    kdump-tools \
    netconsole \
    iproute2 \
    tcpdump \
    tshark \
    nmap \
    curl wget \
    build-essential \
    linux-headers-$(uname -r)

echo "[+] Mounting shared folder from host..."
sudo mkdir -p /mnt/share
sudo mount -t 9p -o trans=virtio host_share /mnt/share
echo "9p host_share /mnt/share 9p trans=virtio,nofail 0 0" | sudo tee -a /etc/fstab

echo "[+] Enabling all SysRq keys..."
echo 1 | sudo tee /proc/sys/kernel/sysrq
echo 'kernel.sysrq = 1' | sudo tee /etc/sysctl.d/99-sysrq.conf

echo "[+] Setting kernel log level to debug..."
echo 8 | sudo tee /proc/sys/kernel/printk

echo "[+] Enabling dynamic debug for net subsystem..."
sudo mount -t debugfs none /sys/kernel/debug 2>/dev/null || true
echo 'file net/ipv4/tcp.c +p'     | sudo tee /sys/kernel/debug/dynamic_debug/control
echo 'file net/ipv4/ip_input.c +p'| sudo tee /sys/kernel/debug/dynamic_debug/control
echo 'file net/core/dev.c +p'     | sudo tee /sys/kernel/debug/dynamic_debug/control

echo "[+] Verifying debug infrastructure..."
echo "  ftrace:   $(ls /sys/kernel/debug/tracing/available_tracers)"
echo "  kprobes:  $(cat /sys/bus/event_source/devices/kprobe/type 2>/dev/null || echo 'check /sys/kernel/debug')"
echo "  BPF BTF:  $(ls /sys/kernel/btf/vmlinux 2>/dev/null && echo OK || echo MISSING)"
echo "  KASAN:    $(dmesg | grep -c KASAN || echo 0) reports"

echo ""
echo "[+] Guest setup complete!"
echo "    Kernel: $(uname -r)"
echo "    Share:  /mnt/share"
GUEST_EOF

    chmod +x "$SHARED_DIR/guest-setup.sh"
    log "Guest setup script written to: $SHARED_DIR/guest-setup.sh"
    info "After booting the VM, run:"
    echo "  mount -t 9p -o trans=virtio host_share /mnt/share"
    echo "  bash /mnt/share/guest-setup.sh"
}

# =============================================================================
# STATUS — Show what's running
# =============================================================================

mode_status() {
    hdr "Status"

    echo ""
    echo -e "${BOLD}QEMU processes:${NC}"
    pgrep -a qemu-system || echo "  none running"

    echo ""
    echo -e "${BOLD}Listening ports:${NC}"
    ss -tlnup 2>/dev/null | grep -E "$SSH_HOST_PORT|$GDB_PORT|$MONITOR_PORT|$NETCONS_PORT" || echo "  none"

    echo ""
    echo -e "${BOLD}Disk images:${NC}"
    for d in "$DISK_24" "$DISK_26"; do
        if [[ -f "$d" ]]; then
            size=$(qemu-img info "$d" 2>/dev/null | grep "disk size" | awk '{print $3, $4}')
            echo "  $d — $size"
        else
            echo "  $d — NOT FOUND"
        fi
    done

    echo ""
    echo -e "${BOLD}Kernel image:${NC}"
    if [[ -f "$KERNEL_IMG" ]]; then
        echo "  $KERNEL_IMG"
        file "$KERNEL_IMG"
    else
        echo "  NOT FOUND: $KERNEL_IMG"
    fi

    echo ""
    echo -e "${BOLD}Shared folder:${NC} $SHARED_DIR"
    ls "$SHARED_DIR" 2>/dev/null || echo "  empty"
}

# =============================================================================
# HELP
# =============================================================================

mode_help() {
    echo ""
    echo -e "${BOLD}${CYAN}kdbg-launch.sh — Linux Kernel Debug QEMU Launcher${NC}"
    echo ""
    echo -e "${BOLD}WORKFLOW:${NC}"
    echo "  1. Edit CONFIG section at top of this script"
    echo "  2. ./kdbg-launch.sh config    # apply all debug Kconfig options"
    echo "  3. cd $KERNEL_SRC && make -j\$(nproc)"
    echo "  4. ./kdbg-launch.sh install   # install Ubuntu into disk image"
    echo "  5. ./kdbg-launch.sh boot      # boot with your kernel"
    echo "  6. (inside guest) bash /mnt/share/guest-setup.sh"
    echo ""
    echo -e "${BOLD}MODES:${NC}"
    printf "  %-12s %s\n" "config"   "Apply all debug Kconfig options to kernel source"
    printf "  %-12s %s\n" "install"  "Boot ISO installer into a new disk image"
    printf "  %-12s %s\n" "boot"     "Boot custom kernel with full debug stack"
    printf "  %-12s %s\n" "debug"    "Boot with KGDB + auto-launch GDB on host"
    printf "  %-12s %s\n" "netlog"   "Listen for netconsole kernel logs from guest"
    printf "  %-12s %s\n" "ftrace"   "Print ftrace setup script to run inside guest"
    printf "  %-12s %s\n" "kunit"    "Run KUnit net subsystem tests via UML"
    printf "  %-12s %s\n" "fuzz"     "Boot with KCOV coverage for fuzzing"
    printf "  %-12s %s\n" "sysrq"    "Show SysRq commands via QEMU monitor"
    printf "  %-12s %s\n" "setup"    "Generate guest-setup.sh into shared folder"
    printf "  %-12s %s\n" "status"   "Show running VMs, ports, disk images"
    printf "  %-12s %s\n" "help"     "Show this message"
    echo ""
    echo -e "${BOLD}QUICK CONNECTIONS (while VM is running):${NC}"
    echo "  SSH into guest:    ssh -p $SSH_HOST_PORT user@localhost"
    echo "  QEMU monitor:      telnet 127.0.0.1 $MONITOR_PORT"
    echo "  GDB (debug mode):  gdb vmlinux -ex 'target remote :$GDB_PORT'"
    echo "  Kernel logs:       $0 netlog"
    echo ""
    echo -e "${BOLD}INSIDE GUEST — net debug quick commands:${NC}"
    echo "  dmesg -w                                 # live kernel log"
    echo "  cat /sys/kernel/debug/tracing/trace_pipe # live ftrace"
    echo "  bpftrace -e 'kprobe:tcp_sendmsg { printf(\"%s\\n\", comm); }'"
    echo "  ss -tnp                                  # TCP connections"
    echo "  cat /proc/net/tcp                        # raw TCP table"
    echo "  cat /proc/net/netstat | grep -i retrans  # retransmit counters"
    echo "  echo g > /proc/sysrq-trigger             # drop into KGDB"
    echo ""
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    check_deps

    local mode="${1:-help}"

    case "$mode" in
        config)   configure_kernel ;;
        install)  create_disks; mode_install ;;
        boot)     mode_boot ;;
        debug)    mode_debug ;;
        netlog)   mode_netlog ;;
        ftrace)   mode_ftrace ;;
        kunit)    mode_kunit ;;
        fuzz)     mode_fuzz ;;
        sysrq)    mode_sysrq ;;
        setup)    gen_guest_setup ;;
        status)   mode_status ;;
        help|--help|-h) mode_help ;;
        *) err "Unknown mode: $mode. Run: $0 help" ;;
    esac
}

main "$@"