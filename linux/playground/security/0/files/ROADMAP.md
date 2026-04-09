# Sentinel LSM — Elite Kernel Developer Roadmap & Full Reference

## Project Layout

```
security/sentinel/            ← in-tree placement
├── Kbuild
├── Kconfig.fragment          → merge into security/Kconfig
├── sentinel_lsm.c            ← C LSM (production, in-tree)
├── sentinel_lsm_buggy.c      ← intentional bugs for training
├── rust/
│   └── sentinel_lsm.rs       ← Rust companion (rust-for-linux)
├── bpf/
│   └── sentinel_bpf.c        ← BPF LSM (loadable, dev/test)
└── tests/
    └── sentinel_lsm_test.c   ← KUnit suite
```

---

## Architecture

```
 ┌─────────────────────────────────────────────────────────────────┐
 │                        User Space                               │
 │  process                     cat /etc/shadow                    │
 └───────────────────────────┬─────────────────────────────────────┘
                              │  syscall (openat)
 ┌────────────────────────────▼────────────────────────────────────┐
 │                      VFS Layer                                  │
 │  do_filp_open() → vfs_open() → security_file_open()  ◄── Hook  │
 └────────────────────────────┬────────────────────────────────────┘
                              │
 ┌────────────────────────────▼────────────────────────────────────┐
 │              Linux Security Module Framework                    │
 │                    (security/security.c)                        │
 │                                                                 │
 │  for_each_hook(file_open):                                      │
 │    SELinux   → 0 (allow)                                        │
 │    AppArmor  → 0 (allow)                                        │
 │    Sentinel  → -EACCES  ◄── our hook fires, returns deny        │
 │    BPF       → 0 (allow, or also deny)                          │
 │                                                                 │
 │  Result: first non-zero return wins (call_int_hook semantics)   │
 └─────────────────────────────────────────────────────────────────┘

 Hook registration path:
   DEFINE_LSM(sentinel) → security_add_hooks()
   → appended to hlist_head per hook-type
   → hooks stored in __lsm_ro_after_init (read-only after boot)

 Policy control plane:
   /proc/sentinel           (read-only stats, rule dump)
   /sys/kernel/security/sentinel/  (securityfs — full RW policy)

 Audit path:
   pr_warn_ratelimited → printk → /dev/kmsg → systemd-journald
   └── for production: audit_log_start() → auditd → SIEM

 BPF LSM (loadable dev path):
   sentinel_bpf.o → libbpf skeleton → bpf_prog_load()
   → SEC("lsm/file_open") attached to same hook-point
   → runs AFTER in-tree LSMs (stacking order)
```

---

## Threat Model

