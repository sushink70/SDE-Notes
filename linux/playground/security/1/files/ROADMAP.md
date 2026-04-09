# auditsec — Developer Roadmap & Upstream Workflow
# =====================================================================
# Documentation references used to write this module and this guide
# =====================================================================

## KERNEL SOURCE FILES READ TO BUILD THIS MODULE

### Core LSM framework
  include/linux/security.h          — public LSM API; security_*()/security_add_hooks()
  include/linux/lsm_hooks.h         — struct security_hook_list, LSM_HOOK_INIT macro
  security/security.c               — call_int_hook(), lsm_add_hooks(), hook dispatch
  security/Kconfig                  — LSM_ORDER, SECURITY_LOADABLE_LSMLIST
  security/commoncap.c              — capability LSM (always-first in stack)

### Existing LSMs to study as reference
  security/selinux/hooks.c          — most complete LSM hook implementation
  security/apparmor/lsm.c           — simpler, well-commented
  security/bpf.c                    — BPF LSM, modern stacking example
  security/landlock/fs.c            — Rust-friendly LSM design, v5.13+

### Kernel call sites for each hook
  fs/open.c                         — do_dentry_open() → security_file_open()
  fs/exec.c                         — bprm_execve() → security_bprm_check()
  fs/namei.c                        — inode_permission() → security_inode_permission()
  net/socket.c                      — __sys_socket() → security_socket_create()
  kernel/signal.c                   — check_kill_permission() → security_task_kill()
  mm/mmap.c                         — mmap_region() → security_mmap_file()

### Data structures
  include/linux/fs.h                — struct file, struct inode, struct dentry
  include/linux/binfmts.h           — struct linux_binprm
  include/linux/sched.h             — struct task_struct
  include/linux/cred.h              — struct cred, current_uid()
  include/linux/dcache.h            — dentry_path_raw()

### Module infrastructure
  include/linux/module.h            — MODULE_* macros, module_init/exit
  include/linux/kobject.h           — kobject_create_and_add()
  include/linux/sysfs.h             — sysfs_create_group(), kobj_attribute

### Rust subsystem
  rust/kernel/                      — Rust kernel API (v6.1+)
  rust/kernel/security.rs           — LSM Rust bindings (in-flight)
  Documentation/rust/index.rst      — Rust-in-kernel overview

## OFFICIAL DOCUMENTATION

### Must-read before writing any kernel code
  Documentation/process/coding-style.rst         — Linux kernel C style
  Documentation/process/submitting-patches.rst   — patch format & workflow
  Documentation/process/development-process.rst  — kernel release cycle
  Documentation/process/email-clients.rst        — git send-email setup
  Documentation/process/maintainer-pgp-guide.rst — GPG key signing

### Security subsystem
  Documentation/security/lsm.rst                 — LSM developer guide
  Documentation/security/lsm-development.rst     — LSM policy design guide
  Documentation/security/credentials.rst         — credential model
  Documentation/security/keys/                   — kernel keyring

### Build system
  Documentation/kbuild/makefiles.rst             — kbuild module writing
  Documentation/kbuild/kconfig-language.rst      — Kconfig syntax
  Documentation/kbuild/modules.rst               — out-of-tree modules

### Debugging tools
  Documentation/trace/ftrace.rst                 — function/graph tracing
  Documentation/trace/kprobes.rst                — kprobe tracing
  Documentation/dev-tools/kasan.rst              — KASAN memory error detection
  Documentation/dev-tools/ubsan.rst              — undefined behaviour sanitiser
  Documentation/dev-tools/kcsan.rst              — data-race detection
  Documentation/admin-guide/kdump/kdump.rst      — crash dump analysis
  Documentation/admin-guide/dynamic-debug-howto.rst — pr_debug() runtime control

### Rust
  Documentation/rust/coding-guidelines.rst
  Documentation/rust/arch-support.rst
  Documentation/rust/kernel-crate.rst

## EXTERNAL REFERENCES

  LWN.net: "The Linux Security Module Framework" (2002, still accurate on basics)
           https://lwn.net/Articles/14313/
  LWN.net: "BPF LSM" series (2020)
           https://lwn.net/Articles/798157/
  LWN.net: "Rust in the kernel" (2022+)
           https://lwn.net/Articles/908347/
  Kernel Newbies: https://kernelnewbies.org/WritingModules
  LKML:    lore.kernel.org/linux-security-module/
  aya-rs (BPF+Rust): https://aya-rs.dev/book/

## FULL DEVELOPER ROADMAP — FROM ZERO TO ELITE CONTRIBUTOR
# =====================================================================

