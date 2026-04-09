#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-only
#
# upstream_workflow.sh — step-by-step guide for submitting to Linus's tree
#
# This follows the actual workflow maintainers like David Miller (net),
# Jakub Kicinski (net-next), and Pablo Neira Ayuso (netfilter) expect.
#
# KEY TREES for net subsystem:
#   Linus mainline:    https://git.kernel.org/torvalds/linux
#   net (fixes):       https://git.kernel.org/netdev/net          [5.x stable fixes]
#   net-next (new):    https://git.kernel.org/netdev/net-next     [new features]
#   netfilter-next:    https://git.kernel.org/netfilter/nf-next   [our target]
#
# Rule: Bug fixes go to 'net'. New features go to 'net-next'.
#       netfilter patches go via Pablo → net-next.

set -euo pipefail

title() { printf '\n\033[1;35m══ STEP %s: %s ══\033[0m\n' "$1" "$2"; }
cmd()   { printf '\033[0;36m$ %s\033[0m\n' "$1"; }
info()  { printf '  \033[0;33m▸\033[0m %s\n' "$1"; }

# ─────────────────────────────────────────────────────────────────────────────
title "0" "Clone the correct tree"
# ─────────────────────────────────────────────────────────────────────────────
cat <<'EOF'
For netfilter new features, work against nf-next:

    git clone https://git.kernel.org/pub/scm/linux/kernel/git/netfilter/nf-next.git
    cd nf-next

    # Add Linus's tree as reference:
    git remote add torvalds https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git
    git fetch torvalds

    # Create your feature branch from nf-next/main:
    git checkout -b feature/nf-pkt-inspector nf-next/main

    # For net (fixes only):
    git clone https://git.kernel.org/pub/scm/linux/kernel/git/netdev/net.git
EOF

# ─────────────────────────────────────────────────────────────────────────────
title "1" "Place files in the correct in-tree location"
# ─────────────────────────────────────────────────────────────────────────────
cat <<'EOF'
For a new netfilter match/target module:
    net/netfilter/nf_pkt_inspector.c        ← implementation
    include/uapi/linux/netfilter/           ← any uAPI headers (userspace ABI)
    include/linux/netfilter/                ← kernel-internal headers

For a new net core helper:
    net/core/pkt_inspector.c

For a new xt_ (iptables extension) module:
    net/netfilter/xt_PKTINSPECT.c
    include/uapi/linux/netfilter/xt_PKTINSPECT.h

Add to the corresponding Kconfig and Makefile:
    net/netfilter/Kconfig   → add config NF_PKT_INSPECTOR block
    net/netfilter/Makefile  → obj-$(CONFIG_NF_PKT_INSPECTOR) += nf_pkt_inspector.o
EOF

# ─────────────────────────────────────────────────────────────────────────────
title "2" "Kconfig entry (in-tree)"
# ─────────────────────────────────────────────────────────────────────────────
cat <<'KCONF'
# Add to net/netfilter/Kconfig:

config NF_PKT_INSPECTOR
    tristate "Netfilter packet inspector (educational)"
    depends on NETFILTER && IP_NF_IPTABLES
    select NF_CONNTRACK
    help
      This module adds a NF_INET_PRE_ROUTING hook that counts and
      optionally drops packets by destination port.

      To compile as a module, choose M here.
      The module will be called nf_pkt_inspector.

KCONF

# ─────────────────────────────────────────────────────────────────────────────
title "3" "Check coding style BEFORE committing"
# ─────────────────────────────────────────────────────────────────────────────
cat <<'EOF'
scripts/checkpatch.pl is mandatory. Patches with checkpatch errors are
rejected by patchwork/maintainers automatically.

    # Check a single file:
    ./scripts/checkpatch.pl --no-tree -f net/netfilter/nf_pkt_inspector.c

    # Check your git patch:
    git format-patch -1 HEAD
    ./scripts/checkpatch.pl 0001-*.patch

    # Common violations to fix:
    #   - Lines > 80 chars (use \  continuation or refactor)
    #   - Missing blank line after declarations
    #   - Trailing whitespace (use `git diff --check`)
    #   - Wrong comment style (use /* */ not // for standalone comments)
    #   - Missing SPDX-License-Identifier

    # Also run sparse:
    make C=2 CF="-D__CHECK_ENDIAN__" net/netfilter/nf_pkt_inspector.o
