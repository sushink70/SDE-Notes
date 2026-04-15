// SPDX-License-Identifier: GPL-2.0
//! xdp_filter — aya-bpf kernel-side XDP program (Rust)
//!
//! Mirrors the logic of xdp_filter.bpf.c exactly:
//!   1. Parse Ethernet → IPv4
//!   2. Blocklist check (HASH map keyed by src IP in network byte-order)
//!   3. Per-source rate limiting (LRU_HASH, 1-second sliding window)
//!   4. Per-CPU stats array
//!
//! Build (cross-compile for BPF target):
//!   cargo build --package xdp-filter-ebpf \
//!               --target bpfel-unknown-none \
//!               -Z build-std=core
//!
//! The aya userspace crate loads the compiled .elf directly via
//! include_bytes_aligned!() — no separate compilation step needed.
//!
//! References:
//!   https://aya-rs.dev/book/
//!   https://github.com/aya-rs/aya

#![no_std]
#![no_main]

use aya_bpf::{
    bindings::xdp_action,
    macros::{map, xdp},
    maps::{HashMap, LruHashMap, PerCpuArray},
    programs::XdpContext,
};
use aya_log_ebpf::info;
use network_types::{
    eth::{EthHdr, EtherType},
    ip::Ipv4Hdr,
};

// ── Constants ──────────────────────────────────────────────────────────────
const MAX_ENTRIES: u32 = 65_536;
const RATE_LIMIT_PPS: u64 = 1_000;
const NS_PER_SEC: u64 = 1_000_000_000;

// Stats array indices
const STAT_PASS: u32 = 0;
const STAT_BLOCK: u32 = 1;
const STAT_RATE: u32 = 2;
const STAT_PARSE: u32 = 3;

// ── BPF Map declarations ───────────────────────────────────────────────────

/// Blocklist: network-order src IPv4 → u8 flag (1 = drop)
#[map(name = "blocklist")]
static mut BLOCKLIST: HashMap<u32, u8> = HashMap::with_max_entries(MAX_ENTRIES, 0);

/// Rate-limit tracking: src IPv4 → [count, last_reset_ns]
/// Packed as a u128: high 64 bits = count, low 64 bits = last_reset_ns
#[map(name = "rate_map")]
static mut RATE_MAP: LruHashMap<u32, u128> = LruHashMap::with_max_entries(MAX_ENTRIES, 0);

/// Per-CPU stats counters
#[map(name = "stats")]
static mut STATS: PerCpuArray<u64> = PerCpuArray::with_max_entries(4, 0);

// ── Helper: increment a stats counter ─────────────────────────────────────
#[inline(always)]
unsafe fn inc_stat(idx: u32) {
    if let Some(val) = STATS.get_ptr_mut(idx) {
        *val += 1;
    }
}

// ── Helper: safe pointer bounds check ─────────────────────────────────────
/// Returns a reference to T at `offset` from `ctx.data_start()`,
/// ensuring we don't exceed `ctx.data_end()`.
#[inline(always)]
unsafe fn ptr_at<T>(ctx: &XdpContext, offset: usize) -> Option<*const T> {
    let start = ctx.data();
    let end = ctx.data_end();
    let len = core::mem::size_of::<T>();

    if start + offset + len > end {
        return None;
    }
    Some((start + offset) as *const T)
}

// ── XDP entry point ────────────────────────────────────────────────────────
#[xdp]
pub fn xdp_filter_prog(ctx: XdpContext) -> u32 {
    match unsafe { try_xdp_filter(&ctx) } {
        Ok(ret) => ret,
        Err(_) => xdp_action::XDP_ABORTED,  // Internal error → let kernel handle
    }
}

unsafe fn try_xdp_filter(ctx: &XdpContext) -> Result<u32, ()> {
    // ── 1. Parse Ethernet header ───────────────────────────────────────────
    let eth = ptr_at::<EthHdr>(ctx, 0).ok_or_else(|| {
        inc_stat(STAT_PARSE);
    })?;

    // Only process IPv4
    if (*eth).ether_type != EtherType::Ipv4 {
        inc_stat(STAT_PASS);
        return Ok(xdp_action::XDP_PASS);
    }

    // ── 2. Parse IPv4 header ───────────────────────────────────────────────
    let ip = ptr_at::<Ipv4Hdr>(ctx, EthHdr::LEN).ok_or_else(|| {
        inc_stat(STAT_PARSE);
    })?;

    // Validate IHL (minimum 5 × 4 = 20 bytes)
    let ihl = (*ip).ihl();
    if ihl < 5 {
        inc_stat(STAT_PARSE);
        return Ok(xdp_action::XDP_PASS);
    }

    // Source IP in NETWORK byte-order — matches map population from userspace
    let src_ip: u32 = (*ip).src_addr;   // u32 already in network order

    // ── 3. Blocklist check ─────────────────────────────────────────────────
    if let Some(flag) = BLOCKLIST.get(&src_ip) {
        if *flag != 0 {
            inc_stat(STAT_BLOCK);
            return Ok(xdp_action::XDP_DROP);
        }
    }

    // ── 4. Rate limiting ───────────────────────────────────────────────────
    // Pack state as u128: upper 64 bits = count, lower 64 bits = last_reset_ns
    let now: u64 = aya_bpf::helpers::bpf_ktime_get_ns();

    match RATE_MAP.get(&src_ip) {
        None => {
            // First packet from this source
            let state: u128 = (1u128 << 64) | (now as u128);
            RATE_MAP.insert(&src_ip, &state, 0).ok();
            inc_stat(STAT_PASS);
            Ok(xdp_action::XDP_PASS)
        }
        Some(state) => {
            let mut count        = (state >> 64) as u64;
            let last_reset_ns = (*state & 0xFFFF_FFFF_FFFF_FFFF) as u64;

            let (new_count, new_ts) = if now.wrapping_sub(last_reset_ns) >= NS_PER_SEC {
                // Window expired: reset counter
                (1u64, now)
            } else {
                count += 1;
                (count, last_reset_ns)
            };

            let updated: u128 = ((new_count as u128) << 64) | (new_ts as u128);
            // Note: get() returned a ref into the map — we must use insert to update
            RATE_MAP.insert(&src_ip, &updated, 0).ok();

            if new_count > RATE_LIMIT_PPS && now.wrapping_sub(last_reset_ns) < NS_PER_SEC {
                inc_stat(STAT_RATE);
                Ok(xdp_action::XDP_DROP)
            } else {
                inc_stat(STAT_PASS);
                Ok(xdp_action::XDP_PASS)
            }
        }
    }
}

// Required by the BPF verifier
#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {
    unsafe { core::hint::unreachable_unchecked() }
}
