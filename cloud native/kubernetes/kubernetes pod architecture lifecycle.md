# Kubernetes Pod Architecture & Lifecycle: Under-the-Hood Deep Dive

## Executive Summary (Security-First Lens)

Pods are Kubernetes' atomic deployment unit—a shared kernel namespace sandbox enabling co-located containers with controlled resource isolation. The **pause container** (infrastructure container) anchors network/IPC namespaces, acting as the PID 1 reaper and namespace holder. **Init containers** enforce ordered DAG initialization with security gates (secrets fetch, TLS bootstrap, policy checks). **Sidecars** extend workload capabilities (mTLS proxy, log shipper, security agent) while sharing network/storage but maintaining process isolation. **Ephemeral containers** enable runtime debugging without image rebuilds, introducing an attack surface requiring RBAC/admission control. **QoS classes** (Guaranteed/Burstable/BestEffort) determine eviction order, OOM scoring, and cgroup resource enforcement, directly impacting availability under resource pressure. Security boundaries: pod-level network policy, per-container securityContext, shared volumes as trust domains, and kubelet CRI/CNI/CSI interactions forming the control plane attack surface.

---

## 1. Pod Architecture: Core Components & Isolation Boundaries

### 1.1 The Pause Container (Infrastructure Container)

**Purpose**: Kernel namespace anchor, PID 1 init process, zombie reaper.

**Implementation** (`pause.c` in kubernetes/kubernetes):
```c
// Simplified pause container (actual: registry.k8s.io/pause:3.9)
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

static void sigdown(int signo) {
  psignal(signo, "Shutting down, got signal");
  exit(0);
}

static void sigreap(int signo) {
  while (waitpid(-1, NULL, WNOHANG) > 0); // Reap zombies
}

int main(int argc, char **argv) {
  if (getpid() != 1) {
    fprintf(stderr, "Warning: pause should be PID 1\n");
  }
  
  if (signal(SIGINT, sigdown) == SIG_ERR) return 1;
  if (signal(SIGTERM, sigdown) == SIG_ERR) return 2;
  if (signal(SIGCHLD, sigreap) == SIG_ERR) return 3;

  for (;;) pause(); // Infinite sleep, minimal CPU
  return 0;
}
```

**Namespaces Owned** (from kubelet CRI):
```
Network (netns)  → Shared IP, ports, loopback
IPC (ipcns)      → Shared SysV IPC, POSIX queues
UTS (utsns)      → Shared hostname
PID (pidns)      → Optional (shareProcessNamespace: true)
```

**Security Properties**:
- Minimal attack surface (statically linked ~700KB binary)
- No shell, no package manager, no unnecessary syscalls
- Runs as non-root (user: 65535:65535) in recent versions
- Immutable: no writes, no configs, no secrets

**ASCII Architecture**:
```
┌─────────────────────────────────────────────────────────────┐
│  Pod: myapp (IP: 10.244.1.5, hostname: myapp-7d9c8)         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐    │
│  │ PAUSE CONTAINER (PID 1 in pod)                      │    │
│  │ Image: registry.k8s.io/pause:3.9                    │    │
│  │ Namespaces: netns, ipcns, utsns, (pidns optional)   │    │
│  │ - Holds network config (eth0, iptables, routes)     │    │
│  │ - Reaps zombie processes                            │    │
│  │ - Keeps namespaces alive if containers restart      │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌──────────────────────┐  ┌──────────────────────┐         │
│  │ Init Container 1     │  │ Init Container 2     │         │
│  │ - Runs sequentially  │→ │ - Must succeed       │         │
│  │ - Shares volumes     │  │ - restartPolicy      │         │
│  └──────────────────────┘  └──────────────────────┘         │
│                ↓                                             │
│  ┌──────────────────────┐  ┌──────────────────────┐         │
│  │ App Container        │  │ Sidecar Container    │         │
│  │ - Joins pause netns  │  │ - Envoy proxy        │         │
│  │ - Own PID/mount ns   │  │ - Shares netns       │         │
│  │ - Cgroup limits      │  │ - Separate cgroup    │         │
│  └──────────────────────┘  └──────────────────────┘         │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Ephemeral Container (debug, on-demand)              │   │
│  │ - kubectl debug --image=nicolaka/netshoot           │   │
│  │ - Shares netns/pidns, isolated filesystem           │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Shared Volumes: /var/run/secrets, /tmp/shared              │
│  Cgroup: /kubepods/burstable/pod<uid>                       │
│  QoS: Burstable (requests < limits)                         │
└─────────────────────────────────────────────────────────────┘
```

---

### 1.2 Init Containers: Ordered Initialization with Security Gates

**Lifecycle**: Sequential execution, must succeed (exit 0) before app containers start.

**Use Cases** (Security-First):
1. **Secrets/Config Bootstrap**: Fetch TLS certs from Vault, decrypt secrets
2. **Dependency Validation**: Wait for DB, ensure schema version
3. **Security Policy Check**: Verify node attestation, enforce compliance
4. **Filesystem Preparation**: Set ownership, permissions on shared volumes

**Example**: TLS Certificate Bootstrap from Vault

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-app
  namespace: prod
spec:
  serviceAccountName: app-sa
  
  initContainers:
  - name: vault-init
    image: vault:1.15
    command:
    - sh
    - -c
    - |
      set -e
      export VAULT_ADDR=https://vault.vault.svc:8200
      export VAULT_CACERT=/vault/tls/ca.crt
      
      # Authenticate with Kubernetes service account
      VAULT_TOKEN=$(vault write -field=token \
        auth/kubernetes/login \
        role=app-role \
        jwt=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token))
      
      # Fetch TLS cert and key
      vault kv get -field=tls.crt secret/app/tls > /tls/tls.crt
      vault kv get -field=tls.key secret/app/tls > /tls/tls.key
      
      # Set strict permissions
      chmod 600 /tls/tls.key
      chmod 644 /tls/tls.crt
      
      # Verify cert validity
      openssl x509 -in /tls/tls.crt -noout -checkend 86400 || exit 1
      
    volumeMounts:
    - name: tls-volume
      mountPath: /tls
    - name: vault-ca
      mountPath: /vault/tls
    
    securityContext:
      runAsNonRoot: true
      runAsUser: 1000
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
      seccompProfile:
        type: RuntimeDefault
  
  - name: wait-for-db
    image: postgres:15-alpine
    command:
    - sh
    - -c
    - |
      until pg_isready -h postgres.db.svc -p 5432 -U app; do
        echo "Waiting for database..."
        sleep 2
      done
    
    securityContext:
      runAsNonRoot: true
      runAsUser: 999
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
      readOnlyRootFilesystem: true
      seccompProfile:
        type: RuntimeDefault
  
  containers:
  - name: app
    image: myapp:v1.2.3
    volumeMounts:
    - name: tls-volume
      mountPath: /etc/app/tls
      readOnly: true
    
    securityContext:
      runAsNonRoot: true
      runAsUser: 1001
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
      readOnlyRootFilesystem: true
      seccompProfile:
        type: RuntimeDefault
  
  volumes:
  - name: tls-volume
    emptyDir:
      medium: Memory  # tmpfs, not persisted
  - name: vault-ca
    configMap:
      name: vault-ca-cert
