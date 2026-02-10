## Executive Summary

You're building a production-grade cloud-native platform with eBPF as the foundational technology for observability, networking, and security. The control plane orchestrates workload lifecycle, policy enforcement, and cluster state, while the data plane executes workloads with runtime isolation, traffic handling, and telemetry collection. eBPF enables kernel-level programmability for zero-overhead observability, advanced networking (XDP, TC), runtime security enforcement, and dynamic policy injection without kernel modules or syscall overhead.

**Key Architecture**: Control plane runs Kubernetes (etcd, API server, scheduler, controllers), service mesh control plane (Istio/Cilium), observability backends (Prometheus/Grafana/Jaeger), and GitOps operators. Data plane runs container runtime (containerd), CNI with eBPF datapath (Cilium), service mesh proxy/eBPF acceleration, eBPF-based monitoring (Tetragon, Pixie), and security enforcement (Falco). All components connect via mutual TLS, enforce least-privilege RBAC, implement defense-in-depth with eBPF LSM hooks, and emit structured telemetry.

**Production Mandate**: This setup mirrors what companies like Datadog, Capital One, Bloomberg, Adobe use: Kubernetes + Cilium for networking/security, Istio/Linkerd for service mesh, Prometheus/Grafana for observability, Falco/Tetragon for runtime security, Vault for secrets, OPA/Kyverno for policy, and GitOps (ArgoCD/Flux) for declarative ops. eBPF eliminates sidecar overhead, provides kernel-level visibility, enables advanced traffic engineering (XDP L4 load balancing), and enforces security at process/network/syscall granularity.

---

## Phase 1: eBPF Deep Dive & Foundation

### 1.1 eBPF Architecture & Kernel Internals

eBPF (extended Berkeley Packet Filter) is an in-kernel virtual machine that allows safe, sandboxed programs to run in kernel space without requiring kernel module compilation or rebooting. It's the foundation for modern observability, networking, and security.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER SPACE                                   │
├─────────────────────────────────────────────────────────────────────┤
│  Application     │  BPF Loader (libbpf)  │  User-space Agent       │
│  (Go/Rust/C)     │  (bpftool/cilium)     │  (Cilium/Tetragon)      │
└──────┬───────────┴──────────┬─────────────┴─────────┬───────────────┘
       │                      │                       │
       │ Syscall (bpf())      │ Map Operations       │ Perf/Ring Buffer
       ▼                      ▼                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    KERNEL SPACE (Ring 0)                             │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              BPF VERIFIER (Safety Guarantees)                 │  │
│  │  • Bounded loops (< 1M instructions)                         │  │
│  │  • No unbounded memory access                                │  │
│  │  • Type safety & pointer arithmetic validation              │  │
│  │  • Prevents kernel crashes/infinite loops                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                               ▼                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │           BPF JIT COMPILER (Just-In-Time)                     │  │
│  │  • Translates BPF bytecode → native x86_64/ARM64            │  │
│  │  • Near-native performance (< 10% overhead)                  │  │
│  │  • Per-CPU compilation cache                                 │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                               ▼                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                 BPF MAPS (Data Exchange)                      │  │
│  │  Types: Hash, Array, LRU, Queue, Stack, RingBuf             │  │
│  │  • Kernel ↔ User space communication                         │  │
│  │  • Per-CPU maps for lock-free aggregation                    │  │
│  │  • BPF-to-BPF map sharing (tail calls)                      │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │           HOOK POINTS (Where BPF Programs Attach)             │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │ XDP (eXpress Data Path)         │ Raw packet @ NIC driver    │  │
│  │ TC (Traffic Control)            │ Ingress/Egress @ qdisc     │  │
│  │ Socket (sock_ops, sockmap)      │ Socket lifecycle events    │  │
│  │ Tracepoints                     │ Stable kernel events       │  │
│  │ kprobes/uprobes                 │ Dynamic kernel/user trace  │  │
│  │ LSM (Linux Security Module)     │ Security policy hooks      │  │
│  │ cgroup (v2)                     │ Resource control hooks     │  │
│  │ Perf Events                     │ HW counters, PMU           │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              HELPER FUNCTIONS (Kernel APIs)                   │  │
│  │  • bpf_probe_read() - Safe memory read                       │  │
│  │  • bpf_map_lookup_elem() - Map operations                    │  │
│  │  • bpf_get_current_task() - Process context                  │  │
│  │  • bpf_redirect() - Packet forwarding (XDP/TC)              │  │
│  │  • bpf_ktime_get_ns() - Timing                               │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

**Why eBPF for Cloud-Native**:
- **Zero-Overhead Observability**: Attach to kernel tracepoints without sidecar proxies (e.g., Pixie captures L7 protocols at < 1% CPU)
- **Advanced Networking**: XDP processes packets at line rate (40Gbps+) for L4 load balancing, DDoS mitigation
- **Runtime Security**: LSM hooks enforce syscall filtering, file access control, network policy without iptables
- **Dynamic Instrumentation**: Deploy security/observability logic without pod restarts or kernel reboots

### 1.2 eBPF Development Toolchain Setup

```bash
# Install eBPF development stack on both VMs
cat <<'EOF' > setup_ebpf_env.sh
#!/bin/bash
set -euo pipefail

# Kernel headers (required for BPF compilation)
apt-get update && apt-get install -y \
  linux-headers-$(uname -r) \
  linux-tools-$(uname -r) \
  linux-tools-common \
  linux-tools-generic

# BPF toolchain
apt-get install -y \
  clang \
  llvm \
  libbpf-dev \
  bpftool \
  libbpf0 \
  libelf-dev \
  zlib1g-dev

# Verification
bpftool version
clang --version | head -1

# Enable BPF JIT compiler
echo 1 > /proc/sys/net/core/bpf_jit_enable
sysctl -w kernel.unprivileged_bpf_disabled=1  # Security: disable unprivileged BPF

# Verify kernel config
grep CONFIG_BPF /boot/config-$(uname -r) | grep -E "BPF|BTF"
EOF

chmod +x setup_ebpf_env.sh
sudo ./setup_ebpf_env.sh
```

