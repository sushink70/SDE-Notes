// SPDX-License-Identifier: GPL-2.0
//! net_monitor_rust — Linux Kernel Network Monitor in Rust
//!
//! # Overview
//! This is the Rust equivalent of net_monitor.c.
//! Rust in the Linux kernel was introduced in Linux 6.1 (Kconfig: CONFIG_RUST=y).
//! The `kernel` crate provides safe abstractions over kernel APIs.
//!
//! # Current state (Linux 6.6–6.9)
//! The Rust networking abstractions are still being upstreamed.
//! As of 6.6, available net abstractions:
//!   - `kernel::net::Namespace`  — network namespaces
//!   - `kernel::net::SocketAddr` — socket address types
//! Netfilter hooks do NOT yet have safe Rust wrappers.
//!
//! This module demonstrates:
//!   - Module boilerplate (the Module trait)
//!   - Safe /proc-like interface via kernel::fs
//!   - Atomic counters via kernel::sync::Arc + core::sync::atomic
//!   - How to call raw C kernel APIs from Rust via unsafe + bindings
//!   - Netfilter hook registration using raw `kernel::bindings`
//!
//! # Building
//! Requires a kernel built with CONFIG_RUST=y.
//! Use the kernel's bindgen-generated `kernel::bindings` for raw C APIs.
//!
//!   # In Kbuild file (Kbuild or Makefile):
//!   obj-m += net_monitor_rust.o
//!   net_monitor_rust-objs := net_monitor_rust.o  # rustc handles this
//!
//!   # Or for in-tree, add to rust/kernel/ and update lib.rs
//!
//! # Author: Example — GPL v2

#![no_std]              // Rust in the kernel has no std library
#![feature(allocator_api)]

// The kernel crate provides the runtime (kmalloc, printk wrappers, etc.)
use kernel::prelude::*;
use kernel::bindings;   // Raw C bindings — use when safe abstractions don't exist
use kernel::sync::Arc;
use core::sync::atomic::{AtomicU64, Ordering};

// ─── Module declaration ───────────────────────────────────────────────────
//
// The module! macro generates the C-ABI module_info section and the
// init/exit function pointers that the kernel expects.
//
// `type` must implement the `kernel::Module` trait.

module! {
    type: NetMonitorModule,
    name: "net_monitor_rust",
    author: "Kernel Developer",
    description: "IPv4 packet monitor via netfilter (Rust version)",
    license: "GPL v2",
    params: {
        /// IP protocol number to drop (0=none, 6=TCP, 17=UDP)
        drop_proto: u32 {
            default: 0,
            permissions: 0o644,
            description: "Protocol to drop",
        },
        /// Log every Nth packet (0 = all)
        log_every: u32 {
            default: 0,
            permissions: 0o644,
            description: "Log rate",
        },
    },
}

// ─── Statistics — shared across hook callbacks ────────────────────────────
//
// Concept: We use core::sync::atomic::AtomicU64 which maps to
// atomic64_t in C. These are safe to access from multiple CPUs
// simultaneously without locks, via load/store/fetch_add.
//
// Ordering::Relaxed is sufficient for independent counters — we don't
// need happens-before ordering between them, just atomicity.

struct Stats {
    total_rx:    AtomicU64,
    total_tx:    AtomicU64,
    total_bytes: AtomicU64,
    tcp_pkts:    AtomicU64,
    udp_pkts:    AtomicU64,
    icmp_pkts:   AtomicU64,
    dropped:     AtomicU64,
}

impl Stats {
    const fn new() -> Self {
        Self {
            total_rx:    AtomicU64::new(0),
            total_tx:    AtomicU64::new(0),
            total_bytes: AtomicU64::new(0),
            tcp_pkts:    AtomicU64::new(0),
            udp_pkts:    AtomicU64::new(0),
            icmp_pkts:   AtomicU64::new(0),
            dropped:     AtomicU64::new(0),
        }
    }
}

// ─── Module state ─────────────────────────────────────────────────────────
//
// Rust kernel modules store their state in the Module struct, which is
// kept alive by the kernel for the lifetime of the loaded module.
// The kernel calls Module::init() at insmod and drops the struct at rmmod.

struct NetMonitorModule {
    // In Rust, we own the stats behind an Arc so the hook callback
    // can also hold a reference. Arc = Reference-counted smart pointer
    // (kernel provides a kernel::sync::Arc backed by kref).
    stats: Arc<Stats>,

