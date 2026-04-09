# nf_pkt_inspector — Linux net subsystem kernel module

## Tree layout

```
net_hook_mod/
├── c_module/
│   ├── nf_pkt_inspector.c          ← CLEAN module (production quality)
│   ├── nf_pkt_inspector_buggy.c    ← BUGGY module (for KASAN/UBSAN practice)
│   ├── Kbuild                      ← kernel build descriptor
│   └── Makefile                    ← out-of-tree build + helper targets
├── rust_module/
│   ├── nf_pkt_inspector.rs         ← Rust version (targets Linux v6.8 rust-next)
│   └── Kbuild
├── tests/
│   └── test_nf_pkt_inspector.sh    ← functional + stress test suite
├── debug/
│   └── debug_nf_pkt_inspector.sh   ← ftrace/kprobe/KASAN/bpftrace/kgdb guide
└── upstream_workflow.sh            ← full upstream submission guide + docs index
```

## Build

```bash
cd c_module
make                       # build against running kernel
make check                 # checkpatch.pl
make sparse                # sparse static analysis
make load drop_port=8080   # insmod
make status                # cat /proc/net/nf_pkt_inspector
```

## Bugs in nf_pkt_inspector_buggy.c

| Bug | Type | Location | Detection |
|-----|------|----------|-----------|
| BUG1 | Code bug: stale `iph` pointer after `pskb_may_pull()` | TCP branch | KASAN heap-use-after-free |
| BUG2 | Logic bug: off-by-one array overflow in ring buffer | SYN log path | UBSAN array-index-out-of-bounds |

Trigger BUG2: `hping3 -S -p 80 --faster -c 70 127.0.0.1`

## Kernel config for full bug detection

```
CONFIG_KASAN=y
CONFIG_KASAN_INLINE=y
CONFIG_UBSAN=y
CONFIG_UBSAN_BOUNDS=y
CONFIG_LOCKDEP=y
CONFIG_DEBUG_SPINLOCK=y
CONFIG_SLUB_DEBUG=y
```