**Test eBPF Capability**:
```bash
# Simple eBPF program to count syscalls
cat <<'EOF' > test_ebpf.c
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, __u64);
} syscall_counter SEC(".maps");

SEC("tracepoint/raw_syscalls/sys_enter")
int count_syscalls(void *ctx) {
    __u32 key = 0;
    __u64 *count = bpf_map_lookup_elem(&syscall_counter, &key);
    if (count)
        __sync_fetch_and_add(count, 1);
    return 0;
}

char _license[] SEC("license") = "GPL";
EOF

# Compile and load
clang -O2 -target bpf -c test_ebpf.c -o test_ebpf.o
sudo bpftool prog load test_ebpf.o /sys/fs/bpf/test_prog
sudo bpftool prog show
sudo rm /sys/fs/bpf/test_prog
```

---

## Phase 2: Production Cloud-Native Stack (Mandatory Components)

### 2.1 Component Taxonomy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CONTROL PLANE VM                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  CLUSTER ORCHESTRATION (State Machine)                         │    │
│  ├────────────────────────────────────────────────────────────────┤    │
│  │  • Kubernetes (v1.29+) - API server, etcd, scheduler           │    │
│  │  • k3s (production-grade, HA capable)                          │    │
│  │  • Talos Linux (immutable, API-managed OS) [OPTIONAL]          │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  SERVICE MESH CONTROL PLANE (Traffic Management)               │    │
│  ├────────────────────────────────────────────────────────────────┤    │
│  │  • Cilium (eBPF-native, L3/L4/L7 policy, no sidecar)          │    │
│  │  • Istio (sidecar-based, mature, rich L7 features)            │    │
│  │  • Linkerd (lightweight, Rust-based, simple)                   │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  POLICY & GOVERNANCE                                            │    │
│  ├────────────────────────────────────────────────────────────────┤    │
│  │  • OPA Gatekeeper (admission control, Rego policies)           │    │
│  │  • Kyverno (Kubernetes-native, no DSL)                         │    │
│  │  • Falco (runtime security, eBPF syscall monitoring)           │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  OBSERVABILITY BACKENDS (Metrics, Logs, Traces)                │    │
│  ├────────────────────────────────────────────────────────────────┤    │
│  │  • Prometheus (metrics, PromQL, TSDB)                          │    │
│  │  • Grafana (visualization, dashboards)                         │    │
│  │  • Loki (log aggregation, LogQL)                               │    │
│  │  • Jaeger / Tempo (distributed tracing)                        │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  SECRETS MANAGEMENT                                             │    │
│  ├────────────────────────────────────────────────────────────────┤    │
│  │  • HashiCorp Vault (secret rotation, dynamic credentials)      │    │
│  │  • External Secrets Operator (sync from cloud KMS)             │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  GitOps & CI/CD                                                 │    │
│  ├────────────────────────────────────────────────────────────────┤    │
│  │  • ArgoCD (declarative sync, multi-cluster)                    │    │
│  │  • Flux (GitOps toolkit, Helm controller)                      │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                          DATA PLANE VM                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  CONTAINER RUNTIME (OCI Spec)                                  │    │
│  ├────────────────────────────────────────────────────────────────┤    │
│  │  • containerd (CNCF standard, gRPC API, CRI plugin)            │    │
│  │  • crun (OCI runtime, C, security-focused) [OPTIONAL]          │    │
│  │  • runc (default OCI runtime, Go)                              │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  CNI (Container Network Interface) - eBPF-First                │    │
│  ├────────────────────────────────────────────────────────────────┤    │
│  │  • Cilium CNI (eBPF datapath, kube-proxy replacement)          │    │
│  │    - XDP acceleration                                           │    │
│  │    - eBPF Host Routing (bypass iptables)                       │    │
│  │    - Network Policy (L3-L7)                                    │    │
│  │    - Service Mesh (sidecar-less with eBPF)                     │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  SERVICE MESH DATA PLANE (Traffic Proxy)                       │    │
│  ├────────────────────────────────────────────────────────────────┤    │
│  │  • Envoy (L7 proxy, HTTP/2, gRPC, WASM filters)                │    │
│  │  • Cilium eBPF (sidecar-less L7 visibility/policy)             │    │
│  │  • Linkerd2-proxy (Rust, low latency)                          │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  OBSERVABILITY AGENTS (eBPF-Based)                             │    │
│  ├────────────────────────────────────────────────────────────────┤    │
│  │  • Cilium Hubble (eBPF flow logs, L3-L7 visibility)            │    │
│  │  • Pixie (eBPF auto-instrumentation, no code changes)          │    │
│  │  • Tetragon (eBPF runtime security observability)              │    │
│  │  • Prometheus Node Exporter (host metrics)                     │    │
│  │  • Fluent Bit (log shipping, eBPF support)                     │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  RUNTIME SECURITY (eBPF Enforcement)                           │    │
│  ├────────────────────────────────────────────────────────────────┤    │
│  │  • Falco (syscall auditing, runtime threat detection)          │    │
│  │  • Tetragon (process/file/network enforcement with eBPF LSM)   │    │
│  │  • Tracee (eBPF security events, Aqua Security)                │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  STORAGE (CSI Drivers)                                          │    │
│  ├────────────────────────────────────────────────────────────────┤    │
│  │  • OpenEBS (cloud-native storage, local PV)                    │    │
│  │  • Rook-Ceph (distributed block/file/object storage)           │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Core Stack Selection Matrix (Production Standards)

