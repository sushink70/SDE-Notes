# Kubernetes Orchestration Internals: Comprehensive Technical Reference Core Components & Control Flow

**RFC-style technical deep-dive for cloud security engineers**

---

## 1. OVERVIEW

Kubernetes is a declarative, eventually-consistent orchestration system that reconciles desired state (manifests) with observed cluster state through a control loop architecture. The control plane manages scheduling, health, and lifecycle; the data plane executes workloads. Security boundaries exist between components, namespaces, nodes, and networks.

**Key principle**: All state lives in etcd; controllers watch etcd and reconcile reality toward intent.

---

## 2. ARCHITECTURE: CONTROL PLANE & DATA PLANE

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CONTROL PLANE                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  kube-api    │  │  kube-        │  │  kube-       │             │
│  │  server      │  │  controller-  │  │  scheduler   │             │
│  │              │  │  manager      │  │              │             │
│  │ - Auth/Authz │  │ - Replication │  │ - Pod        │             │
│  │ - Admission  │  │ - Namespace   │  │   placement  │             │
│  │ - Validation │  │ - Service     │  │ - Affinity   │             │
│  │ - API GW     │  │ - Endpoint    │  │ - Taints     │             │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
│         │                  │                  │                     │
│         └──────────────────┼──────────────────┘                     │
│                            │                                        │
│                    ┌───────▼────────┐                               │
│                    │     etcd       │                               │
│                    │ (distributed   │                               │
│                    │  key-value     │                               │
│                    │  store)        │                               │
│                    └────────────────┘                               │
└─────────────────────────────────────────────────────────────────────┘
                             │
                 ┌───────────┼───────────┐
                 │           │           │
        ┌────────▼──────┐ ┌──▼───────────▼──┐ ┌────────────────┐
        │   NODE 1      │ │   NODE 2        │ │   NODE N       │
        │ ┌───────────┐ │ │ ┌─────────────┐ │ │ ┌────────────┐ │
        │ │  kubelet  │ │ │ │   kubelet   │ │ │ │  kubelet   │ │
        │ │           │ │ │ │             │ │ │ │            │ │
        │ └─────┬─────┘ │ │ └──────┬──────┘ │ │ └──────┬─────┘ │
        │       │       │ │        │        │ │        │       │
        │ ┌─────▼─────┐ │ │ ┌──────▼──────┐ │ │ ┌──────▼─────┐ │
        │ │ Container │ │ │ │  Container  │ │ │ │ Container  │ │
        │ │  Runtime  │ │ │ │   Runtime   │ │ │ │  Runtime   │ │
        │ │ (containerd│ │ │ │(containerd) │ │ │ │(containerd)│ │
        │ │  /cri-o)  │ │ │ │             │ │ │ │            │ │
        │ └───────────┘ │ │ └─────────────┘ │ │ └────────────┘ │
        │               │ │                 │ │                │
        │ ┌───────────┐ │ │ ┌─────────────┐ │ │ ┌────────────┐ │
        │ │ kube-proxy│ │ │ │ kube-proxy  │ │ │ │ kube-proxy │ │
        │ │ (iptables/│ │ │ │             │ │ │ │            │ │
        │ │  ipvs)    │ │ │ │             │ │ │ │            │ │
        │ └───────────┘ │ │ └─────────────┘ │ │ └────────────┘ │
        └───────────────┘ └─────────────────┘ └────────────────┘
                DATA PLANE (Worker Nodes)
```

---

## 3. CORE COMPONENTS

### 3.1 kube-apiserver
**Role**: Frontend to the control plane; only component that talks to etcd directly.

**Responsibilities**:
- **Authentication**: Verifies identity (client certs, bearer tokens, OIDC, webhook)
- **Authorization**: RBAC, ABAC, Node, Webhook authorizers check permissions
- **Admission Control**: Mutating + Validating webhooks enforce policy (PodSecurityPolicy, OPA/Gatekeeper, image validation)
- **API Gateway**: RESTful API for CRUD on resources
- **Watch mechanism**: Long-lived HTTP connections stream resource changes to controllers/kubelet
- **Aggregation layer**: Extends API with custom resources (CRDs, API services)

**Security characteristics**:
- Single point of failure for control plane; compromise = cluster takeover
- All communication must be mTLS (client certs or ServiceAccount tokens)
- Audit logs track every API call (who, what, when, result)
- Rate limiting prevents DoS on etcd
- Admission webhooks are inline; malicious webhook = cluster DoS

**Data flow**:
```
Client → TLS handshake → Authn → Authz → Admission (mutate) 
     → Validation → Admission (validate) → etcd write → Watch notify
```

---

### 3.2 etcd
**Role**: Strongly consistent, distributed key-value store; source of truth for cluster state.

**Characteristics**:
- Raft consensus protocol (leader election, log replication)
- Snapshot + WAL for durability
- All Kubernetes objects stored as protobuf or JSON
- Watches enable reactive controllers
- Typical cluster: 3 or 5 nodes for quorum (tolerates N/2-1 failures)

**Security characteristics**:
- **Encryption at rest**: Mandatory for secrets; kube-apiserver encrypts before write
- **Encryption in transit**: mTLS between etcd peers and apiserver
- **No direct access**: Only apiserver talks to etcd; compromise of etcd = full cluster data leak (secrets, tokens, configs)
- **Backup/DR**: etcd snapshots contain all secrets; must be encrypted and access-controlled
- **Audit**: etcd has own audit log; correlate with apiserver audit

**Threat model**:
- Attacker with etcd read access reads all secrets, ServiceAccount tokens, TLS keys
- Attacker with etcd write access modifies any resource (privilege escalation)
- Network partition → split brain if quorum misconfigured

---

### 3.3 kube-scheduler
**Role**: Watches unscheduled Pods; assigns them to Nodes based on constraints, resources, affinity.

**Scheduling phases**:
1. **Filtering**: Eliminates Nodes that don't meet Pod requirements (resources, taints, node selectors, affinity)
2. **Scoring**: Ranks remaining Nodes (spread, resource balance, custom priorities)
3. **Binding**: Writes Pod.Spec.NodeName to apiserver

**Inputs**:
- Pod resource requests (CPU, memory, ephemeral storage)
- Node capacity and allocatable resources
- Taints/tolerations, node/pod affinity/anti-affinity
- PriorityClasses for preemption
- Custom scheduler extenders or scheduling framework plugins

**Security characteristics**:
- Scheduler has cluster-wide read on Nodes/Pods; write on Pod bindings
- Malicious scheduler can starve workloads, co-locate sensitive Pods (side-channel), place Pods on compromised Nodes
- No direct secret access, but influences placement (e.g., node with GPU vs. public internet access)
- PriorityClass preemption can be abused for DoS

**Failure modes**:
- Scheduler crash: Pods stuck in Pending; no new scheduling
- Scheduler deadlock: Infinite loop on unsatisfiable constraints
- Resource fragmentation: Poor scoring leads to suboptimal packing

---

### 3.4 kube-controller-manager
**Role**: Bundles multiple controllers; each watches a resource type and reconciles state.

**Key controllers**:

| Controller | Watches | Reconciles | Security Impact |
|------------|---------|------------|-----------------|
| **Replication** | ReplicaSet, Deployment | Creates/deletes Pods to match desired count | Can spawn malicious Pods if RS compromised |
| **Namespace** | Namespace | Deletes all objects in terminating namespaces | Bulk deletion → DoS; orphaned objects if buggy |
| **ServiceAccount** | ServiceAccount | Creates default SA + token Secret per namespace | Token compromise = namespace access |
| **Node** | Node | Marks Nodes ready/not-ready; evicts Pods on failure | False eviction → workload disruption |
| **Endpoint** | Service, Pod | Populates Service endpoints with Pod IPs | Incorrect endpoints → traffic to wrong Pods |
| **PersistentVolume** | PVC, PV | Binds PVCs to PVs; reclaims volumes | Data leak if volume rebound incorrectly |
| **CertificateSigningRequest** | CSR | Auto-approves kubelet client certs (if enabled) | Auto-approval abuse → rogue Node |

**Security characteristics**:
- Controllers run with high privileges (often cluster-admin equivalent)
- Controller compromise = ability to create/modify arbitrary resources
- Controllers are reconciliation loops; watch → compare → act → repeat
- Each controller maintains a work queue; rate limiting prevents apiserver overload
- Controllers don't see secrets directly unless needed (e.g., SA controller creates token Secrets)

**Failure modes**:
- Controller crash: Stale state (e.g., Pods not cleaned up after RS deletion)
- Split-brain: Two controller-manager instances running (leader election prevents this)
- Watch stall: Missed events → drift between desired and actual state

---

### 3.5 kubelet
**Role**: Node agent; ensures containers run as specified in Pod manifests.

**Responsibilities**:
- Watches apiserver for Pods assigned to its Node
- Calls container runtime (via CRI) to create/stop containers
- Mounts volumes (via CSI plugins)
- Reports Node/Pod status to apiserver
- Runs liveness/readiness/startup probes
- Handles pod lifecycle hooks (postStart, preStop)
- Evicts Pods on resource pressure
- Static Pods: Reads manifests from local filesystem (e.g., for control plane Pods)

**Security characteristics**:
- Kubelet has Node-level privileges; compromise = host compromise
- Kubelet cert/token authenticates to apiserver; stolen creds allow Pod creation on that Node
- Kubelet API (port 10250) exposes exec/logs/portforward; must be authenticated (--anonymous-auth=false, --authorization-mode=Webhook)
- Static Pods bypass admission control (critical for control plane but risky if abused)
- Volume mounts can escape container (hostPath); kubelet enforces admission policies
- Kubelet reads Secrets/ConfigMaps to mount into Pods; in-memory only, not disk-cached (unless tmpfs misconfigured)

**Data flow**:
```
apiserver (Pod assigned to Node) → kubelet watch 
  → kubelet calls CRI (RunPodSandbox, CreateContainer, StartContainer)
  → container runtime (containerd/cri-o) creates namespace, cgroup, mounts
  → kubelet calls CSI to mount volumes
  → kubelet starts container
  → kubelet monitors container (probes, resource usage)
  → kubelet reports status to apiserver
```

**Failure modes**:
- Kubelet crash: Containers keep running but no new Pods scheduled; no status updates
- CRI failure: Cannot start containers; Pods stuck in ContainerCreating
- Volume mount failure: Pod stuck in Pending (e.g., CSI driver unavailable)
- PLEG (Pod Lifecycle Event Generator) stall: Kubelet thinks Pods are running when they're not

---

### 3.6 kube-proxy
**Role**: Implements Service abstraction; programs network rules to load-balance traffic to Pods.

**Modes**:
- **iptables**: Creates iptables rules for each Service; DNAT to Pod IPs (default, low overhead)
- **ipvs**: Uses IPVS kernel module; better performance for large clusters
- **userspace**: Legacy; kube-proxy itself proxies traffic (deprecated)

**Responsibilities**:
- Watches Services and Endpoints
- Programs NAT rules: ClusterIP → Pod IPs (round-robin or session affinity)
- Handles NodePort, LoadBalancer, ExternalName Services
- Source IP preservation (externalTrafficPolicy: Local)

**Security characteristics**:
- kube-proxy has cluster-wide read on Services/Endpoints
- No authentication/authorization on Service traffic (network-level)
- iptables rules run in kernel; kube-proxy compromise → traffic interception, redirection
- IPTables complexity → accidental rule conflicts (e.g., with network policies)
- NodePort exposes ports on all Nodes; firewall misconfiguration → external exposure

**Failure modes**:
- kube-proxy crash: Existing rules stay; no updates for new Services → traffic blackhole
- iptables rule limit: 1000s of Services → rule explosion → latency spikes
- Endpoint churn: Rapid Pod restarts → iptables rule flapping

---

### 3.7 Container Runtime (CRI)
**Role**: Executes containers; provides isolation, resource limits, image pulling.

**Components**:
- **containerd** (CNCF): Most common; calls runc for OCI container creation
- **CRI-O**: Lightweight, Kubernetes-native runtime
- **Docker** (deprecated): Used dockershim (removed in 1.24)

**CRI interface**:
- **RuntimeService**: RunPodSandbox, CreateContainer, StartContainer, StopContainer, RemoveContainer
- **ImageService**: PullImage, RemoveImage, ImageStatus

**Security characteristics**:
- Container runtime runs as root; compromise = host escape
- Image pull: Authenticates to registry (imagePullSecrets); verifies signatures (if enforced)
- Namespaces: PID, network, IPC, UTS, mount isolation (user namespaces optional)
- Cgroups: CPU, memory, I/O limits
- Seccomp, AppArmor, SELinux profiles enforce syscall/capability restrictions
- RuntimeClass: Allows different runtimes per Pod (e.g., gVisor, Kata for sandboxing)

**Threat model**:
- Malicious image → arbitrary code in container
- Container escape → kernel exploit, misconfigured volume mount
- Shared kernel → side-channel attacks, resource contention
- Registry compromise → supply chain attack (poison images)

---

## 4. REQUEST FLOW: POD CREATION

```
1. User: kubectl apply -f pod.yaml
   ↓
2. kubectl → kube-apiserver (HTTPS, client cert or token)
   ↓
3. kube-apiserver: Authentication
   - Validate cert/token
   - Resolve user/group
   ↓
4. kube-apiserver: Authorization (RBAC)
   - Check user has "create" on "pods" in namespace
   ↓
5. kube-apiserver: Mutating Admission
   - Webhook: Add default limits, inject sidecars
   - PodPreset: Inject env vars, volumes
   ↓
6. kube-apiserver: Schema Validation
   - Ensure required fields present, types correct
   ↓
7. kube-apiserver: Validating Admission
   - Webhook: Check image signature, policy compliance
   - PodSecurityPolicy: Enforce seccomp, runAsNonRoot
   ↓
8. kube-apiserver → etcd: Write Pod object (status: Pending)
   ↓
9. etcd → kube-apiserver: Ack
   ↓
10. kube-apiserver → kubectl: HTTP 201 Created
   ↓
11. kube-scheduler (watching Pods with no Node):
    - Filter Nodes (resources, taints, affinity)
    - Score Nodes
    - Bind: Set Pod.Spec.NodeName → node-1
   ↓
12. kube-apiserver → etcd: Update Pod (nodeName: node-1)
   ↓
13. kubelet on node-1 (watching Pods for its Node):
    - See new Pod assigned
    - Pull image (if not cached)
    - Create Pod sandbox (network namespace)
    - Call CRI: CreateContainer, StartContainer
   ↓
14. Container runtime (containerd):
    - runc creates namespaces, cgroups
    - Mount volumes (call CSI plugins)
    - Start container process
   ↓
15. kubelet: Run probes (startup, liveness, readiness)
   ↓
16. kubelet → kube-apiserver: Update Pod status (phase: Running, conditions: Ready)
   ↓
17. Endpoint controller (watching Pods):
    - If Pod has labels matching a Service, add Pod IP to Endpoints
   ↓
18. kube-proxy (watching Endpoints):
    - Program iptables/ipvs rules for Service → Pod IP
   ↓
