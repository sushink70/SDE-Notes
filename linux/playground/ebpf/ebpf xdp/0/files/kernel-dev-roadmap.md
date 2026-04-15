# XDP/eBPF Kernel Developer Roadmap & Patch Submission Guide
# =============================================================
# Based on: Documentation/process/  Documentation/bpf/  net/core/filter.c
# Linus's tree: https://github.com/torvalds/linux

## PHASE 0 — Environment Setup (Day 1)
###############################################################################

### 0.1 Clone the kernel tree

    # Linus's mainline (read-only mirror on GitHub)
    git clone https://github.com/torvalds/linux.git
    cd linux

    # For BPF work, use the bpf-next tree (where all BPF patches land first)
    git clone https://git.kernel.org/pub/scm/linux/kernel/git/bpf/bpf-next.git
    cd bpf-next

    # Or add as a remote to mainline
    git remote add bpf-next \
        https://git.kernel.org/pub/scm/linux/kernel/git/bpf/bpf-next.git
    git fetch bpf-next

### 0.2 Install build tools (Debian/Ubuntu)

    sudo apt install -y \
        build-essential bc flex bison libssl-dev libelf-dev \
        clang llvm lld pahole dwarves \
        bpftool libbpf-dev \
        sparse smatch coccinelle       # static analysis
    
    # For Rust in-kernel (optional, CONFIG_RUST=y):
    rustup toolchain install $(scripts/min-tool-version.sh rustc)
    rustup component add rust-src rustfmt clippy
    rustup target add bpfel-unknown-none

### 0.3 Configure kernel for BPF development

    # Start from a minimal config
    make defconfig
    ./scripts/config -e CONFIG_BPF
    ./scripts/config -e CONFIG_BPF_SYSCALL
    ./scripts/config -e CONFIG_BPF_JIT
    ./scripts/config -e CONFIG_XDP_SOCKETS
    ./scripts/config -e CONFIG_DEBUG_INFO_BTF      # required for CO-RE
    ./scripts/config -e CONFIG_DEBUG_INFO_DWARF5
    ./scripts/config -e CONFIG_KASAN               # memory error detector
    ./scripts/config -e CONFIG_KCSAN               # concurrency sanitizer
    ./scripts/config -e CONFIG_UBSAN               # UB sanitizer
    ./scripts/config -e CONFIG_LOCKDEP
    ./scripts/config -e CONFIG_DYNAMIC_DEBUG
    make olddefconfig
    make -j$(nproc)

### 0.4 Run in QEMU (never test on production before verifying in VM)

    # Build a minimal rootfs with buildroot or debootstrap
    # Then launch with:
    qemu-system-x86_64 \
        -kernel arch/x86/boot/bzImage \
        -drive file=rootfs.ext4,format=raw \
        -append "root=/dev/sda rw console=ttyS0 nokaslr" \
        -nographic \
        -m 2G \
        -smp 4 \
        -netdev user,id=net0 -device virtio-net,netdev=net0   # virtio: native XDP

## PHASE 1 — Writing BPF Code (Week 1-2)
###############################################################################

### Where BPF programs live in-tree:
    samples/bpf/          # older samples (reference only)
    tools/lib/bpf/        # libbpf (userspace library)
    tools/testing/selftests/bpf/  # official test suite — READ ALL OF THIS
    kernel/bpf/           # BPF core (syscall, verifier, JIT interfaces)
    net/core/filter.c     # XDP / tc BPF dispatch

### Write your program following kernel coding style:
    # MANDATORY: Read and follow verbatim
    Documentation/process/coding-style.rst
    Documentation/process/submitting-patches.rst
    Documentation/bpf/bpf_devel_QA.rst
    Documentation/bpf/libbpf/

    # Check style before submitting:
    ./scripts/checkpatch.pl --strict kernel/bpf/mypatch.patch

### Add a selftest (REQUIRED for all BPF submissions):
    # Location: tools/testing/selftests/bpf/
    # Pattern: prog_tests/your_feature.c  (C framework)
    #       or progs/your_feature.bpf.c   (BPF program)
    
    # Run the test suite:
    cd tools/testing/selftests/bpf
    make -j$(nproc)
    sudo ./test_progs -t your_feature_name
    
    # Run ALL tests (CI requirement):
    sudo ./test_progs -j8

## PHASE 2 — Submitting a Patch to Linus's Tree
###############################################################################
# BPF patches do NOT go directly to Linus. The flow is:
#
#   Your fork → bpf-next@vger.kernel.org (mailing list)
#             → Daniel Borkmann / Alexei Starovoitov review
#             → bpf-next tree
#             → net-next tree
#             → Linus's mainline (Merge Window)

### 2.1 Configure git for kernel development

    git config user.name  "Your Name"
    git config user.email "you@domain.com"    # Must match S-O-B line
    
    # Install b4 (patch series management tool — modern replacement for git send-email)
    pip install b4
    
    # Or classic git send-email:
    git config sendemail.smtpserver   smtp.yourprovider.com
    git config sendemail.smtpuser     you@domain.com
    git config sendemail.smtpencryption tls

### 2.2 Create a topic branch

    git checkout -b bpf/xdp-filter-feature bpf-next/master

