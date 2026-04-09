// SPDX-License-Identifier: GPL-2.0
//
// guardian_lsm_rust.rs — Guardian LSM in Rust (kernel Rust API)
//
// PREREQUISITES:
//   - Linux 6.1+ with CONFIG_RUST=y
//   - Rust nightly toolchain: rustup toolchain install nightly
//   - Kernel rust bindings: make LLVM=1 rustavailable
//
// RUST IN THE KERNEL — KEY CONCEPTS:
//
//   The kernel Rust API provides safe wrappers around C kernel primitives.
//   Instead of raw pointers you get:
//     - `ARef<T>`: a reference-counted kernel object (like Arc<T> in std)
//     - `KVec<T>`: kernel heap vector (like Vec<T> but using kmalloc)
//     - `Result<T>`: maps to 0 / -errno, just like in userspace Rust
//     - `Task`: safe wrapper around struct task_struct
//     - `Cred`: safe wrapper around struct cred
//
//   The `kernel` crate (kernel/rust/kernel/) provides bindings to:
//     - `kernel::security` — LSM hooks (EXPERIMENTAL as of 6.8)
//     - `kernel::fs` — filesystem types
//     - `kernel::print::{pr_info, pr_warn}` — printk wrappers
//     - `kernel::sync::atomic` — AtomicI32, AtomicBool, etc.
//
// NOTE: The Rust LSM API is actively developed. As of Linux 6.8, Rust LSM
// hooks are not yet stabilized upstream. This code targets the abstractions
// proposed in the Rust-for-Linux project (github.com/Rust-for-Linux/linux)
// and may require patches on top of mainline until the API is merged.

#![no_std]
// `no_std` means: do not link the standard library.
// The kernel provides its own runtime — no heap allocator from std,
// no OS threads, no panicking with stack unwinding.

extern crate alloc;

use kernel::prelude::*;
// `prelude::*` brings in commonly used kernel types:
// Module, ThisModule, Result, Error, pr_info!, pr_warn!, etc.

use kernel::{
    fs::file::File,
    security::{self, SecurityHookList},
    sync::atomic::{AtomicI32, Ordering},
    task::Task,
    ThisModule,
};

// ============================================================================
// MODULE METADATA
// ============================================================================
// The `module!` macro generates the kernel module boilerplate:
//   MODULE_LICENSE, MODULE_AUTHOR, MODULE_DESCRIPTION, etc.
// It also registers init/exit functions.

module! {
    type: GuardianLsm,
    name: "guardian_lsm_rust",
    author: "Guardian LSM Developer",
    description: "Guardian LSM — Rust implementation",
    license: "GPL",
}

// ============================================================================
// GLOBAL STATE
// ============================================================================
// AtomicI32: Rust's kernel-safe atomic integer.
// `Ordering::SeqCst` = sequentially consistent — strongest memory ordering,
// guarantees all CPUs see operations in the same order.
// For a single flag like this, `Ordering::Relaxed` would be sufficient,
// but SeqCst is clearer for educational purposes.

static GUARDIAN_ENABLED: AtomicI32 = AtomicI32::new(1);

// ============================================================================
// MODULE STRUCT
// ============================================================================
// In Rust kernel modules, you define a struct that implements the `Module`
// trait. The kernel calls `init()` at load time and calls `drop()` at unload.
// This is idiomatic Rust RAII (Resource Acquisition Is Initialization):
// resources acquired in `new()` / `init()` are released in `drop()`.

struct GuardianLsm {
    // We could hold securityfs dentries here, but for simplicity
    // we omit that in this version and rely on the C module for securityfs.
    _hooks: SecurityHookList,
}

// ============================================================================
// HOOK IMPLEMENTATIONS
// ============================================================================

/// Called before the kernel opens any file.
///
/// In Rust, kernel hook callbacks are defined as associated functions
/// (no `self` parameter) or as closures captured by the hook registration.
/// The `file_open` hook receives a `&File` — a safe Rust wrapper around
/// `struct file *` that enforces lifetimes and prevents use-after-free.
fn guardian_file_open_rust(file: &File) -> Result {
    if GUARDIAN_ENABLED.load(Ordering::SeqCst) == 0 {
        return Ok(());
    }

    // In Rust, accessing the current task is done through `Task::current()`.
    // This gives a `TaskRef` — a borrow of the current `struct task_struct`.
    // `pid()` and `comm()` are safe methods that handle the underlying
    // raw pointer access with proper lifetime guarantees.
    let task = Task::current();
    let pid  = task.pid();

    // `file.path()` returns a `Path` — safe wrapper around `struct path`.
    // `dentry().name()` returns a `&CStr` (a null-terminated kernel string).
    // We use `to_str_lossy()` to get a Rust `&str` for formatting.
    let name = file.path().dentry().name();

    pr_info!("guardian(rust): file_open pid={} file={:?}\n", pid, name);

    Ok(())  // Ok(()) in kernel Rust means "return 0"
}

