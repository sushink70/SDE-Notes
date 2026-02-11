# Kubernetes Components: Comprehensive Security-First Deep Dive

**Summary:** Kubernetes is a distributed system with a control plane (API server, etcd, scheduler, controller-manager, cloud-controller-manager) managing cluster state and worker nodes (kubelet, kube-proxy, container runtime) executing workloads. The API server is the central security boundary—all operations flow through it via REST over mTLS. etcd holds all cluster state as the single source of truth. Scheduler assigns pods to nodes via complex filtering/scoring algorithms, controllers reconcile desired vs actual state, and kubelet manages pod lifecycle on nodes. Every component communicates via authenticated, authorized API calls. This architecture creates multiple isolation boundaries (network, process, filesystem, identity) that must be hardened for production. Security depends on: mTLS everywhere, RBAC on API server, etcd encryption at rest, admission control, runtime security (seccomp/AppArmor/SELinux), network policies, and comprehensive audit logging.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        CONTROL PLANE                             │
│  ┌──────────────┐  ┌──────────┐  ┌───────────┐  ┌────────────┐ │
│  │ kube-apiserver├─►│   etcd   │  │ scheduler │  │controller- │ │
│  │  (REST API)  │◄─┤(raftDB)  │  │           │  │  manager   │ │
│  │   :6443      │  │  :2379   │  │           │  │            │ │
│  └──────┬───────┘  └──────────┘  └─────┬─────┘  └──────┬─────┘ │
│         │ mTLS                          │ watch          │ watch│
└─────────┼───────────────────────────────┼────────────────┼──────┘
          │                               │                │
          │ TLS/auth                      ▼                ▼
          │                         ┌─────────────────────────┐
          │                         │  cloud-controller-mgr   │
          │                         │   (cloud provider)      │
          │                         └─────────────────────────┘
          │
    ┌─────┴──────────────────────────────────────────────┐
    │                  WORKER NODES                       │
    │  ┌────────────┐  ┌──────────┐  ┌────────────────┐ │
    │  │  kubelet   ├──┤container │  │  kube-proxy    │ │
    │  │  :10250    │  │ runtime  │  │  (iptables/    │ │
    │  │            │  │ (CRI)    │  │   IPVS/eBPF)   │ │
    │  └────┬───────┘  └────┬─────┘  └────────────────┘ │
    │       │               │                             │
    │       │           ┌───▼────┐                        │
    │       │           │  PODs  │                        │
    │       │           └────────┘                        │
    │       │ CNI plugin (network namespace)              │
    │       └──────────────────────────────────────────── │
    └─────────────────────────────────────────────────────┘

Security Boundaries:
═══════════════════
1. API Server (AuthN/AuthZ/Admission)
2. etcd (encrypted at rest + mTLS)
3. Node isolation (namespace, cgroups)
4. Pod isolation (network policies, seccomp)
5. Container runtime (user namespace, capabilities)
```

---

## 1. Control Plane Components

### 1.1 kube-apiserver

**Core Function:** Stateless HTTP/JSON REST API gateway; enforces AuthN/AuthZ/Admission; validates/mutates resources; persists to etcd.

**Under the Hood:**

- **Request Flow:**
  ```
  Client → TLS termination → Authentication → Authorization (RBAC) 
       → Admission Controllers (Mutating) → Validation 
       → Admission Controllers (Validating) → etcd write → Watch notification
  ```

- **Key Subsystems:**
  - **API Machinery:** Generic server framework (`k8s.io/apiserver`) handling versioned resources, conversion, defaulting
  - **Aggregation Layer:** Allows extending API via APIService (e.g., metrics-server)
  - **Watch Mechanism:** Long-lived HTTP connections using chunked encoding; clients get resource updates via bookmarks

**Security Deep Dive:**

```go
// Authentication chain (ordered):
1. X509 client certs (CN=username, O=groups)
2. Static token file (Bearer tokens)
3. Bootstrap tokens (for node join)
4. Service account tokens (JWT, audience-bound since 1.20)
5. OIDC (external IdP integration)
6. Webhook token auth (external validation)

// Authorization modes (--authorization-mode):
- Node: Restricts kubelet to its own node resources
- RBAC: Role/ClusterRole + RoleBinding/ClusterRoleBinding
- Webhook: External authz decision
- AlwaysAllow/AlwaysDeny: Testing only

