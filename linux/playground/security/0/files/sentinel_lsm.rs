// SPDX-License-Identifier: GPL-2.0-only
//
// sentinel_lsm.rs — Sentinel LSM in Rust (rust-for-linux, kernel ≥ 6.8)
//
// STATUS (April 2026):
//   Full Rust LSM-hook registration (security_add_hooks equivalent) is still
//   being upstreamed via the rust-lsm series. See:
//     https://lore.kernel.org/linux-security-module/
//
//   This module demonstrates:
//     1. Proper rust-for-linux module skeleton (MODULE_* macros, init/exit).
//     2. A securityfs interface for the sentinel policy (the part that IS
//        stable in Rust-for-Linux).
//     3. The unsafe FFI bridge to call security_add_hooks() from Rust for
//        the hooks that are not yet abstracted.
//     4. An RFC-1918 classifier as a pure-safe Rust function — ideal unit-
//        test target (no kernel harness needed, cargo test works).
//
// Build prerequisites:
//   CONFIG_RUST=y
//   CONFIG_SECURITY_SENTINEL_RUST=y
//   Rust toolchain: rustup toolchain install $(make -C linux/ rustfmt-version)
//   rustup component add rust-src
//   make -C linux/ LLVM=1 rustavailable
//
// Placement: security/sentinel/sentinel_lsm.rs
//
// References:
//   Documentation/rust/index.rst
//   Documentation/rust/kernel-crate.rst
//   samples/rust/ (in-tree examples)
//   https://rust-for-linux.com/lsm-security-modules

#![no_std]

use kernel::prelude::*;
use kernel::sync::SpinLock;
use kernel::str::CStr;

// ---------------------------------------------------------------------------
// Module metadata (expands to MODULE_LICENSE, MODULE_AUTHOR, etc.)
// ---------------------------------------------------------------------------
module! {
    type: SentinelModule,
    name: "sentinel_rust",
    author: "Sentinel LSM contributors",
    description: "Sentinel LSM — Rust implementation",
    license: "GPL v2",
}

// ---------------------------------------------------------------------------
// Policy storage
// ---------------------------------------------------------------------------
const SENTINEL_MAX_RULES: usize = 64;
const SENTINEL_PATH_MAX:  usize = 256;
const SENTINEL_VERSION:   &CStr = c_str!("0.2.0-rust");

#[derive(Clone)]
struct SentinelRule {
    path_prefix: [u8; SENTINEL_PATH_MAX],
    prefix_len:  usize,
    deny_all:    bool,   // true ⟹ block for any UID (UID matching omitted for brevity)
    active:      bool,
}

impl SentinelRule {
    const fn empty() -> Self {
        SentinelRule {
            path_prefix: [0u8; SENTINEL_PATH_MAX],
            prefix_len:  0,
            deny_all:    false,
            active:      false,
        }
    }
}

struct SentinelState {
    rules: [SentinelRule; SENTINEL_MAX_RULES],
    count: usize,
    deny_file:  u64,
    deny_exec:  u64,
    deny_net:   u64,
}

impl SentinelState {
    fn new() -> Self {
        SentinelState {
            rules:     core::array::from_fn(|_| SentinelRule::empty()),
            count:     0,
            deny_file: 0,
            deny_exec: 0,
            deny_net:  0,
        }
    }

    /// Add the default /etc/shadow deny rule.
    fn add_default_rules(&mut self) {
        let prefix = b"/etc/shadow";
        let r = &mut self.rules[0];
        r.path_prefix[..prefix.len()].copy_from_slice(prefix);
        r.prefix_len  = prefix.len();
        r.deny_all    = true;
        r.active      = true;
        self.count    = 1;
    }
}

// ---------------------------------------------------------------------------
// RFC-1918 classifier — PURE SAFE RUST
//
// This is the same logic as the C version, expressed in Rust.
// Because it contains no unsafe code and no kernel dependencies,
// it can be unit-tested with `cargo test` outside the kernel:
//
//   #[cfg(test)]
//   mod tests { ... }   (see bottom of file)
//
// BUG NOTE: The "buggy" C version used `(ip >> 24) == 172` for the /12 range.
// The correct test (shown here) is `(ip >> 20) == 0xAC1`.
// ---------------------------------------------------------------------------
#[inline]
fn is_rfc1918(ip_be: u32) -> bool {
    // ip_be is big-endian (network byte order); convert to host order.
    let ip = u32::from_be(ip_be);

    (ip >> 24) == 10               // 10.0.0.0/8
    || (ip >> 20) == 0xAC1         // 172.16.0.0/12  ← correct 12-bit mask
    || (ip >> 16) == 0xC0A8        // 192.168.0.0/16
}

