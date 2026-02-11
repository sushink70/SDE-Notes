# Sidecar Pattern: Comprehensive Technical Deep-Dive

**Executive Summary:** Sidecars are auxiliary containers deployed alongside primary workload containers in the same execution context (Pod in K8s, Task in ECS, etc.), sharing lifecycle, network namespace, and optionally storage/IPC. They implement cross-cutting concerns (observability, security, networking) via process-level isolation rather than library injection, enabling polyglot support, independent scaling, and security boundaries. Core mechanism: shared kernel namespaces (net, ipc, pid optional) with separate filesystem/user namespaces. Used in service mesh data planes (Envoy), secret injection (Vault Agent), log shipping (Fluent Bit), security enforcement (OPA, Falco), and init-style setup tasks. Production deployments must account for resource contention, startup ordering, failure domains, and upgrade complexity.

---

## Architecture & Execution Model

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Pod / Task Group                          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Shared Network Namespace                   │  │
│  │  ┌──────────────────────┐      ┌────────────────────────┐    │  │
│  │  │  Primary Container   │      │  Sidecar Container     │    │  │
│  │  │  ┌────────────────┐  │      │  ┌──────────────────┐  │    │  │
│  │  │  │  App Process   │  │◄────►│  │  Proxy/Agent     │  │    │  │
│  │  │  │  (Port 8080)   │  │      │  │  (Intercepts)    │  │    │  │
│  │  │  └────────────────┘  │      │  └──────────────────┘  │    │  │
│  │  │  User NS: app-uid    │      │  User NS: sidecar-uid  │    │  │
│  │  │  FS: /app            │      │  FS: /sidecar          │    │  │
│  │  └──────────────────────┘      └────────────────────────┘    │  │
│  │           │                              │                    │  │
│  │           └──────────────┬───────────────┘                    │  │
│  │                          │                                    │  │
│  │         Shared: lo, eth0 (127.0.0.1, Pod IP)                  │  │
│  │         Optional: IPC namespace, PID namespace                │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              Shared Volumes (emptyDir, CSI)                   │  │
│  │  /shared-data    /vault/secrets    /tmp-socket               │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
         │                                      │
         │                                      │
    ┌────▼────┐                          ┌─────▼──────┐
    │  cgroup │                          │  seccomp   │
    │  limits │                          │  apparmor  │
    └─────────┘                          └────────────┘
```

---

## Core Concepts & Under-the-Hood Mechanisms

### 1. Namespace Sharing

**Network Namespace (Always Shared):**
```bash
# Inside Pod infrastructure container (pause/sand)
unshare --net --mount /bin/sh
ip link set lo up
# Primary and sidecar join this netns
nsenter --net=/proc/<pause-pid>/ns/net <container-cmd>
```

- **localhost communication:** App on 127.0.0.1:8080, sidecar binds 127.0.0.1:15001
- **iptables rules shared:** Envoy inserts REDIRECT rules visible to all containers
- **Socket visibility:** `/proc/net/tcp` shows all listening sockets

**IPC Namespace (Optional):**
```yaml
# K8s: shareProcessNamespace for SysV IPC, POSIX queues
spec:
  shareProcessNamespace: true  # Also shares PID
```

**PID Namespace:**
- When shared: sidecar sees app PIDs, enables `kill`, `ptrace` (if caps allow)
- Security tradeoff: broader attack surface vs. monitoring capability

### 2. Container Runtime Integration

**containerd/CRI-O Flow:**
```
1. CRI creates Pod sandbox (pause container) → netns, ipc, uts
2. Primary container: joins sandbox namespaces
   runc spec: "namespaces": [{"type": "network", "path": "/proc/<pause>/ns/net"}]
3. Sidecar container: same namespace join
4. Volume mounts: bind-propagated from host/CSI to both
```

**Docker Compose Equivalent:**
```yaml
services:
  app:
    image: myapp:latest
    network_mode: "service:shared-net"
  
  sidecar:
    image: envoyproxy/envoy:v1.28
    network_mode: "service:shared-net"
  
  shared-net:
    image: gcr.io/google-containers/pause:3.9
```

---

## Production Patterns

### Pattern 1: Service Mesh Data Plane (Envoy)

**Deployment:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-mesh
spec:
  initContainers:
  - name: istio-init
    image: istio/proxyv2:1.20.1
    command: ["istio-iptables"]
    args:
    - "-p" "15001"  # Envoy inbound
    - "-u" "1337"   # Envoy UID (don't redirect its traffic)
    - "-m" "REDIRECT"
    - "-i" "*"      # Capture all inbound
    - "-b" "*"      # Capture all ports
    securityContext:
      capabilities:
        add: ["NET_ADMIN", "NET_RAW"]
      runAsUser: 0
  
  containers:
  - name: app
    image: myapp:v1.2.3
    ports:
    - containerPort: 8080
  
  - name: istio-proxy
    image: istio/proxyv2:1.20.1
    args:
    - proxy
    - sidecar
    - --domain=$(POD_NAMESPACE).svc.cluster.local
    - --proxyLogLevel=warning
    - --proxyComponentLogLevel=misc:error
    env:
    - name: POD_NAMESPACE
      valueFrom:
        fieldRef:
          fieldPath: metadata.namespace
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
      limits:
        cpu: 2000m
        memory: 1Gi
    securityContext:
      runAsUser: 1337
      runAsGroup: 1337
      capabilities:
        drop: ["ALL"]
      readOnlyRootFilesystem: true
```

**Traffic Flow:**
```
Client → Pod IP:8080 
  → iptables PREROUTING (REDIRECT to 15001) 
  → Envoy listener 0.0.0.0:15001 
  → mTLS termination, authz policy check
  → Envoy upstream cluster 127.0.0.1:8080 
  → App container
```

