#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-only
#
# debug_nf_pkt_inspector.sh — debug, trace, and troubleshoot guide
#
# Covers:
#   1. ftrace — function tracer, kprobe, event tracer
#   2. dynamic debug (pr_debug activation)
#   3. KASAN (kernel address sanitizer) — detect the buggy module's issues
#   4. perf — performance profiling the hook
#   5. /proc/net, /proc/net/nf_pkt_inspector, /sys/kernel/debug/tracing/
#   6. kgdb connection setup (over virtio serial in KVM)
#   7. bpftrace one-liners for live hook tracing
#
# Run each section as needed — most require root.

set -euo pipefail

readonly MOD="nf_pkt_inspector"
readonly TRACEFS="/sys/kernel/debug/tracing"
readonly DDEBUG="/sys/kernel/debug/dynamic_debug/control"

info()  { printf '\033[1;33m[INFO]\033[0m  %s\n' "$1"; }
title() { printf '\n\033[1;35m══ %s ══\033[0m\n' "$1"; }
cmd()   { printf '\033[0;36m$ %s\033[0m\n' "$1"; eval "$1"; }

require_root() { [[ $EUID -eq 0 ]] || { echo "Need root"; exit 1; }; }

# ─────────────────────────────────────────────────────────────────────────────
# 1. DYNAMIC DEBUG — activate pr_debug() output
# ─────────────────────────────────────────────────────────────────────────────
enable_dynamic_debug() {
    title "Dynamic Debug"
    info "pr_debug() is compiled out by default."
    info "To activate at runtime (no recompile needed):"
    echo
    # Enable all pr_debug lines in our module
    cmd "echo 'module ${MOD} +p' > ${DDEBUG}"
    cmd "echo 'module ${MOD} +pflmt' > ${DDEBUG}"  # file, line, module, thread
    info "Now pr_debug() in nf_pkt_hook() emits to dmesg."
    info "Verify: dmesg | grep nf_pkt"
    echo
    cmd "cat ${DDEBUG} | grep ${MOD}"
    echo
    info "To disable: echo 'module ${MOD} -p' > ${DDEBUG}"
}

# ─────────────────────────────────────────────────────────────────────────────
# 2. FTRACE — trace the hook function call
# ─────────────────────────────────────────────────────────────────────────────
ftrace_hook_function() {
    title "ftrace: trace nf_pkt_hook"
    info "ftrace lives under ${TRACEFS}/"
    info "Documentation/trace/ftrace.rst"
    echo

    # Save current tracer
    local saved_tracer
    saved_tracer=$(cat "${TRACEFS}/current_tracer")

    # Set function tracer
    cmd "echo 0 > ${TRACEFS}/tracing_on"
    cmd "echo function > ${TRACEFS}/current_tracer"

    # Filter to only our hook function (reduces overhead enormously)
    cmd "echo 'nf_pkt_hook' > ${TRACEFS}/set_ftrace_filter"

    # Also trace nf_register_net_hook to see registration
    cmd "echo 'nf_register_net_hook' >> ${TRACEFS}/set_ftrace_filter"

    cmd "echo 1 > ${TRACEFS}/tracing_on"
    info "Generating 3 packets..."
    curl -s --connect-timeout 1 "http://127.0.0.1:65432/" &>/dev/null || true
    sleep 0.3
    cmd "echo 0 > ${TRACEFS}/tracing_on"

    echo
    info "Trace output (last 20 lines):"
    tail -20 "${TRACEFS}/trace" 2>/dev/null || echo "(trace file empty)"
    echo

    # Restore
    echo "$saved_tracer" > "${TRACEFS}/current_tracer"
    echo > "${TRACEFS}/set_ftrace_filter"
    echo 1 > "${TRACEFS}/tracing_on"
}

# ─────────────────────────────────────────────────────────────────────────────
# 3. KPROBE — trace with kprobe events (no kernel recompile)
# ─────────────────────────────────────────────────────────────────────────────
kprobe_trace() {
    title "kprobe events on nf_pkt_hook"
    info "kprobe_events: attach to any kernel symbol without recompile"
    info "Documentation/trace/kprobetrace.rst"
    echo

    # Syntax: p:name symbol [fetchargs]
    # %di = first arg (void *priv)  %si = second arg (struct sk_buff *skb)
    # +0(%si) = skb->len (offset 0 in sk_buff — verify in include/linux/skbuff.h)
    cmd "echo 'p:hit_hook nf_pkt_hook' > ${TRACEFS}/kprobe_events"
    cmd "echo 1 > ${TRACEFS}/events/kprobes/hit_hook/enable"
    cmd "echo 1 > ${TRACEFS}/tracing_on"

    info "Generating traffic..."
    hping3 -S -c 5 -p 80 --fast 127.0.0.1 &>/dev/null 2>&1 || true
    sleep 0.3

    cmd "echo 0 > ${TRACEFS}/tracing_on"
    cmd "echo 0 > ${TRACEFS}/events/kprobes/hit_hook/enable"

    info "kprobe hits:"
    grep "hit_hook" "${TRACEFS}/trace" | head -10 || echo "(no hits)"

    # Cleanup
    echo "-:hit_hook" >> "${TRACEFS}/kprobe_events"
    echo > "${TRACEFS}/kprobe_events"
    echo 1 > "${TRACEFS}/tracing_on"
}