```

**Kubelet Execution Flow** (from `pkg/kubelet/kuberuntime`):
```go
// Simplified from kubelet/kuberuntime/kuberuntime_manager.go
func (m *kubeGenericRuntimeManager) SyncPod(pod *v1.Pod, podStatus *kubecontainer.PodStatus) error {
    // 1. Create pause/infra container
    podSandboxID, err := m.createPodSandbox(pod, podStatus)
    
    // 2. Start init containers sequentially
    for i, initContainer := range pod.Spec.InitContainers {
        containerID, err := m.startContainer(podSandboxID, pod, &initContainer)
        if err != nil {
            return fmt.Errorf("init container %s failed: %v", initContainer.Name, err)
        }
        
        // Wait for completion
        status := m.waitForContainerExit(containerID)
        if status.ExitCode != 0 {
            return fmt.Errorf("init container %s exited with code %d", initContainer.Name, status.ExitCode)
        }
    }
    
    // 3. Start app containers in parallel
    for _, container := range pod.Spec.Containers {
        go m.startContainer(podSandboxID, pod, &container)
    }
    
    return nil
}
```

**Threat Model**:
- **Secrets in Init**: Credentials exposed in logs, env vars, crash dumps
- **Race Conditions**: App starts before init completes (kubelet bug)
- **Shared Volumes**: Init writes malicious config read by app
- **Container Escape**: Init runs privileged, escapes to node

**Mitigations**:
1. Use `emptyDir` with `medium: Memory` for secrets (no disk persistence)
2. Enforce `securityContext.readOnlyRootFilesystem: true`
3. Drop all capabilities, use seccomp/AppArmor
4. Admission webhook: validate init container images, forbid privileged
5. Audit logs: track init container failures, unexpected restarts

---

### 1.3 Sidecar Containers: Native vs. Legacy Patterns

**Native Sidecars (K8s 1.28+)**: `restartPolicy: Always` on specific containers.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-sidecar
spec:
  initContainers:
  - name: istio-init
    image: istio/proxyv2:1.20
    restartPolicy: Always  # SIDECAR FLAG (1.28+)
    command:
    - istio-iptables
    - -p
    - "15001"
    - -u
    - "1337"
    securityContext:
      capabilities:
        add: ["NET_ADMIN", "NET_RAW"]
      runAsNonRoot: false
      runAsUser: 0
  
  containers:
  - name: app
    image: myapp:v1
    ports:
    - containerPort: 8080
  
  - name: envoy-sidecar
    image: envoyproxy/envoy:v1.29
    args:
    - -c
    - /etc/envoy/envoy.yaml
    volumeMounts:
    - name: envoy-config
      mountPath: /etc/envoy
    
    securityContext:
      runAsUser: 1337
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
      readOnlyRootFilesystem: true
```

**Traffic Flow** (Istio/Envoy Sidecar):
```
┌─────────────────────────────────────────────────┐
│  Pod Network Namespace (shared by all)         │
├─────────────────────────────────────────────────┤
│                                                 │
│  Client → eth0:8080                             │
│              ↓                                  │
│  iptables PREROUTING (by istio-init)            │
│    REDIRECT 8080 → 15001 (Envoy ingress)        │
│              ↓                                  │
│  ┌─────────────────────────┐                    │
│  │ Envoy Sidecar           │                    │
│  │ - Listen: 15001         │                    │
│  │ - mTLS termination      │                    │
│  │ - AuthZ (RBAC/ABAC)     │                    │
│  │ - Metrics (Prometheus)  │                    │
│  │ - Tracing (Jaeger)      │                    │
│  └─────────────────────────┘                    │
│              ↓                                  │
│  Localhost:8080 (App Container)                 │
│  ┌─────────────────────────┐                    │
│  │ App Process             │                    │
│  │ - Listens 127.0.0.1:8080│                    │
│  │ - No TLS required       │                    │
│  └─────────────────────────┘                    │
│              ↓                                  │
│  Outbound: App → 127.0.0.1:15001 → Envoy        │
│    iptables OUTPUT chain → REDIRECT             │
│              ↓                                  │
│  Envoy egress → external service (mTLS)         │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Sidecar Injection Mechanisms**:
1. **Mutating Webhook**: Istio/Linkerd auto-inject on namespace label
2. **Manual YAML**: Explicitly define sidecar containers
3. **Helm Post-Renderer**: Kustomize overlay with sidecar patch

**Security Concerns**:
- **Privilege Escalation**: Init containers need NET_ADMIN for iptables
- **TOCTOU**: Sidecar starts before app, race on shared volume
- **Data Exfiltration**: Sidecar has access to all pod traffic
- **Supply Chain**: Malicious sidecar image in registry

**Hardening**:
```yaml
# OPA Gatekeeper ConstraintTemplate
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: requiresidecarsecuritycontext
spec:
  crd:
    spec:
      names:
        kind: RequireSidecarSecurityContext
  targets:
  - target: admission.k8s.gatekeeper.sh
    rego: |
      package requiresidecarsecuritycontext
      
      violation[{"msg": msg}] {
        container := input.review.object.spec.containers[_]
        container.name == "envoy-sidecar"
        not container.securityContext.runAsNonRoot
        msg := "Sidecar must run as non-root"
      }
      
      violation[{"msg": msg}] {
        container := input.review.object.spec.containers[_]
        container.name == "envoy-sidecar"
        not container.securityContext.readOnlyRootFilesystem
        msg := "Sidecar must have read-only root filesystem"
      }
```

---

### 1.4 Ephemeral Containers: Runtime Debugging Attack Surface

**Purpose**: Attach debugging tools to running pod without image rebuild.

**Implementation** (kubectl debug):
```bash
# Attach ephemeral container with network tools
kubectl debug -it pod/myapp-7d9c8 \
  --image=nicolaka/netshoot \
  --target=app \
  --share-processes \
  -- /bin/bash

# Inside ephemeral container (shares PID namespace with target)
ps aux  # See all pod processes
nsenter -t 1 -n ip addr  # Enter pause container netns
tcpdump -i eth0 -w /tmp/capture.pcap
strace -p $(pidof myapp)  # Trace app syscalls
```

**API Spec**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: myapp-7d9c8
spec:
  containers:
  - name: app
    image: myapp:v1
  
  ephemeralContainers:  # Added by kubectl debug
  - name: debugger
    image: nicolaka/netshoot
    stdin: true
    tty: true
    targetContainerName: app
    securityContext:
      capabilities:
        add: ["SYS_PTRACE", "NET_ADMIN"]  # DANGEROUS
```

**Kubelet Handling** (`pkg/kubelet/kuberuntime/kuberuntime_container.go`):
```go
func (m *kubeGenericRuntimeManager) startEphemeralContainer(pod *v1.Pod, ec *v1.EphemeralContainer) error {
    // Ephemeral containers share pod sandbox (netns)
    podSandboxID := m.getPodSandboxID(pod)
    
    // Create container config
    config := m.generateContainerConfig(ec, pod)
    
    // Target container namespace sharing
    if ec.TargetContainerName != "" {
        targetID := m.getContainerID(pod, ec.TargetContainerName)
        config.Linux.Namespaces = append(config.Linux.Namespaces,
            &runtimeapi.NamespaceOption{
                Type: runtimeapi.NamespaceMode_TARGET,
                TargetId: targetID,
            })
    }
    
    return m.runtimeService.CreateContainer(podSandboxID, config, podSandboxConfig)
}
```

**Threat Model**:
| Attack Vector | Impact | Likelihood |
|--------------|--------|-----------|
| Malicious debug image | Code execution, data exfil | Medium |
| Privilege escalation | Container escape to node | High |
| Credentials theft | Access secrets in memory | High |
| Process injection | Modify app runtime state | Medium |
| Network MitM | Intercept pod traffic | High |

**Mitigations**:

1. **RBAC**: Restrict `pods/ephemeralcontainers` create permission
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: debug-role
rules:
- apiGroups: [""]
  resources: ["pods/ephemeralcontainers"]
  verbs: ["create", "patch"]
  resourceNames: ["myapp-*"]  # Restrict to specific pods
```

2. **Admission Policy** (Kyverno):
```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: restrict-ephemeral-containers
spec:
  validationFailureAction: Enforce
  rules:
  - name: allowed-debug-images
    match:
      resources:
        kinds:
        - Pod
    validate:
      message: "Ephemeral container must use approved debug image"
      pattern:
        spec:
          ephemeralContainers:
          - image: "registry.company.com/debug/*"
  
  - name: no-privileged-ephemeral
    match:
      resources:
        kinds:
        - Pod
    validate:
      message: "Ephemeral containers cannot run privileged"
      pattern:
        spec:
          ephemeralContainers:
          - securityContext:
              privileged: false
              capabilities:
                add: ["!SYS_ADMIN", "!NET_ADMIN", "!SYS_PTRACE"]
```

3. **Audit Logging**:
```yaml
# Audit policy for ephemeral containers
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
- level: RequestResponse
  verbs: ["create", "patch"]
  resources:
  - group: ""
    resources: ["pods/ephemeralcontainers"]
  namespaces: ["prod", "staging"]
```

4. **Runtime Detection** (Falco):
```yaml
- rule: Ephemeral Container Spawned
  desc: Detect ephemeral container creation in production
  condition: >
    container and
    container.image.repository contains "netshoot" or
    container.image.repository contains "debug"
  output: "Ephemeral debug container started (user=%user.name pod=%k8s.pod.name image=%container.image.repository)"
  priority: WARNING
  tags: [k8s, debugging]
```

---

## 2. QoS Classes: Resource Guarantees & Eviction Order

### 2.1 QoS Classification Algorithm

```go
// From k8s.io/kubernetes/pkg/apis/core/v1/helper/qos/qos.go
func GetPodQOS(pod *v1.Pod) v1.PodQOSClass {
    requests := v1.ResourceList{}
    limits := v1.ResourceList{}
    
    for _, container := range pod.Spec.Containers {
        for name, quantity := range container.Resources.Requests {
            if value, ok := requests[name]; !ok {
                requests[name] = quantity.DeepCopy()
            } else {
                value.Add(quantity)
                requests[name] = value
            }
        }
        for name, quantity := range container.Resources.Limits {
            if value, ok := limits[name]; !ok {
                limits[name] = quantity.DeepCopy()
            } else {
                value.Add(quantity)
                limits[name] = value
            }
        }
    }
    
    // GUARANTEED: requests == limits for all resources
    if len(requests) > 0 && len(limits) > 0 {
        if isGuaranteed(requests, limits) {
            return v1.PodQOSGuaranteed
        }
    }
    
    // BESTEFFORT: no requests or limits
    if len(requests) == 0 && len(limits) == 0 {
        return v1.PodQOSBestEffort
    }
    
    // BURSTABLE: everything else
    return v1.PodQOSBurstable
}

func isGuaranteed(requests, limits v1.ResourceList) bool {
    for name, limit := range limits {
        request, exists := requests[name]
        if !exists || request.Cmp(limit) != 0 {
            return false
        }
    }
    return true
}
```

### 2.2 QoS Classes Breakdown

**Guaranteed**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: guaranteed-pod
spec:
  containers:
  - name: app
    image: nginx
    resources:
      requests:
        memory: "1Gi"
        cpu: "1"
      limits:
        memory: "1Gi"  # Must equal requests
        cpu: "1"
```

**Cgroup Configuration**:
```
/sys/fs/cgroup/kubepods.slice/kubepods-pod<uid>.slice/
  ├── cpu.shares = 1024 (1 CPU = 1024 shares)
  ├── cpu.cfs_quota_us = 100000 (1 CPU)
  ├── cpu.cfs_period_us = 100000
  ├── memory.limit_in_bytes = 1073741824 (1Gi)
  ├── memory.soft_limit_in_bytes = 1073741824
  └── oom_score_adj = -997 (high priority, last to be OOM killed)
```

**Burstable**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: burstable-pod
spec:
  containers:
  - name: app
    image: nginx
    resources:
      requests:
        memory: "512Mi"
        cpu: "500m"
      limits:
        memory: "2Gi"  # Different from requests
        cpu: "2"
```

**Cgroup Configuration**:
```
/sys/fs/cgroup/kubepods.slice/kubepods-burstable.slice/kubepods-burstable-pod<uid>.slice/
  ├── cpu.shares = 512 (500m CPU)
  ├── cpu.cfs_quota_us = 200000 (2 CPU limit)
  ├── memory.limit_in_bytes = 2147483648 (2Gi hard limit)
  ├── memory.soft_limit_in_bytes = 536870912 (512Mi request)
  └── oom_score_adj = 2 to 999 (variable, based on memory usage)
```

**BestEffort**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: besteffort-pod
spec:
  containers:
  - name: app
    image: nginx
    # No resources specified
```

**Cgroup Configuration**:
```
/sys/fs/cgroup/kubepods.slice/kubepods-besteffort.slice/kubepods-besteffort-pod<uid>.slice/
  ├── cpu.shares = 2 (minimal CPU priority)
  ├── cpu.cfs_quota_us = -1 (no hard limit)
  ├── memory.limit_in_bytes = <node total> (no limit)
  └── oom_score_adj = 1000 (first to be OOM killed)
```

### 2.3 Eviction & OOM Behavior

**Kubelet Eviction Manager** (`pkg/kubelet/eviction/`):

```go
// Eviction order (lowest to highest priority)
const (
    BestEffort  = 0  // Evicted first
    Burstable   = 1  // Evicted second (within QoS, by usage above request)
    Guaranteed  = 2  // Evicted last
)

func (m *managerImpl) rankPodsByQoS(pods []*v1.Pod) []*v1.Pod {
    sort.Slice(pods, func(i, j int) bool {
        qosI := qos.GetPodQOS(pods[i])
        qosJ := qos.GetPodQOS(pods[j])
        
        // BestEffort < Burstable < Guaranteed
        if qosI != qosJ {
            return qosI < qosJ
        }
        
        // Within same QoS, evict by usage above requests
        usageI := m.getMemoryUsage(pods[i])
        usageJ := m.getMemoryUsage(pods[j])
        
        requestI := m.getMemoryRequests(pods[i])
        requestJ := m.getMemoryRequests(pods[j])
        
        return (usageI - requestI) > (usageJ - requestJ)
    })
    
    return pods
}
```

**OOM Score Adjustment** (kernel integration):
```bash
# Check pod OOM scores
for pod in /sys/fs/cgroup/kubepods.slice/kubepods-*/kubepods-*-pod*/; do
    echo "Pod: $(basename $pod)"
    cat $pod/cgroup.procs | while read pid; do
        echo "  PID $pid: $(cat /proc/$pid/oom_score_adj) ($(cat /proc/$pid/oom_score))"
    done
done

# Example output:
# Pod: kubepods-burstable-pod12345
#   PID 12345: 2 (235)   # Container process
#   PID 12346: 2 (240)   # Another container process
# Pod: kubepods-guaranteed-pod67890
#   PID 67890: -997 (5)  # Protected from OOM
```