**iptables Rules (simplified):**
```bash
# Inserted by istio-init
iptables -t nat -A PREROUTING -p tcp -j REDIRECT --to-ports 15001
iptables -t nat -A OUTPUT -p tcp -m owner --uid-owner 1337 -j RETURN  # Don't loop
iptables -t nat -A OUTPUT -p tcp -j REDIRECT --to-ports 15001
```

---

### Pattern 2: Secret Injection (Vault Agent)

**Vault Agent Sidecar:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-vault
spec:
  serviceAccountName: app-sa
  
  initContainers:
  - name: vault-agent-init
    image: hashicorp/vault:1.15
    args:
    - agent
    - -config=/vault/config/agent.hcl
    - -exit-after-auth
    volumeMounts:
    - name: vault-config
      mountPath: /vault/config
    - name: shared-secrets
      mountPath: /vault/secrets
    env:
    - name: VAULT_ADDR
      value: "https://vault.vault.svc:8200"
  
  containers:
  - name: app
    image: myapp:latest
    volumeMounts:
    - name: shared-secrets
      mountPath: /secrets
      readOnly: true
    # App reads /secrets/db-creds on startup
  
  - name: vault-agent
    image: hashicorp/vault:1.15
    args:
    - agent
    - -config=/vault/config/agent.hcl
    volumeMounts:
    - name: vault-config
      mountPath: /vault/config
    - name: shared-secrets
      mountPath: /vault/secrets
    resources:
      requests:
        cpu: 50m
        memory: 64Mi
  
  volumes:
  - name: vault-config
    configMap:
      name: vault-agent-config
  - name: shared-secrets
    emptyDir:
      medium: Memory  # tmpfs for secrets
```

**Agent Config (`agent.hcl`):**
```hcl
pid_file = "/tmp/pidfile"

vault {
  address = "https://vault.vault.svc:8200"
  tls_skip_verify = false
  ca_cert = "/vault/ca/ca.crt"
}

auto_auth {
  method {
    type = "kubernetes"
    config = {
      role = "app-role"
      token_path = "/var/run/secrets/kubernetes.io/serviceaccount/token"
    }
  }
  
  sink {
    type = "file"
    config = {
      path = "/vault/token"
    }
  }
}

template {
  source      = "/vault/config/db-creds.tmpl"
  destination = "/vault/secrets/db-creds.json"
  command     = "pkill -HUP app"  # Signal app to reload
}
```

**Threat Model:**
- **Attack:** Compromised app reads Vault token from `/vault/token`
- **Mitigation:** Agent uses response-wrapping, token is cubbyhole, single-use
- **Attack:** Sidecar compromise → persistent Vault access
- **Mitigation:** Short TTL tokens (5min), frequent re-auth, audit logs

---

### Pattern 3: Observability (Fluent Bit Log Shipper)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-logging
spec:
  containers:
  - name: app
    image: myapp:latest
    volumeMounts:
    - name: app-logs
      mountPath: /var/log/app
    # App writes to /var/log/app/access.log
  
  - name: fluent-bit
    image: fluent/fluent-bit:2.2
    volumeMounts:
    - name: app-logs
      mountPath: /var/log/app
      readOnly: true
    - name: fluent-bit-config
      mountPath: /fluent-bit/etc/
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
      limits:
        cpu: 500m
        memory: 256Mi
  
  volumes:
  - name: app-logs
    emptyDir: {}
  - name: fluent-bit-config
    configMap:
      name: fluent-bit-config
```

**Fluent Bit Config:**
```ini
[SERVICE]
    Flush         5
    Log_Level     info
    Parsers_File  parsers.conf

[INPUT]
    Name              tail
    Path              /var/log/app/*.log
    Tag               app.*
    Refresh_Interval  5
    Mem_Buf_Limit     5MB
    Skip_Long_Lines   On

[FILTER]
    Name                kubernetes
    Match               app.*
    Kube_URL            https://kubernetes.default.svc:443
    Kube_CA_File        /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    Kube_Token_File     /var/run/secrets/kubernetes.io/serviceaccount/token
    Merge_Log           On
    K8S-Logging.Parser  On
    K8S-Logging.Exclude Off

[OUTPUT]
    Name  es
    Match *
    Host  elasticsearch.logging.svc
    Port  9200
    Index fluentbit
    Type  _doc
    Logstash_Format On
    Retry_Limit False
```

---

### Pattern 4: Security Policy Enforcement (OPA)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-opa
spec:
  containers:
  - name: app
    image: myapp:latest
    env:
    - name: OPA_ADDR
      value: "http://127.0.0.1:8181"
  
  - name: opa
    image: openpolicyagent/opa:0.60.0
    args:
    - run
    - --server
    - --addr=127.0.0.1:8181
    - --bundle-service=bundle-server
    - --bundle-polling-interval=10s
    volumeMounts:
    - name: opa-config
      mountPath: /config
      readOnly: true
    livenessProbe:
      httpGet:
        path: /health
        port: 8181
      initialDelaySeconds: 5
    resources:
      requests:
        cpu: 50m
        memory: 64Mi
  
  volumes:
  - name: opa-config
    configMap:
      name: opa-config
