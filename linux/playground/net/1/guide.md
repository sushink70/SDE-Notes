This is an elite-level topic. I'll build the full guide: workflow diagram → complete C module with intentional bugs → Rust module → build/load/test/debug pipeline → documentation map. Let me construct everything now.Now I'll build all the files. Let me start with the main C module.Here is a complete breakdown of everything delivered and why each piece is structured the way it is.

---

## What was built and why

### The C module (`net_monitor.c`)

This is a netfilter hook module — the most instructive entry point into the net subsystem because it touches every core concept at once. The two deliberate bugs teach the exact failure classes that cause real kernel panics in production:

**Bug #1 — Memory leak** (`describe_packet_BUGGY`): `kmalloc()` without a paired `kfree()`. On a 1 Mpps link this leaks 64 MB/s of kernel memory until the machine OOM-crashes. Detection tool: `kmemleak`. The fix is trivial — one line — but the lesson is the discipline: *every allocation path must have a corresponding free on every exit path*. The goto-ladder in `module_init` is the canonical kernel pattern for this.

**Bug #2 — Endianness** (`is_loopback_BUGGY`): `iph->saddr == 0x7F000001`. On every x86/ARM machine in existence, `saddr` holds `0x0100007F` (big-endian wire format). The comparison silently fails forever. This is the single most common class of network driver bug. Detection tool: `sparse` with `-D__CHECK_ENDIAN__` catches it at compile time. Fix: `ipv4_is_loopback(iph->saddr)`.

### The Rust module (`lib.rs`)

The Rust version demonstrates the fundamental architectural difference: in C, cleanup correctness depends on programmer discipline (the goto ladder). In Rust, the `Drop` trait *guarantees* cleanup happens when the struct goes out of scope — the type system enforces it. The `unsafe` blocks are intentionally isolated and annotated so you can see exactly where the invariant boundary is.

Note that Rust netfilter abstractions are not yet fully upstreamed as of Linux 6.9. The module uses `kernel::bindings` for raw C calls — this is exactly how kernel Rust contributors work today: safe abstractions exist for some APIs, raw bindings for the rest, with the goal of replacing unsafe blocks over time.

### The three key mental models to internalize

**Softirq context**: Your hook runs in bottom-half (BH) context, meaning it can preempt user-space code but cannot sleep. This single rule dictates `GFP_ATOMIC` everywhere, no `mutex_lock`, no `msleep`. Violating this causes the kernel to print `BUG: sleeping function called from invalid context` and it will panic.

**`sk_buff` is not a buffer — it is a descriptor**: The actual packet bytes are somewhere in `head..end`. Layers of the stack push and pull headers using `skb_push`/`skb_pull` without copying data. When you call `ip_hdr(skb)`, you get a pointer computed from an offset stored in the struct — there is no copy.

**Byte order annotation discipline**: The `__be32` type is Sparse's annotation saying "this is big-endian and must not be compared to a host-order value without conversion." Building with `make C=1 CF=-D__CHECK_ENDIAN__` turns byte-order mistakes into compile-time errors. This one habit eliminates an entire class of bugs.

### The documentation reading order

The `DEVELOPER_GUIDE.md` lists 18 specific files in reading order. The most important for this module are: `include/linux/skbuff.h` (read *every* field comment — this is the central data structure of the entire network stack), `net/netfilter/core.c` (understand what happens inside `nf_register_net_hook`), and `net/netfilter/xt_LOG.c` (a clean, small, upstream module to model your code style from).