## Summary

I'll provide a comprehensive, first-principles guide to Kubernetes pods, containers, clusters, and the entire orchestration stack—covering scheduling, networking, storage, security boundaries, control plane architecture, container runtimes, and observability. This spans from hardware/kernel primitives (cgroups, namespaces, seccomp) through CNI/CSI/CRI interfaces, up to application-layer constructs like DaemonSets, StatefulSets, and custom resources. I'll include threat models, isolation boundaries, production trade-offs, and security-first design patterns for each layer.

This is a deep, end-to-end reference for building and securing cloud-native systems at scale.

---

## Table of Contents

1. **Foundational Container Primitives** (Linux kernel, namespaces, cgroups, capabilities, seccomp, AppArmor/SELinux)
2. **Container Runtimes & Standards** (OCI, containerd, CRI-O, runc, gVisor, Kata, Firecracker)
3. **Pod Architecture & Lifecycle** (pause container, init containers, sidecars, ephemeral containers, QoS classes)
4. **Kubernetes Cluster Architecture** (control plane, etcd, API server, scheduler, controller-manager, kubelet, kube-proxy)
5. **Workload Resources** (Deployments, StatefulSets, DaemonSets, Jobs, CronJobs, ReplicaSets)
6. **Networking Deep-Dive** (CNI, pod networking model, Services, Ingress, NetworkPolicy, eBPF-based CNIs, service mesh)
7. **Storage Architecture** (CSI, Volumes, PersistentVolumes, PersistentVolumeClaims, StorageClasses, ephemeral volumes)
8. **Scheduling & Resource Management** (node affinity, taints/tolerations, resource requests/limits, PodDisruptionBudgets, topology spread)
9. **Security Boundaries & Threat Model** (RBAC, Pod Security Standards, secrets management, runtime security, supply chain, multi-tenancy)
10. **Observability & Instrumentation** (metrics, logs, traces, eBPF, Prometheus, Jaeger, OpenTelemetry)
11. **Custom Resources & Operators** (CRDs, controllers, operator pattern, webhooks)
12. **Multi-Cluster & Federation** (cluster API, multi-cluster services, GitOps, disaster recovery)
13. **Production Readiness Checklist** (HA, backups, upgrades, chaos engineering, capacity planning)
14. **References & Next Steps**

---

## 1. Foundational Container Primitives

### Linux Kernel Isolation Mechanisms

**Namespaces** (process isolation):
- **PID**: process tree isolation
- **NET**: network stack isolation (interfaces, routing tables, firewall rules)
- **MNT**: filesystem mount points
- **UTS**: hostname/domainname
- **IPC**: System V IPC, POSIX message queues
- **USER**: UID/GID mappings (rootless containers)
- **Cgroup**: cgroup hierarchy view
- **Time**: system clocks (Linux 5.6+)

**Cgroups** (resource limits):
- v1: separate hierarchies per resource controller (cpu, memory, blkio, pids)
- v2: unified hierarchy, better resource delegation, pressure stall information (PSI)
- Controllers: cpu, memory, io, pids, rdma, hugetlb

**Capabilities** (privilege separation):
- Break root into 40+ fine-grained privileges (CAP_NET_ADMIN, CAP_SYS_ADMIN, etc.)
- Drop unnecessary caps to minimize attack surface

**Seccomp-BPF** (syscall filtering):
- Whitelist allowed syscalls (default Docker profile blocks ~300/330 syscalls)
- Seccomp notifier for logging/policy enforcement

**LSM (Linux Security Modules)**:
- **AppArmor**: path-based MAC, easier policy syntax
- **SELinux**: label-based MAC, finer-grained, type enforcement
- **Landlock**: unprivileged sandboxing (5.13+)

### Threat Model
- **Privilege escalation**: capabilities, user namespaces, setuid binaries
- **Kernel exploits**: shared kernel, vulnerable syscalls (use gVisor/Kata for stronger isolation)
- **Resource exhaustion**: cgroup limits, fork bombs, memory bombs
- **Information disclosure**: /proc, /sys pseudo-filesystems

### Mitigations
1. Drop all capabilities except required ones
2. Read-only root filesystem
3. No privileged mode
4. Seccomp profile (RuntimeDefault or custom)
5. User namespaces for rootless
6. AppArmor/SELinux mandatory profiles
7. Kernel runtime integrity (IMA/EVM)

---

## 2. Container Runtimes & Standards

### OCI (Open Container Initiative) Specifications