19. Traffic to Service ClusterIP → iptables DNAT → Pod IP
```

---

## 5. WATCH MECHANISM & EVENTUAL CONSISTENCY

### 5.1 Watch Protocol
- Controllers/kubelet open long-lived HTTP connections to apiserver: `GET /api/v1/pods?watch=true`
- apiserver streams events: `ADDED`, `MODIFIED`, `DELETED` (JSON or protobuf)
- Clients maintain resourceVersion; resume from last seen version on reconnect
- Watch timeout (~5-10min); client must re-establish

### 5.2 Reconciliation Loop
```
Controller loop:
  1. Watch resource (e.g., Deployment)
  2. On event (ADDED/MODIFIED):
     - Read current state from cache (local)
     - Read desired state from object spec
     - Compare: delta = desired - current
     - If delta ≠ 0:
       - Take action (create/update/delete resources)
       - Update object status
  3. Requeue for periodic resync (30s - 10m)
```

**Implications**:
- **Eventual consistency**: State changes propagate asynchronously; temporary drift is normal
- **Level-triggered**: Controllers act on current state, not just events (idempotent)
- **Conflict resolution**: Optimistic concurrency (resourceVersion); retry on conflict
- **Watch stalls**: Network issue, apiserver restart → missed events; controllers resync periodically

---

## 6. SECURITY MODEL

### 6.1 Authentication
**Methods**:
- **Client certs**: X.509 cert with CN=username, O=groups; signed by cluster CA
- **ServiceAccount tokens**: JWT signed by apiserver; mounted into Pods at `/var/run/secrets/kubernetes.io/serviceaccount/token`
- **OIDC**: Delegate to external IDP (Google, Azure AD); apiserver validates JWT
- **Webhook**: External service validates token
- **Static token file** (deprecated): Plain text file; insecure

**ServiceAccount token flow**:
```
1. Pod starts
2. kubelet mounts projected volume with token (auto-rotated by 1.22+)
3. App reads token from file
4. App → apiserver with "Authorization: Bearer <token>"
5. apiserver validates JWT signature + expiry
6. apiserver maps token to SA (namespace + name)
7. RBAC check: SA permissions
```

**Threat model**:
- Stolen client cert → impersonate user until cert revoked (no revocation mechanism in K8s)
- ServiceAccount token leak → namespace access; rotate by deleting Secret
- OIDC token replay → use short TTL (1h); enable token binding

### 6.2 Authorization (RBAC)
**Resources**:
- **Role**: Namespace-scoped permissions
- **ClusterRole**: Cluster-scoped or namespace-scoped (reusable)
- **RoleBinding**: Binds Role to users/groups/SAs in a namespace
- **ClusterRoleBinding**: Binds ClusterRole at cluster level

**Example**:
```
Role: "pod-reader" in namespace "prod"
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list", "watch"]

RoleBinding: "jane-pod-reader" in namespace "prod"
  - subjects: [{kind: User, name: "jane"}]
  - roleRef: {kind: Role, name: "pod-reader"}
```

**Privilege escalation**:
- User with `create` on `rolebindings` + `bind` on a ClusterRole → grant self cluster-admin
- User with `patch` on `pods/ephemeralcontainers` → exec into privileged container
- User with `create` on `pods` in kube-system → create Pod with hostPath to `/etc/kubernetes` → steal certs

**Defense**:
- Limit `escalate` and `bind` verbs to trusted users
- Use Pod Security Standards (restricted profile) to prevent privileged Pods
- Audit RBAC changes

### 6.3 Admission Control
**Phases**:
1. **Mutating**: Modify object before persistence (add defaults, inject sidecars)
2. **Validating**: Accept/reject based on policy (image signature, resource limits)

**Built-in controllers**:
- **PodSecurity**: Enforce Pod Security Standards (privileged, baseline, restricted)
- **LimitRanger**: Enforce min/max resource requests per Pod/container
- **ResourceQuota**: Enforce aggregate limits per namespace
- **AlwaysPullImages**: Force imagePullPolicy=Always (prevent local image tampering)

**Dynamic admission webhooks**:
- External HTTPS service; apiserver calls on every create/update
- Must respond <30s (configurable); timeout = fail-open or fail-closed
- Mutating: Return JSON patch
- Validating: Return allowed=true/false + reason

**Threat model**:
- Malicious mutating webhook → inject backdoor sidecar into every Pod
- Slow webhook → DoS cluster (all creates block)
- Webhook SSRF → access internal services (webhook runs in apiserver network context)
- Bypass: User with `admissionregistration.k8s.io` permissions can delete/modify webhooks

### 6.4 Network Policies
**Model**: Default allow; NetworkPolicy objects define ingress/egress rules.

**Example**:
```
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
  namespace: prod
spec:
  podSelector: {}
  policyTypes: ["Ingress", "Egress"]
```
→ Deny all traffic to/from Pods in `prod` namespace.

**Implementation**: CNI plugin (Calico, Cilium, Weave) programs iptables/eBPF rules.

**Limitations**:
- No L7 filtering (use service mesh for HTTP path-based rules)
- DNS traffic often allowed by default (egress to kube-dns)
- No encryption enforcement (use mTLS via service mesh)
- Can't restrict traffic between Nodes (use host firewall)

**Threat model**:
- Missing NetworkPolicy → lateral movement after Pod compromise
- Overly permissive policy (e.g., allow all egress) → data exfiltration
- CNI bug → policy not enforced

### 6.5 Secrets Management
**Storage**:
- Secrets stored in etcd (base64 encoded, not encrypted by default)
- Enable encryption at rest: EncryptionConfiguration with KMS provider (AWS KMS, Vault)

**Access**:
- Secrets mounted as files or env vars in Pods
- Only Pods in same namespace can access (RBAC enforced)
- kubelet fetches Secrets from apiserver; caches in memory (not disk)

**Threat model**:
- etcd backup leak → all secrets exposed
- User with `get secrets` in namespace → read passwords, tokens
- Process dump of Pod → extract secrets from env vars
- Secret mounted as volume → accessible to all containers in Pod

**Best practices**:
- External secret store (Vault, AWS Secrets Manager) + CSI driver
- Use ServiceAccount token projection (short-lived, auto-rotated)
- Encrypt etcd backups
- Audit secret access

### 6.6 Pod Security Standards
**Profiles** (enforced via PodSecurity admission):
- **Privileged**: Unrestricted; allows hostPath, privileged containers, host network
- **Baseline**: Minimally restrictive; blocks known privilege escalations (no privileged, no hostPath, no hostNetwork)
- **Restricted**: Hardened; requires runAsNonRoot, drops all capabilities, read-only rootfs, seccomp/AppArmor

**Example**:
```
Namespace label: pod-security.kubernetes.io/enforce: restricted
→ All Pods in namespace must meet restricted profile
```

**Threat model**:
- Privileged Pod → container escape via kernel exploit
- hostPath mount → read/write host filesystem
- hostNetwork → sniff Node traffic, bind privileged ports
- CAP_SYS_ADMIN → mount arbitrary filesystems, ptrace other processes

---

## 7. FAILURE MODES & RESILIENCE

| Component | Failure | Impact | Mitigation |
|-----------|---------|--------|------------|
| **kube-apiserver** | Crash | Control plane down; no API access | HA: 3+ instances + load balancer |
| **etcd** | Leader failure | Cluster elects new leader (<1s) | Quorum: 3 or 5 nodes |
| **etcd** | Quorum loss | Cluster read-only or unavailable | Regular backups; restore from snapshot |
| **scheduler** | Crash | No new Pods scheduled | HA: 1 active + N standby (leader election) |
| **controller-manager** | Crash | No reconciliation (stale state) | HA: 1 active + N standby (leader election) |
| **kubelet** | Crash | Node NotReady; Pods evicted after 5min | Node auto-remediation (cluster-autoscaler) |
| **kube-proxy** | Crash | Existing rules stay; no new Services | Pods still reachable via IP; restart kube-proxy |
| **CNI plugin** | Failure | Network unavailable; Pods can't start | Use stable CNI (Calico, Cilium); test upgrades |
| **Container runtime** | Crash | Containers die; kubelet restarts them | Choose stable runtime (containerd) |

**CAP theorem implications**:
- etcd: CP (consistent, partition-tolerant); unavailable during partition
- Kubernetes: AP for reads (stale data from cache), CP for writes (etcd)

---

## 8. OBSERVABILITY & AUDIT

### 8.1 Logging
- **Control plane logs**: kube-apiserver, scheduler, controller-manager (stdout → log aggregator)
- **Node logs**: kubelet, container runtime (journald or /var/log)
- **Application logs**: Container stdout/stderr (kubectl logs, Fluent Bit, Fluentd)

### 8.2 Metrics
- **Metrics Server**: Scrapes kubelet /metrics, exposes via API (kubectl top)
- **Prometheus**: Scrapes apiserver, scheduler, controller-manager, kubelet, kube-state-metrics
- **Key metrics**:
  - API request rate/latency (apiserver_request_duration_seconds)
  - etcd latency (etcd_disk_backend_commit_duration_seconds)
  - Scheduler latency (scheduler_binding_duration_seconds)
  - Kubelet Pod start time (kubelet_pod_start_duration_seconds)

### 8.3 Audit Logs
- kube-apiserver audit policy: Log who did what, when, result
- Levels: None, Metadata, Request, RequestResponse
- Backends: Log file, webhook (forward to SIEM)

**Critical events to monitor**:
- Exec into Pods (audit: verb=create, resource=pods/exec)
- Secret access (verb=get, resource=secrets)
- RBAC changes (verb=create/update/delete, resource=roles/rolebindings)
- Admission webhook changes
- Node drain/taint

---

## 9. THREAT MODEL SUMMARY

### 9.1 Attack Surface
```
External:
  ├─ kube-apiserver (port 6443): Must be secured (mTLS, RBAC, rate limit)
  ├─ Ingress: L7 traffic into cluster (TLS termination, WAF)
  └─ NodePort/LoadBalancer Services: Exposed ports on Nodes

Internal:
  ├─ etcd (port 2379): Only apiserver access; encrypt data
  ├─ kubelet API (port 10250): Authenticate, authorize; disable anon
  ├─ kube-scheduler, controller-manager: No external exposure
  ├─ Pod-to-Pod: NetworkPolicy to limit lateral movement
  └─ Container escape: Use gVisor/Kata for untrusted workloads
```

### 9.2 Common Exploits
| Attack | Technique | Defense |
|--------|-----------|---------|
| **Credential theft** | Steal ServiceAccount token from Pod | Short-lived tokens, rotate, external secrets |
| **Privilege escalation** | Create privileged Pod in compromised namespace | PodSecurity admission (restricted), RBAC |
| **etcd compromise** | Read etcd backup or access etcd directly | Encrypt at rest, mTLS, audit access |
| **Admission bypass** | Delete ValidatingWebhookConfiguration | Restrict `admissionregistration` permissions |
| **Supply chain** | Pull malicious image | Image scanning, signature verification (Sigstore) |
| **Lateral movement** | Compromise one Pod, scan cluster network | NetworkPolicy (default deny), segmentation |
| **Data exfiltration** | Exfil secrets via DNS/HTTP | Egress NetworkPolicy, DLP, audit logs |
| **API abuse** | Flood apiserver with requests | Rate limiting, resource quotas, audit |

---

## 10. NEXT 3 STEPS

1. **Harden control plane**:
   - Enable etcd encryption at rest with KMS provider
   - Configure audit logging (RequestResponse level, forward to SIEM)
   - Enforce Pod Security Standards (restricted) on all namespaces except kube-system
   - Review RBAC: Principle of least privilege; remove cluster-admin where possible

2. **Secure data plane**:
   - Deploy NetworkPolicy (default deny ingress/egress per namespace)
   - Disable kubelet anonymous auth (--anonymous-auth=false)
   - Use RuntimeClass with gVisor for untrusted workloads
   - Rotate ServiceAccount tokens (delete Secret to force regeneration)

3. **Implement defense-in-depth**:
   - Deploy admission controller (OPA Gatekeeper, Kyverno) for policy enforcement
   - Enable image scanning in CI/CD (Trivy, Clair) + runtime (Falco)
   - Integrate external secret store (Vault + CSI driver)
   - Set up alerting on critical audit events (exec, secret access, RBAC changes)

---

## 11. REFERENCES

- **Official docs**: https://kubernetes.io/docs/concepts/
- **API reference**: https://kubernetes.io/docs/reference/kubernetes-api/
- **Security best practices**: https://kubernetes.io/docs/concepts/security/
- **CIS Benchmark**: https://www.cisecurity.org/benchmark/kubernetes
- **RBAC escalation**: https://www.nccgroup.com/us/research-blog/privilege-escalation-in-kubernetes/
- **Admission control**: https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/
- **Container runtimes**: https://github.com/containerd/containerd
- **Network policies**: https://kubernetes.io/docs/concepts/services-networking/network-policies/

---

**END OF RFC**

# KUBERNETES(7)                  Kubernetes Internals                  KUBERNETES(7)

## NAME

**kubernetes** - Container orchestration platform for automating deployment, scaling, and management of containerized applications with security-integrated controls.

## SYNOPSIS

Kubernetes (K8s) is a declarative, distributed orchestration system for managing containerized workloads across clusters of hosts. It abstracts the underlying infrastructure to provide self-healing, horizontal scaling, and service discovery while enforcing security boundaries through role-based access, network segmentation, and runtime integrity checks. Core internals revolve around a control plane for cluster state management and worker nodes for workload execution, with flows ensuring idempotent reconciliation of desired vs. actual states.

This manual details the theoretical architecture, components, orchestration flows, and mandatory security considerations for cloud security engineers integrating or auditing K8s environments. Emphasis is placed on threat models, access controls, and isolation primitives without implementation specifics.

## DESCRIPTION

Kubernetes operates on a master-worker topology, where the control plane (master nodes) maintains global cluster state and orchestrates resources, while worker nodes execute pods (the atomic unit of deployment, encapsulating one or more containers). The system uses a declarative API model: users define desired states via YAML/JSON manifests, which the control plane reconciles continuously.

Key principles:
- **Immutability**: Pods are ephemeral; updates trigger recreation.
- **Reconciliation Loop**: Controllers observe deviations and apply corrections.
- **Extensibility**: Custom Resource Definitions (CRDs) allow domain-specific extensions, but core focuses on primitives like Pods, Services, Deployments.
- **Security Posture**: Assumes hostile multi-tenant environments; enforces least privilege, encryption in transit/rest, and auditability.

Cluster lifecycle involves bootstrapping (e.g., via kubeadm), scaling nodes, and monitoring via metrics endpoints. High availability (HA) is achieved through multi-master setups with leader election.

## CORE COMPONENTS

### Control Plane Components

The control plane runs on dedicated master nodes (or co-located in single-node setups) and handles cluster-wide decisions. Components communicate via the API server, with etcd as the canonical state store.

#### API Server (kube-apiserver)
- **Role**: Central gatekeeper and declarative interface for all interactions. Validates, authenticates, and authorizes requests; persists objects to etcd; serves as the Kubernetes API (RESTful, versioned endpoints like `/api/v1/pods`).
- **Theory**: Acts as a horizontal scaling point (multiple replicas for load). Uses watch mechanisms for efficient change notifications (via WebSockets or long-polling). Supports admission controllers for pre/post-validation (e.g., mutating webhooks for policy enforcement).
- **Security Considerations**: 
  - Authentication: Integrates with OIDC, certificates, or tokens; mandatory TLS termination.
  - Authorization: RBAC (Role-Based Access Control) or ABAC; scopes permissions to namespaces/resources (e.g., deny cross-namespace reads).
  - Audit: Logs all requests; vulnerable to API spoofing if anonymous access enabled—enforce `--anonymous-auth=false`.
  - Threat Model: Mitigates insider threats via attribute-based access; audit for anomalous patterns (e.g., bulk deletions).

#### etcd
- **Role**: Distributed key-value store for all cluster data (e.g., Pod specs, ConfigMaps). Provides consistent, highly available persistence with ACID guarantees.
- **Theory**: Uses Raft consensus for replication across 3+ nodes; watches trigger API server notifications. Data model: hierarchical keys (e.g., `/registry/pods/default/my-pod`).
- **Security Considerations**:
  - Encryption: At-rest (via X.509 certs or external KMS) and in-transit (TLS peer verification).
  - Access: API server proxies all etcd access—direct exposure risks data exfiltration; peer TLS prevents MITM.
  - Backup/Restore: Compromise exposes entire state; use snapshot isolation for forensics, rotate certs regularly.
  - Threat Model: Single point of failure if not quorate; monitor for unauthorized watches indicating reconnaissance.

#### Scheduler (kube-scheduler)
- **Role**: Assigns unscheduled Pods to feasible nodes based on resource availability, affinities, and predicates.
- **Theory**: Bind operation updates Pod spec with `nodeName`. Uses filters (feasibility checks) then scoring (optimization, e.g., least loaded node). Extensible via scheduler plugins (e.g., volume topology).
- **Security Considerations**:
  - Node Affinity: Enforce taints/tolerations to isolate sensitive workloads (e.g., taint control-plane nodes).
  - Resource Quotas: Prevent DoS via overcommitment; integrate with admission for quota enforcement.
  - Threat Model: Malicious scheduling could co-locate exploits—audit scores for bias toward vulnerable nodes.

#### Controller Manager (kube-controller-manager)
- **Role**: Daemon managing controllers for resource reconciliation (e.g., ReplicaSet ensures desired replicas).
- **Theory**: Houses multiple controllers (e.g., Node Controller for heartbeats, Deployment Controller for rollouts). Leader election via lease ensures single active instance per type.
- **Security Considerations**:
  - Leader Election: Lease hijacking risks duplicate actions; use short TTLs.
  - Controllers as Privileged: Run with minimal RBAC; vulnerable to supply-chain attacks if misconfigured.
  - Threat Model: Compromised controller amplifies to cluster-wide disruption—monitor for anomalous reconciliations.

### Node Components

Worker nodes execute workloads under control plane direction.

#### Kubelet
- **Role**: Primary node agent; registers nodes, manages Pod lifecycle (create/start/stop), and reports status via API.
- **Theory**: Uses Container Runtime Interface (CRI) to interact with runtimes. Static Pod manifests for daemons; dynamic Pods via API watches. Volume mounts and probes (liveness/readiness) ensure health.
- **Security Considerations**:
  - Privileges: Runs as root by default—use Pod Security Admission (PSA) to enforce non-root containers.
  - Image Pull: Validates signatures (e.g., via cosign); mitigates supply-chain via allowlists.
  - Threat Model: Node compromise exposes all Pods—enable SELinux/AppArmor, rotate kubelet certs, audit container escapes.

#### Kube-proxy
- **Role**: Implements Service abstraction (load balancing, discovery) via iptables/IPVS rules.
- **Theory**: Modes: userspace (legacy), iptables (default), IPVS (performance). Translates ClusterIP to backend Pods.
- **Security Considerations**:
  - Network Policies: Integrates with CNI plugins for allow/deny rules; prevents lateral movement.
  - Egress Filtering: Default open—enforce via policies to block unauthorized outbound.
  - Threat Model: Proxy misconfig enables Pod-to-Pod pivoting; monitor rule changes for stealthy exfiltration.

#### Container Runtime Interface (CRI)
- **Role**: Pluggable interface for runtimes (e.g., containerd, CRI-O); handles image pulls, container exec, and sandboxing.
- **Theory**: Abstracts OCI compliance; gRPC-based for kubelet communication. Supports runtime classes for mixed workloads.
- **Security Considerations**:
  - Sandboxing: Enforces seccomp, capabilities drops; vulnerable to kernel exploits.
  - Image Scanning: Pre-pull vulnerability checks; integrate with tools like Trivy.
  - Threat Model: Runtime breakouts (e.g., via privileged mode)—mandate runtime defaults like runc with profile enforcement.

### Networking and Storage Primitives
- **CNI (Container Network Interface)**: Plugins (e.g., Calico, Flannel) for Pod IP assignment, overlay/underlay networks.
  - Security: NetworkPolicies for micro-segmentation; mTLS for inter-Pod.
- **CSI (Container Storage Interface)**: For persistent volumes.
  - Security: Encrypt volumes; RBAC on storage classes.

## ORCHESTRATION FLOW

Kubernetes flows follow an observe-orient-decide-act (OODA) loop, with the control plane as the brain. Below is a theoretical walkthrough of key flows, illustrated with ASCII diagrams.

### Pod Creation and Scheduling Flow

1. User submits Pod manifest to API Server.
2. API Server authenticates/authorizes, applies admission (e.g., security policies), persists to etcd.
3. Watchers (Scheduler, Kubelet) detect; Scheduler binds to node.
4. Kubelet pulls images, starts containers, reports status.
5. Controllers reconcile (e.g., scale up).

```
User/Client
    |
    v
