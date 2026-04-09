// SPDX-License-Identifier: GPL-2.0
// Copyright (C) edu authors
//
// edu_net/rust/lib.rs — Educational virtual NIC in Rust (kernel ≥ 6.6)
//
// Uses: kernel::net, kernel::prelude, kernel::sync, kernel::workqueue
//
// NOTE: The Rust net abstractions are *unstable* in-tree API.
// As of 6.8, kernel::net::dev is in active development (netdev Rust series
// by Fujita / Jianguo). This file targets the abstractions that ARE merged
// or imminently mergeable. Where an abstraction does not yet exist in the
// kernel crate, we use unsafe bindings directly via kernel::bindings — this
// mirrors how real in-tree Rust drivers work today (e.g. r8169, ax88179).
//
// Build: place under drivers/net/edu_net_rs/, add Kconfig + Makefile.
// Then: make M=drivers/net/edu_net_rs CONFIG_EDU_NET_RS=m
//
// Architecture note:
//   Rust kernel code CANNOT use std (no_std). All allocation goes through
//   kernel::alloc (GFP_KERNEL / GFP_ATOMIC wrappers). Panics = kernel BUG().

#![no_std]
// The kernel macro crate pulls in the kernel prelude.
// In-tree modules use the `kernel` crate directly.
#[macro_use]
extern crate kernel;

use kernel::prelude::*;
use kernel::sync::{Arc, SpinLock};
use kernel::net::dev::{NetDevice, NetDeviceAdapter, NetDeviceFlags, TxResult};
use kernel::net::SkBuff;
use kernel::c_str;

// ---------------------------------------------------------------------------
// Module metadata — kernel::module! macro emits the required ELF sections.
// ---------------------------------------------------------------------------
module! {
    type: EduNetRs,
    name: "edu_net_rs",
    author: "edu",
    description: "Educational virtual NIC in Rust",
    license: "GPL",
}

// ---------------------------------------------------------------------------
// Per-device statistics — wraps a SpinLock<EduStats>
// SpinLock<T> in the kernel crate is a pinned, IRQ-safe spinlock.
// ---------------------------------------------------------------------------
#[derive(Default)]
struct EduStats {
    tx_packets: u64,
    tx_bytes:   u64,
    tx_dropped: u64,
    rx_packets: u64,
    rx_bytes:   u64,
}

// ---------------------------------------------------------------------------
// The adapter struct implements NetDeviceAdapter, which the kernel crate
// maps to C net_device_ops via a generated vtable (monomorphisation).
// ---------------------------------------------------------------------------
struct EduNetAdapter {
    /// Shared mutable stats protected by spinlock.
    stats: SpinLock<EduStats>,
    /// When true, TX frames are reflected back as RX.
    loopback: bool,
}

// SAFETY: EduNetAdapter is only accessed through the kernel's serialised
// netdev callbacks + our SpinLock. No raw pointers escape to userspace.
unsafe impl Send for EduNetAdapter {}
unsafe impl Sync for EduNetAdapter {}

/// The trait that the kernel crate requires us to implement.
/// It mirrors net_device_ops but in safe Rust where possible.
impl NetDeviceAdapter for EduNetAdapter {
    // Required associated type: the netdevice private data type.
    // The kernel crate will embed this in the net_device via alloc_netdev.
    type Data = Arc<EduNetAdapter>;

    /// ndo_open equivalent
    fn open(dev: &NetDevice<Self>) -> Result {
        pr_info!("{}: opened\n", dev.name());
        dev.start_queue();
        Ok(())
    }

    /// ndo_stop equivalent
    fn stop(dev: &NetDevice<Self>) -> Result {
        dev.stop_queue();
        pr_info!("{}: stopped\n", dev.name());
        Ok(())
    }