**Image Spec**: layered filesystem, manifest, config JSON
**Runtime Spec**: config.json (namespaces, cgroups, mounts, hooks, seccomp, caps)
**Distribution Spec**: registry protocol (push/pull)

### Runtime Hierarchy

```
Kubernetes CRI (Container Runtime Interface)
         |
         v
+--------+--------+--------+
|        |        |        |
containerd  CRI-O  Docker  |
    |        |       |     |
    v        v       v     v
  runc    crun   runc  Kata/gVisor/Firecracker
    |        |       |
    +--------+-------+
            |
        Linux Kernel (namespaces, cgroups, seccomp)
```

### Runtime Comparison

| Runtime | Isolation | Overhead | Use Case |
|---------|-----------|----------|----------|
| **runc** | Linux namespaces | ~10MB RAM/container | Standard workloads |
| **crun** | Linux namespaces | ~3MB RAM, 2x faster startup | Resource-constrained |
| **gVisor (runsc)** | User-space kernel | ~15-30% CPU, +50MB RAM | Untrusted code, multi-tenant |
| **Kata Containers** | Lightweight VM (KVM/Firecracker) | +130MB RAM, VM boot time | Strong isolation, legacy apps |
| **Firecracker** | microVM (KVM) | +5MB RAM, <125ms boot | Serverless, multi-tenant |

### Threat Model
- **Container escape**: kernel vulnerabilities, privileged mode, volume mounts
- **Supply chain**: malicious images, vulnerable base images, typosquatting
- **Registry compromise**: unsigned images, MITM attacks

### Mitigations
1. Image signing & verification (cosign, Notary v2)
2. Vulnerability scanning (Trivy, Clair, Grype)
3. Distroless/minimal base images
4. Multi-stage builds (separate build/runtime)
5. Read-only root filesystem
6. Drop all capabilities
7. Use gVisor/Kata for untrusted workloads
8. Private registry with authentication
9. Image pull policies (Always, IfNotPresent)
10. Admission controllers (ImagePolicyWebhook, Kyverno, OPA Gatekeeper)

---

## 3. Pod Architecture & Lifecycle

### Pod Definition

A **Pod** is the smallest deployable unit in Kubernetes—one or more containers sharing:
- Network namespace (IP address, localhost)
- IPC namespace
- UTS namespace (hostname)
- PID namespace (optional, `shareProcessNamespace: true`)
- Volumes

### Pause Container

Every pod has an "infrastructure" container (pause/sandbox) that:
1. Holds the network namespace
2. Reaps zombie processes (PID 1)
3. Keeps pod alive if all containers crash

```bash
# View pause container
docker ps | grep pause
# Or with crictl
sudo crictl ps | grep pause
```

### Container Types in a Pod

```
┌─────────────────────────────────────────────────────┐
│                       Pod                           │
│                                                     │
│  ┌──────────────┐  ┌──────────────┐               │
│  │ Init Container│  │ Init Container│               │
│  │  (run in seq) │─>│  (run in seq) │               │
│  └──────────────┘  └──────────────┘               │
│           │                                         │
│           v                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────┐  │
│  │   Main App   │  │   Sidecar    │  │ Sidecar │  │
│  │  Container   │  │  (logging)   │  │ (proxy) │  │
│  └──────────────┘  └──────────────┘  └─────────┘  │
│                                                     │
│  Ephemeral Container (debug, no restart)           │
│                                                     │
│  Shared: Network, IPC, Volumes                     │
└─────────────────────────────────────────────────────┘
```

**Init Containers**:
- Run sequentially before main containers
- Must complete successfully
- Use cases: DB schema migrations, config fetching, wait for dependencies

**Sidecar Containers** (native in 1.29+):
- Run alongside main container
- Use cases: logging agents (Fluent Bit), service mesh proxies (Envoy), secret rotation

**Ephemeral Containers**:
- Added to running pod for debugging
- Cannot be restarted, no resource guarantees
- Use: `kubectl debug`

### Pod Lifecycle Phases

1. **Pending**: accepted by cluster, waiting for scheduling/image pull
2. **Running**: at least one container running
3. **Succeeded**: all containers terminated successfully (exit 0)
4. **Failed**: at least one container failed (non-zero exit)
5. **Unknown**: state cannot be determined (node communication failure)

### Container States
- **Waiting**: pulling image, waiting for init containers
- **Running**: executing
- **Terminated**: exited (check exit code, reason)

## Summary