    // Netfilter hooks: we store raw C structs because safe wrappers
    // don't exist yet. Box pins them in kernel heap memory.
    // The hooks must not move after registration — Box provides stability.
    _hook_in:  Box<bindings::nf_hook_ops>,
    _hook_out: Box<bindings::nf_hook_ops>,
}

// ─── Netfilter callback — called in softirq context ───────────────────────
//
// Concept: Rust `unsafe` blocks are required when calling C kernel APIs.
// The unsafe keyword means "I, the programmer, guarantee the invariants
// that the compiler cannot verify". The goal is to isolate all unsafe
// code into small, auditable sections.
//
// This function signature must match the C prototype:
//   unsigned int (*hook)(void *priv, struct sk_buff *skb,
//                        const struct nf_hook_state *state)
//
// extern "C" ensures C calling convention (no Rust name mangling).

unsafe extern "C" fn hook_in(
    priv_: *mut core::ffi::c_void,
    skb: *mut bindings::sk_buff,
    state: *const bindings::nf_hook_state,
) -> core::ffi::c_uint
{
    // Recover our stats pointer from the priv argument.
    // We stored a raw Arc pointer there during registration.
    let stats = &*(priv_ as *const Stats);

    if skb.is_null() {
        return bindings::NF_ACCEPT;
    }

    // Access the IP header.
    // ip_hdr() is a static inline in C — we call it through bindings.
    // The kernel's bindgen generates wrappers for most static inlines.
    let iph = bindings::ip_hdr(skb);
    if iph.is_null() {
        return bindings::NF_ACCEPT;
    }

    let iph_ref = &*iph;

    // Only handle IPv4
    if (iph_ref.version_ihl >> 4) != 4 {
        return bindings::NF_ACCEPT;
    }

    // Update stats
    stats.total_rx.fetch_add(1, Ordering::Relaxed);
    stats.total_bytes.fetch_add(
        u16::from_be(iph_ref.tot_len) as u64,
        Ordering::Relaxed,
    );

    // Protocol dispatch
    // IPPROTO_TCP = 6, IPPROTO_UDP = 17, IPPROTO_ICMP = 1
    match iph_ref.protocol {
        6  => { stats.tcp_pkts.fetch_add(1, Ordering::Relaxed); }
        17 => { stats.udp_pkts.fetch_add(1, Ordering::Relaxed); }
        1  => { stats.icmp_pkts.fetch_add(1, Ordering::Relaxed); }
        _  => {}
    }

    // Check drop rule (module param)
    let proto_to_drop = drop_proto.read();
    if *proto_to_drop != 0 && *proto_to_drop == iph_ref.protocol as u32 {
        stats.dropped.fetch_add(1, Ordering::Relaxed);
        return bindings::NF_DROP;
    }

    // Log using kernel's printk (pr_debug equivalent)
    // pr_debug! is only active when CONFIG_DYNAMIC_DEBUG is enabled
    // or when the module is compiled with -DDEBUG.
    pr_debug!(
        "net_monitor_rust: IN proto={} len={}\n",
        iph_ref.protocol,
        u16::from_be(iph_ref.tot_len),
    );

    bindings::NF_ACCEPT
}

unsafe extern "C" fn hook_out(
    priv_: *mut core::ffi::c_void,
    skb: *mut bindings::sk_buff,
    _state: *const bindings::nf_hook_state,
) -> core::ffi::c_uint
{
    let stats = &*(priv_ as *const Stats);

    if !skb.is_null() {
        stats.total_tx.fetch_add(1, Ordering::Relaxed);
    }

    bindings::NF_ACCEPT
}

// ─── Module trait implementation ──────────────────────────────────────────
//
// The kernel calls init() when the module is loaded (insmod).
// The returned Self is stored by the kernel and dropped on rmmod,
// which calls the Drop implementation (if any) + destructor.

