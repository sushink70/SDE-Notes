// ebpf-prog/src/main.rs
// BPF LSM kernel-side program written in Rust using aya-bpf.
//
// Project layout (aya convention):
//   ebpf-prog/     — BPF program (compiled with bpf target, no_std)
//     src/main.rs  — this file
//     Cargo.toml
//   userspace/     — host binary (compiled native)
//     src/main.rs
//     Cargo.toml
//
// Build command (from workspace root):
//   cargo xtask build-ebpf   (uses aya-tool xtask pattern)
//   # or manually:
//   cargo build --package ebpf-prog \
//     --target bpfel-unknown-none \   # or bpfeb- for big-endian
//     -Z build-std=core               # no_std requires build-std nightly feature
//
// References:
//   https://aya-rs.dev/book/
//   https://docs.rs/aya-bpf/latest/aya_bpf/
//   https://github.com/aya-rs/aya/tree/main/examples

// BPF programs run in kernel context: no stdlib, no heap allocator.
#![no_std]
#![no_main]

// aya-bpf provides:
//   - BPF helper wrappers (bpf_map_*, bpf_get_current_*, etc.)
//   - Map types (HashMap, RingBuf, PerCpuArray, etc.)
//   - Program attribute macros (#[lsm], #[kprobe], etc.)
//   - bpf_printk! for kernel debug output
use aya_bpf::{
    bindings::path,
    cty::c_int,
    helpers::{bpf_get_current_comm, bpf_get_current_pid_tgid, bpf_get_current_uid_gid, bpf_ktime_get_ns},
    macros::{lsm, map},
    maps::{HashMap, PerCpuArray, RingBuf},
    programs::LsmContext,
    BpfContext,
};
use aya_log_ebpf::info;

// Shared types: in a real workspace, use a shared `common` crate
// that both ebpf-prog and userspace depend on.
// Here we inline them for clarity.

// ─── Event Types ──────────────────────────────────────────────────────────────
const EVENT_EXEC_BLOCKED: u32     = 1;
const EVENT_FILE_OPEN_DENIED: u32 = 2;
const EVENT_PTRACE_BLOCKED: u32   = 3;

const POLICY_DENY: u8  = 1;
const POLICY_AUDIT: u8 = 2;

// ─── Shared Event Structure ───────────────────────────────────────────────────
// Must match the layout in the Rust userspace and the C header.
// #[repr(C)] ensures no Rust-specific padding/reordering.
#[repr(C)]
pub struct LsmEvent {
    pub timestamp_ns: u64,
    pub event_type:   u32,
    pub pid:          u32,
    pub tid:          u32,
    pub uid:          u32,
    pub gid:          u32,
    pub inode:        u32,
    pub dev:          u32,
    pub padding:      u32,
    pub comm:         [u8; 16],
    pub path:         [u8; 128],
}

// ─── Policy Key ───────────────────────────────────────────────────────────────
#[repr(C)]
#[derive(Copy, Clone)]
pub struct PolicyKey {
    pub inode: u32,
    pub dev:   u32,
}

// ─── Maps ─────────────────────────────────────────────────────────────────────

// Ringbuf: kernel → userspace event channel
// capacity must be a power-of-2 number of bytes
#[map]
static EVENTS: RingBuf = RingBuf::with_byte_size(256 * 1024, 0);

// File-level policy: key={inode,dev}, value=POLICY_DENY|POLICY_AUDIT
#[map]
static BLOCKED_FILES: HashMap<PolicyKey, u8> =
    HashMap::<PolicyKey, u8>::with_max_entries(4096, 0);

// UID-level policy: key=uid, value=POLICY_DENY
#[map]
static BLOCKED_UIDS: HashMap<u32, u8> =
    HashMap::<u32, u8>::with_max_entries(256, 0);

// Per-CPU stats: index = hook type, value = (total, denied)
// PerCpuArray avoids atomic contention on hot paths
#[repr(C)]
#[derive(Copy, Clone, Default)]
pub struct HookStats {
    pub total:  u64,
    pub denied: u64,
}