This guide covers the complete Kubernetes and container orchestration ecosystem from first principles: containers (namespaces, cgroups, runtimes), pods (init/sidecar/ephemeral patterns, lifecycle), workload controllers (Deployments, StatefulSets, DaemonSets, Jobs), cluster architecture (control plane components, data plane, networking models), storage abstractions (volumes, PVs, CSI), networking (CNI, Services, Ingress, NetworkPolicy), security primitives (RBAC, PSS/PSA, OPA, admission control), observability (metrics/logs/traces), scheduling/resource management, and multi-tenancy/isolation boundaries. This is production-grade knowledge for building secure, scalable cloud-native systems with defense-in-depth at every layer.

---

## 1. Container Fundamentals

### Linux Kernel Primitives
- **Namespaces**: Isolation boundaries for processes—PID (process tree), NET (network stack), MNT (filesystem), UTS (hostname), IPC (message queues), USER (UID/GID mapping), Cgroup (control group hierarchy), Time (clock isolation in 5.6+)
- **Cgroups (Control Groups)**: Resource limiting/accounting—CPU shares/quotas, memory limits/OOM behavior, block I/O throttling, network priority, device access control
- **Capabilities**: Fine-grained privilege decomposition—CAP_NET_ADMIN, CAP_SYS_ADMIN, CAP_CHOWN, etc., reducing need for full root
- **Seccomp (Secure Computing Mode)**: Syscall filtering—whitelist/blacklist syscalls, reduce attack surface
- **AppArmor/SELinux**: Mandatory Access Control (MAC)—label-based security policies, file/network/process restrictions
- **Copy-on-Write Filesystems**: Layered image storage—UnionFS, OverlayFS, AUFS for efficient image management

### Container Runtimes
- **High-level runtimes**: containerd, CRI-O—manage image pull, container lifecycle, implement CRI (Container Runtime Interface)
- **Low-level runtimes**: runc, crun, runsc (gVisor), kata-runtime (Kata Containers), firecracker-containerd—OCI (Open Container Initiative) spec compliance, execute containers
- **OCI Specifications**: runtime-spec (config.json, execution), image-spec (manifest, layers, config), distribution-spec (registry API)
- **Image Format**: Layers (tar.gz), manifest (JSON metadata), config (entrypoint, env, user), digest-based addressing (SHA256)
- **Image Registry**: Distribution protocol, content-addressable storage, signature verification (Notary, cosign), vulnerability scanning

### Container Security
- **Root vs Rootless**: UID 0 inside container vs user namespaces, privilege escalation risks
- **Read-only Root Filesystem**: Immutable container images, writable volumes only where needed
- **Non-root User**: Run as UID > 0, principle of least privilege
- **Drop Capabilities**: Remove unnecessary Linux capabilities
- **Seccomp Profiles**: Custom syscall filters, default Docker/Kubernetes profiles
- **Image Scanning**: Trivy, Clair, Anchore—CVE detection, SBOM (Software Bill of Materials)
- **Image Signing**: Verify provenance, chain of custody, supply chain security

---

## 2. Pods: Atomic Unit of Deployment

### Pod Composition
- **Pod Definition**: One or more containers sharing namespaces (NET, IPC, UTS), storage volumes, lifecycle
- **Pause Container**: Infrastructure container holding namespaces, other containers join its namespaces
- **Shared Resources**: Localhost networking (127.0.0.1), shared volumes, shared IPC
- **Pod IP**: Single IP per pod, containers communicate via localhost:<port>

### Container Types in Pods
- **Init Containers**: Sequential execution before app containers, setup/preconditions, run to completion, failures block pod startup
- **App Containers**: Main workload containers, parallel startup after init containers succeed
- **Sidecar Containers**: Helper containers (logging agents, proxies, service mesh), lifecycle tied to app container
- **Ephemeral Containers**: Debug containers injected at runtime, no restart policy, no resource guarantees, for troubleshooting live pods

### Pod Lifecycle
- **Phases**: Pending (scheduling), Running (at least one container running), Succeeded (all completed), Failed (at least one failed), Unknown (lost communication)
- **Container States**: Waiting (pulling image, backoff), Running (started successfully), Terminated (completed or crashed)
- **Restart Policy**: Always (default for Deployments), OnFailure (for Jobs), Never (for one-shot tasks)
- **Termination Graceful Shutdown**: SIGTERM signal, grace period (default 30s), preStop hook, SIGKILL after grace period

### Pod Patterns
- **Sidecar Pattern**: Log shipper, metrics exporter, service mesh proxy (Envoy)
- **Ambassador Pattern**: Proxy to external services, connection pooling, circuit breaking
- **Adapter Pattern**: Normalize data formats, protocol translation, legacy integration
- **Init Pattern**: Database migrations, secret fetching, dependency checks