// Admission Controllers (--enable-admission-plugins):
Critical for security:
- PodSecurityPolicy (deprecated 1.21, removed 1.25)
- PodSecurity (replacement, enforces pod security standards)
- NodeRestriction (limits node's kubelet to modify own node/pods)
- ResourceQuota, LimitRanger
- MutatingWebhookConfiguration, ValidatingWebhookConfiguration
```

**Critical Flags:**

```bash
# Production API server config
kube-apiserver \
  --advertise-address=10.0.0.1 \
  --secure-port=6443 \
  --etcd-servers=https://10.0.0.10:2379,https://10.0.0.11:2379,https://10.0.0.12:2379 \
  --etcd-cafile=/etc/kubernetes/pki/etcd/ca.crt \
  --etcd-certfile=/etc/kubernetes/pki/apiserver-etcd-client.crt \
  --etcd-keyfile=/etc/kubernetes/pki/apiserver-etcd-client.key \
  --client-ca-file=/etc/kubernetes/pki/ca.crt \
  --tls-cert-file=/etc/kubernetes/pki/apiserver.crt \
  --tls-private-key-file=/etc/kubernetes/pki/apiserver.key \
  --kubelet-client-certificate=/etc/kubernetes/pki/apiserver-kubelet-client.crt \
  --kubelet-client-key=/etc/kubernetes/pki/apiserver-kubelet-client.key \
  --service-account-key-file=/etc/kubernetes/pki/sa.pub \
  --service-account-signing-key-file=/etc/kubernetes/pki/sa.key \
  --service-account-issuer=https://kubernetes.default.svc.cluster.local \
  --authorization-mode=Node,RBAC \
  --enable-admission-plugins=NodeRestriction,PodSecurity \
  --audit-log-path=/var/log/kubernetes/audit.log \
  --audit-policy-file=/etc/kubernetes/audit-policy.yaml \
  --audit-log-maxage=30 \
  --audit-log-maxbackup=10 \
  --encryption-provider-config=/etc/kubernetes/encryption-config.yaml \
  --requestheader-client-ca-file=/etc/kubernetes/pki/front-proxy-ca.crt \
  --enable-bootstrap-token-auth=true \
  --anonymous-auth=false \
  --profiling=false
```

**Threat Model:**

| Threat | Mitigation |
|--------|-----------|
| Unauthorized API access | mTLS client certs, RBAC, deny anonymous |
| Privilege escalation | NodeRestriction admission, RBAC rules, audit logs |
| etcd compromise | Encrypt etcd at rest, network segmentation, mTLS |
| Admission webhook bypass | FailurePolicy=Fail, webhook timeout limits |
| API DoS | Rate limiting (--max-requests-inflight, --max-mutating-requests-inflight) |

**Verification:**

```bash
# Check API server health
curl -k https://localhost:6443/livez
curl -k https://localhost:6443/readyz

# Verify mTLS to etcd
openssl s_client -connect 10.0.0.10:2379 \
  -cert /etc/kubernetes/pki/apiserver-etcd-client.crt \
  -key /etc/kubernetes/pki/apiserver-etcd-client.key \
  -CAfile /etc/kubernetes/pki/etcd/ca.crt

# Audit log verification
tail -f /var/log/kubernetes/audit.log | jq '.verb, .objectRef, .user'

# Check admission plugins
kubectl get --raw /metrics | grep apiserver_admission_controller
```

---

### 1.2 etcd

**Core Function:** Distributed, strongly consistent key-value store (Raft consensus); single source of truth for cluster state.

**Under the Hood:**

- **Raft Consensus:** Leader election, log replication, committed writes visible to all followers
- **Storage:** BoltDB (B+tree) on disk, versioned keys (revision-based MVCC)
- **Watch:** Efficient change notifications via gRPC streams
- **Compaction:** Removes old revisions to reclaim space

**Data Layout:**

```
/registry/
├── pods/default/nginx-abc123
├── services/specs/default/nginx-svc
├── configmaps/kube-system/kubeadm-config
├── secrets/default/my-secret (encrypted if encryption-provider-config enabled)
└── events/...
```

**Security Configuration:**

```yaml
# /etc/etcd/etcd.yaml
name: etcd-1
data-dir: /var/lib/etcd
listen-peer-urls: https://10.0.0.10:2380
listen-client-urls: https://10.0.0.10:2379,https://127.0.0.1:2379
initial-advertise-peer-urls: https://10.0.0.10:2380
advertise-client-urls: https://10.0.0.10:2379

# TLS for peer communication (Raft)
peer-cert-file: /etc/kubernetes/pki/etcd/peer.crt
peer-key-file: /etc/kubernetes/pki/etcd/peer.key
peer-client-cert-auth: true
peer-trusted-ca-file: /etc/kubernetes/pki/etcd/ca.crt

# TLS for client communication
cert-file: /etc/kubernetes/pki/etcd/server.crt
key-file: /etc/kubernetes/pki/etcd/server.key
client-cert-auth: true
trusted-ca-file: /etc/kubernetes/pki/etcd/ca.crt

initial-cluster: etcd-1=https://10.0.0.10:2380,etcd-2=https://10.0.0.11:2380,etcd-3=https://10.0.0.12:2380
initial-cluster-state: new
initial-cluster-token: etcd-cluster-1

# Security hardening
auto-compaction-mode: periodic
auto-compaction-retention: "1h"
quota-backend-bytes: 8589934592  # 8GB
```

**Encryption at Rest (API Server Config):**

```yaml
# /etc/kubernetes/encryption-config.yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
      - configmaps
    providers:
      - aescbc:
          keys:
            - name: key1
              secret: <base64-encoded-32-byte-key>
      - identity: {}  # fallback for unencrypted data
```

**Threat Model:**

| Threat | Mitigation |
|--------|-----------|
| Unauthorized etcd access | mTLS client auth, firewall to API server only |
| Data exfiltration | Encrypt at rest, network isolation |
| Raft partition | Odd-numbered cluster (3/5/7 nodes), monitor quorum |
| Disk corruption | Automated backups, snapshot validation |
| Snapshot theft | Encrypt backups, secure storage (S3 with KMS) |

**Operations:**

```bash
# Backup etcd
ETCDCTL_API=3 etcdctl snapshot save /backup/etcd-snapshot-$(date +%Y%m%d-%H%M%S).db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Verify snapshot
ETCDCTL_API=3 etcdctl snapshot status /backup/etcd-snapshot.db -w table

# Restore (DESTRUCTIVE - test in staging first)
ETCDCTL_API=3 etcdctl snapshot restore /backup/etcd-snapshot.db \
  --data-dir=/var/lib/etcd-restore \
  --name etcd-1 \
  --initial-cluster etcd-1=https://10.0.0.10:2380 \
  --initial-advertise-peer-urls https://10.0.0.10:2380

# Check cluster health
ETCDCTL_API=3 etcdctl endpoint health \
  --endpoints=https://10.0.0.10:2379,https://10.0.0.11:2379,https://10.0.0.12:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Defragment (reduces disk usage)
ETCDCTL_API=3 etcdctl defrag \
  --endpoints=https://10.0.0.10:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key
```

---

### 1.3 kube-scheduler

**Core Function:** Assigns pods to nodes via filtering (feasibility) and scoring (optimization) algorithms.

**Scheduling Cycle:**

```
1. Watch API server for unscheduled pods (spec.nodeName == "")
2. Filtering: Eliminate nodes that don't meet requirements
   - PodFitsResources (CPU/memory)
   - PodFitsHostPorts
   - NodeSelector/NodeAffinity
   - Taints/Tolerations
   - Volume zone constraints
3. Scoring: Rank remaining nodes (0-100)
   - LeastAllocated (prefer nodes with more free resources)
   - BalancedResourceAllocation
   - ImageLocality (prefer nodes with image cached)
   - NodeAffinity weight
4. Bind: Update pod spec.nodeName via API server
```

**Advanced Scheduling:**

```yaml
# Pod with scheduling constraints
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  # Node affinity (hard requirement)
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: security-zone
                operator: In
                values: ["dmz", "trusted"]
      preferredDuringSchedulingIgnoredDuringExecution:
        - weight: 100
          preference:
            matchExpressions:
              - key: disk-type
                operator: In
                values: ["ssd"]
    # Pod anti-affinity (spread across nodes)
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        - labelSelector:
            matchLabels:
              app: secure-pod
          topologyKey: kubernetes.io/hostname
  # Toleration for tainted nodes
  tolerations:
    - key: "dedicated"
      operator: "Equal"
      value: "security"
      effect: "NoSchedule"
  # Topology spread
  topologySpreadConstraints:
    - maxSkew: 1
      topologyKey: topology.kubernetes.io/zone
      whenUnsatisfiable: DoNotSchedule
      labelSelector:
        matchLabels:
          app: secure-pod
  # Priority (preemption)
  priorityClassName: high-priority
  containers:
    - name: app
      image: secure-app:v1
      resources:
        requests:
          cpu: "1"
          memory: "2Gi"
        limits:
          cpu: "2"
          memory: "4Gi"
```

**Scheduler Configuration:**

```yaml
# /etc/kubernetes/scheduler-config.yaml
apiVersion: kubescheduler.config.k8s.io/v1
kind: KubeSchedulerConfiguration
profiles:
  - schedulerName: default-scheduler
    plugins:
      score:
        disabled:
          - name: NodeResourcesLeastAllocated
        enabled:
          - name: NodeResourcesBalancedAllocation
            weight: 1
      filter:
        enabled:
          - name: NodeResourcesFit
clientConnection:
  kubeconfig: /etc/kubernetes/scheduler.conf
```

**Threat Model:**

| Threat | Mitigation |
|--------|-----------|
| Pod placed on compromised node | Node isolation, taints, security zones |
| Resource exhaustion | ResourceQuota, LimitRange, PodPriority |
| Data locality violation | Topology constraints, volume affinity |
| Scheduler poisoning | RBAC (scheduler needs minimal write access) |

**Debugging:**

```bash
# Check scheduler events
kubectl get events --all-namespaces --field-selector reason=FailedScheduling

# Describe pod for scheduling details
kubectl describe pod <pod-name>

# Scheduler logs
kubectl logs -n kube-system kube-scheduler-<node>

# Metrics
kubectl get --raw /metrics | grep scheduler_
```

---

### 1.4 kube-controller-manager

**Core Function:** Runs control loops that reconcile cluster state (desired vs actual).

**Built-in Controllers (50+):**

1. **Node Controller:** Monitors node health, evicts pods from unhealthy nodes
2. **ReplicaSet Controller:** Maintains desired pod count
3. **Deployment Controller:** Manages ReplicaSets (rolling updates)
4. **StatefulSet Controller:** Manages stateful workloads (stable identity)
5. **Job Controller:** Runs batch jobs to completion
6. **CronJob Controller:** Scheduled jobs
7. **Service Controller:** Creates cloud load balancers (delegates to cloud-controller-manager)
8. **Endpoint/EndpointSlice Controller:** Populates service endpoints
9. **Namespace Controller:** Deletes resources when namespace is deleted
10. **ServiceAccount Controller:** Creates default ServiceAccount per namespace
11. **Token Controller:** Generates tokens for ServiceAccounts
12. **PersistentVolume Controller:** Binds PVCs to PVs
13. **ResourceQuota Controller:** Enforces quotas
14. **TTL Controller:** Cleans up finished Jobs

**Reconciliation Loop Pattern:**

```go
// Pseudo-code for a controller
func (c *Controller) Run() {
    for {
        // 1. Watch for changes
        event := c.watchQueue.Get()
        
        // 2. Get current state
        currentState := c.apiserver.Get(event.Key)
        
        // 3. Get desired state
        desiredState := event.Object.Spec
        
        // 4. Reconcile (idempotent)
        if currentState != desiredState {
            c.reconcile(currentState, desiredState)
        }
        
        // 5. Update status
        c.apiserver.UpdateStatus(event.Key, currentState)
    }
}
```

**Critical Flags:**

```bash
kube-controller-manager \
  --kubeconfig=/etc/kubernetes/controller-manager.conf \
  --authentication-kubeconfig=/etc/kubernetes/controller-manager.conf \
  --authorization-kubeconfig=/etc/kubernetes/controller-manager.conf \
  --bind-address=127.0.0.1 \
  --leader-elect=true \
  --cluster-signing-cert-file=/etc/kubernetes/pki/ca.crt \
  --cluster-signing-key-file=/etc/kubernetes/pki/ca.key \
  --service-account-private-key-file=/etc/kubernetes/pki/sa.key \
  --root-ca-file=/etc/kubernetes/pki/ca.crt \
  --use-service-account-credentials=true \
  --controllers=*,bootstrapsigner,tokencleaner \
  --node-monitor-period=5s \
  --node-monitor-grace-period=40s \
  --pod-eviction-timeout=5m \
  --terminated-pod-gc-threshold=12500
```

**Security Considerations:**

- **Principle of Least Privilege:** Each controller uses its own ServiceAccount with minimal RBAC
- **Leader Election:** Only one instance active (prevents split-brain)
- **Certificate Management:** Signs kubelet CSRs (TLS bootstrapping)

**Node Eviction Logic:**

```
Node conditions checked:
- Ready: False/Unknown
- MemoryPressure, DiskPressure, PIDPressure

Eviction process:
1. Mark node as NotReady (taints with NoSchedule, NoExecute)
2. Wait node-monitor-grace-period (40s default)
3. Start evicting pods (respects PodDisruptionBudget)
4. Terminate pods after pod-eviction-timeout (5m default)
```

---

### 1.5 cloud-controller-manager

**Core Function:** Integrates Kubernetes with cloud provider APIs (AWS, Azure, GCP, etc.).

**Controllers:**

1. **Node Controller:** Adds cloud metadata (zone, instance type, providerID)
2. **Route Controller:** Configures VPC routes for pod networking
3. **Service Controller:** Provisions cloud load balancers for type=LoadBalancer services

**Example: AWS Integration:**

```yaml
# Service creates ELB/NLB
apiVersion: v1
kind: Service
metadata:
  name: web-service
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-internal: "true"
    service.beta.kubernetes.io/aws-load-balancer-subnets: "subnet-abc,subnet-def"
spec:
  type: LoadBalancer
  selector:
    app: web
  ports:
    - port: 443
      targetPort: 8443
```

**Security:**

- Uses cloud IAM roles (e.g., IRSA on EKS, Workload Identity on GKE)
- Scoped permissions (ec2:DescribeInstances, elasticloadbalancing:*, ec2:CreateRoute)

---

## 2. Node Components

### 2.1 kubelet

**Core Function:** Pod lifecycle manager; runs on every node; ensures containers are running.

**Responsibilities:**

1. **Pod Sync:** Watches API server for pods assigned to this node
2. **Container Management:** Starts/stops containers via CRI
3. **Health Checks:** Liveness, readiness, startup probes
4. **Volume Management:** Mounts volumes via CSI
5. **Status Reporting:** Updates pod/node status to API server
6. **Resource Enforcement:** Enforces CPU/memory limits via cgroups
7. **Garbage Collection:** Removes dead containers/images

**Key Subsystems:**

```
kubelet
├── PLEG (Pod Lifecycle Event Generator): Detects container state changes
├── PodManager: In-memory cache of pod specs
├── VolumeManager: Mounts/unmounts volumes
├── ImageManager: Pulls/deletes images
├── StatusManager: Syncs pod status to API server
├── ProbeManager: Executes health probes
└── EvictionManager: Evicts pods on resource pressure
```

**Configuration:**

```yaml
# /var/lib/kubelet/config.yaml
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
authentication:
  anonymous:
    enabled: false
  webhook:
    enabled: true
  x509:
    clientCAFile: /etc/kubernetes/pki/ca.crt
authorization:
  mode: Webhook
clusterDomain: cluster.local
clusterDNS:
  - 10.96.0.10
cgroupDriver: systemd
containerRuntimeEndpoint: unix:///var/run/containerd/containerd.sock
resolvConf: /run/systemd/resolve/resolv.conf
rotateCertificates: true
serverTLSBootstrap: true
tlsCertFile: /var/lib/kubelet/pki/kubelet.crt
tlsPrivateKeyFile: /var/lib/kubelet/pki/kubelet.key

# Security hardening
protectKernelDefaults: true
makeIPTablesUtilChains: true
eventRecordQPS: 5
imageGCHighThresholdPercent: 85
imageGCLowThresholdPercent: 80
evictionHard:
  memory.available: "100Mi"
  nodefs.available: "10%"
  imagefs.available: "15%"
  nodefs.inodesFree: "5%"
evictionSoft:
  memory.available: "200Mi"
evictionSoftGracePeriod:
  memory.available: "1m30s"
```

**Static Pods:**

Kubelet can run pods from filesystem (without API server):

```yaml
# /etc/kubernetes/manifests/kube-apiserver.yaml
apiVersion: v1
kind: Pod
metadata:
  name: kube-apiserver
  namespace: kube-system
spec:
  hostNetwork: true
  containers:
    - name: kube-apiserver
      image: registry.k8s.io/kube-apiserver:v1.29.0
      command:
        - kube-apiserver
        - --advertise-address=10.0.0.1
        # ... more flags
```

**Security:**

```bash
# kubelet flags
kubelet \
  --config=/var/lib/kubelet/config.yaml \
  --kubeconfig=/etc/kubernetes/kubelet.conf \
  --bootstrap-kubeconfig=/etc/kubernetes/bootstrap-kubelet.conf \
  --cert-dir=/var/lib/kubelet/pki \
  --tls-cert-file=/var/lib/kubelet/pki/kubelet.crt \
  --tls-private-key-file=/var/lib/kubelet/pki/kubelet.key \
  --read-only-port=0 \
  --anonymous-auth=false \
  --authorization-mode=Webhook \
  --client-ca-file=/etc/kubernetes/pki/ca.crt \
  --feature-gates=RotateKubeletServerCertificate=true
```

**Threat Model:**

| Threat | Mitigation |
|--------|-----------|
| Unauthorized kubelet access | Disable anonymous auth, webhook authz, mTLS |
| Container escape | seccomp, AppArmor, SELinux, user namespaces |
| Host filesystem access | ReadOnlyRootFilesystem, no hostPath volumes |
| Privilege escalation | PodSecurityStandard, drop capabilities |
| Node resource exhaustion | ResourceQuota, LimitRange, eviction policies |

**Debugging:**

```bash
# kubelet logs
journalctl -u kubelet -f

# Check node conditions
kubectl describe node <node-name>

# kubelet API (requires auth)
curl -k --cert /var/lib/kubelet/pki/kubelet.crt \
        --key /var/lib/kubelet/pki/kubelet.key \
        https://localhost:10250/metrics

# cgroup inspection
systemd-cgls
systemd-cgtop
```

---

### 2.2 kube-proxy

**Core Function:** Manages network rules for Service abstraction; load balances traffic to pod endpoints.

**Modes:**

1. **iptables (default):** Creates iptables rules for NAT/load balancing
2. **IPVS:** Uses Linux IPVS for better performance at scale
3. **eBPF (Cilium, Calico):** Kernel-level packet processing

**iptables Mode Deep Dive:**

```bash
# Service: web-svc (ClusterIP: 10.96.100.50, port 80)
# Endpoints: 192.168.1.10:8080, 192.168.1.11:8080

# kube-proxy creates these iptables rules:
-A KUBE-SERVICES -d 10.96.100.50/32 -p tcp -m tcp --dport 80 -j KUBE-SVC-XXX

# Load balance to endpoints (round-robin via statistic module)
-A KUBE-SVC-XXX -m statistic --mode random --probability 0.5 -j KUBE-SEP-AAA
-A KUBE-SVC-XXX -j KUBE-SEP-BBB

# DNAT to pod IPs
-A KUBE-SEP-AAA -p tcp -m tcp -j DNAT --to-destination 192.168.1.10:8080
-A KUBE-SEP-BBB -p tcp -m tcp -j DNAT --to-destination 192.168.1.11:8080

# Mark for SNAT (return traffic)
-A KUBE-POSTROUTING -m mark --mark 0x4000/0x4000 -j MASQUERADE
```

**IPVS Mode (Better Performance):**

```bash
# Configuration
kube-proxy \
  --proxy-mode=ipvs \
  --ipvs-scheduler=rr \  # round-robin, lc (least connection), sh (source hash)
  --ipvs-sync-period=30s \
  --ipvs-min-sync-period=2s

# IPVS creates virtual servers:
ipvsadm -Ln
# IP Virtual Server version 1.2.1
# Prot LocalAddress:Port Scheduler Flags
#   -> RemoteAddress:Port           Forward Weight ActiveConn InActConn
# TCP  10.96.100.50:80 rr
#   -> 192.168.1.10:8080            Masq    1      0          0
#   -> 192.168.1.11:8080            Masq    1      0          0
```

**Security Considerations:**

- **Userspace mode (deprecated):** kube-proxy proxies connections (slow, but works in restricted environments)
- **Network Policies:** kube-proxy does NOT enforce NetworkPolicies (CNI plugin responsibility)
- **iptables rules:** Can grow to 10k+ rules in large clusters (O(n) lookups)

**Troubleshooting:**

```bash
# Check kube-proxy logs
kubectl logs -n kube-system kube-proxy-<node>

# Inspect iptables rules
iptables-save | grep KUBE

# IPVS rules
ipvsadm -Ln

# Connection tracking
conntrack -L | grep <service-ip>

# Debug Service connectivity
kubectl run -it --rm debug --image=nicolaka/netshoot --restart=Never -- bash
# Inside pod:
nslookup web-svc
curl http://web-svc
tcpdump -i any -nn port 80
```

---

### 2.3 Container Runtime

**Core Function:** Runs containers; implements CRI (Container Runtime Interface).

**Supported Runtimes:**

1. **containerd** (default): Lightweight, OCI-compliant
2. **CRI-O**: Kubernetes-optimized, OCI-compliant
3. **Docker Engine** (deprecated): Requires dockershim (removed in 1.24)

**containerd Architecture:**

```
kubelet (CRI client)
    |
    v
containerd (CRI plugin)
    |
    +-- containerd-shim (per container)
    |       |
    |       v
    |   runc (OCI runtime)
    |       |
    |       v
    |   container process (isolated)
    |
    +-- image service (pull/manage images)
    +-- snapshot service (overlay filesystem)
```

**Configuration:**

```toml
# /etc/containerd/config.toml
version = 2

[plugins."io.containerd.grpc.v1.cri"]
  sandbox_image = "registry.k8s.io/pause:3.9"
  
  [plugins."io.containerd.grpc.v1.cri".containerd]
    default_runtime_name = "runc"
    
    [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc]
      runtime_type = "io.containerd.runc.v2"
      
      [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]
        SystemdCgroup = true
        
    # gVisor (sandboxed runtime)
    [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runsc]
      runtime_type = "io.containerd.runsc.v1"

  [plugins."io.containerd.grpc.v1.cri".cni]
    bin_dir = "/opt/cni/bin"
    conf_dir = "/etc/cni/net.d"

[plugins."io.containerd.grpc.v1.cri".registry]
  [plugins."io.containerd.grpc.v1.cri".registry.mirrors]
    [plugins."io.containerd.grpc.v1.cri".registry.mirrors."docker.io"]
      endpoint = ["https://registry-1.docker.io"]
```

**Security Isolation Layers:**

```
┌────────────────────────────────────────┐
│         Container Process              │
│  (user namespace, PID 1 inside)        │
├────────────────────────────────────────┤
│         Capabilities (dropped)         │
│  (CAP_NET_RAW, CAP_SYS_ADMIN, etc.)   │
├────────────────────────────────────────┤
│         seccomp Profile                │
│  (syscall filtering)                   │
├────────────────────────────────────────┤
│         AppArmor/SELinux               │
│  (MAC policies)                        │
├────────────────────────────────────────┤
│         cgroups (resource limits)      │
│  (CPU, memory, PIDs)                   │
├────────────────────────────────────────┤
│         Namespaces                     │
│  (PID, NET, MNT, UTS, IPC, USER)      │
├────────────────────────────────────────┤
│         Kernel                         │
└────────────────────────────────────────┘
```

**Pod Security Context:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: security-hardened
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 3000
    fsGroup: 2000
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: app
      image: myapp:v1
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop:
            - ALL
          add:
            - NET_BIND_SERVICE
      volumeMounts:
        - name: tmp
          mountPath: /tmp
  volumes:
    - name: tmp
      emptyDir: {}
```

**RuntimeClass (Multi-Runtime):**

```yaml
# RuntimeClass for gVisor
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: gvisor
handler: runsc

---
# Pod using gVisor
apiVersion: v1
kind: Pod
metadata:
  name: sandboxed-pod
spec:
  runtimeClassName: gvisor
  containers:
    - name: app
      image: untrusted:v1
```

**Operations:**

```bash
# containerd CLI
ctr --namespace k8s.io containers list
ctr --namespace k8s.io images list
ctr --namespace k8s.io tasks ls

# crictl (CRI debugging tool)
crictl ps
crictl images
crictl logs <container-id>
crictl exec -it <container-id> sh
crictl inspect <container-id>

# Image pull
crictl pull docker.io/library/nginx:alpine

# Pod sandbox (pause container)
crictl pods
crictl inspectp <pod-id>
```

---

## 3. Add-on Components

### 3.1 CoreDNS

**Function:** Cluster DNS; resolves `service.namespace.svc.cluster.local`.

**Configuration:**

```yaml
# ConfigMap: coredns
apiVersion: v1
kind: ConfigMap
metadata:
  name: coredns
  namespace: kube-system
data:
  Corefile: |
    .:53 {
        errors
        health {
            lameduck 5s
        }
        ready
        kubernetes cluster.local in-addr.arpa ip6.arpa {
            pods insecure
            fallthrough in-addr.arpa ip6.arpa
            ttl 30
        }
        prometheus :9153
        forward . /etc/resolv.conf {
            max_concurrent 1000
        }
        cache 30
        loop
        reload
        loadbalance
    }
```

**DNS Resolution Path:**

```
Pod (app container)
  → /etc/resolv.conf (nameserver: 10.96.0.10)
    → CoreDNS service (10.96.0.10:53)
      → CoreDNS pods (queries etcd via API server)
        → Returns A record (e.g., web-svc.default.svc.cluster.local → 10.96.100.50)
```

---

### 3.2 CNI (Container Network Interface)

**Function:** Pod networking; assigns IP addresses, sets up network namespaces.

**Popular CNI Plugins:**

1. **Calico:** L3 networking, NetworkPolicy enforcement, BGP/VXLAN
2. **Cilium:** eBPF-based, fast, observability, NetworkPolicy
3. **Flannel:** Simple overlay (VXLAN), no NetworkPolicy
4. **Weave:** Mesh networking, encryption

**CNI Configuration:**

```json
// /etc/cni/net.d/10-calico.conflist
{
  "name": "k8s-pod-network",
  "cniVersion": "0.3.1",
  "plugins": [
    {
      "type": "calico",
      "log_level": "info",
      "datastore_type": "kubernetes",
      "nodename": "node1",
      "ipam": {
        "type": "calico-ipam",
        "assign_ipv4": "true",
        "assign_ipv6": "false"
      },
      "policy": {
        "type": "k8s"
      },
      "kubernetes": {
        "kubeconfig": "/etc/cni/net.d/calico-kubeconfig"
      }
    },
    {
      "type": "portmap",
      "capabilities": {"portMappings": true}
    }
  ]
}
```

---

## 4. Communication Patterns

```
┌─────────────────────────────────────────────────────┐
│                API Server (Hub)                     │
│         All traffic goes through here               │
└─────────────┬───────────────────────┬───────────────┘
              │                       │
       ┌──────▼──────┐         ┌──────▼──────┐
       │   etcd      │         │  Controllers│
       │  (write)    │         │   (watch)   │
       └─────────────┘         └─────────────┘
              │                       │
       ┌──────▼──────┐         ┌──────▼──────┐
       │  Scheduler  │         │   kubelet   │
       │   (watch)   │         │   (watch)   │
       └─────────────┘         └─────────────┘

Key protocols:
- API server ↔ etcd: gRPC over mTLS (port 2379)
- Client ↔ API server: HTTPS/JSON (port 6443)
- API server → kubelet: HTTPS (port 10250)
- Controllers/Scheduler → API server: HTTPS (watch streams)
```

---

## 5. Testing & Validation

```bash
# 1. Cluster smoke test
kubectl cluster-info
kubectl get nodes
kubectl get pods -A

# 2. Component health
kubectl get componentstatuses  # deprecated but useful

# 3. API server health
curl -k https://localhost:6443/healthz
curl -k https://localhost:6443/livez
curl -k https://localhost:6443/readyz

# 4. etcd health
ETCDCTL_API=3 etcdctl endpoint health --cluster

# 5. Network connectivity
kubectl run test-pod --image=nicolaka/netshoot --rm -it -- bash
# Inside: ping 8.8.8.8, nslookup kubernetes.default, curl https://kubernetes.default

# 6. RBAC validation
kubectl auth can-i create pods --as=system:serviceaccount:default:default

# 7. Audit log check
tail -f /var/log/kubernetes/audit.log | jq .

# 8. Performance baseline
kubectl run perf --image=nginx --restart=Never
kubectl delete pod perf
# Measure time to Running state
```

---

## 6. Production Rollout Plan

**Phase 1: Pre-deployment**
1. Set up HA control plane (3 masters, 3 etcd nodes)
2. Configure mTLS for all components
3. Enable etcd encryption at rest
4. Set up audit logging with remote backend
5. Configure RBAC policies (deny-by-default)

**Phase 2: Deployment**
1. Deploy control plane components (kubeadm/kops/kubespray)
2. Validate certificates (check expiry: `kubeadm certs check-expiration`)
3. Join worker nodes with TLS bootstrapping
4. Deploy CNI (Calico with NetworkPolicy)

**Phase 3: Hardening**
1. Enable PodSecurity admission (enforce restricted)
2. Configure resource quotas per namespace
3. Set up monitoring (Prometheus, Grafana)
4. Deploy Falco for runtime security

**Phase 4: Validation**
1. Run CIS Benchmark (`kube-bench`)
2. Penetration testing (`kube-hunter`)
3. Chaos engineering (litmus, chaos-mesh)

**Rollback Plan:**
- etcd snapshot before changes
- Control plane component version pinning
- Node cordoning before updates
- PodDisruptionBudget for workloads

---

## 7. Threat Model Summary

| Asset | Threat | Control |
|-------|--------|---------|
| API server | Unauthorized access | mTLS, RBAC, audit logs |
| etcd | Data exfiltration | Encryption at rest, network isolation |
| kubelet | Container escape | seccomp, AppArmor, user namespaces |
| Pods | Lateral movement | NetworkPolicy, RBAC, service mesh (mTLS) |
| Secrets | Exposure | Encryption at rest, external secrets (Vault) |
| Images | Supply chain attack | Image signing (Notary, Cosign), admission webhooks |

---

## 8. References

1. **Kubernetes Architecture:** https://kubernetes.io/docs/concepts/architecture/
2. **Component Reference:** https://kubernetes.io/docs/reference/command-line-tools-reference/
3. **CIS Kubernetes Benchmark:** https://www.cisecurity.org/benchmark/kubernetes
4. **kube-bench (CIS):** https://github.com/aquasecurity/kube-bench
5. **Kubernetes Security Best Practices:** https://kubernetes.io/docs/concepts/security/
6. **etcd Documentation:** https://etcd.io/docs/
7. **containerd:** https://containerd.io/
8. **Cilium (eBPF CNI):** https://cilium.io/
9. **Falco (Runtime Security):** https://falco.org/
10. **CNCF Landscape:** https://landscape.cncf.io/

---

## Next 3 Steps

1. **Deploy a 3-node cluster:** Use kubeadm on bare-metal/VMs with full mTLS, encryption at rest, and audit logging enabled. Validate with `kube-bench`.

2. **Trace a request end-to-end:** `kubectl create pod` → API server (AuthN/AuthZ/Admission) → etcd write → scheduler watch → bind → kubelet watch → containerd → pod running. Use `--v=8` flag for debug logs.

3. **Implement NetworkPolicy enforcement:** Deploy Calico, create deny-all default policy, whitelist specific traffic. Test with `netshoot` pod and `tcpdump` to verify isolation.