// SPDX-License-Identifier: GPL-2.0
//! xdp_filter userspace — aya control-plane loader
//!
//! Loads the compiled BPF ELF (produced by xdp-filter-ebpf crate),
//! attaches it to a network interface, manages maps, and polls stats.
//!
//! Usage:
//!   sudo cargo run --release -- --iface eth0 --block 192.168.1.100 --stats
//!
//! References:
//!   https://aya-rs.dev/book/
//!   https://docs.rs/aya/latest/aya/

use anyhow::{Context, Result};
use aya::{
    include_bytes_aligned,
    maps::{HashMap, LruHashMap, PerCpuArray},
    programs::{Xdp, XdpFlags},
    Bpf,
};
use aya_log::BpfLogger;
use clap::Parser;
use std::{
    net::Ipv4Addr,
    str::FromStr,
    sync::atomic::{AtomicBool, Ordering},
    sync::Arc,
    time::Duration,
};
use tokio::signal;

// ── CLI ────────────────────────────────────────────────────────────────────
#[derive(Parser, Debug)]
#[command(
    name  = "xdp-filter",
    about = "XDP IP blocklist + rate limiter (aya/Rust)",
    long_about = None
)]
struct Opt {
    #[arg(short, long, default_value = "eth0")]
    iface: String,

    /// Block this source IP (can be repeated)
    #[arg(short, long)]
    block: Vec<String>,

    /// Unblock this source IP
    #[arg(short, long)]
    unblock: Vec<String>,

    /// Poll and display stats every second
    #[arg(short, long)]
    stats: bool,

    /// Use SKB/generic mode instead of native XDP driver mode
    #[arg(long)]
    skb_mode: bool,
}

// ── Stats array indices (must match BPF program) ───────────────────────────
const STAT_PASS:  u32 = 0;
const STAT_BLOCK: u32 = 1;
const STAT_RATE:  u32 = 2;
const STAT_PARSE: u32 = 3;

#[tokio::main]
async fn main() -> Result<()> {
    let opt = Opt::parse();

    // ── Elevate logging ──────────────────────────────────────────────────
    env_logger::init();

    // ── Load compiled BPF ELF (embedded at compile time) ────────────────
    // include_bytes_aligned! ensures 8-byte alignment required by libbpf.
    #[cfg(debug_assertions)]
    let bpf_bytes = include_bytes_aligned!(
        "../../target/bpfel-unknown-none/debug/xdp-filter-ebpf"
    );
    #[cfg(not(debug_assertions))]
    let bpf_bytes = include_bytes_aligned!(
        "../../target/bpfel-unknown-none/release/xdp-filter-ebpf"
    );

    let mut bpf = Bpf::load(bpf_bytes).context("Failed to load BPF object")?;

    // ── Hook up aya's BPF log relay (routes bpf_printk → env_logger) ────
    if let Err(e) = BpfLogger::init(&mut bpf) {
        eprintln!("Warning: BPF logger init failed (kernel may lack ring buffer): {e}");
    }

    // ── Attach XDP program ───────────────────────────────────────────────
    let program: &mut Xdp = bpf
        .program_mut("xdp_filter_prog")
        .context("Program 'xdp_filter_prog' not found in ELF")?
        .try_into()?;

    program.load().context("BPF verifier rejected program")?;

    let flags = if opt.skb_mode {
        XdpFlags::SKB_MODE
    } else {
        XdpFlags::DRV_MODE
    };

    program
        .attach(&opt.iface, flags)
        .with_context(|| format!("Failed to attach XDP to {}", opt.iface))?;

    println!(
        "[xdp-filter] Attached to {} ({} mode)",
        opt.iface,
        if opt.skb_mode { "skb/generic" } else { "native/driver" }
    );

    // ── Manage blocklist map ─────────────────────────────────────────────
    let mut blocklist: HashMap<_, u32, u8> = HashMap::try_from(
        bpf.map_mut("blocklist").context("Map 'blocklist' not found")?,
    )?;

    for ip_str in &opt.block {
        let ip = Ipv4Addr::from_str(ip_str)
            .with_context(|| format!("Invalid IP: {ip_str}"))?;
        // Store in NETWORK byte-order (to_bits() gives host-order on all platforms;
        // u32::to_be() converts to network/big-endian byte-order)
        let key: u32 = u32::from(ip).to_be();
        blocklist
            .insert(key, 1u8, 0)
            .with_context(|| format!("Failed to block {ip_str}"))?;
        println!("[blocklist] BLOCKED {ip_str}");
    }

    for ip_str in &opt.unblock {
        let ip = Ipv4Addr::from_str(ip_str)
            .with_context(|| format!("Invalid IP: {ip_str}"))?;
        let key: u32 = u32::from(ip).to_be();
        blocklist
            .remove(&key)
            .with_context(|| format!("Failed to unblock {ip_str}"))?;
        println!("[blocklist] UNBLOCKED {ip_str}");
    }

    // ── Stats polling loop ───────────────────────────────────────────────
    let running = Arc::new(AtomicBool::new(true));
    let r       = running.clone();

    if opt.stats {
        let stats_map = bpf
            .map("stats")
            .context("Map 'stats' not found")?;

        tokio::spawn(async move {
            let mut interval = tokio::time::interval(Duration::from_secs(1));
            loop {
                interval.tick().await;
                if !r.load(Ordering::Relaxed) {
                    break;
                }
                // Read per-CPU counters and sum them
                if let Ok(stats) = PerCpuArray::<_, u64>::try_from(stats_map) {
                    let sum = |idx: u32| -> u64 {
                        stats.get(idx, 0)
                            .map(|v| v.iter().sum())
                            .unwrap_or(0)
                    };
                    print!(
                        "\r[stats] PASS={:<10} BLOCK={:<10} RATE_DROP={:<10} PARSE_ERR={:<6}",
                        sum(STAT_PASS), sum(STAT_BLOCK), sum(STAT_RATE), sum(STAT_PARSE)
                    );
                    let _ = std::io::Write::flush(&mut std::io::stdout());
                }
            }
        });
    }

    // ── Wait for Ctrl-C ──────────────────────────────────────────────────
    signal::ctrl_c().await.context("Failed to listen for Ctrl-C")?;
    running.store(false, Ordering::Relaxed);
    println!("\n[xdp-filter] Shutting down, XDP detached.");

    Ok(())
    // XDP is automatically detached when `program` drops (aya RAII)
}