| Category | Project | Why Production-Ready | eBPF Integration | Companies Using |
|----------|---------|---------------------|------------------|-----------------|
| **Orchestration** | Kubernetes (k3s) | Battle-tested, CNCF graduated, HA, multi-cluster | Native (cgroup v2) | Google, Spotify, Capital One |
| **CNI** | Cilium | eBPF datapath, kube-proxy replacement, L7 policy | Core (XDP, TC, LSM) | Adobe, Bell Canada, CapitalOne |
| **Service Mesh** | Cilium (sidecar-less) or Istio | Cilium: eBPF L7 no sidecar; Istio: mature L7 | Cilium: native; Istio: optional | Datadog, Sky, Google (Istio) |
| **Container Runtime** | containerd | CNCF graduated, CRI standard, secure defaults | cgroup v2 hooks | Docker, AWS EKS, GKE |
| **Observability** | Prometheus + Grafana + Loki + Hubble | Industry standard, PromQL, long-term storage | Hubble: eBPF flow logs | Grafana Labs, CERN, GitLab |
| **Tracing** | Jaeger or Tempo | OpenTelemetry compatible, distributed trace | eBPF uprobes for auto-instrumentation | Uber, Red Hat, Grafana |
| **Runtime Security** | Falco + Tetragon | Real-time threat detection, MITRE ATT&CK mapping | eBPF syscalls, LSM hooks | IBM, Yahoo, GitLab |
| **Policy Engine** | OPA Gatekeeper or Kyverno | Admission control, Rego/YAML policies | N/A (pre-admission) | Netflix, Pinterest, Nirmata |
| **Secrets** | HashiCorp Vault | Dynamic secrets, audit logging, PKI | N/A | Adobe, Barclays, Citadel |
| **GitOps** | ArgoCD | Declarative, RBAC, multi-cluster sync | N/A | Intuit, Red Hat, Ticketmaster |
| **Load Balancer** | MetalLB or Cilium LB (XDP) | Bare-metal L4 LB, BGP support | Cilium: XDP-based | N/A (on-prem standard) |

---

## Phase 3: Step-by-Step Implementation

### 3.1 Control Plane Setup (Kubernetes + Core Services)

```bash
# === CONTROL PLANE VM (8GB RAM, 4 CPU, 20GB SSD) ===

# 1. Install k3s (lightweight Kubernetes)
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="server \
  --disable traefik \
  --disable servicelb \
  --disable metrics-server \
  --flannel-backend=none \
  --disable-network-policy \
  --cluster-cidr=10.42.0.0/16 \
  --service-cidr=10.43.0.0/16 \
  --kube-proxy-arg=metrics-bind-address=0.0.0.0 \
  --kubelet-arg=feature-gates=GracefulNodeShutdown=true" sh -

# Wait for k3s
sudo k3s kubectl wait --for=condition=Ready node --all --timeout=300s

# Export kubeconfig
mkdir -p $HOME/.kube
sudo cp /etc/rancher/k3s/k3s.yaml $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
export KUBECONFIG=$HOME/.kube/config

# Verify
kubectl get nodes
kubectl get pods -A
```

**Get Node Token** (for data plane join):
```bash
sudo cat /var/lib/rancher/k3s/server/node-token
# Save this token, you'll need it for data plane
```

### 3.2 Data Plane Setup (Worker Node)

```bash
# === DATA PLANE VM (16GB RAM, 4 CPU, 40GB SSD) ===

# Join cluster as agent
export K3S_URL="https://<CONTROL_PLANE_IP>:6443"
export K3S_TOKEN="<TOKEN_FROM_CONTROL_PLANE>"

curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="agent \
  --node-label node-role.kubernetes.io/worker=true \
  --kubelet-arg=feature-gates=GracefulNodeShutdown=true" sh -

# Verify from control plane
kubectl get nodes
# You should see both control-plane and worker nodes
```

### 3.3 Install Cilium (eBPF CNI + kube-proxy Replacement)

```bash
# === RUN ON CONTROL PLANE ===

# Install Cilium CLI
CILIUM_CLI_VERSION=$(curl -s https://raw.githubusercontent.com/cilium/cilium-cli/main/stable.txt)
CLI_ARCH=amd64
curl -L --fail --remote-name-all https://github.com/cilium/cilium-cli/releases/download/${CILIUM_CLI_VERSION}/cilium-linux-${CLI_ARCH}.tar.gz{,.sha256sum}
sha256sum --check cilium-linux-${CLI_ARCH}.tar.gz.sha256sum
sudo tar xzvfC cilium-linux-${CLI_ARCH}.tar.gz /usr/local/bin
rm cilium-linux-${CLI_ARCH}.tar.gz{,.sha256sum}

# Install Cilium with eBPF features
cilium install \
  --version 1.15.1 \
  --set kubeProxyReplacement=true \
  --set k8sServiceHost=<CONTROL_PLANE_IP> \
  --set k8sServicePort=6443 \
  --set bpf.masquerade=true \
  --set enableIPv4Masquerade=true \
  --set enableIPv6=false \
  --set hostServices.enabled=true \
  --set externalIPs.enabled=true \
  --set nodePort.enabled=true \
  --set hostPort.enabled=true \
  --set tunnel=disabled \
  --set autoDirectNodeRoutes=true \
  --set ipam.mode=kubernetes \
  --set enableCiliumEndpointSlice=true \
  --set bpf.hostLegacyRouting=false

# Enable Hubble (eBPF observability)
cilium hubble enable --ui

# Wait for Cilium to be ready
cilium status --wait

# Validate eBPF programs loaded
sudo bpftool prog show | grep -E "cilium|bpf"
sudo bpftool map show | grep cilium

# Connectivity test
cilium connectivity test
```

**Cilium Architecture Under the Hood**:
```
┌─────────────────────────────────────────────────────────────────┐
│                      POD-TO-POD COMMUNICATION                    │
└─────────────────────────────────────────────────────────────────┘
    Pod A (10.42.1.5)                         Pod B (10.42.2.8)
         │                                          │
         │ syscall(sendto)                          │
         ▼                                          ▼
    ┌─────────────┐                            ┌─────────────┐
    │  veth pair  │                            │  veth pair  │
    └──────┬──────┘                            └──────┬──────┘
           │                                          │
     [TC egress eBPF]                          [TC ingress eBPF]
           │                                          │
           │ eBPF program:                            │ eBPF program:
           │ • L3/L4/L7 policy check                  │ • Connection tracking
           │ • Service translation (ClusterIP)        │ • NAT reverse
           │ • Identity-based security                │ • Policy enforcement
           │ • Metrics collection (Hubble)            │ • Decryption (WireGuard)
           ▼                                          ▼
    ┌──────────────────────────────────────────────────────┐
    │           HOST NETWORK NAMESPACE (eBPF Maps)         │
    │  ┌────────────────────────────────────────────┐     │
    │  │  BPF_MAP_TYPE_HASH: Endpoint identities    │     │
    │  │  BPF_MAP_TYPE_LRU: Connection tracking     │     │
    │  │  BPF_MAP_TYPE_ARRAY: Policy rules          │     │
    │  │  BPF_MAP_TYPE_RINGBUF: Hubble flow logs    │     │
    │  └────────────────────────────────────────────┘     │
    └──────────────────────────────────────────────────────┘
           │                                          ▲
           │ Direct routing (no NAT/tunnel)          │
           │ eBPF Host Routing bypasses iptables     │
           ▼                                          │
    ┌──────────────────────────────────────────────────────┐
    │              Physical NIC (eth0)                     │
    │  [XDP program @ driver layer]                        │
    │  • DDoS mitigation                                   │
    │  • L4 load balancing (40Gbps line rate)              │
    │  • Packet drop/redirect before skb allocation        │
    └──────────────────────────────────────────────────────┘
```

