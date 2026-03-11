# Kubernetes Workload Resources: Comprehensive Security-First Guide

## Executive Summary

Kubernetes workload resources are declarative API objects that manage pod lifecycle, scheduling, and scaling across cluster nodes. **Deployments** provide declarative rolling updates for stateless apps; **StatefulSets** guarantee stable network identity and persistent storage for stateful workloads; **DaemonSets** ensure exactly one pod per node for system-level agents; **Jobs** run pods to completion; **CronJobs** schedule Jobs on time-based triggers; **ReplicaSets** (underlying Deployments) maintain desired pod replica counts. Under the hood, these controllers run reconciliation loops in kube-controller-manager, watching API server state and orchestrating pod creation/deletion through the scheduler and kubelet. Security boundaries include RBAC for API access, Pod Security Standards for runtime policy, network policies for traffic control, and admission webhooks for policy enforcement at creation time.

---

## Architecture: Controller Pattern & Pod Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Server (etcd)                        │
│  Stores desired state: Deployment, StatefulSet, Job, etc.      │
└──────────────┬──────────────────────────────────────────────────┘
               │ Watch/List API
               │
┌──────────────▼──────────────────────────────────────────────────┐
│              kube-controller-manager                            │
│  ┌──────────────┐  ┌───────────────┐  ┌─────────────┐         │
│  │  Deployment  │  │  StatefulSet  │  │     Job     │         │
│  │  Controller  │  │  Controller   │  │  Controller │  ...    │
│  └──────┬───────┘  └───────┬───────┘  └──────┬──────┘         │
│         │                  │                  │                 │
│         └──────────────────┼──────────────────┘                 │
│                            │ Reconciliation Loop                │
│                            │ (Observe → Diff → Act)             │
└────────────────────────────┼────────────────────────────────────┘
                             │
                ┌────────────▼────────────┐
                │   ReplicaSet (owned)    │
                │   StatefulSet manages   │
                │   Pods directly         │
                └────────────┬────────────┘
                             │
            ┌────────────────▼────────────────┐
            │          kube-scheduler         │
            │  Assigns Pods to Nodes          │
            │  (affinity, taints, resources)  │
            └────────────┬────────────────────┘
                         │
        ┌────────────────▼────────────────┐
        │          kubelet (Node)         │
        │  ┌──────────────────────────┐   │
        │  │  CRI (containerd/cri-o)  │   │
        │  │  ┌────────┐  ┌────────┐  │   │
        │  │  │  Pod1  │  │  Pod2  │  │   │
        │  │  └────────┘  └────────┘  │   │
        │  └──────────────────────────┘   │
        └─────────────────────────────────┘

Security Boundaries:
├─ RBAC: Who can create/modify workload resources
├─ Admission: Validating/Mutating webhooks (OPA, Kyverno)
├─ PSA/PSS: Pod Security Admission enforces standards
├─ Network Policy: L3/L4 traffic isolation between Pods
└─ Runtime: seccomp, AppArmor, SELinux, User Namespaces
```

---

## 1. ReplicaSet (Foundation)

### Core Concepts

**ReplicaSet** ensures a specified number of pod replicas are running at any given time. It's the primitive underlying Deployments. Direct use is rare—Deployments are preferred for declarative updates.

**Controller Logic (under the hood):**
```go
// Simplified reconciliation loop
func (rs *ReplicaSetController) syncReplicaSet(key string) error {
    replicaSet := getReplicaSet(key)
    allPods := listPods(replicaSet.Spec.Selector)
    
    filteredPods := filterActivePods(allPods)
    diff := replicaSet.Spec.Replicas - len(filteredPods)
    
    if diff > 0 {
        // Scale up: create pods
        createPods(diff, replicaSet.Spec.Template)
    } else if diff < 0 {
        // Scale down: delete pods
        deletePods(-diff, filteredPods)
    }
    
    updateStatus(replicaSet, len(filteredPods))
}
```

**Key Fields:**
- `spec.replicas`: Desired pod count
- `spec.selector`: Label selector matching pods
- `spec.template`: Pod template (metadata + spec)
- `status.replicas`, `status.readyReplicas`, `status.availableReplicas`

### Security & Isolation

**Threat Model:**
- **Pod Escape → Horizontal Movement**: Compromised pod uses node credentials to enumerate/delete other pods
- **Label Selector Hijacking**: Attacker modifies labels to orphan pods or attach to wrong ReplicaSet
- **Resource Exhaustion**: Malicious ReplicaSet spec creates thousands of pods

**Mitigations:**
```yaml
# 1. RBAC: Restrict who can create/modify ReplicaSets
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: prod
  name: replicaset-operator
rules:
- apiGroups: ["apps"]
  resources: ["replicasets"]
  verbs: ["get", "list", "watch", "create", "update", "patch"]
  # Never "delete" or "*" in production
  
# 2. Resource Quotas: Prevent DoS
apiVersion: v1
kind: ResourceQuota
metadata:
  namespace: prod
spec:
  hard:
    pods: "100"
    requests.cpu: "50"
    requests.memory: 100Gi
    
# 3. PodSecurity: Enforce baseline/restricted
apiVersion: v1
kind: Namespace
metadata:
  name: prod
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### Validation Steps

```bash
# Create ReplicaSet
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: nginx-rs
  namespace: default
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
      tier: frontend
  template:
    metadata:
      labels:
        app: nginx
        tier: frontend
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 2000
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: nginx
        image: nginx:1.25-alpine
        securityContext:
          allowPrivilegeEscalation: false
          capabilities:
            drop: ["ALL"]
          readOnlyRootFilesystem: true
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 200m
            memory: 256Mi
        volumeMounts:
        - name: cache
          mountPath: /var/cache/nginx
        - name: run
          mountPath: /var/run
      volumes:
      - name: cache
        emptyDir: {}
      - name: run
        emptyDir: {}
EOF

# Verify reconciliation
kubectl get rs nginx-rs -o wide
kubectl get pods -l app=nginx --show-labels

# Test scaling
kubectl scale rs nginx-rs --replicas=5
watch -n1 'kubectl get pods -l app=nginx | grep -E "Running|Pending"'

# Observe controller behavior
kubectl get events --field-selector involvedObject.name=nginx-rs

# Test pod deletion (should recreate)
POD=$(kubectl get pod -l app=nginx -o name | head -1)
kubectl delete $POD
# Verify new pod created within seconds

# Cleanup
kubectl delete rs nginx-rs
```

---

## 2. Deployment (Declarative Updates)

### Core Concepts

**Deployment** provides declarative updates for Pods via ReplicaSets. It manages rollout strategy, rollback, and version history. This is the primary workload resource for stateless applications.

**Update Strategies:**
1. **RollingUpdate** (default): Gradually replace old pods with new ones
2. **Recreate**: Delete all old pods before creating new ones (downtime)