    /// ndo_start_xmit equivalent.
    /// Returns TxResult::Ok or TxResult::Busy.
    /// The kernel crate converts this to NETDEV_TX_OK / NETDEV_TX_BUSY.
    ///
    /// CONTRACT: if TxResult::Busy, skb must NOT be freed (qdisc retries).
    ///           if TxResult::Ok,   skb must have been consumed (freed/fwd).
    fn start_xmit(skb: SkBuff, dev: &NetDevice<Self>) -> TxResult {
        let data = dev.data();
        let pkt_len = skb.len() as u64;

        if data.loopback {
            // Clone and re-inject as RX.
            // In a real driver we'd enqueue to an RX ring; here we use
            // netif_rx which is simpler but less efficient (no NAPI).
            match skb.clone_for_rx() {
                Some(rx_skb) => {
                    // SAFETY: we set all required fields before handing off.
                    unsafe {
                        rx_skb.set_protocol_from_eth_type_trans(dev);
                        rx_skb.set_ip_summed_none();
                        rx_skb.netif_rx();
                    }
                    // Record RX stats
                    {
                        let mut s = data.stats.lock();
                        s.rx_packets += 1;
                        s.rx_bytes   += pkt_len;
                    }
                }
                None => {
                    // Clone failed — OOM; drop silently
                    let mut s = data.stats.lock();
                    s.tx_dropped += 1;
                    // skb is consumed by Drop impl
                    return TxResult::Ok;
                }
            }
            // Record TX stats
            {
                let mut s = data.stats.lock();
                s.tx_packets += 1;
                s.tx_bytes   += pkt_len;
            }
            // skb Drop impl calls dev_kfree_skb_any
        } else {
            let mut s = data.stats.lock();
            s.tx_dropped += 1;
            // skb dropped here via Drop
        }

        TxResult::Ok
    }

    /// ndo_get_stats64 equivalent
    fn get_stats64(dev: &NetDevice<Self>, stats: &mut kernel::net::RtnlLinkStats64) {
        let data = dev.data();
        let s = data.stats.lock();
        stats.tx_packets = s.tx_packets;
        stats.tx_bytes   = s.tx_bytes;
        stats.tx_dropped = s.tx_dropped;
        stats.rx_packets = s.rx_packets;
        stats.rx_bytes   = s.rx_bytes;
    }
}

// ---------------------------------------------------------------------------
// Module state — holds the registered net_device handle.
// The kernel crate wraps this in a Registration<T> that calls
// unregister_netdev on Drop.
// ---------------------------------------------------------------------------
struct EduNetRs {
    /// Keeps the device alive for the module lifetime.
    _dev: kernel::net::dev::Registration<EduNetAdapter>,
}

impl kernel::Module for EduNetRs {
    fn init(_module: &'static ThisModule) -> Result<Self> {
        pr_info!("edu_net_rs: loading\n");

        // Build the private data
        let adapter = Arc::try_new(EduNetAdapter {
            // SAFETY: SpinLock::new is unsafe because the caller must
            // pin it before use; the kernel crate's Registration handles this.
            stats:    unsafe { SpinLock::new(EduStats::default()) },
            loopback: true,
        })?;

        // alloc_netdev + register_netdev in one call.
        // The kernel crate generates the net_device_ops vtable from EduNetAdapter.
        let dev = kernel::net::dev::Registration::new_ethernet(
            c_str!("edu_rs%d"),
            adapter,
            // Setup callback (mirrors edu_net_setup in C)
            |dev| {
                dev.set_flags(NetDeviceFlags::NOARP);
                dev.set_mtu(1500);
                dev.set_min_mtu(68);
                dev.set_max_mtu(9000);
                dev.set_tx_queue_len(1000);
                dev.eth_hw_addr_random();
            },
        )?;

        pr_info!("edu_net_rs: registered {}\n", dev.name());
        Ok(Self { _dev: dev })
    }
}

impl Drop for EduNetRs {
    fn drop(&mut self) {
        pr_info!("edu_net_rs: unloading\n");
        // _dev's Drop calls unregister_netdev automatically
    }
}

// ---------------------------------------------------------------------------
// Rust safety notes for kernel reviewers:
//
// 1. All allocations use kernel::alloc — no Box/Vec from std.
// 2. SpinLock<T> is kernel spinlock + IRQ-disable; not std::sync::Mutex.
// 3. SkBuff Drop calls dev_kfree_skb_any — no manual free needed.
// 4. Arc<T> is kernel::sync::Arc backed by refcount_t, not std::sync::Arc.
// 5. No global mutable state — all state is in the Registration struct.
// 6. SAFETY comments required on every `unsafe` block per kernel policy.
// ---------------------------------------------------------------------------