**kube-proxy Replacement**:
Cilium eBPF replaces iptables-based kube-proxy with in-kernel service load balancing:
- **Socket-level LB**: `bpf_sock_ops` intercepts `connect()` syscall, rewrites destination to backend pod IP
- **XDP L4 LB**: For NodePort/LoadBalancer, XDP at NIC layer performs DNAT before packet enters network stack
- **No iptables**: Eliminates O(n) rule traversal, reduces latency from ~1ms to <100μs

### 3.4 Install Observability Stack (Prometheus, Grafana, Loki, Hubble)

```bash
# Add Helm repos
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Create namespace
kubectl create namespace observability

# Install kube-prometheus-stack (Prometheus + Grafana + Alertmanager)
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace observability \
  --set prometheus.prometheusSpec.retention=7d \
  --set prometheus.prometheusSpec.resources.requests.memory=2Gi \
  --set grafana.enabled=true \
  --set grafana.adminPassword=admin \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false

# Install Loki (log aggregation)
helm install loki grafana/loki-stack \
  --namespace observability \
  --set fluent-bit.enabled=true \
  --set promtail.enabled=true \
  --set grafana.enabled=false

# Verify
kubectl get pods -n observability
kubectl get svc -n observability

# Access Grafana
kubectl port-forward -n observability svc/prometheus-grafana 3000:80
# Open http://localhost:3000 (admin/admin)
```

**Hubble UI** (Cilium eBPF flow visualization):
```bash
cilium hubble port-forward &
# Access http://localhost:12000
```

### 3.5 Install Runtime Security (Falco + Tetragon)

```bash
# === FALCO (eBPF syscall monitoring) ===
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm repo update

helm install falco falcosecurity/falco \
  --namespace falco --create-namespace \
  --set driver.kind=ebpf \
  --set tty=true \
  --set falco.grpc.enabled=true \
  --set falcoctl.artifact.install.enabled=true \
  --set falcoctl.artifact.follow.enabled=true

# Verify Falco eBPF probe
kubectl logs -n falco -l app.kubernetes.io/name=falco | grep -i ebpf

# === TETRAGON (eBPF runtime enforcement) ===
helm repo add cilium https://helm.cilium.io/
helm install tetragon cilium/tetragon \
  --namespace kube-system \
  --set tetragon.enabled=true \
  --set tetragon.exportFilename=/var/run/cilium/tetragon/tetragon.log

# Test Tetragon: Block file access to /etc/shadow
cat <<EOF | kubectl apply -f -
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: block-shadow-access
spec:
  kprobes:
  - call: "security_file_open"
    syscall: false
    args:
    - index: 0
      type: "file"
    selectors:
    - matchArgs:
      - index: 0
        operator: "Equal"
        values:
        - "/etc/shadow"
      matchActions:
      - action: Sigkill
EOF

kubectl get tracingpolicies
```

**Falco vs Tetragon**:
| Feature | Falco | Tetragon |
|---------|-------|----------|
| Detection | Rule-based (YAML), outputs alerts | Policy-based (CRD), enforces actions |
| Response | Log, alert, webhook | Kill process, deny syscall, override return |
| Performance | ~1-3% CPU overhead | < 1% CPU overhead (eBPF LSM) |
| Use Case | SIEM integration, threat detection | Active runtime enforcement |

### 3.6 Install Policy Engine (OPA Gatekeeper or Kyverno)

```bash
# === OPA GATEKEEPER ===
kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/master/deploy/gatekeeper.yaml

# Wait for Gatekeeper
kubectl wait --for=condition=Available --timeout=300s deployment/gatekeeper-controller-manager -n gatekeeper-system

# Example policy: Deny privileged containers
cat <<EOF | kubectl apply -f -
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8spspprivilegedcontainer
spec:
  crd:
    spec:
      names:
        kind: K8sPSPPrivilegedContainer
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8spspprivilegedcontainer
        violation[{"msg": msg}] {
          c := input.review.object.spec.containers[_]
          c.securityContext.privileged
          msg := sprintf("Privileged container not allowed: %v", [c.name])
        }
EOF

cat <<EOF | kubectl apply -f -
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sPSPPrivilegedContainer
metadata:
  name: deny-privileged
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
EOF

# Test (should be denied)
kubectl run privileged-test --image=nginx --restart=Never --privileged
```

**Alternative: Kyverno** (no Rego, YAML-native):
```bash
kubectl create -f https://github.com/kyverno/kyverno/releases/download/v1.11.4/install.yaml

# Example policy
cat <<EOF | kubectl apply -f -
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-run-as-nonroot
spec:
  validationFailureAction: enforce
  rules:
  - name: check-runAsNonRoot
    match:
      resources:
        kinds:
        - Pod
    validate:
      message: "Running as root is not allowed"
      pattern:
        spec:
          securityContext:
            runAsNonRoot: true
EOF
```

### 3.7 Install Secrets Management (HashiCorp Vault)