[API Server] <--> [etcd] (Store Desired State)
    | Auth/Authz/Admission
    |
    +--> [Scheduler] (Filter/Score/Bind Node)
    |       |
    |       v
    |   [Node Selection]
    |
    +--> [Controller Manager] (Reconcile Replicas)
          |
          v
[Worker Node: Kubelet] --> [CRI/Runtime] (Pull Image, Start Container)
    | Report Status
    |               |
    +---------------+
                        [Health Probes] --> Self-Healing
```

- **Security Integration**: Admission webhooks inspect manifests for vulnerabilities (e.g., reject hostPath mounts). Scheduler respects PodSecurityContext for runtime flags.

### Service Discovery and Load Balancing Flow

1. Service creation updates etcd.
2. Kube-proxy watches, updates iptables/IPVS for backend selection.
3. DNS (CoreDNS) resolves ClusterIP to Endpoints.
4. Traffic routes via CNI to Pods.

```
[Pod A] --(App Traffic)--> [Service ClusterIP]
    |                        |
    v                        v
[Endpoints Controller] --> [Kube-proxy (iptables/IPVS Rules)]
    |                                           |
    +--> [etcd Watch] <------------------------+
    |
    v
[CoreDNS] --(Resolution)--> Client Queries (e.g., my-svc.default.svc.cluster.local)
```

- **Security Integration**: NetworkPolicies filter traffic (e.g., allow only from namespace X). Service mesh (e.g., Istio) adds mTLS, but core relies on CNI enforcement.

### Node Health and Eviction Flow

1. Kubelet heartbeats to API Server (via NodeStatus).
2. Node Controller detects taints/conditions (e.g., disk pressure).
3. Evicts Pods, reschedules via Scheduler.

```
[Worker Node: Kubelet]
    | Heartbeat (Every 10s)
    v
[API Server] --> [Node Controller] (Mark NotReady, Taint)
    |                           |
    |                           +--> Eviction API Calls to Pods
    v
[Scheduler] (Requeue Unschedulable Pods)
    |
    v
New Node Binding --> [Kubelet: Cordon/Drain]
```

- **Security Integration**: Eviction priorities protect critical Pods (e.g., security scanners). Taints prevent scheduling of untrusted workloads on edge nodes.

### Rolling Update Flow (Deployment)

1. Deployment update triggers ReplicaSet creation.
2. Controllers scale old/new RS asynchronously.
3. Readiness gates ensure zero-downtime.

```
[Deployment Spec Update]
    |
    v
[Deployment Controller] --> Create New ReplicaSet (Desired Replicas=3)
    |                           |
    |                           +--> Scale Down Old RS (Gradual)
    |                                       |
    v                                       v
[ReplicaSet Controller] <----------------- [Pod Creation/Scheduling]
    |                                       |
    +--> Monitor Readiness -----------------+
```

- **Security Integration**: MaxUnavailable limits exposure during updates; validate images pre-rollout.

## SECURITY CONSIDERATIONS

Security is woven into every layer, assuming a zero-trust model with threats from insiders, supply chains, and runtime exploits.

- **Access Control**: RBAC/PSA for fine-grained permissions; ClusterRoles for admins only. Audit logs mandatory for compliance (e.g., PCI-DSS).
- **Data Protection**: Secrets as base64 (use external vaults like Vault); encrypt etcd/PVs. TLS everywhere—disable insecure ports.
- **Workload Isolation**: Namespaces for logical separation; PodSecurityStandards (privileged/restricted/baseline) enforced via admission. Limit container capabilities, use read-only FS.
- **Network Security**: Default-deny NetworkPolicies; CNI with encryption (e.g., WireGuard). Ingress/Egress controls via annotations.
- **Supply Chain**: Image signing/verification; admission for vuln scans. Avoid hostNetwork/hostPID.
- **Monitoring/Auditing**: API audit logs, metrics (Prometheus), events. Detect anomalies like privilege escalations.
- **Threat Mitigations**:
  - **Privilege Escalation**: Drop ALL capabilities; no host mounts.
  - **Lateral Movement**: Namespace isolation, service account token rotation.
  - **DoS**: ResourceQuotas, LimitRanges; horizontal pod autoscaling with security budgets.
  - **Compliance**: Integrate OPA/Gatekeeper for policy-as-code.

Common Pitfalls: Overly permissive RBAC (e.g., cluster-admin binds), unencrypted etcd, or disabled audit. Regular pentests recommended.

## FILES

- `/etc/kubernetes/` (Conceptual paths for manifests; theory only).
- API Reference: `kubectl explain <resource>` for introspection.

## SEE ALSO

- Kubernetes API Documentation (kubernetes.io/docs/reference).
- Pod Security Standards (kubernetes.io/docs/concepts/security).
- RBAC Guide (kubernetes.io/docs/reference/access-authn-authz/rbac).

## HISTORY

Introduced 2014 by Google; evolved to v1.30+ with enhanced security (e.g., in-tree to out-of-tree drivers).

Kubernetes Internals                       October 31, 2025



# Kubernetes(8) - Core Components & Internal Flow

## NAME

Kubernetes - An in-depth guide to the core components, internal workflows, and security considerations of a Kubernetes cluster, intended for cloud security software engineers.

## SYNOPSIS

This document provides a comprehensive, man-page-style explanation of the Kubernetes orchestration engine. It details the architecture, core components of the Control Plane and Worker Nodes, and the end-to-end workflows for common operations. All concepts are analyzed from a security perspective, highlighting potential attack surfaces, security controls, and defense-in-depth principles. No code or configuration examples are provided; the focus is purely on theoretical architecture and flow.

## DESCRIPTION

Kubernetes is an open-source container orchestration platform for automating deployment, scaling, and management of containerized applications. Its architecture follows a master-agent (or control plane-worker node) model. Understanding the interaction between these components is critical for securing the platform.

### Architectural Overview

A Kubernetes cluster is divided into two main parts:

1.  **Control Plane:** The "brain" of the cluster. It makes global decisions about the cluster (e.g., scheduling), and detects and responds to cluster events. It consists of several components that can be run on a single master node or distributed across multiple nodes for high availability.
2.  **Worker Nodes:** The "muscle" of the cluster. These are the machines (VMs or physical servers) that run your applications. Each node is managed by the Control Plane and contains the services necessary to run Pods.

```
+-------------------------------------------------------------+
|                        CONTROL PLANE                        |
|                                                             |
|   +----------------+    +-----------------+    +----------+ |
|   |   kube-apiserver|<->|      etcd       |    | Scheduler| |
|   +-------+--------+    +-----------------+    +----+-----+ |
|           ^                      ^                   ^     |
|           |                      |                   |     |
|           v                      v                   v     |
|   +----------------+    +-----------------+               |
|   |cloud-controller|    |kube-controller  |               |
|   |    -manager    |    |    -manager     |               |
|   +----------------+    +-----------------+               |
|        ^      ^                  ^      ^                 |
|        |      |                  |      |                 |
+--------|------|------------------|------|-----------------+
         |      |                  |      |
         |      |                  |      | (watch/listen)
         |      |                  |      |