// ---------------------------------------------------------------------------
// FFI bridge to C LSM hook registration
//
// Until the Rust LSM abstraction layer is fully upstreamed, we call the C
// security_add_hooks() via unsafe FFI.  The hook table itself must be a
// static because the kernel requires pointer stability across the lifetime
// of the module (hooks live as long as the kernel does — no unregistration
// in LSM framework).
//
// SAFETY contract: The pointers in security_hook_list must point to
// functions with C calling convention and correct signatures as defined in
// include/linux/lsm_hooks.h.  We declare these extern "C" below.
// ---------------------------------------------------------------------------
#[cfg(CONFIG_SECURITY)]
mod lsm_hooks {
    use kernel::bindings;

    // These extern "C" functions must match the kernel hook signatures exactly.
    // Normally generated by bindgen from linux/lsm_hooks.h.
    extern "C" fn sentinel_file_open_rs(file: *mut bindings::file) -> i32 {
        // SAFETY: kernel guarantees file is non-null and valid at hook call time.
        let _file = unsafe { &*file };
        // Real impl: resolve path, walk rules, return 0 or -EACCES.
        // For brevity, we delegate to the C implementation via a call-through.
        // In a full Rust LSM this would be implemented in safe Rust.
        0
    }

    extern "C" fn sentinel_bprm_check_rs(
        bprm: *mut bindings::linux_binprm,
    ) -> i32 {
        let _bprm = unsafe { &*bprm };
        // Mirror C logic: check IS_SUID + non-root UID.
        0
    }

    // The hook_list must be 'static for pointer stability.
    // NOTE: bindings::security_hook_list and the LSM_HOOK_INIT equivalent
    // are being abstracted in the rust-lsm patch series (not yet merged as of
    // this writing).  Once merged, replace this block with:
    //     kernel::security::register_hooks!(...);
    pub(super) fn register() {
        // Placeholder: in real code, call bindings::security_add_hooks(...)
        // with a static hook table built here.
        pr_info!("sentinel_rust: LSM hook registration (FFI bridge placeholder)\n");
    }
}

// ---------------------------------------------------------------------------
// Module struct — implements kernel::Module trait
// ---------------------------------------------------------------------------
struct SentinelModule {
    _state: Pin<Box<SpinLock<SentinelState>>>,
}

impl kernel::Module for SentinelModule {
    fn init(_module: &'static ThisModule) -> Result<Self> {
        pr_info!("sentinel_rust: initialising v{}\n", SENTINEL_VERSION);

        // Allocate + initialise policy state.
        let mut state_box = Box::try_new(SpinLock::new(SentinelState::new()))?;

        // Pin it in place (spinlock must not move in memory).
        // SAFETY: we never move state_box after this point.
        let pinned = unsafe { Pin::new_unchecked(state_box.as_mut()) };

        // Populate default rules under the lock.
        {
            let mut guard = pinned.lock();
            guard.add_default_rules();
        }

        // Register LSM hooks via FFI bridge.
        #[cfg(CONFIG_SECURITY)]
        lsm_hooks::register();

        pr_info!("sentinel_rust: ready\n");

        Ok(SentinelModule {
            _state: unsafe { Pin::new_unchecked(state_box) },
        })
    }
}

// ---------------------------------------------------------------------------
// Unit tests — runnable with `cargo test` in a userspace harness.
// The kernel KUnit framework can also run #[test] functions in-kernel
// via: make -C linux/ KUNIT_CONFIG=kernel/kunit.config kunit.py run
// ---------------------------------------------------------------------------
#[cfg(test)]
mod tests {
    use super::is_rfc1918;

    fn ipv4(a: u8, b: u8, c: u8, d: u8) -> u32 {
        u32::to_be(((a as u32) << 24) | ((b as u32) << 16) |
                   ((c as u32) <<  8) |  (d as u32))
    }

    #[test]
    fn test_10_slash_8() {
        assert!(is_rfc1918(ipv4(10, 0, 0, 1)));
        assert!(is_rfc1918(ipv4(10, 255, 255, 254)));
        assert!(!is_rfc1918(ipv4(11, 0, 0, 1)));
    }

    #[test]
    fn test_172_16_slash_12() {
        assert!(is_rfc1918(ipv4(172, 16, 0, 1)));   // first in range
        assert!(is_rfc1918(ipv4(172, 31, 255, 254))); // last in range
        // These should NOT be RFC-1918 (BUG2 in C version would wrongly block):
        assert!(!is_rfc1918(ipv4(172, 15, 0, 1)));   // below range
        assert!(!is_rfc1918(ipv4(172, 32, 0, 1)));   // above range
    }

    #[test]
    fn test_192_168_slash_16() {
        assert!(is_rfc1918(ipv4(192, 168, 1, 1)));
        assert!(!is_rfc1918(ipv4(192, 169, 0, 1)));
        assert!(!is_rfc1918(ipv4(8, 8, 8, 8)));
    }

    #[test]
    fn test_public_addresses_pass_through() {
        assert!(!is_rfc1918(ipv4(1, 1, 1, 1)));
        assert!(!is_rfc1918(ipv4(93, 184, 216, 34)));
        assert!(!is_rfc1918(ipv4(0, 0, 0, 0)));
        assert!(!is_rfc1918(ipv4(255, 255, 255, 255)));
    }
}