**Under the Hood (RollingUpdate):**
```
Deployment v2 created
  ├─ Creates new ReplicaSet-v2 (replicas: 0)
  ├─ Scales up RS-v2 by maxSurge
  ├─ Waits for pods to be Ready
  ├─ Scales down RS-v1 by maxUnavailable
  ├─ Repeats until RS-v2 has all replicas
  └─ RS-v1 scaled to 0 (retained for rollback)

Timeline:
  RS-v1: 3 → 3 → 2 → 1 → 0
  RS-v2: 0 → 1 → 2 → 3 → 3
         └── maxSurge=1, maxUnavailable=1
```

**Key Fields:**
- `spec.strategy.type`: RollingUpdate | Recreate
- `spec.strategy.rollingUpdate.maxSurge`: Max pods over desired count (default 25%)
- `spec.strategy.rollingUpdate.maxUnavailable`: Max pods unavailable (default 25%)
- `spec.revisionHistoryLimit`: Number of old ReplicaSets to retain (default 10)
- `spec.progressDeadlineSeconds`: Timeout for rollout progress (default 600s)
- `spec.minReadySeconds`: Min seconds for pod to be considered ready

### Production Patterns

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
  namespace: prod
  annotations:
    # GitOps: track source commit
    config.kubernetes.io/origin: |
      git@github.com:org/repo.git/deploy/api.yaml
    kubernetes.io/change-cause: "Update to v1.2.3 - CVE-2024-XXXX patch"
spec:
  replicas: 10
  revisionHistoryLimit: 5
  progressDeadlineSeconds: 300
  minReadySeconds: 10  # Wait 10s after Ready before next pod
  
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 2        # At most 12 pods during rollout
      maxUnavailable: 1  # At least 9 pods available
      
  selector:
    matchLabels:
      app: api-server
      
  template:
    metadata:
      labels:
        app: api-server
        version: v1.2.3
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
    spec:
      # Anti-affinity: spread across nodes/zones
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchLabels:
                  app: api-server
              topologyKey: kubernetes.io/hostname
          - weight: 50
            podAffinityTerm:
              labelSelector:
                matchLabels:
                  app: api-server
              topologyKey: topology.kubernetes.io/zone
              
      # Service Account for workload identity
      serviceAccountName: api-server
      automountServiceAccountToken: false  # Mount only if needed
      
      # Security hardening
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        fsGroup: 10001
        seccompProfile:
          type: RuntimeDefault
        
      # Init containers for setup
      initContainers:
      - name: wait-db
        image: busybox:1.36
        command: ['sh', '-c', 'until nc -z postgres 5432; do sleep 1; done']
        securityContext:
          allowPrivilegeEscalation: false
          capabilities:
            drop: ["ALL"]
          readOnlyRootFilesystem: true
          
      containers:
      - name: api
        image: registry.internal/api-server:v1.2.3
        imagePullPolicy: IfNotPresent
        
        ports:
        - name: http
          containerPort: 8080
          protocol: TCP
        - name: metrics
          containerPort: 9090
          protocol: TCP
          
        env:
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: POD_NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        - name: DB_HOST
          value: postgres.data.svc.cluster.local
        envFrom:
        - secretRef:
            name: api-secrets
            
        # Probes for rollout health
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8080
            scheme: HTTP
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
          
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
          successThreshold: 1
          
        startupProbe:
          httpGet:
            path: /healthz
            port: 8080
          initialDelaySeconds: 0
          periodSeconds: 5
          failureThreshold: 30  # 150s max startup time
          
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 2000m
            memory: 2Gi
            
        securityContext:
          allowPrivilegeEscalation: false
          capabilities:
            drop: ["ALL"]
          readOnlyRootFilesystem: true
          
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: cache
          mountPath: /app/cache
          
      volumes:
      - name: tmp
        emptyDir:
          sizeLimit: 1Gi
      - name: cache
        emptyDir:
          sizeLimit: 5Gi
          
      # Topology spread for HA
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: ScheduleAnyway
        labelSelector:
          matchLabels:
            app: api-server
```

### Rollout & Rollback

```bash
# Apply deployment
kubectl apply -f api-deployment.yaml

# Watch rollout
kubectl rollout status deployment/api-server -n prod
# Output: Waiting for deployment "api-server" rollout to finish: 2 out of 10 new replicas have been updated...

# Monitor in detail
watch -n1 'kubectl get rs -n prod -l app=api-server'

# View rollout history
kubectl rollout history deployment/api-server -n prod
# REVISION  CHANGE-CAUSE
# 1         Initial deployment
# 2         Update to v1.2.3 - CVE-2024-XXXX patch

# Rollback to previous version
kubectl rollout undo deployment/api-server -n prod

# Rollback to specific revision
kubectl rollout undo deployment/api-server -n prod --to-revision=1

# Pause rollout (canary testing)
kubectl rollout pause deployment/api-server -n prod
# ... validate metrics, errors, latency ...
kubectl rollout resume deployment/api-server -n prod

# Restart deployment (recreate all pods)
kubectl rollout restart deployment/api-server -n prod
```

### Security Considerations

**Threat Model:**
- **Image Vulnerabilities**: Outdated base images, CVEs
- **Rollout Poisoning**: Attacker deploys malicious image
- **Privilege Escalation**: Pods run as root, mount host paths
- **Secret Exposure**: Environment variables logged, secrets in images

**Mitigations:**
```yaml
# 1. Image signing & verification (sigstore/cosign)
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-images
spec:
  validationFailureAction: Enforce
  rules:
  - name: verify-signature
    match:
      resources:
        kinds:
        - Pod
    verifyImages:
    - imageReferences:
      - "registry.internal/*"
      attestors:
      - entries:
        - keys:
            publicKeys: |-
              -----BEGIN PUBLIC KEY-----
              ...
              -----END PUBLIC KEY-----

# 2. Image scanning (Trivy, Grype)
# Pre-deployment in CI/CD
trivy image --severity HIGH,CRITICAL registry.internal/api-server:v1.2.3

# 3. Runtime security (Falco)
# Detect anomalous behavior
- rule: Unexpected outbound connection
  condition: outbound and not allowed_destinations
  output: "Suspicious connection from %container.name to %fd.rip"

# 4. Network policies
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-server-netpol
  namespace: prod
spec:
  podSelector:
    matchLabels:
      app: api-server
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: ingress-nginx
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
  - to:  # DNS
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: kube-system
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53
```

### Testing & Validation

```bash
# 1. Dry-run validation
kubectl apply -f api-deployment.yaml --dry-run=server

# 2. Admission policy testing
kubectl run test --image=nginx --dry-run=server

# 3. Load testing during rollout
# Terminal 1: Start rollout
kubectl set image deployment/api-server api=registry.internal/api-server:v1.2.4 -n prod

# Terminal 2: Generate load
k6 run - <<EOF
import http from 'k6/http';
import { check } from 'k6';

export let options = {
  stages: [
    { duration: '5m', target: 1000 },
  ],
};

export default function() {
  let res = http.get('http://api-server.prod.svc.cluster.local:8080/api/v1/health');
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
}
EOF

# Terminal 3: Monitor error rate
kubectl logs -f -n prod -l app=api-server | grep ERROR

# 4. Rollback test
kubectl rollout undo deployment/api-server -n prod
kubectl rollout status deployment/api-server -n prod