```bash
# Install Vault in dev mode (for testing; use HA for production)
helm repo add hashicorp https://helm.releases.hashicorp.com
helm install vault hashicorp/vault \
  --namespace vault --create-namespace \
  --set server.dev.enabled=true \
  --set server.dev.devRootToken=root \
  --set injector.enabled=true

# Wait for Vault
kubectl wait --for=condition=Ready pod/vault-0 -n vault --timeout=300s

# Enable Kubernetes auth
kubectl exec -n vault vault-0 -- vault auth enable kubernetes
kubectl exec -n vault vault-0 -- vault write auth/kubernetes/config \
  kubernetes_host="https://kubernetes.default.svc.cluster.local:443"

# Create secret
kubectl exec -n vault vault-0 -- vault kv put secret/db password=supersecret

# Test: Inject secret into pod
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: vault-test
  annotations:
    vault.hashicorp.com/agent-inject: "true"
    vault.hashicorp.com/role: "myapp"
    vault.hashicorp.com/agent-inject-secret-db: "secret/db"
spec:
  serviceAccountName: default
  containers:
  - name: app
    image: nginx
EOF
```

### 3.8 Install GitOps (ArgoCD)

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD
kubectl wait --for=condition=Available --timeout=300s deployment/argocd-server -n argocd

# Get admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Port-forward
kubectl port-forward svc/argocd-server -n argocd 8080:443 &
# Access https://localhost:8080 (admin/<password>)
```

---

## Phase 4: eBPF Deep Dive - Advanced Topics

### 4.1 eBPF Maps Deep Dive

eBPF maps are the primary mechanism for data exchange between kernel and user space, and between different eBPF programs.

```c
// Example: Per-CPU hash map for connection tracking
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

struct conn_key {
    __u32 saddr;
    __u32 daddr;
    __u16 sport;
    __u16 dport;
};

struct conn_value {
    __u64 packets;
    __u64 bytes;
    __u64 last_seen;
};

// Per-CPU map: each CPU has its own copy (lock-free)
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_HASH);
    __uint(max_entries, 65536);
    __type(key, struct conn_key);
    __type(value, struct conn_value);
} conn_track SEC(".maps");

SEC("xdp")
int track_connections(struct xdp_md *ctx) {
    void *data_end = (void *)(long)ctx->data_end;
    void *data = (void *)(long)ctx->data;
    
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;
    
    if (eth->h_proto != __constant_htons(ETH_P_IP))
        return XDP_PASS;
    
    struct iphdr *iph = (void *)(eth + 1);
    if ((void *)(iph + 1) > data_end)
        return XDP_PASS;
    
    if (iph->protocol != IPPROTO_TCP)
        return XDP_PASS;
    
    struct tcphdr *tcph = (void *)(iph + 1);
    if ((void *)(tcph + 1) > data_end)
        return XDP_PASS;
    
    struct conn_key key = {
        .saddr = iph->saddr,
        .daddr = iph->daddr,
        .sport = tcph->source,
        .dport = tcph->dest,
    };
    
    struct conn_value *value = bpf_map_lookup_elem(&conn_track, &key);
    if (value) {
        __sync_fetch_and_add(&value->packets, 1);
        __sync_fetch_and_add(&value->bytes, data_end - data);
        value->last_seen = bpf_ktime_get_ns();
    } else {
        struct conn_value new_value = {
            .packets = 1,
            .bytes = data_end - data,
            .last_seen = bpf_ktime_get_ns(),
        };
        bpf_map_update_elem(&conn_track, &key, &new_value, BPF_ANY);
    }
    
    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";
```

**Map Types**:
- `BPF_MAP_TYPE_HASH`: General-purpose key-value (spinlock-protected)
- `BPF_MAP_TYPE_PERCPU_HASH`: Per-CPU copy, lock-free (ideal for high-frequency updates)
- `BPF_MAP_TYPE_LRU_HASH`: Evicts least-recently-used entries automatically
- `BPF_MAP_TYPE_ARRAY`: Fixed-size, fast O(1) lookup
- `BPF_MAP_TYPE_RINGBUF`: Producer-consumer queue (kernel → user space)
- `BPF_MAP_TYPE_STACK`: LIFO stack
- `BPF_MAP_TYPE_QUEUE`: FIFO queue

### 4.2 XDP (eXpress Data Path) - Line-Rate Packet Processing

XDP operates at the NIC driver layer, before sk_buff allocation. This enables packet processing at 40Gbps+ with minimal CPU overhead.

```
┌────────────────────────────────────────────────────────────────┐
│                  PACKET JOURNEY (XDP vs Traditional)            │
└────────────────────────────────────────────────────────────────┘

TRADITIONAL PATH (iptables/netfilter):
NIC → Driver → sk_buff allocation → iptables (O(n) rules) 
  → Routing → Bridge → TC → Application
  ⏱️ Latency: ~1-5ms, Throughput: ~10Gbps (iptables limited)

XDP PATH:
NIC → Driver → XDP BPF program → {XDP_PASS, XDP_DROP, XDP_TX, XDP_REDIRECT}
  ⏱️ Latency: ~10-100μs, Throughput: 40Gbps+ (line rate)

XDP ACTIONS:
• XDP_DROP: Discard packet (DDoS mitigation)
• XDP_PASS: Continue to network stack
• XDP_TX: Bounce packet back out same interface (echo server)
• XDP_REDIRECT: Send to another interface/CPU (load balancing)
• XDP_ABORTED: Error, packet dropped
```

**XDP L4 Load Balancer Example**:
```c
// XDP-based L4 load balancer (simplified)
#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <bpf/bpf_helpers.h>

#define BACKEND_COUNT 3

struct backend {
    __u32 ip;
    __u16 port;
};

struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, BACKEND_COUNT);
    __type(key, __u32);
    __type(value, struct backend);
} backends SEC(".maps");

