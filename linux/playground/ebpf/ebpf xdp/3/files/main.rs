// XDP Security — Rust Kernel-Space Program (using Aya framework)
//
// Key concept — "Aya":
//   Aya is a Rust library for writing and loading eBPF programs.
//   It does NOT require libbpf (pure Rust BPF loader).
//   Two crates:
//     aya-ebpf  : kernel-side helpers (maps, helpers, SEC annotations)
//     aya       : userspace loader (equivalent to libbpf in Rust)
//
// This file is compiled with:
//   cargo build --release --target bpfel-unknown-none -Z build-std=core
//   (bpfel = BPF little-endian, unknown = no OS, none = no std)
//
// References:
//   https://aya-rs.dev/book/
//   https://github.com/aya-rs/aya
//   https://docs.rs/aya-ebpf/

#![no_std]       // no Rust standard library — we're in kernel space!
#![no_main]      // no main() — the BPF verifier is the entry point manager

// Key concept — "no_std":
//   In BPF kernel programs we cannot use the Rust std library.
//   No heap allocation (no Vec, Box, String), no OS calls.
//   We use aya_ebpf which provides BPF-safe abstractions.

use aya_ebpf::{
    bindings::xdp_action,
    macros::{map, xdp},
    maps::{HashMap, LruHashMap, PerCpuArray},
    programs::XdpContext,
};
use aya_log_ebpf::info;

// ─── CONSTANTS ────────────────────────────────────────────────────────────
const RATE_LIMIT_PKTS: u64     = 500;
const SYN_FLOOD_THRESHOLD: u64 = 200;
const NANOSEC_PER_SEC: u64     = 1_000_000_000;

// ─── DATA STRUCTURES ──────────────────────────────────────────────────────
#[repr(C)]
pub struct RateEntry {
    pub count: u64,
    pub window_start: u64,
}

#[repr(C)]
pub struct SynEntry {
    pub syn_count: u64,
    pub window_start: u64,
}

#[repr(C)]
pub struct Stats {
    pub total_pkts: u64,
    pub dropped_blocklist: u64,
    pub dropped_rate_limit: u64,
    pub dropped_syn_flood: u64,
    pub passed_pkts: u64,
    pub passed_allowlist: u64,
}

// ─── BPF MAP DECLARATIONS ─────────────────────────────────────────────────
// Key concept — #[map] attribute:
//   Marks this static as a BPF map.
//   Aya generates the correct ELF section annotation.
//   Equivalent to `struct { ... } name SEC(".maps");` in C.

#[map]
static IP_BLOCKLIST: HashMap<u32, u8> =
    HashMap::with_max_entries(65536, 0);

#[map]
static IP_ALLOWLIST: HashMap<u32, u8> =
    HashMap::with_max_entries(1024, 0);

#[map]
static PKT_RATE_MAP: LruHashMap<u32, RateEntry> =
    LruHashMap::with_max_entries(100_000, 0);

#[map]
static SYN_FLOOD_MAP: LruHashMap<u32, SynEntry> =
    LruHashMap::with_max_entries(100_000, 0);

#[map]
static XDP_STATS: PerCpuArray<Stats> =
    PerCpuArray::with_max_entries(1, 0);

// ─── PACKET PARSING HELPERS ────────────────────────────────────────────────
// Key concept — unsafe pointer arithmetic in Rust BPF:
//   Unlike C, Rust enforces safety rules strictly.
//   In BPF we MUST use unsafe for raw pointer operations,
//   and we MUST do bounds checks (same as C — verifier enforces it).

/// Safely read bytes from XDP packet context.
/// Returns None if access would go out of bounds.
#[inline(always)]
unsafe fn ptr_at<T>(ctx: &XdpContext, offset: usize) -> Option<*const T> {
    let start = ctx.data();
    let end   = ctx.data_end();
    let len   = core::mem::size_of::<T>();

    if start + offset + len > end {
        return None;  // Bounds check — verifier tracks this
    }
    Some((start + offset) as *const T)
}

// ─── ETHERNET HEADER ──────────────────────────────────────────────────────
// Manually define network headers (no kernel headers in no_std Rust BPF)
#[repr(C)]
struct EthHdr {
    h_dest:   [u8; 6],
    h_source: [u8; 6],
    h_proto:  u16,  // network byte order (big-endian)
}

const ETH_P_IP: u16 = 0x0800_u16.to_be(); // big-endian 0x0800

// ─── IPv4 HEADER ──────────────────────────────────────────────────────────
#[repr(C)]
struct Ipv4Hdr {
    version_ihl: u8,  // version (4 bits) | IHL (4 bits)
    tos:         u8,
    tot_len:     u16,
    id:          u16,
    frag_off:    u16,
    ttl:         u8,
    protocol:    u8,
    check:       u16,
    saddr:       u32,  // network byte order
    daddr:       u32,
}

const IPPROTO_TCP: u8 = 6;

impl Ipv4Hdr {
    #[inline(always)]
    fn ihl_bytes(&self) -> usize {
        // IHL field is in 32-bit words; multiply by 4 for bytes
        ((self.version_ihl & 0x0f) as usize) * 4
    }
}

// ─── TCP HEADER ───────────────────────────────────────────────────────────
#[repr(C)]
struct TcpHdr {
    source:  u16,
    dest:    u16,
    seq:     u32,
    ack_seq: u32,
    flags:   u16,  // data_off (4) | reserved (3) | flags (9)
    window:  u16,
    check:   u16,
    urg_ptr: u16,
}