# 5. Chaos testing (pod deletion)
for i in {1..10}; do
  POD=$(kubectl get pod -n prod -l app=api-server -o name | shuf -n1)
  kubectl delete -n prod $POD
  sleep 5
done
# Verify: curl should never fail
```

---

## 3. StatefulSet (Stable Identity & Storage)

### Core Concepts

**StatefulSet** manages stateful applications requiring:
- **Stable network identity**: Predictable DNS names (`pod-0.service.namespace.svc.cluster.local`)
- **Stable persistent storage**: PVCs tied to pod identity
- **Ordered deployment/scaling**: Pods created/deleted sequentially
- **Ordered updates**: Rolling updates proceed in reverse ordinal order

**Identity Guarantees:**
```
StatefulSet: cassandra
Service (Headless): cassandra  # clusterIP: None

Pods:
  cassandra-0 → cassandra-0.cassandra.default.svc.cluster.local
  cassandra-1 → cassandra-1.cassandra.default.svc.cluster.local
  cassandra-2 → cassandra-2.cassandra.default.svc.cluster.local

PVCs (never deleted automatically):
  data-cassandra-0 → Bound to cassandra-0
  data-cassandra-1 → Bound to cassandra-1
  data-cassandra-2 → Bound to cassandra-2
```

**Scaling Behavior:**
```
Scale Up (3→5):
  1. Create cassandra-3, wait for Running+Ready
  2. Create cassandra-4, wait for Running+Ready

Scale Down (5→3):
  1. Delete cassandra-4, wait for termination
  2. Delete cassandra-3, wait for termination
  Note: PVCs data-cassandra-3, data-cassandra-4 remain (manual cleanup)
```

### Under the Hood

**Controller Logic:**
```go
// Simplified StatefulSet reconciliation
func (ssc *StatefulSetController) syncStatefulSet(key string) error {
    sts := getStatefulSet(key)
    pods := listPods(sts.Spec.Selector)
    
    // Sort by ordinal: pod-0, pod-1, pod-2, ...
    sort.Sort(byOrdinal(pods))
    
    // Ensure PVCs exist for all replicas
    for i := 0; i < sts.Spec.Replicas; i++ {
        ensurePVC(sts, i)  // Creates data-<sts>-<i>
    }
    
    // Deployment: 0 → replicas
    for i := 0; i < sts.Spec.Replicas; i++ {
        if !podExists(pods, i) {
            createPod(sts, i)
            return nil  // Wait for next reconciliation
        }
        if !isPodReady(pods[i]) {
            return nil  // Wait for pod to be Ready
        }
    }
    
    // Scale down: replicas → current
    for i := len(pods)-1; i >= sts.Spec.Replicas; i-- {
        deletePod(pods[i])
        return nil  // Sequential deletion
    }
    
    // Rolling update (OnDelete or RollingUpdate)
    if sts.Spec.UpdateStrategy.Type == RollingUpdate {
        for i := len(pods)-1; i >= 0; i-- {
            if needsUpdate(pods[i], sts.Spec.Template) {
                deletePod(pods[i])
                return nil  // Recreate on next reconcile
            }
        }
    }
}
```

### Production Example: Distributed Database

```yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: data
  labels:
    app: postgres