+--------|------|------------------|------|-----------------+
|        v      v                  v      v                 |
|                  WORKER NODE 1          |   WORKER NODE 2 |
|   +----------------+    +----------+    |   +----------+  |
|   |     kubelet    |<->|kube-proxy|    |   | kubelet  |  |
|   +-------+--------+    +----+-----+    |   +----+-----+  |
|           |                 |          |        |        |
|           v                 v          |        v        |
|   +----------------+    +----------+    |   +----------+  |
|   |Container Runtime|    |   Pods   |    |   |   Pods   |  |
|   +----------------+    +----------+    |   +----------+  |
|                                                             |
+-------------------------------------------------------------+
```

---

## CONTROL PLANE COMPONENTS

### 1. etcd

**Description:**
`etcd` is a consistent and highly-available key-value store used as Kubernetes' backing store for all cluster data. It is the single source of truth for the state of the cluster, including node information, pod configurations, service definitions, secrets, and more. It is built on the Raft consensus algorithm to ensure data consistency across a distributed cluster.

**Security Considerations:**
*   **Confidentiality:** `etcd` stores all cluster state, including Secrets. Unauthorized read access to `etcd` is a full cluster compromise. **Encryption at Rest** is mandatory. Data should be encrypted using a dedicated key management service (KMS) provider.
*   **Integrity:** `etcd`'s consensus model protects against data corruption, but an attacker with write access can maliciously alter the cluster's desired state, leading to privilege escalation, data exfiltration, or denial of service.
*   **Access Control:** `etcd` must be protected by strong mutual TLS (mTLS) for both peer-to-peer communication (between `etcd` members) and client-to-server communication (from the API server). Network policies or firewall rules should restrict `etcd` access to only the API server and control plane nodes.
*   **Availability:** A DoS attack on `etcd` or loss of a quorum of `etcd` nodes will render the entire cluster inoperable. Regular backups are critical for disaster recovery.

### 2. kube-apiserver

**Description:**
The `kube-apiserver` is the central management entity of the control plane. It exposes the Kubernetes API, which is the primary interface used by users, management tools (like `kubectl`), and other control plane components to interact with the cluster. All operations (create, read, update, delete) go through the API server. It validates and processes requests, and then persists the desired state in `etcd`.

**Security Considerations:**
*   **Gateway & Enforcement Point:** The API server is the primary security enforcement point. It is responsible for **Authentication**, **Authorization**, and **Admission Control**.
*   **Authentication:** Verifies the identity of the requester. Supports multiple mechanisms (X.509 client certs, bearer tokens, OIDC, etc.). Weak authentication mechanisms lead to unauthorized access.
*   **Authorization:** Determines if an authenticated user is allowed to perform the requested action on a resource. **Role-Based Access Control (RBAC)** is the standard. Misconfigured RBAC (e.g., overly permissive cluster roles) is a common path to privilege escalation.
*   **Admission Control:** A set of gatekeepers that intercept requests to the API server *after* authentication and authorization but before the object is persisted to `etcd`. This is a critical security hook for policy enforcement. Key admission controllers include:
    *   `PodSecurityPolicy` (deprecated, replaced by Pod Security Admission): Enforces pod security standards (e.g., running as non-root, read-only root filesystem).
    *   `NodeRestriction`: Limits what a kubelet can do, preventing it from modifying pods/labels on other nodes.
    *   `ResourceQuota`: Limits resource consumption per namespace.
    *   Custom Admission Webhooks (ValidatingAdmissionWebhook, MutatingAdmissionWebhook): Allow for custom logic, such as scanning container images for vulnerabilities before they are allowed to run, or injecting sidecars for security monitoring.
*   **Exposure:** The API server should never be exposed to the public internet without strong protection. Access should be restricted via network firewalls, cloud security groups, and a bastion host or API gateway.

### 3. kube-scheduler

**Description:**
The `kube-scheduler` is responsible for assigning newly created Pods to nodes. It watches the API server for Pods that have no `nodeName` assigned and selects the best node for them based on resource requirements, hardware/policy constraints, affinity and anti-affinity specifications, taints, and tolerations.

**Security Considerations:**
*   **Pod Placement as a Security Control:** The scheduler's decisions can be used to enforce security isolation. Using **Taints and Tolerations**, you can dedicate specific nodes to run only trusted workloads or workloads with special hardware security modules (HSMs), preventing untrusted pods from being scheduled there.
*   **Denial of Service:** A misconfigured scheduler or a flood of pod creation requests can lead to resource starvation or "no available nodes" errors, causing a denial of service for legitimate applications.
*   **Integrity:** The scheduler itself is a high-privilege component. Compromise of the scheduler could allow an attacker to control pod placement, potentially scheduling malicious pods onto sensitive nodes or evicting critical workloads.

### 4. kube-controller-manager

**Description:**
The `kube-controller-manager` runs several core controller processes. These controllers watch the state of the cluster via the API server and work to move the current state towards the desired state. It's a collection of controllers, including:
*   **Node Controller:** Responsible for noticing when a node goes down and taking action.
*   **Replication Controller:** Responsible for maintaining the correct number of pods for every replication controller, ReplicaSet, or Deployment.
*   **Endpoint Controller:** Populates the Endpoint object (that joins Services & Pods).
*   **Service Account & Token Controllers:** Create default accounts and API access tokens for new namespaces.

**Security Considerations:**
*   **Automated Privilege Escalation:** Controllers are highly privileged. A vulnerability in a controller could be exploited to gain cluster-wide control. For example, a flaw in the Replication Controller could be used to create pods with elevated privileges.
*   **State Manipulation:** Since controllers continuously reconcile state, a vulnerability could allow an attacker to create a persistent, undesirable state in the cluster that is difficult to remove manually.
*   **Token Management:** The Service Account Token Controller is responsible for issuing service account tokens. A compromise could lead to the issuance of forged tokens for unauthorized access.

### 5. cloud-controller-manager

**Description:**
The `cloud-controller-manager` allows you to link your cluster into your cloud provider's API. It is an abstraction layer that separates Kubernetes components that interact with the cloud platform from those that don't. It contains controllers specific to the cloud provider for managing nodes, routes, and services (e.g., LoadBalancer type).

**Security Considerations:**
*   **Cloud Credential Compromise:** This component requires credentials to interact with the cloud provider's API (e.g., AWS, GCP, Azure). Compromise of these credentials could lead to catastrophic security breaches, allowing an attacker to manipulate cloud resources outside the cluster (e.g., create/destroy VMs, modify storage, access cloud databases).
*   **Credential Management:** Cloud credentials must be stored securely, preferably using a dedicated secrets management system and short-lived tokens, rather than static, long-lived credentials.

---

## WORKER NODE COMPONENTS

### 1. kubelet

**Description:**
The `kubelet` is the primary "agent" that runs on each node. It ensures that the containers described in PodSpecs are running and healthy. The kubelet does not manage containers that were not created by Kubernetes. It works in terms of a PodSpec, which is a YAML or JSON object that describes a pod. The kubelet receives PodSpecs from the API server and ensures the containers described in those PodSpecs are running and healthy.

**Security Considerations:**
*   **Primary Attack Surface on Nodes:** The kubelet is a high-value target. Compromise of a kubelet gives an attacker control over all pods on that node and can be a pivot point to attack the rest of the cluster.
*   **API Server Interaction:** The kubelet authenticates to the API server, typically using a TLS client certificate. The security of this certificate is paramount.
*   **Kubelet API:** The kubelet also exposes its own API, which can be used to view logs, exec into containers, and port-forward. Unauthorized access to this API is a direct compromise of the node. It should be protected with mTLS and authorization. The read-only port (10255) is insecure and should be disabled in production.
*   **Authorization Modes:** The kubelet can be configured with an authorization mode (e.g., `Webhook`, `AlwaysAllow`). `AlwaysAllow` is insecure. `Webhook` mode, which delegates authorization decisions to the API server, is recommended.
*   **Image Pull:** The kubelet is responsible for pulling container images. An attacker who can compromise the container registry could supply malicious images. Enforcing image pull policies (`AlwaysPull`) and using signed images are important mitigations.

### 2. kube-proxy

**Description:**
`kube-proxy` is a network proxy that runs on each node. Its job is to maintain network rules on nodes that allow network communication to your Pods from network sessions inside or outside of your cluster. It implements the Kubernetes Service concept. It can use several technologies for this, primarily `iptables` or `IPVS`.

**Security Considerations:**
*   **Network Policy Enforcement:** `kube-proxy` itself does not enforce Network Policies. It is the data plane implementation for Services. However, its rules can interact with Network Policies (implemented by a CNI plugin). A misconfiguration can lead to unintended traffic bypassing security policies.
*   **Denial of Service:** `iptables` can become a performance bottleneck on nodes with a very large number of services/endpoints, potentially leading to a network-related DoS. `IPVS` is designed for better performance at scale.
*   **Host Access:** `kube-proxy` runs with privileged access to the host's network stack (`CAP_NET_ADMIN`). A vulnerability in `kube-proxy` could be exploited to compromise the node's networking.

### 3. Container Runtime

**Description:**
The container runtime is the software responsible for running containers. Kubernetes uses the Container Runtime Interface (CRI) as a pluggable interface for this. Popular runtimes include `containerd` and `CRI-O`. The kubelet interacts with the runtime via the CRI to start, stop, and manage containers.

**Security Considerations:**
*   **Runtime Isolation:** The fundamental security of a container depends on the runtime's ability to isolate it from the host and other containers. This involves Linux kernel features like **namespaces** and **cgroups**.
*   **Runtime Vulnerabilities:** Vulnerabilities in the container runtime daemon (e.g., `containerd` or `dockerd`) can lead to host escape, where a malicious container can break out and gain control of the underlying node. Keeping the runtime updated is critical.
*   **Security Profiles:** The runtime can apply security profiles to containers to restrict their capabilities:
    *   **Seccomp:** Filters system calls.
    *   **AppArmor/SELinux:** Enforces mandatory access control policies.
    *   **Rootless Containers:** Running the entire container stack without root privileges significantly reduces the impact of a container escape.
*   **Image Security:** The runtime is responsible for unpacking and running the container image. It must validate image signatures and layers if configured to do so.

---

## WORKFLOWS

### Pod Creation Workflow

This diagram illustrates the sequence of events when a user creates a Pod.

```
+----------------+      1. kubectl apply      +-----------------+
|   User/Client  | -------------------------> |  kube-apiserver |
+----------------+                            +--------+--------+
                                                      | (AuthN/AuthZ)
                                                      v
                                              2. Validate & Store
                                                      |
                                                      v
+-----------------+    3. Persist desired state   +-----------------+
|      etcd       | <--------------------------- |  kube-apiserver |
+-----------------+                              +--------+--------+
      ^                                                 |
      | 4. Watch for un-scheduled pods                   |
      |                                                 v
      |                                         5. Inform scheduler
+-----------------+                              +--------+--------+
| kube-scheduler  | <--------------------------- |  kube-apiserver |
+-----------------+                              +--------+--------+
      |                                                 |
      | 6. Find best node                               |
      |                                                 v
      |                                         7. Bind pod to node
      |                                         (update API object)
      |                                                 |
      v                                                 v
+-----------------+    8. Persist binding info   +-----------------+
|      etcd       | <--------------------------- |  kube-apiserver |
+-----------------+                              +--------+--------+
      ^                                                 |
      |                                                 v
      |                                         9. Kubelet on Node-X
      |                                           (watches API server)
      |                                                 |
      |                                                 v
+-----------------+    10. Instruct runtime to   +-----------------+
| Container Runtime| <-------------------------- |     kubelet     |
| (e.g., containerd)|   create container         +-----------------+
+-----------------+
      |
      | 11. Container starts
      v
+-----------------+
|      Pod        |
| (Running State) |
+-----------------+
      |
      | 12. Update pod status
      v
+-----------------+    13. Persist actual state   +-----------------+
|      etcd       | <--------------------------- |  kube-apiserver |
+-----------------+                              +-----------------+

```

**Security Flow Analysis:**
1.  **Authentication/Authorization:** The user's credentials are validated at the API server. RBAC checks if the user is allowed to create a pod in the target namespace.
2.  **Admission Control:** Before persisting to `etcd`, admission controllers are invoked. A `PodSecurity` admission controller might reject the pod for requesting to run as root. A `ValidatingAdmissionWebhook` might scan the container image for vulnerabilities and reject it if it fails.
3.  **Secure Storage:** The desired state is stored in `etcd`. If the pod uses secrets, they are stored here, hopefully encrypted at rest.
4.  **Privileged Scheduling:** The scheduler runs with high privileges to view all nodes and make binding decisions.
7.  **Binding Integrity:** The binding decision is an API object that is authenticated and authorized, preventing a rogue component from hijacking a pod's placement.
9.  **Kubelet Security:** The kubelet authenticates to the API server to watch for pods assigned to its node. The API server, in turn, authorizes the kubelet's requests (e.g., to update pod status).
10. **Runtime Isolation:** The kubelet instructs the container runtime to create the container. The runtime enforces the security context defined in the pod spec (user, seccomp, AppArmor, etc.).

### Service Discovery & Traffic Flow

This diagram shows how a request to a Service is routed to a Pod.

```
+----------------+      1. Request to Service IP      +-----------------+
|   Client Pod   | ------------------------------> |  kube-proxy     |
| (or external)  |                                 | (on Node-X)     |
+----------------+                                 +--------+--------+
      |                                                   |
      | (e.g., ClusterIP: 10.96.0.100)                    |
      |                                                   v
      |                                         2. NAT / Packet Forward
      |                                                   |
      |                                                   v
      |                                         +-----------------+
      +-----------------------------------------> |   Target Pod    |
                                                  | (on Node-Y)     |
                                                  +-----------------+

```

**Internal State:**
*   The `kube-apiserver` creates a Service object with a stable virtual IP (ClusterIP).
*   The `Endpoint Controller` (part of `kube-controller-manager`) watches for Pods that match the Service's selector and creates/updates an `Endpoints` object listing the IPs of all ready pods.
*   `kube-proxy` on every node watches for Service and Endpoint objects via the API server.
*   When a Service is created/updated, `kube-proxy` programs the node's `iptables` or `IPVS` rules. It creates a rule that captures traffic destined for the Service's ClusterIP and DNATs (Destination Network Address Translation) it to one of the Pod IPs from the Endpoints list.

**Security Flow Analysis:**
*   **Network Policy Enforcement:** This flow is subject to Network Policies. A CNI plugin (like Calico or Cilium) implements the actual enforcement. If a Network Policy denies traffic from the Client Pod's namespace to the Target Pod's namespace, the CNI will drop the packet *before* it reaches the pod, even if `kube-proxy`'s rules allow it. The CNI and `kube-proxy` rules must work in concert.
*   **Egress/Ingress Control:** Egress traffic from the client pod and ingress to the target pod can be controlled by Network Policies or cloud-level Network Security Groups.
*   **Service Isolation:** By default, a Service is reachable from within the cluster. `NetworkPolicy` is required to restrict access. Services of type `LoadBalancer` or `NodePort` expose the service externally, which requires careful security configuration at the cloud provider or ingress controller level.

## CONCLUSION

Kubernetes' internal architecture is a complex, distributed system with numerous interdependent components. For a security engineer, every component and communication path represents a potential attack surface. A robust security posture requires a defense-in-depth strategy, focusing on:
1.  **Hardening the Control Plane:** Protecting `etcd`, securing the API server with strong AuthN/Z and admission control, and limiting the privileges of controllers.
2.  **Securing Worker Nodes:** Hardening the `kubelet`, using a secure container runtime with security profiles, and implementing network policies at the CNI level.
3.  **Protecting All Communication:** Enforcing mutual TLS (mTLS) for all control plane and node-to-control-plane communication.
4.  **Auditing and Logging:** Continuously monitoring API server audit logs and component logs for suspicious activity.

Understanding these internals is the first step toward building, deploying, and maintaining secure, resilient applications on Kubernetes.

Summary — two lines
Kubernetes is a declarative, controller-driven orchestration system built around a strongly-consistent API surface (kube-apiserver + etcd) and a set of controllers that continuously reconcile desired state to actual state. This document explains the core components, request & reconciliation flows, data model, extensibility points, and a security-first threat model for a cloud security software engineer.

# Purpose & scope

This is an RFC/man-page style explanation of Kubernetes internals for engineers designing, securing, or auditing orchestration systems. Focus: conceptual architecture, control-plane and node flows, reconciliation patterns, observability signals, extensibility, and security considerations. No code or config — theory only, with ASCII diagrams where helpful.

# Terminology (short)

* **Cluster**: control plane(s) + nodes hosting workloads.
* **Control plane**: components that expose API (kube-apiserver), store state (etcd), and run controllers/schedulers.
* **Node**: machine running kubelet + container runtime + kube-proxy (or CNIs).
* **Pod**: atomic scheduling unit (one or more co-located containers, shared namespace).
* **Controller**: loop that observes objects and reconciles actual state toward desired state.
* **Reconciliation**: continuous process of comparing observed state with desired state and making changes to converge them.
* **Admission**: mutation/validation step in API request path.
* **Informer / Watch**: caching & event propagation mechanism used by controllers.

# High-level component map (ASCII)

Control plane and node components and basic request flow.

```
  +------------------+            +------------------+       +--------------+
  | kubectl / UI /   |  <--HTTPS->| kube-apiserver   | <-->  | etcd (raft)  |
  | controllersync   |            | (authn/authz,    |       +--------------+
  | / external-svc   |            | admission)       |
  +------------------+            +--------+---------+
                                          |
                    +---------------------+---------------------+
                    |                     |                     |
           +--------v--------+   +--------v---------+   +-------v------+
           | kube-scheduler  |   | controller-mgr   |   | aggregated   |
           | (binds pod->node)|  | (replicasets,    |   | apiservers   |
           +-----------------+   | daemonsets, jobs)|   +---------------+
                                 +------------------+
                                          |
                               (controllers use watches/informers)
                                          |
  +-------------------+    +---------------v---------------+    +--------------+
  | Node A (kubelet)  |    |   Networking (CNI) / Service  |    | Node B kubelet|
  | CRI, kube-proxy   |<-->|   load balancing / DNS       |<-->| CRI, kube-proxy|
  +-------------------+    +-------------------------------+    +--------------+
