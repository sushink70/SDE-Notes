### Summary
eBPF (extended Berkeley Packet Filter) is a powerful in-kernel virtual machine technology in Linux, enabling safe, efficient execution of custom programs for networking, observability, security, and more without modifying kernel code. It's foundational for modern cloud-native infrastructure, powering projects in CNCF landscapes like Cilium for networking and Falco for runtime security. This list compiles all known open-source projects based on eBPF from curated sources, deduplicated across ecosystems (e.g., ebpf.io, awesome-ebpf, LibHunt), focusing on production-grade ones relevant to your security-first, systems engineering background. Projects span core infrastructure (runtimes, compilers), libraries, and applications in networking, observability, security, and tooling. Total unique projects: ~100; categorized for clarity with brief descriptions, emphasizing security implications where applicable. Prioritize CO-RE (Compile Once Run Everywhere) designs for reproducibility across multi-cloud/hybrid envs. Assumptions: List is exhaustive as of Jan 2026 based on public sources; may miss proprietary or emerging ones—verify with provided commands.

### Comprehensive List of eBPF-Based Projects
Use this table for quick reference; projects are categorized by primary use case (some overlap). Focus on those with security integrations (e.g., LSM hooks) for your cloud/data-center work. Stars indicate popularity from sources like GitHub/LibHunt (approximate as of search).