### Pod Security Context
- **Pod-level Security**: runAsUser, runAsGroup, fsGroup, supplementalGroups, seccompProfile, seLinuxOptions
- **Container-level Security**: Overrides pod-level settings, allowPrivilegeEscalation, readOnlyRootFilesystem, capabilities, privileged flag
- **Volume Security**: fsGroup applies group ownership to mounted volumes, UID/GID mapping

---

## 3. Workload Controllers

### ReplicaSet
- **Purpose**: Maintain desired replica count, self-healing, pod template
- **Label Selectors**: Match pods by labels, declarative pod ownership
- **Not Directly Used**: Deployments manage ReplicaSets, rarely created manually

### Deployment
- **Declarative Updates**: Rolling updates, rollback capability, revision history
- **Strategies**: RollingUpdate (default—maxUnavailable, maxSurge), Recreate (all-at-once)
- **Rollout Management**: Pause/resume, history, rollback to specific revision
- **Progressive Delivery**: Blue-green via Services, canary with multiple Deployments/weighted routing

### StatefulSet
- **Stable Identity**: Ordered pod names (app-0, app-1), persistent hostname/DNS
- **Stable Storage**: PVC per pod, survives pod rescheduling
- **Ordered Operations**: Sequential creation/deletion, rolling updates with partitions
- **Headless Service**: Direct pod DNS (app-0.service.namespace.svc.cluster.local)
- **Use Cases**: Databases, distributed systems (etcd, Kafka, Cassandra), leader election

### DaemonSet
- **Node Coverage**: One pod per node (or subset via nodeSelector/affinity)
- **Update Strategies**: RollingUpdate, OnDelete (manual trigger)
- **Use Cases**: Logging agents (fluentd), monitoring (node-exporter), CNI plugins, storage daemons

### Job
- **Batch Workloads**: Run to completion, exit code 0 = success
- **Parallelism**: Completions (total successes needed), parallelism (concurrent pods)
- **Backoff**: Exponential backoff on failure, backoffLimit (max retries)
- **TTL**: Automatic cleanup after completion (ttlSecondsAfterFinished)

### CronJob
- **Scheduled Jobs**: Cron syntax, timezone support
- **Concurrency**: Allow, Forbid, Replace policies
- **Job Retention**: successfulJobsHistoryLimit, failedJobsHistoryLimit

---

## 4. Cluster Architecture

### Control Plane Components
- **kube-apiserver**: RESTful API gateway, authentication/authorization, admission control, etcd frontend, horizontal scaling (stateless)
- **etcd**: Distributed key-value store, Raft consensus, control plane data persistence, watch mechanism for controllers
- **kube-scheduler**: Pod placement decisions—node affinity, taints/tolerations, resource requests, custom schedulers
- **kube-controller-manager**: Reconciliation loops—ReplicaSet, Deployment, StatefulSet, Node, ServiceAccount, PV controllers
- **cloud-controller-manager**: Cloud-specific controllers—node lifecycle, LoadBalancer services, persistent volumes

### Data Plane (Worker Nodes)
- **kubelet**: Node agent, pod lifecycle management, reports node/pod status, CRI client, volume mounts, liveness/readiness probes
- **kube-proxy**: Network proxy, Service abstraction via iptables/IPVS/eBPF, ClusterIP load balancing
- **Container Runtime**: containerd, CRI-O—container execution, image management

### Add-ons (Cluster-level Services)
- **DNS**: CoreDNS—service discovery, pod DNS, external DNS resolution
- **Ingress Controller**: nginx, Traefik, Envoy Gateway—L7 routing, TLS termination
- **Metrics Server**: Resource metrics for HPA (Horizontal Pod Autoscaler), kubectl top
- **Dashboard**: Web UI (use caution, often over-privileged)
- **Cluster Autoscaler**: Node provisioning based on pending pods
- **Storage Provisioners**: Dynamic PV creation via CSI drivers

### API Resources and Extensions
- **Built-in Resources**: Pods, Services, ConfigMaps, Secrets, Deployments, etc.
- **Custom Resources (CR)**: Extend API with CRDs (CustomResourceDefinitions)
- **Operators**: Controllers for CRs—declarative automation, day-2 ops (backup, upgrade)
- **Aggregation Layer**: Extend apiserver with custom API servers (metrics-server)

---

## 5. Networking

### Network Model
- **Flat Network**: All pods can communicate without NAT, each pod has unique IP
- **Requirements**: Pod-to-pod across nodes, node-to-pod, external-to-Service
- **CNI (Container Network Interface)**: Plugin spec for network setup—Calico, Cilium, Flannel, Weave, Multus