```

**App Authorization Check:**
```go
// In app container
func checkAuthorization(user, action, resource string) (bool, error) {
    input := map[string]interface{}{
        "user":     user,
        "action":   action,
        "resource": resource,
    }
    
    resp, err := http.Post(
        "http://127.0.0.1:8181/v1/data/app/authz/allow",
        "application/json",
        marshal(input),
    )
    // Parse OPA decision
}
```

---

## Resource Management & Isolation

### CPU/Memory Limits

```yaml
# Prevent sidecar starvation
spec:
  containers:
  - name: app
    resources:
      requests:
        cpu: 1000m
        memory: 2Gi
      limits:
        cpu: 4000m
        memory: 4Gi
  
  - name: sidecar
    resources:
      requests:
        cpu: 100m      # Guaranteed slice
        memory: 128Mi
      limits:
        cpu: 2000m     # Burst capacity
        memory: 512Mi  # OOM before app
```

**cgroup Hierarchy:**
```
/sys/fs/cgroup/cpu/kubepods/burstable/<pod-uid>/
  ├── <app-container-id>/
  │   └── cpu.cfs_quota_us = 400000 (4 cores)
  └── <sidecar-container-id>/
      └── cpu.cfs_quota_us = 200000 (2 cores)
```

### I/O Priority

```yaml
# Prevent log shipper from starving app disk I/O
spec:
  containers:
  - name: fluent-bit
    securityContext:
      # Best-effort I/O class (CFQ scheduler)
      runAsNonRoot: true
    # Use ionice in entrypoint
    command: ["ionice", "-c3", "fluent-bit", "-c", "/fluent-bit/etc/fluent-bit.conf"]
```

---

## Startup Ordering & Dependencies

### Init Containers (Sequential)

```yaml
spec:
  initContainers:
  - name: 01-fetch-config
    image: busybox
    command: ["sh", "-c"]
    args:
    - |
      wget -O /config/app.yaml https://config-server/v1/config
      chmod 600 /config/app.yaml
    volumeMounts:
    - name: config
      mountPath: /config
  
  - name: 02-migrate-db
    image: migrate/migrate
    args: ["-path", "/migrations", "-database", "$(DB_URL)", "up"]
    env:
    - name: DB_URL
      valueFrom:
        secretKeyRef:
          name: db-creds
          key: url
  
  containers:
  - name: app
    # Starts only after init containers succeed
```

### Readiness Gates (K8s 1.14+)

```yaml
# App shouldn't receive traffic until sidecar ready
spec:
  readinessGates:
  - conditionType: "mesh.istio.io/proxy-ready"
  
  containers:
  - name: app
    readinessProbe:
      httpGet:
        path: /ready
        port: 8080
  
  - name: istio-proxy
    readinessProbe:
      httpGet:
        path: /ready
        port: 15021
```

### Lifecycle Hooks

```yaml
spec:
  containers:
  - name: app
    lifecycle:
      preStop:
        exec:
          command: ["/bin/sh", "-c", "sleep 15"]  # Wait for connections to drain
  
  - name: envoy
    lifecycle:
      preStop:
        exec:
          command: ["/usr/local/bin/pilot-agent", "request", "POST", 
                    "http://127.0.0.1:15000/drain_listeners?inboundonly"]
```

---

## Failure Modes & Blast Radius

### Sidecar Crash Impact

**RestartPolicy Interaction:**
```yaml
# Pod-level restart policy applies to ALL containers
spec:
  restartPolicy: Always
  
  # If sidecar crashes, kubelet restarts it
  # App continues running (unless PID namespace shared and sidecar was PID 1)
```

**Critical Sidecar Pattern:**
```yaml
# Make sidecar mandatory for app functionality
- name: envoy
  livenessProbe:
    httpGet:
      path: /server_info
      port: 15000
    failureThreshold: 3
  # If envoy fails, kubelet kills it → restarts → if still failing, backoff
  # App keeps running but can't send/receive traffic (iptables redirect to dead port)
```

**Mitigation: Health Aggregation**
```go
// App's /ready endpoint checks sidecar
func readyHandler(w http.ResponseWriter, r *http.Request) {
    if !checkSidecarReady("http://127.0.0.1:15021/ready") {
        http.Error(w, "Sidecar not ready", 503)
        return
    }
    w.WriteHeader(200)
}
```

### Resource Exhaustion

**Scenario: Log Explosion**
```
1. App bug → 10K logs/sec → Fluent Bit buffer fills
2. Fluent Bit OOMKilled (512Mi limit)
3. Kubelet restarts Fluent Bit (CrashLoopBackoff)
4. App logs lost during downtime
```

**Mitigation:**
```yaml
- name: fluent-bit
  env:
  - name: FLB_MEM_BUF_LIMIT
    value: "256MB"  # Per-input buffer limit
  resources:
    limits:
      memory: 512Mi
  # Rate limiting in config
  [INPUT]
      Mem_Buf_Limit  256MB
      Skip_Long_Lines On
```

---

## Security Boundaries

### User Namespace Isolation

```yaml
# K8s 1.25+ with user namespaces (alpha)
spec:
  securityContext:
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
  
  containers:
  - name: app
    securityContext:
      runAsNonRoot: true
      allowPrivilegeEscalation: false
  
  - name: sidecar
    securityContext:
      runAsUser: 2000  # Different UID
      capabilities:
        drop: ["ALL"]
      seccompProfile:
        type: RuntimeDefault
```

**Kernel-Level Mapping (User NS):**
```
Host:       UID 100000-165535
Container:  UID 0-65535
  App:        UID 1000 → Host UID 101000
  Sidecar:    UID 2000 → Host UID 102000
```

### Seccomp/AppArmor

```yaml
metadata:
  annotations:
    container.apparmor.security.beta.kubernetes.io/envoy: localhost/envoy-profile

spec:
  containers:
  - name: envoy
    securityContext:
      seccompProfile:
        type: Localhost
        localhostProfile: profiles/envoy.json