### 2.3 Commit message format (NON-NEGOTIABLE)

    bpf: xdp: add per-source rate limiting to xdp_filter sample
    
    Add an LRU_HASH-backed per-source-IP rate limiter to the xdp_filter
    example program. The limiter uses a 1-second sliding window and drops
    packets from any source exceeding RATE_LIMIT_PPS (1000 pps by default).
    
    This demonstrates LRU map eviction semantics under sustained traffic
    and serves as a reference for production XDP rate limiters.
    
    The corresponding selftest verifies:
    - Normal traffic passes the rate limiter
    - Traffic exceeding 1000 pps is dropped
    - Per-CPU stats counters are consistent across CPUs
    
    Signed-off-by: Your Name <you@domain.com>

    # Rules for the commit message:
    # - Subject: "subsystem: component: short imperative description" (≤72 chars)
    # - Blank line between subject and body
    # - Body: WHY this change, not WHAT (the diff shows what)
    # - Signed-off-by is MANDATORY (Developer Certificate of Origin)

### 2.4 Generate patch file

    git format-patch bpf-next/master --subject-prefix="PATCH bpf-next"
    # For a series of patches:
    git format-patch bpf-next/master --subject-prefix="PATCH bpf-next v2" \
        --cover-letter -n

### 2.5 Run checkpatch

    ./scripts/checkpatch.pl --strict *.patch
    # Fix ALL warnings and errors. Reviewers will bounce patches with issues.

### 2.6 Find the right maintainers

    ./scripts/get_maintainer.pl *.patch
    # This gives you the To: and Cc: lines for the email

### 2.7 Send the patch

    # Using b4 (recommended):
    b4 send *.patch
    
    # Or git send-email:
    git send-email \
        --to=bpf@vger.kernel.org \
        --cc=ast@kernel.org \
        --cc=daniel@iogearbox.net \
        --cc=netdev@vger.kernel.org \
        *.patch

### 2.8 Respond to review comments

    # After feedback, amend and resend as v2:
    git commit --amend
    git format-patch bpf-next/master --subject-prefix="PATCH bpf-next v2"
    # Add a changelog after the --- line explaining v1→v2 changes

## PHASE 3 — BPF Kernel Internals to Study
###############################################################################

    kernel/bpf/verifier.c       # 14,000 lines — the program validator
    kernel/bpf/core.c           # BPF interpreter and JIT dispatch
    kernel/bpf/syscall.c        # BPF(2) syscall handlers
    kernel/bpf/hashtab.c        # BPF hash map implementation
    kernel/bpf/lpm_trie.c       # Longest prefix match (for CIDR matching)
    net/core/filter.c           # Network BPF hooks (XDP, tc, socket filter)
    net/core/dev.c              # netif_receive_skb, XDP dispatch path
    drivers/net/virtio_net.c    # virtio_net XDP native implementation (read this)

## PHASE 4 — Elite Kernel Developer Checklist
###############################################################################

    [x] Can explain every line of the BPF verifier's type checker
    [x] Know all BPF map types, their locking models, and eviction semantics
    [x] Can write CO-RE-portable programs without vmlinux.h tricks
    [x] Understand JIT code generation for x86_64 and arm64
    [x] Have submitted ≥1 accepted patch to bpf-next
    [x] Run the full selftests suite locally before every send
    [x] Read every BPF commit message in Linus's tree for past 2 years
    [x] Know the difference between XDP, tc BPF, cgroup BPF, and kprobe BPF
    [x] Can debug a verifier rejection from raw log output
    [x] Have reviewed (commented on) other developers' patches on the list

## DOCUMENTATION REFERENCE LIBRARY
###############################################################################

# Kernel tree docs (Documentation/):
    Documentation/bpf/
    Documentation/bpf/libbpf/libbpf_overview.rst
    Documentation/bpf/btf.rst
    Documentation/bpf/verifier.rst
    Documentation/bpf/map_hash.rst
    Documentation/networking/xdp-tutorial.rst
    Documentation/networking/filter.rst
    Documentation/process/submitting-patches.rst
    Documentation/process/coding-style.rst
    Documentation/process/email-clients.rst

# Canonical online references:
    https://ebpf.io/what-is-ebpf/                  # high-level intro
    https://docs.kernel.org/bpf/                    # rendered kernel docs
    https://nakryiko.com/posts/bpf-core-reference/  # CO-RE deep dive (Nakryiko)
    https://nakryiko.com/posts/bpf-portability-and-co-re/
    https://docs.cilium.io/en/latest/bpf/           # Cilium BPF reference
    https://aya-rs.dev/book/                        # Rust aya framework
    https://github.com/libbpf/libbpf               # libbpf source + examples
    https://github.com/iovisor/bcc                  # BCC Python frontend
    https://github.com/xdp-project/xdp-tutorial    # step-by-step XDP labs
    https://github.com/xdp-project/xdp-tools       # production XDP utilities (xdp-filter, xdp-dump)
    https://lore.kernel.org/bpf/                    # BPF mailing list archive
    https://patchwork.kernel.org/project/netdevbpf/ # patch tracker

# Books:
    "Linux Kernel Development" — Robert Love
    "Understanding the Linux Network Stack" — Benvenuti
    "BPF Performance Tools" — Brendan Gregg (O'Reilly 2019)
    "Learning eBPF" — Liz Rice (O'Reilly 2023)
    "Systems Performance" 2nd Ed. — Brendan Gregg

# RFC / Specs:
    RFC 791  — IPv4
    RFC 894  — Ethernet encapsulation
    Linux kernel RFC: tools/testing/selftests/bpf/ test patterns