EOF

# ─────────────────────────────────────────────────────────────────────────────
title "4" "Write the commit message"
# ─────────────────────────────────────────────────────────────────────────────
cat <<'COMMIT'
Kernel commit message format (Documentation/process/submitting-patches.rst):

    netfilter: add nf_pkt_inspector module

    Add a NF_INET_PRE_ROUTING hook module that:
    - counts IPv4 packets by protocol (TCP/UDP/other)
    - logs TCP SYN packets with src/dst IP and port into a ring buffer
    - optionally drops packets matching a configurable destination port

    The ring buffer uses a bitmask-wrapped index (LOG_RING_SIZE must be
    power-of-two) and is protected by a spinlock safe for softirq context.
    Counters use atomic64_t to avoid per-cpu overhead in a learning module.

    Expose statistics via /proc/net/nf_pkt_inspector using seq_file.

    Tested on x86_64 with kernel v6.8, 1000 SYN stress test, KASAN clean.

    Signed-off-by: Your Name <your@email.com>

Rules:
  - First line: subsystem: short description (≤ 72 chars, imperative mood)
  - Blank line after subject
  - Body: WHY you made the change, not WHAT the code does
  - If fixing a bug: include Fixes: <sha> ("subsystem: ...")
  - Signed-off-by: required (Developer Certificate of Origin)
  - Add Reviewed-by/Acked-by tags as they come in from reviewers
COMMIT

# ─────────────────────────────────────────────────────────────────────────────
title "5" "Generate and send the patch"
# ─────────────────────────────────────────────────────────────────────────────
cat <<'PATCH'
# Configure git send-email (one-time):
    git config --global sendemail.smtpserver  smtp.yourprovider.com
    git config --global sendemail.smtpencryption tls
    git config --global sendemail.smtpserverport 587
    git config --global sendemail.from "Your Name <you@email.com>"

# Use b4 (modern replacement for get_maintainer + send-email workflow):
    pip install b4
    # Find maintainers automatically:
    b4 send -H HEAD         # shows what would be sent
    b4 send HEAD            # actually sends

# Or manually:
    # 1. Generate patch file:
    git format-patch -1 --subject-prefix="PATCH net-next" HEAD

    # 2. Find maintainers to CC:
    ./scripts/get_maintainer.pl 0001-netfilter-*.patch
    # Output will include:
    #   Pablo Neira Ayuso <pablo@netfilter.org> (netfilter maintainer)
    #   netfilter-devel@vger.kernel.org (mailing list)
    #   netdev@vger.kernel.org (net subsystem list)

    # 3. Send:
    git send-email \
        --to netfilter-devel@vger.kernel.org \
        --cc pablo@netfilter.org \
        --cc netdev@vger.kernel.org \
        0001-netfilter-add-nf_pkt_inspector-module.patch

# For a patch series (multiple patches):
    git format-patch -3 --cover-letter --subject-prefix="PATCH net-next v2"
    # Edit 0000-cover-letter.patch with motivation
    git send-email 0000-*.patch 0001-*.patch 0002-*.patch ...
PATCH

# ─────────────────────────────────────────────────────────────────────────────
title "6" "Track the patch on patchwork"
# ─────────────────────────────────────────────────────────────────────────────
cat <<'PW'
    # patchwork.kernel.org tracks all patches sent to mailing lists
    # Find your patch at: https://patchwork.kernel.org/project/netfilter-devel/list/

    # Use b4 to track review status:
    b4 am <msgid-from-patchwork>   # apply a reviewed patch locally
    b4 shazam <url>                # apply from a patchwork URL

    # Reply to review comments:
    # - Answer every reviewer concern
    # - For v2: add "Changes in v2:" before Signed-off-by
    # - Re-send with --subject-prefix="PATCH net-next v2"