spec:
  # Headless service for stable DNS
  clusterIP: None
  selector:
    app: postgres
  ports:
  - name: postgres
    port: 5432
    targetPort: 5432
  - name: replication
    port: 5433
    targetPort: 5433
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: data
spec:
  serviceName: postgres
  replicas: 3
  podManagementPolicy: OrderedReady  # Default: sequential startup
  # podManagementPolicy: Parallel  # Start all pods simultaneously
  
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 0  # Update pods with ordinal >= partition
      
  selector:
    matchLabels:
      app: postgres
      
  # PVC template (creates per-pod PVCs)
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 100Gi
          
  template:
    metadata:
      labels:
        app: postgres
    spec:
      securityContext:
        runAsUser: 999  # postgres user
        runAsGroup: 999
        fsGroup: 999
        fsGroupChangePolicy: OnRootMismatch
        seccompProfile:
          type: RuntimeDefault
          
      # Termination grace period for clean shutdown
      terminationGracePeriodSeconds: 60
      
      initContainers:
      - name: init-config
        image: postgres:16-alpine
        command:
        - sh
        - -c
        - |
          set -ex
          # Determine if primary or replica
          ordinal=${HOSTNAME##*-}
          if [ "$ordinal" = "0" ]; then
            echo "primary_conninfo = ''" > /config/replica.conf
          else
            echo "primary_conninfo = 'host=postgres-0.postgres port=5432 user=replicator password=$REPL_PASSWORD'" > /config/replica.conf
          fi
        env:
        - name: REPL_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-repl
              key: password
        volumeMounts:
        - name: config
          mountPath: /config
        securityContext:
          allowPrivilegeEscalation: false
          capabilities:
            drop: ["ALL"]
          readOnlyRootFilesystem: true
          
      containers:
      - name: postgres
        image: postgres:16-alpine
        ports:
        - name: postgres
          containerPort: 5432
        - name: replication
          containerPort: 5433
          
        env:
        - name: POSTGRES_DB
          value: app
        - name: POSTGRES_USER
          value: app
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-app
              key: password
        - name: PGDATA
          value: /var/lib/postgresql/data/pgdata
        - name: POD_IP
          valueFrom:
            fieldRef:
              fieldPath: status.podIP
              
        # Lifecycle hooks
        lifecycle:
          preStop:
            exec:
              command:
              - /bin/sh
              - -c
              - |
                # Graceful shutdown: promote replica or flush WAL
                pg_ctl stop -D $PGDATA -m fast -w -t 30
                
        livenessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - pg_isready -U app -h 127.0.0.1
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
          
        readinessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - pg_isready -U app -h 127.0.0.1 && [ -f /tmp/ready ]
          initialDelaySeconds: 5
          periodSeconds: 5
          
        resources:
          requests:
            cpu: 2000m
            memory: 4Gi
          limits:
            cpu: 4000m
            memory: 8Gi
            
        securityContext:
          allowPrivilegeEscalation: false
          capabilities:
            drop: ["ALL"]
          # Note: readOnlyRootFilesystem not compatible with postgres
          # Use tmpfs for writable paths instead
          
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
        - name: config
          mountPath: /etc/postgres
        - name: tmp
          mountPath: /tmp
        - name: run
          mountPath: /var/run/postgresql
          
      volumes:
      - name: config
        emptyDir: {}
      - name: tmp
        emptyDir:
          sizeLimit: 1Gi
      - name: run
        emptyDir:
          medium: Memory
          sizeLimit: 100Mi
```

### Operations

```bash
# Deploy StatefulSet
kubectl apply -f postgres-sts.yaml

# Watch pods come up sequentially
watch -n1 'kubectl get pods -n data -l app=postgres'
# postgres-0   0/1   ContainerCreating
# postgres-0   1/1   Running          ← waits for Ready
# postgres-1   0/1   ContainerCreating
# postgres-1   1/1   Running
# postgres-2   0/1   ContainerCreating
# postgres-2   1/1   Running

# Verify stable DNS
kubectl run -it --rm debug --image=postgres:16-alpine -n data -- bash
$ for i in 0 1 2; do
    nslookup postgres-$i.postgres.data.svc.cluster.local
  done
# Each resolves to pod IP

# Verify PVCs
kubectl get pvc -n data
# NAME               STATUS   VOLUME    CAPACITY   STORAGECLASS
# data-postgres-0    Bound    pvc-xxx   100Gi      fast-ssd
# data-postgres-1    Bound    pvc-yyy   100Gi      fast-ssd
# data-postgres-2    Bound    pvc-zzz   100Gi      fast-ssd

# Test scaling
kubectl scale sts postgres -n data --replicas=5
# Creates postgres-3, then postgres-4 sequentially

# Scale down
kubectl scale sts postgres -n data --replicas=3
# Deletes postgres-4, then postgres-3
# PVCs remain! (manual cleanup required)

# Rolling update with partition
kubectl patch sts postgres -n data -p '{"spec":{"updateStrategy":{"rollingUpdate":{"partition":2}}}}'
kubectl set image sts/postgres -n data postgres=postgres:16.1-alpine
# Only postgres-2 updated (ordinal >= partition)
# Test, then partition=1, then partition=0

# Clean delete (removes pods but NOT PVCs)
kubectl delete sts postgres -n data
kubectl delete pvc -n data -l app=postgres  # Manual cleanup
```

### Security: Encryption at Rest

```yaml
# StorageClass with encrypted volumes
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: encrypted-ssd
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  encrypted: "true"
  kmsKeyId: arn:aws:kms:us-east-1:123456789012:key/abcd-1234
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer

---
# Use in StatefulSet
volumeClaimTemplates:
- metadata:
    name: data
  spec:
    storageClassName: encrypted-ssd
    accessModes: ["ReadWriteOnce"]
    resources:
      requests:
        storage: 100Gi
```

### Backup & Disaster Recovery

```bash
# 1. Snapshot PVCs (CSI driver)
kubectl create -f - <<EOF
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: postgres-0-snap-$(date +%Y%m%d-%H%M%S)
  namespace: data
spec:
  volumeSnapshotClassName: csi-snapclass
  source:
    persistentVolumeClaimName: data-postgres-0
EOF

# 2. Application-level backup (pg_dump)
kubectl exec -n data postgres-0 -- pg_dumpall -U app > backup-$(date +%Y%m%d).sql

# 3. Restore from snapshot
# Edit PVC to use volumeSnapshot as dataSource
kubectl patch pvc data-postgres-0 -n data --type merge -p '
spec:
  dataSource:
    name: postgres-0-snap-20240209-120000
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io'
```

---

## 4. DaemonSet (Node-Level Agents)

### Core Concepts

**DaemonSet** ensures exactly one pod runs on each (or selected) node. Used for system-level services: logging, monitoring, security agents, storage drivers.

**Scheduling:**
- Creates pod on every node matching `nodeSelector` / `affinity` / `tolerations`
- Bypasses normal scheduling (uses DaemonSet controller scheduler)
- Survives node drain/cordon (unless pod has `eviction` configured)

**Update Strategies:**
1. **RollingUpdate**: Gradual rollout (default)
2. **OnDelete**: Manual deletion triggers update

### Production Example: Security Monitoring

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: falco
  namespace: security
  labels:
    app: falco
spec:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1  # Update one node at a time
      
  selector:
    matchLabels:
      app: falco
      
  template:
    metadata:
      labels:
        app: falco
    spec:
      # Run on all nodes (including control plane if needed)
      tolerations:
      - key: node-role.kubernetes.io/control-plane
        operator: Exists
        effect: NoSchedule
      - key: node-role.kubernetes.io/master  # Legacy
        operator: Exists
        effect: NoSchedule
        
      # Priority: ensure critical security agent runs
      priorityClassName: system-node-critical
      
      # Host namespaces for kernel visibility
      hostNetwork: true
      hostPID: true
      
      # Service account for event forwarding
      serviceAccountName: falco
      
      containers:
      - name: falco
        image: falcosecurity/falco:0.37.0
        imagePullPolicy: IfNotPresent
        
        args:
        - /usr/bin/falco
        - -K
        - /var/run/secrets/kubernetes.io/serviceaccount/token
        - -k
        - https://$(KUBERNETES_SERVICE_HOST)
        - -pk
        
        env:
        - name: FALCO_K8S_NODE_NAME
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName
              
        securityContext:
          # Privileged required for kernel module or eBPF
          privileged: true
          # Alternatives: use eBPF driver with CAP_SYS_ADMIN
          # capabilities:
          #   add: ["SYS_ADMIN", "SYS_PTRACE", "SYS_RESOURCE"]
          
        resources:
          requests:
            cpu: 100m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1Gi
            
        volumeMounts:
        # Kernel headers for module compilation
        - name: lib-modules
          mountPath: /lib/modules
          readOnly: true
        - name: usr-src
          mountPath: /usr/src
          readOnly: true
        # Container runtime socket for enrichment
        - name: containerd-sock
          mountPath: /run/containerd/containerd.sock
        # Proc filesystem
        - name: proc
          mountPath: /host/proc
          readOnly: true
        # Config
        - name: config
          mountPath: /etc/falco
          
      volumes:
      - name: lib-modules
        hostPath:
          path: /lib/modules
      - name: usr-src
        hostPath:
          path: /usr/src
      - name: containerd-sock
        hostPath:
          path: /run/containerd/containerd.sock
      - name: proc
        hostPath:
          path: /proc
      - name: config
        configMap:
          name: falco-config
---
# ConfigMap with Falco rules
apiVersion: v1
kind: ConfigMap
metadata:
  name: falco-config
  namespace: security
data:
  falco.yaml: |
    rules_file:
      - /etc/falco/rules.d/falco_rules.yaml
      - /etc/falco/rules.d/custom_rules.yaml
    json_output: true
    json_include_output_property: true
    log_stderr: true
    log_syslog: false
    priority: notice
    
  custom_rules.yaml: |
    - rule: Unexpected outbound connection
      desc: Detect outbound connections from pods to internet
      condition: >
        outbound and 
        not fd.sip in (allowed_ips) and
        container.image.repository startswith "registry.internal/"
      output: >
        Unexpected outbound connection
        (connection=%fd.name user=%user.name container=%container.name
        image=%container.image.repository:%container.image.tag)
      priority: WARNING
      
    - rule: Sensitive file access
      desc: Detect access to /etc/shadow or SSH keys
      condition: >
        open_read and 
        (fd.name=/etc/shadow or fd.name startswith /home/ and fd.name endswith .ssh/)
      output: >
        Sensitive file read
        (file=%fd.name user=%user.name container=%container.name)
      priority: ERROR
```

### Node Selection

```yaml
# Run only on specific nodes
spec:
  template:
    spec:
      nodeSelector:
        disktype: ssd
        region: us-west-2
        
      # Or use affinity for complex logic
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: kubernetes.io/arch
                operator: In
                values:
                - amd64
                - arm64
              - key: node.kubernetes.io/instance-type
                operator: NotIn
                values:
                - t2.micro  # Skip small instances
```

### Validation

```bash
# Deploy DaemonSet
kubectl apply -f falco-ds.yaml

# Verify pod on each node
kubectl get ds -n security falco
# NAME    DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR
# falco   5         5         5       5            5           <none>

kubectl get pods -n security -o wide
# falco-abc   node-1
# falco-def   node-2
# falco-ghi   node-3
# falco-jkl   node-4
# falco-mno   node-5

# Test: add new node
# DaemonSet controller automatically schedules pod on new node

# Update DaemonSet
kubectl set image ds/falco -n security falco=falcosecurity/falco:0.37.1
kubectl rollout status ds/falco -n security

# Monitor rollout (one node at a time due to maxUnavailable: 1)
watch -n1 'kubectl get pods -n security -l app=falco'

# View logs
kubectl logs -n security -l app=falco --tail=100 -f | grep CRITICAL
```

### Security Considerations

**Threat Model:**
- **Kernel Module Exploit**: Malicious falco image loads backdoor kernel module
- **Host Escape**: Container escapes via hostPath or privileged mode
- **Data Exfiltration**: Agent forwards sensitive /proc data externally

**Mitigations:**
```yaml
# 1. Use eBPF instead of kernel module (no privileged)
# falco-ebpf driver requires CAP_BPF (Kubernetes 1.29+)
spec:
  template:
    spec:
      containers:
      - name: falco
        image: falcosecurity/falco:0.37.0-driver-loader
        env:
        - name: DRIVER_KIND
          value: ebpf
        securityContext:
          capabilities:
            add:
            - BPF
            - SYS_RESOURCE
            - PERFMON
            - SYS_PTRACE
          privileged: false

# 2. Image verification
# Ensure DaemonSet images are signed
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-daemonset-images
spec:
  validationFailureAction: Enforce
  rules:
  - name: verify-falco
    match:
      resources:
        kinds:
        - DaemonSet
    verifyImages:
    - imageReferences:
      - "falcosecurity/falco:*"
      attestors:
      - entries:
        - keys:
            publicKeys: |-
              -----BEGIN PUBLIC KEY-----
              ...
              -----END PUBLIC KEY-----

# 3. Network policy for agent
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: falco-egress
  namespace: security
spec:
  podSelector:
    matchLabels:
      app: falco
  policyTypes:
  - Egress
  egress:
  - to:  # Kubernetes API
    - namespaceSelector: {}
      podSelector:
        matchLabels:
          component: kube-apiserver
    ports:
    - protocol: TCP
      port: 6443
  - to:  # Metrics/logging backend
    - podSelector:
        matchLabels:
          app: prometheus
    ports:
    - protocol: TCP
      port: 9090
```

---

## 5. Job (Run to Completion)

### Core Concepts

**Job** creates one or more pods and ensures they successfully terminate. Used for batch processing, data migration, backups, cron tasks.

**Completion Modes:**
1. **Non-parallel** (default): Single pod, restarts on failure
2. **Parallel with fixed count**: N pods run in parallel
3. **Work queue**: Pods coordinate via external queue

**Termination:**
- **Success**: Pod exit code 0
- **Failure**: Pod exit code non-zero, restarts based on `restartPolicy`
- **Backoff**: Exponential backoff on failures (6s, 12s, 24s, ... max 6min)

### Production Example: Database Migration

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migrate-v1.2.3
  namespace: data
  annotations:
    kubernetes.io/change-cause: "Migration for v1.2.3 - add user_preferences table"
spec:
  # Backoff limit: max retries before marking failed
  backoffLimit: 3
  
  # Completion: require 1 successful pod
  completions: 1
  parallelism: 1
  
  # Cleanup: delete after 1 week
  ttlSecondsAfterFinished: 604800
  
  # Timeout: fail if not complete within 30 min
  activeDeadlineSeconds: 1800
  
  template:
    metadata:
      labels:
        app: db-migrate
        version: v1.2.3
    spec:
      restartPolicy: OnFailure  # Required for Jobs (Never | OnFailure)
      
      serviceAccountName: db-migrator
      
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
        seccompProfile:
          type: RuntimeDefault
          
      # Init: validate connectivity
      initContainers:
      - name: check-db
        image: postgres:16-alpine
        command:
        - sh
        - -c
        - |
          until pg_isready -h postgres-0.postgres -U app; do
            echo "Waiting for database..."
            sleep 2
          done
        env:
        - name: PGPASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-app
              key: password
        securityContext:
          allowPrivilegeEscalation: false
          capabilities:
            drop: ["ALL"]
          readOnlyRootFilesystem: true
          
      containers:
      - name: migrate
        image: registry.internal/db-migrator:v1.2.3
        command:
        - /bin/sh
        - -c
        - |
          set -e
          echo "Starting migration v1.2.3"
          
          # Acquire advisory lock to prevent concurrent migrations
          psql -c "SELECT pg_advisory_lock(123456);"
          
          # Run migration
          /app/migrate up
          
          # Release lock
          psql -c "SELECT pg_advisory_unlock(123456);"
          
          echo "Migration complete"
          
        env:
        - name: DATABASE_URL
          value: postgres://app@postgres-0.postgres:5432/app
        - name: PGPASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-app
              key: password
              
        resources:
          requests:
            cpu: 500m
            memory: 256Mi
          limits:
            cpu: 1000m
            memory: 512Mi
            
        securityContext:
          allowPrivilegeEscalation: false
          capabilities:
            drop: ["ALL"]
          readOnlyRootFilesystem: true
          
        volumeMounts:
        - name: migrations
          mountPath: /app/migrations
          readOnly: true
        - name: tmp
          mountPath: /tmp
          
      volumes:
      - name: migrations
        configMap:
          name: db-migrations-v1.2.3
      - name: tmp
        emptyDir:
          sizeLimit: 100Mi
```

### Parallel Processing

```yaml
# Process 100 items, 10 at a time
apiVersion: batch/v1
kind: Job
metadata:
  name: process-images
  namespace: default
spec:
  completions: 100      # Total successful pods required
  parallelism: 10       # Max concurrent pods
  backoffLimit: 5
  
  template:
    spec:
      restartPolicy: OnFailure
      containers:
      - name: processor
        image: registry.internal/image-processor:latest
        command:
        - /bin/sh
        - -c
        - |
          # Get unique work item from queue
          ITEM_ID=$(curl -X POST http://work-queue/claim)
          
          # Process
          /app/process --item-id=$ITEM_ID
          
          # Mark complete
          curl -X POST http://work-queue/complete/$ITEM_ID
```

### Operations

```bash
# Create job
kubectl apply -f db-migrate-job.yaml

# Monitor progress
kubectl get jobs -n data db-migrate-v1.2.3
# NAME                 COMPLETIONS   DURATION   AGE
# db-migrate-v1.2.3    0/1           2s         2s

watch -n1 'kubectl get pods -n data -l app=db-migrate'

# View logs
kubectl logs -n data -l app=db-migrate -f

# Job succeeded
kubectl get jobs -n data db-migrate-v1.2.3
# NAME                 COMPLETIONS   DURATION   AGE
# db-migrate-v1.2.3    1/1           45s        1m

# Cleanup (or wait for TTL)
kubectl delete job db-migrate-v1.2.3 -n data

# Failed job: inspect
kubectl describe job failed-job -n data
# Events: BackoffLimitExceeded

# Get failed pod logs
kubectl logs -n data $(kubectl get pod -n data -l job-name=failed-job -o name)

# Manual retry: delete and recreate
kubectl delete job failed-job -n data
kubectl apply -f failed-job.yaml
```

### Security: Least Privilege

```yaml
# ServiceAccount with minimal RBAC
apiVersion: v1
kind: ServiceAccount
metadata:
  name: db-migrator
  namespace: data
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: db-migrator
  namespace: data
rules:
# No API access needed for migration job
# Only if job needs to read ConfigMaps/Secrets
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list"]
  resourceNames: ["db-migrations-v1.2.3"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: db-migrator
  namespace: data
subjects:
- kind: ServiceAccount
  name: db-migrator
roleRef:
  kind: Role
  name: db-migrator
  apiGroup: rbac.authorization.k8s.io
```

---

## 6. CronJob (Scheduled Jobs)

### Core Concepts

**CronJob** creates Jobs on a time-based schedule (cron format). Used for periodic tasks: backups, reports, cleanup, monitoring.

**Schedule Format:**
```
┌───────────── minute (0-59)
│ ┌───────────── hour (0-23)
│ │ ┌───────────── day of month (1-31)
│ │ │ ┌───────────── month (1-12)
│ │ │ │ ┌───────────── day of week (0-6, Sunday=0)
│ │ │ │ │
* * * * *

Examples:
"0 2 * * *"        # Daily at 2 AM
"*/15 * * * *"     # Every 15 minutes
"0 0 * * 0"        # Weekly on Sunday midnight
"0 3 1 * *"        # Monthly on 1st at 3 AM
```

**Concurrency Policy:**
- `Allow` (default): Allow concurrent jobs
- `Forbid`: Skip new job if previous still running
- `Replace`: Cancel previous job, start new

### Production Example: Backup

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
  namespace: data
spec:
  # Daily at 2 AM UTC
  schedule: "0 2 * * *"
  
  # Timezone (Kubernetes 1.27+)
  timeZone: "America/New_York"
  
  # Concurrency: don't start if previous backup running
  concurrencyPolicy: Forbid
  
  # History: keep last 3 successful, 1 failed
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  
  # Deadline: start job within 5 min of scheduled time
  startingDeadlineSeconds: 300
  
  # Suspend: pause without deleting
  suspend: false
  
  jobTemplate:
    spec:
      backoffLimit: 2
      ttlSecondsAfterFinished: 86400  # Delete job after 1 day
      activeDeadlineSeconds: 3600     # Max 1 hour runtime
      
      template:
        metadata:
          labels:
            app: postgres-backup
        spec:
          restartPolicy: OnFailure
          
          serviceAccountName: backup-agent
          
          securityContext:
            runAsNonRoot: true
            runAsUser: 1000
            fsGroup: 1000
            seccompProfile:
              type: RuntimeDefault
              
          containers:
          - name: backup
            image: registry.internal/postgres-backup:latest
            command:
            - /bin/sh
            - -c
            - |
              set -e
              BACKUP_FILE="/backup/postgres-$(date +%Y%m%d-%H%M%S).sql.gz"
              
              echo "Starting backup to $BACKUP_FILE"
              
              # Dump database
              pg_dumpall -h postgres-0.postgres -U app | gzip > $BACKUP_FILE
              
              # Upload to S3
              aws s3 cp $BACKUP_FILE s3://backups/postgres/
              
              # Cleanup local file
              rm $BACKUP_FILE
              
              # Prune old backups (keep 30 days)
              aws s3 ls s3://backups/postgres/ | while read -r line; do
                createDate=$(echo $line | awk '{print $1" "$2}')
                createTimestamp=$(date -d "$createDate" +%s)
                olderThan=$(date -d "30 days ago" +%s)
                if [[ $createTimestamp -lt $olderThan ]]; then
                  fileName=$(echo $line | awk '{print $4}')
                  aws s3 rm s3://backups/postgres/$fileName
                fi
              done
              
              echo "Backup complete"
              
            env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-app
                  key: password
            - name: AWS_ACCESS_KEY_ID
              valueFrom:
                secretKeyRef:
                  name: s3-backup
                  key: access-key-id
            - name: AWS_SECRET_ACCESS_KEY
              valueFrom:
                secretKeyRef:
                  name: s3-backup
                  key: secret-access-key
                  
            resources:
              requests:
                cpu: 500m
                memory: 1Gi
              limits:
                cpu: 2000m
                memory: 4Gi
                
            securityContext:
              allowPrivilegeEscalation: false
              capabilities:
                drop: ["ALL"]
              readOnlyRootFilesystem: true
              
            volumeMounts:
            - name: backup
              mountPath: /backup
              
          volumes:
          - name: backup
            emptyDir:
              sizeLimit: 50Gi
```

### Operations

```bash
# Create CronJob
kubectl apply -f postgres-backup-cronjob.yaml

# View CronJob
kubectl get cronjob -n data postgres-backup
# NAME              SCHEDULE    SUSPEND   ACTIVE   LAST SCHEDULE   AGE
# postgres-backup   0 2 * * *   False     0        12h             5d

# View created Jobs
kubectl get jobs -n data -l app=postgres-backup
# NAME                        COMPLETIONS   DURATION   AGE
# postgres-backup-28493920    1/1           3m         12h
# postgres-backup-28480560    1/1           3m         1d
# postgres-backup-28467200    1/1           3m         2d

# Manual trigger (create Job immediately)
kubectl create job --from=cronjob/postgres-backup manual-backup-$(date +%s) -n data

# Suspend CronJob
kubectl patch cronjob postgres-backup -n data -p '{"spec":{"suspend":true}}'

# Resume
kubectl patch cronjob postgres-backup -n data -p '{"spec":{"suspend":false}}'

# Delete CronJob (doesn't delete existing Jobs)
kubectl delete cronjob postgres-backup -n data
```

### Monitoring & Alerting

```yaml
# Prometheus ServiceMonitor for job metrics
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: cronjob-monitor
  namespace: data
spec:
  selector:
    matchLabels:
      app: postgres-backup
  endpoints:
  - port: metrics
---
# PrometheusRule for failed backups
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: backup-alerts
  namespace: data
spec:
  groups:
  - name: backups
    interval: 30s
    rules:
    - alert: BackupJobFailed
      expr: kube_job_failed{job_name=~"postgres-backup.*"} > 0
      for: 5m
      annotations:
        summary: "Backup job {{ $labels.job_name }} failed"
        description: "Postgres backup failed. Check logs immediately."
      labels:
        severity: critical
        
    - alert: BackupJobMissing
      expr: time() - kube_cronjob_next_schedule_time{cronjob="postgres-backup"} > 3600
      for: 10m
      annotations:
        summary: "Backup job hasn't run in over 1 hour"
        description: "CronJob postgres-backup may be suspended or failing to schedule."
      labels:
        severity: warning
```

---

## Threat Model & Defense-in-Depth

### Attack Surface

```
┌─────────────────────────────────────────────────────────┐
│ Layer 1: API Access (Control Plane)                    │
├─────────────────────────────────────────────────────────┤
│ Threats:                                                │
│ • Unauthorized workload creation (crypto miners)        │
│ • Privilege escalation via privileged pods             │
│ • Secret theft via pod exec/logs                       │
│ • Resource exhaustion (fork bombs, CPU/mem limits)     │
├─────────────────────────────────────────────────────────┤
│ Mitigations:                                            │
│ ✓ RBAC: Least privilege (no wildcard verbs/resources)  │
│ ✓ Admission: OPA/Kyverno policies                      │
│ ✓ PSA: Enforce restricted profile                      │
│ ✓ Resource Quotas: Namespace limits                    │
│ ✓ Audit Logging: API request trail                     │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Layer 2: Container Runtime (Data Plane)                │
├─────────────────────────────────────────────────────────┤
│ Threats:                                                │
│ • Container escape via kernel exploit                   │
│ • Host path mount → file system tampering              │
│ • Privileged containers → node compromise              │
│ • Supply chain attack (malicious images)               │
├─────────────────────────────────────────────────────────┤
│ Mitigations:                                            │
│ ✓ seccomp: Block dangerous syscalls                    │
│ ✓ AppArmor/SELinux: MAC enforcement                    │
│ ✓ User Namespaces: Non-root UIDs in containers         │
│ ✓ Image Scanning: CVE detection (Trivy, Grype)         │
│ ✓ Image Signing: Cosign verification                   │
│ ✓ Read-only root filesystem                            │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Layer 3: Network (Pod-to-Pod)                          │
├─────────────────────────────────────────────────────────┤
│ Threats:                                                │
│ • Lateral movement after pod compromise                │
│ • Data exfiltration to external IPs                    │
│ • Man-in-the-middle (unencrypted traffic)              │
│ • DNS spoofing                                          │
├─────────────────────────────────────────────────────────┤
│ Mitigations:                                            │
│ ✓ Network Policies: Default deny, allowlist            │
│ ✓ Service Mesh: mTLS (Istio, Linkerd)                  │
│ ✓ Egress Gateway: Controlled internet access           │
│ ✓ DNS Policy: ClusterFirst, DNSSEC                     │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Layer 4: Data (Secrets, PVs)                           │
├─────────────────────────────────────────────────────────┤
│ Threats:                                                │
│ • Secret theft from etcd                                │
│ • PV data exfiltration                                  │
│ • Unencrypted data at rest                             │
│ • Credential stuffing                                   │
├─────────────────────────────────────────────────────────┤
│ Mitigations:                                            │
│ ✓ etcd Encryption: KMS provider (AWS KMS, Vault)       │
│ ✓ External Secrets: Vault, AWS Secrets Manager         │
│ ✓ Volume Encryption: CSI driver encryption             │
│ ✓ Short-lived tokens: Projected ServiceAccount tokens  │
└─────────────────────────────────────────────────────────┘
```

### Hardened Pod Template

```yaml
# Security-first pod template
apiVersion: v1
kind: Pod
metadata:
  name: hardened-app
  annotations:
    container.apparmor.security.beta.kubernetes.io/app: runtime/default
spec:
  # Drop all service account credentials
  automountServiceAccountToken: false
  
  # Pod-level security
  securityContext:
    runAsNonRoot: true
    runAsUser: 10001
    runAsGroup: 10001
    fsGroup: 10001
    fsGroupChangePolicy: OnRootMismatch
    seccompProfile:
      type: RuntimeDefault  # Or Localhost with custom profile
    supplementalGroups: [10001]
    sysctls: []  # Avoid unless necessary
    
  containers:
  - name: app
    image: registry.internal/app:v1.0.0@sha256:abc123...  # Digest pinning
    imagePullPolicy: IfNotPresent
    
    # Container-level security (overrides pod)
    securityContext:
      allowPrivilegeEscalation: false
      privileged: false
      readOnlyRootFilesystem: true
      runAsNonRoot: true
      runAsUser: 10001
      capabilities:
        drop: ["ALL"]
        # Only add if absolutely required
        # add: ["NET_BIND_SERVICE"]
        
    # Resource limits (prevent noisy neighbor)
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
        ephemeral-storage: 1Gi
      limits:
        cpu: 500m
        memory: 512Mi
        ephemeral-storage: 2Gi
        
    # Liveness: restart if unhealthy
    livenessProbe:
      httpGet:
        path: /healthz
        port: 8080
        scheme: HTTP
      initialDelaySeconds: 30
      periodSeconds: 10
      timeoutSeconds: 5
      failureThreshold: 3
      
    # Readiness: remove from service if not ready
    readinessProbe:
      httpGet:
        path: /ready
        port: 8080
      initialDelaySeconds: 5
      periodSeconds: 5
      failureThreshold: 2
      
    # Startup: allow slow startup
    startupProbe:
      httpGet:
        path: /healthz
        port: 8080
      initialDelaySeconds: 0
      periodSeconds: 5
      failureThreshold: 30
      
    volumeMounts:
    - name: tmp
      mountPath: /tmp
    - name: cache
      mountPath: /app/cache
      
  volumes:
  - name: tmp
    emptyDir:
      medium: Memory  # tmpfs for sensitive data
      sizeLimit: 100Mi
  - name: cache
    emptyDir:
      sizeLimit: 1Gi
      
  # DNS: avoid cluster-wide DNS for isolated workloads
  dnsPolicy: ClusterFirst
  # dnsConfig:
  #   nameservers: ["10.96.0.10"]
  #   searches: ["svc.cluster.local"]
    
  # Termination grace period
  terminationGracePeriodSeconds: 30
  
  # Node selection
  nodeSelector:
    kubernetes.io/os: linux
    node.kubernetes.io/instance-type: c5.xlarge
    
  tolerations: []  # No special tolerations
  
  affinity:
    podAntiAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchLabels:
              app: hardened-app
          topologyKey: kubernetes.io/hostname
```

---

## Testing & Fuzzing

### 1. Validation Testing

```bash
# Test pod security standards
kubectl label namespace test pod-security.kubernetes.io/enforce=restricted

# Attempt privileged pod (should fail)
kubectl run test-priv --image=nginx --privileged=true -n test
# Error: pods "test-priv" is forbidden: violates PodSecurity "restricted:latest"

# Test resource limits
kubectl run test-limits --image=nginx -n test \
  --requests=cpu=10000,memory=1000Gi
# Error: exceeded quota

# Test network policy (default deny)
kubectl run test-net --image=nginx -n test
kubectl exec test-net -- curl google.com
# Timeout (egress blocked)
```

### 2. Chaos Engineering

```bash
# Install Chaos Mesh
helm repo add chaos-mesh https://charts.chaos-mesh.org
helm install chaos-mesh chaos-mesh/chaos-mesh -n chaos-mesh --create-namespace

# Pod kill experiment
kubectl apply -f - <<EOF
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: pod-kill
  namespace: prod
spec:
  action: pod-kill
  mode: one
  selector:
    namespaces:
    - prod
    labelSelectors:
      app: api-server
  scheduler:
    cron: "@every 2m"
EOF

# Network delay
kubectl apply -f - <<EOF
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: network-delay
  namespace: prod
spec:
  action: delay
  mode: all
  selector:
    namespaces:
    - prod
    labelSelectors:
      app: api-server
  delay:
    latency: "100ms"
    jitter: "50ms"
  duration: "5m"
EOF

# Observe behavior
kubectl get pods -n prod --watch
```

### 3. Load Testing

```go
// k6 test script
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 100 },  // Ramp up
    { duration: '5m', target: 100 },  // Steady
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function() {
  let res = http.get('http://api-server.prod.svc.cluster.local/api/v1/status');
  check(res, {
    'status 200': (r) => r.status === 200,
    'latency OK': (r) => r.timings.duration < 500,
  });
  sleep(1);
}
```

```bash
# Run load test
k6 run --vus 100 --duration 10m loadtest.js

# Monitor during test
kubectl top pods -n prod -l app=api-server
watch -n1 'kubectl get hpa -n prod'
```

### 4. Fuzzing Admission Policies

```bash
# Generate random pod specs
for i in {1..1000}; do
  kubectl run fuzz-$i --image=nginx --dry-run=server \
    --overrides="$(python3 -c "import random, json; print(json.dumps({
      'spec': {
        'securityContext': {
          'runAsUser': random.randint(0, 65535),
          'runAsGroup': random.randint(0, 65535),
        },
        'containers': [{
          'name': 'nginx',
          'image': 'nginx',
          'securityContext': {
            'privileged': random.choice([True, False]),
            'allowPrivilegeEscalation': random.choice([True, False]),
          }
        }]
      }
    }))")" 2>&1 | grep -E "forbidden|admitted"
done
```

---

## Roll-out / Roll-back Plan

### Pre-Deployment Checklist

```bash
# 1. Validate manifests
kubectl apply --dry-run=server -f deployment.yaml
kubectl diff -f deployment.yaml

# 2. Check admission policies
kubectl run --dry-run=server test --image=nginx

# 3. Verify resource quotas
kubectl describe quota -n prod

# 4. Review RBAC
kubectl auth can-i create deployments --namespace=prod

# 5. Image availability
docker pull registry.internal/app:v1.2.3
trivy image registry.internal/app:v1.2.3

# 6. Backup current state
kubectl get all -n prod -o yaml > backup-$(date +%Y%m%d-%H%M%S).yaml
```

### Deployment Process

```bash
# 1. Blue-Green: Deploy to staging
kubectl apply -f deployment.yaml -n staging
kubectl rollout status deployment/app -n staging

# 2. Smoke tests
curl http://app.staging.svc.cluster.local/healthz

# 3. Canary: Prod with partition
kubectl apply -f deployment.yaml -n prod
kubectl patch deployment app -n prod -p '{"spec":{"replicas":12}}'
# Traffic split: 10% new, 90% old

# 4. Monitor metrics (5-10 minutes)
# - Error rate
# - Latency (p50, p95, p99)
# - Resource usage
# - Business metrics

# 5. Full rollout
kubectl scale deployment app -n prod --replicas=10
kubectl rollout status deployment/app -n prod

# 6. Verify
kubectl get deployment app -n prod
kubectl get pods -n prod -l app=app
```

### Rollback Procedure

```bash
# Immediate rollback
kubectl rollout undo deployment/app -n prod

# Rollback to specific revision
kubectl rollout history deployment/app -n prod
kubectl rollout undo deployment/app -n prod --to-revision=3

# Emergency: scale to zero, then redeploy old version
kubectl scale deployment app -n prod --replicas=0
kubectl set image deployment/app app=registry.internal/app:v1.2.2 -n prod
kubectl scale deployment app -n prod --replicas=10

# Restore from backup
kubectl apply -f backup-20240209-120000.yaml
```

### Post-Deployment Verification

```bash
# 1. Pod health
kubectl get pods -n prod -l app=app
kubectl top pods -n prod -l app=app

# 2. Events
kubectl get events -n prod --sort-by=.metadata.creationTimestamp

# 3. Logs
kubectl logs -n prod -l app=app --tail=100 | grep ERROR

# 4. Metrics
curl -s http://prometheus:9090/api/v1/query?query=up{job="app"} | jq .

# 5. Alerts
kubectl get prometheusrules -n prod
```

---

## Next 3 Steps

1. **Implement GitOps Pipeline**
   ```bash
   # Install ArgoCD
   kubectl create namespace argocd
   kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
   
   # Create Application
   kubectl apply -f - <<EOF
   apiVersion: argoproj.io/v1alpha1
   kind: Application
   metadata:
     name: api-server
     namespace: argocd
   spec:
     project: default
     source:
       repoURL: https://github.com/org/repo
       targetRevision: HEAD
       path: k8s/prod
     destination:
       server: https://kubernetes.default.svc
       namespace: prod
     syncPolicy:
       automated:
         prune: true
         selfHeal: true
   EOF
   ```

2. **Set Up Runtime Security**
   ```bash
   # Deploy Falco
   helm repo add falcosecurity https://falcosecurity.github.io/charts
   helm install falco falcosecurity/falco \
     --namespace security --create-namespace \
     --set driver.kind=ebpf \
     --set falcosidekick.enabled=true
   
   # Custom rules
   kubectl apply -f custom-falco-rules.yaml
   
   # Test detection
   kubectl exec -it test-pod -- bash
   # cat /etc/shadow  # Should trigger alert
   ```

3. **Establish Observability Stack**
   ```bash
   # Install kube-prometheus-stack
   helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
   helm install kube-prom prometheus-community/kube-prometheus-stack \
     --namespace monitoring --create-namespace
   
   # ServiceMonitor for apps
   kubectl apply -f servicemonitor.yaml
   
   # Grafana dashboards
   kubectl port-forward -n monitoring svc/kube-prom-grafana 3000:80
   # Import dashboards: 315 (Kubernetes cluster), 6417 (Pods)
   ```

---

## References

- **Kubernetes Documentation**: https://kubernetes.io/docs/concepts/workloads/controllers/
- **Pod Security Standards**: https://kubernetes.io/docs/concepts/security/pod-security-standards/
- **CNCF Security Whitepaper**: https://github.com/cncf/tag-security/blob/main/security-whitepaper/
- **NSA/CISA Kubernetes Hardening**: https://media.defense.gov/2022/Aug/29/2003066362/-1/-1/0/CTR_KUBERNETES_HARDENING_GUIDANCE_1.2_20220829.PDF
- **CIS Kubernetes Benchmark**: https://www.cisecurity.org/benchmark/kubernetes
- **Falco Rules**: https://github.com/falcosecurity/rules
- **OPA Gatekeeper Library**: https://github.com/open-policy-agent/gatekeeper-library

This guide covers workload resources from first principles through production deployment. Practice with the commands, build test clusters, and contribute security policies to CNCF projects for real-world experience.