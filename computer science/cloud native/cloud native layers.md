**Cloud-native and data-center infrastructure are organized into vertical layers—from bare metal through orchestration to application runtime—with CNCF projects filling most gaps.**

---

## **Layered Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│  L7: Developer Experience & Workflows                       │
│  (CI/CD, GitOps, Policy, Config Management)                 │
│  → Argo, Flux, Tekton, Backstage, OPA, Crossplane          │
└─────────────────────────────────────────────────────────────┘
                           ▲
┌─────────────────────────────────────────────────────────────┐
│  L6: Application Definition & Image Build                   │
│  (Manifests, Helm, Operators, Image Distribution)           │
│  → Helm, Operator Framework, Harbor, Buildpacks, KubeVirt   │
└─────────────────────────────────────────────────────────────┘
                           ▲
┌─────────────────────────────────────────────────────────────┐
│  L5: Observability & Analysis                                │
│  (Metrics, Logs, Traces, Cost, Chaos)                       │
│  → Prometheus, Grafana, Jaeger, OpenTelemetry, Fluentd,    │
│    Thanos, Loki, Cortex, LitmusChaos                        │
└─────────────────────────────────────────────────────────────┘
                           ▲
┌─────────────────────────────────────────────────────────────┐
│  L4: Service Mesh & API Gateway                              │
│  (L7 routing, mTLS, policy, traffic management)             │
│  → Istio, Linkerd, Envoy, Contour, Cilium (L7)             │
└─────────────────────────────────────────────────────────────┘
                           ▲
┌─────────────────────────────────────────────────────────────┐
│  L3: Orchestration & Scheduling                              │
│  (Workload placement, scaling, lifecycle)                    │
│  → Kubernetes, Nomad, Crossplane (control-plane ext)        │
└─────────────────────────────────────────────────────────────┘
                           ▲
┌─────────────────────────────────────────────────────────────┐
│  L2: Container Runtime & Storage/Networking Primitives       │
│  (OCI runtime, CNI, CSI, node-level isolation)              │
│  → containerd, CRI-O, runc, gVisor, Kata, Cilium (eBPF),   │
│    Rook, Longhorn, Calico, Flannel, Weave                   │
└─────────────────────────────────────────────────────────────┘
                           ▲
┌─────────────────────────────────────────────────────────────┐
│  L1: Host OS & Virtualization                                │
│  (Kernel, systemd, KVM/Xen, node agents)                    │
│  → Flatcar, Bottlerocket, Talos, KubeVirt                   │
└─────────────────────────────────────────────────────────────┘
                           ▲
┌─────────────────────────────────────────────────────────────┐
│  L0: Physical/Cloud Infrastructure                           │
│  (Compute, network fabric, storage arrays, IaaS APIs)       │
│  → Bare metal, AWS/GCP/Azure, Cluster API, Tinkerbell       │
└─────────────────────────────────────────────────────────────┘
```

---

## **Layer 0: Physical & IaaS**

**Scope**: Servers, racks, ToR switches, storage SANs, hyperscale cloud APIs.

**CNCF Projects**:
- **Cluster API**: Declarative K8s-style provisioning for clusters across clouds/bare-metal.
- **Tinkerbell**: Bare-metal provisioning (DHCP, netboot, workflow engine).
- **Metal³**: Kubernetes-native bare-metal management (Ironic integration).

**Example**:
```yaml
# ClusterAPI MachineDeployment for AWS
apiVersion: cluster.x-k8s.io/v1beta1
kind: MachineDeployment
metadata:
  name: worker-nodes
spec:
  replicas: 3
  template:
    spec:
      infrastructureRef:
        apiVersion: infrastructure.cluster.x-k8s.io/v1beta2
        kind: AWSMachineTemplate
        name: worker-template
```

**Threat Model**:
- **Firmware/BMC compromise** → Use measured boot (TPM), UEFI Secure Boot.
- **Network fabric attacks** → 802.1X, MACsec, segmented VLANs.

**Trade-offs**:
- On-prem: Full control, CapEx overhead, slower provisioning.
- Cloud IaaS: Elastic, OpEx, vendor lock-in, noisy neighbors.

---

## **Layer 1: Host OS & Virtualization**

**Scope**: Minimal OS, init system, KVM/Xen for VMs, node-level agents (kubelet, systemd).

**CNCF Projects**:
- **KubeVirt**: Run VMs as K8s pods (libvirt + CRDs).
- Container-optimized OSes: Flatcar Container Linux, Bottlerocket, Talos Linux.

**Example**:
```yaml
# KubeVirt VirtualMachine
apiVersion: kubevirt.io/v1
kind: VirtualMachine
metadata:
  name: legacy-app-vm
