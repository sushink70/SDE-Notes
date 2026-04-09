================================================================================
 LINUX KERNEL NET SUBSYSTEM — DOCUMENTATION INDEX & ELITE DEVELOPER ROADMAP
================================================================================

All paths relative to the kernel source tree root.
Online: https://docs.kernel.org/  (built from Documentation/ at HEAD)

================================================================================
TIER 0 — READ BEFORE TOUCHING ANY CODE
================================================================================

Documentation/process/
  submitting-patches.rst          # THE document. Non-negotiable before sending.
  coding-style.rst                # checkpatch.pl enforces this
  kernel-enforcement-statement.rst
  stable-kernel-rules.rst         # when/how to CC stable@vger

Documentation/networking/
  net_dev_ops.rst                 # Every field of net_device_ops explained
  skbuff.rst                      # sk_buff layout, cloning, refcounting
  netdev-features.rst             # NETIF_F_* bitmask semantics
  statistics.rst                  # rtnl_link_stats64, per-cpu stats

Documentation/core-api/
  memory-allocation.rst           # kmalloc vs vmalloc vs alloc_pages
  genericirq.rst                  # IRQ subsystem internals
  workqueue.rst                   # kernel workqueue API
  rcu_concepts.rst                # RCU mental model (MUST read)
  refcount-vs-atomic.rst          # Why refcount_t not atomic_t

Documentation/locking/
  spinlocks.rst                   # spin_lock_irqsave et al
  locktypes.rst                   # mutex vs spinlock vs rwlock
  lockdep-design.rst              # How lockdep tracks lock classes
  seqlock.rst                     # seqlock for readers > writers

================================================================================
TIER 1 — NET SUBSYSTEM INTERNALS
================================================================================

Documentation/networking/
  driver.rst                      # net driver overview and guidelines
  ethtool-netlink.rst             # ethtool over netlink
  napi.rst                        # NAPI architecture, budgets, GRO
  scaling.rst                     # RSS, RPS, XPS, aRFS
  timestamping.rst                # SO_TIMESTAMPING, PTP, HW timestamps
  tc-actions-env.rst              # TC classifier/action pipeline
  xdp/
    xdp-rx-metadata.rst           # XDP metadata kfunc interface
  af_xdp.rst                      # AF_XDP zero-copy sockets
  tproxy.rst                      # transparent proxying

include/linux/netdevice.h         # struct net_device, net_device_ops: THE header
include/linux/skbuff.h            # struct sk_buff: THE other header
include/net/sock.h                # struct sock: socket ↔ skb linkage
net/core/dev.c                    # netif_receive_skb, dev_queue_xmit
net/core/skbuff.c                 # alloc_skb, kfree_skb, skb_clone
net/core/ethtool.c                # ethtool dispatch

REFERENCE DRIVERS (study these in order):
  drivers/net/loopback.c          # simplest: 200 lines, perfect start
  drivers/net/dummy.c             # almost as simple
  drivers/net/veth.c              # veth pair: good NAPI + loopback model
  drivers/net/tun.c               # tun/tap: userspace↔kernel data path
  drivers/net/ethernet/intel/igb/ # production NIC: DMA rings, MSI-X, SR-IOV

================================================================================
TIER 2 — BUILD SYSTEM, KBUILD, RUST
================================================================================

Documentation/kbuild/
  kbuild.rst                      # Makefile variables: obj-m, ccflags-y
  kconfig-language.rst            # Kconfig syntax: tristate, depends on
  modules.rst                     # Module loading, symbol namespaces
  makefiles.rst                   # Full Makefile reference

Documentation/rust/
  quick-start.rst                 # Setup: rustup, bindgen, rust-analyzer
  coding-guidelines.rst           # SAFETY comments, Rust style in kernel
  arch-support.rst                # Which arches support Rust
  kernel-api.rst                  # kernel:: crate API overview

rust/kernel/net/                  # in-tree Rust net abstractions (evolving)
rust/kernel/sync.rs               # SpinLock, Mutex, Arc, UniqueArc
rust/kernel/alloc/                # GFP_KERNEL/ATOMIC wrappers

================================================================================
TIER 3 — DEBUGGING AND ANALYSIS TOOLS
================================================================================