### STAGE 1 — Environment (Week 1–2)
  [ ] Install KVM + libvirt on Kali host
  [ ] Clone kernel: git clone https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git
  [ ] Build minimal KVM kernel:
        make kvmconfig
        scripts/config --enable CONFIG_KASAN --enable CONFIG_DEBUG_INFO
        make -j$(nproc) && make modules_install
  [ ] Boot custom kernel in KVM VM1
  [ ] Subscribe to LKML: https://subspace.kernel.org/lists.linux.dev.html
  [ ] Subscribe to LSM list: linux-security-module@vger.kernel.org

### STAGE 2 — Read the code (Week 2–4)
  [ ] Read security/security.c top-to-bottom
  [ ] Read security/apparmor/lsm.c (simpler than SELinux)
  [ ] Trace a syscall: open("/etc/hostname") → VFS → LSM hook → your module
      Tool: sudo bpftrace -e 'kprobe:security_file_open { printf("%s\n", comm); }'
  [ ] Study struct task_struct: include/linux/sched.h
  [ ] Study LSM stacking: Documentation/security/lsm.rst §"Stacking"

### STAGE 3 — Build this module (Week 3–5)
  [ ] make (out-of-tree build)
  [ ] Run checkpatch.pl — zero warnings required for upstream
  [ ] Run sparse (make sparse) — fix all errors
  [ ] Run coccicheck — apply null-check patterns
  [ ] Load in KVM VM2 (stable kernel)
  [ ] Run auditsec_test.sh all
  [ ] Reproduce BUG-1 with KASAN, read the report
  [ ] Reproduce BUG-2, confirm correct fix with test

### STAGE 4 — Debugging mastery (Week 5–7)
  [ ] ftrace: trace security_file_open call graph
  [ ] kprobes: write a bpftrace script counting LSM denials per second
  [ ] KASAN: build kernel with KASAN, trigger BUG-1, read symbolised trace
  [ ] kdump: configure crash kernel, trigger BUG-1, analyse vmcore with crash(8)
  [ ] kgdb: attach GDB to KVM, set breakpoint in auditsec_bprm_check
  [ ] perf record + perf report on the module's hot path

### STAGE 5 — Upstream workflow (Week 7–10)
  [ ] Read Documentation/process/submitting-patches.rst in full
  [ ] Configure git send-email:
        git config sendemail.smtpserver smtp.gmail.com
        git config sendemail.smtpencryption tls
  [ ] Install b4: pip install b4
  [ ] Format patch:
        git format-patch -1 --subject-prefix="RFC PATCH security"
  [ ] Run checkpatch on the formatted patch (must be clean)
  [ ] Find maintainer:
        ./scripts/get_maintainer.pl security/auditsec/auditsec.c
  [ ] Send to subsystem list (NOT Linus directly):
        b4 send --to linux-security-module@vger.kernel.org
  [ ] Respond to review comments within 48 hours
  [ ] Version the patch: v2, v3 with changelog

### STAGE 6 — Advanced topics (Month 3+)
  [ ] Study SELinux type enforcement (security/selinux/te_avtab.c)
  [ ] Study Landlock — resource-based sandboxing, v5.13
  [ ] BPF LSM programs (aya-rs + CONFIG_BPF_LSM=y)
  [ ] Write Rust LSM once bindings land (track rust-for-linux ML)
  [ ] Contribute a real bug fix to security/: start with Documentation fixes
  [ ] Review other people's patches on linux-security-module list

## PATCH COMMIT MESSAGE FORMAT (kernel standard)
#
# First line: <subsystem>: <summary in imperative mood, ≤72 chars>
# Body: what, why (not how — the diff shows how)
# Closes/Fixes tag if applicable
# Signed-off-by: Your Name <email>
#
# Example:
#
# security/auditsec: fix null dereference in file_open hook
#
# dentry_path_raw() dereferences the dentry argument unconditionally.
# When called from file_open with an anonymous file (pipe, socketpair),
# file->f_path.dentry is NULL, causing a NULL pointer dereference.
#
# Add a NULL check before calling dentry_path_raw() and log a static
# "<anon/pipe/socket>" string for anonymous files instead.
#
# Fixes: abcdef012345 ("security/auditsec: add file_open hook")
# Reported-by: test-robot@intel.com
# Signed-off-by: Your Name <your@email.org>

## GIT WORKFLOW FOR KERNEL DEVELOPMENT

  # Track Linus's tree
  git remote add linus https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git

  # Track subsystem tree (security)
  git remote add pcmoore https://git.kernel.org/pub/scm/linux/kernel/git/pcmoore/security.git
  git fetch pcmoore
  git checkout -b auditsec-fix pcmoore/next

  # Make your change, then:
  git add security/auditsec/auditsec.c
  git commit -s   # -s adds Signed-off-by automatically

  # Format patch for sending
  git format-patch -1 --cover-letter -o patches/

  # Check it
  ./scripts/checkpatch.pl patches/0001-*.patch

  # Get maintainers
  ./scripts/get_maintainer.pl patches/0001-*.patch

  # Send (b4 handles threading and message-id)
  b4 send patches/0001-*.patch