**Memory Pressure Handling**:
```
┌─────────────────────────────────────────────────┐
│  Node Memory Pressure Detection                 │
├─────────────────────────────────────────────────┤
│                                                 │
│  Available < eviction.memory.available?         │
│  (default: <100Mi or <5%)                       │
│         ↓ YES                                   │
│  ┌───────────────────────────────────────────┐  │
│  │ Eviction Manager                          │  │
│  │ 1. Rank pods by QoS                       │  │
│  │ 2. Select BestEffort pods first           │  │
│  │ 3. Send SIGTERM → wait 30s → SIGKILL      │  │
│  │ 4. Remove pod, update node status         │  │
│  └───────────────────────────────────────────┘  │
│         ↓                                       │
│  ┌───────────────────────────────────────────┐  │
│  │ Scheduler Re-schedules Pod                │  │
│  │ - Respects pod anti-affinity              │  │
│  │ - Avoids nodes under pressure             │  │
│  └───────────────────────────────────────────┘  │
│                                                 │
│  OOM Killer (kernel, if eviction too slow)      │
│  - Kills processes with highest oom_score       │
│  - Guaranteed pods: -997 (nearly immune)        │
│  - BestEffort pods: 1000 (first to die)         │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Security Implications**:
- **Denial of Service**: BestEffort pods can be evicted, disrupting low-priority services
- **Resource Exhaustion**: Burstable pods bursting to limits starve others
- **OOM Bomb**: Malicious pod intentionally triggers OOM to evict neighbors
- **Noisy Neighbor**: CPU/memory contention degrades Guaranteed pods

**Mitigations**:
1. **ResourceQuotas** per namespace
2. **LimitRanges** to enforce min/max resources
3. **PodDisruptionBudgets** to protect critical pods
4. **Node taints/tolerations** to isolate workload classes
5. **Monitoring**: Alert on eviction rate, OOM kills, throttling

---

## 3. Pod Lifecycle Phases & State Machine

### 3.1 Lifecycle State Diagram

```
┌──────────┐
│ Pending  │◄────────────────────────┐
└────┬─────┘                         │
     │                               │
     │ Image Pull                    │
     │ Scheduling                    │
     │                               │
     ↓                               │
┌──────────┐     ┌──────────────┐    │
│ Running  │────→│ Terminating  │    │
└────┬─────┘     └──────┬───────┘    │
     │                  │            │
     │ Container        │ Grace      │
     │ Restarts         │ Period     │
     │                  │            │
     ↓                  ↓            │
┌──────────┐     ┌──────────────┐    │
│ Failed   │     │  Succeeded   │    │
└────┬─────┘     └──────────────┘    │
     │                               │
     │ RestartPolicy: Always         │
     └───────────────────────────────┘
```

### 3.2 Pod Phases (API Spec)

```go
// From k8s.io/api/core/v1/types.go
type PodPhase string

const (
    PodPending    PodPhase = "Pending"    // Scheduled but not running
    PodRunning    PodPhase = "Running"    // At least one container running
    PodSucceeded  PodPhase = "Succeeded"  // All containers terminated successfully
    PodFailed     PodPhase = "Failed"     // All containers terminated, at least one failed
    PodUnknown    PodPhase = "Unknown"    // Cannot determine state (node unreachable)
)
```

### 3.3 Container State Machine

```go
type ContainerState struct {
    Waiting *ContainerStateWaiting      // Not yet running
    Running *ContainerStateRunning      // Currently executing
    Terminated *ContainerStateTerminated // Finished (success or failure)
}

type ContainerStateWaiting struct {
    Reason  string  // "ErrImagePull", "CrashLoopBackOff", "CreateContainerConfigError"
    Message string  // Detailed error message
}

type ContainerStateRunning struct {
    StartedAt metav1.Time  // When container started
}

type ContainerStateTerminated struct {
    ExitCode    int32      // Process exit code
    Signal      int32      // Signal that terminated process (SIGKILL, SIGTERM)
    Reason      string     // "Completed", "Error", "OOMKilled"
    Message     string     // Additional details
    StartedAt   metav1.Time
    FinishedAt  metav1.Time
    ContainerID string     // Runtime container ID
}
```

### 3.4 Lifecycle Hooks (postStart, preStop)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: lifecycle-demo
spec:
  containers:
  - name: app
    image: nginx
    
    lifecycle:
      postStart:
        exec:
          command:
          - /bin/sh
          - -c
          - |
            # Wait for nginx to start
            while ! nc -z localhost 80; do sleep 1; done
            
            # Register with service discovery
            curl -X POST http://consul.service.consul:8500/v1/agent/service/register \
              -d '{"name":"nginx","port":80,"check":{"http":"http://localhost:80","interval":"10s"}}'
      
      preStop:
        exec:
          command:
          - /bin/sh
          - -c
          - |
            # Deregister from service discovery
            curl -X PUT http://consul.service.consul:8500/v1/agent/service/deregister/nginx
            
            # Graceful shutdown
            nginx -s quit
            
            # Wait for connections to drain
            sleep 15
    
    terminationGracePeriodSeconds: 30
```

**Execution Semantics**:
- `postStart`: Runs **asynchronously** after container starts (no guarantee of ordering with ENTRYPOINT)
- `preStop`: Runs **synchronously** before SIGTERM sent to main process
- Failures in hooks do NOT prevent container from starting/stopping

**Kubelet Implementation** (`pkg/kubelet/lifecycle/handlers.go`):
```go
func (hr *HandlerRunner) Run(containerID kubecontainer.ContainerID, pod *v1.Pod, container *v1.Container, handler *v1.Handler) error {
    switch {
    case handler.Exec != nil:
        // Execute command in container
        return hr.commandRunner.RunInContainer(containerID, handler.Exec.Command, time.Second*10)
        
    case handler.HTTPGet != nil:
        // HTTP GET request
        url := fmt.Sprintf("http://%s:%d%s", pod.Status.PodIP, handler.HTTPGet.Port.IntValue(), handler.HTTPGet.Path)
        resp, err := hr.httpClient.Get(url)
        if err != nil || resp.StatusCode >= 400 {
            return fmt.Errorf("HTTP handler failed: %v", err)
        }
        
    case handler.TCPSocket != nil:
        // TCP socket check
        conn, err := net.DialTimeout("tcp", fmt.Sprintf("%s:%d", pod.Status.PodIP, handler.TCPSocket.Port.IntValue()), time.Second*10)
        if err != nil {
            return err
        }
        conn.Close()
    }
    
    return nil
}
```

**Security Risks**:
- **Command Injection**: Unsanitized env vars in exec handlers
- **SSRF**: HTTPGet to internal metadata APIs
- **Race Condition**: postStart assumes app is ready (may not be)
- **Long preStop**: Blocks pod termination, can exceed grace period

---

## 4. Container Runtime Interface (CRI) Deep Dive

### 4.1 CRI Architecture