```

# Core components — role & flow (with security notes)

## kube-apiserver

* **Role:** single API façade for all cluster state. All reads/writes go through it. Implements RESTful HTTP API, aggregates other APIs (API aggregation), and routes admission chains.
* **Key flows:** authentication → authorization → admission controllers → persistence to etcd (Raft leader).
* **Security notes:** TLS for client-server, mTLS with clients (control-plane components and kubelets), short-lived credentials, audit logging, limiting privileged endpoints (e.g., exec/attach/port-forward).

## etcd

* **Role:** strongly-consistent distributed key-value store (Raft), the source-of-truth for Kubernetes objects. Stores object JSON/YAML.
* **Important semantics:** revisions, resourceVersion for optimistic concurrency, compaction, snapshot/restore.
* **Security notes:** encrypt-at-rest beyond etcd’s disk, mutual TLS between etcd peers/clients, strict ACL network segmentation, least-privilege API access for control plane.

## kube-controller-manager

* **Role:** runs control loops (replicaset controller, deployment controller, node controller, namespace controller, service-account controller, endpoint controller, garbage collector). Each control loop watches objects and reconciles.
* **Pattern:** read from informer cache, react to events, create/update/delete via kube-apiserver. Idempotent operations and rate-limited.
* **Security notes:** avoid privilege escalation in controllers, protect service account tokens for controllers, validate inputs.

## kube-scheduler

* **Role:** watches unscheduled Pods and assigns nodes based on predicates (constraints) and priority (scoring). Post-binding, it writes the Pod.spec.nodeName by creating a binding.
* **Extensibility:** policy, extenders, scheduling framework plugins (preFilter, score, permit, reserve, preBind).
* **Security notes:** scheduling decisions may be influenced by labels/taints — ensure node labels/tolerations are trusted; guard against malicious admission webhooks that alter scheduling metadata.

## kubelet (on each node)

* **Role:** node agent that enforces Pod spec on the node via CRI (container runtime interface). Reports node and pod status back to API server; performs health checks, exec/attach endpoints, volume mounting.
* **Flows:** receives Pod spec, pulls images, starts containers, manages cgroups/network, reports status via status subresource.
* **Security notes:** kubelet API must be secured (authentication/authorization), limit exec/attach/port-forward, use kubelet certificate rotation, node attestation to prevent rogue nodes.

## kube-proxy / CNI

* **kube-proxy:** implements Services via iptables/ipvs rules or userspace; handles ClusterIP, NodePort mechanics.
* **CNI:** implements pod networking, isolation, and network policies.
* **Security notes:** enforce network policy for east-west isolation; secure BGP/overlay backends; defend against ARP/IP spoofing; avoid privileged binaries in the network plane.

## CoreDNS

* **Role:** DNS for cluster service discovery. Watches Service/Endpoint objects and answers cluster DNS.
* **Security notes:** guard plugins that execute script-like code; harden read access and cache poisoning defenses.

# API object model & metadata

* **Declarative desired state:** users post specs (e.g., Deployment) describing desired state; controllers converge actual state to that spec.
* **Core fields:** `metadata.uid`, `metadata.resourceVersion`, `metadata.generation`, `spec`, `status`, `ownerReferences`, `finalizers`.
* **Optimistic concurrency:** clients use resourceVersion and server-side apply/fieldManager to manage conflicts.
* **Finalizers:** prevent resource deletion until custom cleanup runs — important for lifecycle control (and a potential DOS if abused).

# Watch/informer/reconciliation model

* **Watch:** apiserver provides watch streams (via etcd’s watch functionality) returning event stream of ADD/MODIFY/DELETE.
* **Informers:** controllers use local caches (informers) to avoid hammering the API; they maintain a delta queue (workqueue) and process keys idempotently.
* **Reconciliation loop:** controllers implement `Reconcile(key)` → read latest object state (from cache/APIServer) → compute desired actions → call apiserver to mutate other objects/resources → requeue if necessary.
* **Design rules:** reconciliation must be idempotent, tolerates duplicate events, must handle out-of-order events, perform exponential backoff on failures.

# Scheduling & placement details (theory)

* **Predicates (filters):** node capacity, taints/tolerations, nodeSelector/affinity, volume topology, topology spread constraints.
* **Scores:** select best-fit based on utilization, topology, affinity, custom metrics.
* **Binding:** scheduler creates a binding (update) to assign Pod to node — this is a write to the API server and triggers kubelet to act.
* **Preemption:** scheduler may evict lower-priority pods to fit higher-priority ones; preemption is complex and must preserve progress.

# Networking & services (theory)

* **Pod networking model:** each Pod gets its own network namespace and IP; pods can reach other pods directly (flat network). CNI plugins enforce this.
* **Service abstraction:** virtual IPs (ClusterIP) mapped to endpoints; kube-proxy implements rules to forward traffic; service ports, session affinity, headless services (DNS-only).
* **Ingress vs Service vs LoadBalancer:** Ingress is L7 entry usually backed by an ingress controller; Service of type LoadBalancer maps to external LB.
* **NetworkPolicy:** declarative model to allow traffic between pods/namespaces based on selectors — default allow unless policy is enforced by CNI.

# Storage & Volumes (theory)

* **PersistentVolume (PV) & PersistentVolumeClaim (PVC):** decouple lifecycle of storage and consumers.
* **Volume lifecycle:** node mount/unmount controlled by kubelet; attach/detach controllers may run on control plane.
* **CSI (Container Storage Interface):** vendor plugin model — extarts complexity and trust surface.
* **Security notes:** enforce RBAC for PV creation, validate CSI drivers, ensure volume encryption and node trust (avoid exfil via filesystem mounts).

# Extensibility: CRDs, Aggregated API, Webhooks

* **CRDs (CustomResourceDefinitions):** allow custom types stored in etcd and handled by custom controllers. They increase API surface and require same security rigor.
* **API Aggregation:** external apiservers can be aggregated into the main API endpoint.
* **Admission Webhooks:** mutating and validating webhooks run synchronously in the admission chain; they have high power — can change/create objects or block requests.

# Versioning & semantic lifecycle concepts

* **API versioning:** alpha/beta/stable fields; deprecation windows and conversion webhooks.
* **Migrations:** schema conversion, CRD versioning, and careful rollouts are necessary for backward compatibility.

# Observability & audit signals (what to collect)

* **Audit logs:** record who did what and when (with request/response morphology). Critical for security forensics.
* **API server metrics:** request latencies, request counts, watch counts, authentication/authorization failures.
* **Controller metrics:** reconcile durations, queue lengths, error rates.
* **Node metrics & kubelet logs:** container startup latencies, eviction events, image pull metrics.
* **Etcd metrics:** leader changes, commit latency, watch latency, compaction, DB size.
* **Tracing & distributed profiling:** important for scheduling delays and admission latency debugging.

# High-availability & leader election

* **HA patterns:** run multiple kube-apiserver instances behind a load balancer; etcd cluster must be sized and placed across failure domains; control-plane components use leader election for single-active tasks.
* **Leader election:** uses coordination API (Leases) so controllers only act when leader; avoid split-brain by proper quorum.

# Security-focused architecture concepts (concise)

* **Least privilege:** controllers, controllers’ service accounts, and kubelets must have minimal RBAC privileges.
* **Defense in depth:** network segmentation, encryption (in transit & at rest), admission controls.
* **Immutable infrastructure:** treat nodes & control-plane instances as replaceable; use ephemeral credentials.
* **Attestation & identity:** node bootstrap uses attestation; workload identity should be short-lived tokens (projected JWTs).
* **Supply chain:** images must be signed and provenance checked before runtime.

# Reconciliation patterns and common controller behaviors

* **Declarative controller:** desired state expressed by `spec`, controllers maintain `status`.
* **Workqueue & rate-limits:** controllers use exponential backoff and per-key rate limiting.
* **Leader election for controllers:** one instance acts to avoid duplicate reconciliation.
* **Failure modes:** controller thrash (too many requeues), eventual consistency windows (stale cache), API server overload due to hot loops.

# Threat model — prioritized attack vectors & mitigations

```
+--------------------------------------------------------+
| Threat                     | Risk | Core Mitigation     |
+--------------------------------------------------------+
| Compromise kube-apiserver  | H   | Network isolate APIS, mTLS, strong authN, audit logs, WAF |
| Leaked etcd access/backup  | H   | Encrypt-at-rest, ACLs, offline backups encryption        |
| Malicious admission webhook| H   | Webhook authn, timeouts, fail-closed vs fail-open policy, code review, audit |
| Rogue node (kubelet)       | H   | Node attestation, revocable certs, network policies, run less-privileged workloads |
| ServiceAccount token theft | H   | Short-lived tokens, projected tokens, bound tokens, audience constraints |
| Privileged container image | H   | Image scanning, runtime seccomp, drop capabilities, Pod Security Admission |
| Privileged CRD/controller  | M-H | RBAC least privilege, restrict CRD creation, audit usage |
| Network spoofing/poisoning | M   | CNI security, network policies, mTLS, eBPF verification       |
| Supply chain compromise    | M   | Signed images, SBOMs, provenance checks, vulnerability scanning |
| Denial-of-service (API)    | M   | Rate limiting, request throttling, API server horizontal scale, admission gate |
+--------------------------------------------------------+
```

Expanded mitigations (conceptual):

* **Authentication/Identity:** Prefer short-lived credentials, OIDC federated identity for humans, mTLS and node attestation for components.
* **Authorization:** RBAC with least privilege; use ABAC rarely; minimize cluster-admin scoping; separate control-plane adaptors.
* **Admission controls:** Enforce PodSecurity standards, image policies, resource quotas, and validation webhooks.
* **Audit & detection:** Centralize audit logs, detect anomalous API patterns, retain for investigation.
* **Runtime hardening:** Enforce seccomp, AppArmor, SELinux, read-only rootfs where possible; drop unnecessary capabilities; runtime network segmentation.
* **Etcd hardening:** encrypt sensitive fields (Secrets) before storage; enable etcd authentication; restrict network access.

# Failure modes and how reconciliation behaves

* **Stale watches:** controllers must handle partial restart and full resync patterns; use resourceVersion and relist to reconcile gaps.
* **API server latency/backpressure:** controllers should backoff and multiplex leader election to avoid thrash.
* **Etcd compaction/slow disk:** watch streams may break; controllers must re-list and re-sync gracefully.
* **Split-brain etcd or partition:** ensure quorum; use global leader only when quorum exists.

# Testing, fuzzing & benchmarking ideas (theory — no code)

* **Fuzz inputs:** feed malformed API objects via admission chain to test webhook robustness.
* **Chaos tests:** simulate node flapping, network partitions, leader election failures; observe controller convergence and kube-scheduler behavior.
* **Load tests:** create bursts of API writes (e.g., thousands of Pod create/delete) and measure API server latency, etcd commit lag, and controller queue saturation.
* **Property-based testing:** assert monotonic properties: e.g., desired replicas eventually equal actual replicas under steady-state network.
* **Fuzz RPCs:** test watch stream edge cases, resourceVersion evolution, and compacted resourceVersion handling.
* **Security fuzzing:** fuzz authentication tokens, certificate rotations, and webhook responses.
* **Benchmarks to collect:** API server QPS and P95/P99 latency; etcd commit latency; scheduler binding latency; controller reconcile latency.

# Rollout & rollback conceptual plan (control-plane and feature)

* **Control plane HA upgrade:** upgrade apiservers behind LB; then leader-elected controllers one-by-one; then etcd rolling restart with snapshot/restore verification. Use canaries for admission webhooks.
* **Feature rollout (e.g., admission webhook or CRD):** staged: test cluster → pre-prod → canary subset of namespaces → full rollout. Use progressive enablement (feature gates) and ability to disable via admission/feature flags.
* **Rollback:** maintain backup snapshots (etcd snapshot), keep prior API semantics (versioned CRDs), remove newly added admission webhooks or revert feature gates, restore etcd if corruption detected.

# Observability & what normal looks like (signals & thresholds)

* **API server:** successful QPS, authn/authz failures low, watch count stable, request latency P50/P95/P99 under threshold.
* **Etcd:** leader changes rare, commit latencies low, DB size growth expected and compaction happening.
* **Controllers:** queue depth near zero under steady state, reconciliation latencies small, requeue spikes indicate issues.
* **Nodes:** eviction events rare, disk pressure events low, image pull failures minimal.

# Extensibility risks & safe patterns

* **CRDs & controllers:** treat CRDs like first-class APIs — ensure validation, conversion webhooks, and protec­tion by RBAC. Use admission webhooks to validate CRD content.
* **Aggregated apiservers & webhooks:** place behind authn/authz; be mindful of synchronous blocking impact on API latency.

# Short ASCII flow: API create Pod → scheduling → kubelet run

```
User -> kube-apiserver
    (authn/authz)
    -> admission (mutating/validating)
    -> persist to etcd
etcd notifies watches -> informers -> scheduler sees unscheduled Pod
scheduler picks node -> writes binding (update Pod.spec.nodeName)
kube-apiserver persists binding -> kubelet on node sees pod via watch/cache
kubelet asks CRI to pull/start containers -> updates Pod status (Running)
kube-apiserver stores status -> endpoint controller / service updates as needed
```

# References (topics to read deeply)

* Kubernetes control plane architecture (API server, etcd, controllers, scheduler)
* Etcd internals (Raft, compaction, snapshots)
* Reconciliation and controller patterns (Kubebuilder patterns, informer caches)
* Admission controllers & webhooks — security implications
* CRI & CSI plugin models
* Network policies and CNI models
* Kubernetes RBAC and authentication (service accounts, OIDC)
* Audit logging and forensics best practices

# Next 3 steps (practical, conceptual)

1. Map your current cluster topology against the roles above and inventory high-privilege service accounts and admission webhooks.
2. Identify the top 3 audit signals (API-server audit, etcd access logs, node kubelet logs) and configure centralized collection and alerts for anomalies.
3. Run a controlled chaos experiment (node reboot and API latency spike) in a canary namespace and measure reconcile windows and service availability.

# Closing notes — pitfalls to watch

* Admission webhooks are extremely powerful — they run in-band and can silently change request semantics or block traffic. Treat them as high-risk code.
* Etcd compromises are catastrophic; protect snapshots and backups as top-secret assets.
* Declarative control + eventual consistency leads to windows where reality differs from desired state — design for idempotence and clear observability.

This is a condensed RFC-style reference covering orchestration internals with security emphasis. If you want a single-page “cheat sheet” (one A4) or an expanded section on any controller (e.g., Deployment controller lifecycle & failure modes, StatefulSet quirks, or the scheduler algorithm intricacies and plugins), I’ll produce that next — no configs, just deep theory and detailed ASCII flows.


## RFC-Style Technical Specification

**Status:** Informational  
**Category:** Container Orchestration Security & Architecture  
**Target Audience:** Cloud Security Engineers  
**Last Updated:** October 2025

---

## Table of Contents

1. [Abstract](#1-abstract)
2. [Architecture Overview](#2-architecture-overview)
3. [Control Plane Components](#3-control-plane-components)
4. [Node Components](#4-node-components)
5. [Request Flow & Processing Pipeline](#5-request-flow--processing-pipeline)
6. [Security Architecture](#6-security-architecture)
7. [Authentication & Authorization](#7-authentication--authorization)
8. [Network Security Model](#8-network-security-model)
9. [Storage Security](#9-storage-security)
10. [Admission Control](#10-admission-control)
11. [Runtime Security](#11-runtime-security)
12. [Security Best Practices](#12-security-best-practices)

---

## 1. Abstract

Kubernetes is a distributed system for automating deployment, scaling, and management of containerized applications. This document provides a detailed technical analysis of Kubernetes core components, internal communication flows, and security mechanisms for cloud security engineers responsible for securing and auditing Kubernetes deployments.

---

## 2. Architecture Overview

### 2.1 Cluster Topology

```
┌─────────────────────────────────────────────────────────────┐
│                      CONTROL PLANE                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐   │
│  │   API    │  │  etcd    │  │Scheduler │  │Controller│   │
│  │  Server  │  │(Key-Value│  │          │  │ Manager  │   │
│  │          │  │  Store)  │  │          │  │          │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘   │
└───────┼─────────────┼─────────────┼─────────────┼─────────┘
        │             │             │             │
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
┌───────▼──────────┐      ┌─────────▼─────────┐
│   WORKER NODE 1  │      │   WORKER NODE N   │
│  ┌────────────┐  │      │  ┌────────────┐   │
│  │  kubelet   │  │      │  │  kubelet   │   │
│  ├────────────┤  │      │  ├────────────┤   │
│  │ kube-proxy │  │      │  │ kube-proxy │   │
│  ├────────────┤  │      │  ├────────────┤   │
│  │  Container │  │      │  │  Container │   │
│  │  Runtime   │  │      │  │  Runtime   │   │
│  └────────────┘  │      │  └────────────┘   │
│   [POD] [POD]    │      │   [POD] [POD]     │
└──────────────────┘      └───────────────────┘
```

### 2.2 Communication Patterns

**Hub-and-Spoke Model:**
- All components communicate through the API Server
- API Server is the ONLY component that directly interacts with etcd
- All communications are encrypted using TLS 1.2+ (1.3 preferred)

---

## 3. Control Plane Components

### 3.1 API Server (kube-apiserver)

**Purpose:** Central management entity and communication hub for the cluster.

**Key Responsibilities:**
- RESTful API gateway for all cluster operations
- Authentication and authorization gateway
- Admission control enforcement
- Validation and mutation of objects
- etcd interaction proxy
- Watch/notification mechanism for resource changes

**Security Characteristics:**

```
Request Flow through API Server:
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ 1. TLS Handshake (mTLS optional)
       ▼