```

**Seccomp Profile (envoy.json):**
```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64"],
  "syscalls": [
    {"names": ["read", "write", "open", "close", "socket", "bind", "listen", "accept", "connect", "sendto", "recvfrom", "epoll_create", "epoll_ctl", "epoll_wait", "mmap", "munmap", "futex", "clone"], "action": "SCMP_ACT_ALLOW"}
  ]
}
```

### Network Policies

```yaml
# Only sidecar can egress to external IPs
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: app-egress
spec:
  podSelector:
    matchLabels:
      app: myapp
  policyTypes:
  - Egress
  egress:
  - to:
    - podSelector: {}  # Allow to all pods in namespace
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: TCP
      port: 53  # CoreDNS
  # Block direct external egress from app
  # Sidecar enforces via iptables OWNER match
```

---

## Testing & Validation

### Unit Test: Namespace Sharing

```go
// Test that sidecar sees app's listening port
func TestNetworkNamespaceShared(t *testing.T) {
    ctx := context.Background()
    cli, _ := client.NewClientWithOpts(client.FromEnv)
    
    // Create network
    net, _ := cli.NetworkCreate(ctx, "test-net", types.NetworkCreate{})
    defer cli.NetworkRemove(ctx, net.ID)
    
    // App container
    appResp, _ := cli.ContainerCreate(ctx, &container.Config{
        Image: "nginx:alpine",
    }, &container.HostConfig{
        NetworkMode: container.NetworkMode(net.ID),
    }, nil, nil, "app")
    cli.ContainerStart(ctx, appResp.ID, types.ContainerStartOptions{})
    defer cli.ContainerRemove(ctx, appResp.ID, types.ContainerRemoveOptions{Force: true})
    
    // Sidecar container
    sidecarResp, _ := cli.ContainerCreate(ctx, &container.Config{
        Image: "alpine",
        Cmd:   []string{"sh", "-c", "netstat -tuln | grep 80"},
    }, &container.HostConfig{
        NetworkMode: container.NetworkMode("container:" + appResp.ID),
    }, nil, nil, "sidecar")
    
    cli.ContainerStart(ctx, sidecarResp.ID, types.ContainerStartOptions{})
    statusCh, _ := cli.ContainerWait(ctx, sidecarResp.ID, container.WaitConditionNotRunning)
    <-statusCh
    
    logs, _ := cli.ContainerLogs(ctx, sidecarResp.ID, types.ContainerLogsOptions{ShowStdout: true})
    buf := new(strings.Builder)
    io.Copy(buf, logs)
    
    assert.Contains(t, buf.String(), ":80", "Sidecar should see nginx port 80")
}
```

### Integration Test: Istio Injection

```bash
#!/bin/bash
set -euo pipefail

# Deploy app without sidecar
kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: test-app
  namespace: default
spec:
  containers:
  - name: app
    image: kennethreitz/httpbin
    ports:
    - containerPort: 80
EOF

# Wait for ready
kubectl wait --for=condition=ready pod/test-app --timeout=60s

# Verify no sidecar
[ $(kubectl get pod test-app -o json | jq '.spec.containers | length') -eq 1 ]

# Enable injection
kubectl label namespace default istio-injection=enabled

# Recreate pod
kubectl delete pod test-app
kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: test-app
  namespace: default
spec:
  containers:
  - name: app
    image: kennethreitz/httpbin
EOF

kubectl wait --for=condition=ready pod/test-app --timeout=120s

# Verify sidecar injected
CONTAINER_COUNT=$(kubectl get pod test-app -o json | jq '.spec.containers | length')
[ "$CONTAINER_COUNT" -eq 2 ] || exit 1

# Verify iptables rules
kubectl exec test-app -c istio-proxy -- iptables -t nat -L -n | grep 15001
```

### Load Test: Resource Contention

```go
// Simulate app + sidecar CPU competition
func BenchmarkCPUContention(b *testing.B) {
    // Start CPU-bound sidecar task
    sidecarDone := make(chan struct{})
    go func() {
        for {
            select {
            case <-sidecarDone:
                return
            default:
                // Hash computation (simulate Envoy crypto)
                sha256.Sum256(make([]byte, 1024))
            }
        }
    }()
    defer close(sidecarDone)
    
    // Measure app request latency
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        resp, err := http.Get("http://127.0.0.1:8080/api/test")
        if err != nil || resp.StatusCode != 200 {
            b.Fatalf("Request failed: %v", err)
        }
        resp.Body.Close()
    }
}
```

---

## Rollout & Rollback Strategies

### Canary Deployment with Sidecar Version

```yaml
# Production pods with Envoy 1.27
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-stable
spec:
  replicas: 9
  template:
    metadata:
      annotations:
        sidecar.istio.io/proxyImage: istio/proxyv2:1.27.0
    spec:
      containers:
      - name: app
        image: myapp:v2.1.0

---
# Canary pods with Envoy 1.28
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-canary
spec:
  replicas: 1
  template:
    metadata:
      annotations:
        sidecar.istio.io/proxyImage: istio/proxyv2:1.28.0
    spec:
      containers:
      - name: app
        image: myapp:v2.1.0  # Same app version
```

**Traffic Split (Istio VirtualService):**
```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: myapp-canary
spec:
  hosts:
  - myapp.default.svc.cluster.local
  http:
  - match:
    - headers:
        x-canary:
          exact: "true"
    route:
    - destination:
        host: myapp-canary
  - route:
    - destination:
        host: myapp-stable
      weight: 90
    - destination:
        host: myapp-canary
      weight: 10
```

### Rollback Procedure

```bash
#!/bin/bash
# Automated rollback on sidecar failure

