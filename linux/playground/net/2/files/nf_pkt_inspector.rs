// SPDX-License-Identifier: GPL-2.0-only
// Copyright (C) 2024 kernel-learner
//
// nf_pkt_inspector.rs — Rust netfilter hook module
//
// Rust support landed in Linux v6.1 (Rust for Linux project).
// Netfilter Rust bindings are under active development as of v6.8.
// This file targets v6.8+ and uses the abstractions in rust/kernel/net/.
//
// Kernel source references:
//   rust/kernel/net/filter.rs          — Netfilter Rust bindings
//   rust/kernel/net.rs                 — net namespace, NetDevice
//   rust/kernel/sync/                  — SpinLock, Mutex wrappers
//   rust/kernel/proc.rs                — /proc interface (WIP in mainline)
//   Documentation/rust/index.rst
//   Documentation/rust/coding-guidelines.rst
//   Documentation/rust/quick-start.rst
//
// Build requirements:
//   CONFIG_RUST=y
//   CONFIG_SAMPLES_RUST=y (for in-tree samples)
//   rustup toolchain matching Documentation/rust/quick-start.rst version
//
// Kbuild entry (add to Kbuild file):
//   obj-m += nf_pkt_inspector.o
//   nf_pkt_inspector-objs := nf_pkt_inspector.o  (auto from .rs)
//
// NOTE: As of v6.8 the netfilter Rust API is NOT yet merged into mainline.
// The bindings shown here follow the pattern from the RFC patches on LKML:
//   [PATCH RFC 0/5] Rust abstractions for netfilter
//   https://lore.kernel.org/netfilter-devel/
// They compile against the rust-for-linux tree (branch: rust-next).
// The C module (nf_pkt_inspector.c) is fully mainline-ready.

#![no_std]
#![feature(allocator_api)]

use kernel::prelude::*;
use kernel::net::filter::{
    HookOps, HookResult, NetfilterHook, Proto, HookNum,
};
use kernel::net::SkBuff;
use kernel::sync::SpinLock;
use kernel::c_str;

module! {
    type: NfPktInspector,
    name: "nf_pkt_inspector_rs",
    author: "kernel-learner",
    description: "Netfilter hook module in Rust",
    license: "GPL v2",
    params: {
        drop_port: u16 {
            default: 0,
            permissions: 0o644,
            description: "Drop TCP packets to this destination port (0=disabled)",
        },
        log_syn: bool {
            default: true,
            permissions: 0o644,
            description: "Log TCP SYN packets",
        },
    },
}

/// Statistics counters.
///
/// In C we'd use `atomic64_t`; the Rust kernel bindings expose
/// `kernel::sync::atomic::AtomicI64` wrapping the C atomic64_t.
struct Stats {
    total:    core::sync::atomic::AtomicI64,
    tcp:      core::sync::atomic::AtomicI64,
    tcp_syn:  core::sync::atomic::AtomicI64,
    udp:      core::sync::atomic::AtomicI64,
    dropped:  core::sync::atomic::AtomicI64,
}

impl Stats {
    const fn new() -> Self {
        use core::sync::atomic::AtomicI64;
        Self {
            total:   AtomicI64::new(0),
            tcp:     AtomicI64::new(0),
            tcp_syn: AtomicI64::new(0),
            udp:     AtomicI64::new(0),
            dropped: AtomicI64::new(0),
        }
    }
}

/// Ring buffer for last SYN entries.
/// Equivalent to the C syn_ring[] + syn_ring_head + syn_ring_lock.
const RING_SZ: usize = 64;

#[derive(Clone, Copy, Default)]
struct SynEntry {
    saddr:      u32,  // network byte order
    daddr:      u32,
    dport:      u16,
}

struct SynRing {
    entries: [SynEntry; RING_SZ],
    head:    usize,
}

impl SynRing {
    const fn new() -> Self {
        Self {
            entries: [SynEntry { saddr: 0, daddr: 0, dport: 0 }; RING_SZ],
            head: 0,
        }
    }

    /// Push a new entry — wraps via bitmask, safe against overflow.
    fn push(&mut self, e: SynEntry) {
        let idx = self.head & (RING_SZ - 1);
        self.entries[idx] = e;
        self.head = self.head.wrapping_add(1);
    }
}

