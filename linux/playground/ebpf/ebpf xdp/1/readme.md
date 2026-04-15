# Elite Linux Kernel Developer: eBPF + Net Subsystem
## Complete Field Manual — C & Rust

---

## Directory Layout

```
ebpf-net-guide/
├── README.md                    ← You are here
├── c/
│   ├── kern/
│   │   ├── xdp_pkt_counter.bpf.c   ← eBPF kernel-side (XDP)
│   │   ├── tc_rate_limit.bpf.c     ← eBPF TC egress limiter
│   │   └── netdev_module.c         ← Traditional kernel module (net notifier)
│   ├── user/
│   │   ├── loader.c                ← libbpf userspace loader
│   │   └── stats.c                 ← Read/print BPF maps
│   ├── bugs/
│   │   ├── bug_code_demo.bpf.c     ← Intentional code bug
│   │   └── bug_logic_demo.bpf.c    ← Intentional logic bug
│   ├── tests/
│   │   ├── test_xdp.sh             ← Functional test with veth pair
│   │   └── test_module.sh          ← Module load/unload tests
│   └── Makefile
├── rust/
│   ├── xdp-counter/
│   │   ├── Cargo.toml
│   │   ├── src/
│   │   │   ├── main.rs             ← Aya userspace
│   │   │   └── bpf/
│   │   │       └── xdp_counter.rs  ← Aya eBPF program
│   │   └── build.rs
│   └── README.md
├── scripts/
│   ├── setup_env.sh                ← Full dev env bootstrap
│   ├── load_xdp.sh
│   ├── unload_xdp.sh
│   ├── debug_bpf.sh                ← ftrace + bpf_printk reader
│   └── send_test_traffic.sh
└── docs/
    ├── WORKFLOW.md                 ← How Linus's tree works
    ├── DEBUGGING.md                ← Complete debug guide
    ├── ROADMAP.md                  ← 6-month elite roadmap
    └── REFERENCES.md               ← All docs/books/repos
```