spec:
  running: true
  template:
    spec:
      domain:
        devices:
          disks:
          - disk:
              bus: virtio
            name: containerdisk
        resources:
          requests:
            memory: 1024M
      volumes:
      - containerDisk:
          image: quay.io/kubevirt/fedora-cloud-container-disk-demo
        name: containerdisk
```

**Security**:
- **Immutable root**: Bottlerocket, Talos → read-only `/`, A/B updates.
- **seccomp, AppArmor, SELinux**: Kernel MAC policies.
- **CIS benchmarks**: Harden sshd, disable unused services.

**Verification**:
```bash
# Check Bottlerocket version & immutability
apiclient get os
# Talos: verify node config
talosctl get machineconfig
```

---

## **Layer 2: Container Runtime & Node-Level Primitives**

**Scope**: OCI runtime (runc, gVisor), CRI (containerd, CRI-O), CNI plugins, CSI drivers.

**CNCF Projects**:
- **containerd**: High-level runtime (CRI, image pull, snapshots).
- **CRI-O**: Minimal CRI for Kubernetes (OCI-only).
- **runc**: Low-level OCI executor (cgroups, namespaces).
- **gVisor**: User-space kernel (syscall sandboxing).
- **Kata Containers**: VM-isolated containers (KVM boundary).
- **Cilium**: eBPF-based CNI (L3/L4/L7, observability).
- **Calico, Flannel**: Traditional overlay/underlay CNI.
- **Rook**: Cloud-native storage orchestrator (Ceph operator).
- **Longhorn**: Distributed block storage.

**Example: containerd + gVisor**:
```toml
# /etc/containerd/config.toml
[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runsc]
  runtime_type = "io.containerd.runsc.v1"
[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runsc.options]
  TypeUrl = "io.containerd.runsc.v1.options"
  ConfigPath = "/etc/containerd/runsc.toml"
```
```yaml
# Pod with gVisor
apiVersion: v1
kind: Pod
metadata:
  name: sandboxed-app
spec:
  runtimeClassName: gvisor
  containers:
  - name: app
    image: nginx:alpine
```

**CNI Configuration (Cilium)**:
```bash
# Install Cilium CNI
cilium install --set hubble.relay.enabled=true
# Verify eBPF programs loaded
cilium status
bpftool prog list | grep cilium
```

**Threat Model**:
- **Container escape** → Use gVisor/Kata for untrusted workloads, seccomp strict profiles.
- **Network sniffing** → Cilium network policies (L3/L4/L7), WireGuard encryption.
- **Storage tampering** → CSI encryption at rest (LUKS), Rook/Ceph auth.

**Test**:
```bash
# Benchmark containerd vs gVisor
sysbench cpu run --threads=1 --time=10
# In gVisor: expect ~30-50% overhead for syscall-heavy workloads
```

---

## **Layer 3: Orchestration & Scheduling**

**Scope**: Workload placement, autoscaling, rolling updates, multi-tenancy.

**CNCF Projects**:
- **Kubernetes**: Dominant orchestrator (pods, services, CRDs).
- **Crossplane**: Universal control plane (manage cloud resources as K8s objects).

**Example: Advanced Scheduling**:
```yaml
# Pod with affinity, taints, topology spread
apiVersion: v1
kind: Pod
metadata:
  name: latency-sensitive
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: workload-type
            operator: In
            values: ["latency-sensitive"]
  topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: topology.kubernetes.io/zone
    whenUnsatisfiable: DoNotSchedule
    labelSelector:
      matchLabels:
        app: frontend
  tolerations:
  - key: "dedicated"
    operator: "Equal"
    value: "gpu"
    effect: "NoSchedule"
  containers:
  - name: app
    image: myapp:v2
    resources:
      requests:
        cpu: "2"
        memory: "4Gi"
      limits:
        nvidia.com/gpu: "1"