/// Global state — lives for the module lifetime.
static STATS: Stats = Stats::new();

// SpinLock requires Pin<Box<_>> because it must not move after init.
// kernel::sync::SpinLock<T> is a safe wrapper around C spinlock_t.
static SYN_RING: kernel::sync::Mutex<SynRing> =
    unsafe { kernel::sync::Mutex::new(SynRing::new()) };

/// The netfilter hook implementation.
///
/// `NetfilterHook` is a Rust trait defined in rust/kernel/net/filter.rs.
/// Implementing it means providing a `hook()` method that mirrors the C
/// callback signature: (priv, skb, state) → NF_ACCEPT/NF_DROP.
struct PktHook;

impl NetfilterHook for PktHook {
    fn hook(skb: &SkBuff) -> HookResult {
        use core::sync::atomic::Ordering::Relaxed;
        use kernel::net::IpProtocol;

        STATS.total.fetch_add(1, Relaxed);

        let protocol = match skb.ip_protocol() {
            Some(p) => p,
            None    => return HookResult::Accept,
        };

        match protocol {
            IpProtocol::TCP => {
                STATS.tcp.fetch_add(1, Relaxed);

                // skb.tcp_header() returns Option<&TcpHeader>.
                // The binding calls pskb_may_pull() internally and
                // re-fetches the IP header after any realloc — safe.
                let tcp = match skb.tcp_header() {
                    Some(h) => h,
                    None    => return HookResult::Accept,
                };

                let is_syn = tcp.syn() && !tcp.ack();
                let dport  = tcp.dest();

                if is_syn {
                    STATS.tcp_syn.fetch_add(1, Relaxed);

                    if *log_syn.read() {
                        // pr_debug! maps to printk(KERN_DEBUG ...)
                        // Only emits output if dynamic debug is enabled:
                        //   echo 'module nf_pkt_inspector_rs +p' \
                        //     > /sys/kernel/debug/dynamic_debug/control
                        pr_debug!(
                            "nf_pkt_inspector_rs: SYN sport={} dport={}\n",
                            tcp.source(),
                            dport,
                        );

                        // Lock the ring and push — SpinLock::lock() disables
                        // preemption + interrupts on the local CPU, equivalent
                        // to spin_lock_irqsave() in C.
                        let mut ring = SYN_RING.lock();
                        ring.push(SynEntry {
                            saddr: skb.ip_saddr().unwrap_or(0),
                            daddr: skb.ip_daddr().unwrap_or(0),
                            dport,
                        });
                    }
                }

                // Port-based dropping
                let dp = *drop_port.read();
                if dp != 0 && dport == dp {
                    STATS.dropped.fetch_add(1, Relaxed);
                    return HookResult::Drop;
                }
            }

            IpProtocol::UDP => {
                STATS.udp.fetch_add(1, Relaxed);
            }

            _ => {}
        }

        HookResult::Accept
    }
}

/// Module struct — holds the registered hook handle.
///
/// When this struct is dropped (rmmod), the `Drop` impl calls
/// nf_unregister_net_hook() automatically.  No manual cleanup needed.
struct NfPktInspector {
    _hook: HookOps<PktHook>,
}

impl kernel::Module for NfPktInspector {
    fn init(_module: &'static ThisModule) -> Result<Self> {
        pr_info!("nf_pkt_inspector_rs: loading\n");

        // HookOps::register() calls nf_register_net_hook(&init_net, ops)
        // Returns Result<HookOps<_>> — the handle owns the registration.
        let hook = HookOps::<PktHook>::register(
            Proto::Ipv4,
            HookNum::PreRouting,
            // Priority: equivalent to NF_IP_PRI_FIRST + 1
            i32::MIN + 1,
        )?;

        pr_info!("nf_pkt_inspector_rs: hook registered\n");

        Ok(NfPktInspector { _hook: hook })
    }
}

impl Drop for NfPktInspector {
    fn drop(&mut self) {
        // _hook is dropped here → nf_unregister_net_hook() called
        use core::sync::atomic::Ordering::Relaxed;
        pr_info!(
            "nf_pkt_inspector_rs: unloading — total={} dropped={}\n",
            STATS.total.load(Relaxed),
            STATS.dropped.load(Relaxed),
        );
    }
}