| Category | Project Name | Brief Description | Security Relevance | Stars (Approx.) | Key Links/Repos |
|----------|--------------|-------------------|--------------------|-----------------|-----------------|
| **Core Infrastructure** | Linux Kernel | eBPF runtime for program execution, verification, JIT compilation. | Kernel-level isolation; verifier prevents unsafe code. | N/A | [kernel.org](https://kernel.org)  |
| **Core Infrastructure** | LLVM Compiler | Backend for compiling C-like code to eBPF ELF files with BTF metadata. | Ensures safe bytecode generation. | N/A | [llvm.org](https://llvm.org)  |
| **Core Infrastructure** | GCC Compiler | eBPF backend (from GCC 10) for ELF files, binutils, GDB support. | Alternative compiler with simulation for debugging. | N/A | [gcc.gnu.org](https://gcc.gnu.org)  |
| **Core Infrastructure** | bpftool | CLI for inspecting/managing eBPF objects (programs, maps). | Audit eBPF deployments securely. | N/A | [github.com/libbpf/bpftool](https://github.com/libbpf/bpftool)  |
| **Core Infrastructure** | eBPF for Windows | Port for running eBPF on Windows with existing toolchains. | Cross-platform security auditing. | N/A | [github.com/microsoft/ebpf-for-windows](https://github.com/microsoft/ebpf-for-windows)  |
| **Core Infrastructure** | uBPF | User-space eBPF runtime with interpreter/JIT (x86-64, ARM64). | Safe user-mode testing. | N/A | [github.com/iovisor/ubpf](https://github.com/iovisor/ubpf)  |
| **Core Infrastructure** | rbpf | Rust-based user-space eBPF interpreter/JIT. | Rust safety for cross-platform. | N/A | N/A  |
| **Core Infrastructure** | hBPF | Hardware eBPF CPU on FPGA using Migen/LiteX. | Hardware-accelerated secure filtering. | N/A | N/A  |
| **Core Infrastructure** | PREVAIL | Polynomial-time verifier with loop support. | Formal verification for safety. | N/A | [github.com/vbpf/ebpf-verifier](https://github.com/vbpf/ebpf-verifier)  |
| **Core Infrastructure** | bpftime | User-space runtime for unprivileged eBPF with JIT/interpreter. | Reduces kernel privilege needs. | N/A | N/A  |
| **Core Infrastructure** | BPF Conformance | Testing framework for eBPF runtime compliance. | Ensures spec adherence for prod. | N/A | [github.com/Alan-Jowett/bpf_conformance](https://github.com/Alan-Jowett/bpf_conformance)  |
| **Libraries** | libbpf | C/C++ library for loading/processing eBPF ELF files (CO-RE support). | Production-grade loader with globals/skeletons. | N/A | [github.com/libbpf/libbpf](https://github.com/libbpf/libbpf)  |
| **Libraries** | cilium/ebpf (Golang) | Pure Go library for eBPF program management. | Go-based for control planes. | 7,453 | [github.com/cilium/ebpf](https://github.com/cilium/ebpf)  |
| **Libraries** | libbpfgo | Go wrapper around libbpf for CO-RE. | Full libbpf API in Go. | N/A | [github.com/aquasecurity/libbpfgo](https://github.com/aquasecurity/libbpfgo)  |
| **Libraries** | aya | Rust library for eBPF with focus on DX/operability. | Rust safety for programs/userspace. | 4,181 | [github.com/aya-rs/aya](https://github.com/aya-rs/aya)  |
| **Libraries** | libbpf-rs | Rust wrapper for libbpf with CO-RE. | Idiomatic Rust API. | N/A | [github.com/libbpf/libbpf-rs](https://github.com/libbpf/libbpf-rs)  |
| **Libraries** | libxdp | XDP helpers on top of libbpf (multi-program, AF_XDP). | Efficient packet handling. | N/A | [github.com/xdp-project/xdp-tools](https://github.com/xdp-project/xdp-tools)  |
| **Libraries** | PcapPlusPlus | C++ packet capture/parsing with AF_XDP support. | Network security analysis. | N/A | N/A  |
| **Libraries** | gobpf | Go bindings for BCC. | Legacy Go support. | N/A | N/A  |
| **Libraries** | Ebpfguard | Rust for Linux security policies. | MAC policies. | N/A | N/A  |
| **Libraries** | zbpf | Zig framework for eBPF. | Cross-platform Zig. | N/A | N/A  |
| **Libraries** | eunomia-bpf | Framework for CO-RE in multiple langs/WASM. | Portable eBPF. | N/A | N/A  |
| **Libraries** | oxidebpf | Rust library for security-focused eBPF. | Stability emphasis. | N/A | N/A  |
| **Networking** | Cilium | eBPF/XDP for container networking/security/observability (CNCF). | Policy enforcement, encryption. | 23,252 | [cilium.io](https://cilium.io)  |
| **Networking** | Calico | eBPF dataplane for Kubernetes networking/security. | Low-latency policies. | 6,989 | [projectcalico.org](https://projectcalico.org)  |
| **Networking** | Katran | XDP-based L4 load balancer. | High-perf DDoS mitigation. | N/A | [github.com/facebookincubator/katran](https://github.com/facebookincubator/katran)  |
| **Networking** | LoxiLB | eBPF load balancer for 5G/edge. | Cloud-native LB. | N/A | N/A  |
| **Networking** | merbridge | eBPF for accelerating service mesh. | Replaces iptables for security. | N/A | N/A  |
| **Networking** | dae | High-perf transparent proxy. | Traffic control. | 5,021 | N/A  |
| **Networking** | kyanos | eBPF network analysis CLI. | Request capture for debugging. | 4,951 | N/A  |
| **Networking** | pwru | Kernel network packet tracer. | Debugging packet drops. | 3,642 | N/A  |
| **Networking** | Retina | Distributed networking observability for K8s. | Flow monitoring. | N/A | N/A  |
| **Networking** | netobserv | Flow-based observability. | Network security insights. | N/A | N/A  |
| **Networking** | vc5 | L4 load balancer. | Simple LB. | N/A | N/A  |
| **Networking** | bpfilter | Packet filtering framework. | Firewall-like. | N/A | N/A  |
| **Networking** | ingress-node-firewall | Stateless node firewall. | Ingress protection. | N/A | N/A  |
| **Networking** | upf-bpf | XDP for 5G UPF. | Telecom security. | N/A | N/A  |
| **Networking** | ipx_wrap | PoC IPX implementation. | Legacy protocol support. | N/A | N/A  |
| **Networking** | ApFree WiFiDog | Captive portal with DPI. | User authentication. | N/A | N/A  |
| **Networking** | qtap | Encryption visibility. | TLS inspection. | N/A | N/A  |
| **Networking** | EBPFCat | EtherCAT master/code gen. | Industrial networking. | N/A | N/A  |
| **Observability** | bcc | Toolkit for kernel tracing. | Low-level monitoring. | N/A | [github.com/iovisor/bcc](https://github.com/iovisor/bcc)  |
| **Observability** | bpftrace | High-level tracing language. | Dynamic tracing. | 9,869 | [github.com/bpftrace/bpftrace](https://github.com/bpftrace/bpftrace)  |
| **Observability** | Pixie | K8s observability with protocol tracing. | Zero-instrument. | 6,313 | [px.dev](https://px.dev)  |
| **Observability** | Parca | Continuous profiling. | CPU/memory analysis. | 4,727 | [parca.dev](https://parca.dev)  |
| **Observability** | Hubble | K8s network/security observability. | Flow visibility. | 4,041 | N/A  |
| **Observability** | DeepFlow | Automated observability platform. | AI/cloud-native. | N/A | N/A  |
| **Observability** | coroot | AI-powered APM/observability. | Root cause analysis. | 7,328 | N/A  |
| **Observability** | Odigos | Zero-code distributed tracing. | OpenTelemetry integration. | 3,606 | N/A  |
| **Observability** | Caretta | K8s service map. | Dependency visualization. | N/A | N/A  |
| **Observability** | OpenTelemetry eBPF Profiler | Whole-system profiler. | Cross-lang profiling. | N/A | N/A  |
| **Observability** | Pyroscope | Continuous profiling (merged into Parca). | Performance monitoring. | N/A | N/A  |
| **Observability** | Kindling | Cloud-native monitoring/profiling. | Multi-metric. | N/A | N/A  |
| **Observability** | Alaz | Low-overhead K8s monitoring. | Effortless setup. | N/A | N/A  |
| **Observability** | KubeSkoop | Network monitoring/diagnosis for K8s. | Fault isolation. | N/A | N/A  |
| **Observability** | wachy | UI for eBPF performance debugging. | Interactive traces. | N/A | N/A  |
| **Observability** | Trayce | Network tab for Docker. | Container flows. | N/A | N/A  |
| **Observability** | Kepler | Power level exporter for K8s. | Energy efficiency. | N/A | N/A  |
| **Observability** | kflow | Process monitoring on endpoints. | Endpoint security. | N/A | N/A  |
| **Observability** | Apache SkyWalking | APM system with eBPF profiler. | Multi-lang monitoring. | 24,688 | [skywalking.apache.org](https://skywalking.apache.org)  |
| **Observability** | Beyla | Zero-code instrumentation with OTEL. | Auto-instrument. | N/A | N/A  |
| **Observability** | rbperf | Ruby sampler/tracer. | Lang-specific. | N/A | N/A  |
| **Observability** | oster | Go tracing via uprobes. | Go app monitoring. | N/A | N/A  |
| **Security** | Falco | Cloud-native runtime security (CNCF). | Threat detection rules. | 8,561 | [falco.org](https://falco.org)  |
| **Security** | Tetragon | Security observability/enforcement. | Runtime policies. | 4,356 | [cilium.io/tetragon](https://cilium.io/tetragon)  |
| **Security** | Tracee | Runtime security/forensics. | Behavioral detection. | 4,329 | [aquasecurity.github.io/tracee](https://aquasecurity.github.io/tracee)  |
| **Security** | KubeArmor | Container runtime security enforcement. | LSM-based policies. | N/A | N/A  |
| **Security** | Kubescape | K8s security from dev to runtime. | Compliance scanning. | N/A | N/A  |
| **Security** | Sysinternals Sysmon for Linux | Security observability. | Event logging. | N/A | N/A  |
| **Security** | Pulsar | Modular IoT runtime security. | Device protection. | N/A | N/A  |
| **Security** | bpflock | Locking/auditing for Linux. | Machine hardening. | N/A | N/A  |
| **Security** | redcanary-ebpf-sensor | Security event data collection. | Endpoint detection. | N/A | N/A  |
| **Security** | harpoon | Syscall tracing from userspace. | Function hooking. | N/A | N/A  |
| **Security** | Synapse | XDR with eBPF firewall/proxy. | Server protection. | N/A | N/A  |
| **Security** | BPFJailer | Process jailing with MAC. | Sandboxing. | N/A | N/A  |
| **Security** | Bombini | eBPF security monitoring agent (Aya-based). | Malicious activity detection. | N/A | [github.com/anfedotoff/bombini](https://github.com/anfedotoff/bombini)  |
| **Security** | lockc | LSM-based MAC for containers. | Audit/enforce policies. | N/A | [github.com/rancher-sandbox/lockc](https://github.com/rancher-sandbox/lockc)  |
| **Security** | kunai | Threat hunting/monitoring. | Event generation for IR. | N/A | [github.com/kunai-project/kunai](https://github.com/kunai-project/kunai)  |
| **Security** | Red Canary Linux Agent | Security monitoring. | EDR-like. | N/A | N/A  |
| **Security** | BPFire | Firewall with eBPF addons. | Packet filtering. | N/A | N/A  |
| **Security** | eCapture | SSL/TLS capture without CA. | Traffic inspection. | 14,924 | N/A  |
| **Tooling/Scheduling** | iproute2 | Network mgmt with tc/ip for eBPF/XDP. | Base for attachments. | N/A | N/A  |
| **Tooling/Scheduling** | libbpf-bootstrap | Scaffolding for CO-RE apps. | Dev setup. | N/A | N/A  |
| **Tooling/Scheduling** | aya-template | Templates for Aya BPF apps. | Rust dev. | N/A | N/A  |
| **Tooling/Scheduling** | bpf_asm | Minimal cBPF assembler. | Legacy BPF. | N/A | N/A  |
| **Tooling/Scheduling** | bpf_dbg | cBPF debugger. | Debugging. | N/A | N/A  |
| **Tooling/Scheduling** | bpf_jit_disasm | BPF disassembler. | Inspection. | N/A | N/A  |
| **Tooling/Scheduling** | generic-ebpf | Cross-platform user-space. | Testing. | N/A | N/A  |
| **Tooling/Scheduling** | xdp-vagrant | Vagrant for XDP testing. | Env setup. | N/A | N/A  |
| **Tooling/Scheduling** | ply | Dynamic Linux tracer. | Simple scripting. | N/A | N/A  |
| **Tooling/Scheduling** | kubectl trace | bpftrace on K8s. | Cluster tracing. | N/A | N/A  |
| **Tooling/Scheduling** | Inspektor Gadget | K8s/Linux data collection gadgets. | Debugging. | N/A | N/A  |
| **Tooling/Scheduling** | bpfd | Daemon for BPF programs (container-aware). | Management. | N/A | N/A  |
| **Tooling/Scheduling** | BPFd | Tracer for Android. | Mobile debugging. | N/A | N/A  |
| **Tooling/Scheduling** | adeb | Android tracing shell. | Mobile env. | N/A | N/A  |
| **Tooling/Scheduling** | greggd | Daemon for eBPF compile/load. | Metrics forwarding. | N/A | N/A  |
| **Tooling/Scheduling** | redbpf | Rust eBPF framework. | Rust tooling. | N/A | N/A  |
| **Tooling/Scheduling** | ebpf-explorer | Web UI for eBPF maps/programs. | Inspection. | N/A | N/A  |
| **Tooling/Scheduling** | ebpfmon | TUI for eBPF monitoring. | Real-time stats. | N/A | N/A  |
| **Tooling/Scheduling** | bpfman | Manager/operator for eBPF (OCI images). | K8s integration. | N/A | N/A  |
| **Tooling/Scheduling** | ptcpdump | Process-aware tcpdump. | Advanced capture. | N/A | N/A  |
| **Tooling/Scheduling** | oryx | TUI for network sniffing. | Traffic analysis. | N/A | N/A  |
| **Tooling/Scheduling** | bpftop | Real-time eBPF stats. | Performance monitoring. | N/A | N/A  |
| **Tooling/Scheduling** | BumbleBee | OCI-compliant eBPF tooling. | Containerized. | N/A | N/A  |
| **Tooling/Scheduling** | L3AF | Lifecycle mgmt for eBPF programs. | Orchestration. | N/A | N/A  |
| **Tooling/Scheduling** | scx | Sched_ext schedulers. | Custom scheduling. | N/A | N/A  |
| **Tooling/Scheduling** | Gthulhu | Scheduler for cloud-native. | Workload optimization. | N/A | N/A  |
| **Tooling/Scheduling** | blixt | K8s Gateway L4 LB (Aya-based). | Ingress LB. | N/A | [github.com/kubernetes-sigs/blixt](https://github.com/kubernetes-sigs/blixt)  |
| **Other/Misc** | kubesphere | K8s platform with eBPF components. | Multi-cloud mgmt. | 16,802 | N/A  |
| **Other/Misc** | keploy | API testing with eBPF. | Test generation. | 14,981 | N/A  |
| **Other/Misc** | ntopng | Web-based traffic/security monitoring. | Network forensics. | 7,422 | N/A  |
| **Other/Misc** | awesome-ebpf | Curated list (meta). | Resource aggregation. | 4,886 | [github.com/zoidyzoidzoid/awesome-ebpf](https://github.com/zoidyzoidzoid/awesome-ebpf)  |
| **Other/Misc** | bpf-developer-tutorial | Learning eBPF with examples. | Education. | 3,864 | N/A  |
| **Other/Misc** | Open vSwitch (OvS) | eBPF for flow offloading. | Virtualization. | N/A | [openvswitch.org](https://openvswitch.org)  |

### Actionable Steps
To explore eBPF projects hands-on, focus on reproducible setups in your preferred langs (Go/Rust/C++). Here's a production-grade workflow for Cilium (networking/security exemplar) on a K8s cluster—assumes Ubuntu/Debian host with kernel >=5.4 for eBPF support.

1. **Verify Kernel Support**: Run `uname -r` to check kernel version; if <5.4, upgrade via `sudo apt update && sudo apt install linux-generic-hwe-22.04`. Confirm eBPF features: `sysctl kernel.bpf_stats_enabled` (should be 1; set with `sudo sysctl -w kernel.bpf_stats_enabled=1`).

2. **Install Dependencies**: `sudo apt install -y golang-go rustc cargo clang llvm libelf-dev zlib1g-dev libbpf-dev`. For Rust/Aya: `cargo install bpf-linker`.

3. **Build/Run Cilium (Go-based)**: Clone repo `git clone https://github.com/cilium/cilium.git && cd cilium`. Build: `make build`. Test locally: `./cilium install --kube-proxy-replacement=strict` (in minikube). Config (minimal security-first): Edit `cilium.yaml` with `securityContext: privileged: false` for least-priv. Run: `kubectl apply -f cilium.yaml`. Verify: `cilium status`.

4. **Code Snippet for Custom eBPF Probe (Rust/Aya)**: For a simple kprobe tracing syscalls (security audit).
   ```rust
   // Cargo.toml: [dependencies] aya = "0.11"
   use aya::{programs::KProbe, Bpf};
   fn main() -> Result<(), anyhow::Error> {
       let mut bpf = Bpf::load_file("probe.ebpf.o")?;
       let prog: &mut KProbe = bpf.program_mut("my_probe")?.try_into()?;
       prog.load()?;
       prog.attach("sys_execve", 0)?;
       println!("Attached kprobe");
       loop { std::thread::sleep(std::time::Duration::from_secs(1)); }
   }
   ```
   Build: `cargo build --release`. eBPF code (in src/probe.bpf.c): Use clang to compile to .o. Run: `sudo target/release/my_probe`. Test: Execute a binary and check dmesg for traces.

Alternatives: For pure C, use libbpf-bootstrap; failure mode: If attach fails (e.g., CAP_SYS_ADMIN missing), fallback to `sudo setcap cap_sys_admin+ep binary`.

### Architecture View (ASCII)
eBPF ecosystem in cloud/security context—user/kernel boundaries for isolation.

```
+-------------------+     +-------------------+     +-------------------+
| User Space Apps   |     | Libraries/Tools   |     | Projects (Apps)   |
| (Go/Rust/C++/Py)  |<--->| libbpf/aya/bcc    |<--->| Cilium/Falco/etc. |
+-------------------+     +-------------------+     +-------------------+
          |                           |                       ^
          v                           v                       |
+--------------------+   +-------------------+   +-------------------+
| Kernel Attachments |   | eBPF VM/Verifier  |   | Maps/Programs     |
| (kprobe/XDP/LSM)   |<->| JIT/Interpreter   |<->| (Ringbuf/Hash)    |
+--------------------+   +-------------------+   +-------------------+
          ^                           ^
          |                           |
+-------------------+     +-------------------+
| Hardware/VM        |     | Network/Storage  |
| (FPGA/CPU)         |     | (XDP/TC)         |
+-------------------+     +-------------------+
```
- User space loads programs via syscalls; verifier ensures no crashes/loops.
- Security: LSM for MAC, XDP for early packet drop.

### Threat Model + Mitigation
**Threats**: 1) Malicious eBPF code bypassing verifier (e.g., JIT bugs)—mitigate with PREVAIL verifier or kernel hardening (`kernel.unprivileged_bpf_disabled=1`). 2) Privilege escalation via CAP_BPF—run in namespaces, use seccomp to restrict. 3) DoS from inefficient programs—limit maps/programs via rlimits (`ulimit -m`). 4) Side-channel leaks in shared maps—use per-cpu maps, encrypt sensitive data. Alternatives: User-space runtimes (uBPF) for testing; failure: Verifier reject—debug with `bpftool prog dump jited id <id>`.

Defense-in-depth: Combine with SELinux/AppArmor for boundaries; identity via mTLS in Cilium.

### Tests/Fuzzing/Bench Steps
1. **Unit Tests**: For custom code, use aya's test framework: `cargo test`.
2. **Fuzzing**: Use syzkaller with eBPF focus: `git clone https://github.com/google/syzkaller && make; ./bin/syz-manager -config mycfg.json` (enable bpf in config).
3. **Bench**: Benchmark probe overhead: `bpftool prog run <prog> data_in /dev/zero data_out /dev/null repeat 1000000`; compare with `perf stat`.
Verify: If unsure about overhead, run `bpftool feature probe` for system capabilities.

### Roll-out/Rollback Plan
1. **Roll-out**: Start in staging K8s namespace; deploy via Helm (e.g., `helm install cilium cilium/cilium --namespace kube-system`). Monitor with `cilium monitor`. Scale: Use DaemonSet for node coverage.
2. **Rollback**: Pin versions (`helm rollback cilium 1`); unload programs: `bpftool prog list | grep my_prog | awk '{print $1}' | xargs -I{} bpftool prog unload {}`. Fallback to iptables-based (e.g., kube-proxy).
Failure mode: If kernel panic (rare, post-verifier), reboot with older kernel via GRUB.

### References
- ebpf.io/applications & infrastructure  
- awesome-ebpf GitHub  
- awesome-aya GitHub 
- LibHunt eBPF topic 
- CNCF Landscape: https://landscape.cncf.io/?category=security-compliance,observability-monitoring (filter eBPF).

### Next 3 Steps
1. Pick a project (e.g., Cilium): Set up minikube (`minikube start --network-plugin=cni`) and install as above; test network policy: `kubectl apply -f policy.yaml` with deny-all.
2. Build a custom probe: Use the Rust snippet; attach to a VM/hypervisor syscall for virtualization security insights—run and log outputs.
3. Verify completeness: Run `git clone https://github.com/zoidyzoidzoid/awesome-ebpf && grep -r "project" .` to cross-check list; if missing, search CNCF repos with `gh search repos ebpf --owner cncf`.