Documentation/dev-tools/
  kasan.rst                       # Kernel Address Sanitizer
  kfence.rst                      # Low-overhead sampling sanitizer
  ubsan.rst                       # Undefined Behavior Sanitizer
  kmemleak.rst                    # Memory leak detector
  kcsan.rst                       # Kernel Concurrency Sanitizer
  sparse.rst                      # sparse type checker
  smatch.rst                      # smatch interprocedural checker

Documentation/trace/
  ftrace.rst                      # function tracer, graph tracer
  kprobes.rst                     # dynamic breakpoints
  tracepoints.rst                 # TRACE_EVENT macro system
  events.rst                      # perf events from tracepoints
  histogram.rst                   # trace histogram triggers
  boottime-trace.rst              # trace from boot

Documentation/admin-guide/
  dynamic-debug-howto.rst         # pr_debug() at runtime

================================================================================
TIER 4 — SECURITY, NAMESPACES, CGROUPS
================================================================================

Documentation/networking/
  net_namespaces.rst              # Network namespace internals
  secid.rst                       # Security identifiers on skb
  timestamping.rst

Documentation/security/
  credentials.rst                 # cred, capable(), ns_capable()
  keys/

Documentation/admin-guide/
  cgroup-v2.rst                   # net_cls, net_prio cgroup controllers

include/linux/netfilter.h         # Netfilter hook points
net/netfilter/                    # nftables, iptables, conntrack
net/xfrm/                         # IPsec xfrm framework

================================================================================
TIER 5 — PERFORMANCE, XDP, eBPF
================================================================================

Documentation/networking/
  af_xdp.rst
  xdp/xdp-rx-metadata.rst

Documentation/bpf/
  btf.rst                         # BPF Type Format
  programs.rst                    # BPF program types
  maps.rst                        # BPF map types
  verifier.rst                    # BPF verifier internals

tools/perf/Documentation/         # perf tool man pages
kernel/bpf/                       # BPF core implementation

External:
  https://www.kernel.org/doc/html/latest/networking/
  https://www.youtube.com/c/linuxfoundation  # Netdev conference talks
  https://netdev.bots.linux.dev/              # automated patch testing results
  https://lore.kernel.org/netdev/            # netdev mailing list archive
  https://elixir.bootlin.com/linux/          # cross-referenced kernel source

================================================================================
ELITE DEVELOPER ROADMAP — 12-MONTH PROGRESSION
================================================================================

MONTH 1-2: Environment + First Patch
  □ Set up virtme-ng workflow (boot in < 5s iteration cycle)
  □ Study loopback.c and dummy.c completely
  □ Write edu_net.c (this codebase)
  □ Load with insmod, verify /proc/net/dev
  □ Run checkpatch.pl, fix all warnings
  □ Submit a trivial cleanup patch to netdev (typo fix, comment improvement)
  □ Read your rejection email from Jakub/Paolo — iterate

MONTH 3-4: sk_buff Mastery
  □ Add GRO (Generic Receive Offload) to edu_net
  □ Implement ethtool statistics (ETHTOOL_GSTATS)
  □ Add netlink attributes (IFLA_*) for rtnetlink
  □ Implement NAPI with budget accounting and interrupt coalescing
  □ Read veth.c completely; understand peer TX → peer RX path
  □ Trace sk_buff from socket → qdisc → driver → NIC with ftrace graph

MONTH 5-6: Protocol Internals
  □ Trace a TCP connect() through tcp_connect → tcp_transmit_skb → IP → driver
  □ Add XDP program support to edu_net (xdp_prog hook in ndo_bpf)
  □ Write a BPF program that drops packets matching a pattern on edu_net
  □ Understand the qdisc layer: pfifo_fast, fq_codel, HTB
  □ Read net/core/dev.c: __dev_queue_xmit flow completely

MONTH 7-8: Concurrency + Security
  □ Add RCU-protected configuration (loopback/drop mode switchable at runtime)
  □ Integrate with network namespaces (alloc_netdev_mqs per netns)
  □ Add sysfs attributes (kobject/ktype) for runtime config
  □ Study KCSAN output on edu_net under parallel TX+RX load
  □ Add lockdep annotations (lock_class_key, lockdep_set_class)
  □ Implement a netfilter hook and understand nft rule matching