### Pod Networking
- **Pod IP Assignment**: CNI plugin allocates IP from pod CIDR, single IP per pod
- **Network Namespaces**: Each pod in its own netns, veth pair connects to host/overlay
- **Overlay Networks**: VXLAN, IPsec tunnels—encapsulate pod traffic across nodes
- **BGP Routing**: Calico, Cilium—advertise pod CIDRs to physical routers, no encapsulation

### Services
- **ClusterIP**: Virtual IP, internal load balancing, kube-proxy rules (iptables/IPVS), DNS name (service.namespace.svc.cluster.local)
- **NodePort**: Expose on all nodes, port range 30000-32767, external traffic entry
- **LoadBalancer**: Cloud provider LB, external IP, integrates with AWS ELB, GCP GLB, Azure LB
- **ExternalName**: CNAME DNS alias, no proxying
- **Headless Service**: ClusterIP=None, returns pod IPs directly, for StatefulSets

### Service Mesh
- **Data Plane**: Envoy/Linkerd proxies, intercept pod traffic, L7 routing, retries, circuit breaking
- **Control Plane**: Istio Pilot, Linkerd controller—push config to proxies, service discovery
- **mTLS**: Automatic certificate issuance, encrypted pod-to-pod communication
- **Observability**: Distributed tracing, golden metrics (latency, traffic, errors, saturation)
- **Traffic Management**: Canary, A/B testing, traffic shifting, fault injection

### Ingress
- **L7 Routing**: Host/path-based routing, TLS termination, single external IP
- **Ingress Controller**: nginx, Traefik, HAProxy, Envoy Gateway—implements Ingress resource
- **Gateway API**: Next-gen Ingress, role-based (GatewayClass, Gateway, HTTPRoute), more expressive

### NetworkPolicy
- **Pod Segmentation**: L3/L4 firewall rules, ingress/egress, pod/namespace/CIDR selectors
- **Default Deny**: Explicitly allow traffic, zero-trust networking
- **CNI Support**: Calico, Cilium, Weave—not all CNIs enforce NetworkPolicy

### DNS
- **CoreDNS**: Cluster DNS server, service discovery (service.namespace.svc.cluster.local), pod DNS (pod-ip.namespace.pod.cluster.local)
- **DNS Policy**: ClusterFirst (default), Default (node DNS), None (custom), ClusterFirstWithHostNet

---

## 6. Storage

### Volumes
- **emptyDir**: Temporary storage, pod-scoped, survives container restart, deleted on pod deletion
- **hostPath**: Mount host filesystem, node-specific, breaks pod portability, security risk
- **configMap/secret**: Inject config/secrets as files, read-only by default
- **persistentVolumeClaim**: Request persistent storage, dynamic provisioning

### Persistent Volumes (PV)
- **Lifecycle**: Static provisioning (admin creates PV), dynamic provisioning (StorageClass auto-creates)
- **Access Modes**: ReadWriteOnce (RWO—single node), ReadOnlyMany (ROX—multiple nodes read), ReadWriteMany (RWX—multiple nodes write), ReadWriteOncePod (RWOP—single pod)
- **Reclaim Policy**: Retain (manual cleanup), Delete (auto-delete backing storage), Recycle (deprecated)
- **Volume Binding**: Immediate (bind at PVC creation), WaitForFirstConsumer (bind at pod scheduling, topology-aware)

### Persistent Volume Claims (PVC)
- **Request**: Size, access mode, StorageClass
- **Binding**: 1:1 PVC-to-PV relationship, remains bound until PVC deleted

### StorageClass
- **Dynamic Provisioning**: Defines provisioner (CSI driver), parameters (type, IOPS, replication)
- **Parameters**: Cloud-specific (AWS EBS gp3, Azure Premium SSD, GCP PD-SSD)
- **Default StorageClass**: Used if PVC doesn't specify StorageClass

### CSI (Container Storage Interface)
- **Plugin Architecture**: Node plugin (mount/unmount), controller plugin (provision/delete), identity service
- **Drivers**: AWS EBS CSI, GCE PD CSI, Azure Disk CSI, Ceph CSI, Longhorn, OpenEBS
- **Features**: Snapshots, cloning, expansion, topology-aware scheduling

### Volume Snapshots
- **VolumeSnapshot**: Point-in-time copy, CSI support required
- **VolumeSnapshotClass**: Define snapshot provider, parameters
- **Restore**: Create PVC from snapshot

---