/// Called before creating a new inode (file, directory, etc.).
///
/// Blocks non-privileged creation inside /tmp.
fn guardian_inode_create_rust(
    dir: &kernel::fs::inode::Inode,
    dentry: &kernel::fs::dentry::Dentry,
    _mode: kernel::fs::mode::Mode,
) -> Result {
    if GUARDIAN_ENABLED.load(Ordering::SeqCst) == 0 {
        return Ok(());
    }

    // `Task::current_cred()` returns the credentials of the calling task.
    // In Rust, we return a `CredRef` — a reference-counted safe wrapper.
    // `has_capability()` checks for a specific POSIX capability.
    let task = Task::current();
    if task.cred().has_capability(kernel::capability::CAP_DAC_OVERRIDE) {
        return Ok(());  // privileged — allow
    }

    // Build parent path. In Rust, `KVec` is the kernel heap vector.
    // This automatically calls `kfree` when `path_buf` is dropped —
    // no manual memory management needed (Rust RAII in action).
    let mut path_buf = KVec::<u8>::with_capacity(kernel::fs::path::PATH_MAX, GFP_KERNEL)?;
    let parent_path  = dentry.parent().path_string(&mut path_buf)?;

    if parent_path.starts_with("/tmp") {
        let name = dentry.name();
        pr_warn!(
            "guardian(rust): BLOCKED inode_create in {} pid={} file={:?}\n",
            parent_path,
            task.pid(),
            name
        );
        // In Rust kernel code, returning an `Err(EPERM)` translates
        // directly to `return -EPERM` in the generated C ABI layer.
        return Err(EPERM);
    }

    Ok(())
}

/// Audits UID changes.
fn guardian_task_fix_setuid_rust(
    new: &kernel::cred::Cred,
    old: &kernel::cred::Cred,
    _flags: i32,
) -> Result {
    if GUARDIAN_ENABLED.load(Ordering::SeqCst) == 0 {
        return Ok(());
    }

    let old_uid = old.uid().val();
    let new_uid = new.uid().val();

    if old_uid != new_uid {
        let task = Task::current();
        pr_info!(
            "guardian(rust): setuid pid={} {} -> {}\n",
            task.pid(),
            old_uid,
            new_uid
        );

        if new_uid == 0 && old_uid != 0 {
            pr_warn!(
                "guardian(rust): SUSPICIOUS setuid to root pid={} comm={:?}\n",
                task.pid(),
                task.comm()
            );
        }
    }

    Ok(())
}

// ============================================================================
// MODULE TRAIT IMPLEMENTATION
// ============================================================================

impl kernel::Module for GuardianLsm {
    /// Called when the module is loaded (`insmod`).
    ///
    /// `_module: &'static ThisModule` is a reference to the module descriptor.
    /// The `'static` lifetime means it lives as long as the module is loaded.
    fn init(_module: &'static ThisModule) -> Result<Self> {
        pr_info!("guardian(rust): initializing LSM\n");

        // Register our hooks with the LSM framework.
        // SecurityHookList::new() takes closures or function pointers.
        // The returned `SecurityHookList` value owns the registration;
        // when it is dropped, the hooks are automatically unregistered.
        // This is the Rust advantage: no manual cleanup in exit().
        let hooks = SecurityHookList::new()
            .file_open(guardian_file_open_rust)
            .inode_create(guardian_inode_create_rust)
            .task_fix_setuid(guardian_task_fix_setuid_rust)
            .register()?;

        pr_info!("guardian(rust): LSM initialized. Hooks registered.\n");

        Ok(GuardianLsm { _hooks: hooks })
    }
}

// ============================================================================
// AUTOMATIC CLEANUP VIA Drop TRAIT
// ============================================================================
// Rust calls `drop()` automatically when `GuardianLsm` goes out of scope
// (i.e., when the module is unloaded via `rmmod`).
// The `_hooks: SecurityHookList` field has its own `Drop` that calls
// `security_delete_hooks()`, so we do NOT need to write manual cleanup.
// This is the core Rust memory safety guarantee applied to kernel code.

impl Drop for GuardianLsm {
    fn drop(&mut self) {
        pr_info!("guardian(rust): LSM unloaded\n");
        // _hooks is dropped automatically here — hooks unregistered,
        // securityfs entries cleaned up, memory freed.
        // Compare with C: we needed explicit guardian_exit() doing all this.
    }
}