```
┌─────────────────────────────────────────────────────┐
│  Kubelet                                            │
├─────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────┐   │
│  │ Pod Manager                                  │   │
│  │ - Desired state (API server)                 │   │
│  │ - Actual state (CRI)                         │   │
│  │ - Reconciliation loop                        │   │
│  └──────────────────────────────────────────────┘   │
│                    ↓ gRPC                           │
│  ┌──────────────────────────────────────────────┐   │
│  │ CRI Runtime Service (RuntimeService)         │   │
│  │ - RunPodSandbox                              │   │
│  │ - CreateContainer                            │   │
│  │ - StartContainer                             │   │
│  │ - StopContainer                              │   │
│  │ - RemoveContainer                            │   │
│  │ - PodSandboxStatus                           │   │
│  └──────────────────────────────────────────────┘   │
│                    ↓                                │
│  ┌──────────────────────────────────────────────┐   │
│  │ CRI Image Service (ImageService)             │   │
│  │ - PullImage                                  │   │
│  │ - RemoveImage                                │   │
│  │ - ImageStatus                                │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
                     ↓ Unix socket
┌─────────────────────────────────────────────────────┐
│  Container Runtime (containerd, CRI-O)              │
├─────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────┐   │
│  │ containerd-shim (per pod)                    │   │
│  │ - Manages container lifecycle               │   │
│  │ - Stdio redirection                          │   │
│  │ - Exit code collection                       │   │
│  └──────────────────────────────────────────────┘   │
│                    ↓                                │
│  ┌──────────────────────────────────────────────┐   │
│  │ runc (OCI runtime)                           │   │
│  │ - Creates namespaces (pid, net, mnt, etc.)   │   │
│  │ - Applies cgroups                            │   │
│  │ - Sets seccomp/apparmor                      │   │
│  │ - Executes container process                 │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────┐
│  Linux Kernel                                       │
│  - Namespaces (isolation)                           │
│  - Cgroups (resource limits)                        │
│  - SELinux/AppArmor (MAC)                           │
│  - Seccomp (syscall filtering)                      │
└─────────────────────────────────────────────────────┘
```

### 4.2 CRI gRPC API (Simplified)

```protobuf
// From k8s.io/cri-api/pkg/apis/runtime/v1/api.proto
service RuntimeService {
    // Sandbox (pause container) operations
    rpc RunPodSandbox(RunPodSandboxRequest) returns (RunPodSandboxResponse);
    rpc StopPodSandbox(StopPodSandboxRequest) returns (StopPodSandboxResponse);
    rpc RemovePodSandbox(RemovePodSandboxRequest) returns (RemovePodSandboxResponse);
    rpc PodSandboxStatus(PodSandboxStatusRequest) returns (PodSandboxStatusResponse);
    rpc ListPodSandbox(ListPodSandboxRequest) returns (ListPodSandboxResponse);
    
    // Container operations
    rpc CreateContainer(CreateContainerRequest) returns (CreateContainerResponse);
    rpc StartContainer(StartContainerRequest) returns (StartContainerResponse);
    rpc StopContainer(StopContainerRequest) returns (StopContainerResponse);
    rpc RemoveContainer(RemoveContainerRequest) returns (RemoveContainerResponse);
    rpc ListContainers(ListContainersRequest) returns (ListContainersResponse);
    rpc ContainerStatus(ContainerStatusRequest) returns (ContainerStatusResponse);
    
    // Exec/attach
    rpc ExecSync(ExecSyncRequest) returns (ExecSyncResponse);
    rpc Exec(ExecRequest) returns (ExecResponse);
    rpc Attach(AttachRequest) returns (AttachResponse);
}

message PodSandboxConfig {
    PodSandboxMetadata metadata = 1;
    string hostname = 2;
    string log_directory = 3;
    DNSConfig dns_config = 4;
    repeated PortMapping port_mappings = 5;
    map<string, string> labels = 6;
    map<string, string> annotations = 7;
    LinuxPodSandboxConfig linux = 8;
}

message LinuxPodSandboxConfig {
    string cgroup_parent = 1;
    LinuxSandboxSecurityContext security_context = 2;
    map<string, string> sysctls = 3;
}

message LinuxSandboxSecurityContext {
    NamespaceOption namespace_options = 1;
    SELinuxOption selinux_options = 2;
    int64 run_as_user = 3;
    int64 run_as_group = 4;
    bool readonly_rootfs = 5;
    repeated int64 supplemental_groups = 6;
    bool privileged = 7;
    string seccomp_profile_path = 8;
    string apparmor_profile = 9;
}
```

### 4.3 Pod Creation Flow (containerd)

**Step-by-Step Execution**:

```bash
# 1. Kubelet receives pod spec from API server
# 2. Kubelet calls CRI: RunPodSandbox

# containerd creates sandbox (pause container)
sudo crictl runp sandbox-config.json
# Returns: "abc123" (sandbox ID)

# 3. Kubelet calls CRI: CreateContainer (for each init/app container)
sudo crictl create abc123 container-config.json sandbox-config.json
# Returns: "def456" (container ID)

# 4. Kubelet calls CRI: StartContainer
sudo crictl start def456

# 5. Kubelet monitors via ContainerStatus
sudo crictl inspect def456
```

**Example Configs**:

`sandbox-config.json`:
```json
{
  "metadata": {
    "name": "myapp",
    "namespace": "default",
    "uid": "12345678-1234-1234-1234-123456789012"
  },
  "hostname": "myapp-7d9c8",
  "log_directory": "/var/log/pods/default_myapp_12345678",
  "dns_config": {
    "servers": ["10.96.0.10"],
    "searches": ["default.svc.cluster.local", "svc.cluster.local", "cluster.local"],
    "options": ["ndots:5"]
  },
  "port_mappings": [
    {"container_port": 8080, "host_port": 0, "protocol": "TCP"}
  ],
  "linux": {
    "cgroup_parent": "/kubepods/burstable/pod12345678",
    "security_context": {
      "namespace_options": {
        "network": "POD",
        "ipc": "POD",
        "pid": "CONTAINER"
      },
      "run_as_user": 65535,
      "readonly_rootfs": true,
      "seccomp_profile_path": "runtime/default"
    }
  }
}
```

`container-config.json` (for app container):
```json
{
  "metadata": {
    "name": "app"
  },
  "image": {
    "image": "myapp:v1.2.3"
  },
  "command": ["/app/server"],
  "args": ["--port=8080"],
  "working_dir": "/app",
  "envs": [
    {"key": "DB_HOST", "value": "postgres.db.svc"},
    {"key": "LOG_LEVEL", "value": "info"}
  ],
  "mounts": [
    {
      "container_path": "/var/run/secrets/kubernetes.io/serviceaccount",
      "host_path": "/var/lib/kubelet/pods/12345678/volumes/kubernetes.io~projected/kube-api-access-abc",
      "readonly": true
    }
  ],
  "linux": {
    "resources": {
      "cpu_period": 100000,
      "cpu_quota": 100000,
      "memory_limit_in_bytes": 1073741824
    },
    "security_context": {
      "run_as_user": 1001,
      "run_as_group": 1001,
      "readonly_rootfs": true,
      "capabilities": {
        "drop": ["ALL"]
      },
      "seccomp_profile_path": "/var/lib/kubelet/seccomp/profiles/audit.json"
    }
  }
}
```

**containerd Implementation** (simplified):
```go
// From containerd/cri/pkg/server/sandbox_run.go
func (c *criService) RunPodSandbox(ctx context.Context, req *runtime.RunPodSandboxRequest) (*runtime.RunPodSandboxResponse, error) {
    config := req.GetConfig()
    
    // 1. Setup networking (call CNI plugin)
    netNS, err := c.setupPodNetwork(config)
    
    // 2. Create sandbox container (pause)
    sandboxImage := "registry.k8s.io/pause:3.9"
    container, err := c.client.NewContainer(ctx,
        id,
        containerd.WithImage(sandboxImage),
        containerd.WithSnapshotter(c.config.Snapshotter),
        containerd.WithNewSnapshot(id, sandboxImage),
        containerd.WithContainerLabels(labels),
        containerd.WithRuntime(c.config.Runtime, &runtimeOptions),
    )
    
    // 3. Create task (actual process)
    task, err := container.NewTask(ctx,
        cio.NewCreator(cio.WithStreams(os.Stdin, os.Stdout, os.Stderr)),
    )
    
    // 4. Start task
    err = task.Start(ctx)
    
    return &runtime.RunPodSandboxResponse{PodSandboxId: id}, nil
}
```

