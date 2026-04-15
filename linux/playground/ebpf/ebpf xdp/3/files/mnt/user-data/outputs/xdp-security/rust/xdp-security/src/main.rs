// XDP Security — Rust Userspace Loader (using Aya)
//
// This is the control plane: loads BPF, attaches to interface,
// manages maps, and polls statistics.
//
// Run with: sudo cargo run --release -- --iface eth0

use anyhow::{bail, Context, Result};
use aya::{
    include_bytes_aligned,
    maps::{HashMap, LruHashMap, PerCpuArray},
    programs::{Xdp, XdpFlags},
    Bpf,
};
use aya_log::BpfLogger;
use clap::Parser;
use log::{info, warn};
use std::{
    net::Ipv4Addr,
    str::FromStr,
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc,
    },
    thread,
    time::Duration,
};

// ─── CLI ARGUMENTS ─────────────────────────────────────────────────────────
// Key concept — "clap":
//   Rust crate for parsing command-line arguments declaratively.
#[derive(Parser, Debug)]
#[command(name = "xdp-security", about = "XDP Security Loader")]
struct Opt {
    /// Network interface to attach XDP program to
    #[arg(short, long, default_value = "eth0")]
    iface: String,

    /// Block an IP address
    #[arg(long, value_name = "IP")]
    block: Option<String>,

    /// Unblock an IP address
    #[arg(long, value_name = "IP")]
    unblock: Option<String>,

    /// Allowlist an IP address (always pass)
    #[arg(long, value_name = "IP")]
    allow: Option<String>,

    /// Use SKB (generic) mode instead of native driver mode
    #[arg(long)]
    skb_mode: bool,

    /// Statistics polling interval in seconds
    #[arg(long, default_value_t = 2)]
    interval: u64,
}

// ─── BPF STATISTICS STRUCT (mirrors kernel-side) ───────────────────────────
#[repr(C)]
#[derive(Clone, Copy, Default)]
struct Stats {
    total_pkts:         u64,
    dropped_blocklist:  u64,
    dropped_rate_limit: u64,
    dropped_syn_flood:  u64,
    passed_pkts:        u64,
    passed_allowlist:   u64,
}

