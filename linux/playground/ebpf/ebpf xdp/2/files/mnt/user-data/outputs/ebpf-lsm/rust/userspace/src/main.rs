// userspace/src/main.rs — Aya-based userspace loader and event consumer
//
// Responsibilities:
//   1. Load compiled BPF ELF object (from ebpf-prog build output)
//   2. Attach LSM hooks
//   3. Populate policy maps
//   4. Poll ringbuf and dispatch events
//   5. Graceful SIGINT/SIGTERM shutdown
//
// Cargo.toml dependencies:
//   aya = { version = "0.12", features = ["async_tokio"] }
//   aya-log = "0.2"
//   tokio = { version = "1", features = ["full"] }
//   anyhow = "1"
//   clap = { version = "4", features = ["derive"] }
//   log = "0.4"
//   env_logger = "0.10"
//
// Build:
//   cargo build --package userspace --release
//
// Run (root required for BPF LSM):
//   sudo ./target/release/userspace

use anyhow::{Context, Result};
use aya::{
    include_bytes_aligned,
    maps::{HashMap, PerCpuArray, RingBuf},
    programs::{Lsm, ProgramError},
    Bpf, BpfLoader, BtfError,
};
use aya_log::BpfLogger;
use clap::Parser;
use log::{error, info, warn};
use std::{
    mem,
    net::Ipv4Addr,
    os::unix::fs::MetadataExt,
    path::PathBuf,
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc,
    },
    thread,
    time::Duration,
};
use tokio::signal;

// ─── Shared types (mirror BPF-side) ──────────────────────────────────────────
// In a workspace, this would be in a `common` crate.

const EVENT_EXEC_BLOCKED: u32     = 1;
const EVENT_FILE_OPEN_DENIED: u32 = 2;
const EVENT_PTRACE_BLOCKED: u32   = 3;

const POLICY_DENY: u8  = 1;
const POLICY_AUDIT: u8 = 2;

#[repr(C)]
#[derive(Clone, Copy)]
struct LsmEvent {
    timestamp_ns: u64,
    event_type:   u32,
    pid:          u32,
    tid:          u32,
    uid:          u32,
    gid:          u32,
    inode:        u32,
    dev:          u32,
    padding:      u32,
    comm:         [u8; 16],
    path:         [u8; 128],
}

#[repr(C)]
#[derive(Clone, Copy, Hash, Eq, PartialEq)]
struct PolicyKey {
    inode: u32,
    dev:   u32,
}

#[repr(C)]
#[derive(Clone, Copy, Default)]
struct HookStats {
    total:  u64,
    denied: u64,
}

// ─── CLI ──────────────────────────────────────────────────────────────────────
#[derive(Parser, Debug)]
#[command(name = "security-monitor", about = "BPF LSM security monitor")]
struct Opts {
    /// Path to compiled BPF ELF object
    #[arg(short, long, default_value = "target/bpfel-unknown-none/debug/ebpf-prog")]
    bpf_path: PathBuf,

    /// Additional files to block (comma-separated paths)
    #[arg(short, long, value_delimiter = ',')]
    block_files: Vec<PathBuf>,

    /// UIDs to block exec for
    #[arg(short = 'u', long, value_delimiter = ',')]
    block_uids: Vec<u32>,

    /// Verbose BPF log output
    #[arg(short, long)]
    verbose: bool,
}

// ─── Event handling ───────────────────────────────────────────────────────────
fn event_type_str(t: u32) -> &'static str {
    match t {
        EVENT_EXEC_BLOCKED     => "EXEC_BLOCKED",
        EVENT_FILE_OPEN_DENIED => "FILE_OPEN_DENIED",
        EVENT_PTRACE_BLOCKED   => "PTRACE_BLOCKED",
        _                      => "UNKNOWN",
    }
}

fn handle_event(data: &[u8]) {
    if data.len() < mem::size_of::<LsmEvent>() {
        warn!("Short event payload: {} bytes", data.len());
        return;
    }

    // SAFETY: We verified size above and LsmEvent is #[repr(C)] with no padding
    // issues for the fixed-width fields. The [u8] arrays are always valid.
    let e: &LsmEvent = unsafe { &*(data.as_ptr() as *const LsmEvent) };

    let comm = std::str::from_utf8(&e.comm)
        .unwrap_or("?")
        .trim_end_matches('\0');

    info!(
        "{:>20} pid={:<7} uid={:<6} gid={:<6} comm={:<16} inode={} dev={}",
        event_type_str(e.event_type),
        e.pid, e.uid, e.gid,
        comm,
        e.inode, e.dev,
    );
}

// ─── Policy population ────────────────────────────────────────────────────────
fn add_file_policy(
    map: &mut HashMap<aya::maps::MapData, PolicyKey, u8>,
    path: &PathBuf,
    action: u8,
) -> Result<()> {
    let meta = std::fs::metadata(path)
        .with_context(|| format!("stat({:?})", path))?;

    let key = PolicyKey {
        inode: meta.ino() as u32,
        dev:   meta.dev() as u32,
    };

    map.insert(key, action, 0)
        .with_context(|| format!("insert policy for {:?}", path))?;

    info!("Policy: {} {:?} (inode={} dev={})",
          if action == POLICY_DENY { "DENY" } else { "AUDIT" },
          path, key.inode, key.dev);
    Ok(())
}

