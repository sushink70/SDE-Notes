# File: docs/REFERENCES.md
# Complete Reference List: eBPF + Linux Kernel Net Development

---

## Tier 1: Read These First (Canonical Sources)

### Kernel Documentation (in-tree, always current)
```
Documentation/bpf/index.rst               — BPF overview
Documentation/bpf/verifier.rst            — Verifier internals
Documentation/networking/xdp-rx-metadata.rst — XDP metadata
Documentation/networking/af_xdp.rst       — AF_XDP zero-copy
Documentation/networking/filter.txt       — Classic BPF + seccomp
Documentation/process/submitting-patches.rst — Patch submission
Documentation/process/coding-style.rst    — Kernel code style
```

### Books
| Title | Author | Why Read It |
|-------|--------|-------------|
| **Linux Kernel Development** (3rd ed.) | Robert Love | Best intro to kernel internals overall |
| **Understanding Linux Network Internals** | Christian Benvenuti | Deep dive on sk_buff, NAPI, routing |
| **Linux Kernel Networking** | Rami Rosen | Modern net stack (covers namespaces, tc) |
| **Linux Device Drivers** (3rd ed., free) | Corbet, Rubini, Kroah-Hartman | Module writing fundamentals |
| **BPF Performance Tools** | Brendan Gregg | bpftrace, BCC, perf-everything |
| **Systems Performance** (2nd ed.) | Brendan Gregg | Profiling methodology |

---

## Tier 2: Essential Blogs + Papers

### eBPF-Specific
| Source | URL | Focus |
|--------|-----|-------|
| Andrii Nakryiko's blog | nakryiko.com | libbpf, CO-RE internals |
| Brendan Gregg's blog | brendangregg.com/blog | BPF tracing, profiling |
| Cilium blog | cilium.io/blog | Production eBPF use cases |
| LWN.net kernel coverage | lwn.net | Every major kernel change explained |
| eBPF.io | ebpf.io | Curated eBPF learning resources |

### Networking-Specific
| Source | URL | Focus |
|--------|-----|-------|
| PackageCloud blog | blog.packagecloud.io | TCP/UDP Linux internals (deep) |
| Cloudflare blog | blog.cloudflare.com | XDP, DDoS mitigation at scale |
| Facebook/Meta networking | engineering.fb.com | Katran LB, XDP production |

### Papers
- "The eXpress Data Path" (Høiland-Jørgensen et al., 2018) — original XDP paper
- "BPF: A New Type of Software" (Starovoitov, 2021) — BPF design philosophy
- "Cilium: BPF & XDP for Containers" (Borkmann, 2016)

---

## Tier 3: GitHub Repositories (Study These Codebases)

### Must-Read Repos
```
torvalds/linux                  — THE kernel (read net/core/, kernel/bpf/)
libbpf/libbpf                   — Canonical C BPF library
aya-rs/aya                      — Rust BPF framework
libbpf/bpftool                  — Essential debugging tool
xdp-project/xdp-tools           — xdp-bench, xdppass, xdpdump
iovisor/bcc                     — Python/Lua eBPF scripting
```

### Reference Implementations (Production Quality)
```
cilium/cilium                   — Kubernetes CNI using eBPF; read pkg/ebpf/
facebook/katran                 — XDP L4 load balancer
cloudflare/ebpf_exporter        — eBPF → Prometheus
aquasecurity/tracee             — Security tracing with eBPF
```

### Learning Repos
```
xdp-project/xdp-tutorial        — Step-by-step XDP labs (BEST starting point)
libbpf/libbpf-bootstrap         — Minimal libbpf project template
aya-rs/aya-template              — Minimal Aya project template
brendangregg/bpf-perf-tools-book — All examples from Gregg's book
```

---

## Tier 4: Kernel Mailing Lists + Patchwork

### Where to Watch
- https://lore.kernel.org/bpf/ — BPF patches (real professional code reviews)
- https://lore.kernel.org/netdev/ — Networking patches
- https://patchwork.kernel.org/project/netdevbpf/ — Patch tracking

### How to Read Kernel Code Reviews (Learning Exercise)
Pick any recent patch thread on lore.kernel.org/bpf/.
Read:
1. The patch itself
2. Maintainer's first review comment
3. Author's response
4. Final accepted version

This teaches you: what production-quality kernel code looks like,
what reviewers care about, and common mistakes to avoid.

---

## Tier 5: Standards and Specifications

| Spec | Relevance |
|------|-----------|
| RFC 791 (IPv4) | Know the header format cold |
| RFC 793 (TCP) | TCP state machine, options |
| RFC 8200 (IPv6) | Extension headers |
| IEEE 802.3 | Ethernet frame format |
| BTF spec (kernel docs) | Required for CO-RE |
| BPF ISA spec | `Documentation/bpf/instruction-set.rst` |

---

## Essential man pages
```bash
man bpf          # bpf() syscall — read every word
man bpf-helpers  # all available BPF helper functions
man tc-bpf       # TC BPF attachment
man ip-link      # XDP attachment via ip
man bpftool-prog
man bpftool-map
man bpftool-net
```

---

## Kernel Commit Log Research Technique

When you don't understand WHY something was written a certain way:
```bash
# In the kernel tree:
git log --all --oneline --follow -p net/core/filter.c | less

# Search for commits related to a specific function:
git log --all --grep="xdp_do_filter" --oneline

# Find when a specific line was added:
git blame net/core/filter.c

# Find when a specific structure field was added:
git log --all -S "xdp_rxq_info" --oneline
```

This practice — reading git history alongside code — is how expert
kernel developers build deep understanding. Every non-obvious line
has a commit explaining the "why".