# Monitor canary error rate
ERROR_RATE=$(kubectl exec -n istio-system deploy/istio-ingressgateway -- \
  pilot-agent request GET 'http://127.0.0.1:15000/stats/prometheus' | \
  grep 'envoy_cluster_upstream_rq_5xx{cluster_name="outbound|80||myapp-canary"}' | \
  awk '{print $2}')

TOTAL_REQ=$(kubectl exec -n istio-system deploy/istio-ingressgateway -- \
  pilot-agent request GET 'http://127.0.0.1:15000/stats/prometheus' | \
  grep 'envoy_cluster_upstream_rq_total{cluster_name="outbound|80||myapp-canary"}' | \
  awk '{print $2}')

if (( $(echo "$ERROR_RATE / $TOTAL_REQ > 0.05" | bc -l) )); then
  echo "Error rate >5%, rolling back canary"
  kubectl patch deployment myapp-canary -p '{"spec":{"template":{"metadata":{"annotations":{"sidecar.istio.io/proxyImage":"istio/proxyv2:1.27.0"}}}}}'
  kubectl rollout restart deployment/myapp-canary
fi
```

---

## Advanced Patterns

### Pattern: Dynamic Sidecar Injection (MutatingWebhook)

```go
// Webhook that injects OPA sidecar based on annotation
func mutatePod(ar *v1beta1.AdmissionReview) *v1beta1.AdmissionResponse {
    pod := &corev1.Pod{}
    json.Unmarshal(ar.Request.Object.Raw, pod)
    
    if pod.Annotations["opa-injection"] != "enabled" {
        return &v1beta1.AdmissionResponse{Allowed: true}
    }
    
    opaSidecar := corev1.Container{
        Name:  "opa",
        Image: "openpolicyagent/opa:0.60.0",
        Args:  []string{"run", "--server", "--addr=127.0.0.1:8181"},
        Resources: corev1.ResourceRequirements{
            Requests: corev1.ResourceList{
                corev1.ResourceCPU:    resource.MustParse("50m"),
                corev1.ResourceMemory: resource.MustParse("64Mi"),
            },
        },
    }
    
    patches := []patchOperation{
        {
            Op:    "add",
            Path:  "/spec/containers/-",
            Value: opaSidecar,
        },
    }
    
    patchBytes, _ := json.Marshal(patches)
    return &v1beta1.AdmissionResponse{
        Allowed: true,
        Patch:   patchBytes,
        PatchType: func() *v1beta1.PatchType {
            pt := v1beta1.PatchTypeJSONPatch
            return &pt
        }(),
    }}
```

### Pattern: eBPF-based Sidecar (Cilium)

```yaml
# Replace userspace proxy with kernel eBPF for lower latency
apiVersion: v1
kind: Pod
metadata:
  name: app-with-ebpf
  annotations:
    io.cilium.proxy-visibility: "<Egress/53/UDP/DNS>,<Ingress/80/TCP/HTTP>"
spec:
  containers:
  - name: app
    image: myapp:latest
  # No sidecar container needed
  # Cilium daemonset injects eBPF programs into kernel

# CNI plugin flow:
# 1. Cilium agent compiles BPF bytecode for policy
# 2. Attaches to Pod's veth pair via TC (traffic control)
# 3. BPF program inspects/redirects packets in kernel
# 4. L7 visibility via sockmap (socket-level redirect)
```

**Comparison: Envoy vs eBPF**
```
Metric              | Envoy Sidecar | Cilium eBPF
--------------------|---------------|-------------
Latency (p99)       | 2-5ms         | 50-200μs
CPU overhead        | 100-500m      | 10-50m
Memory overhead     | 128-512Mi     | 20-50Mi
L7 visibility       | Full (HTTP/gRPC/Kafka) | HTTP only (limited)
mTLS termination    | Yes           | No (requires sidecar)
Deployment model    | Per-pod       | Per-node (DaemonSet)
Security boundary   | Process       | Kernel (higher trust)
```

---

## Cross-Platform Implementations

### ECS Sidecar (AWS Fargate)

```json
{
  "family": "app-with-sidecar",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "app",
      "image": "123456789.dkr.ecr.us-east-1.amazonaws.com/myapp:latest",
      "portMappings": [{"containerPort": 8080, "protocol": "tcp"}],
      "cpu": 768,
      "memory": 1536,
      "dependsOn": [
        {
          "containerName": "envoy",
          "condition": "HEALTHY"
        }
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    },
    {
      "name": "envoy",
      "image": "840364872350.dkr.ecr.us-west-2.amazonaws.com/aws-appmesh-envoy:v1.27.0.0",
      "essential": true,
      "cpu": 256,
      "memory": 512,
      "environment": [
        {"name": "APPMESH_RESOURCE_ARN", "value": "arn:aws:appmesh:us-east-1:123456789:mesh/my-mesh/virtualNode/app-vn"}
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -s http://localhost:9901/ready | grep LIVE"],
        "interval": 5,
        "timeout": 2,
        "retries": 3
      },
      "user": "1337"
    },
    {
      "name": "xray-daemon",
      "image": "public.ecr.aws/xray/aws-xray-daemon:latest",
      "cpu": 32,
      "memory": 256,
      "portMappings": [{"containerPort": 2000, "protocol": "udp"}]
    }
  ],
  "proxyConfiguration": {
    "type": "APPMESH",
    "containerName": "envoy",
    "properties": [
      {"name": "IgnoredUID", "value": "1337"},
      {"name": "ProxyIngressPort", "value": "15000"},
      {"name": "ProxyEgressPort", "value": "15001"},
      {"name": "AppPorts", "value": "8080"},
      {"name": "EgressIgnoredIPs", "value": "169.254.170.2,169.254.169.254"}
    ]
  }
}
```

**ECS Proxy Config Translation:**
```bash
# ECS task launch injects iptables rules via proxyConfiguration
iptables -t nat -A PREROUTING -p tcp -d 169.254.170.2 --dport 80 -j ACCEPT  # Task metadata
iptables -t nat -A PREROUTING -p tcp -j REDIRECT --to-ports 15000
iptables -t nat -A OUTPUT -p tcp -m owner --uid-owner 1337 -j RETURN
iptables -t nat -A OUTPUT -p tcp --dport 8080 -j REDIRECT --to-ports 15001
```

### Cloud Run Sidecar (GCP)

```yaml
# Cloud Run doesn't support traditional sidecars (single container per service)
# Workaround: Use multi-process supervisor
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: app-with-sidecar
spec:
  template:
    spec:
      containers:
      - name: app-and-sidecar
        image: gcr.io/myproject/app-bundle:latest
        ports:
        - containerPort: 8080
        resources:
          limits:
            cpu: "2"
            memory: 2Gi
        env:
        - name: PORT
          value: "8080"