┌─────────────────────────────────────┐
│     Authentication Layer            │
│  - X.509 Client Certs               │
│  - Bearer Tokens (ServiceAccount)   │
│  - OpenID Connect (OIDC)            │
│  - Webhook Token Authentication     │
│  - Bootstrap Tokens                 │
└──────┬──────────────────────────────┘
       │ 2. Identity established
       ▼
┌─────────────────────────────────────┐
│     Authorization Layer             │
│  - RBAC (Role-Based Access Control) │
│  - ABAC (Attribute-Based)           │
│  - Webhook Authorization            │
│  - Node Authorization               │
└──────┬──────────────────────────────┘
       │ 3. Permissions verified
       ▼
┌─────────────────────────────────────┐
│     Admission Control               │
│  - Mutating Webhooks (ordered)      │
│  - Validating Webhooks              │
│  - Built-in Admission Controllers   │
└──────┬──────────────────────────────┘
       │ 4. Object validated/mutated
       ▼
┌─────────────────────────────────────┐
│     Schema Validation               │
│  - OpenAPI schema enforcement       │
└──────┬──────────────────────────────┘
       │ 5. Persist to etcd
       ▼
┌─────────────────────────────────────┐
│         etcd Storage                │
└─────────────────────────────────────┘
```

**Configuration Security Parameters:**

```yaml
# Critical API Server Flags
--anonymous-auth=false                    # Disable anonymous access
--authorization-mode=Node,RBAC            # Enable Node + RBAC authorization
--enable-admission-plugins=               # Admission controllers (see §10)
  NodeRestriction,
  PodSecurityPolicy,
  ServiceAccount,
  SecurityContextDeny
--audit-log-path=/var/log/k8s-audit.log  # Audit logging
--audit-policy-file=/etc/k8s/audit.yml   # Audit policy
--encryption-provider-config=...          # etcd encryption config
--etcd-cafile=...                         # etcd CA certificate
--etcd-certfile=...                       # etcd client certificate
--etcd-keyfile=...                        # etcd client private key
--tls-cert-file=...                       # API server certificate
--tls-private-key-file=...                # API server private key
--client-ca-file=...                      # CA for client cert authentication
--service-account-key-file=...            # Public key for SA token verification
--service-account-signing-key-file=...    # Private key for SA token signing
--requestheader-client-ca-file=...        # CA for aggregation layer
--oidc-issuer-url=...                     # OIDC identity provider
--oidc-client-id=...                      # OIDC client ID
```

**Network Exposure:**
- Default Port: 6443 (HTTPS)
- Should NEVER be exposed to public internet without additional security layers
- Access should be restricted via network policies, security groups, or firewall rules

### 3.2 etcd

**Purpose:** Distributed, consistent key-value store for cluster state.

**Security Model:**

```
etcd Security Layers:
┌─────────────────────────────────────┐
│    Transport Security (TLS)         │
│  - Peer communication (2380)        │
│  - Client communication (2379)      │
│  - Mutual TLS required              │
└──────┬──────────────────────────────┘
       │
┌──────▼──────────────────────────────┐
│    Authentication                   │
│  - Client certificate auth          │
│  - No token-based auth by default   │
└──────┬──────────────────────────────┘
       │
┌──────▼──────────────────────────────┐
│    Data Encryption at Rest          │
│  - AES-CBC or AES-GCM               │
│  - Key rotation supported           │
│  - Configured via EncryptionConfig  │
└─────────────────────────────────────┘
```

**Critical Data Stored in etcd:**
- All Kubernetes objects (Pods, Services, Secrets, ConfigMaps, etc.)
- Cluster secrets (API tokens, TLS certificates, passwords)
- Configuration data
- State information

**Encryption at Rest Configuration:**

```yaml
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
      - identity: {}  # Fallback for reading unencrypted data
```

**Security Imperatives:**
- **CRITICAL:** etcd must NEVER be accessible from worker nodes
- Network segmentation required between etcd and API server
- Regular encrypted backups with secure key management
- etcd should run on dedicated control plane nodes
- Implement RBAC within etcd for API server access
- Monitor etcd access logs continuously

**Backup Security:**
```bash
# Secure etcd backup
ETCDCTL_API=3 etcdctl snapshot save backup.db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Encrypt backup
gpg --encrypt --recipient admin@example.com backup.db
```

### 3.3 Scheduler (kube-scheduler)

**Purpose:** Determines which node should run newly created Pods.

**Scheduling Algorithm:**

```
Scheduling Decision Process:
┌────────────────────────────────────┐
│  1. Watch API Server for           │
│     Unscheduled Pods               │
└────────┬───────────────────────────┘
         │
┌────────▼───────────────────────────┐
│  2. Filtering Phase                │
│     - Node selector matching       │
│     - Resource requirements        │
│     - Taints & Tolerations         │
│     - Node affinity/anti-affinity  │
│     - Pod affinity/anti-affinity   │
│     - Volume requirements          │
│     - Port availability            │
└────────┬───────────────────────────┘
         │ (Feasible nodes only)
┌────────▼───────────────────────────┐
│  3. Scoring Phase                  │
│     - Resource balance             │
│     - Image locality               │
│     - Inter-pod affinity           │
│     - Node preference              │
└────────┬───────────────────────────┘
         │ (Node with highest score)
┌────────▼───────────────────────────┐
│  4. Binding Phase                  │
│     - Update Pod spec with         │
│       NodeName field               │
│     - Write to API Server          │
└────────────────────────────────────┘
```

**Security Considerations:**

```yaml
# Scheduler Configuration (KubeSchedulerConfiguration)
apiVersion: kubescheduler.config.k8s.io/v1
kind: KubeSchedulerConfiguration
clientConnection:
  kubeconfig: /etc/kubernetes/scheduler.conf
  # Use certificate-based authentication
leaderElection:
  leaderElect: true  # HA scheduler setup
  # Only one scheduler instance makes decisions
```

**Security Implications:**
- Scheduler has read access to most cluster resources
- Can influence workload placement (data gravity attacks)
- Must authenticate with API server using strong credentials
- Should implement least-privilege RBAC
- Pod Security Standards affect scheduling decisions

**Threat Model:**
- Compromised scheduler could schedule malicious pods on specific nodes
- Could gather intelligence about cluster topology
- Potential for denial-of-service through poor scheduling decisions

### 3.4 Controller Manager (kube-controller-manager)

**Purpose:** Runs controller processes that regulate cluster state.

**Key Controllers:**

```
Controller Types:
┌──────────────────────────────────────────┐
│  Node Controller                         │
│  - Monitors node health                  │
│  - Evicts pods from failed nodes         │
│  - Updates node status                   │
└──────────────────────────────────────────┘
┌──────────────────────────────────────────┐
│  Replication Controller                  │
│  - Maintains desired replica count       │
│  - Creates/deletes pods as needed        │
└──────────────────────────────────────────┘
┌──────────────────────────────────────────┐
│  Endpoints Controller                    │
│  - Populates Endpoints objects           │
│  - Links Services to Pods                │
└──────────────────────────────────────────┘
┌──────────────────────────────────────────┐
│  ServiceAccount & Token Controllers      │
│  - Creates default ServiceAccounts       │
│  - Generates ServiceAccount tokens       │
│  - Rotates tokens (time-bound)           │
└──────────────────────────────────────────┘
┌──────────────────────────────────────────┐
│  Namespace Controller                    │
│  - Cleans up terminated namespaces       │
│  - Deletes all namespace resources       │
└──────────────────────────────────────────┘
```

**Security-Relevant Configuration:**

```bash
# Controller Manager Flags
--service-account-private-key-file=...     # Key for signing SA tokens
--root-ca-file=...                         # Root CA for SA token validation
--cluster-signing-cert-file=...            # For certificate signing
--cluster-signing-key-file=...             # CSR signing key
--use-service-account-credentials=true     # Each controller uses own SA
--bind-address=127.0.0.1                   # Localhost only (secure default)
--secure-port=10257                        # Secure metrics/health port
--authentication-kubeconfig=...            # Auth config
--authorization-kubeconfig=...             # Authz config
```

**Security Properties:**
- Each controller can run with separate ServiceAccount credentials
- Controllers watch and modify cluster resources (high privilege)
- ServiceAccount token controller manages authentication credentials
- Certificate signing for kubelet certificates (TLS bootstrap)

**Security Concerns:**
- Compromise grants broad cluster control
- Can create/modify sensitive resources (Secrets, ServiceAccounts)
- Access to certificate signing keys enables certificate forgery
- Must protect the service account private key file

### 3.5 Cloud Controller Manager (Optional)

**Purpose:** Integrates cloud provider-specific control logic.

**Responsibilities:**
- Node lifecycle management (cloud VM → Kubernetes Node)
- Load balancer provisioning for Services
- Volume provisioning and attachment
- Network route management

**Security Considerations:**
- Requires cloud provider API credentials (high privilege)
- Should use workload identity/instance metadata when possible
- Credentials should have least-privilege IAM policies
- Monitor for excessive cloud API calls (potential abuse)

---

## 4. Node Components

### 4.1 kubelet

**Purpose:** Primary node agent that manages pods and containers on each node.

**Core Responsibilities:**

```
kubelet Operational Flow:
┌─────────────────────────────────────┐
│  1. Register Node with API Server   │
│     - Send node info (capacity,     │
│       OS, kernel version)           │
└──────┬──────────────────────────────┘
       │
┌──────▼──────────────────────────────┐
│  2. Watch API Server for Pod Specs  │
│     - Assigned to this node         │
│     - Filter by node name           │
└──────┬──────────────────────────────┘
       │
┌──────▼──────────────────────────────┐
│  3. Pod Lifecycle Management        │
│     - Pull container images         │
│     - Create containers via CRI     │
│     - Mount volumes                 │
│     - Configure networking          │
│     - Execute probes (liveness,     │
│       readiness, startup)           │
└──────┬──────────────────────────────┘
       │
┌──────▼──────────────────────────────┐
│  4. Status Reporting                │
│     - Pod status updates            │
│     - Node resource usage           │
│     - Node conditions               │
└──────┬──────────────────────────────┘
       │
┌──────▼──────────────────────────────┐
│  5. Garbage Collection              │
│     - Remove terminated containers  │
│     - Clean up unused images        │
└─────────────────────────────────────┘
```

**Security Configuration:**

```yaml
# kubelet config.yaml
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
authentication:
  anonymous:
    enabled: false                          # Disable anonymous access
  webhook:
    enabled: true                           # Delegate auth to API server
    cacheTTL: 2m0s
  x509:
    clientCAFile: /etc/kubernetes/pki/ca.crt
authorization:
  mode: Webhook                             # Delegate authz to API server
  webhook:
    cacheAuthorizedTTL: 5m0s
    cacheUnauthorizedTTL: 30s
tlsCertFile: /var/lib/kubelet/pki/kubelet.crt
tlsPrivateKeyFile: /var/lib/kubelet/pki/kubelet.key
tlsCipherSuites:                            # Strong cipher suites only
  - TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
  - TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
  - TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
  - TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
rotateCertificates: true                    # Auto certificate rotation
serverTLSBootstrap: true                    # Bootstrap server cert
protectKernelDefaults: true                 # Enforce kernel security settings
makeIPTablesUtilChains: true                # Create iptables chains
eventRecordQPS: 5                           # Rate limit events
readOnlyPort: 0                             # Disable insecure port (10255)
```

**Critical Security Features:**

1. **Node Authorization:** API server restricts kubelet to only modify its own node and pods on that node

2. **Certificate Rotation:** Automatic rotation of kubelet client and server certificates

3. **Read-Only Port:** Port 10255 should be disabled (security risk - unauthenticated access)

4. **Admission:** kubelet has its own admission chain (PodSecurityPolicy enforcement point)

**Attack Surface:**

```
kubelet API (Port 10250):
- Authenticated endpoint (requires valid client cert or token)
- Commands: exec, logs, port-forward, attach
- /pods endpoint exposes running pod information
- /run endpoint can execute commands in containers
- /metrics endpoint exposes node metrics

Security Measures:
- Mutual TLS required
- Webhook authentication/authorization to API server
- NodeRestriction admission plugin limits kubelet scope
```

**Common Vulnerabilities:**
- Exposed kubelet API without authentication (historical issue)
- Overly permissive RBAC for nodes
- Kernel vulnerabilities accessible via privileged containers
- Container escape via misconfigured volume mounts

### 4.2 Container Runtime

**Purpose:** Software responsible for running containers (containerd, CRI-O, Docker Engine).

**Container Runtime Interface (CRI):**

```
CRI Architecture:
┌──────────┐
│  kubelet │
└────┬─────┘
     │ CRI gRPC API
     │ (ImageService, RuntimeService)
┌────▼──────────────────┐
│  CRI Runtime          │
│  (containerd/CRI-O)   │
└────┬──────────────────┘
     │
┌────▼──────────────────┐
│  OCI Runtime          │
│  (runc, kata, gVisor) │
└───────────────────────┘
     │
┌────▼──────────────────┐
│  Linux Kernel         │
│  - Namespaces         │
│  - Cgroups            │
│  - Seccomp            │
│  - AppArmor/SELinux   │
└───────────────────────┘
```

**Security Mechanisms:**

**1. Linux Namespaces (Isolation):**
```
- PID namespace: Process isolation
- Network namespace: Network stack isolation
- Mount namespace: Filesystem isolation
- UTS namespace: Hostname isolation
- IPC namespace: Inter-process communication isolation
- User namespace: UID/GID mapping (rootless containers)
```

**2. Cgroups (Resource Control):**
```
- CPU limits
- Memory limits
- Block I/O limits
- Network bandwidth (with CNI plugins)
- Prevents noisy neighbor attacks
```

**3. Security Profiles:**

```yaml
# Seccomp Profile Example (blocks dangerous syscalls)
apiVersion: v1
kind: Pod
metadata:
  name: secured-pod
spec:
  securityContext:
    seccompProfile:
      type: RuntimeDefault    # Use runtime's default seccomp profile
  containers:
  - name: app
    image: myapp:1.0
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop:
        - ALL                   # Drop all capabilities
        add:
        - NET_BIND_SERVICE      # Only add necessary capabilities
      readOnlyRootFilesystem: true
      runAsNonRoot: true
      runAsUser: 10000
