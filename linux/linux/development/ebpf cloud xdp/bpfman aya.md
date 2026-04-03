Let me fetch the actual source files so I give you real, accurate entry points — not guesses.Now I have real, accurate data from the actual docs and source. Let me give you the precise, surgical entry point guide.

---

# 🎯 The Exact Entry Points for Code Investigation

The correct mental model before you open a single file:

```
THERE ARE TWO SIDES TO AYA — ALWAYS REMEMBER THIS:

  SIDE A: aya-ebpf/          ← Runs INSIDE the Linux kernel (eBPF VM)
  SIDE B: aya/               ← Runs in YOUR process (userspace)

  They COMMUNICATE via BPF Maps.
  You must understand BOTH sides to understand aya.
```

Do not mix them up. Different constraints, different APIs, different Rust targets.

---

## 🔴 ENTRY POINT #1 — The Userspace Side (`aya/`)

The single most important struct in the entire codebase is:

```
aya::Ebpf
```

For more loading options, see `EbpfLoader`. The `Ebpf` struct is used like: `let bpf = Ebpf::load_file("file.o")?` — it loads eBPF bytecode from a file, parses the object code, and initializes the maps defined in it. If the kernel supports BTF debug info, it is automatically loaded from `/sys/kernel/btf/vmlinux`.

Everything flows through this struct. Here is the **exact file path and call chain** to trace:

```
FILE:  aya/src/lib.rs          ← Public API definition, re-exports
         ↓
FILE:  aya/src/ebpf.rs         ← Ebpf struct implementation
         ↓
  pub fn load_file(path) → calls load(bytes)
         ↓
  pub fn load(data: &[u8]) → calls EbpfLoader::new().load(data)
         ↓
FILE:  aya/src/ebpf.rs         ← EbpfLoader struct
         ↓
  fn load(data) →
    1. aya_obj::Object::parse(data)    ← PARSES the .o ELF file
    2. object.relocate_maps()          ← Fixes map references
    3. object.relocate_btf()           ← Applies BTF relocations
    4. bpf_load_map() for each map     ← Kernel syscall per map
    5. bpf_load_program() per program  ← Kernel syscall per program
         ↓
FILE:  aya/src/sys/bpf.rs      ← RAW BPF SYSCALL WRAPPERS
         ↓
  bpf(BPF_PROG_LOAD, attr)  ← THIS IS THE ACTUAL LINUX SYSCALL
```

**Your investigation trail, step by step:**

```
STEP 1 — Open:  aya/src/lib.rs
  Purpose: See what is public API. What does aya EXPORT?
  Look for: pub use, pub mod
  Key question: "What can a user of this library actually touch?"

STEP 2 — Open:  aya/src/ebpf.rs
  Purpose: The Ebpf struct — the heart of userspace aya
  Look for: impl Ebpf, impl EbpfLoader
  Key question: "How does load() actually work, step by step?"

STEP 3 — Open:  aya-obj/src/obj.rs  (or mod.rs)
  Purpose: ELF object file parser — reads your .o file
  Key concept: ELF = Executable and Linkable Format.
               Your compiled eBPF code is stored as ELF.
               aya parses it WITHOUT libbpf — this is what makes aya unique.
  Look for: pub struct Object, fn parse()
  Key question: "How does aya read sections from the .o file?"

STEP 4 — Open:  aya/src/sys/bpf.rs
  Purpose: The LOWEST level — direct kernel BPF syscalls
  Look for: fn bpf(), BPF_PROG_LOAD, BPF_MAP_CREATE
  Key question: "What does the kernel actually receive?"
  WARNING: This is unsafe Rust. Study it carefully.
```

---

## 🔵 ENTRY POINT #2 — The Kernel Side (`aya-ebpf/`)

This is the code that actually runs **inside the kernel**. It has completely different constraints than normal Rust:

```
CONSTRAINTS OF eBPF RUST (aya-ebpf side):
┌──────────────────────────────────────────────┐
│  NO std library  → use core instead          │
│  NO heap         → no Vec, no String         │
│  NO panic        → must handle all errors    │
│  NO main()       → entry = your #[xdp] fn   │
│  512 bytes stack → be very careful           │
│  NO loops that   → verifier rejects infinite │
│  run forever       loops                     │
└──────────────────────────────────────────────┘
```

The entry point of a kernel-side eBPF program in aya looks like this (from the real Aya book):

```rust
#![no_std]   // ← NO standard library
#![no_main]  // ← NO main() function

use aya_ebpf::{
    bindings::xdp_action,
    macros::xdp,           // ← PROC MACRO: generates ELF section name
    programs::XdpContext,  // ← Context gives you access to the packet
};

#[xdp]   // ← This macro is the ENTRY POINT declaration
pub fn xdp_hello(ctx: XdpContext) -> u32 {
    match unsafe { try_xdp_hello(ctx) } {
        Ok(ret) => ret,
        Err(_) => xdp_action::XDP_ABORTED,
    }
}

unsafe fn try_xdp_hello(ctx: XdpContext) -> Result<u32, u32> {
    Ok(xdp_action::XDP_PASS)  // ← Let packet through
}

#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {
    loop {}  // ← Verifier ensures this is never reached
}
```

**Your investigation trail for the kernel side:**

