---

## Summary

The **Sentinel LSM** is a stacked Linux Security Module that hooks `file_open`, `bprm_check_security`, and `socket_connect` — three of the highest-value hook points for host-based intrusion containment. It must be compiled **in-tree** (`DEFINE_LSM` is not loadable as `.ko`; the kernel removed that capability intentionally to prevent malicious modules from registering hooks). The codebase ships in C (production), Rust (rust-for-linux ≥ 6.8), and a BPF/KRSI version (loadable, for fast iteration without reboots). Two intentional bugs are planted — one UAF memory-safety bug and one logic error in RFC-1918 detection — each with KASAN/KUnit reproduction paths and one-line fixes.

---

## Architecture

```
  User space: cat /etc/shadow
         │  syscall openat(2)
         ▼
  ┌─────────────────────────────────────────────────┐
  │  VFS: do_filp_open → vfs_open                   │
  │         └─► security_file_open()  (security.c)  │
  └──────────────────┬──────────────────────────────┘
                     │  call_int_hook(file_open, ...)
        ┌────────────┼────────────┐
        ▼            ▼            ▼
    SELinux      AppArmor      Sentinel  ←── our code
      0(ok)        0(ok)       -EACCES ← first non-zero wins
                               │
                 pr_warn_ratelimited → dmesg
                 atomic64_inc(cnt_file_deny)

  Hook table (__lsm_ro_after_init → read-only after init):
  sentinel_hooks[] → security_add_hooks() → hlist_head per hook-type
```

---

## Key design decisions and why

**Why `DEFINE_LSM` not `module_init`?** The kernel deliberately removed loadable LSM support around 3.x. A `.ko` with `security_add_hooks()` would work at build time but is architecturally wrong — any rootkit could do the same. `DEFINE_LSM` runs during `security_init()` (before SMP, before userspace) and the hook table goes into `__lsm_ro_after_init` (write-protected by `mark_rodata_ro()`).

**Why `__lsm_ro_after_init` on the hook table?** After `sentinel_init()` returns, the memory page holding `sentinel_hooks[]` is flipped to read-only by the kernel's `mark_rodata_ro()` call. A kernel exploit cannot overwrite hook pointers without first defeating SMEP/SMAP + page-table protections.

**Why `GFP_ATOMIC` for the path buffer?** `file_open` hooks can be called from interrupt context (e.g., a file opened during IRQ handling). `GFP_KERNEL` would sleep, causing a BUG splat. Fail-open on allocation failure is a deliberate trade-off — use per-CPU pre-allocated buffers in production.

**Why `pr_warn_ratelimited` not `pr_warn`?** Without rate limiting, a process tight-looping `open()` on a denied path floods the kernel ring buffer and degrades system performance (an easy DoS).

---

## The Two Bugs, Explained Fully

### BUG #1 — Use-After-Free (`sentinel_lsm_buggy.c` line ~90)

```
SEQUENCE IN BUGGY CODE:
  buf  = kzalloc(256)           →  buf = 0xffff888003e5c000
  path = d_path(..., buf, 256)  →  path = 0xffff888003e5c080  (pointer INTO buf)
  kfree(buf)                    →  slab marks 0xffff888003e5c000 as free ← BUG
  strncmp(path, ...)            →  reads from 0xffff888003e5c080 = FREED MEMORY
```

KASAN catches it immediately because it poisons the freed slab slot. Without KASAN, the race window is small but real: the allocator can reuse the block between `kfree` and `strncmp`, silently corrupting the comparison and flipping the policy result (either false-deny or false-allow — both are security failures).

**Fix:** single `kfree(buf)` at function exit, after all uses of `path`.

### BUG #2 — Logic error in `is_rfc1918` (`sentinel_lsm_buggy.c` line ~155)

```
RFC-1918 range 172.16.0.0/12:
  Top 12 bits must equal 0b1010_1100_0001 = 0xAC1
  Test: (ip >> 20) == 0xAC1

Buggy code:
  (ip >> 24) == 172  →  tests only top 8 bits  →  matches 172.0.0.0/8

Effect:
  172.0.0.1   → wrongly BLOCKED (not RFC-1918)
  172.15.0.1  → wrongly BLOCKED (not RFC-1918)
  172.32.0.1  → wrongly BLOCKED (not RFC-1918)
  172.16.0.1  → correctly blocked
```

Security impact: legitimate outbound traffic to publicly-routable 172.x/8 IPs is silently dropped. The KUnit test `sentinel_test_172_16_slash_12_correct` catches this precisely because it tests the boundary values `172.15.x` and `172.32.x`.

---

## The Three Implementations