## 7. Configuration and Secrets

### ConfigMaps
- **Use Cases**: Non-sensitive config, feature flags, environment-specific settings
- **Consumption**: Environment variables, command-line args, volume mounts
- **Immutable**: Optional immutability for performance/safety
- **Size Limit**: 1MB per ConfigMap

### Secrets
- **Types**: Opaque (arbitrary data), kubernetes.io/service-account-token, kubernetes.io/dockerconfigjson (image pull), TLS certs
- **Base64 Encoding**: Not encryption, only obfuscation in YAML
- **Consumption**: Environment variables (risky—visible in pod spec), volume mounts (tmpfs, in-memory)
- **Encryption at Rest**: etcd encryption, KMS provider (AWS KMS, Azure Key Vault, GCP KMS), envelope encryption
- **External Secrets**: External Secrets Operator, Vault Agent Injector—sync from Vault, AWS Secrets Manager, etc.

### Service Accounts
- **Identity**: Pod identity for API access, token auto-mounted at /var/run/secrets/kubernetes.io/serviceaccount
- **RBAC Binding**: Role/ClusterRole define permissions, RoleBinding/ClusterRoleBinding grant to ServiceAccount
- **Token Projection**: Audience, expiration, rotation—BoundServiceAccountTokenVolume feature

---

## 8. Security

### Authentication
- **Client Certificates**: X.509 certs, CN=username, O=group
- **Bearer Tokens**: ServiceAccount tokens (JWT), static tokens, bootstrap tokens
- **OIDC**: External IdP (Okta, Auth0, Google), group claims
- **Webhook**: Delegate authn to external service
- **Anonymous Requests**: Often disabled, allows unauthenticated access

### Authorization
- **RBAC (Role-Based Access Control)**: Standard authz mode
  - **Role/ClusterRole**: Define permissions (verbs: get, list, watch, create, update, patch, delete; resources: pods, services, configmaps)
  - **RoleBinding/ClusterRoleBinding**: Grant Role/ClusterRole to subjects (User, Group, ServiceAccount)
  - **Namespace-scoped**: Role/RoleBinding (within namespace)
  - **Cluster-scoped**: ClusterRole/ClusterRoleBinding (all namespaces, cluster-level resources)
- **ABAC (Attribute-Based)**: Legacy, policy file
- **Node Authz**: Restricts kubelet API access to own node resources
- **Webhook**: External authz service (OPA, Kyverno)

### Admission Control
- **Mutating Admission**: Modify requests—inject sidecar, set default values, image pull secrets
- **Validating Admission**: Accept/reject requests—enforce naming conventions, require labels, deny privileged pods
- **Built-in Controllers**: PodSecurityPolicy (deprecated), LimitRanger, ResourceQuota, PodSecurityAdmission
- **Dynamic Admission**: Webhooks—MutatingWebhookConfiguration, ValidatingWebhookConfiguration
- **Policy Engines**: OPA/Gatekeeper (Rego), Kyverno (YAML), Kubewarden (WebAssembly)

### Pod Security Standards (PSS)
- **Baseline**: Minimal restrictions, prevent privilege escalation, host access
- **Restricted**: Hardened, drop all capabilities, read-only root filesystem, non-root user
- **Privileged**: Unrestricted, for trusted workloads (CNI plugins, storage drivers)

### Pod Security Admission (PSA)
- **Namespace Labels**: Enforcement modes—enforce, audit, warn
- **Version Pinning**: pod-security.kubernetes.io/enforce-version

### Network Security
- **NetworkPolicy**: Pod-to-pod micro-segmentation, default deny
- **Service Mesh mTLS**: Encrypted pod-to-pod, certificate rotation, identity-based authz
- **Egress Control**: Restrict outbound traffic, prevent data exfiltration

### Image Security
- **Private Registries**: ImagePullSecrets, service account default secrets
- **Admission Controllers**: ImagePolicyWebhook, validate signatures (Notary, cosign)
- **Vulnerability Scanning**: Trivy, Anchore, Clair—CI/CD integration, runtime scanning

### Runtime Security
- **Falco**: Runtime threat detection, syscall monitoring, anomaly detection
- **Seccomp/AppArmor**: Mandatory profiles via pod annotations
- **gVisor/Kata Containers**: Stronger isolation, syscall interception, nested virtualization
- **eBPF**: Kernel observability, network policies (Cilium), runtime enforcement

### Secrets Management
- **etcd Encryption**: EncryptionConfiguration, KMS provider integration
- **External Secrets**: Vault, AWS Secrets Manager, Azure Key Vault, GCP Secret Manager
- **Secret Rotation**: Short-lived tokens, projected ServiceAccount tokens, cert-manager