```
STEP 1 — Open: aya-ebpf-macros/src/lib.rs
  Purpose: The proc macros like #[xdp], #[kprobe], #[tracepoint]
  Key question: "What does #[xdp] actually DO to my function?"
  Answer: It places the function in the correct ELF section
          e.g. section name "xdp" → kernel knows it's an XDP program

STEP 2 — Open: aya-ebpf/src/programs/xdp.rs
  Purpose: XdpContext — the struct passed to your XDP function
  Key question: "How do I access packet data from context?"
  Look for: impl XdpContext, data(), data_end()

STEP 3 — Open: aya-ebpf/src/maps/hash_map.rs
  Purpose: HashMap on the eBPF (kernel) side
  Key question: "How does a map lookup work from inside the kernel?"
  Look for: fn get(), fn insert()
  Note: These call kernel BPF helper functions like bpf_map_lookup_elem
```

---

## 🟢 ENTRY POINT #3 — The Bridge: BPF Maps

Maps are the **communication channel** between your kernel eBPF code and your userspace Rust app. Understanding them is critical.

```
KERNEL SIDE                    USERSPACE SIDE
(aya-ebpf/src/maps/)           (aya/src/maps/)

HashMap::get(&key)    ←→    HashMap::get(&key, &mut value)
HashMap::insert()     ←→    HashMap::insert(&key, &value, flags)
PerfEventArray        ←→    AsyncPerfEventArray
                             (async! reads events from kernel)
```

```
FILE TO OPEN:  aya/src/maps/hash_map.rs    (userspace)
FILE TO OPEN:  aya-ebpf/src/maps/hash_map.rs  (kernel side)

COMPARE THEM SIDE BY SIDE.
They operate on the SAME kernel memory but through different APIs.
This comparison will teach you more than any tutorial.
```

---

## 🟡 ENTRY POINT #4 — bpfman's `main.rs`

For bpfman, the entry is the daemon binary:

```
FILE:  bpfman/src/bin/bpfman.rs   ← main() of the daemon
         ↓
  Sets up gRPC server
         ↓
FILE:  bpfman-api/src/lib.rs      ← gRPC API (protobuf-generated + handwritten)
         ↓
FILE:  bpfman/src/lib.rs          ← Core program management logic
         ↓
FILE:  bpfman/src/multiprog/      ← THE MOST INTERESTING PART
         xdp.rs                   ← XDP dispatcher (how multiple programs share one hook)
         tc.rs                    ← TC dispatcher
```

The **dispatcher** is bpfman's secret weapon. This is how it lets multiple eBPF programs share one XDP hook — it inserts its own eBPF program that acts as a jump table, calling each registered program in sequence.

```
WITHOUT bpfman:
  eth0 XDP hook → YOUR program (only one allowed)

WITH bpfman dispatcher:
  eth0 XDP hook → bpfman DISPATCHER program
                      ↓
                  calls program A  (returns XDP_PASS)
                      ↓
                  calls program B  (returns XDP_DROP)
                      ↓
                  final verdict = XDP_DROP
```

---

## The Investigation Protocol (How Experts Read a New Codebase)

Use this exact method — it's called **"breadth-first skeleton, then depth-first focus"**:

```
PHASE 1: SKELETON (2 hours)
  Do NOT read implementation details yet.
  Open every file, read only:
  - Struct names
  - Public fn signatures
  - Module names
  Draw the map on paper.

PHASE 2: TRACE ONE PATH (4 hours)
  Pick ONE operation: Ebpf::load_file("x.o")
  Follow it from the top call to the raw syscall.
  Read EVERY line on that path.
  Annotate what you don't understand.

PHASE 3: FOLLOW THE DATA (ongoing)
  Pick ONE data structure: e.g. HashMap map
  Trace it:
  - How is it DEFINED in eBPF? (aya-ebpf/src/maps/)
  - How is it CREATED? (bpf_map_create syscall in sys/bpf.rs)
  - How is it WRITTEN from kernel side? (bpf_map_update_elem helper)
  - How is it READ from userspace? (aya/src/maps/hash_map.rs)

PHASE 4: READ THE TESTS
  The integration tests in test/ are DOCUMENTATION.
  They show you exactly how the API is meant to be used.
  Treat every test as a guaranteed-correct usage example.
```

---

## Concrete First Session — Exactly What to Open Right Now

```bash
git clone https://github.com/aya-rs/aya
cd aya

# Open these files in this order, in your editor:
# 1. aya/src/lib.rs              ← 5 min: public API overview
# 2. aya/src/ebpf.rs             ← 30 min: Ebpf + EbpfLoader structs
# 3. aya-obj/src/obj.rs          ← 20 min: ELF parsing
# 4. aya/src/sys/bpf.rs          ← 20 min: raw syscalls
# 5. aya/src/programs/xdp.rs     ← 20 min: one program type end-to-end
# 6. aya-ebpf-macros/src/lib.rs  ← 15 min: how #[xdp] works
```

**After this session**, you should be able to answer:
- How does `Ebpf::load_file()` become a `bpf()` syscall?
- What does the `#[xdp]` macro actually emit?
- How is the `.o` ELF file parsed without libbpf?

That's your first milestone. Everything else builds on top of it.

---

**Cognitive note:** What you are doing here is called **"tracing"** — following a single vertical path through a system from the highest abstraction (`load_file`) to the lowest (`bpf() syscall`). This is the single most powerful technique for understanding any large codebase. Computer scientists call this building a **"mental execution model"** — once you can simulate the execution of one operation in your head, the whole system becomes navigable.