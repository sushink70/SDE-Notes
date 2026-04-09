// SPDX-License-Identifier: GPL-2.0
// Copyright (C) auditsec-demo
//
// auditsec_rust — Rust port of the auditsec LSM.
//
// Requires: CONFIG_RUST=y, CONFIG_SECURITY=y
// Kernel Rust API refs:
//   rust/kernel/security.rs       — LSM trait definitions (in-flight upstream)
//   rust/kernel/task.rs           — Task, current()
//   rust/kernel/cred.rs           — Cred, uid()
//   rust/kernel/fs/file.rs        — File, path()
//   rust/kernel/net/socket.rs     — Socket
//   Documentation/rust/index.rst — Rust-in-kernel overview
//
// STATUS: Rust LSM bindings are still partially in-flight as of v6.8.
//   The BPF LSM + Rust combination (security/bpf.c + rust BPF programs)
//   is the most practical Rust+security path TODAY.
//   This file shows the target API shape once rust/kernel/security.rs lands.
//   Track: https://lore.kernel.org/rust-for-linux/ "[RFC] Rust LSM bindings"
//
// To compile: add to rust/ subdirectory under kernel tree with
//   obj-$(CONFIG_SECURITY_AUDITSEC_RUST) += auditsec_rust.o

#![no_std]
#![feature(allocator_api)]

use kernel::prelude::*;
use kernel::security::{self, Hooks, FileOpenCtx, BprmCtx, SocketCreateCtx};
use kernel::task::Task;
use kernel::sync::atomic::{AtomicI64, Ordering};

module! {
    type: AuditSecModule,
    name: "auditsec_rust",
    author: "auditsec-demo",
    description: "Audit-logging LSM written in Rust",
    license: "GPL v2",
}

/// Per-module state — lives in a static (kernel modules are effectively
/// singletons).  AtomicI64 used for lock-free stat counters;
/// equivalent to C's atomic_long_t.
struct AuditSecState {
    file_opens:  AtomicI64,
    exec_checks: AtomicI64,
    sock_create: AtomicI64,
    denied:      AtomicI64,
    enabled:     AtomicI64,   // 0=off 1=log 2=enforce
    denied_uid:  AtomicI64,   // -1 = disabled
}

static STATE: AuditSecState = AuditSecState {
    file_opens:  AtomicI64::new(0),
    exec_checks: AtomicI64::new(0),
    sock_create: AtomicI64::new(0),
    denied:      AtomicI64::new(0),
    enabled:     AtomicI64::new(1),
    denied_uid:  AtomicI64::new(-1),
};

/// `AuditSecHooks` implements the `Hooks` trait from `rust/kernel/security.rs`.
/// Each method corresponds to an LSM hook; defaults (allow) are provided by
/// the trait so you only override what you need.
struct AuditSecHooks;

impl Hooks for AuditSecHooks {
    // -------------------------------------------------------------------------
    // Hook: file_open
    // C equivalent: security_file_open() → fs/open.c:do_dentry_open()
    // -------------------------------------------------------------------------
    fn file_open(ctx: &FileOpenCtx) -> Result {
        let enabled = STATE.enabled.load(Ordering::Relaxed);
        if enabled == 0 {
            return Ok(());
        }

        STATE.file_opens.fetch_add(1, Ordering::Relaxed);

        // ctx.path() returns a kernel::fs::Path — wraps struct path
        // Rust binding ensures lifetime safety; no manual NULL check needed
        // because the Rust type system guarantees the dentry is valid inside
        // FileOpenCtx.  Anonymous files (pipes/sockets) produce an empty path
        // string rather than a NULL dereference — this is the Rust advantage
        // over the C version's BUG-1.
        let path = ctx.path().to_str().unwrap_or("<anon>");

        pr_info!(
            "[file_open] uid={} pid={} comm={} :: {}\n",
            Task::current().uid(),
            Task::current().pid(),
            Task::current().comm(),
            path,
        );
        Ok(())
    }

    // -------------------------------------------------------------------------
    // Hook: bprm_check_security
    // C equivalent: security_bprm_check() → fs/exec.c:bprm_execve()
    //
    // Rust note: the type system forces you to be explicit about the
    // uid == vs uid != comparison.  The logic bug present in auditsec.c
    // (BUG-2) is harder to introduce accidentally because the policy is
    // expressed as a named predicate rather than an inline comparison.
    // -------------------------------------------------------------------------
    fn bprm_check_security(ctx: &BprmCtx) -> Result {
        let enabled = STATE.enabled.load(Ordering::Relaxed);
        STATE.exec_checks.fetch_add(1, Ordering::Relaxed);

        let uid        = Task::current().uid() as i64;
        let denied_uid = STATE.denied_uid.load(Ordering::Relaxed);
        let path       = ctx.filename().to_str().unwrap_or("<binary>");

        pr_info!(
            "[bprm_check] uid={} path={}\n",
            uid, path,
        );

        // Explicit helper makes the policy readable and testable in isolation.
        fn is_denied_uid(uid: i64, denied: i64) -> bool {
            denied >= 0 && uid == denied          // NOTE: == not !=
        }

        if enabled == 2 && is_denied_uid(uid, denied_uid) {
            STATE.denied.fetch_add(1, Ordering::Relaxed);
            pr_warn!("auditsec_rust: DENY exec uid={} path={}\n", uid, path);
            return Err(EACCES);
        }
        Ok(())
    }

    // -------------------------------------------------------------------------
    // Hook: socket_create
    // C equivalent: security_socket_create() → net/socket.c:__sys_socket()
    // -------------------------------------------------------------------------
    fn socket_create(ctx: &SocketCreateCtx) -> Result {
        if ctx.kern() {
            return Ok(());
        }
        STATE.sock_create.fetch_add(1, Ordering::Relaxed);
        pr_info!(
            "[sock_create] family={} type={} proto={}\n",
            ctx.family(), ctx.sock_type(), ctx.protocol(),
        );
        Ok(())
    }
}

// -------------------------------------------------------------------------
// Module entry/exit — mirrors C module_init / module_exit
// -------------------------------------------------------------------------
struct AuditSecModule {
    _hooks: security::Registration<AuditSecHooks>,
}

impl kernel::Module for AuditSecModule {
    fn init(_module: &'static ThisModule) -> Result<Self> {
        pr_info!("auditsec_rust: initialising\n");

        // security::Registration::new() calls security_add_hooks() internally
        // and returns a RAII guard that is drop()-safe (though removal is still
        // not supported by the kernel; drop() is a no-op today).
        let _hooks = security::Registration::new()?;

        pr_info!("auditsec_rust: hooks registered\n");
        Ok(AuditSecModule { _hooks })
    }
}

impl Drop for AuditSecModule {
    fn drop(&mut self) {
        pr_info!("auditsec_rust: unloaded\n");
    }
}

// -------------------------------------------------------------------------
// BPF LSM alternative (WORKS TODAY on v6.8+ without in-flight bindings)
// -------------------------------------------------------------------------
// If the rust/kernel/security.rs bindings are not yet merged in your kernel,
// use BPF LSM programs written in Rust via aya-rs (userspace BPF framework):
//
//   [dependencies]
//   aya-bpf = { version = "0.1", features = ["lsm"] }
//
//   #[lsm(hook = "file_open")]
//   pub fn auditsec_file_open(ctx: LsmContext) -> i32 {
//       // ctx provides bpf_get_current_uid_gid(), bpf_get_current_comm(), etc.
//       0  // allow
//   }
//
// aya-rs repo: https://github.com/aya-rs/aya
// Requires: CONFIG_BPF_LSM=y, kernel.bpf.lsm_hooks sysctl