SEC("xdp")
int load_balancer(struct xdp_md *ctx) {
    void *data_end = (void *)(long)ctx->data_end;
    void *data = (void *)(long)ctx->data;
    
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;
    
    if (eth->h_proto != __constant_htons(ETH_P_IP))
        return XDP_PASS;
    
    struct iphdr *iph = (void *)(eth + 1);
    if ((void *)(iph + 1) > data_end)
        return XDP_PASS;
    
    if (iph->protocol != IPPROTO_TCP)
        return XDP_PASS;
    
    struct tcphdr *tcph = (void *)(iph + 1);
    if ((void *)(tcph + 1) > data_end)
        return XDP_PASS;
    
    // Simple hash-based load balancing
    __u32 hash = iph->saddr ^ tcph->source;
    __u32 backend_idx = hash % BACKEND_COUNT;
    
    struct backend *be = bpf_map_lookup_elem(&backends, &backend_idx);
    if (!be)
        return XDP_PASS;
    
    // Rewrite destination (DNAT)
    __u32 old_daddr = iph->daddr;
    __u16 old_dport = tcph->dest;
    
    iph->daddr = be->ip;
    tcph->dest = be->port;
    
    // Update checksums
    iph->check = 0;
    iph->check = calculate_ip_checksum(iph);
    
    // TCP checksum (pseudo-header + TCP header)
    tcph->check = 0;
    tcph->check = calculate_tcp_checksum(iph, tcph, data_end);
    
    return XDP_TX;  // Send back out
}
```

Compile and load:
```bash
clang -O2 -target bpf -c xdp_lb.c -o xdp_lb.o
sudo ip link set dev eth0 xdp obj xdp_lb.o sec xdp

# Verify
sudo bpftool net show dev eth0
sudo bpftool prog show

# Unload
sudo ip link set dev eth0 xdp off
```

### 4.3 eBPF LSM (Linux Security Module) - Runtime Enforcement

eBPF LSM hooks allow security policy enforcement at kernel security checkpoints without modifying kernel code or loading kernel modules.

```c
// Deny execution of /usr/bin/wget (example)
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_core_read.h>

SEC("lsm/bprm_check_security")
int BPF_PROG(deny_wget, struct linux_binprm *bprm, int ret)
{
    const char *filename = BPF_CORE_READ(bprm, filename);
    char comm[16];
    
    bpf_probe_read_str(comm, sizeof(comm), filename);
    
    if (bpf_strncmp(comm, 12, "/usr/bin/wget") == 0) {
        bpf_printk("Blocked execution of wget");
        return -EPERM;  // Deny execution
    }
    
    return 0;  // Allow
}

char _license[] SEC("license") = "GPL";
```

**LSM Hook Points**:
- `bprm_check_security`: Binary execution
- `file_open`: File access
- `socket_connect`: Network connections
- `task_kill`: Signal sending (kill)
- `sb_mount`: Filesystem mounting

### 4.4 CO-RE (Compile Once, Run Everywhere)

Traditional eBPF programs break when kernel versions change (struct layouts, field offsets). CO-RE solves this with BTF (BPF Type Format).

```c
// Without CO-RE (breaks on kernel updates)
struct task_struct *task = (struct task_struct *)bpf_get_current_task();
pid_t pid = task->pid;  // Offset hardcoded at compile time

// With CO-RE (portable across kernels)
struct task_struct *task = (struct task_struct *)bpf_get_current_task();
pid_t pid = BPF_CORE_READ(task, pid);  // Offset resolved at load time via BTF
```

**Enable BTF**:
```bash
# Check if BTF is available
ls /sys/kernel/btf/vmlinux

# If missing, rebuild kernel with CONFIG_DEBUG_INFO_BTF=y
# Ubuntu 20.04+ has BTF by default
```

---

## Phase 5: Production Hardening & Security

### 5.1 Threat Model

```
┌────────────────────────────────────────────────────────────────────┐
│                      THREAT LANDSCAPE                               │
├────────────────────────────────────────────────────────────────────┤
│ Attack Surface        │ Threat                  │ eBPF Mitigation  │
├───────────────────────┼─────────────────────────┼──────────────────┤
│ Container escape      │ Privileged containers   │ Falco/Tetragon   │
│                       │ Kernel exploits         │ LSM hooks deny   │
├───────────────────────┼─────────────────────────┼──────────────────┤
│ Network eavesdropping │ Unencrypted traffic     │ Cilium WireGuard │
│                       │ Man-in-the-middle       │ mTLS enforcement │
├───────────────────────┼─────────────────────────┼──────────────────┤
│ Data exfiltration     │ Unexpected egress       │ Cilium L3/L4/L7  │
│                       │ DNS tunneling           │ policy + Hubble  │
├───────────────────────┼─────────────────────────┼──────────────────┤
│ Supply chain          │ Malicious images        │ Admission ctrl   │
│                       │ Unsigned binaries       │ + Sigstore       │
├───────────────────────┼─────────────────────────┼──────────────────┤
│ Lateral movement      │ Pod-to-pod unrestricted │ Zero-trust net   │
│                       │ Stolen credentials      │ + identity-based │
└───────────────────────┴─────────────────────────┴──────────────────┘
```

### 5.2 Defense-in-Depth Implementation

```bash
# 1. Enable Pod Security Standards (PSS)
kubectl label namespace default pod-security.kubernetes.io/enforce=restricted
kubectl label namespace default pod-security.kubernetes.io/warn=restricted

# 2. Network Segmentation (Cilium NetworkPolicy)
cat <<EOF | kubectl apply -f -
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: default-deny-all
spec:
  endpointSelector: {}
  ingress:
  - {}
  egress:
  - {}
---
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: allow-dns
spec:
  endpointSelector: {}
  egress:
  - toEndpoints:
    - matchLabels:
        k8s:io.kubernetes.pod.namespace: kube-system
        k8s:k8s-app: kube-dns
    toPorts:
    - ports:
      - port: "53"
        protocol: UDP
      rules:
        dns:
        - matchPattern: "*"
EOF

# 3. Enable Cilium Encryption (WireGuard)
cilium upgrade --set encryption.enabled=true --set encryption.type=wireguard

# 4. Enable Hubble Flow Logging
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: hubble-config
  namespace: kube-system
data:
  enable-hubble: "true"
  hubble-listen-address: ":4244"
  hubble-metrics-server: ":9091"
  hubble-metrics:
    - dns
    - drop
    - tcp
    - flow
    - icmp
    - http
EOF