PW

# ─────────────────────────────────────────────────────────────────────────────
title "7" "Documentation index for net subsystem development"
# ─────────────────────────────────────────────────────────────────────────────
cat <<'DOCS'
════════════════════════════════════════════════════════════════════
KERNEL DOCUMENTATION (Documentation/ tree)
════════════════════════════════════════════════════════════════════

Process & Contribution:
  Documentation/process/submitting-patches.rst    ← how to submit
  Documentation/process/coding-style.rst          ← Linux coding style
  Documentation/process/stable-kernel-rules.rst   ← stable backports
  Documentation/process/email-clients.rst         ← setup for send-email

Networking Subsystem:
  Documentation/networking/filter.rst             ← BPF/netfilter overview
  Documentation/networking/netfilter-sysctl.rst   ← sysctl tunables
  Documentation/networking/net_dim.rst            ← DIM adaptive coalescing
  Documentation/networking/skbuff.rst             ← sk_buff documentation
  Documentation/networking/kapi.rst               ← networking kernel API
  Documentation/networking/driver.rst             ← NIC driver guide

Rust for Linux:
  Documentation/rust/index.rst                    ← Rust overview
  Documentation/rust/quick-start.rst             ← toolchain setup
  Documentation/rust/coding-guidelines.rst        ← Rust kernel style

Testing:
  Documentation/dev-tools/kasan.rst              ← KASAN setup
  Documentation/dev-tools/kgdb.rst               ← kgdb setup
  Documentation/dev-tools/ubsan.rst              ← UBSAN setup
  Documentation/trace/ftrace.rst                  ← ftrace usage
  Documentation/trace/kprobetrace.rst            ← kprobe events
  tools/testing/selftests/net/                   ← kernel net selftests

Build System:
  Documentation/kbuild/makefiles.rst             ← Kbuild/Makefile docs
  Documentation/kbuild/modules.rst               ← out-of-tree modules

════════════════════════════════════════════════════════════════════
KEY KERNEL SOURCE FILES
════════════════════════════════════════════════════════════════════

Netfilter core:
  net/netfilter/core.c                   nf_register_net_hook()
  net/netfilter/nf_queue.c               NF_QUEUE implementation
  include/linux/netfilter.h              nf_hook_ops, NF_ACCEPT/DROP
  include/linux/netfilter_ipv4.h         hook points, priorities

sk_buff:
  include/linux/skbuff.h                 struct sk_buff, all accessors
  net/core/skbuff.c                      skb alloc/free/clone
  include/linux/ip.h                     struct iphdr
  include/linux/tcp.h                    struct tcphdr

IP layer:
  net/ipv4/ip_input.c                    ip_rcv() → NF_HOOK()
  net/ipv4/ip_output.c                   ip_output() → POST_ROUTING hook

proc/seq_file:
  fs/proc/generic.c                      proc_create()
  include/linux/seq_file.h               seq_printf(), single_open()
  include/linux/proc_fs.h                proc_ops

════════════════════════════════════════════════════════════════════
EXTERNAL REFERENCES
════════════════════════════════════════════════════════════════════

  LWN.net articles:
    https://lwn.net/Articles/traversing-netfilter/   ← netfilter internals
    https://lwn.net/Articles/783 (Rust in kernel series)

  Kernel Newbies:
    https://kernelnewbies.org/FirstKernelPatch

  Netfilter development:
    https://www.netfilter.org/documentation/
    https://lore.kernel.org/netfilter-devel/

  Books:
    Robert Love — Linux Kernel Development (3rd ed)
    Daniel P. Bovet — Understanding the Linux Kernel
    Jonathan Corbet — Linux Device Drivers (3rd ed, free at lwn.net)

  Interactive:
    https://elixir.bootlin.com/   ← browse kernel source with cross-refs
    https://git.kernel.org/       ← official kernel git hosting
DOCS

echo
echo "Workflow complete. Happy hacking."