#[map]
static STATS: PerCpuArray<HookStats> = PerCpuArray::<HookStats>::with_max_entries(4, 0);

// ─── Helper: emit event to ringbuf ───────────────────────────────────────────
//
// #[inline(always)] — BPF verifier has a call instruction limit;
// inlining avoids the call overhead and stack frame nesting limit.
// aya-bpf functions are generally inlined; explicitly mark helpers.
#[inline(always)]
unsafe fn emit_event(event_type: u32, inode: u32, dev: u32) {
    let mut entry = match EVENTS.reserve::<LsmEvent>(0) {
        Some(e) => e,
        None    => return, // ringbuf full — drop event
    };

    let pid_tgid = bpf_get_current_pid_tgid();
    let uid_gid  = bpf_get_current_uid_gid();

    let e = entry.as_mut_ptr();

    (*e).timestamp_ns = bpf_ktime_get_ns();
    (*e).event_type   = event_type;
    (*e).pid          = (pid_tgid >> 32) as u32;
    (*e).tid          = (pid_tgid & 0xFFFF_FFFF) as u32;
    (*e).uid          = (uid_gid  & 0xFFFF_FFFF) as u32;
    (*e).gid          = (uid_gid  >> 32) as u32;
    (*e).inode        = inode;
    (*e).dev          = dev;
    (*e).padding      = 0;
    (*e).path[0]      = 0;

    // bpf_get_current_comm writes up to 16 bytes; on error comm is zeroed
    let comm_ptr = (*e).comm.as_mut_ptr();
    let _ = bpf_get_current_comm(comm_ptr as *mut _, 16);

    entry.submit(0);
}

// ─── Helper: update per-CPU stats ────────────────────────────────────────────
#[inline(always)]
unsafe fn update_stats(hook_idx: u32, denied: bool) {
    if let Some(s) = STATS.get_ptr_mut(hook_idx) {
        (*s).total  += 1;
        if denied {
            (*s).denied += 1;
        }
    }
}

// ─── LSM Hook 1: bprm_check_security ─────────────────────────────────────────
//
// #[lsm(hook = "bprm_check_security")] tells the linker to place this
// function in the correct ELF section: "lsm/bprm_check_security"
// The kernel's BPF LSM dispatcher calls it at exec time.
//
// LsmContext wraps the kernel-provided args. For bprm_check_security,
// ctx.arg(0) is a *const linux_binprm pointer. We use raw pointer reads
// guarded by BPF verifier checks.
#[lsm(hook = "bprm_check_security")]
pub fn bprm_check_security(ctx: LsmContext) -> i32 {
    // Safety: BPF verifier ensures we only reach this in valid LSM context.
    // The pointer passed from the kernel is always valid at hook call time.
    match unsafe { try_bprm_check(&ctx) } {
        Ok(ret)  => ret,
        Err(ret) => ret,
    }
}

unsafe fn try_bprm_check(ctx: &LsmContext) -> Result<i32, i32> {
    // Read linux_binprm → file → f_inode → {i_ino, i_sb → s_dev}
    // aya-bpf provides co_re_read! for BTF-guided reads, equivalent to
    // BPF_CORE_READ in C. Without CO-RE: use ctx.read_at() with known offsets.
    //
    // For production, use aya-tool to generate Rust bindings from vmlinux BTF:
    //   aya-tool generate linux_binprm > binprm_types.rs
    // Then access fields via generated structs.
    //
    // Here we demonstrate the raw approach with explicit byte offsets as fallback:
    let bprm_ptr: *const u8 = ctx.arg(0);

    // Offsets depend on kernel version — use CO-RE / vmlinux bindings in prod.
    // For demo: hardcode x86_64 6.1 offsets (verify with pahole or bpftool btf)
    //   offsetof(linux_binprm, file) = 168
    //   offsetof(file, f_inode)      = 32
    //   offsetof(inode, i_ino)       = 64
    //   offsetof(inode, i_sb)        = 40
    //   offsetof(super_block, s_dev) = 0
    //
    // NOTE: These offsets are illustrative. Use CO-RE bindings (aya-tool) for
    // real kernels to handle layout changes automatically.
    let file_ptr: *const u8 = *(bprm_ptr.add(168) as *const *const u8);
    let inode_ptr: *const u8 = *(file_ptr.add(32) as *const *const u8);
    let inode_nr: u32 = *(inode_ptr.add(64) as *const u32);
    let sb_ptr: *const u8 = *(inode_ptr.add(40) as *const *const u8);
    let dev: u32 = *(sb_ptr as *const u32);

    let uid_gid = bpf_get_current_uid_gid();
    let uid = (uid_gid & 0xFFFF_FFFF) as u32;

    let mut deny = false;

    // Check UID block list
    if let Some(&action) = BLOCKED_UIDS.get(&uid) {
        if action == POLICY_DENY {
            deny = true;
        }
    }

    if !deny {
        let k = PolicyKey { inode: inode_nr, dev };
        if let Some(&action) = BLOCKED_FILES.get(&k) {
            if action == POLICY_DENY {
                deny = true;
            }
        }
    }

    update_stats(EVENT_EXEC_BLOCKED, deny);

    if deny {
        emit_event(EVENT_EXEC_BLOCKED, inode_nr, dev);
        return Err(-1); // -EPERM = -1 in BPF return convention
    }

    Ok(0)
}