| Threat                        | Mitigation                                    |
|-------------------------------|-----------------------------------------------|
| Hook table tampering          | `__lsm_ro_after_init` + SMEP/SMAP/WX          |
| Spinlock starvation (DoS)     | Replace with RCU list for high-freq paths     |
| Path resolution race (TOCTOU) | Hook fires at VFS open; inode-based secondary |
| UAF in path buffer (BUG #1)   | kfree only after last use; KASAN detects it   |
| Logic inversion (BUG #2)      | KUnit tests on boundary IPs; fuzz with syzkaller|
| Privilege escalation via /proc| 0444 permissions; no write path in procfs     |
| UID spoofing                  | Use cred->uid (kernel credential, unforgeable)|
| BPF LSM bypass                | In-tree LSM cannot be bypassed by BPF order   |

---

## Step-by-step: Add Sentinel to Linus's Tree

### 0. Prerequisites

```bash
# Clone Linus's tree (read-only mirror; patch submission goes to subsystem trees)
git clone https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git
cd linux

# Install build dependencies (Debian/Ubuntu)
apt-get install -y build-essential libssl-dev libelf-dev bison flex \
    gcc-12 clang lld pahole cpio qemu-system-x86 bc

# For Rust support
rustup toolchain install $(scripts/min-tool-version.sh rustc)
rustup component add rust-src
make LLVM=1 rustavailable
```

### 1. Place the files

```bash
mkdir -p security/sentinel
cp /path/to/sentinel_lsm.c         security/sentinel/
cp /path/to/Kbuild                  security/sentinel/
cp -r /path/to/rust                 security/sentinel/
cp /path/to/tests/sentinel_lsm_test.c security/sentinel/

# Add Kconfig fragment to security/Kconfig (after AppArmor block):
cat Kconfig.fragment >> security/Kconfig

# Register the subdirectory in security/Makefile:
echo 'obj-$(CONFIG_SECURITY_SENTINEL) += sentinel/' >> security/Makefile

# Add sentinel to the default LSM order in security/Kconfig:
# Find the line: default "lockdown,yama,..."
# Append ",sentinel" to it (it goes last = lowest priority)
sed -i 's/default "lockdown,yama,loadpin,safesetid,smack,selinux,tomoyo,apparmor,bpf"/default "lockdown,yama,loadpin,safesetid,smack,selinux,tomoyo,apparmor,bpf,sentinel"/' \
    security/Kconfig
```

### 2. Configure

```bash
# Start from a minimal config (good for CI/testing)
make defconfig

# Enable sentinel (and KASAN for bug detection)
./scripts/config --enable  CONFIG_SECURITY
./scripts/config --enable  CONFIG_SECURITY_SENTINEL
./scripts/config --enable  CONFIG_SECURITY_SENTINEL_RUST  # if using Rust
./scripts/config --enable  CONFIG_KASAN
./scripts/config --enable  CONFIG_KASAN_INLINE
./scripts/config --enable  CONFIG_BPF_LSM              # for BPF companion
./scripts/config --enable  CONFIG_DEBUG_INFO_BTF        # for BPF CO-RE
./scripts/config --set-str CONFIG_LSM "lockdown,yama,apparmor,bpf,sentinel"

make olddefconfig
```

### 3. Build

```bash
# Parallel build with Clang/LLVM (recommended for Rust + LTO)
make LLVM=1 -j$(nproc) 2>&1 | tee build.log

# Check sentinel symbols are in vmlinux:
nm vmlinux | grep sentinel_
# Expected: sentinel_init, sentinel_file_open, sentinel_hooks, ...

# Verify LSM registration:
grep -r sentinel security/built-in.a 2>/dev/null || \
    objdump -t security/sentinel/sentinel_lsm.o | grep sentinel_init
```

### 4. Test in QEMU (never test LSMs on bare metal first)

```bash
# Build a minimal initramfs
mkdir -p initramfs/{bin,dev,proc,sys,etc}
cp $(which busybox) initramfs/bin/
ln -s busybox initramfs/bin/sh
cat > initramfs/init << 'EOF'
#!/bin/sh
mount -t proc  none /proc
mount -t sysfs none /sys
echo "--- Sentinel LSM test ---"
cat /proc/sentinel
echo "--- Testing file deny (should get Permission denied) ---"
cat /etc/shadow 2>&1 || true
exec sh
EOF
chmod +x initramfs/init
echo "root:x:0:0:root:/root:/bin/sh" > initramfs/etc/shadow
( cd initramfs && find . | cpio -o -H newc | gzip > ../initramfs.cpio.gz )

# Boot QEMU
qemu-system-x86_64 \
    -kernel arch/x86/boot/bzImage \
    -initrd initramfs.cpio.gz \
    -append "console=ttyS0 lsm=lockdown,yama,apparmor,bpf,sentinel nokaslr" \
    -nographic -m 512M -cpu host -enable-kvm \
    -serial mon:stdio

# Expected dmesg output:
#   sentinel: LSM initialised (version 0.2.0, hooks=3)
# Expected cat /etc/shadow output:
#   cat: /etc/shadow: Permission denied
```

### 5. Run KUnit tests

```bash
# Via kunit.py (UML — no reboot needed)
./tools/testing/kunit/kunit.py run \
    --kunitconfig=security/sentinel/.kunitconfig \
    --arch=um \
    -- sentinel_lsm

# Expected output:
# KTAP version 1
# ok 1 sentinel_test_10_slash_8
# ok 2 sentinel_test_172_16_slash_12_correct
# ok 3 sentinel_test_172_16_slash_12_buggy
# ok 4 sentinel_test_192_168_slash_16
# ok 5 sentinel_test_public_ips
# ok 6 sentinel_test_path_prefix
# # Totals: pass:6 fail:0 skip:0 total:6
```

---

## Debugging Techniques

### KASAN (BUG #1 — UAF detection)

```bash
# Build with KASAN:
./scripts/config --enable CONFIG_KASAN
./scripts/config --enable CONFIG_KASAN_INLINE
make LLVM=1 -j$(nproc)

# Boot QEMU and trigger the buggy open:
# In QEMU shell: cat /etc/shadow

# KASAN output in dmesg:
# ==================================================================
# BUG: KASAN: use-after-free in sentinel_file_open+0x8f/0x120
# Read of size 1 at addr ffff888003e5c1a0 by task cat/123
#
# CPU: 0 PID: 123 Comm: cat
# Call Trace:
#  kasan_report+0x...
#  sentinel_file_open+0x8f/0x120
#  security_file_open+0x...
#  do_filp_open+0x...
# Freed by task 123:
#  kfree+0x...
#  sentinel_file_open+0x7a/0x120   ← kfree called too early
```

### ftrace / function tracer

```bash
# Trace sentinel hooks in real-time:
echo sentinel_file_open > /sys/kernel/debug/tracing/set_ftrace_filter
echo function > /sys/kernel/debug/tracing/current_tracer
echo 1 > /sys/kernel/debug/tracing/tracing_on
cat /etc/shadow 2>/dev/null || true
cat /sys/kernel/debug/tracing/trace | grep sentinel
echo 0 > /sys/kernel/debug/tracing/tracing_on
```

### kgdb / QEMU remote GDB

```bash
# Boot QEMU with gdbserver:
qemu-system-x86_64 ... -s -S &   # -s = :1234, -S = pause at start

# Attach GDB with kernel symbols:
gdb vmlinux
(gdb) target remote :1234
(gdb) break sentinel_file_open
(gdb) continue
# Now trigger: cat /etc/shadow in QEMU
# GDB will break at sentinel_file_open
(gdb) print *file
(gdb) print path
(gdb) print buf
(gdb) next  # step through — observe UAF point
```

### syzkaller fuzzing setup (abbreviated)

```bash
# syzkaller will fuzz syscalls and trigger LSM hooks.
# Key syszkaller config additions for LSM coverage:
# "enable_syscalls": ["openat", "connect", "execve"]
# Requires: KCOV=y, KCSAN=y (for data-race detection too)
./scripts/config --enable CONFIG_KCOV
./scripts/config --enable CONFIG_KCSAN
# Build + point syzkaller workdir at QEMU image.
# Full guide: https://github.com/google/syzkaller/blob/master/docs/linux/setup.md
```

---

## Bug Fixes (diff format)

### BUG #1 Fix (UAF)

```diff
--- sentinel_lsm_buggy.c
+++ sentinel_lsm.c
@@ sentinel_file_open()
-       /* ❌ kfree(buf) called here — path dangles */
-       kfree(buf);
-
        cred = current_cred();

        spin_lock(&sentinel_lock);
        for (i = 0; i < sentinel_rule_count; i++) {
                ...strncmp(path, ...)...   /* path still valid */
        }
        spin_unlock(&sentinel_lock);

+       kfree(buf);   /* ✅ freed AFTER last use of path */
        return ret;
```

### BUG #2 Fix (logic)

```diff
--- sentinel_lsm_buggy.c
+++ sentinel_lsm.c
@@ is_rfc1918()
-       || ((ip >> 24) == 172)          /* ❌ /8 — wrong range */
+       || ((ip >> 20) == 0xAC1)        /* ✅ 172.16.0.0/12 — correct */
```

---

## Documentation References

### Mandatory reading (in order)

1. `Documentation/process/howto.rst`               — Kernel contribution process
2. `Documentation/process/submitting-patches.rst`  — Patch format, sign-off, cover letter
3. `Documentation/security/lsm.rst`                — LSM overview
4. `Documentation/security/lsm-development.rst`    — Hook authoring guide
5. `include/linux/lsm_hooks.h`                     — All hook signatures + comments
6. `security/security.c`                           — Framework implementation (read fully)
7. `security/selinux/hooks.c`                      — Reference LSM (copy patterns from here)
8. `Documentation/dev-tools/kunit/index.rst`       — KUnit testing
9. `Documentation/dev-tools/kasan.rst`             — KASAN memory error detection
10. `Documentation/bpf/prog_lsm.rst`               — BPF LSM (KRSI)

### Rust for Linux

11. `Documentation/rust/index.rst`
12. `Documentation/rust/kernel-crate.rst`
13. `samples/rust/`                                — In-tree Rust examples
14. https://rust-for-linux.com/lsm-security-modules
15. https://lore.kernel.org/linux-security-module/ — Rust LSM patch series

### Deep-dive books / resources

16. *Linux Kernel Development* — Robert Love (3rd ed.)
17. *Understanding the Linux Kernel* — Bovet & Cesati (3rd ed.)
18. *Linux Device Drivers* — Corbet, Rubini, Kroah-Hartman (free online)
19. https://elixir.bootlin.com/linux/latest — Cross-reference (use instead of grep)
20. https://lore.kernel.org/lsm/              — LSM mailing list archive

### Mailing lists to subscribe to

- linux-kernel@vger.kernel.org      (LKML)
- linux-security-module@vger.kernel.org
- linux-hardening@vger.kernel.org
- rust-for-linux@vger.kernel.org

---

## Elite Kernel Developer Roadmap

### Phase 1 — Foundation (months 1–3)
- [ ] Read Documentation/process/* end-to-end
- [ ] Submit 5 trivial fixes (typos, docs, checkpatch) to feel the process
- [ ] Read security/security.c and security/selinux/hooks.c completely
- [ ] Build and boot a custom kernel in QEMU daily

### Phase 2 — LSM Internals (months 3–6)
- [ ] Implement and boot this sentinel LSM in QEMU
- [ ] Add securityfs R/W policy interface (security/sentinel/securityfs.c)
- [ ] Write syzkaller reproducers for LSM hook paths
- [ ] Instrument with KASAN + KCOV; achieve >80% hook coverage

### Phase 3 — Subsystem Ownership (months 6–12)
- [ ] Port the C LSM to Rust using upstream rust-lsm abstractions
- [ ] Contribute Rust LSM abstraction patches to rust-for-linux
- [ ] Submit RFC patch series to linux-security-module@vger.kernel.org
- [ ] Survive review from Kees Cook, Paul Moore, James Morris

### Phase 4 — Production & Community (year 2+)
- [ ] Maintain sentinel in a -next tree (security/next branch)
- [ ] Integrate with audit framework (audit_log_start/audit_log_end)
- [ ] Integrate with IMA/EVM for binary policy signing
- [ ] Present at Linux Security Summit or LPC

---

## Next 3 Steps

1. **Boot it**: Clone Linus's tree, place the files, run `make defconfig` + enable
   CONFIG_SECURITY_SENTINEL + CONFIG_KASAN, boot in QEMU, observe `sentinel:
   LSM initialised` in dmesg, then trigger `cat /etc/shadow` as non-root.

2. **Trigger BUG #1 with KASAN**: Swap sentinel_lsm.c for sentinel_lsm_buggy.c,
   rebuild, boot in QEMU with KASAN enabled, `cat /etc/shadow`, and read the
   KASAN use-after-free report. Apply the one-line fix and verify it disappears.

3. **Run KUnit + add boundary tests**: Set up kunit.py with UML, run the test suite,
   then add two new KUNIT_CASE entries that test the `sentinel_test_path_prefix`
   edge case (`/etc/shadow~` matching) and decide if that's the desired behaviour
   (it probably isn't — fix the strncmp to require exact match or trailing `/\0`).