| Dimension | C in-tree LSM | Rust in-tree | BPF/KRSI |
|---|---|---|---|
| **Loadable** | No (in vmlinux) | No (in vmlinux) | Yes (`.o` via libbpf) |
| **Hook type** | `DEFINE_LSM` | `DEFINE_LSM` + FFI | `SEC("lsm/...")` |
| **Memory safety** | Manual + KASAN | Rust borrow checker | BPF verifier |
| **Policy update** | Reboot | Reboot | `bpf_map_update_elem` live |
| **LSM rust abstractions** | N/A | Partial (6.8+) | N/A |
| **Best for** | Production | Future production | Dev/test iteration |

The BPF version (`sentinel_bpf.c`) is your **development inner loop** — you edit it, `clang -target bpf` compile it, load it with bpftool/libbpf, and test without rebooting. Once the policy logic is solid, port it to the in-tree C/Rust version and go through the kernel patch submission process.

---

## Rust Status (Honest)

As of kernel 6.12/6.13, the `kernel::security` Rust abstraction layer is being upstreamed via the [rust-lsm patch series](https://lore.kernel.org/linux-security-module/). The `sentinel_lsm.rs` file shows:

- The correct `module! {}` skeleton (stable since 6.1)
- `SpinLock<T>` with `Pin<Box<>>` (stable)
- The `is_rfc1918()` pure-safe function — **testable with `cargo test` outside the kernel right now**
- The FFI bridge via `kernel::bindings` for hooks not yet abstracted
- `#[cfg(test)]` unit tests that reproduce exactly the BUG #2 boundary cases

The Rust tests in `sentinel_lsm.rs` are the fastest feedback loop in the entire codebase — run them with `cargo test` before any kernel build:

```bash
cd sentinel_lsm/rust
# Stub a minimal kernel crate mock, then:
cargo test 2>&1 | grep -E 'test |FAILED|ok'
```

---

## Documentation References (ordered by priority)

```
PROCESS:
  Documentation/process/howto.rst                   ← read first, no exceptions
  Documentation/process/submitting-patches.rst      ← your patch will be rejected
  Documentation/process/coding-style.rst              without reading this

LSM FRAMEWORK:
  Documentation/security/lsm.rst                   ← LSM stacking model
  Documentation/security/lsm-development.rst        ← hook authoring
  include/linux/lsm_hooks.h                         ← ALL hook signatures
  security/security.c                               ← call_int_hook, framework
  security/selinux/hooks.c                          ← best reference LSM

DEBUGGING / TESTING:
  Documentation/dev-tools/kasan.rst
  Documentation/dev-tools/kunit/index.rst
  Documentation/dev-tools/kunit/usage.rst
  Documentation/trace/ftrace.rst

BPF LSM:
  Documentation/bpf/prog_lsm.rst
  tools/testing/selftests/bpf/progs/lsm.c           ← in-tree BPF LSM examples

RUST FOR LINUX:
  Documentation/rust/index.rst
  Documentation/rust/kernel-crate.rst
  samples/rust/                                      ← rust_minimal.rs is hello-world
  https://rust-for-linux.com/lsm-security-modules

MAILING LISTS (subscribe, read, then post):
  linux-security-module@vger.kernel.org
  linux-hardening@vger.kernel.org
  rust-for-linux@vger.kernel.org
  lore.kernel.org/lsm/                              ← archive search
```

---

## Next 3 Steps

1. **Boot and verify in QEMU today**: Clone Linus's tree, run the placement commands from `ROADMAP.md`, `make defconfig` + enable `CONFIG_SECURITY_SENTINEL` + `CONFIG_KASAN`, boot in QEMU, confirm `sentinel: LSM initialised` in dmesg, then `cat /etc/shadow` as non-root UID — you must see `Permission denied` and `sentinel: DENY file_open` in dmesg. This proves the full hook → VFS → policy → audit path.

2. **Trigger and fix BUG #1 under KASAN**: Swap to `sentinel_lsm_buggy.c`, rebuild with KASAN, boot, trigger `cat /etc/shadow`, read the KASAN use-after-free report with its full call trace. Apply the one-line `kfree` move, rebuild, confirm the report disappears. This drill is the core muscle memory of kernel debugging.

3. **Run the Rust unit tests standalone then in KUnit**: In the `rust/` directory, stub a minimal `no_std` harness and run `cargo test` — the `test_172_16_slash_12` tests will catch BUG #2 immediately without building a kernel. Then set up `kunit.py` with UML and run `sentinel_lsm_test.c` against the C implementation to close the loop between the language-level tests and the kernel integration tests.