// ─── Main ─────────────────────────────────────────────────────────────────────
#[tokio::main]
async fn main() -> Result<()> {
    let opts = Opts::parse();

    env_logger::Builder::from_env(
        env_logger::Env::default().default_filter_or(
            if opts.verbose { "debug" } else { "info" }
        )
    ).init();

    // ── 1. Load BPF ELF ──────────────────────────────────────────────────────
    //
    // BpfLoader::new() gives fine control over loading:
    //   - set_global() injects constants into .rodata (replaces compile-time consts)
    //   - btf() sets the BTF blob for CO-RE (defaults to /sys/kernel/btf/vmlinux)
    //   - load_file() reads and validates the ELF, runs verifier on load()
    //
    let bpf_bytes = std::fs::read(&opts.bpf_path)
        .with_context(|| format!("Reading BPF object: {:?}", opts.bpf_path))?;

    let mut bpf = BpfLoader::new()
        // Override a map max_entries if needed:
        // .map_pin_path("/sys/fs/bpf")   // pin maps for persistence across restarts
        .load(&bpf_bytes)
        .context("Loading BPF ELF")?;

    // ── 2. BPF logger (aya_log bridge → env_logger) ──────────────────────────
    if let Err(e) = BpfLogger::init(&mut bpf) {
        warn!("BPF logger init failed (non-fatal): {}", e);
    }

    // ── 3. Attach LSM hooks ───────────────────────────────────────────────────
    //
    // LSM programs require BTF at attach time (not just load time).
    // aya handles this transparently for CONFIG_DEBUG_INFO_BTF=y kernels.
    //
    // Note: hook names must match SEC("lsm/<name>") in the BPF program exactly.
    let hooks = ["bprm_check_security", "file_open", "ptrace_access_check"];
    let mut links = Vec::new();

    for hook in &hooks {
        let prog: &mut Lsm = bpf
            .program_mut(hook)
            .with_context(|| format!("Finding program '{}'", hook))?
            .try_into()
            .with_context(|| format!("Casting program '{}'", hook))?;

        prog.load(hook, &aya::Btf::from_sys_fs()?)
            .with_context(|| format!("Loading LSM program '{}'", hook))?;

        let link = prog.attach()
            .with_context(|| format!("Attaching LSM hook '{}'", hook))?;

        info!("Attached LSM hook: {}", hook);
        links.push(link);
    }

    // ── 4. Populate policy maps ───────────────────────────────────────────────
    {
        let mut blocked_files: HashMap<_, PolicyKey, u8> = HashMap::try_from(
            bpf.map_mut("BLOCKED_FILES").context("blocked_files map")?
        )?;

        // Default demo policy
        add_file_policy(&mut blocked_files, &PathBuf::from("/etc/shadow"),  POLICY_AUDIT).ok();
        add_file_policy(&mut blocked_files, &PathBuf::from("/usr/bin/id"),  POLICY_DENY).ok();

        // CLI-specified files
        for path in &opts.block_files {
            add_file_policy(&mut blocked_files, path, POLICY_DENY).ok();
        }
    }

    {
        let mut blocked_uids: HashMap<_, u32, u8> = HashMap::try_from(
            bpf.map_mut("BLOCKED_UIDS").context("blocked_uids map")?
        )?;

        blocked_uids.insert(65534u32, POLICY_DENY, 0).ok(); // nobody
        for uid in &opts.block_uids {
            blocked_uids.insert(*uid, POLICY_DENY, 0).ok();
            info!("Policy: UID {} → DENY", uid);
        }
    }

    // ── 5. Ringbuf consumer ───────────────────────────────────────────────────
    let mut ring_buf = RingBuf::try_from(
        bpf.map_mut("EVENTS").context("events ringbuf")?
    )?;

    info!("Monitoring. Press Ctrl+C to stop.");

    // ── 6. Event loop ─────────────────────────────────────────────────────────
    loop {
        tokio::select! {
            _ = signal::ctrl_c() => {
                info!("Shutting down...");
                break;
            }
            _ = tokio::time::sleep(Duration::from_millis(10)) => {
                // Drain all available events
                while let Some(item) = ring_buf.next() {
                    handle_event(&item);
                }
            }
        }
    }

    // ── 7. Print final stats ──────────────────────────────────────────────────
    print_stats(&bpf);

    // links dropped here → hooks detached automatically
    drop(links);
    info!("Detached. Exiting.");
    Ok(())
}

fn print_stats(bpf: &Bpf) {
    let stats_map: PerCpuArray<_, HookStats> = match bpf.map("STATS") {
        Some(m) => match PerCpuArray::try_from(m) {
            Ok(v) => v,
            Err(_) => return,
        },
        None => return,
    };

    let names = ["", "exec_blocked", "file_open", "ptrace_blocked"];
    println!("\n--- BPF LSM Stats ---");
    for i in 1u32..=3 {
        if let Ok(vals) = stats_map.get(&i, 0) {
            let (total, denied) = vals.iter().fold((0u64, 0u64), |acc, s| {
                (acc.0 + s.total, acc.1 + s.denied)
            });
            println!("  {:<20} total={:<8} denied={}", names[i as usize], total, denied);
        }
    }
    println!("---------------------");
}