```

**4. AppArmor/SELinux:**
```yaml
# AppArmor Profile
apiVersion: v1
kind: Pod
metadata:
  name: apparmor-pod
  annotations:
    container.apparmor.security.beta.kubernetes.io/app: runtime/default
spec:
  containers:
  - name: app
    image: myapp:1.0
```

**Container Runtime Security Best Practices:**
- Use rootless containers when possible
- Enable user namespace remapping
- Apply seccomp profiles to all workloads
- Use AppArmor or SELinux mandatory access control
- Regular CVE scanning of container images
- Implement image signing and verification
- Use minimal base images (distroless)

### 4.3 kube-proxy

**Purpose:** Network proxy that implements Kubernetes Service abstraction on each node.

**Modes of Operation:**

```
1. iptables Mode (Default):
   - Creates iptables rules for service IPs
   - DNAT for load balancing
   - Random selection for endpoints
   
2. IPVS Mode:
   - Uses Linux IPVS (IP Virtual Server)
   - More efficient for large clusters
   - Better load balancing algorithms
   
3. userspace Mode (Legacy):
   - kube-proxy itself forwards traffic
   - Performance bottleneck
   - Deprecated
```

**Network Flow (iptables mode):**

```
Client Pod → Service IP (10.96.0.10:80)
              ↓
         iptables PREROUTING
              ↓
         KUBE-SERVICES chain
              ↓
         KUBE-SVC-XXX chain (service-specific)
              ↓
         KUBE-SEP-YYY chain (endpoint-specific)
              ↓
         DNAT to Pod IP (192.168.1.5:8080)
              ↓
         Pod Container
```

**Security Considerations:**

```bash
# kube-proxy flags
--proxy-mode=ipvs                        # Use IPVS for better performance
--masquerade-all=false                   # Only masquerade when necessary
--bind-address=0.0.0.0                   # Listen address
--healthz-bind-address=127.0.0.1         # Health check localhost only
--metrics-bind-address=127.0.0.1:10249   # Metrics localhost only
--iptables-sync-period=30s               # Rule refresh interval
```

**Security Properties:**
- kube-proxy has cluster-wide service/endpoint read access
- Can manipulate node iptables/IPVS rules (requires root/CAP_NET_ADMIN)
- Network traffic not encrypted at this layer (use service mesh for mTLS)
- Potential for iptables rule exhaustion in large clusters

**NetworkPolicy Enforcement:**
- kube-proxy does NOT enforce NetworkPolicies
- NetworkPolicy enforcement is handled by CNI plugins
- Common CNI plugins with NetworkPolicy support: Calico, Cilium, Weave

---

## 5. Request Flow & Processing Pipeline

### 5.1 Pod Creation Flow

```
Complete Pod Creation Sequence:
═════════════════════════════════════════════════════════════

1. CLIENT REQUEST
   ├─ kubectl apply -f pod.yaml
   └─ HTTPS POST to API Server (port 6443)

2. API SERVER PROCESSING
   ├─ TLS termination and authentication
   ├─ Authorization (RBAC check)
   ├─ Admission Control (Mutating webhooks)
   │  ├─ Add default values
   │  ├─ Inject sidecars
   │  └─ Modify security context
   ├─ Admission Control (Validating webhooks)
   │  ├─ Policy validation (OPA, Kyverno)
   │  ├─ Security constraints
   │  └─ Resource quotas
   ├─ Schema validation
   └─ Write to etcd
      └─ Pod object created (status: Pending)

3. SCHEDULER WATCH EVENT
   ├─ Detects new unscheduled Pod
   ├─ Filtering Phase
   │  ├─ Resource availability
   │  ├─ Node selectors
   │  ├─ Affinity/Anti-affinity
   │  ├─ Taints and tolerations
   │  └─ Volume constraints
   ├─ Scoring Phase
   │  ├─ Calculate node scores
   │  └─ Select optimal node
   └─ Binding
      ├─ Create Binding object
      └─ API Server updates Pod.spec.nodeName

4. KUBELET WATCH EVENT (on assigned node)
   ├─ Detects Pod assigned to its node
   ├─ Pod Admission (local plugins)
   ├─ Create Pod sandbox (network namespace)
   ├─ Pull container images
   │  ├─ Image pull secrets
   │  ├─ Registry authentication
   │  └─ Image verification (if configured)
   ├─ Create containers via CRI
   │  ├─ Apply security context
   │  ├─ Mount volumes
   │  ├─ Set resource limits (cgroups)
   │  └─ Configure network (CNI)
   ├─ Start init containers (sequential)
   ├─ Start main containers (parallel)
   └─ Report status to API Server
      └─ Pod status: Running

5. ENDPOINTS CONTROLLER
   ├─ Watches for Pod IP assignment
   ├─ Updates Endpoints object
   └─ Associates Pod with Service

6. KUBE-PROXY (on all nodes)
   ├─ Watches Service/Endpoints changes
   └─ Updates iptables/IPVS rules
      └─ Service now routable to Pod

═════════════════════════════════════════════════════════════
```

### 5.2 Watch Mechanism

**API Server Watch Implementation:**

```
Watch Protocol (HTTP Long-Polling):
┌─────────────────────────────────────┐
│  Client (kubectl, kubelet, etc.)    │
└──────┬──────────────────────────────┘
       │ GET /api/v1/pods?watch=true
       │ (HTTP/1.1 Chunked Transfer)
┌──────▼──────────────────────────────┐
│      API Server Watch Cache         │
│  - Maintains in-memory cache        │
│  - Tracks resource versions         │
│  - Sends JSON-encoded events        │
└──────┬──────────────────────────────┘
       │
       │ Event Types:
       │ - ADDED: New resource created
       │ - MODIFIED: Resource updated
       │ - DELETED: Resource removed
       │ - ERROR: Watch error occurred
       │
┌──────▼──────────────────────────────┐
│  Client Receives Stream of Events   │
│  {"type": "ADDED", "object": {...}} │
└─────────────────────────────────────┘
```

**Watch Guarantees:**
- Ordered delivery of events (within same resource)
- At-least-once delivery
- ResourceVersion for consistency

**Security Implications:**
- Long-lived connections increase attack surface
- Watch permissions must be carefully controlled
- Potential for resource exhaustion (watch storm)
- Sensitive data can be exposed through watch streams

### 5.3 Informer Pattern (Client-Side Caching)

```
Informer Architecture (client-go):
┌─────────────────────────────────────┐
│         Reflector                   │
│  - Watches API server               │
│  - Handles reconnection             │
└──────┬──────────────────────────────┘
       │ Events
┌──────▼──────────────────────────────┐
│         DeltaFIFO Queue             │
│  - Queues events                    │
│  - Deduplicates                     │
└──────┬──────────────────────────────┘
       │
┌──────▼──────────────────────────────┐
│         Local Cache (Indexer)       │
│  - In-memory store                  │
│  - Fast local queries               │
└──────┬──────────────────────────────┘
       │
┌──────▼──────────────────────────────┐
│    Event Handlers (Controller)      │
│  - OnAdd, OnUpdate, OnDelete        │
└─────────────────────────────────────┘
```

---

## 6. Security Architecture

### 6.1 Defense in Depth Model

```
Security Layers (Onion Model):
┌─────────────────────────────────────────────┐
│  Layer 1: Infrastructure Security           │
│  - Physical/VM security                     │
│  - Network segmentation                     │
│  - Host OS hardening                        │
└──────┬──────────────────────────────────────┘
┌──────▼──────────────────────────────────────┐
│  Layer 2: Cluster Access Control            │
│  - API server authentication                │
│  - RBAC authorization                       │
│  - Network policies                         │
└──────┬──────────────────────────────────────┘
┌──────▼──────────────────────────────────────┐
│  Layer 3: Admission Control                 │
│  - Pod Security Standards                   │
│  - Policy enforcement (OPA, Kyverno)        │
│  - Resource quotas                          │
└──────┬──────────────────────────────────────┘
┌──────▼──────────────────────────────────────┐
│  Layer 4: Runtime Security                  │
│  - Container isolation (namespaces)         │
│  - Security contexts (seccomp, AppArmor)    │
│  - Resource limits (cgroups)                │
└──────┬──────────────────────────────────────┘
┌──────▼──────────────────────────────────────┐
│  Layer 5: Application Security              │
│  - Image scanning                           │
│
- Secure coding practices                   │
│  - Secrets management                       │
│  - Service mesh (mTLS)                      │
└──────┬──────────────────────────────────────┘
┌──────▼──────────────────────────────────────┐
│  Layer 6: Monitoring & Response             │
│  - Audit logging                            │
│  - Runtime threat detection                 │
│  - Incident response                        │
└─────────────────────────────────────────────┘
```

### 6.2 Certificate Authority & PKI

**Kubernetes PKI Structure:**

```
Certificate Hierarchy:
═══════════════════════════════════════════════

Root CA (kubernetes-ca)
├─ API Server Certificate
│  ├─ Subject: kube-apiserver
│  ├─ SAN: kubernetes, kubernetes.default, 
│  │       kubernetes.default.svc,
│  │       kubernetes.default.svc.cluster.local,
│  │       <API_SERVER_IP>, <LB_IP>
│  └─ Usage: Server Authentication
│
├─ API Server Kubelet Client Certificate
│  ├─ Subject: kube-apiserver-kubelet-client
│  ├─ Organization: system:masters
│  └─ Usage: Client Authentication
│
├─ Kubelet Server Certificates (per node)
│  ├─ Subject: system:node:<node-name>
│  ├─ Organization: system:nodes
│  └─ Usage: Server Authentication
│
├─ Kubelet Client Certificates (per node)
│  ├─ Subject: system:node:<node-name>
│  ├─ Organization: system:nodes
│  └─ Usage: Client Authentication
│
├─ Controller Manager Client Certificate
│  ├─ Subject: system:kube-controller-manager
│  └─ Usage: Client Authentication
│
├─ Scheduler Client Certificate
│  ├─ Subject: system:kube-scheduler
│  └─ Usage: Client Authentication
│
├─ Admin Client Certificate
│  ├─ Subject: kubernetes-admin
│  ├─ Organization: system:masters
│  └─ Usage: Client Authentication (full access)
│
└─ Service Account Signing Key (RSA/ECDSA)
   └─ Used to sign ServiceAccount tokens (JWT)

Front Proxy CA (separate)
└─ Used for API aggregation layer
   └─ Aggregated API servers

etcd CA (separate, recommended)
├─ etcd Server Certificates
├─ etcd Peer Certificates
└─ etcd Client Certificates (API server)
```

**Certificate Lifecycle Management:**

```yaml
# Certificate Signing Request (CSR) API
apiVersion: certificates.k8s.io/v1
kind: CertificateSigningRequest
metadata:
  name: node-csr-<node-name>
spec:
  request: <base64-encoded-CSR>
  signerName: kubernetes.io/kubelet-serving
  usages:
  - digital signature
  - key encipherment
  - server auth
```

**Certificate Rotation:**

```bash
# Kubelet automatic certificate rotation
--rotate-certificates=true
--rotate-server-certificates=true

# Certificate renewal (kubeadm)
kubeadm certs renew all

# Check certificate expiration
kubeadm certs check-expiration
openssl x509 -in /etc/kubernetes/pki/apiserver.crt -text -noout
```

**Security Best Practices:**
- Separate CAs for different trust boundaries (etcd, front-proxy)
- Short certificate lifetimes (default: 1 year, recommend: 90 days)
- Automated rotation before expiration
- Hardware Security Module (HSM) for CA keys in production
- Regular audits of issued certificates
- Revocation mechanism (though K8s doesn't natively support CRL/OCSP)

---

## 7. Authentication & Authorization

### 7.1 Authentication Methods

**Authentication Chain:**

```
API Server Authentication Modules (evaluated in order):
┌─────────────────────────────────────────────┐
│  1. X.509 Client Certificates               │
│     - Parsed from TLS handshake             │
│     - CN used as username                   │
│     - O (Organization) used as groups       │
│     - Most secure, recommended for          │
│       component-to-component auth           │
└──────┬──────────────────────────────────────┘
┌──────▼──────────────────────────────────────┐
│  2. Static Token File (NOT RECOMMENDED)     │
│     - Bearer token in HTTP header           │
│     - Format: token,user,uid,"group1,..."   │
│     - Cannot be updated without restart     │
│     - SECURITY RISK: tokens don't expire    │
└──────┬──────────────────────────────────────┘
┌──────▼──────────────────────────────────────┐
│  3. Bootstrap Tokens                        │
│     - Used for node joining (TLS bootstrap) │
│     - Time-limited                          │
│     - Stored as Secrets in kube-system      │
└──────┬──────────────────────────────────────┘
┌──────▼──────────────────────────────────────┐
│  4. Service Account Tokens (JWT)            │
│     - Automatically mounted in pods         │
│     - Signed by SA signing key              │
│     - Time-bound (v1.21+)                   │
│     - Audience-bound                        │
└──────┬──────────────────────────────────────┘
┌──────▼──────────────────────────────────────┐
│  5. OpenID Connect (OIDC) Tokens            │
│     - External identity provider            │
│     - JWT with claims                       │
│     - Standard: Google, Azure AD, Keycloak  │
└──────┬──────────────────────────────────────┘
┌──────▼──────────────────────────────────────┐
│  6. Webhook Token Authentication            │
│     - Delegate to external service          │
│     - POST token to webhook endpoint        │
│     - Webhook returns user info             │
└──────┬──────────────────────────────────────┘
┌──────▼──────────────────────────────────────┐
│  7. Authenticating Proxy                    │
│     - Trust headers from proxy              │
│     - X-Remote-User, X-Remote-Group         │
│     - SECURITY: Validate proxy identity!    │
└──────┬──────────────────────────────────────┘
┌──────▼──────────────────────────────────────┐
│  8. Anonymous Requests                      │
│     - system:anonymous user                 │
│     - system:unauthenticated group          │
│     - SHOULD BE DISABLED                    │
│       --anonymous-auth=false                │
└─────────────────────────────────────────────┘
```

**Service Account Token Evolution:**

```yaml
# Legacy Service Account Token (never expires)
apiVersion: v1
kind: Secret
metadata:
  name: my-sa-token
  annotations:
    kubernetes.io/service-account.name: my-sa
type: kubernetes.io/service-account-token
# SECURITY ISSUE: Token never expires

# Modern Service Account Token (time-bound)
# Projected volume with TokenRequest API
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  serviceAccountName: my-sa
  containers:
  - name: app
    image: myapp:1.0
    volumeMounts:
    - name: sa-token
      mountPath: /var/run/secrets/kubernetes.io/serviceaccount
  volumes:
  - name: sa-token
    projected:
      sources:
      - serviceAccountToken:
          path: token
          expirationSeconds: 3600      # 1 hour expiry
          audience: api                # Audience validation
      - configMap:
          name: kube-root-ca.crt
          items:
          - key: ca.crt
            path: ca.crt
      - downwardAPI:
          items:
          - path: namespace
            fieldRef:
              fieldPath: metadata.namespace
```

**OIDC Configuration:**

```bash
# API Server OIDC flags
--oidc-issuer-url=https://accounts.google.com
--oidc-client-id=kubernetes
--oidc-username-claim=email
--oidc-username-prefix=oidc:
--oidc-groups-claim=groups
--oidc-groups-prefix=oidc:
--oidc-ca-file=/etc/kubernetes/pki/oidc-ca.crt