### Supply Chain Security
- **SBOM**: Software Bill of Materials, vulnerability tracking
- **Image Signing**: cosign, Notary—verify provenance
- **Admission Policies**: Require signed images, check signatures on admission
- **SLSA**: Supply-chain Levels for Software Artifacts framework

---

## 9. Scheduling and Resource Management

### Scheduling
- **Default Scheduler**: Score nodes, filter predicates, priorities
- **Node Affinity**: Required/preferred rules, label selectors, node topology
- **Pod Affinity/Anti-affinity**: Co-locate or separate pods, topologyKey (hostname, zone)
- **Taints and Tolerations**: Repel pods from nodes, NoSchedule, PreferNoSchedule, NoExecute
- **Node Selectors**: Simple label-based node selection
- **Topology Spread Constraints**: Even distribution across zones/nodes, skew limits

### Resource Requests and Limits
- **Requests**: Minimum resources guaranteed, scheduling decision, CPU/memory
- **Limits**: Maximum resources allowed, throttling (CPU), OOMKill (memory)
- **QoS Classes**: Guaranteed (requests=limits), Burstable (requests<limits), BestEffort (no requests/limits)
- **Eviction**: Node pressure (memory, disk, PID), evict BestEffort first, then Burstable

### Resource Quotas
- **Namespace-scoped**: Limit total resources, object counts (pods, services, PVCs)
- **Types**: CPU, memory, storage, object counts, extended resources (GPUs)

### LimitRanges
- **Default Requests/Limits**: Per-container defaults, min/max constraints
- **Validation**: Enforce limits at admission time

### Priority and Preemption
- **PriorityClass**: Numeric priority, higher evicts lower
- **Preemption**: Evict lower-priority pods to schedule high-priority pods
- **System-critical Pods**: High priority, guaranteed scheduling

### Autoscaling
- **Horizontal Pod Autoscaler (HPA)**: Scale replicas based on metrics (CPU, memory, custom)
- **Vertical Pod Autoscaler (VPA)**: Adjust requests/limits, restart pods
- **Cluster Autoscaler**: Add/remove nodes based on pending pods, cloud provider integration

---

## 10. Observability

### Metrics
- **Metrics Server**: Resource metrics (CPU, memory), kubectl top, HPA
- **Prometheus**: TSDB, scrape metrics endpoints, ServiceMonitor (Prometheus Operator)
- **Node Exporter**: Host-level metrics (CPU, disk, network)
- **kube-state-metrics**: Kubernetes object state (pod status, deployments, jobs)
- **cAdvisor**: Container metrics, built into kubelet

### Logging
- **Node-level**: Application logs to stdout/stderr, kubelet captures
- **Cluster-level Logging**: DaemonSet log shippers (fluentd, fluent-bit, Promtail)
- **Log Aggregation**: Elasticsearch, Loki, CloudWatch Logs, Splunk
- **Structured Logging**: JSON logs, log levels, context (trace IDs)

### Tracing
- **Distributed Tracing**: OpenTelemetry, Jaeger, Zipkin
- **Spans**: Trace request through services, latency breakdown, error tracking
- **Service Mesh Integration**: Automatic trace headers, Envoy telemetry

### Events
- **Kubernetes Events**: Object lifecycle (pod scheduled, container started, OOMKilled)
- **Event Retention**: Short-lived (1h default), event exporter for long-term storage

### Probes
- **Liveness Probe**: Restart unhealthy containers, HTTP, TCP, exec
- **Readiness Probe**: Remove from Service endpoints, don't send traffic if not ready
- **Startup Probe**: Delay liveness/readiness for slow-starting containers

---

## 11. Multi-tenancy and Isolation

### Namespace Isolation
- **Soft Multi-tenancy**: Trust boundary, RBAC, ResourceQuota, NetworkPolicy
- **Limitations**: Shared kernel, node-level resources, cluster-scoped resources

### Hard Multi-tenancy
- **Virtual Clusters**: vCluster, Kamaji—nested Kubernetes, separate control planes
- **Cluster API**: Manage multiple clusters as Kubernetes resources
- **Separate Clusters**: Strongest isolation, operational overhead

### Hierarchical Namespaces
- **HNC (Hierarchical Namespace Controller)**: Namespace inheritance, policy propagation

### Policy Enforcement
- **Gatekeeper**: OPA-based, ConstraintTemplates, audit mode
- **Kyverno**: YAML policies, generate/mutate/validate, policy reports