MONTH 9-10: Hardware Acceleration + XDP
  □ Port edu_net to simulate DMA ring (physically addressed buffers)
  □ Implement XDP_TX and XDP_REDIRECT on the simulated ring
  □ Add AF_XDP zero-copy support (xsk_pool integration)
  □ Study igb or mlx5 driver: MSI-X, NUMA-aware ring allocation
  □ Profile with perf + flamegraph; reduce cycles/packet by 20%

MONTH 11-12: Rust + Upstream Contribution
  □ Port edu_net to Rust using in-tree kernel crate
  □ Track the Rust netdev series (Fujita, Jianguo) on lore.kernel.org
  □ File a bug on netdev via Bugzilla or list with reproducer + bisect
  □ Submit a non-trivial feature patch with full test coverage
  □ Attend Netdev conference virtually; watch all talks
  □ Review other people's patches on the list (Reviewed-by: credits)

KEY METRICS FOR "ELITE" STATUS:
  • Can read any net driver in the tree and understand data flow in 30 min
  • Can reproduce a kernel net bug with a minimal C reproducer in < 2 hours
  • Can write, pass checkpatch, and send a patch series without being asked
    to redo the entire thing
  • Understands every lock in net/core/dev.c and why it's there
  • Can write a BPF verifier-compliant program targeting skb TC hooks
  • Has at least one patch merged into netdev/net-next

================================================================================
CRITICAL INVARIANTS EVERY NET KERNEL DEVELOPER MUST KNOW
================================================================================

1. SK_BUFF OWNERSHIP
   - Every skb has exactly one owner at any time
   - ndo_start_xmit: if OK → you own it → free it. If BUSY → qdisc owns it.
   - netif_receive_skb / netif_rx: transfers ownership to the stack
   - skb_clone(): both original and clone need separate kfree_skb calls
   - skb_get(): increments users; caller must kfree_skb when done
   RULE: never free an skb you don't own; never lose track of one you do.

2. CONTEXT RULES
   - ndo_start_xmit: softirq context, no sleep, GFP_ATOMIC only
   - ndo_open/stop:  process context, can sleep, GFP_KERNEL ok
   - NAPI poll:      softirq context; napi_complete() before next schedule
   - netif_rx():     any context including hardirq; uses backlog queue
   - netif_receive_skb(): softirq only; direct delivery, no queue

3. NAPI CONTRACT
   - Always call napi_complete_done() when work_done < budget
   - Never call napi_schedule() from poll() — causes infinite loop
   - napi_disable() in ndo_stop() waits for in-flight poll to finish
   - netif_napi_del() must be called before free_netdev()

4. MEMORY BARRIERS IN RING BUFFERS
   - smp_wmb() after writing descriptor, before bumping producer index
   - smp_rmb() before reading descriptor, after reading producer index
   - In Rust: use core::sync::atomic::Ordering::{Release, Acquire}

5. STATS FAST PATH
   - Use u64_stats_sync (u64_stats_update_begin/end) on 32-bit safe reads
   - Prefer per-CPU stats (this_cpu_ptr) to avoid cache line bouncing
   - ndo_get_stats64 accumulates per-CPU with seqcount protection

================================================================================
MAILING LISTS AND PEOPLE (2025)
================================================================================

  netdev@vger.kernel.org          # THE list. All net patches go here.
  linux-kernel@vger.kernel.org    # CC for cross-subsystem patches

  Jakub Kicinski   kuba@kernel.org           # net-next maintainer
  Paolo Abeni      pabeni@redhat.com          # net-next co-maintainer
  David S. Miller  davem@davemloft.net        # legendary maintainer (semi-retired)
  Eric Dumazet     edumazet@google.com        # core networking guru, reviews all
  Alexei Starovoitov ast@kernel.org           # BPF / XDP
  Daniel Borkmann  daniel@iogearbox.net       # BPF
  Björn Töpel      bjorn@kernel.org           # AF_XDP, XDP
  Toke Høiland-Jørgensen toke@redhat.com     # TC, XDP

  Patch archive:   https://lore.kernel.org/netdev/
  Patch testing:   https://netdev.bots.linux.dev/ (patchwork + pw-bot)
  CI:              https://github.com/intel/net-next-CI

================================================================================