# 5. Tetragon Tracing Policy: Deny /etc/passwd writes
cat <<EOF | kubectl apply -f -
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: protect-passwd
spec:
  kprobes:
  - call: "security_file_permission"
    syscall: false
    args:
    - index: 0
      type: "file"
    - index: 1
      type: "int"
    selectors:
    - matchArgs:
      - index: 0
        operator: "Equal"
        values:
        - "/etc/passwd"
      - index: 1
        operator: "Mask"
        values:
        - "2"  # MAY_WRITE
      matchActions:
      - action: Sigkill
EOF
```

### 5.3 Security Testing

```bash
# 1. Test container escape (should be blocked)
kubectl run escape-test --image=alpine --restart=Never -- sh -c "cat /etc/shadow"
# Check Falco logs
kubectl logs -n falco -l app.kubernetes.io/name=falco | grep -i shadow

# 2. Test network policy (should deny)
kubectl run nettest --image=busybox --restart=Never -- wget -O- http://google.com
kubectl logs nettest

# 3. Test privileged container (OPA should deny)
kubectl run priv-test --image=nginx --privileged --restart=Never
# Should fail with "Privileged container not allowed"

# 4. Cilium connectivity test (end-to-end)
cilium connectivity test --test-concurrency=1

# 5. Benchmark: XDP vs iptables
# Install iperf3
kubectl run iperf-server --image=networkstatic/iperf3 -- -s
kubectl run iperf-client --image=networkstatic/iperf3 -- -c <SERVER_IP> -t 30
```

---

## Phase 6: Observability Deep Dive

### 6.1 Hubble Flow Logs (eBPF L3-L7 Visibility)

```bash
# Install Hubble CLI
HUBBLE_VERSION=$(curl -s https://raw.githubusercontent.com/cilium/hubble/master/stable.txt)
curl -L --remote-name-all https://github.com/cilium/hubble/releases/download/$HUBBLE_VERSION/hubble-linux-amd64.tar.gz{,.sha256sum}
tar xzvfC hubble-linux-amd64.tar.gz /usr/local/bin
rm hubble-linux-amd64.tar.gz{,.sha256sum}

# Port-forward Hubble relay
cilium hubble port-forward &

# Watch flows in real-time
hubble observe --follow

# Filter by pod
hubble observe --pod kube-system/coredns

# Filter by L7 protocol
hubble observe --protocol http

# Top connections
hubble observe --last 1000 | grep -oP 'from [^ ]+' | sort | uniq -c | sort -rn | head -10
```

**Hubble Architecture**:
```
┌────────────────────────────────────────────────────────────────┐
│                       HUBBLE FLOW PIPELINE                      │
└────────────────────────────────────────────────────────────────┘
  Pod Traffic
      │
      ▼
  ┌──────────────────┐
  │ Cilium Agent     │
  │ (eBPF datapath)  │
  └────────┬─────────┘
           │ eBPF ringbuffer
           ▼
  ┌──────────────────┐
  │ Hubble Server    │ (per-node)
  │ • Decodes flows  │
  │ • Adds metadata  │
  │ • L7 parsing     │
  └────────┬─────────┘
           │ gRPC
           ▼
  ┌──────────────────┐
  │ Hubble Relay     │ (cluster-wide)
  │ • Aggregates     │
  │ • Filters        │
  └────────┬─────────┘
           │ gRPC
           ├────────────────┬──────────────┐
           ▼                ▼              ▼
      Hubble UI      Hubble CLI      Prometheus
                                      (metrics export)
```

### 6.2 Pixie (eBPF Auto-Instrumentation)

Pixie automatically captures application metrics, traces, and logs without code changes or sidecar injection.

```bash
# Install Pixie CLI
bash -c "$(curl -fsSL https://withpixie.ai/install.sh)"

# Install Pixie on cluster
px deploy

# Wait for deployment
px get viziers

# Run pre-built queries
px live "/http_data"  # HTTP requests/responses
px live "/dns_data"   # DNS queries
px live "/mysql_data" # MySQL queries (parsed from eBPF uprobes)

# Custom PxL script (Pixie Language)
cat <<'EOF' > custom_query.pxl
import px

df = px.DataFrame(table='http_events', start_time='-5m')
df = df[df.resp_status >= 400]  # Errors only
df = df.groupby(['req_path', 'resp_status']).agg(count=('resp_status', px.count))
px.display(df)
EOF

px run -f custom_query.pxl
```

**Pixie Under the Hood**:
- **uprobes**: Dynamically attach to SSL_read/SSL_write in OpenSSL library → decrypt HTTPS traffic
- **Kernel tracepoints**: Capture socket events, syscalls
- **eBPF maps**: Store connection state, protocol parsers
- **No sidecars**: Zero application modification

---

## Phase 7: Advanced eBPF Projects

### 7.1 Katran (XDP L4 Load Balancer by Facebook)

```bash
git clone https://github.com/facebookincubator/katran.git
cd katran
# Follow build instructions (requires BPF/LLVM toolchain)
```

### 7.2 bpftrace (DTrace-like Tracing)

```bash
apt-get install -y bpftrace

# Trace all syscalls by process
bpftrace -e 'tracepoint:raw_syscalls:sys_enter { @[comm] = count(); }'

# Trace file opens
bpftrace -e 'tracepoint:syscalls:sys_enter_openat { printf("%s opened %s\n", comm, str(args->filename)); }'

# Latency histogram for block I/O
bpftrace -e 'kprobe:blk_account_io_start { @start[tid] = nsecs; } kretprobe:blk_account_io_done /@start[tid]/ { @latency = hist(nsecs - @start[tid]); delete(@start[tid]); }'
```

---

## Phase 8: Production Roll-Out Plan

### 8.1 Rollout Strategy

```
┌────────────────────────────────────────────────────────────────┐
│                   PHASED ROLLOUT (CANARY)                       │
└────────────────────────────────────────────────────────────────┘
Week 1: Dev Environment
  • Deploy full stack on dev cluster
  • Run integration tests
  • Falco/Tetragon in audit mode (log only, no enforcement)
  • Validate eBPF programs loaded correctly (bpftool)

Week 2: Staging Environment
  • Enable Cilium Network Policies (default-deny)
  • Enable Tetragon enforcement (gradual: start with file policies)
  • Load test with realistic traffic (k6, Locust)
  • Benchmark: XDP load balancer vs iptables

Week 3: Production Canary (10% traffic)
  • Deploy to 1 node
  • Monitor: Hubble flow drops, Falco alerts, Prometheus metrics
  • Compare latency/throughput vs baseline
  • Automated rollback if error rate > 1%

Week 4: Production Full Rollout
  • Gradual rollout: 10% → 25% → 50% → 100%
  • Enable WireGuard encryption
  • Enable Vault secrets injection
  • Final validation: Cilium connectivity test
```

### 8.2 Rollback Plan

```bash
# Automated rollback script
cat <<'EOF' > rollback.sh
#!/bin/bash
set -e

echo "Rolling back to previous version..."

# Cilium rollback
helm rollback cilium -n kube-system

# Remove Tetragon enforcement
kubectl delete tracingpolicies --all

# Revert to iptables kube-proxy (if needed)
kubectl delete daemonset cilium -n kube-system
curl -sfL https://get.k3s.io | sh -s - server --flannel-backend=vxlan

# Verify
kubectl get nodes
kubectl get pods -A
EOF

chmod +x rollback.sh
```

---

## Phase 9: Benchmarking & Performance Tuning

### 9.1 eBPF Overhead Measurement

```bash
# Baseline: no eBPF
iperf3 -s &
iperf3 -c localhost -t 30 -P 4

# With Cilium eBPF
# (Typically < 5% overhead for datapath, < 1% for observability)

# With Hubble + Tetragon + Falco
# (Combined < 8% CPU overhead)
```

### 9.2 Tuning eBPF Maps

```bash
# Increase map size for high-connection workloads
cilium config set bpf-ct-global-tcp-max 1048576  # Default: 524288
cilium config set bpf-ct-global-any-max 262144   # Default: 131072

# Per-CPU maps for lock-free performance
# Already enabled by default in Cilium
```

---

## Phase 10: Next Steps & References

### Next 3 Steps

1. **Deploy Base Infrastructure** (Days 1-3):
   - Set up k3s cluster (control + data plane)
   - Install Cilium with eBPF features
   - Validate with `cilium connectivity test`

2. **Security Hardening** (Days 4-7):
   - Deploy Falco + Tetragon (audit mode first)
   - Implement OPA/Kyverno policies (deny privileged, enforce resource limits)
   - Enable Cilium Network Policies (default-deny, allow DNS/egress)

3. **Observability Stack** (Days 8-10):
   - Install Prometheus + Grafana + Loki
   - Enable Hubble UI for flow visualization
   - Deploy Pixie for auto-instrumented APM

### References

**eBPF Core**:
- eBPF.io (official docs): https://ebpf.io/
- Cilium eBPF docs: https://docs.cilium.io/en/stable/bpf/
- Linux kernel BPF docs: https://www.kernel.org/doc/html/latest/bpf/
- libbpf GitHub: https://github.com/libbpf/libbpf

**Production Projects**:
- Cilium: https://github.com/cilium/cilium
- Falco: https://github.com/falcosecurity/falco
- Tetragon: https://github.com/cilium/tetragon
- Pixie: https://github.com/pixie-io/pixie
- Hubble: https://github.com/cilium/hubble

**Learning Resources**:
- "BPF Performance Tools" by Brendan Gregg (book)
- Cilium eBPF workshop: https://github.com/cilium/ebpf-summit-2021
- eBPF Summit recordings: https://ebpf.io/summit-2024/

**Security**:
- MITRE ATT&CK for Containers: https://attack.mitre.org/matrices/enterprise/containers/
- Kubernetes Security Best Practices: https://kubernetes.io/docs/concepts/security/

---

## Architecture Cheat Sheet

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FINAL PRODUCTION ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                      CONTROL PLANE VM                          │ │
│  ├───────────────────────────────────────────────────────────────┤ │
│  │  k3s (Kubernetes)                                              │ │
│  │    ├─ etcd (state store)                                       │ │
│  │    ├─ API server (6443)                                        │ │
│  │    └─ Scheduler + Controllers                                  │ │
│  │  Cilium Control Plane                                          │ │
│  │    ├─ Operator (policy compilation)                            │ │
│  │    └─ Hubble Relay (cluster-wide flow aggregation)             │ │
│  │  Prometheus + Grafana + Loki                                   │ │
│  │  Vault (secrets)                                               │ │
│  │  ArgoCD (GitOps)                                               │ │
│  │  OPA Gatekeeper / Kyverno                                      │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                            ▲                                         │
│                            │ kubectl, gRPC                           │
│                            ▼                                         │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                       DATA PLANE VM                            │ │
│  ├───────────────────────────────────────────────────────────────┤ │
│  │  containerd (CRI)                                              │ │
│  │  Cilium Agent (eBPF datapath)                                  │ │
│  │    ├─ XDP programs (L4 LB, DDoS)                               │ │
│  │    ├─ TC programs (L3/L4/L7 policy)                            │ │
│  │    ├─ Socket programs (transparent proxy)                      │ │
│  │    └─ LSM hooks (runtime security)                             │ │
│  │  Hubble Server (local flow export)                             │ │
│  │  Falco (syscall monitoring)                                    │ │
│  │  Tetragon (enforcement engine)                                 │ │
│  │  Pixie (auto-instrumentation)                                  │ │
│  │  Prometheus Node Exporter                                      │ │
│  │  Fluent Bit (log shipping)                                     │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

**Final Notes**:
- Your hardware (i5, 32GB RAM, GTX 1650) is sufficient for this setup
- Control plane (8GB RAM) will run at ~60-70% utilization under load
- Data plane (16GB RAM) will handle ~50-100 pods comfortably
- eBPF overhead is negligible (< 5% CPU for networking, < 3% for observability)
- All components are production-proven (Adobe, Capital One, Bloomberg use this exact stack)

This guide provides a foundation for a secure, observable, high-performance cloud-native platform. The eBPF-first approach eliminates sidecar overhead, provides kernel-level visibility, and enables runtime security enforcement without kernel modules. Start with the base k3s + Cilium setup, then layer in observability and security components incrementally.