# Dockerfile for multi-process container
FROM golang:1.21 AS builder
COPY . .
RUN go build -o /app ./cmd/app
RUN go build -o /sidecar ./cmd/sidecar

FROM gcr.io/distroless/base
COPY --from=builder /app /app
COPY --from=builder /sidecar /sidecar
COPY supervisord.conf /etc/supervisord.conf
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]
```

**Note:** This violates true sidecar pattern (process isolation), but is necessary workaround for Cloud Run.

### Azure Container Instances

```json
{
  "name": "app-with-sidecar",
  "properties": {
    "containers": [
      {
        "name": "app",
        "properties": {
          "image": "myregistry.azurecr.io/myapp:latest",
          "resources": {
            "requests": {"cpu": 1.0, "memoryInGB": 1.5}
          },
          "ports": [{"port": 80}]
        }
      },
      {
        "name": "dapr",
        "properties": {
          "image": "daprio/daprd:1.12",
          "command": [
            "/daprd",
            "--app-id", "myapp",
            "--app-port", "80",
            "--dapr-http-port", "3500",
            "--dapr-grpc-port", "50001"
          ],
          "resources": {
            "requests": {"cpu": 0.5, "memoryInGB": 0.5}
          }
        }
      }
    ],
    "osType": "Linux",
    "ipAddress": {
      "type": "Public",
      "ports": [{"protocol": "TCP", "port": 80}]
    }
  }
}
```

---

## Performance Optimization

### Zero-Copy Socket Passing (Unix Domain Sockets)

```yaml
# Avoid TCP loopback overhead
spec:
  containers:
  - name: app
    volumeMounts:
    - name: sockets
      mountPath: /var/run/app
  
  - name: envoy
    volumeMounts:
    - name: sockets
      mountPath: /var/run/app
    args:
    - --config-path /etc/envoy/envoy.yaml
  
  volumes:
  - name: sockets
    emptyDir: {}
```

**Envoy Config (UDS listener):**
```yaml
static_resources:
  listeners:
  - name: app_listener
    address:
      pipe:
        path: /var/run/app/app.sock
    filter_chains:
    - filters:
      - name: envoy.filters.network.http_connection_manager
        typed_config:
          "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
          stat_prefix: ingress_http
          route_config:
            name: local_route
            virtual_hosts:
            - name: backend
              domains: ["*"]
              routes:
              - match: {prefix: "/"}
                route:
                  cluster: app_cluster

  clusters:
  - name: app_cluster
    connect_timeout: 0.25s
    type: STATIC
    load_assignment:
      cluster_name: app_cluster
      endpoints:
      - lb_endpoints:
        - endpoint:
            address:
              pipe:
                path: /var/run/app/upstream.sock
```

**App Server (Go):**
```go
// Listen on UDS instead of TCP
func main() {
    os.Remove("/var/run/app/upstream.sock")
    listener, err := net.Listen("unix", "/var/run/app/upstream.sock")
    if err != nil {
        log.Fatal(err)
    }
    defer listener.Close()
    
    os.Chmod("/var/run/app/upstream.sock", 0666)
    
    http.Serve(listener, handler)
}
```

**Performance Gain:**
```
Benchmark: 100K requests, 1KB payload
TCP loopback (127.0.0.1:8080):  p50=1.2ms, p99=4.5ms
UDS:                             p50=0.8ms, p99=2.1ms
Gain: 33% p50, 53% p99 latency reduction
```

### Shared Memory (POSIX SHM)

```c
// App writes metrics to shared memory
#include <sys/mman.h>
#include <fcntl.h>

struct metrics {
    uint64_t request_count;
    uint64_t error_count;
    double avg_latency_ms;
};

int main() {
    int fd = shm_open("/app_metrics", O_CREAT | O_RDWR, 0666);
    ftruncate(fd, sizeof(struct metrics));
    
    struct metrics *m = mmap(NULL, sizeof(struct metrics),
                             PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    
    while (1) {
        // Update atomically
        __atomic_add_fetch(&m->request_count, 1, __ATOMIC_SEQ_CST);
    }
}
```

```go
// Sidecar reads from shared memory
import "golang.org/x/sys/unix"

func readMetrics() {
    fd, _ := unix.ShmOpen("/app_metrics", unix.O_RDONLY, 0)
    defer unix.Close(fd)
    
    data, _ := unix.Mmap(fd, 0, 64, unix.PROT_READ, unix.MAP_SHARED)
    defer unix.Munmap(data)
    
    // Cast to struct and read
    requestCount := *(*uint64)(unsafe.Pointer(&data[0]))
}
```

---

## Monitoring & Observability

### Sidecar-Specific Metrics

**Prometheus Scrape Config:**
```yaml
scrape_configs:
- job_name: 'kubernetes-pods'
  kubernetes_sd_configs:
  - role: pod
  
  relabel_configs:
  # Scrape app container
  - source_labels: [__meta_kubernetes_pod_container_name]
    action: keep
    regex: app
  - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
    action: keep
    regex: true
  - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_port]
    action: replace
    target_label: __address__
    regex: ([^:]+)(?::\d+)?
    replacement: $1:8080