```

**Security**:
- **RBAC**: Least-privilege service accounts, namespace isolation.
- **PodSecurityStandards**: Enforce restricted profile (no privileged, no hostPath).
- **Audit logs**: `--audit-log-path`, ship to SIEM.

**Verification**:
```bash
# Check scheduler decisions
kubectl get events --field-selector involvedObject.kind=Pod --sort-by='.lastTimestamp'
# Autoscaler logs
kubectl logs -n kube-system deployment/cluster-autoscaler
```

**Failure Mode**: Scheduler thrashing → Set PDBs, node anti-affinity, monitor pending pods.

---

## **Layer 4: Service Mesh & API Gateway**

**Scope**: L7 traffic management, mTLS, observability, policy enforcement.

**CNCF Projects**:
- **Istio**: Full-featured mesh (Envoy sidecar, control plane).
- **Linkerd**: Lightweight, Rust-based data plane.
- **Envoy**: High-performance L7 proxy (xDS API).
- **Contour**: Ingress controller (Envoy-based).
- **Cilium**: eBPF service mesh (no sidecar).

**Example: Istio mTLS + AuthorizationPolicy**:
```yaml
# Enable strict mTLS
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: prod
spec:
  mtls:
    mode: STRICT
---
# L7 policy: only allow GET from frontend
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: backend-policy
  namespace: prod
spec:
  selector:
    matchLabels:
      app: backend
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/prod/sa/frontend"]
    to:
    - operation:
        methods: ["GET"]
        paths: ["/api/v1/*"]
```

**Observability**:
```bash
# Verify mTLS
istioctl authn tls-check frontend-pod.prod backend.prod.svc.cluster.local
# Envoy stats
kubectl exec frontend-pod -c istio-proxy -- curl localhost:15000/stats/prometheus
```

**Threat Model**:
- **Man-in-the-middle** → Enforce STRICT mTLS, rotate certs (cert-manager + Istio CA).
- **Lateral movement** → L7 AuthorizationPolicy, deny-by-default.

**Trade-offs**:
- Istio: Feature-rich, 20-50ms latency overhead, complex.
- Linkerd: Simpler, lower overhead (~1ms), fewer features.
- Cilium: No sidecar (eBPF), bleeding-edge, kernel ≥5.10 required.

---

## **Layer 5: Observability & Analysis**

**Scope**: Metrics, logs, traces, cost attribution, chaos engineering.

**CNCF Projects**:
- **Prometheus**: Metrics scraping, PromQL, alerting.
- **Grafana**: Visualization, dashboards.
- **Thanos, Cortex**: Long-term Prometheus storage (multi-cluster).
- **Loki**: Log aggregation (Prometheus for logs).
- **Jaeger, Tempo**: Distributed tracing.
- **OpenTelemetry**: Unified telemetry SDK (metrics/logs/traces).
- **Fluentd, Fluent Bit**: Log forwarding.
- **LitmusChaos**: Chaos experiments (pod kill, network latency).

**Example: Full Observability Stack**:
```yaml
# Prometheus ServiceMonitor
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: backend-metrics
spec:
  selector:
    matchLabels:
      app: backend
  endpoints:
  - port: metrics
    path: /metrics
    interval: 15s
---
# Loki LogQL alert
groups:
- name: errors
  rules:
  - alert: HighErrorRate
    expr: |
      sum(rate({app="backend"} |= "ERROR" [5m])) > 10
    for: 5m
```

**OpenTelemetry Instrumentation (Go)**:
```go
import (
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
    sdktrace "go.opentelemetry.io/otel/sdk/trace"
)

func initTracer() (*sdktrace.TracerProvider, error) {
    exp, _ := otlptracegrpc.New(context.Background(),
        otlptracegrpc.WithEndpoint("otel-collector:4317"),
        otlptracegrpc.WithInsecure(),
    )
    tp := sdktrace.NewTracerProvider(
        sdktrace.WithBatcher(exp),
        sdktrace.WithSampler(sdktrace.AlwaysSample()),
    )
    otel.SetTracerProvider(tp)
    return tp, nil
}
```

**Chaos Test**:
```bash
# LitmusChaos: inject 200ms latency
kubectl apply -f - <<EOF
apiVersion: litmuschaos.io/v1alpha1
kind: ChaosEngine
metadata:
  name: network-chaos
spec:
  engineState: active
  chaosServiceAccount: litmus-admin
  experiments:
  - name: pod-network-latency
    spec:
      components:
        env:
        - name: NETWORK_LATENCY
          value: '200'
        - name: TARGET_CONTAINER
          value: backend