---

## 5. Threat Model & Security Hardening

### 5.1 Attack Surface Analysis

| Component | Attack Vector | Impact | Mitigation |
|-----------|--------------|--------|------------|
| Pause Container | Malicious image | Namespace takeover | Use verified registry, image signature verification |
| Init Container | Privilege escalation | Host compromise | Drop capabilities, seccomp, RBAC |
| Sidecar | Data exfiltration | Credential theft | Network policies, mTLS, RBAC |
| Ephemeral Container | Debugging backdoor | Persistent access | Admission policy, audit logs, time limits |
| Shared Volumes | Secrets exposure | Lateral movement | emptyDir with Memory, read-only mounts |
| CRI Socket | Runtime escape | Node takeover | Restrict kubelet auth, use CRI without Docker socket |
| QoS BestEffort | Resource exhaustion DoS | Service degradation | ResourceQuotas, LimitRanges |

### 5.2 Defense-in-Depth Configuration

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: hardened-pod
  namespace: prod
  labels:
    app: secure-app
spec:
  # Security: Disable service account auto-mount
  automountServiceAccountToken: false
  
  # Security: Enable process namespace sharing (optional, for debugging)
  shareProcessNamespace: false
  
  # Security: Set pod-level security context
  securityContext:
    runAsNonRoot: true
    runAsUser: 1001
    runAsGroup: 1001
    fsGroup: 1001
    fsGroupChangePolicy: "OnRootMismatch"
    seccompProfile:
      type: RuntimeDefault
    # seLinuxOptions:
    #   level: "s0:c123,c456"
  
  # Security: Node affinity for trusted nodes
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: security-zone
            operator: In
            values: ["trusted"]
  
  # Security: Tolerations for tainted nodes
  tolerations:
  - key: "workload-type"
    operator: "Equal"
    value: "secure"
    effect: "NoSchedule"
  
  initContainers:
  - name: tls-init
    image: registry.company.com/vault-init:v1.0
    imagePullPolicy: Always
    
    command:
    - /init-script.sh
    
    volumeMounts:
    - name: tls-certs
      mountPath: /tls
    
    securityContext:
      runAsNonRoot: true
      runAsUser: 1000
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop: ["ALL"]
      seccompProfile:
        type: RuntimeDefault
    
    resources:
      requests:
        memory: "64Mi"
        cpu: "100m"
      limits:
        memory: "128Mi"
        cpu: "200m"
  
  containers:
  - name: app
    image: registry.company.com/myapp:v1.2.3@sha256:abcdef...
    imagePullPolicy: Always
    
    command:
    - /app/server
    
    args:
    - --tls-cert=/tls/tls.crt
    - --tls-key=/tls/tls.key
    
    ports:
    - name: https
      containerPort: 8443
      protocol: TCP
    
    env:
    - name: DB_HOST
      valueFrom:
        secretKeyRef:
          name: db-credentials
          key: host
    
    # Security: Resource limits (Guaranteed QoS)
    resources:
      requests:
        memory: "1Gi"
        cpu: "1"
      limits:
        memory: "1Gi"
        cpu: "1"
    
    # Security: Liveness/readiness probes
    livenessProbe:
      httpGet:
        path: /healthz
        port: 8443
        scheme: HTTPS
      initialDelaySeconds: 30
      periodSeconds: 10
      timeoutSeconds: 5
      failureThreshold: 3
    
    readinessProbe:
      httpGet:
        path: /ready
        port: 8443
        scheme: HTTPS
      initialDelaySeconds: 10
      periodSeconds: 5
      timeoutSeconds: 3
      successThreshold: 1
      failureThreshold: 3
    
    # Security: Volume mounts
    volumeMounts:
    - name: tls-certs
      mountPath: /tls
      readOnly: true
    - name: tmp
      mountPath: /tmp
    - name: app-cache
      mountPath: /app/cache
    
    # Security: Container-level hardening
    securityContext:
      runAsNonRoot: true
      runAsUser: 1001
      runAsGroup: 1001
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop: ["ALL"]
      seccompProfile:
        type: Localhost
        localhostProfile: "profiles/app-seccomp.json"
      # appArmorProfile:
      #   type: Localhost
      #   localhostProfile: "k8s-apparmor-app"
  
  volumes:
  - name: tls-certs
    emptyDir:
      medium: Memory  # tmpfs, not persisted to disk
      sizeLimit: "10Mi"
  - name: tmp
    emptyDir:
      sizeLimit: "100Mi"
  - name: app-cache
    emptyDir:
      sizeLimit: "500Mi"
  
  # Security: Termination grace period
  terminationGracePeriodSeconds: 30
  
  # Security: DNS policy
  dnsPolicy: ClusterFirst
  
  # Security: Host namespace isolation
  hostNetwork: false
  hostPID: false
  hostIPC: false
  
  # Security: Image pull secrets
  imagePullSecrets:
  - name: registry-credentials