- job_name: 'kubernetes-pods-sidecar'
  kubernetes_sd_configs:
  - role: pod
  
  relabel_configs:
  # Scrape sidecar container
  - source_labels: [__meta_kubernetes_pod_container_name]
    action: keep
    regex: (envoy|istio-proxy)
  - source_labels: [__address__]
    action: replace
    target_label: __address__
    regex: ([^:]+)(?::\d+)?
    replacement: $1:15090  # Envoy stats port
```

**Key Metrics to Alert On:**
```promql
# Sidecar high memory usage
container_memory_working_set_bytes{container="istio-proxy"} / 
container_spec_memory_limit_bytes{container="istio-proxy"} > 0.9

# Sidecar high CPU throttling
rate(container_cpu_cfs_throttled_seconds_total{container="istio-proxy"}[5m]) > 0.5

# Sidecar crash loop
rate(kube_pod_container_status_restarts_total{container="istio-proxy"}[15m]) > 0

# Sidecar not ready
kube_pod_container_status_ready{container="istio-proxy"} == 0
```

### Distributed Tracing

**OpenTelemetry Collector Sidecar:**
```yaml
spec:
  containers:
  - name: app
    env:
    - name: OTEL_EXPORTER_OTLP_ENDPOINT
      value: "http://127.0.0.1:4317"
  
  - name: otel-collector
    image: otel/opentelemetry-collector:0.91.0
    args: ["--config=/conf/otel-collector-config.yaml"]
    volumeMounts:
    - name: otel-config
      mountPath: /conf
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
  
  volumes:
  - name: otel-config
    configMap:
      name: otel-collector-config
```

**Collector Config:**
```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 127.0.0.1:4317
      http:
        endpoint: 127.0.0.1:4318

processors:
  batch:
    timeout: 10s
    send_batch_size: 1024
  
  resource:
    attributes:
    - key: service.name
      value: myapp
      action: upsert
    - key: pod.name
      from_attribute: k8s.pod.name
      action: insert

exporters:
  otlp:
    endpoint: tempo.monitoring.svc:4317
    tls:
      insecure: false
      ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch, resource]
      exporters: [otlp]
```

---

## Threat Modeling

### Attack Surface Analysis

**Threat: Container Escape → Lateral Movement**
```
1. Attacker exploits app RCE
2. Escalates to root in app container
3. Attempts kernel exploit (CVE-2022-0847 "Dirty Pipe")
4. Escapes to host → accesses sidecar container's secrets
```

**Mitigations:**
```yaml
# Defense in depth
spec:
  securityContext:
    runAsNonRoot: true
    seccompProfile:
      type: RuntimeDefault
  
  containers:
  - name: app
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
      readOnlyRootFilesystem: true
  
  - name: sidecar
    securityContext:
      runAsUser: 65534  # nobody
      capabilities:
        drop: ["ALL"]
      readOnlyRootFilesystem: true
  
  # Separate service accounts
  serviceAccountName: app-sa

---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: sidecar-sa
# Mount sidecar SA token in sidecar only
```

**Threat: Sidecar Compromise → Credential Theft**
```
1. Envoy vulnerability (CVE-2023-XXXX)
2. Attacker gains code execution in sidecar
3. Reads app's /secrets volume
4. Exfiltrates DB credentials
```

**Mitigations:**
```yaml
# Separate secret volumes per container
spec:
  containers:
  - name: app
    volumeMounts:
    - name: app-secrets
      mountPath: /secrets
      readOnly: true
  
  - name: envoy
    # No access to app secrets
    volumeMounts:
    - name: envoy-certs
      mountPath: /etc/envoy/certs
      readOnly: true
  
  volumes:
  - name: app-secrets
    secret:
      secretName: app-db-creds
      defaultMode: 0400  # Read-only for owner
  - name: envoy-certs
    secret:
      secretName: envoy-tls-certs
```

### Supply Chain Security

**Sidecar Image Verification:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-verified
spec:
  containers:
  - name: app
    image: myregistry.io/myapp@sha256:abc123...  # Digest pinning
  
  - name: envoy
    image: istio/proxyv2@sha256:def456...
  
  # Admission controller validates signatures
  # (Sigstore/Cosign, Notary v2)
```

**Admission Policy (Kyverno):**
```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-sidecar-images
spec:
  validationFailureAction: enforce
  rules:
  - name: verify-istio-proxy
    match:
      resources:
        kinds:
        - Pod
    verifyImages:
    - imageReferences:
      - "istio/proxyv2:*"
      attestors:
      - count: 1
        entries:
        - keys:
            publicKeys: |-
              -----BEGIN PUBLIC KEY-----
              MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...
              -----END PUBLIC KEY-----
```

---

## Cost Optimization

### Resource Right-Sizing

**Vertical Pod Autoscaler for Sidecars:**
```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: envoy-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: istio-proxy
      minAllowed:
        cpu: 50m
        memory: 64Mi
      maxAllowed:
        cpu: 1000m
        memory: 512Mi
      controlledResources: ["cpu", "memory"]
```

