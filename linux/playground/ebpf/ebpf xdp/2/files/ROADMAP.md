# eBPF + LSM Kernel Development: Complete Roadmap & Workflow
# Elite Kernel Developer Guide — Security Focus
# =============================================================================

## 4-Line Summary
#
# BPF LSM programs attach to Linux Security Module hooks (bprm_check_security,
# file_open, ptrace_access_check) as BPF programs, providing programmable,
# runtime-configurable kernel security policy without kernel recompilation.
# CO-RE (Compile Once, Run Everywhere) via BTF makes programs portable across
# kernel versions. The BPF verifier enforces memory safety at load time; logic
# bugs must be caught by behavioral tests. The workflow mirrors upstream kernel
# development: patch → checkpatch → mailing list → Linus tree → stable backport.

## ARCHITECTURE
# =============================================================================

  User Space                         Kernel Space
  ─────────────────────────────────  ──────────────────────────────────────────
  security_monitor (loader)          ┌─ BPF Verifier ─────────────────────────┐
    │                                │  Type tracking, CFG analysis,           │
    │  bpf_object__open()            │  memory access bounds, stack depth      │
    │  bpf_object__load()  ──────────►  Returns: accept or EINVAL + log        │
    │  bpf_program__attach()         └─────────────────────────────────────────┘
    │                                          │
    │  map_update_elem() ──────────────────►  BPF Maps (kernel memory)
    │    ├─ blocked_files (HASH)              │  ├─ blocked_files
    │    ├─ blocked_uids  (HASH)              │  ├─ blocked_uids
    │    └─ events (RINGBUF) ◄────────────────┘  └─ events (ringbuf)
    │                                                      ▲
    │  ring_buffer__poll()                                 │  emit_event()
    │    └─ handle_event()                                 │
    │         └─ print/log                                 │
    │                                            ┌─ LSM Framework ────────────┐
    │                                            │  security_file_open()       │
  Policy Config                                  │  security_bprm_check()      │
    (files/uids)                                 │  security_ptrace_access()   │
                                                 └────────────────────────────┘
                                                          ▲
                                                 syscall layer: open(2), execve(2), ptrace(2)
                                                          ▲
                                                   User Workloads
                                                   (processes, containers)


## PHASE 1: FOUNDATION (Weeks 1-6)
# =============================================================================

### 1.1 Kernel Build Environment

  # Clone Linus's mainline tree (the authoritative development tree)
  git clone git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git
  cd linux

  # Key subsystem trees to track for BPF + security work:
  #   BPF:      git://git.kernel.org/pub/scm/linux/kernel/git/bpf/bpf.git        (fixes)
  #   BPF-next: git://git.kernel.org/pub/scm/linux/kernel/git/bpf/bpf-next.git   (new features)
  #   LSM:      git://git.kernel.org/pub/scm/linux/kernel/git/jmorris/linux-security.git
  #   Stable:   git://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git
  #
  # Workflow: new features go to bpf-next, bug fixes to bpf, both merge to Linus.

  git remote add bpf-next \
    git://git.kernel.org/pub/scm/linux/kernel/git/bpf/bpf-next.git
  git fetch bpf-next

### 1.2 Kernel Config for BPF + LSM Development

  # Start from a known good config
  make defconfig
  make menuconfig   # or scripts/config for scripted changes

  # Required for BPF LSM:
  scripts/config --enable CONFIG_BPF
  scripts/config --enable CONFIG_BPF_SYSCALL
  scripts/config --enable CONFIG_BPF_JIT
  scripts/config --enable CONFIG_BPF_JIT_ALWAYS_ON     # security: no interpreter
  scripts/config --enable CONFIG_BPF_LSM
  scripts/config --enable CONFIG_DEBUG_INFO_BTF         # CO-RE support
  scripts/config --enable CONFIG_DEBUG_INFO_BTF_MODULES
  scripts/config --enable CONFIG_LSM="lockdown,yama,loadpin,safesetid,integrity,bpf"

  # Required for debugging:
  scripts/config --enable CONFIG_KASAN               # AddressSanitizer
  scripts/config --enable CONFIG_KASAN_INLINE
  scripts/config --enable CONFIG_UBSAN               # Undefined behavior
  scripts/config --enable CONFIG_LOCKDEP             # Lock ordering
  scripts/config --enable CONFIG_DEBUG_LOCKDEP
  scripts/config --enable CONFIG_PROVE_LOCKING
  scripts/config --enable CONFIG_FTRACE
  scripts/config --enable CONFIG_FUNCTION_TRACER
  scripts/config --enable CONFIG_DYNAMIC_FTRACE
  scripts/config --enable CONFIG_DEBUG_INFO          # DWARF for gdb/crash
  scripts/config --enable CONFIG_FRAME_POINTER       # stack traces
  scripts/config --enable CONFIG_BPF_EVENTS          # BPF perf events
  scripts/config --enable CONFIG_DEBUG_BPF_ENABLE_OBJTOOL  # verifier debug

  # Build (parallelize: ncpus * 1.5 for I/O overlap)
  make -j$(nproc) LOCALVERSION=-bpflsm-dev

  # Install to test VM (NEVER test on production machine):
  make modules_install INSTALL_MOD_PATH=/mnt/rootfs
  make install INSTALL_PATH=/mnt/rootfs/boot

  # Boot parameter (GRUB or qemu):
  # lsm=lockdown,capability,yama,bpf