// ─── MAIN ──────────────────────────────────────────────────────────────────
#[tokio::main]
async fn main() -> Result<()> {
    let opt = Opt::parse();

    // Initialize logging
    env_logger::init();

    // ── BUMP MEMLOCK ──
    // Key concept — rlimit:
    // Same as C version — allow unlimited memory locking for BPF maps.
    #[cfg(not(feature = "async"))]
    let rlim = libc::rlimit {
        rlim_cur: libc::RLIM_INFINITY,
        rlim_max: libc::RLIM_INFINITY,
    };
    #[cfg(not(feature = "async"))]
    unsafe { libc::setrlimit(libc::RLIMIT_MEMLOCK, &rlim) };

    // ── LOAD BPF PROGRAM ──
    // Key concept — include_bytes_aligned!:
    //   Embeds the compiled BPF ELF binary directly into the Rust binary.
    //   No external .o file needed at runtime!
    //   The path is relative to the workspace root.
    //   The BPF program is compiled separately and embedded at build time.
    let bpf_bytes = include_bytes_aligned!(
        "../../target/bpfel-unknown-none/release/xdp-security-ebpf"
    );

    let mut bpf = Bpf::load(bpf_bytes)
        .context("Failed to load BPF program")?;

    // ── SETUP BPF LOGGER (reads bpf_printk output) ──
    if let Err(e) = BpfLogger::init(&mut bpf) {
        warn!("Failed to init BPF logger (non-fatal): {}", e);
    }

    // ── APPLY BLOCKLIST / ALLOWLIST RULES ──
    {
        let mut blocklist: HashMap<_, u32, u8> =
            HashMap::try_from(bpf.map_mut("IP_BLOCKLIST")
                .context("Map IP_BLOCKLIST not found")?)?;

        let mut allowlist: HashMap<_, u32, u8> =
            HashMap::try_from(bpf.map_mut("IP_ALLOWLIST")
                .context("Map IP_ALLOWLIST not found")?)?;

        if let Some(ref ip_str) = opt.block {
            let ip: Ipv4Addr = Ipv4Addr::from_str(ip_str)
                .context("Invalid block IP")?;
            let key = u32::from(ip).to_be(); // network byte order
            blocklist.insert(key, 1, 0)
                .context("Failed to insert into blocklist")?;
            info!("Blocked: {}", ip_str);
        }

        if let Some(ref ip_str) = opt.unblock {
            let ip: Ipv4Addr = Ipv4Addr::from_str(ip_str)
                .context("Invalid unblock IP")?;
            let key = u32::from(ip).to_be();
            blocklist.remove(&key)
                .context("Failed to remove from blocklist")?;
            info!("Unblocked: {}", ip_str);
        }

        if let Some(ref ip_str) = opt.allow {
            let ip: Ipv4Addr = Ipv4Addr::from_str(ip_str)
                .context("Invalid allow IP")?;
            let key = u32::from(ip).to_be();
            allowlist.insert(key, 1, 0)
                .context("Failed to insert into allowlist")?;
            info!("Allowlisted: {}", ip_str);
        }
    }

    // ── ATTACH XDP PROGRAM ──
    let xdp_flags = if opt.skb_mode {
        XdpFlags::SKB_MODE   // generic, slower, all drivers
    } else {
        XdpFlags::DRV_MODE   // native, faster, requires driver support
    };

    let program: &mut Xdp = bpf
        .program_mut("xdp_security")
        .context("BPF program 'xdp_security' not found")?
        .try_into()
        .context("Not an XDP program")?;

    program.load().context("Failed to load XDP program (verifier error?)")?;
    program
        .attach(&opt.iface, xdp_flags)
        .context(format!(
            "Failed to attach XDP to {}. Try --skb-mode for generic mode.",
            opt.iface
        ))?;

    info!("XDP program attached to {} ({} mode)",
          opt.iface,
          if opt.skb_mode { "SKB/generic" } else { "native driver" });

    // ── CTRL-C HANDLER ──
    let running = Arc::new(AtomicBool::new(true));
    let r = running.clone();
    ctrlc::set_handler(move || {
        r.store(false, Ordering::SeqCst);
    })?;

    // ── STATISTICS LOOP ──
    println!("Running XDP security. Press Ctrl-C to stop.\n");

    while running.load(Ordering::SeqCst) {
        thread::sleep(Duration::from_secs(opt.interval));
        print_stats(&bpf)?;
    }

    info!("Shutting down — XDP program will be detached automatically.");
    // Aya automatically detaches when `program` is dropped.
    Ok(())
}

// ─── STATS PRINTER ─────────────────────────────────────────────────────────
fn print_stats(bpf: &Bpf) -> Result<()> {
    let stats_map: PerCpuArray<_, Stats> =
        PerCpuArray::try_from(bpf.map("XDP_STATS")
            .context("Map XDP_STATS not found")?)?;

    let per_cpu_values = stats_map.get(&0, 0)
        .context("Failed to read stats")?;

    // Sum across all CPUs
    let totals = per_cpu_values.iter().fold(Stats::default(), |mut acc, s| {
        acc.total_pkts         += s.total_pkts;
        acc.dropped_blocklist  += s.dropped_blocklist;
        acc.dropped_rate_limit += s.dropped_rate_limit;
        acc.dropped_syn_flood  += s.dropped_syn_flood;
        acc.passed_pkts        += s.passed_pkts;
        acc.passed_allowlist   += s.passed_allowlist;
        acc
    });

    // Clear terminal and print
    print!("\x1b[2J\x1b[H");
    println!("╔══════════════════════════════════════════╗");
    println!("║     XDP Security (Rust/Aya) — Stats      ║");
    println!("╠══════════════════════════════════════════╣");
    println!("║  Total Packets       : {:>16} ║", totals.total_pkts);
    println!("║  Passed              : {:>16} ║", totals.passed_pkts);
    println!("║  Passed (allowlist)  : {:>16} ║", totals.passed_allowlist);
    println!("║  Dropped (blocklist) : {:>16} ║", totals.dropped_blocklist);
    println!("║  Dropped (rate limit): {:>16} ║", totals.dropped_rate_limit);
    println!("║  Dropped (SYN flood) : {:>16} ║", totals.dropped_syn_flood);
    println!("╚══════════════════════════════════════════╝");
    println!("  [Ctrl-C to stop]");

    Ok(())
}