EOF
```

**Verification**:
```bash
# Query Prometheus
promtool query instant http://prometheus:9090 'rate(http_requests_total[5m])'
# Trace lookup (Jaeger)
curl "http://jaeger:16686/api/traces?service=backend&limit=10"
```

---

## **Layer 6: Application Definition & Image Build**

**Scope**: Packaging (Helm, Kustomize), operators (CRDs + controllers), image registries.

**CNCF Projects**:
- **Helm**: Package manager (charts, templating).
- **Operator Framework**: Build Kubernetes operators (Go, Ansible, Helm-based).
- **Harbor**: Enterprise registry (vulnerability scanning, replication, RBAC).
- **Buildpacks**: OCI image builds without Dockerfiles (Cloud Native Buildpacks).
- **KubeVirt**: (Also L1) VM CRDs.

**Example: Helm + Operator**:
```bash
# Deploy PostgreSQL operator
helm repo add postgres-operator-charts https://opensource.zalando.com/postgres-operator/charts/postgres-operator
helm install postgres-operator postgres-operator-charts/postgres-operator
# Custom resource for PG cluster
cat <<EOF | kubectl apply -f -
apiVersion: acid.zalan.do/v1
kind: postgresql
metadata:
  name: prod-db
spec:
  teamId: platform
  numberOfInstances: 3
  volume:
    size: 100Gi
    storageClass: fast-ssd
  postgresql:
    version: "15"
    parameters:
      max_connections: "200"
EOF
```

**Buildpacks (Dockerfile-less)**:
```bash
# Build Go app with Cloud Native Buildpacks
pack build myapp:v1 --builder paketobuildpacks/builder:base
# Result: OCI image with minimal layers, auto-detected runtime
```

**Harbor Scan**:
```bash
# Tag & push
docker tag myapp:v1 harbor.example.com/prod/myapp:v1
docker push harbor.example.com/prod/myapp:v1
# Scan via API
curl -u admin:password https://harbor.example.com/api/v2.0/projects/prod/repositories/myapp/artifacts/v1/scan
```

**Threat Model**:
- **Supply chain attacks** → Sign images (Sigstore/Cosign), SBOM (Syft), verify in admission controller (Kyverno).
- **Vulnerable dependencies** → Integrate Trivy/Grype in CI, block HIGH/CRITICAL.

---

## **Layer 7: Developer Experience & Workflows**

**Scope**: CI/CD pipelines, GitOps, policy-as-code, IDP (Internal Developer Platform).

**CNCF Projects**:
- **Argo CD, Flux**: GitOps continuous delivery.
- **Tekton**: Kubernetes-native CI/CD (Tasks, Pipelines).
- **Backstage**: Developer portal (service catalog, templates).
- **Open Policy Agent (OPA)**: Policy engine (Rego language).
- **Crossplane**: (Also L3) Infrastructure-as-K8s-resources.

**Example: Argo CD + OPA Gatekeeper**:
```yaml
# ArgoCD Application
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: backend-prod
spec:
  project: default
  source:
    repoURL: https://github.com/myorg/backend
    targetRevision: main
    path: k8s/overlays/prod
  destination:
    server: https://kubernetes.default.svc
    namespace: prod
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
---
# OPA Gatekeeper constraint: require resource limits
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sContainerLimits
metadata:
  name: must-have-limits
spec:
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
  parameters:
    cpu: "2"
    memory: "8Gi"
```

**Tekton Pipeline (Build + Deploy)**:
```yaml
apiVersion: tekton.dev/v1beta1
kind: Pipeline
metadata:
  name: build-deploy
spec:
  params:
  - name: git-url
  - name: image-name
  tasks:
  - name: git-clone
    taskRef:
      name: git-clone
    params:
    - name: url
      value: $(params.git-url)
  - name: build-image
    runAfter: ["git-clone"]
    taskRef:
      name: kaniko
    params:
    - name: IMAGE
      value: $(params.image-name)
  - name: scan-image
    runAfter: ["build-image"]
    taskRef:
      name: trivy-scan
  - name: deploy
    runAfter: ["scan-image"]
    taskRef:
      name: kubectl-deploy