// ─── LSM Hook 2: file_open ────────────────────────────────────────────────────
#[lsm(hook = "file_open")]
pub fn file_open(ctx: LsmContext) -> i32 {
    match unsafe { try_file_open(&ctx) } {
        Ok(ret)  => ret,
        Err(ret) => ret,
    }
}

unsafe fn try_file_open(ctx: &LsmContext) -> Result<i32, i32> {
    let file_ptr: *const u8 = ctx.arg(0);

    // file → f_inode → i_ino, i_sb → s_dev
    let inode_ptr: *const u8 = *(file_ptr.add(32) as *const *const u8);
    let inode_nr: u32 = *(inode_ptr.add(64) as *const u32);
    let sb_ptr: *const u8 = *(inode_ptr.add(40) as *const *const u8);
    let dev: u32 = *(sb_ptr as *const u32);

    let k = PolicyKey { inode: inode_nr, dev };

    if let Some(&action) = BLOCKED_FILES.get(&k) {
        emit_event(EVENT_FILE_OPEN_DENIED, inode_nr, dev);
        update_stats(EVENT_FILE_OPEN_DENIED, action == POLICY_DENY);
        if action == POLICY_DENY {
            return Err(-13); // -EACCES
        }
    }

    update_stats(EVENT_FILE_OPEN_DENIED, false);
    Ok(0)
}

// ─── LSM Hook 3: ptrace_access_check ─────────────────────────────────────────
#[lsm(hook = "ptrace_access_check")]
pub fn ptrace_access_check(ctx: LsmContext) -> i32 {
    match unsafe { try_ptrace(&ctx) } {
        Ok(ret)  => ret,
        Err(ret) => ret,
    }
}

unsafe fn try_ptrace(ctx: &LsmContext) -> Result<i32, i32> {
    let uid_gid = bpf_get_current_uid_gid();
    let current_uid = (uid_gid & 0xFFFF_FFFF) as u32;

    if current_uid == 0 {
        return Ok(0); // root always allowed at this level
    }

    // child: task_struct pointer; arg(0)
    // offsetof(task_struct, cred) ~ 1096 on x86_64 6.1 (verify with pahole)
    // offsetof(cred, uid) ~ 4
    let child_ptr: *const u8 = ctx.arg(0);
    let cred_ptr: *const u8 = *(child_ptr.add(1096) as *const *const u8);
    let target_uid: u32 = *(cred_ptr.add(4) as *const u32);

    let deny = current_uid != target_uid;

    update_stats(EVENT_PTRACE_BLOCKED, deny);

    if deny {
        emit_event(EVENT_PTRACE_BLOCKED, 0, 0);
        return Err(-1); // -EPERM
    }

    Ok(0)
}

// Required panic handler for no_std BPF programs.
// The BPF verifier eliminates unreachable code; this is never called at runtime.
#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {
    loop {}
}