impl TcpHdr {
    #[inline(always)]
    fn is_syn(&self) -> bool {
        // SYN flag is bit 1 of the low byte of flags (big-endian)
        (u16::from_be(self.flags) & 0x002) != 0
    }

    #[inline(always)]
    fn is_ack(&self) -> bool {
        (u16::from_be(self.flags) & 0x010) != 0
    }
}

// ─── RATE LIMITER ─────────────────────────────────────────────────────────
#[inline(always)]
unsafe fn is_rate_limited(src_ip: u32) -> bool {
    let now = aya_ebpf::helpers::bpf_ktime_get_ns();

    match PKT_RATE_MAP.get_ptr_mut(&src_ip) {
        Some(entry) => {
            let elapsed = now - (*entry).window_start;
            if elapsed >= NANOSEC_PER_SEC {
                (*entry).count        = 1;
                (*entry).window_start = now;
                false
            } else {
                (*entry).count += 1;
                (*entry).count > RATE_LIMIT_PKTS
            }
        }
        None => {
            // First packet from this IP
            let _ = PKT_RATE_MAP.insert(
                &src_ip,
                &RateEntry { count: 1, window_start: now },
                0,
            );
            false
        }
    }
}

// ─── SYN FLOOD DETECTOR ───────────────────────────────────────────────────
#[inline(always)]
unsafe fn is_syn_flood(src_ip: u32, tcp: *const TcpHdr) -> bool {
    if !(*tcp).is_syn() || (*tcp).is_ack() {
        return false;
    }

    let now = aya_ebpf::helpers::bpf_ktime_get_ns();

    match SYN_FLOOD_MAP.get_ptr_mut(&src_ip) {
        Some(entry) => {
            if now - (*entry).window_start >= NANOSEC_PER_SEC {
                (*entry).syn_count    = 1;
                (*entry).window_start = now;
                false
            } else {
                (*entry).syn_count += 1;
                (*entry).syn_count > SYN_FLOOD_THRESHOLD
            }
        }
        None => {
            let _ = SYN_FLOOD_MAP.insert(
                &src_ip,
                &SynEntry { syn_count: 1, window_start: now },
                0,
            );
            false
        }
    }
}

// ─── MAIN XDP ENTRY POINT ─────────────────────────────────────────────────
// Key concept — #[xdp] attribute:
//   Marks this function as an XDP program.
//   Aya places it in the "xdp" ELF section.
//   The function signature MUST take XdpContext and return u32.
#[xdp]
pub fn xdp_security(ctx: XdpContext) -> u32 {
    match try_xdp_security(&ctx) {
        Ok(action)  => action,
        Err(_)      => xdp_action::XDP_PASS,  // fail open (never drop on error)
    }
}

// Inner function returns Result so we can use ? for early-exit.
// Key concept — "fail open" vs "fail closed":
//   Fail open  (return PASS on error): avoid blocking legitimate traffic.
//   Fail closed (return DROP on error): more secure but risky.
//   For a firewall, choose carefully. Here we fail open.
#[inline(always)]
fn try_xdp_security(ctx: &XdpContext) -> Result<u32, ()> {
    // ── LAYER 2: Ethernet ──
    let eth: *const EthHdr = unsafe { ptr_at(ctx, 0) }.ok_or(())?;

    if unsafe { (*eth).h_proto } != ETH_P_IP {
        return Ok(xdp_action::XDP_PASS);
    }

    // ── LAYER 3: IPv4 ──
    let ipv4: *const Ipv4Hdr =
        unsafe { ptr_at(ctx, core::mem::size_of::<EthHdr>()) }.ok_or(())?;

    let src_ip = unsafe { (*ipv4).saddr };

    // ── ALLOWLIST ──
    if unsafe { IP_ALLOWLIST.get(&src_ip) }.is_some() {
        return Ok(xdp_action::XDP_PASS);
    }

    // ── BLOCKLIST ──
    if let Some(&1) = unsafe { IP_BLOCKLIST.get(&src_ip) } {
        return Ok(xdp_action::XDP_DROP);
    }

    // ── RATE LIMIT ──
    if unsafe { is_rate_limited(src_ip) } {
        let _ = unsafe { IP_BLOCKLIST.insert(&src_ip, &1, 0) };
        return Ok(xdp_action::XDP_DROP);
    }

    // ── LAYER 4: TCP / SYN FLOOD ──
    if unsafe { (*ipv4).protocol } == IPPROTO_TCP {
        let ihl = unsafe { (*ipv4).ihl_bytes() };
        if ihl < core::mem::size_of::<Ipv4Hdr>() {
            return Ok(xdp_action::XDP_DROP);
        }
        let tcp_offset = core::mem::size_of::<EthHdr>() + ihl;
        let tcp: *const TcpHdr =
            unsafe { ptr_at(ctx, tcp_offset) }.ok_or(())?;

        if unsafe { is_syn_flood(src_ip, tcp) } {
            let _ = unsafe { IP_BLOCKLIST.insert(&src_ip, &1, 0) };
            return Ok(xdp_action::XDP_DROP);
        }
    }

    Ok(xdp_action::XDP_PASS)
}

// Required by Rust BPF: panic handler (must not actually panic in BPF)
#[cfg(not(test))]
#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {
    loop {}
}