```

**Policy Test**:
```bash
# Dry-run OPA policy
conftest test k8s/deployment.yaml --policy opa-policies/
# Gatekeeper audit
kubectl get constraints -A
```

---

## **Cross-Cutting Concerns**

| Concern          | CNCF Projects                                  | Implementation                                   |
|------------------|------------------------------------------------|--------------------------------------------------|
| **Identity**     | SPIFFE/SPIRE, Keycloak (sandbox)             | Workload identity (X.509 SVIDs), OIDC          |
| **Secrets**      | External Secrets Operator, Sealed Secrets     | Sync from Vault/AWS Secrets Manager             |
| **Multi-tenancy**| HNC (Hierarchical Namespaces), vcluster       | Namespace hierarchy, virtual clusters           |
| **Cost**         | OpenCost, Kubecost (uses Prometheus)          | Pod-level cost attribution                      |
| **Edge/IoT**     | K3s, KubeEdge, Akri                           | Lightweight K8s, device management              |

---

## **Threat Model Summary**

| Layer | Top Threats | Mitigations |
|-------|-------------|-------------|
| L0-L1 | Firmware rootkits, hypervisor escape | Measured boot, UEFI SB, KVM hardening |
| L2 | Container escape, network sniffing | gVisor/Kata, seccomp, Cilium encryption |
| L3 | RBAC bypass, scheduler abuse | PodSecurityStandards, audit logs, resource quotas |
| L4 | MITM, unauthorized L7 access | mTLS STRICT, AuthorizationPolicy |
| L5 | Log injection, metric spoofing | Sanitize logs, mTLS to collectors |
| L6 | Supply chain attacks | Image signing (Cosign), SBOM, admission control |
| L7 | GitOps repo compromise, policy drift | Branch protection, OPA/Kyverno, drift detection |

---

## **Production Rollout Plan**

1. **Phase 1 (Weeks 1-2)**: Deploy L0-L2 foundation.
   ```bash
   # Provision nodes (Cluster API)
   clusterctl init --infrastructure aws
   clusterctl generate cluster prod --kubernetes-version v1.28.0 > cluster.yaml
   kubectl apply -f cluster.yaml
   # Install containerd + Cilium CNI
   ```

2. **Phase 2 (Week 3)**: L3 orchestration + L5 observability baseline.
   ```bash
   # Deploy Prometheus + Grafana (kube-prometheus-stack)
   helm install kube-prometheus prometheus-community/kube-prometheus-stack
   # Enable audit logging on API server
   ```

3. **Phase 3 (Week 4)**: L4 service mesh (canary to 20% traffic).
   ```bash
   istioctl install --set profile=production
   kubectl label namespace prod istio-injection=enabled
   ```

4. **Phase 4 (Weeks 5-6)**: L6-L7 developer tooling + GitOps.
   ```bash
   # Argo CD
   kubectl create namespace argocd
   kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
   # OPA Gatekeeper
   kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/release-3.14/deploy/gatekeeper.yaml
   ```

**Rollback**: Keep previous CNI/mesh configs in Git; `kubectl apply -f previous/`. For L0-L1, maintain rescue kernel params in GRUB.

---

## **Next 3 Steps**

1. **Baseline L2 runtime security**: Deploy gVisor/Kata for untrusted workloads; profile seccomp with `oci-seccomp-bpf-hook`.
   ```bash
   git clone https://github.com/containers/oci-seccomp-bpf-hook
   # Generate profile, apply to RuntimeClass
   ```

2. **Instrument L5 observability**: Deploy OpenTelemetry collector + auto-instrumentation operator; trace 3 critical paths.
   ```bash
   kubectl apply -f https://github.com/open-telemetry/opentelemetry-operator/releases/latest/download/opentelemetry-operator.yaml
   ```

3. **Enforce L7 policies**: Write 5 Rego policies (no privileged, enforce limits, require mTLS); integrate with Gatekeeper + Argo CD pre-sync.
   ```bash
   kubectl apply -f opa-policies/gatekeeper-constraints.yaml
   argocd app set backend-prod --sync-option SkipDryRunOnMissingResource=true
   ```

---

## **References**

- CNCF Landscape: https://landscape.cncf.io
- Kubernetes Hardening Guide (NSA/CISA): https://media.defense.gov/2022/Aug/29/2003066362/-1/-1/0/CTR_KUBERNETES_HARDENING_GUIDANCE_1.2_20220829.PDF
- Cilium eBPF deep dive: https://docs.cilium.io/en/stable/concepts/ebpf/
- Istio security best practices: https://istio.io/latest/docs/ops/best-practices/security/
- OpenTelemetry specification: https://opentelemetry.io/docs/specs/otel/