# ─────────────────────────────────────────────────────────────────────────────
# 4. NETFILTER TRACE EVENT — built-in nf tracing
# ─────────────────────────────────────────────────────────────────────────────
nf_trace_events() {
    title "netfilter trace events"
    info "The kernel has built-in nf trace events under events/netfilter/"
    echo

    local nf_event_dir="${TRACEFS}/events/netfilter"
    if [[ -d "$nf_event_dir" ]]; then
        cmd "ls ${nf_event_dir}/"
        cmd "echo 1 > ${nf_event_dir}/enable"
        cmd "echo 1 > ${TRACEFS}/tracing_on"
        sleep 0.2
        # generate one packet
        curl -s --connect-timeout 1 "http://127.0.0.1:65432/" &>/dev/null || true
        sleep 0.2
        cmd "echo 0 > ${TRACEFS}/tracing_on"
        cmd "echo 0 > ${nf_event_dir}/enable"
        head -20 "${TRACEFS}/trace" || true
    else
        info "events/netfilter not available (need CONFIG_NF_TABLES_TRACE or NETFILTER_XT_TARGET_TRACE)"
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
# 5. PERF — profile the hook
# ─────────────────────────────────────────────────────────────────────────────
perf_profile() {
    title "perf: profile netfilter hook overhead"
    info "Requires: perf (linux-tools-$(uname -r))"
    echo

    info "Record 5s of kernel call graph while sending SYNs:"
    cat <<'CMDS'
# In terminal 1 (background traffic):
    hping3 -S -p 80 --faster 127.0.0.1 &
    HPING_PID=$!

# In terminal 2:
    perf record -ag -F 999 --call-graph dwarf -- sleep 5

# Stop hping:
    kill $HPING_PID

# Analyse:
    perf report --stdio --sort comm,dso,symbol | head -60
    perf report --no-children --stdio | grep -A5 nf_pkt_hook

# Check latency with perf trace (syscall/softirq latency):
    perf trace -e 'net:*' sleep 2

# For counter-based profiling of our hook:
    perf stat -e cycles,instructions,cache-misses,cache-references \
        -p $(cat /proc/$(pidof hping3 2>/dev/null || echo 1)/stat 2>/dev/null | awk '{print $1}') \
        sleep 2
CMDS
    echo
    info "Run perf commands above manually in your test VM."
}

# ─────────────────────────────────────────────────────────────────────────────
# 6. KASAN — detecting bugs in the buggy module
# ─────────────────────────────────────────────────────────────────────────────
kasan_demo() {
    title "KASAN: detecting the buggy module's bugs"
    info "Requires: kernel built with CONFIG_KASAN=y, CONFIG_KASAN_INLINE=y"
    info "Check: grep CONFIG_KASAN /boot/config-\$(uname -r)"
    echo

    cat <<'GUIDE'
# ── Kernel config for KASAN VM ──────────────────────────────────────
# In your VM2 (debugging kernel), add to .config:
#
#   CONFIG_KASAN=y
#   CONFIG_KASAN_INLINE=y          # faster than outline
#   CONFIG_KASAN_STACK=1           # detect stack bugs too
#   CONFIG_UBSAN=y                 # undefined behaviour sanitizer
#   CONFIG_UBSAN_BOUNDS=y          # array out-of-bounds (BUG2 trigger)
#   CONFIG_LOCKDEP=y               # lock ordering bugs
#   CONFIG_DEBUG_KERNEL=y
#   CONFIG_DEBUG_SPINLOCK=y
#   CONFIG_SLUB_DEBUG=y
#
# Build the kernel:
#   make menuconfig        # navigate: Kernel hacking → Memory Debugging
#   make -j$(nproc)
#   make modules_install
#   make install

# ── Reproduce BUG1 (stale iph pointer) ──────────────────────────────
# Load the buggy module, send fragmented packets to force pskb_may_pull
# to reallocate skb->head:
#
    sudo insmod nf_pkt_inspector_buggy.ko
    # Send TCP SYNs with IP options (increases header size, forces realloc)
    sudo hping3 -S -p 80 --ipopt 01 -c 20 127.0.0.1
    dmesg | grep -A 20 "KASAN:"
#
# Expected KASAN output (BUG1):
#   ==================================================================
#   BUG: KASAN: use-after-free in nf_pkt_hook_buggy+0x...
#   Read of size 2 at addr ffff888... by task softirq/0
#   Call Trace:
#     nf_pkt_hook_buggy+0x...
#     nf_hook_thresh+0x...
#     ip_rcv+0x...
#   Allocated by task 0:
#     skb_try_coalesce+0x... (old head)
#   Freed by task 0:
#     pskb_expand_head+0x...
#   ==================================================================

# ── Reproduce BUG2 (array overflow) ─────────────────────────────────
# Send 65+ SYN packets to overflow the syn_ring[64] array:
#
    sudo hping3 -S -p 80 --faster -c 70 127.0.0.1
    dmesg | grep -A 10 "KASAN:\|UBSAN:"
#
# Expected UBSAN output (BUG2):
#   UBSAN: array-index-out-of-bounds in nf_pkt_inspector_buggy.c:97:15
#   index 64 is out of range for type 'struct syn_entry [64]'
#
# Expected KASAN output (if global redzones enabled):
#   BUG: KASAN: global-out-of-bounds in nf_pkt_hook_buggy+0x...
#   Write of size 10 at addr ffffffff... by task softirq

# ── Fix verification ─────────────────────────────────────────────────
# After applying the fix (see nf_pkt_inspector.c):
    sudo rmmod nf_pkt_inspector_buggy
    sudo insmod nf_pkt_inspector.ko
    sudo hping3 -S -p 80 --faster -c 70 127.0.0.1
    dmesg | tail -5   # should be clean — no KASAN/UBSAN
GUIDE
}

# ─────────────────────────────────────────────────────────────────────────────
# 7. BPFTRACE — live hook tracing without kernel recompile
# ─────────────────────────────────────────────────────────────────────────────
bpftrace_oneliner() {
    title "bpftrace one-liners for netfilter"
    info "Requires: bpftrace >= 0.12, CONFIG_BPF=y, CONFIG_KPROBE_EVENTS=y"
    echo

    cat <<'BPFTRACE'
# ── Count hook calls per second ─────────────────────────────────────
sudo bpftrace -e '
kprobe:nf_pkt_hook {
    @calls = count();
}
interval:s:1 {
    print(@calls);
    delete(@calls);
}
'

# ── Print source IP + dest port for every SYN the hook sees ─────────
# sk_buff layout: skb->head + network_header = struct iphdr
# iph->ihl * 4 = ip header length; tcph starts after that
sudo bpftrace -e '
kprobe:nf_pkt_hook {
    $skb  = (struct sk_buff *)arg1;
    $iph  = (struct iphdr *)($skb->head + $skb->network_header);
    if ($iph->protocol == 6) {          /* IPPROTO_TCP */
        $tcp_off = (uint32)$iph->ihl * 4;
        $tcph = (struct tcphdr *)((uint8 *)$iph + $tcp_off);
        if ($tcph->syn == 1 && $tcph->ack == 0) {
            printf("SYN: %s -> %s:%d\n",
                ntop($iph->saddr),
                ntop($iph->daddr),
                bswap16($tcph->dest));
        }
    }
}
'

# ── Measure hook latency histogram ──────────────────────────────────
sudo bpftrace -e '
kprobe:nf_pkt_hook    { @start[tid] = nsecs; }
kretprobe:nf_pkt_hook {
    if (@start[tid]) {
        @lat_ns = hist(nsecs - @start[tid]);
        delete(@start[tid]);
    }
}
END { print(@lat_ns); }
'

# ── Trace nf_register_net_hook / nf_unregister_net_hook ─────────────
sudo bpftrace -e '
kprobe:nf_register_net_hook   { printf("REGISTER hook\n"); }
kprobe:nf_unregister_net_hook { printf("UNREGISTER hook\n"); }
'

# ── Watch for NF_DROP verdicts ───────────────────────────────────────
sudo bpftrace -e '
kretprobe:nf_pkt_hook {
    if (retval == 0) {   /* NF_DROP = 0 */
        @drops = count();
    }
}
interval:s:1 { print(@drops); delete(@drops); }
'
BPFTRACE
}

# ─────────────────────────────────────────────────────────────────────────────
# 8. KGDB — kernel debugger over serial (KVM virtio-serial)
# ─────────────────────────────────────────────────────────────────────────────
kgdb_setup() {
    title "kgdb: source-level kernel debugging"
    info "Documentation/dev-tools/kgdb.rst"
    echo

    cat <<'KGDB'
# ── KVM VM setup (run on Kali host) ─────────────────────────────────
# Add virtio-serial to your VM definition:
#
    virsh edit <vm-name>
    # Add inside <devices>:
    #   <channel type='unix'>
    #     <source mode='bind' path='/tmp/kgdb.sock'/>
    #     <target type='virtio' name='org.kernel.kgdb.0'/>
    #   </channel>
#
# Or with qemu-system-x86_64:
    qemu-system-x86_64 \
        -kernel /boot/vmlinuz-$(uname -r) \
        -append "kgdboc=ttyS0,115200 kgdbwait nokaslr" \
        -serial unix:/tmp/kgdb.sock,server,nowait \
        [... other flags ...]

# ── Guest kernel boot parameters ────────────────────────────────────
# In /etc/default/grub on the VM:
#   GRUB_CMDLINE_LINUX="kgdboc=ttyS0,115200 nokaslr"
#
# nokaslr: disable KASLR so gdb addresses match
# kgdbwait: stop at early boot (for boot debugging)

# ── Trigger kgdb from inside the VM ─────────────────────────────────
    echo g > /proc/sysrq-trigger   # drops into kgdb

# ── Connect from host ────────────────────────────────────────────────
    gdb vmlinux  # vmlinux from the VM's kernel build
    # In gdb:
    (gdb) target remote /tmp/kgdb.sock
    (gdb) lx-symbols /path/to/nf_pkt_inspector/   # load module symbols
    (gdb) break nf_pkt_hook
    (gdb) continue
    # The hook breaks on the next packet
    (gdb) print *skb
    (gdb) print *iph
    (gdb) x/16xb skb->head + skb->network_header

# ── Useful gdb scripts for kernel (from linux/scripts/gdb/) ─────────
    python import sys; sys.path.insert(0, '/path/to/linux/scripts/gdb')
    # provides: lx-dmesg, lx-ps, lx-lsmod, lx-symbols, lx-iomem

# ── Alternative: crash (post-mortem) ────────────────────────────────
# For post-mortem analysis of a kernel panic/oops:
    # On VM: Enable kdump (apt install kdump-tools)
    # Trigger: echo c > /proc/sysrq-trigger
    # Analyse: crash /path/to/vmlinux /var/crash/$(date +%Y-%m-%d)/vmcore
    #   crash> bt          # backtrace of crashed task
    #   crash> net         # show network state at crash
    #   crash> mod         # show loaded modules
KGDB
}

# ─────────────────────────────────────────────────────────────────────────────
# 9. QUICK DIAGNOSTIC COMMANDS
# ─────────────────────────────────────────────────────────────────────────────
quick_diag() {
    title "Quick diagnostics"
    echo

    info "Module state:"
    lsmod | grep nf_pkt || echo "  (not loaded)"

    info "Proc entry:"
    if [[ -r /proc/net/nf_pkt_inspector ]]; then
        cat /proc/net/nf_pkt_inspector
    else
        echo "  (not present)"
    fi

    info "dmesg (last 10 relevant lines):"
    dmesg | grep -iE "nf_pkt|netfilter" | tail -10 || echo "  (none)"

    info "Active netfilter hooks:"
    # /proc/net/ip_tables_matches shows registered iptables modules
    cat /proc/net/ip_tables_matches 2>/dev/null || true
    # nf_conntrack shows connection tracking state
    if [[ -r /proc/net/nf_conntrack ]]; then
        echo "nf_conntrack entries: $(wc -l < /proc/net/nf_conntrack)"
    fi

    info "Network interfaces:"
    ip -brief link show
}

# ── main ──────────────────────────────────────────────────────────────────────
usage() {
    echo "Usage: $0 [ddebug|ftrace|kprobe|nf_trace|perf|kasan|bpftrace|kgdb|diag|all]"
}

main() {
    require_root

    case "${1:-diag}" in
        ddebug)   enable_dynamic_debug ;;
        ftrace)   ftrace_hook_function ;;
        kprobe)   kprobe_trace ;;
        nf_trace) nf_trace_events ;;
        perf)     perf_profile ;;
        kasan)    kasan_demo ;;
        bpftrace) bpftrace_oneliner ;;
        kgdb)     kgdb_setup ;;
        diag)     quick_diag ;;
        all)
            enable_dynamic_debug
            ftrace_hook_function
            kprobe_trace
            nf_trace_events
            kasan_demo
            bpftrace_oneliner
            kgdb_setup
            quick_diag
            ;;
        *) usage; exit 1 ;;
    esac
}

main "$@"