### Tenant Isolation Strategies
- **RBAC**: Restrict API access per tenant
- **NetworkPolicy**: Pod-to-pod isolation
- **ResourceQuota**: Prevent resource exhaustion
- **PodSecurityPolicy/PSA**: Enforce security baselines
- **Node Pools**: Dedicated nodes per tenant, taints/tolerations

---

## 12. GitOps and Declarative Management

### GitOps Principles
- **Git as Source of Truth**: Cluster state in Git, version control, audit trail
- **Automated Sync**: Continuous reconciliation, detect drift, auto-heal
- **Tools**: Argo CD, Flux, Jenkins X

### Declarative Configuration
- **Kubernetes Manifests**: YAML/JSON, apply vs create, server-side apply
- **Kustomize**: Overlays, patches, bases—DRY config, environment-specific
- **Helm**: Templating, package manager, values.yaml, chart repositories

### CI/CD Integration
- **Build**: Container image build, vulnerability scanning, signing
- **Test**: Unit, integration, end-to-end in ephemeral clusters
- **Deploy**: Rolling updates, canary, blue-green via GitOps sync

---

## 13. Cluster Federation and Multi-cluster

### Cluster Federation
- **KubeFed**: Federated resources, sync across clusters, global policy
- **Use Cases**: Multi-region HA, disaster recovery, workload placement

### Service Mesh Federation
- **Istio Multi-primary**: Shared control plane across clusters, east-west traffic
- **Linkerd Multi-cluster**: Service mirroring, cross-cluster service discovery

### Multi-cluster Ingress
- **Global Load Balancing**: GCLB (GCP), Route53 (AWS), Traffic Manager (Azure)
- **Submariner**: Cross-cluster pod/service connectivity, secure tunnels

---

## 14. Backup and Disaster Recovery

### etcd Backup
- **Snapshot**: etcdctl snapshot save, critical for cluster state
- **Restore**: etcdctl snapshot restore, new cluster recovery

### Application Backup
- **Velero**: Backup/restore Kubernetes resources, PV snapshots, disaster recovery
- **Hooks**: Pre/post-backup scripts, application-consistent snapshots

### Disaster Recovery
- **RTO/RPO**: Define recovery objectives, test failover procedures
- **Multi-region**: Active-active, active-passive, geo-replication

---

## 15. Advanced Topics

### Custom Controllers and Operators
- **Controller Pattern**: Watch-reconcile loop, level-triggered
- **Operator Framework**: Helm-based, Go-based (kubebuilder, operator-sdk), Ansible-based
- **Day-2 Operations**: Backup, upgrade, scaling, self-healing

### Cluster API
- **Infrastructure as Code**: Provision Kubernetes clusters via Kubernetes APIs
- **Providers**: AWS, Azure, GCP, vSphere, bare-metal

### Extended Resources
- **GPUs**: nvidia.com/gpu, device plugins, GPU scheduling
- **FPGAs, Infiniband**: Custom resources, specialized workloads

### Kubelet API
- **Metrics Endpoint**: /metrics/resource, /metrics/cadvisor
- **Logs Endpoint**: /logs, node-level log access
- **Exec/Attach**: kubectl exec backend, WebSocket/SPDY

### API Priority and Fairness
- **FlowSchema**: Request classification, priority levels
- **Admission Control**: Prevent API server overload, QoS for API requests

### Pod Overhead
- **RuntimeClass**: Define overhead (CPU, memory) for runtime (gVisor, Kata)
- **Accurate Accounting**: Include sidecar/pause container overhead in scheduling

### PodDisruptionBudget (PDB)
- **Voluntary Disruptions**: Node drain, upgrades
- **Availability Guarantees**: minAvailable, maxUnavailable

---

## Next 3 Steps

1. **Map your current infrastructure to these concepts**: Identify which workload controllers, networking patterns, and security primitives your production systems use—document the architecture, label resources, and trace request flows end-to-end to understand where isolation boundaries, authentication, and encryption occur.

2. **Build a threat model for your clusters**: For each layer (node, network, pod, control plane), enumerate threats (privilege escalation, lateral movement, data exfiltration, supply chain compromise), map existing controls (RBAC, NetworkPolicy, PSS, image scanning), and identify gaps requiring additional defense-in-depth measures.

3. **Establish observability and incident response baselines**: Instrument critical workloads with metrics/logs/traces, define SLIs/SLOs, test failure scenarios (pod eviction, node loss, zone outage), and document runbooks for common incidents—this prepares you for production operations and systematic troubleshooting.