**Cost Analysis:**
```bash
# Calculate sidecar overhead across cluster
kubectl get pods -A -o json | jq -r '
  .items[] | 
  select(.spec.containers | length > 1) |
  .spec.containers[] |
  select(.name | contains("proxy") or contains("sidecar")) |
  {
    pod: .metadata.name,
    cpu: .resources.requests.cpu,
    mem: .resources.requests.memory
  }
' | jq -s 'map(.cpu | rtrimstr("m") | tonumber) | add'

# Output: 45000 (45 cores across all sidecars)
# At $0.04/core-hour = $1,800/month just for sidecars
```

**Optimization: Ambient Mesh (Istio 1.18+)**
```yaml
# Remove per-pod sidecars, use per-node ztunnel
# Cost: 2 cores/node vs 100m/pod
# Savings: 90%+ for clusters with >20 pods/node
```

---

## Debugging Techniques

### Enter Sidecar Namespace

```bash
# Debug network issues from sidecar's perspective
kubectl debug -it pod/myapp --image=nicolaka/netshoot \
  --target=istio-proxy -- /bin/bash

# Now in sidecar's network namespace
netstat -tuln  # See Envoy listeners
ss -tanp | grep envoy
tcpdump -i any -w /tmp/capture.pcap port 15001
```

### Trace iptables Flow

```bash
# Enable iptables tracing
kubectl exec pod/myapp -c istio-proxy -- \
  iptables -t raw -A PREROUTING -p tcp --dport 8080 -j TRACE

# View trace
kubectl exec pod/myapp -c istio-proxy -- \
  tail -f /var/log/messages | grep TRACE
```

### BPF Tracing (bpftrace)

```bash
# Trace sidecar's syscalls
kubectl exec -it pod/myapp -c istio-proxy -- \
  bpftrace -e '
    tracepoint:syscalls:sys_enter_sendto /comm == "envoy"/ {
      printf("%s sent %d bytes\n", comm, args->len);
    }
  '
```

---

## Alternatives & Trade-offs

| Approach | Pros | Cons | Use When |
|----------|------|------|----------|
| **Sidecar** | Strong isolation, language-agnostic, independent lifecycle | Resource overhead, complex networking, startup ordering | Multi-language apps, security boundaries needed |
| **Library/SDK** | No overhead, simpler deployment, faster | Vendor lock-in, language-specific, app rebuilds for updates | Homogeneous tech stack, trusted code |
| **DaemonSet** | Lower cost (shared per node), simpler updates | Weaker isolation, noisy neighbor risk, single point of failure | Trusted environment, cost-sensitive |
| **eBPF/Ambient** | Minimal overhead, kernel-level security | Limited L7 features, kernel version dependency, trust kernel | High-scale, latency-critical, cost-sensitive |
| **Out-of-process Agent** | Decoupled, can run privileged | Network hop penalty, config complexity | Legacy apps, external control plane |

---

## Next 3 Steps

1. **Deploy Reference Implementation**
   ```bash
   # Clone production-ready sidecar patterns
   git clone https://github.com/istio/istio
   cd istio/samples/bookinfo
   kubectl apply -f <(istioctl kube-inject -f platform/kube/bookinfo.yaml)
   
   # Observe traffic flow
   kubectl exec -it deploy/productpage-v1 -c istio-proxy -- \
     pilot-agent request GET http://127.0.0.1:15000/config_dump > config.json
   ```

2. **Build Custom Sidecar**
   ```bash
   # Example: Rate-limiting sidecar in Rust
   cargo new --bin ratelimit-sidecar
   # Implement: listen on 15001, proxy to 127.0.0.1:8080 with token bucket
   # Test: Deploy alongside app, verify rate limits
   ```

3. **Conduct Load Test**
   ```bash
   # Measure sidecar overhead
   kubectl apply -f <(cat <<EOF
   apiVersion: v1
   kind: Pod
   metadata:
     name: baseline
   spec:
     containers:
     - name: app
       image: nginx
   ---
   apiVersion: v1
   kind: Pod
   metadata:
     name: with-sidecar
   spec:
     containers:
     - name: app
       image: nginx
     - name: envoy
       image: envoyproxy/envoy:v1.28
   EOF
   )
   
   # Benchmark both
   wrk -t12 -c400 -d30s http://<baseline-ip>
   wrk -t12 -c400 -d30s http://<with-sidecar-ip>
   ```

---

## References

**Official Specs:**
- OCI Runtime Spec (namespace mechanics): https://github.com/opencontainers/runtime-spec/blob/main/config-linux.md#namespaces
- Kubernetes Pod Spec: https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/pod-v1/
- Linux namespaces man page: `man 7 namespaces`

**Production Implementations:**
- Istio sidecar injection: https://github.com/istio/istio/tree/master/pkg/kube/inject
- Linkerd proxy: https://github.com/linkerd/linkerd2-proxy
- Dapr runtime: https://github.com/dapr/dapr
- AWS App Mesh Envoy: https://github.com/aws/aws-app-mesh-examples

**Security Hardening:**
- CIS Kubernetes Benchmark (sidecar sections): https://www.cisecurity.org/benchmark/kubernetes
- NSA/CISA Kubernetes Hardening Guide: https://media.defense.gov/2022/Aug/29/2003066362/-1/-1/0/CTR_KUBERNETES_HARDENING_GUIDANCE_1.2_20220829.PDF
- Seccomp profiles: https://github.com/kubernetes/kubernetes/tree/master/test/seccomp

**Performance Studies:**
- Istio performance benchmarks: https://istio.io/latest/docs/ops/deployment/performance-and-scalability/
- CNCF Network Performance WG: https://github.com/cncf/cnf-wg/tree/main/network-performance