```

### 5.3 Custom Seccomp Profile

`/var/lib/kubelet/seccomp/profiles/app-seccomp.json`:
```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "defaultErrnoRet": 1,
  "architectures": [
    "SCMP_ARCH_X86_64",
    "SCMP_ARCH_X86",
    "SCMP_ARCH_X32"
  ],
  "syscalls": [
    {
      "names": [
        "accept",
        "accept4",
        "bind",
        "brk",
        "close",
        "connect",
        "dup",
        "dup2",
        "epoll_create",
        "epoll_create1",
        "epoll_ctl",
        "epoll_wait",
        "exit",
        "exit_group",
        "fcntl",
        "fstat",
        "futex",
        "getcwd",
        "getdents64",
        "getpid",
        "getppid",
        "getrandom",
        "getsockname",
        "getsockopt",
        "listen",
        "lseek",
        "madvise",
        "mmap",
        "mprotect",
        "munmap",
        "nanosleep",
        "open",
        "openat",
        "pipe",
        "pipe2",
        "poll",
        "read",
        "readv",
        "recvfrom",
        "recvmsg",
        "rt_sigaction",
        "rt_sigprocmask",
        "rt_sigreturn",
        "sched_getaffinity",
        "sched_yield",
        "sendmsg",
        "sendto",
        "set_robust_list",
        "setitimer",
        "setsockopt",
        "shutdown",
        "socket",
        "stat",
        "tgkill",
        "write",
        "writev"
      ],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
```

### 5.4 Network Policy (Zero-Trust)

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: app-network-policy
  namespace: prod
spec:
  podSelector:
    matchLabels:
      app: secure-app
  
  policyTypes:
  - Ingress
  - Egress
  
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8443
  
  egress:
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
  
  # Allow database
  - to:
    - namespaceSelector:
        matchLabels:
          name: database
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
  
  # Allow external HTTPS (for webhooks, APIs)
  - to:
    - podSelector: {}
    ports:
    - protocol: TCP
      port: 443
```

---

## 6. Observability & Debugging

### 6.1 Inspection Commands

```bash
# Pod details
kubectl get pod myapp-7d9c8 -o yaml
kubectl describe pod myapp-7d9c8

# Container logs
kubectl logs myapp-7d9c8 -c app --previous  # Previous instance
kubectl logs myapp-7d9c8 -c app --since=1h
kubectl logs myapp-7d9c8 -c app --tail=100 -f

# Init container logs
kubectl logs myapp-7d9c8 -c tls-init

# Events
kubectl get events --field-selector involvedObject.name=myapp-7d9c8

# Resource usage (requires metrics-server)
kubectl top pod myapp-7d9c8 --containers

# CRI-level inspection
sudo crictl pods --name myapp-7d9c8
sudo crictl ps -a --pod=<sandbox-id>
sudo crictl inspect <container-id>
sudo crictl logs <container-id>

# Cgroup verification
POD_UID=$(kubectl get pod myapp-7d9c8 -o jsonpath='{.metadata.uid}')
sudo ls -la /sys/fs/cgroup/kubepods*/kubepods-*-pod${POD_UID//-/_}.slice/
sudo cat /sys/fs/cgroup/kubepods*/kubepods-*-pod${POD_UID//-/_}.slice/memory.limit_in_bytes

# Namespace inspection
sudo lsns -p $(pgrep -f "pause")
sudo nsenter -t <pause-pid> -n ip addr

# Security context verification
kubectl get pod myapp-7d9c8 -o jsonpath='{.spec.containers[0].securityContext}'
```

### 6.2 Debugging Init Container Failures

```bash
# Check init container status
kubectl get pod myapp-7d9c8 -o jsonpath='{.status.initContainerStatuses[*].state}'

# Describe for detailed error
kubectl describe pod myapp-7d9c8 | grep -A 20 "Init Containers:"

# If init restarts are disabled, create debug pod
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: debug-init
spec:
  restartPolicy: Never
  initContainers:
  - name: tls-init
    image: registry.company.com/vault-init:v1.0
    command: ["/bin/sh", "-c", "sleep 3600"]  # Keep alive
    volumeMounts:
    - name: tls-certs
      mountPath: /tls
  containers:
  - name: placeholder
    image: busybox
    command: ["sleep", "infinity"]
  volumes:
  - name: tls-certs
    emptyDir: {}
EOF

# Exec into init container
kubectl exec -it debug-init -c tls-init -- /bin/sh
```

### 6.3 QoS Class Verification

```bash
# Check pod QoS
kubectl get pod myapp-7d9c8 -o jsonpath='{.status.qosClass}'

# Verify cgroup placement
POD_UID=$(kubectl get pod myapp-7d9c8 -o jsonpath='{.metadata.uid}')
QOS=$(kubectl get pod myapp-7d9c8 -o jsonpath='{.status.qosClass}' | tr '[:upper:]' '[:lower:]')
sudo ls /sys/fs/cgroup/kubepods.slice/kubepods-${QOS}.slice/

# Check OOM scores
ps aux | grep myapp | awk '{print $2}' | while read pid; do
  echo "PID $pid: oom_score_adj=$(cat /proc/$pid/oom_score_adj) oom_score=$(cat /proc/$pid/oom_score)"
done
```

### 6.4 Prometheus Metrics (Key Pod Metrics)

```promql
# Pod CPU usage
sum(rate(container_cpu_usage_seconds_total{pod="myapp-7d9c8"}[5m])) by (container)

# Pod memory usage
sum(container_memory_working_set_bytes{pod="myapp-7d9c8"}) by (container)

# Container restarts
increase(kube_pod_container_status_restarts_total{pod="myapp-7d9c8"}[1h])

# OOM kills
increase(container_oom_events_total{pod="myapp-7d9c8"}[1h])

# Pod evictions
increase(kube_pod_status_phase{phase="Failed", reason="Evicted"}[1h])

# Init container failures
sum(kube_pod_init_container_status_terminated_reason{reason!="Completed"}) by (pod, container)
```

---

## 7. Testing & Validation

### 7.1 Pod Lifecycle Test (Go)

```go
// test/pod_lifecycle_test.go
package test

import (
    "context"
    "testing"
    "time"

    corev1 "k8s.io/api/core/v1"
    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
    "k8s.io/apimachinery/pkg/util/wait"
    "k8s.io/client-go/kubernetes"
    "k8s.io/client-go/tools/clientcmd"
)

func TestPodLifecycle(t *testing.T) {
    config, err := clientcmd.BuildConfigFromFlags("", "~/.kube/config")
    if err != nil {
        t.Fatalf("Failed to build kubeconfig: %v", err)
    }
    
    clientset, err := kubernetes.NewForConfig(config)
    if err != nil {
        t.Fatalf("Failed to create clientset: %v", err)
    }
    
    ctx := context.Background()
    ns := "test-pod-lifecycle"
    
    // Create test namespace
    _, err = clientset.CoreV1().Namespaces().Create(ctx, &corev1.Namespace{
        ObjectMeta: metav1.ObjectMeta{Name: ns},
    }, metav1.CreateOptions{})
    if err != nil {
        t.Fatalf("Failed to create namespace: %v", err)
    }
    defer clientset.CoreV1().Namespaces().Delete(ctx, ns, metav1.DeleteOptions{})
    
    // Create pod with init container
    pod := &corev1.Pod{
        ObjectMeta: metav1.ObjectMeta{
            Name:      "test-pod",
            Namespace: ns,
        },
        Spec: corev1.PodSpec{
            InitContainers: []corev1.Container{
                {
                    Name:    "init-test",
                    Image:   "busybox:1.35",
                    Command: []string{"sh", "-c", "echo 'Init complete' && sleep 5"},
                },
            },
            Containers: []corev1.Container{
                {
                    Name:    "app",
                    Image:   "nginx:1.25",
                    Command: []string{"nginx", "-g", "daemon off;"},
                    Resources: corev1.ResourceRequirements{
                        Requests: corev1.ResourceList{
                            corev1.ResourceMemory: resource.MustParse("64Mi"),
                            corev1.ResourceCPU:    resource.MustParse("100m"),
                        },
                        Limits: corev1.ResourceList{
                            corev1.ResourceMemory: resource.MustParse("64Mi"),
                            corev1.ResourceCPU:    resource.MustParse("100m"),
                        },
                    },
                },
            },
            RestartPolicy: corev1.RestartPolicyNever,
        },
    }
    
    _, err = clientset.CoreV1().Pods(ns).Create(ctx, pod, metav1.CreateOptions{})
    if err != nil {
        t.Fatalf("Failed to create pod: %v", err)
    }
    
    // Wait for init container to complete
    err = wait.PollImmediate(1*time.Second, 30*time.Second, func() (bool, error) {
        p, err := clientset.CoreV1().Pods(ns).Get(ctx, "test-pod", metav1.GetOptions{})
        if err != nil {
            return false, err
        }
        
        for _, initStatus := range p.Status.InitContainerStatuses {
            if initStatus.State.Terminated != nil && initStatus.State.Terminated.ExitCode == 0 {
                return true, nil
            }
        }
        return false, nil
    })
    if err != nil {
        t.Fatalf("Init container did not complete: %v", err)
    }
    
    // Wait for app container to start
    err = wait.PollImmediate(1*time.Second, 30*time.Second, func() (bool, error) {
        p, err := clientset.CoreV1().Pods(ns).Get(ctx, "test-pod", metav1.GetOptions{})
        if err != nil {
            return false, err
        }
        
        if p.Status.Phase == corev1.PodRunning {
            return true, nil
        }
        return false, nil
    })
    if err != nil {
        t.Fatalf("Pod did not reach Running phase: %v", err)
    }
    
    // Verify QoS class
    p, _ := clientset.CoreV1().Pods(ns).Get(ctx, "test-pod", metav1.GetOptions{})
    if p.Status.QOSClass != corev1.PodQOSGuaranteed {
        t.Errorf("Expected QoS Guaranteed, got %s", p.Status.QOSClass)
    }
    
    t.Logf("Pod lifecycle test passed")
}
```

### 7.2 Security Context Validation (Rust)

```rust
// tests/security_context_test.rs
use k8s_openapi::api::core::v1::{Pod, SecurityContext, PodSecurityContext};
use kube::{Api, Client};
use kube::api::{PostParams, DeleteParams};
use anyhow::Result;

#[tokio::test]
async fn test_security_context_enforcement() -> Result<()> {
    let client = Client::try_default().await?;
    let pods: Api<Pod> = Api::namespaced(client, "test-security");
    
    // Create pod with hardened security context
    let pod = serde_json::from_value(serde_json::json!({
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": "secure-test"
        },
        "spec": {
            "securityContext": {
                "runAsNonRoot": true,
                "runAsUser": 1000,
                "fsGroup": 1000,
                "seccompProfile": {
                    "type": "RuntimeDefault"
                }
            },
            "containers": [{
                "name": "app",
                "image": "nginx:1.25",
                "securityContext": {
                    "allowPrivilegeEscalation": false,
                    "readOnlyRootFilesystem": true,
                    "capabilities": {
                        "drop": ["ALL"]
                    }
                }
            }]
        }
    }))?;
    
    pods.create(&PostParams::default(), &pod).await?;
    
    // Wait for pod to start
    tokio::time::sleep(tokio::time::Duration::from_secs(10)).await;
    
    // Verify security context applied
    let pod_status = pods.get("secure-test").await?;
    let container_status = &pod_status.status.unwrap().container_statuses.unwrap()[0];
    
    assert!(container_status.state.as_ref().unwrap().running.is_some(),
            "Container should be running with hardened security context");
    
    // Cleanup
    pods.delete("secure-test", &DeleteParams::default()).await?;
    
    Ok(())
}
```

### 7.3 Chaos Engineering (Pod Deletion)

```bash
# Install chaos-mesh
helm repo add chaos-mesh https://charts.chaos-mesh.org
helm install chaos-mesh chaos-mesh/chaos-mesh -n chaos-mesh --create-namespace

# Create PodChaos experiment
cat <<EOF | kubectl apply -f -
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: pod-kill-test
  namespace: prod
spec:
  action: pod-kill
  mode: one
  selector:
    namespaces:
    - prod
    labelSelectors:
      app: myapp
  scheduler:
    cron: "@every 5m"
  duration: "10s"
EOF

# Monitor pod restarts
watch -n 1 'kubectl get pods -n prod -l app=myapp'

# Verify resilience (should auto-restart)
kubectl describe pod -n prod -l app=myapp | grep -A 5 "Restart Count"
```

---

## 8. Rollout & Rollback Strategy

### 8.1 Deployment with Pod Template Updates

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  namespace: prod
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0  # Zero-downtime
  
  selector:
    matchLabels:
      app: myapp
  
  template:
    metadata:
      labels:
        app: myapp
        version: v1.2.3
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
    
    spec:
      # Pod spec (as defined in section 5.2)
      ...
```

### 8.2 Rollout Procedure

```bash
# 1. Update deployment (change image, env vars, etc.)
kubectl set image deployment/myapp app=myapp:v1.2.4 -n prod

# 2. Monitor rollout
kubectl rollout status deployment/myapp -n prod --watch

# 3. Check pod template hash (new ReplicaSet)
kubectl get rs -n prod -l app=myapp

# 4. Verify new pods running
kubectl get pods -n prod -l app=myapp,version=v1.2.4

# 5. Check logs for errors
kubectl logs -n prod -l app=myapp,version=v1.2.4 --tail=100

# 6. Run smoke tests
curl -k https://myapp.prod.svc:8443/healthz

# If issues detected:
# 7. Rollback immediately
kubectl rollout undo deployment/myapp -n prod

# OR rollback to specific revision
kubectl rollout history deployment/myapp -n prod
kubectl rollout undo deployment/myapp -n prod --to-revision=3
```

### 8.3 Canary Deployment (Flagger + Istio)

```yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: myapp
  namespace: prod
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  
  service:
    port: 8443
    targetPort: 8443
  
  analysis:
    interval: 1m
    threshold: 5
    maxWeight: 50
    stepWeight: 10
    
    metrics:
    - name: request-success-rate
      thresholdRange:
        min: 99
      interval: 1m
    
    - name: request-duration
      thresholdRange:
        max: 500
      interval: 1m
    
    webhooks:
    - name: load-test
      url: http://flagger-loadtester/
      timeout: 5s
      metadata:
        cmd: "hey -z 1m -q 10 -c 2 https://myapp-canary.prod:8443/healthz"
```

---

## 9. References & Further Reading

1. **Kubernetes Official Docs**:
   - Pod Lifecycle: https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/
   - Init Containers: https://kubernetes.io/docs/concepts/workloads/pods/init-containers/
   - Ephemeral Containers: https://kubernetes.io/docs/concepts/workloads/pods/ephemeral-containers/
   - QoS Classes: https://kubernetes.io/docs/tasks/configure-pod-container/quality-service-pod/

2. **Source Code**:
   - kubelet: https://github.com/kubernetes/kubernetes/tree/master/pkg/kubelet
   - CRI: https://github.com/kubernetes/cri-api
   - containerd: https://github.com/containerd/containerd
   - runc: https://github.com/opencontainers/runc

3. **Security Resources**:
   - NSA/CISA K8s Hardening Guide: https://media.defense.gov/2022/Aug/29/2003066362/-1/-1/0/CTR_KUBERNETES_HARDENING_GUIDANCE_1.2_20220829.PDF
   - CIS Kubernetes Benchmark: https://www.cisecurity.org/benchmark/kubernetes
   - Pod Security Standards: https://kubernetes.io/docs/concepts/security/pod-security-standards/

4. **CNCF Projects**:
   - Falco (Runtime Security): https://falco.org/
   - OPA Gatekeeper (Admission Control): https://open-policy-agent.github.io/gatekeeper/
   - Kyverno (Policy Engine): https://kyverno.io/
   - Cilium (Network Security): https://cilium.io/

5. **Tools**:
   - crictl: https://github.com/kubernetes-sigs/cri-tools
   - kubectl debug: https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/
   - kube-bench: https://github.com/aquasecurity/kube-bench

---

## Next 3 Steps

1. **Lab Setup**: Deploy test cluster (kind/k3s), create pods with each QoS class, observe cgroup configs and eviction behavior under memory pressure (`stress-ng --vm 4 --vm-bytes 90%`).

2. **Security Hardening**: Implement OPA Gatekeeper policies to enforce securityContext (non-root, drop caps, read-only FS), test with intentionally vulnerable pods, verify denials in audit logs.

3. **CRI Deep Dive**: Trace complete pod creation flow using `crictl` + `strace` on kubelet, capture CRI gRPC calls with Wireshark/tcpdump, analyze containerd/runc namespace/cgroup setup in `/proc/<pid>/ns` and `/sys/fs/cgroup`.

**Verification Commands**:
```bash
# Step 1: Memory pressure test
kubectl run memory-hog --image=polinux/stress --restart=Never -- stress --vm 1 --vm-bytes 1G --vm-hang 0
kubectl get events --watch | grep -i evict

# Step 2: Test policy enforcement
kubectl apply -f opa-policy.yaml
kubectl run bad-pod --image=nginx --privileged=true  # Should be denied

# Step 3: Trace CRI calls
sudo strace -e trace=connect -p $(pgrep kubelet) 2>&1 | grep cri
sudo crictl --debug runp test-sandbox.json 2>&1 | tee cri-trace.log
```