### 1.3 Development VM Setup (QEMU + virtme for fast iteration)

  # virtme: mounts host kernel source, boots minimal VM in seconds
  pip install virtme
  virtme-run --kimg arch/x86/boot/bzImage \
    --qemu-opts "-m 2G -cpu host -enable-kvm" \
    --rwdir /tmp

  # Or use syzkaller's VM infrastructure for fuzzing:
  # https://github.com/google/syzkaller/blob/master/docs/linux/setup_ubuntu-host_qemu-vm_x86-64-kernel.md

  # For BPF development: use a dedicated test VM, not WSL2/container.
  # BPF LSM requires real kernel with correct config; containers share host kernel.


## PHASE 2: BPF LSM DEVELOPMENT WORKFLOW
# =============================================================================

### 2.1 Kernel Developer Write → Test → Submit Loop

  ┌─────────────────────────────────────────────────────────────┐
  │  1. Read documentation (see Phase 5 references)             │
  │  2. Write BPF program (.bpf.c)                              │
  │  3. Compile with clang -target bpf -g -O2                   │
  │  4. Run BPF verifier: bpftool prog load <obj> /sys/fs/bpf/  │
  │  5. Check verifier log: /proc/sys/kernel/bpf_log_level      │
  │  6. Write userspace loader (libbpf / aya)                   │
  │  7. Test against actual syscalls                            │
  │  8. Add to kernel selftests: tools/testing/selftests/bpf/   │
  │  9. checkpatch.pl --strict                                   │
  │  10. git format-patch -o patches/ origin/master             │
  │  11. get_maintainer.pl patches/*.patch                      │
  │  12. git send-email --to <maintainers> patches/*.patch      │
  └─────────────────────────────────────────────────────────────┘

### 2.2 BPF Verifier — What it Checks

  The verifier is the core safety mechanism. It performs:

  a) Control Flow Graph (CFG) analysis
     - All paths must terminate (bounded loops, no infinite loops)
     - All paths must reach BPF_EXIT
     - Loop iterations bounded (BPF_MAX_LOOP_ITER = 8,000,000 since 5.17)

  b) Type tracking (register states)
     - PTR_TO_MAP_VALUE, PTR_TO_STACK, PTR_TO_CTX, SCALAR_VALUE
     - Every register has a type; writes enforce type constraints
     - bpf_ringbuf_reserve() → PTR_TO_MEM_OR_NULL (requires NULL check)

  c) Memory access bounds
     - Map value accesses: checked against map value size
     - Stack: ±512 bytes from frame pointer
     - Context (ctx): verified against program type allowed fields

  d) Helper call validation
     - Each helper has constraints on arg types
     - GPL-only helpers require GPL license declaration

  e) Complexity limit
     - 1,000,000 instructions analyzed (BPF_COMPLEXITY_LIMIT_INSNS)
     - Scales with loop unrolling; use __always_inline carefully

### 2.3 CO-RE (Compile Once – Run Everywhere)

  Problem: kernel struct layouts change between versions.
  Solution: BTF (BPF Type Format) + CO-RE relocations.

  How it works:
    1. clang emits BTF into the BPF ELF object (from DWARF via -g)
    2. bpf_core_read() emits a CO-RE relocation record
    3. At load time, libbpf reads /sys/kernel/btf/vmlinux
    4. For each CO-RE relocation, libbpf computes the actual field offset
       on the running kernel and patches the BPF instructions

  # Generate vmlinux.h (type definitions for CO-RE programs):
  bpftool btf dump file /sys/kernel/btf/vmlinux format c > vmlinux.h

  # Verify BTF in your compiled object:
  bpftool btf dump file security_monitor.bpf.o
  # Look for: linux_binprm, file, inode structs

  # Check CO-RE relocations:
  llvm-objdump -d --no-show-raw-insn security_monitor.bpf.o
  readelf -S security_monitor.bpf.o | grep -i core

  # Verify BTF correctness with pahole:
  pahole -C linux_binprm /sys/kernel/btf/vmlinux   # print struct layout with offsets


## PHASE 3: BUILD, LOAD, DEBUG
# =============================================================================

### 3.1 Build Pipeline

  # Step 1: Generate vmlinux.h
  bpftool btf dump file /sys/kernel/btf/vmlinux format c > include/vmlinux.h

  # Step 2: Compile BPF program
  clang -target bpf -g -O2 -Wall \
    -D__TARGET_ARCH_x86 \
    -I./include \
    -c bpf/security_monitor.bpf.c \
    -o build/security_monitor.bpf.o

  # Step 3: Verify compiled object
  llvm-objdump -d build/security_monitor.bpf.o     # disassemble
  bpftool prog dump xlated id <id>                   # after load: show translated BPF
  bpftool btf dump file build/security_monitor.bpf.o # BTF types

  # Step 4: Generate skeleton
  bpftool gen skeleton build/security_monitor.bpf.o \
    > include/security_monitor.skel.h

  # Step 5: Compile userspace
  gcc -g -O2 -Wall \
    -I./include \
    userspace/security_monitor.c \
    -lbpf -lelf -lz \
    -o build/security_monitor

### 3.2 Loading to Kernel

  # Verify BPF LSM is active:
  cat /sys/kernel/security/lsm
  # Expected output includes: bpf

  # Manual load test (verifier log):
  bpftool prog load build/security_monitor.bpf.o \
    /sys/fs/bpf/security_monitor \
    type lsm 2>&1

  # View verifier log on failure:
  # In code: set bpf_object_open_opts.kernel_log_level = 2
  # Env: LIBBPF_LOG_LEVEL=debug

  # Run the full program (root required):
  sudo build/security_monitor

  # Pin maps for persistence across program restarts:
  # In loader: bpf_map__set_pin_path(skel->maps.blocked_files, "/sys/fs/bpf/bf");

### 3.3 Runtime Debugging

  # 1. bpf_printk() — simplest debug output
  #    In BPF program:
  bpf_printk("uid_gid=0x%llx uid=%u\n", uid_gid, uid);
  #    Read output:
  cat /sys/kernel/debug/tracing/trace_pipe
  # OR: trace-cmd stream

  # 2. bpftool — inspect everything at runtime
  bpftool prog list                              # list loaded programs
  bpftool prog dump xlated id <ID>              # BPF instructions (post-JIT)
  bpftool prog dump jited  id <ID>              # x86 JIT output
  bpftool map list                               # list maps
  bpftool map dump id <ID>                      # dump map contents
  bpftool map update id <ID> key 0 0 0 1 value 1  # inject policy entry
  bpftool net list                               # show network attachments
  bpftool perf list                              # show perf_event attachments

  # 3. bpftrace — high-level eBPF scripting for ad-hoc debugging
  #    Attach a kprobe to see raw args at the hook site:
  sudo bpftrace -e '
    kprobe:security_bprm_check {
      printf("pid=%d uid=%d comm=%s\n", pid, uid, comm);
    }'

  # 4. perf + BPF
  perf stat -e bpf-output/BPF-PROG-ID/ -- sleep 1
  perf record -e bpf:* -a -- sleep 5
  perf script

  # 5. ftrace — trace LSM hook calls
  echo 1 > /sys/kernel/debug/tracing/events/lsm/enable
  cat /sys/kernel/debug/tracing/trace
  # or: trace-cmd record -e lsm:* -- sleep 5; trace-cmd report

  # 6. KASAN (AddressSanitizer) — catches kernel memory bugs
  #    Kernel must be built with CONFIG_KASAN=y
  #    KASAN reports appear in dmesg:
  dmesg | grep -A 30 "BUG: KASAN"

  # 7. lockdep — detect lock ordering violations
  dmesg | grep -i "possible deadlock\|lock order"

  # 8. crash — post-mortem analysis
  crash /usr/lib/debug/boot/vmlinux-$(uname -r) /proc/kcore


## PHASE 4: KERNEL TREE INTEGRATION (Upstream Contribution)
# =============================================================================

### 4.1 Adding BPF Selftests (tools/testing/selftests/bpf/)

  # Your BPF LSM selftest lives here:
  tools/testing/selftests/bpf/progs/lsm_security_monitor.c  # BPF program
  tools/testing/selftests/bpf/test_lsm_security_monitor.c   # test runner

  # Build selftests:
  make -C tools/testing/selftests/bpf

  # Run all BPF selftests:
  cd tools/testing/selftests/bpf
  sudo ./test_progs -v

  # Run specific test:
  sudo ./test_progs -t lsm_security_monitor

  # Run with vmtest.sh (official upstream testing in QEMU):
  ./tools/testing/selftests/bpf/vmtest.sh

### 4.2 Patch Preparation for Upstream Submission

  # 1. Develop on a topic branch
  git checkout -b bpf/lsm-security-monitor origin/bpf-next/master

  # 2. Commit with proper format
  git commit -s -m "bpf, lsm: add security monitor sample with CO-RE"
  # Commit message format:
  # subsystem/area: short description
  # <blank line>
  # Long explanation of why this is needed (not what — the diff shows what).
  # Reference related commits, RFCs, or bug reports.
  # <blank line>
  # Signed-off-by: Your Name <you@example.com>  (added by -s)

  # 3. Run checkpatch (MANDATORY — maintainers reject non-compliant patches)
  ./scripts/checkpatch.pl --strict -f bpf/security_monitor.bpf.c
  ./scripts/checkpatch.pl --strict $(git format-patch -1)

  # 4. Verify build across configs
  make allmodconfig && make -j$(nproc)   # all modules enabled
  make W=1 -j$(nproc)                    # extra warnings

  # 5. Generate patch series
  git format-patch -o /tmp/patches/ origin/bpf-next/master

  # 6. Find maintainers
  ./scripts/get_maintainer.pl /tmp/patches/*.patch
  # → lists who to CC on BPF, LSM, and affected subsystems

  # 7. Send patch (requires configured git send-email)
  git send-email \
    --to bpf@vger.kernel.org \
    --cc linux-security-module@vger.kernel.org \
    --cc netdev@vger.kernel.org \
    /tmp/patches/*.patch

  # 8. Track your patch at patchwork:
  #    https://patchwork.kernel.org/project/netdevbpf/list/


## PHASE 5: REFERENCE DOCUMENTATION
# =============================================================================

### Primary Sources (read in this order):

  # BPF Internals:
  Documentation/bpf/                           # start here
  Documentation/bpf/bpf_lsm.rst               # LSM + BPF integration
  Documentation/bpf/btf.rst                    # BTF format spec
  Documentation/bpf/ringbuf.rst                # ringbuf vs perf_event
  Documentation/bpf/bpf_devel_QA.rst          # developer Q&A (MUST READ)
  Documentation/bpf/libbpf/libbpf_overview.rst

  # Kernel Security:
  Documentation/admin-guide/LSM/              # LSM overview
  include/linux/lsm_hooks.h                   # all hook definitions + doc
  security/bpf/hooks.c                        # BPF LSM hook implementations
  kernel/bpf/bpf_lsm.c                        # BPF LSM core

  # BPF Verifier Internals (advanced):
  kernel/bpf/verifier.c                       # the verifier (20,000+ lines)
  kernel/bpf/core.c                           # BPF interpreter + JIT dispatch
  include/linux/bpf.h                         # BPF types, map definitions
  include/uapi/linux/bpf.h                    # userspace-visible BPF API

  # libbpf:
  tools/lib/bpf/libbpf.h                      # public API
  tools/lib/bpf/bpf_helpers.h                 # BPF-side helpers (used in .bpf.c)
  tools/lib/bpf/bpf_core_read.h               # CO-RE read macros

  # Selftests reference implementations:
  tools/testing/selftests/bpf/progs/lsm.c     # upstream BPF LSM selftest
  tools/testing/selftests/bpf/test_lsm.c      # upstream LSM test runner
  samples/bpf/                                 # sample BPF programs

  # External (always check against upstream):
  https://docs.ebpf.io/                        # ebpf.io reference
  https://docs.kernel.org/bpf/               # kernel.org BPF docs
  https://nakryiko.com/                        # Andrii Nakryiko's blog (libbpf author)
  https://pchaigno.github.io/                  # BPF verifier deep dives
  https://aya-rs.dev/book/                     # Aya (Rust BPF) book

  # Papers:
  "The BSD Packet Filter" (McCanne, Jacobson, 1993) — original BPF
  "eBPF - Extended Berkeley Packet Filter" — LWN.net coverage
  "BPF and XDP Reference Guide" — Cilium documentation


## PHASE 6: ELITE DEVELOPER MILESTONES
# =============================================================================

  Week  1-2:   Read Documentation/bpf/ fully. Run tools/testing/selftests/bpf/.
  Week  3-4:   Build custom kernel with BPF + LSM config. Write hello-world BPF.
  Week  5-8:   Complete security_monitor project. Add BPF selftests. checkpatch clean.
  Month 3:     Submit a real patch to bpf@vger.kernel.org (bug fix or improvement).
  Month 4-5:   Study verifier.c. Understand register states, type checking.
  Month 6:     Contribute to libbpf or BPF selftests. Respond to review feedback.
  Month 7-9:   Implement a non-trivial BPF program (e.g., container escape detection).
  Month 10-12: Co-author a subsystem feature. Track bpf-next development daily.
  Year  2+:    Become a reviewer. Author RFC patches. Attend Linux Plumbers Conf (BPF track).

  Key habits of elite kernel developers:
    - Read kernel mailing lists daily: lore.kernel.org/bpf/
    - Always read the patch history of files you modify: git log -p <file>
    - Never merge without bisect-able history
    - Use sparse, smatch, and coccinelle for static analysis
    - Test on real hardware, not just VMs (especially for JIT correctness)
    - Keep a kernel bisect VM ready for regression hunting


## THREAT MODEL
# =============================================================================

  Asset: Process execution integrity, file access confidentiality, ptrace isolation

  Threat Actors:
    T1: Compromised container / escaped workload (UID non-zero, limited caps)
    T2: Privilege escalation via ptrace cross-UID (e.g., CVE-2019-13272 class)
    T3: Supply chain: malicious binary placed at known path
    T4: BPF program itself as attack surface (verifier bypass)

  Mitigations:
    T1 → UID block list + inode-based exec control (maps hot-reloaded)
    T2 → ptrace_access_check hook: cross-UID ptrace → -EPERM
    T3 → inode-based policy (bypasses path-based TOCTOU); sign executables (IMA)
    T4 → BPF verifier (memory safety); unprivileged BPF disabled (sysctl)
         CAP_BPF required for LSM program loading
         BPF JIT hardening: CONFIG_BPF_JIT_ALWAYS_ON (no interpreter fallback)
         Constant blinding: randomize immediate values in JIT output

  Residual risks:
    - inode reuse: if attacker creates file with same inode after blocking
      (mitigate: pin device + inode, use IMA hash instead)
    - Ringbuf overflow drops events (tune max_entries; add drop counter)
    - BPF verifier bugs (CVE class exists); mitigate by keeping kernel updated
    - Cross-CPU stats (per-CPU array) not globally consistent; use atomics
      or accept approximate counts


## ROLL-OUT / ROLLBACK PLAN
# =============================================================================

  Roll-out:
    1. Deploy in POLICY_AUDIT mode first (log, don't block)
    2. Review events for 48h; confirm no false positives
    3. Switch to POLICY_DENY for high-confidence entries
    4. Monitor stats map for anomalous deny spike
    5. Pin BPF maps to BPFFS for hot-reload without service restart

  Rollback (zero-downtime):
    - BPF LSM hooks are attached via file descriptors
    - Closing the fd (program exit or explicit detach) atomically removes the hook
    - Maps are reference-counted; policy cleared by userspace map deletion
    - No kernel reboot required
    - Emergency: kill -TERM security_monitor → hooks detached in <1ms

    # Verify hook is detached:
    bpftool prog list | grep lsm   # should be empty after detach

  Production hardening checklist:
    □ CONFIG_BPF_JIT_ALWAYS_ON=y          (no interpreter: smaller attack surface)
    □ sysctl kernel.unprivileged_bpf_disabled=1
    □ sysctl kernel.perf_event_paranoid=3
    □ IMA (Integrity Measurement Architecture) for file hash policy
    □ Seccomp + BPF LSM layered defense
    □ Audit ringbuf drop counter in stats map
    □ Systemd unit with RestartSec=1 for monitor process reliability
