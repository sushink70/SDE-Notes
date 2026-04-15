// File: rust/xdp-counter/src/bpf/xdp_counter.rs
//
// eBPF XDP program written in Rust using the Aya framework.
//
// Aya = pure-Rust eBPF library. No C, no LLVM wrappers, no libbpf dependency.
// It uses the Rust BPF target (bpfel-unknown-none) to emit BPF bytecode.
//
// PROJECT STRUCTURE (Aya convention — workspace with two crates):
//
//   xdp-counter/
//   ├── Cargo.toml              (workspace root)
//   ├── xdp-counter/            (userspace crate)
//   │   ├── Cargo.toml
//   │   └── src/main.rs
//   ├── xdp-counter-ebpf/       (eBPF crate — this file)
//   │   ├── Cargo.toml
//   │   └── src/main.rs         (contains the eBPF program below)
//   └── xdp-counter-common/     (shared structs between both crates)
//       ├── Cargo.toml
//       └── src/lib.rs
//
// BUILD:
//   cargo xtask build-ebpf    (builds the eBPF crate for bpfel target)
//   cargo build               (builds userspace)
//
// HOW AYA WORKS:
//   The eBPF crate compiles to BPF bytecode. The userspace crate embeds
//   that bytecode using include_bytes_aligned!() and loads it at runtime
//   without any external .o files.

// eBPF crate — compiles to BPF bytecode
// This goes in: xdp-counter-ebpf/src/main.rs

#![no_std]
#![no_main]

// Panic handler for no_std BPF programs
use aya_ebpf::macros::{map, xdp};
use aya_ebpf::maps::PerCpuArray;
use aya_ebpf::programs::XdpContext;
use aya_ebpf::{bindings::xdp_action, helpers::bpf_ktime_get_ns};
use aya_log_ebpf::debug;
use core::mem;

// Shared types from the common crate
// In a real workspace: use xdp_counter_common::*;
// Here we define inline for clarity:

#[repr(C)]
#[derive(Copy, Clone, Default)]
pub struct PacketStats {
    pub packets: u64,
    pub bytes: u64,
    pub drops: u64,
}

// ─── Maps ─────────────────────────────────────────────────────────────────────
//
// Aya's map macros generate the correct BPF map ELF sections.
// PerCpuArray<T, N> maps to BPF_MAP_TYPE_PERCPU_ARRAY.
// Array index = key (protocol number).

#[map]
static PROTO_STATS: PerCpuArray<PacketStats> = PerCpuArray::with_max_entries(256, 0);

// ─── Network header parsing ───────────────────────────────────────────────────
//
// Aya provides ptr_at<T>() which does the bounds check automatically.
// This is the Rust-idiomatic way to replace the C bounds-check pattern.

#[inline(always)]
fn ptr_at<T>(ctx: &XdpContext, offset: usize) -> Option<*const T> {
    let start = ctx.data();
    let end   = ctx.data_end();
    let len   = mem::size_of::<T>();

    if start + offset + len > end {
        return None;
    }
    Some((start + offset) as *const T)
}

// Ethernet header constants (no kernel headers in no_std)
const ETH_P_IP:   u16 = 0x0800;
const ETH_P_IPV6: u16 = 0x86DD;
const IPPROTO_TCP: u8 = 6;
const IPPROTO_UDP: u8 = 17;

// Minimal header representations
#[repr(C, packed)]
struct EthHdr {
    h_dest:   [u8; 6],
    h_source: [u8; 6],
    h_proto:  u16,   // big-endian
}

#[repr(C)]
struct IpHdr {
    version_ihl: u8,
    tos:         u8,
    tot_len:     u16,
    id:          u16,
    frag_off:    u16,
    ttl:         u8,
    protocol:    u8,
    check:       u16,
    saddr:       u32,
    daddr:       u32,
}

impl IpHdr {
    fn ihl(&self) -> u8 {
        self.version_ihl & 0x0F
    }
}

// ─── XDP Entry Point ──────────────────────────────────────────────────────────
//
// #[xdp] macro generates the SEC("xdp") ELF section.
// The function MUST return xdp_action (u32).

#[xdp]
pub fn xdp_packet_counter(ctx: XdpContext) -> u32 {
    match try_xdp_pkt_counter(&ctx) {
        Ok(action) => action,
        // On any parse error (bounds violation), just pass the packet through
        Err(_)     => xdp_action::XDP_PASS,
    }
}

fn try_xdp_pkt_counter(ctx: &XdpContext) -> Result<u32, ()> {
    let eth: *const EthHdr = ptr_at(ctx, 0).ok_or(())?;
    // SAFETY: ptr_at verified bounds above
    let h_proto = u16::from_be(unsafe { (*eth).h_proto });

    let pkt_len = (ctx.data_end() - ctx.data()) as u64;
    let mut proto_key: u32 = 255; // "other"

    if h_proto == ETH_P_IP {
        let ip_off = mem::size_of::<EthHdr>();
        let iph: *const IpHdr = ptr_at(ctx, ip_off).ok_or(())?;
        // SAFETY: ptr_at verified
        let protocol = unsafe { (*iph).protocol };
        let ihl      = unsafe { (*iph).ihl() };

        proto_key = protocol as u32;

        // Demonstrate TCP SYN parsing in Rust (same logic as C version)
        if protocol == IPPROTO_TCP {
            // Parse TCP header
            let tcp_off = ip_off + (ihl as usize * 4);
            // We only need bytes 12-13 for flags
            // In a real program use a proper TcpHdr struct
            let _tcp_flags_ptr: *const u8 = ptr_at(ctx, tcp_off + 13).ok_or(())?;
        }
    } else if h_proto == ETH_P_IPV6 {
        let ip6_off = mem::size_of::<EthHdr>();
        // IPv6 next_header is at offset 6 in the IPv6 header
        let nexthdr_ptr: *const u8 = ptr_at(ctx, ip6_off + 6).ok_or(())?;
        proto_key = unsafe { *nexthdr_ptr } as u32;
    }

    // Update per-CPU stats
    // Aya's get_ptr_mut() returns Option — safe access
    if let Some(stats) = PROTO_STATS.get_ptr_mut(proto_key) {
        // SAFETY: per-CPU means no concurrent access
        unsafe {
            (*stats).packets += 1;
            (*stats).bytes   += pkt_len;
        }
    }

    // Also update total (key=0)
    if let Some(total) = PROTO_STATS.get_ptr_mut(0) {
        unsafe {
            (*total).packets += 1;
            (*total).bytes   += pkt_len;
        }
    }

    Ok(xdp_action::XDP_PASS)
}

#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {
    loop {}
}