# User authenticates with OIDC provider
# kubectl configured with id_token in kubeconfig
# API server validates token signature and claims
```

### 7.2 Authorization Modes

**Authorization Chain:**

```
Authorization Evaluation (short-circuit OR):
┌─────────────────────────────────────────────┐
│  Node Authorization                         │
│  - Kubelets can only access:                │
│    • Their own Node object                  │
│    • Pods bound to their node               │
│    • Secrets/ConfigMaps for those pods      │
│    • Services/Endpoints (all)               │
│    • PVs/PVCs for attached volumes          │
│  - Prevents node-to-node attacks            │
│  - Enabled via NodeRestriction admission    │
└──────┬──────────────────────────────────────┘
       │ DENY → Next mode
┌──────▼──────────────────────────────────────┐
│  RBAC (Role-Based Access Control)           │
│  - Most common and recommended              │
│  - Roles/ClusterRoles define permissions    │
│  - RoleBindings/ClusterRoleBindings         │
│    associate subjects with roles            │
└──────┬──────────────────────────────────────┘
       │ DENY → Next mode
┌──────▼──────────────────────────────────────┐
│  ABAC (Attribute-Based Access Control)      │
│  - DEPRECATED, use RBAC                     │
│  - Policy file with JSON rules              │
│  - Requires API server restart for changes  │
└──────┬──────────────────────────────────────┘
       │ DENY → Next mode
┌──────▼──────────────────────────────────────┐
│  Webhook Authorization                      │
│  - Delegate decision to external service    │
│  - Useful for custom logic                  │
│  - Example: Open Policy Agent (OPA)         │
└──────┬──────────────────────────────────────┘
       │ DENY → Request denied
       │ ALLOW → Request allowed
```

**RBAC Deep Dive:**

```yaml
# ClusterRole: Cluster-scoped permissions
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: secret-reader
rules:
- apiGroups: [""]              # "" = core API group
  resources: ["secrets"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["secrets"]
  resourceNames: ["my-secret"]  # Restrict to specific resource
  verbs: ["delete"]
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list"]
- apiGroups: ["apps"]
  resources: ["deployments/scale"]  # Subresource
  verbs: ["update"]

---
# Role: Namespace-scoped permissions
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: production
  name: pod-manager
rules:
- apiGroups: [""]
  resources: ["pods", "pods/log", "pods/exec"]
  verbs: ["get", "list", "create", "delete"]

---
# ClusterRoleBinding: Grant cluster-wide
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: read-secrets-global
subjects:
- kind: User
  name: alice
  apiGroup: rbac.authorization.k8s.io
- kind: ServiceAccount
  name: monitoring
  namespace: monitoring
roleRef:
  kind: ClusterRole
  name: secret-reader
  apiGroup: rbac.authorization.k8s.io

---
# RoleBinding: Grant within namespace
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: manage-pods-prod
  namespace: production
subjects:
- kind: Group
  name: dev-team
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role              # Can also reference ClusterRole
  name: pod-manager
  apiGroup: rbac.authorization.k8s.io
```

**RBAC Verbs:**

```
Standard Verbs:
- get: Read single resource
- list: Read multiple resources
- watch: Watch for changes
- create: Create new resource
- update: Update existing resource
- patch: Partially update resource
- delete: Delete resource
- deletecollection: Delete multiple resources

Special Verbs:
- use: For PodSecurityPolicies, use this PSP
- bind: For escalation prevention (roles/clusterroles)
- impersonate: Impersonate user/group/serviceaccount
- exec: Execute commands in containers
- portforward: Port forward to pods
- proxy: Proxy requests to pods/services/nodes
```

**Built-in ClusterRoles:**

```
system:masters
  - Superuser, bypasses all authorization
  - Granted to kubernetes-admin certificate
  - NEVER use in production workloads

cluster-admin
  - Full cluster access via RBAC
  - All verbs on all resources
  - Should be used sparingly

admin
  - Namespace admin
  - Read/write most resources in namespace
  - Can create Roles/RoleBindings

edit
  - Read/write common resources
  - Cannot view/modify Roles/RoleBindings

view
  - Read-only access
  - Cannot view Secrets
```

**Privilege Escalation Prevention:**

```yaml
# RBAC prevents privilege escalation by default
# User can only create RoleBindings for roles they have "bind" permission on

# Example: Prevent non-admin from granting admin
# This would be rejected:
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: sneaky-escalation
subjects:
- kind: ServiceAccount
  name: my-app
roleRef:
  kind: ClusterRole
  name: cluster-admin  # DENIED: user lacks bind permission for cluster-admin
```

**Security Audit Commands:**

```bash
# Check what a user can do
kubectl auth can-i create pods --as alice --namespace production
kubectl auth can-i '*' '*' --as alice  # Check if user is admin

# List all RoleBindings for a namespace
kubectl get rolebindings -n production

# List subjects with cluster-admin
kubectl get clusterrolebindings -o json | \
  jq '.items[] | select(.roleRef.name=="cluster-admin") | .subjects'

# Audit ServiceAccount permissions
kubectl auth can-i --list --as system:serviceaccount:default:my-app

# Find overly permissive bindings (using kubectl-who-can plugin)
kubectl who-can create pods -A
kubectl who-can '*' secrets
```

---

## 8. Network Security Model

### 8.1 Network Namespace Isolation

**Pod Network Namespace:**

```
Network Isolation Architecture:
┌─────────────────────────────────────────────┐
│  Host Network Namespace                     │
│                                             │
│  ┌───────────────────────────────────────┐ │
│  │ Pod Network Namespace 1               │ │
│  │  eth0: 10.244.1.5                     │ │
│  │  ├─ Container A (shared netns)        │ │
│  │  └─ Container B (shared netns)        │ │
│  └───────────────────────────────────────┘ │
│                ↕ (veth pair)                │
│  ┌───────────────────────────────────────┐ │
│  │ Pod Network Namespace 2               │ │
│  │  eth0: 10.244.1.6                     │ │
│  │  └─ Container C                       │ │
│  └───────────────────────────────────────┘ │
│                ↕                            │
│  ┌───────────────────────────────────────┐ │
│  │ Bridge/Overlay Network                │ │
│  │  (CNI Plugin manages routing)         │ │
│  └───────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

**Host Network Pods (Security Risk):**

```yaml
# Pod using host network namespace
apiVersion: v1
kind: Pod
metadata:
  name: host-network-pod
spec:
  hostNetwork: true  # SECURITY WARNING
  containers:
  - name: app
    image: nginx
    
# Security implications:
# - Pod has access to all host network interfaces
# - Can bind to privileged ports (< 1024)
# - Can sniff traffic on host
# - No network isolation from node
# - Required for some CNI plugins and monitoring tools
```

### 8.2 Container Network Interface (CNI)

**CNI Plugin Responsibilities:**

```
CNI Plugin Flow:
┌─────────────────────────────────────────────┐
│  kubelet calls CNI plugin                   │
└──────┬──────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────┐
│  1. ADD Command                             │
│     - Create network namespace              │
│     - Create veth pair                      │
│     - Assign IP address (IPAM plugin)       │
│     - Configure routes                      │
│     - Setup bridge/overlay                  │
│     - Apply network policies (if supported) │
└──────┬──────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────┐
│  2. DEL Command                             │
│     - Remove network configuration          │
│     - Delete veth pair                      │
│     - Release IP address                    │
└─────────────────────────────────────────────┘
```

**Popular CNI Plugins:**

```
Plugin Comparison:
┌─────────────────────────────────────────────────────────────┐
│ Calico                                                      │
│  - Network Policies: ✓ (most feature-rich)                 │
│  - Encryption: ✓ (WireGuard, IPsec)                        │
│  - Network Modes: BGP, VXLAN, IP-in-IP                     │
│  - eBPF Dataplane: ✓                                       │
│  - Security: Strong, fine-grained policies                 │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│ Cilium                                                      │
│  - Network Policies: ✓ (L3/L4/L7)                          │
│  - Encryption: ✓ (WireGuard, IPsec)                        │
│  - Network Modes: VXLAN, Geneve, Native routing            │
│  - eBPF Dataplane: ✓ (eBPF-native)                         │
│  - Security: Identity-based (not IP-based)                 │
│  - Service Mesh: Integrated                                │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│ Weave Net                                                   │
│  - Network Policies: ✓                                     │
│  - Encryption: ✓ (sleeve mode)                             │
│  - Network Modes: Fastdp, sleeve                           │
│  - Security: Automatic mesh encryption                     │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│ Flannel                                                     │
│  - Network Policies: ✗ (needs additional plugin)           │
│  - Encryption: ✗                                           │
│  - Network Modes: VXLAN, host-gw, UDP                      │
│  - Security: Basic, simple overlay                         │
└─────────────────────────────────────────────────────────────┘
```

### 8.3 Network Policies

**NetworkPolicy Resource:**

```yaml
# Default deny all ingress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: production
spec:
  podSelector: {}  # Applies to all pods in namespace
  policyTypes:
  - Ingress

---
# Default deny all egress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-egress
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Egress

---
# Allow specific ingress traffic
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-allow
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    # Allow from pods with specific label
    - podSelector:
        matchLabels:
          role: frontend
    # AND from specific namespace
    - namespaceSelector:
        matchLabels:
          name: production
    # AND from specific IP blocks
    - ipBlock:
        cidr: 10.0.0.0/8
        except:
        - 10.0.1.0/24
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - protocol: TCP
      port: 5432
  # Allow DNS
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    - podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53

---
# Advanced: Layer 7 policies (Cilium CRD)
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: l7-policy
spec:
  endpointSelector:
    matchLabels:
      app: api
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: frontend
    toPorts:
    - ports:
      - port: "80"
        protocol: TCP
      rules:
        http:
        - method: "GET"
          path: "/api/v1/.*"
        - method: "POST"
          path: "/api/v1/users"
          headers:
          - "X-API-Key: .*"
```

**NetworkPolicy Best Practices:**

```yaml
# 1. Start with default deny
# 2. Explicitly allow required traffic
# 3. Implement namespace isolation

# Production namespace isolation
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: namespace-isolation
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  # Only allow from same namespace
  - from:
    - podSelector: {}
  egress:
  # Only allow to same namespace
  - to:
    - podSelector: {}
  # Allow DNS queries
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - port: 53
      protocol: UDP
  # Allow external HTTPS (if needed)
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0
        except:
        - 10.0.0.0/8
        - 172.16.0.0/12
        - 192.168.0.0/16
    ports:
    - port: 443
      protocol: TCP
```

### 8.4 Service Mesh Security

**Service Mesh (Istio/Linkerd) Architecture:**

```
Service Mesh Components:
┌─────────────────────────────────────────────┐
│  Control Plane                              │
│  ├─ Istiod (Istio) / Linkerd Control Plane │
│  ├─ Certificate Authority                   │
│  ├─ Policy Engine                           │
│  └─ Telemetry Collection                    │
└──────┬──────────────────────────────────────┘
       │ mTLS certificates
       │ Configuration
┌──────▼──────────────────────────────────────┐
│  Data Plane (Sidecar Proxies)              │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ Pod                                 │   │
│  │  ├─ Application Container           │   │
│  │  └─ Envoy Proxy Sidecar             │   │
│  │      ├─ Intercepts all traffic      │   │
│  │      ├─ mTLS termination            │   │
│  │      ├─ Authorization enforcement   │   │
│  │      └─ Telemetry collection        │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

**Automatic Mutual TLS:**

```yaml
# Istio PeerAuthentication (strict mTLS)
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: production
spec:
  mtls:
    mode: STRICT  # Require mTLS for all traffic

---
# Authorization Policy
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: api-authz
  namespace: production
spec:
  selector:
    matchLabels:
      app: api
  action: ALLOW
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/production/sa/frontend"]
    to:
    - operation:
        methods: ["GET", "POST"]
        paths: ["/api/v1/*"]
    when:
    - key: request.auth.claims[iss]
      values: ["https://accounts.google.com"]
```

**Security Benefits:**
- Zero-trust networking (identity-based, not IP-based)
- Automatic mutual TLS between services
- Traffic encryption without application changes
- Fine-grained authorization policies
- Request-level telemetry for security monitoring

---

## 9. Storage Security

### 9.1 Volume Types & Security Implications

```
Volume Type Security Matrix:
┌─────────────────────────────────────────────────────────────┐
│ emptyDir                                                    │
│  - Ephemeral storage (deleted with pod)                    │
│  - Stored on node's disk                                   │
│  - Security: Shared node storage, potential info leak      │
│  - Use tmpfs option for sensitive data:                    │
│    emptyDir:                                               │
│      medium: Memory  # RAM-backed, more secure             │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│ hostPath                                                    │
│  - Mount directory from host node                          │
│  - SECURITY RISK: Direct host filesystem access            │
│  - Can escape container if writable                        │
│  - NEVER allow untrusted workloads                         │
│  - Required for: node monitoring, log collection           │
│  - Mitigations:                                            │
│    • Read-only mounts                                      │
│    • PodSecurityPolicy restrictions                        │
│    • SELinux/AppArmor confinement                          │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│ Persistent Volumes (PV/PVC)                                 │
│  - Network-attached storage                                 │
│  - Security: Depends on backend (NFS, iSCSI, Cloud)        │
│  - Access modes: ReadWriteOnce, ReadOnlyMany, ReadWriteMany│
│  - Encryption: CSI driver dependent                         │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│ Secret Volume                                               │
│  - tmpfs (memory-backed)                                    │
│  - Base64 encoded in etcd (NOT encrypted by default)       │
│  - CRITICAL: Enable etcd encryption at rest                │
│  - Mounted read-only by default                            │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│ Projected Volume (ServiceAccount Token)                     │
│  - JWT token with expiry                                   │
│  - Automatically rotated                                    │
│  - Audience-bound                                          │
│  - More secure than legacy SA tokens                       │
└─────────────────────────────────────────────────────────────┘
```

### 9.2 Secrets Management

**Secret Object:**

```yaml
# Opaque Secret (generic)
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
  namespace: production
type: Opaque
data:
  username: YWRtaW4=  # base64(admin)
  password: cGFzc3dvcmQxMjM=  # base64(password123)
stringData:  # Alternative: plain text (auto-encoded)
  connection-string: "postgres://admin:password123@db:5432/mydb"

---
# TLS Secret
apiVersion: v1
kind: Secret
metadata:
  name: tls-cert
type: kubernetes.io/tls
data:
  tls.crt: <base64-cert>
  tls.key: <base64-key>

---
# Docker Registry Secret
apiVersion: v1
kind: Secret
metadata:
  name: registry-creds
type: kubernetes.io/dockerconfigjson
data:
  .dockerconfigjson: <base64-encoded-docker-config>
```

**Secret Security Concerns:**

```
Critical Security Issues with Kubernetes Secrets:
┌─────────────────────────────────────────────────────────────┐
│  1. Base64 Encoding Only                               │
│     - Secrets are not encrypted by default in etcd        │
│     - Anyone with etcd access can read secrets            │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│  2. In-Memory Exposure                                   │
│     - Mounted as files in pods (readable by any container) │
│     - Can be exposed via logs, exec, or compromised apps   │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│  3. Etcd Access Risks                                    │
│     - Etcd should be secured with TLS and authentication    │
│     - Regular audits of etcd access                        │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│  4. RBAC Misconfigurations                               │
│     - Overly permissive roles can expose secrets           │
│     - Principle of least privilege must be enforced         │
└─────────────────────────────────────────────────────────────┘
```