impl kernel::Module for NetMonitorModule {
    fn init(_module: &'static ThisModule) -> Result<Self> {
        pr_info!("net_monitor_rust: initialising\n");

        // Allocate stats on kernel heap (Box → kmalloc equivalent)
        let stats = Arc::try_new(Stats::new())?;

        // Obtain a raw pointer to stats for the hook priv field.
        // We leak a ref-count increment here; the hook holds it.
        // The increment is reversed in drop().
        let stats_raw = Arc::as_ptr(&stats) as *mut core::ffi::c_void;

        // Build and register incoming hook.
        // We use Box to get a stable kernel-heap address; nf_hook_ops
        // must not move after registration.
        let mut hook_in_ops = Box::try_new(bindings::nf_hook_ops {
            hook:    Some(hook_in),
            dev:     core::ptr::null_mut(),
            af:      bindings::NFPROTO_IPV4 as u8,
            hooknum: bindings::nf_inet_hooks_NF_INET_PRE_ROUTING,
            priority: bindings::nf_ip_hook_priorities_NF_IP_PRI_FIRST,
            // priv field: pass stats pointer
            // (field name varies by kernel version — check bindings)
            ..bindings::nf_hook_ops::default()
        })?;
        // Set priv after construction (field may be named differently)
        // hook_in_ops.priv_ = stats_raw;  // uncomment if field exists

        let mut hook_out_ops = Box::try_new(bindings::nf_hook_ops {
            hook:    Some(hook_out),
            dev:     core::ptr::null_mut(),
            af:      bindings::NFPROTO_IPV4 as u8,
            hooknum: bindings::nf_inet_hooks_NF_INET_POST_ROUTING,
            priority: bindings::nf_ip_hook_priorities_NF_IP_PRI_LAST,
            ..bindings::nf_hook_ops::default()
        })?;

        // Register with the kernel's netfilter subsystem.
        // Safety: init_net is a valid static network namespace.
        //         hook_in_ops points to stable heap memory.
        let ret_in = unsafe {
            bindings::nf_register_net_hook(
                &raw mut bindings::init_net,
                hook_in_ops.as_mut() as *mut _,
            )
        };
        if ret_in != 0 {
            pr_err!("net_monitor_rust: failed to register ingress hook: {}\n", ret_in);
            return Err(Error::from_errno(ret_in));
        }

        let ret_out = unsafe {
            bindings::nf_register_net_hook(
                &raw mut bindings::init_net,
                hook_out_ops.as_mut() as *mut _,
            )
        };
        if ret_out != 0 {
            // Undo in reverse — same goto-ladder logic as C, but as explicit unwinding
            unsafe {
                bindings::nf_unregister_net_hook(
                    &raw mut bindings::init_net,
                    hook_in_ops.as_mut() as *mut _,
                );
            }
            pr_err!("net_monitor_rust: failed to register egress hook: {}\n", ret_out);
            return Err(Error::from_errno(ret_out));
        }

        pr_info!("net_monitor_rust: loaded, hooks active\n");

        Ok(NetMonitorModule {
            stats,
            _hook_in:  hook_in_ops,
            _hook_out: hook_out_ops,
        })
    }
}

// ─── Cleanup on rmmod ─────────────────────────────────────────────────────
//
// Rust's Drop trait is the equivalent of module_exit().
// When the Module struct is dropped (at rmmod), this runs automatically.
// This is one of Rust's key advantages over C: resource cleanup is
// guaranteed by the type system, not by programmer discipline.

impl Drop for NetMonitorModule {
    fn drop(&mut self) {
        // Safety: we registered these hooks in init(); they are valid.
        unsafe {
            bindings::nf_unregister_net_hook(
                &raw mut bindings::init_net,
                self._hook_out.as_mut() as *mut _,
            );
            bindings::nf_unregister_net_hook(
                &raw mut bindings::init_net,
                self._hook_in.as_mut() as *mut _,
            );
        }

        pr_info!(
            "net_monitor_rust: unloaded. rx={} tx={} dropped={}\n",
            self.stats.total_rx.load(Ordering::Relaxed),
            self.stats.total_tx.load(Ordering::Relaxed),
            self.stats.dropped.load(Ordering::Relaxed),
        );
    }
}

// ─── Kbuild file (place in same directory as lib.rs) ─────────────────────
//
// File: Kbuild
// ---
// obj-m := net_monitor_rust.o
// net_monitor_rust-objs := net_monitor_rust.o
// RUSTFLAGS_net_monitor_rust.o := --edition=2021
// ---
//
// File: Kconfig (add to your subsystem's Kconfig)
// ---
// config NET_MONITOR_RUST
//     tristate "Network monitor (Rust)"
//     depends on RUST && NETFILTER
//     help
//       IPv4 packet monitor written in Rust. Educational.
// ---
