# CI/CD Container Deployments: Control Plane, Data Plane & Zero-Impact Production

**Summary**: Production-safe CI/CD requires **separation of control plane** (orchestration, scheduling, config management) from **data plane** (workload execution, traffic handling). Deploy new versions using **immutable infrastructure**, **progressive delivery** (canary/blue-green), **feature flags**, and **traffic shadowing** to test in production without impact. Use **GitOps** for declarative control plane state, **service mesh** for data plane traffic control, **observability** for validation, and **automated rollback** on SLO violations. Key: never mutate running production; always deploy alongside and migrate traffic with validation gates.

---

## 1. CONTROL PLANE VS DATA PLANE ARCHITECTURE

### 1.1 Conceptual Separation
```
┌─────────────────────────────────────────────────────────────────────┐
│                         CONTROL PLANE                                │
│  (What should run, where, and how - orchestration & policy)         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   GitOps     │  │ Kubernetes   │  │   Config     │              │
│  │   (Source    │→ │   API        │→ │   Mgmt       │              │
│  │   of Truth)  │  │   Server     │  │   (etcd)     │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│         ↓                  ↓                  ↓                      │
│  ┌──────────────────────────────────────────────────┐               │
│  │         Controllers & Operators                  │               │
│  │  (Reconciliation loops: desired → actual state)  │               │
│  └──────────────────────────────────────────────────┘               │
│         ↓                  ↓                  ↓                      │
└─────────┼──────────────────┼──────────────────┼──────────────────────┘
          │                  │                  │
          ↓                  ↓                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                          DATA PLANE                                  │
│  (Actual workload execution & traffic handling)                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Pods/      │  │   Service    │  │   Ingress/   │              │
│  │ Containers   │  │    Mesh      │  │   Gateway    │              │
│  │  (workload)  │  │  (Envoy/     │  │   (Traffic   │              │
│  │              │  │  Linkerd)    │  │    Routing)  │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│         ↓                  ↓                  ↓                      │
│  ┌──────────────────────────────────────────────────┐               │
│  │    Actual User Traffic & Business Logic          │               │
│  │         (Revenue-generating requests)             │               │
│  └──────────────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────────────┘

KEY PRINCIPLE: Control plane changes don't immediately affect data plane.
Data plane changes are gated by validation and progressive rollout.
```

### 1.2 Kubernetes Implementation
```
┌─────────────────────────────────────────────────────────────────┐
│                    KUBERNETES CONTROL PLANE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  kube-apiserver ←─── kubectl/CI/CD pipeline                     │
│       ↓                                                          │
│  etcd (desired state storage)                                   │
│       ↓                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ kube-       │  │ kube-       │  │ cloud-      │             │
│  │ scheduler   │  │ controller  │  │ controller  │             │
│  │             │  │ manager     │  │ manager     │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│       ↓                  ↓                  ↓                    │
└───────┼──────────────────┼──────────────────┼────────────────────┘
        │                  │                  │
        ↓                  ↓                  ↓
┌─────────────────────────────────────────────────────────────────┐
│                    KUBERNETES DATA PLANE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Node 1              Node 2              Node 3                 │
│  ┌────────────┐      ┌────────────┐      ┌────────────┐         │
│  │ kubelet    │      │ kubelet    │      │ kubelet    │         │
│  │ kube-proxy │      │ kube-proxy │      │ kube-proxy │         │
│  │ container  │      │ container  │      │ container  │         │
│  │ runtime    │      │ runtime    │      │ runtime    │         │
│  └────────────┘      └────────────┘      └────────────┘         │
│       ↓                   ↓                   ↓                  │
│  ┌────────────┐      ┌────────────┐      ┌────────────┐         │
│  │ Pod        │      │ Pod        │      │ Pod        │         │
│  │  app:v1    │      │  app:v2    │      │  app:v1    │         │
│  │ (OLD)      │      │ (NEW)      │      │ (OLD)      │         │
│  └────────────┘      └────────────┘      └────────────┘         │
│       ↑                   ↑                   ↑                  │
│       └───────────────────┴───────────────────┘                  │
│                    Service (Load Balancer)                       │
│              ↑                                                   │
└──────────────┼───────────────────────────────────────────────────┘
               │
          User Traffic
```

---

## 2. CI/CD PIPELINE ARCHITECTURE

### 2.1 Full Pipeline View
```
┌──────────────────────────────────────────────────────────────────────┐
│                        SOURCE CODE REPO (Git)                         │
│  main branch (production) ← PR ← feature branch                      │
└────────────────────────────┬─────────────────────────────────────────┘
                             │ (git push triggers webhook)
                             ↓
┌──────────────────────────────────────────────────────────────────────┐
│                         CI PIPELINE (Build)                           │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  1. Checkout Code                                                    │
│     ↓                                                                 │
│  2. Build Container Image (BuildKit)                                 │
│     ├─ Multi-stage build                                             │
│     ├─ Layer caching                                                 │
│     └─ Tag: registry.io/app:${GIT_SHA}, :${VERSION}, :latest        │
│     ↓                                                                 │
│  3. Security Scanning                                                │
│     ├─ SAST (Static Analysis) - SonarQube, Semgrep                  │
│     ├─ Image Scanning - Trivy, Grype, Snyk                          │
│     ├─ Secret Detection - gitleaks, trufflehog                      │
│     └─ Policy Checks - OPA, Kyverno                                 │
│     ↓                                                                 │
│  4. Unit & Integration Tests                                         │
│     ├─ Run tests in container                                        │
│     ├─ Generate coverage reports                                     │
│     └─ Publish test results                                          │
│     ↓                                                                 │
│  5. SBOM Generation                                                  │
│     ├─ Syft/Cyclonedx                                                │
│     └─ Attach to image metadata                                      │
│     ↓                                                                 │
│  6. Image Signing                                                    │
│     ├─ Cosign/Notary                                                 │
│     └─ Verify in admission controller                               │
│     ↓                                                                 │
│  7. Push to Registry                                                 │
│     └─ registry.io/app:${GIT_SHA}                                    │
│                                                                       │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ↓
┌──────────────────────────────────────────────────────────────────────┐
│                    CD PIPELINE (Deploy to Envs)                       │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  ENVIRONMENT 1: Development (dev cluster)                   │     │
│  ├────────────────────────────────────────────────────────────┤     │
│  │  • Auto-deploy on PR merge to dev branch                   │     │
│  │  • Full stack deployment (all microservices)               │     │
│  │  • Smoke tests                                              │     │
│  │  • Manual testing by developers                            │     │
│  └────────────────────────────────────────────────────────────┘     │
│                             ↓ (manual approval or auto)              │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  ENVIRONMENT 2: Staging (staging cluster)                   │     │
│  ├────────────────────────────────────────────────────────────┤     │
│  │  • Production-like environment                              │     │
│  │  • Same resource limits as prod                            │     │
│  │  • E2E tests, load tests, chaos tests                      │     │
│  │  • Security validation (penetration testing)               │     │
│  │  • Performance baseline (SLO validation)                   │     │
│  └────────────────────────────────────────────────────────────┘     │
│                             ↓ (strict approval gates)                │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  ENVIRONMENT 3: Production (multi-region clusters)          │     │
│  ├────────────────────────────────────────────────────────────┤     │
│  │  • Progressive delivery (canary/blue-green)                │     │
│  │  • Automated validation gates                              │     │
│  │  • SLO monitoring (error rate, latency, saturation)        │     │
│  │  • Automatic rollback on failure                           │     │
│  │  • Manual approval for full rollout                        │     │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

### 2.2 GitOps Control Plane Pattern
```
┌──────────────────────────────────────────────────────────────────────┐
│                   CONFIG REPO (GitOps - Single Source of Truth)       │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  environments/                                                        │
│  ├── dev/                                                             │
│  │   ├── kustomization.yaml                                          │
│  │   ├── deployment.yaml    (image: app:dev-abc123)                 │
│  │   ├── service.yaml                                                │
│  │   └── configmap.yaml     (replicas: 1, resources: low)           │
│  ├── staging/                                                         │
│  │   ├── kustomization.yaml                                          │
│  │   ├── deployment.yaml    (image: app:v1.2.3-rc1)                 │
│  │   └── configmap.yaml     (replicas: 3, resources: prod-like)     │
│  └── prod/                                                            │
│      ├── us-west/                                                     │
│      │   ├── deployment.yaml    (image: app:v1.2.2)  ← STABLE       │
│      │   ├── deployment-canary.yaml (image: app:v1.2.3) ← TESTING   │
│      │   └── traffic-split.yaml (stable: 95%, canary: 5%)          │
│      └── eu-west/                                                     │
│          └── deployment.yaml    (image: app:v1.2.2)  ← Not updated  │
│                                                                       │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ↓ (continuous reconciliation)
┌──────────────────────────────────────────────────────────────────────┐
│                    GitOps Operator (ArgoCD/Flux)                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  1. Poll config repo every 3 minutes (or webhook trigger)            │
│  2. Diff desired state (Git) vs actual state (cluster)               │
│  3. Sync differences:                                                 │
│     ├─ Apply new manifests                                           │
│     ├─ Update existing resources                                     │
│     └─ Prune deleted resources (if enabled)                          │
│  4. Health checks (wait for rollout completion)                      │
│  5. Post-sync hooks (run tests, notify Slack)                        │
│                                                                       │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ↓
┌──────────────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster (Production)                    │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Deployment (app-stable)          Deployment (app-canary)            │
│  ├─ Pod: app:v1.2.2 (OLD)         ├─ Pod: app:v1.2.3 (NEW)          │
│  ├─ Pod: app:v1.2.2               ├─ Pod: app:v1.2.3                │
│  └─ Pod: app:v1.2.2               └─ Pod: app:v1.2.3                │
│       ↑                                   ↑                           │
│       └────────────┬──────────────────────┘                           │
│                    │                                                  │
│           Service / Ingress                                          │
│          (Traffic split: 95% / 5%)                                   │
│                    │                                                  │
└────────────────────┼──────────────────────────────────────────────────┘
                     │
                User Traffic
```

---

## 3. DEPLOYMENT STRATEGIES (ZERO-DOWNTIME)

### 3.1 Blue-Green Deployment
```
PRINCIPLE: Run two identical production environments (blue=current, green=new).
Switch traffic atomically after validation. Instant rollback if needed.

┌──────────────────────────────────────────────────────────────────────┐
│                         INITIAL STATE (Blue Active)                   │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Load Balancer / Ingress                                             │
│         │                                                             │
│         ├─────────────► Blue Environment (v1.0)                      │
│         │               ├─ 10 pods, app:v1.0                         │
│         │               ├─ Database: v1 schema                       │
│         │               └─ Config: prod-v1                           │
│         │                                                             │
│         └─── (inactive) Green Environment (empty/old)                │
│                         └─ No traffic                                │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
                             ↓
                    Deploy new version to Green
                             ↓
┌──────────────────────────────────────────────────────────────────────┐
│                    DEPLOYMENT PHASE (Both Running)                    │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Load Balancer / Ingress                                             │
│         │                                                             │
│         ├─────────────► Blue Environment (v1.0)                      │
│         │               ├─ 10 pods, app:v1.0                         │
│         │               └─ Serving 100% traffic                      │
│         │                                                             │
│         └─── (warming up) Green Environment (v2.0)                   │
│                         ├─ 10 pods, app:v2.0                         │
│                         ├─ Run smoke tests                           │
│                         ├─ Validate health checks                    │
│                         └─ No live traffic yet                       │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
                             ↓
                    Validation passes, switch traffic
                             ↓
┌──────────────────────────────────────────────────────────────────────┐
│                     CUTOVER (Green Active)                            │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Load Balancer / Ingress                                             │
│         │                                                             │
│         ├─── (standby) Blue Environment (v1.0)                       │
│         │               ├─ 10 pods, app:v1.0                         │
│         │               └─ No traffic, ready for rollback            │
│         │                                                             │
│         └─────────────► Green Environment (v2.0)                     │
│                         ├─ 10 pods, app:v2.0                         │
│                         ├─ Serving 100% traffic                      │
│                         └─ Monitor SLOs for 1 hour                   │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
                             ↓
                If SLOs violated: instant rollback to Blue
                If SLOs met: decommission Blue, Green becomes new Blue
```

**Kubernetes Implementation** (Blue-Green):
```yaml
# blue-deployment.yaml (current production)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-blue
  labels:
    app: myapp
    version: v1.0
    slot: blue
spec:
  replicas: 10
  selector:
    matchLabels:
      app: myapp
      version: v1.0
  template:
    metadata:
      labels:
        app: myapp
        version: v1.0
        slot: blue
    spec:
      containers:
      - name: app
        image: registry.io/app:v1.0.0
        resources:
          requests:
            cpu: "1000m"
            memory: "2Gi"
          limits:
            cpu: "2000m"
            memory: "4Gi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 3

---
# green-deployment.yaml (new version)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-green
  labels:
    app: myapp
    version: v2.0
    slot: green
spec:
  replicas: 10
  selector:
    matchLabels:
      app: myapp
      version: v2.0
  template:
    metadata:
      labels:
        app: myapp
        version: v2.0
        slot: green
    spec:
      containers:
      - name: app
        image: registry.io/app:v2.0.0
        resources:
          requests:
            cpu: "1000m"
            memory: "2Gi"
          limits:
            cpu: "2000m"
            memory: "4Gi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 3

---
# service.yaml (selector controls which deployment receives traffic)
apiVersion: v1
kind: Service
metadata:
  name: app-service
spec:
  selector:
    app: myapp
    slot: blue  # ← Change to "green" to switch traffic
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: ClusterIP
```

**Automated Blue-Green Script**:
```bash
#!/bin/bash
# blue-green-deploy.sh

set -euo pipefail

NEW_VERSION="v2.0.0"
ACTIVE_SLOT=$(kubectl get svc app-service -o jsonpath='{.spec.selector.slot}')
INACTIVE_SLOT=$([[ "$ACTIVE_SLOT" == "blue" ]] && echo "green" || echo "blue")

echo "Active slot: $ACTIVE_SLOT, Deploying to: $INACTIVE_SLOT"

# 1. Deploy new version to inactive slot
kubectl set image deployment/app-${INACTIVE_SLOT} \
  app=registry.io/app:${NEW_VERSION}

# 2. Wait for rollout
kubectl rollout status deployment/app-${INACTIVE_SLOT} --timeout=5m

# 3. Run smoke tests against inactive slot
INACTIVE_POD=$(kubectl get pods -l slot=${INACTIVE_SLOT} -o jsonpath='{.items[0].metadata.name}')
kubectl exec $INACTIVE_POD -- /app/smoke-tests.sh

# 4. Validation gates
echo "Running validation gates..."
./validate-metrics.sh app-${INACTIVE_SLOT} || { echo "Validation failed"; exit 1; }

# 5. Switch traffic (atomic operation)
echo "Switching traffic from $ACTIVE_SLOT to $INACTIVE_SLOT"
kubectl patch svc app-service -p "{\"spec\":{\"selector\":{\"slot\":\"${INACTIVE_SLOT}\"}}}"

# 6. Monitor SLOs for 5 minutes
echo "Monitoring SLOs for 5 minutes..."
for i in {1..10}; do
  ERROR_RATE=$(kubectl exec -n monitoring prometheus-0 -- \
    promtool query instant 'rate(http_requests_total{status=~"5.."}[1m])' | jq -r '.value[1]')
  
  if (( $(echo "$ERROR_RATE > 0.01" | bc -l) )); then
    echo "ERROR: Error rate $ERROR_RATE exceeds threshold! Rolling back..."
    kubectl patch svc app-service -p "{\"spec\":{\"selector\":{\"slot\":\"${ACTIVE_SLOT}\"}}}"
    exit 1
  fi
  
  echo "Check $i/10: Error rate: $ERROR_RATE (OK)"
  sleep 30
done

echo "Deployment successful! Old slot ($ACTIVE_SLOT) kept as standby for 1 hour."
```

### 3.2 Canary Deployment (Progressive Traffic Shift)
```
PRINCIPLE: Route small percentage of traffic to new version, increase gradually
while monitoring metrics. Rollback if degradation detected.

┌──────────────────────────────────────────────────────────────────────┐
│                        PHASE 1: Canary 5%                             │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│                     Ingress / Service Mesh                           │
│                              │                                        │
│         ┌────────────────────┼────────────────────┐                  │
│         │                    │                    │                  │
│         ↓ 95%                ↓ 5%                 ↓                  │
│  Stable Deployment      Canary Deployment    (Dark Traffic)          │
│  ├─ 20 pods            ├─ 1 pod               ├─ Shadow requests    │
│  ├─ app:v1.0           ├─ app:v2.0            └─ to v2.0 (no       │
│  └─ Baseline SLOs      └─ Monitor closely         response used)    │
│                                                                       │
│  Validation: error rate, latency p99, resource usage                 │
│  Duration: 10 minutes                                                 │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
                             ↓ (if SLOs met)
┌──────────────────────────────────────────────────────────────────────┐
│                        PHASE 2: Canary 25%                            │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│                     Ingress / Service Mesh                           │
│                              │                                        │
│         ┌────────────────────┼────────────────────┐                  │
│         │                    │                                        │
│         ↓ 75%                ↓ 25%                                    │
│  Stable Deployment      Canary Deployment                            │
│  ├─ 15 pods            ├─ 5 pods                                     │
│  ├─ app:v1.0           ├─ app:v2.0                                   │
│  └─ Normal traffic     └─ Higher traffic volume                      │
│                                                                       │
│  Validation: compare latency histograms stable vs canary             │
│  Duration: 20 minutes                                                 │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
                             ↓ (if SLOs met)
┌──────────────────────────────────────────────────────────────────────┐
│                        PHASE 3: Canary 50%                            │
├──────────────────────────────────────────────────────────────────────┤
│  (Repeat validation, increase stakes)                                │
└──────────────────────────────────────────────────────────────────────┘
                             ↓ (if SLOs met)
┌──────────────────────────────────────────────────────────────────────┐
│                        PHASE 4: Canary 100%                           │
├──────────────────────────────────────────────────────────────────────┤
│  • All traffic to v2.0                                                │
│  • Stable deployment scaled to 0                                     │
│  • Canary becomes new stable                                         │
└──────────────────────────────────────────────────────────────────────┘
```

**Flagger (Automated Canary with Istio/Linkerd)**:
```yaml
# flagger-canary.yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: myapp
  namespace: prod
spec:
  # Target deployment to canary
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  
  # Service mesh provider
  provider: istio  # or linkerd, nginx, contour, gloo, appmesh
  
  # Deployment strategy
  progressDeadlineSeconds: 600
  
  service:
    port: 80
    targetPort: 8080
    gateways:
    - public-gateway
    hosts:
    - app.example.com
    trafficPolicy:
      tls:
        mode: ISTIO_MUTUAL
  
  # Canary analysis
  analysis:
    # Schedule interval
    interval: 1m
    
    # Max traffic percentage routed to canary
    maxWeight: 50
    
    # Canary increment step (5% → 10% → 15% → ...)
    stepWeight: 5
    
    # Number of checks before rollout
    threshold: 5
    
    # Metrics to validate (from Prometheus)
    metrics:
    - name: request-success-rate
      thresholdRange:
        min: 99  # Must maintain 99% success rate
      interval: 1m
      query: |
        sum(rate(
          istio_requests_total{
            destination_workload_namespace="prod",
            destination_workload="myapp",
            response_code!~"5.*"
          }[1m]
        )) 
        / 
        sum(rate(
          istio_requests_total{
            destination_workload_namespace="prod",
            destination_workload="myapp"
          }[1m]
        )) * 100
    
    - name: request-duration
      thresholdRange:
        max: 500  # p99 latency must be < 500ms
      interval: 1m
      query: |
        histogram_quantile(0.99,
          sum(rate(
            istio_request_duration_milliseconds_bucket{
              destination_workload_namespace="prod",
              destination_workload="myapp"
            }[1m]
          )) by (le)
        )
    
    # Webhooks for custom validation
    webhooks:
    - name: load-test
      url: http://flagger-loadtester/
      timeout: 5s
      metadata:
        type: cmd
        cmd: "hey -z 1m -q 10 -c 2 http://myapp-canary.prod:8080/"
    
    - name: smoke-test
      url: http://flagger-loadtester/
      timeout: 30s
      metadata:
        type: bash
        bash: |
          curl -sd 'test' http://myapp-canary.prod:8080/token | \
          grep token

  # Rollback on failed checks
  skipAnalysis: false
```

**Manual Canary with Istio VirtualService**:
```yaml
# istio-traffic-split.yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: myapp
spec:
  hosts:
  - app.example.com
  gateways:
  - public-gateway
  http:
  - match:
    - headers:
        user-agent:
          regex: ".*Chrome.*"  # Canary only for Chrome users
    route:
    - destination:
        host: myapp-canary
        port:
          number: 80
  
  - match:
    - headers:
        x-canary:
          exact: "true"  # Explicit canary opt-in
    route:
    - destination:
        host: myapp-canary
        port:
          number: 80
  
  - route:
    - destination:
        host: myapp-stable
        port:
          number: 80
      weight: 95  # 95% to stable
    - destination:
        host: myapp-canary
        port:
          number: 80
      weight: 5   # 5% to canary
    
    timeout: 10s
    retries:
      attempts: 3
      perTryTimeout: 2s
      retryOn: 5xx,reset,connect-failure,refused-stream
```

### 3.3 Rolling Update (Kubernetes Native)
```
PRINCIPLE: Gradually replace old pods with new pods. Default K8s strategy.
No additional infrastructure, but limited traffic control.

┌──────────────────────────────────────────────────────────────────────┐
│                    INITIAL STATE (v1.0 - 4 replicas)                  │
├──────────────────────────────────────────────────────────────────────┤
│  Pod-1 (v1.0)  Pod-2 (v1.0)  Pod-3 (v1.0)  Pod-4 (v1.0)             │
│    Running       Running       Running       Running                 │
└──────────────────────────────────────────────────────────────────────┘
                             ↓
                    kubectl set image ... (v2.0)
                             ↓
┌──────────────────────────────────────────────────────────────────────┐
│                         STEP 1: Create new pod                        │
├──────────────────────────────────────────────────────────────────────┤
│  Pod-1 (v1.0)  Pod-2 (v1.0)  Pod-3 (v1.0)  Pod-4 (v1.0)  Pod-5 (v2.0)│
│    Running       Running       Running       Running     Creating... │
│                                                                       │
│  MaxSurge=1: Allow 1 extra pod during rollout (5 total)              │
└──────────────────────────────────────────────────────────────────────┘
                             ↓
┌──────────────────────────────────────────────────────────────────────┐
│                  STEP 2: New pod ready, terminate old                 │
├──────────────────────────────────────────────────────────────────────┤
│  Pod-1 (v1.0)  Pod-2 (v1.0)  Pod-3 (v1.0)  Pod-4 (v1.0)  Pod-5 (v2.0)│
│  Terminating     Running       Running       Running       Running   │
│                                                                       │
│  MaxUnavailable=0: Always maintain 4 ready pods                      │
└──────────────────────────────────────────────────────────────────────┘
                             ↓
┌──────────────────────────────────────────────────────────────────────┐
│                  STEP 3: Repeat for remaining pods                    │
├──────────────────────────────────────────────────────────────────────┤
│  Pod-2 (v1.0)  Pod-3 (v1.0)  Pod-4 (v1.0)  Pod-5 (v2.0)  Pod-6 (v2.0)│
│    Running       Running       Running       Running      Creating   │
└──────────────────────────────────────────────────────────────────────┘
                             ↓
                         (Continue...)
                             ↓
┌──────────────────────────────────────────────────────────────────────┐
│                 FINAL STATE (v2.0 - 4 replicas)                       │
├──────────────────────────────────────────────────────────────────────┤
│  Pod-5 (v2.0)  Pod-6 (v2.0)  Pod-7 (v2.0)  Pod-8 (v2.0)             │
│    Running       Running       Running       Running                 │
└──────────────────────────────────────────────────────────────────────┘
```

**Rolling Update Configuration**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 10
  
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%        # Max 2-3 extra pods during rollout
      maxUnavailable: 0%   # Never go below 10 ready pods
  
  minReadySeconds: 30      # Wait 30s after pod ready before next
  progressDeadlineSeconds: 600  # Rollout must complete in 10 min
  
  selector:
    matchLabels:
      app: myapp
  
  template:
    metadata:
      labels:
        app: myapp
        version: v2.0
    spec:
      containers:
      - name: app
        image: registry.io/app:v2.0.0
        
        # Readiness determines when pod receives traffic
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
          successThreshold: 2  # Must pass 2 consecutive checks
          failureThreshold: 3
        
        # Liveness determines when pod is restarted
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          failureThreshold: 3
        
        # Lifecycle hooks
        lifecycle:
          preStop:
            exec:
              command:
              - /bin/sh
              - -c
              - sleep 15  # Allow time for deregistration from LB
        
        resources:
          requests:
            cpu: "1000m"
            memory: "2Gi"
          limits:
            cpu: "2000m"
            memory: "4Gi"

---
# PodDisruptionBudget: Ensure availability during voluntary disruptions
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: myapp-pdb
spec:
  minAvailable: 8  # Always keep at least 8/10 pods running
  selector:
    matchLabels:
      app: myapp
```

**Rollback on Failure**:
```bash
# Watch rollout progress
kubectl rollout status deployment/myapp

# If issues detected, rollback
kubectl rollout undo deployment/myapp

# Rollback to specific revision
kubectl rollout history deployment/myapp
kubectl rollout undo deployment/myapp --to-revision=3

# Pause rollout (manual investigation)
kubectl rollout pause deployment/myapp
# ... investigate ...
kubectl rollout resume deployment/myapp
```

### 3.4 Traffic Shadowing (Dark Launch)
```
PRINCIPLE: Send copy of production traffic to new version (without using response).
Validate behavior under real load before any user impact.

┌──────────────────────────────────────────────────────────────────────┐
│                         Traffic Shadowing                             │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│                        User Request                                  │
│                             │                                         │
│                             ↓                                         │
│                      Ingress / Mesh                                  │
│                             │                                         │
│         ┌───────────────────┼───────────────────┐                    │
│         │                   │                   │                    │
│         ↓ (PRIMARY)         ↓ (MIRROR)          ↓                    │
│  Stable v1.0          Shadow v2.0         (Logs/Metrics)             │
│  ├─ Process request   ├─ Process copy     ├─ Compare:               │
│  ├─ Return response   ├─ Response IGNORED │  • Latency              │
│  └─ User sees this    └─ Just observe     │  • Errors               │
│                                            │  • Resource usage       │
│                                            └─ No user impact!        │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

**Istio Traffic Mirroring**:
```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: myapp
spec:
  hosts:
  - app.example.com
  http:
  - route:
    - destination:
        host: myapp-stable
        port:
          number: 80
      weight: 100  # All responses from stable
    
    mirror:
      host: myapp-shadow  # Shadow deployment
      port:
        number: 80
    
    mirrorPercentage:
      value: 100.0  # Mirror 100% of traffic (or use sampling)
```

**Use Cases**:
- Database migration testing (dual writes)
- New algorithm validation (compare results)
- Performance regression detection
- Load testing with real traffic patterns

---

## 4. ENVIRONMENT ISOLATION & PARITY

### 4.1 Multi-Environment Architecture
```
┌──────────────────────────────────────────────────────────────────────┐
│                      DEVELOPMENT ENVIRONMENT                          │
├──────────────────────────────────────────────────────────────────────┤
│  • Kubernetes cluster (kind/minikube/EKS dev)                        │
│  • Namespace per developer (dev-alice, dev-bob)                      │
│  • Shared services (databases, message queues)                       │
│  • Auto-deploy on git push to feature branch                         │
│  • Relaxed resource limits (low cost)                                │
│  • No SLA, can break often                                           │
│  • Mock external dependencies (payment gateways, etc.)               │
└──────────────────────────────────────────────────────────────────────┘
                             ↓ (merge to main)
┌──────────────────────────────────────────────────────────────────────┐
│                       STAGING ENVIRONMENT                             │
├──────────────────────────────────────────────────────────────────────┤
│  • Production-identical cluster (same K8s version, node types)       │
│  • Same resource limits, autoscaling configs                         │
│  • Real external integrations (sandbox APIs)                         │
│  • E2E tests, load tests, chaos tests                                │
│  • Security scanning (DAST, penetration testing)                     │
│  • Database schema migrations tested here first                      │
│  • Performance baseline: must meet SLO targets                       │
│  • Manual QA approval gate                                           │
└──────────────────────────────────────────────────────────────────────┘
                             ↓ (approval + validation)
┌──────────────────────────────────────────────────────────────────────┐
│                      PRODUCTION ENVIRONMENT                           │
├──────────────────────────────────────────────────────────────────────┤
│  • Multi-region, multi-AZ clusters                                   │
│  • Progressive rollout (region by region)                            │
│  • Canary/blue-green deployment                                      │
│  • Real user traffic, revenue impact                                 │
│  • Strict SLO monitoring (99.95% uptime)                             │
│  • Automatic rollback on SLO breach                                  │
│  • Change freeze windows (holidays, high-traffic events)             │
└──────────────────────────────────────────────────────────────────────┘
```

### 4.2 Namespace-Based Isolation
```bash
# Create isolated namespaces
kubectl create namespace dev
kubectl create namespace staging
kubectl create namespace prod

# RBAC: Developers can deploy to dev, read staging
cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: dev
  name: developer
rules:
- apiGroups: ["", "apps", "batch"]
  resources: ["*"]
  verbs: ["*"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: staging
  name: developer-read-only
rules:
- apiGroups: ["", "apps", "batch"]
  resources: ["*"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: prod
  name: developer-forbidden
rules: []  # No access to prod
EOF

# Network policies: Isolate namespaces
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-from-other-namespaces
  namespace: prod
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector: {}  # Only pods in same namespace
EOF
```

### 4.3 Configuration Management (Per-Environment)
```bash
# Kustomize overlays for environment-specific config
.
├── base/
│   ├── kustomization.yaml
│   ├── deployment.yaml       # Base template
│   ├── service.yaml
│   └── configmap.yaml
└── overlays/
    ├── dev/
    │   ├── kustomization.yaml
    │   ├── replica-patch.yaml     # replicas: 1
    │   └── resource-patch.yaml    # Low CPU/mem
    ├── staging/
    │   ├── kustomization.yaml
    │   ├── replica-patch.yaml     # replicas: 3
    │   └── resource-patch.yaml    # Prod-like resources
    └── prod/
        ├── kustomization.yaml
        ├── replica-patch.yaml     # replicas: 10
        ├── resource-patch.yaml    # High resources
        ├── hpa.yaml               # Autoscaling
        └── pdb.yaml               # Pod disruption budget
```

**Example Kustomize Overlay**:
```yaml
# overlays/prod/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: prod

bases:
- ../../base

images:
- name: registry.io/app
  newTag: v2.0.0  # Override image version

replicas:
- name: myapp
  count: 10

patches:
- path: resource-patch.yaml
- path: hpa.yaml
- path: pdb.yaml

configMapGenerator:
- name: app-config
  behavior: merge
  literals:
  - LOG_LEVEL=info
  - ENVIRONMENT=production
  - CACHE_TTL=3600

secretGenerator:
- name: app-secrets
  env: secrets.env  # prod/secrets.env (not in git!)
```

```bash
# Deploy to each environment
kustomize build overlays/dev | kubectl apply -f -
kustomize build overlays/staging | kubectl apply -f -
kustomize build overlays/prod | kubectl apply -f -
```

---

## 5. TESTING IN PRODUCTION (SAFE PATTERNS)

### 5.1 Feature Flags (Runtime Toggle)
```
┌──────────────────────────────────────────────────────────────────────┐
│                        Feature Flag Architecture                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Application Code:                                                   │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  if featureFlag.isEnabled("new-checkout-flow", user) {     │     │
│  │    return newCheckoutV2(cart)                              │     │
│  │  } else {                                                   │     │
│  │    return oldCheckoutV1(cart)                              │     │
│  │  }                                                          │     │
│  └────────────────────────────────────────────────────────────┘     │
│                             ↓                                         │
│  Feature Flag Service (LaunchDarkly/Unleash/ConfigCat):              │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  Flag: "new-checkout-flow"                                 │     │
│  │  ├─ Environments:                                          │     │
│  │  │  ├─ dev: 100% enabled                                   │     │
│  │  │  ├─ staging: 100% enabled                              │     │
│  │  │  └─ prod:                                               │     │
│  │  │     ├─ 5% of users (canary)                            │     │
│  │  │     ├─ Whitelist: [internal_users, beta_testers]       │     │
│  │  │     ├─ Targeting: user.country == "US"                 │     │
│  │  │     └─ Kill switch: can disable instantly              │     │
│  │  └─ Metrics: track adoption, errors, performance          │     │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

**Implementation (Go with Unleash)**:
```go
// main.go
package main

import (
    "github.com/Unleash/unleash-client-go/v4"
    "github.com/Unleash/unleash-client-go/v4/context"
)

func main() {
    // Initialize feature flag client
    unleash.Initialize(
        unleash.WithListener(&unleash.DebugListener{}),
        unleash.WithAppName("myapp"),
        unleash.WithUrl("https://unleash.example.com/api/"),
        unleash.WithCustomHeaders(http.Header{"Authorization": {"API_TOKEN"}}),
        unleash.WithRefreshInterval(15*time.Second),
    )
    
    http.HandleFunc("/checkout", checkoutHandler)
    http.ListenAndServe(":8080", nil)
}

func checkoutHandler(w http.ResponseWriter, r *http.Request) {
    userID := r.Header.Get("X-User-ID")
    
    // Create feature flag context
    ctx := context.Context{
        UserId:        userID,
        SessionId:     r.Header.Get("X-Session-ID"),
        RemoteAddress: r.RemoteAddr,
        Properties: map[string]string{
            "country": r.Header.Get("X-Country"),
            "tier":    getUserTier(userID),
        },
    }
    
    // Check feature flag
    if unleash.IsEnabled("new-checkout-flow", unleash.WithContext(ctx)) {
        newCheckoutV2(w, r)  // New implementation
    } else {
        oldCheckoutV1(w, r)  // Existing implementation
    }
}
```

**Gradual Rollout Strategy**:
```
Day 1: Enable for internal employees only
  ├─ Monitor error rates, latency
  └─ Collect feedback

Day 3: 1% of production users (random sampling)
  ├─ A/B test metrics: conversion rate, cart abandonment
  ├─ Monitor SLOs
  └─ If degradation: disable instantly

Day 5: 5% of production users
  ├─ Validate at scale
  └─ Check for edge cases

Day 7: 25% rollout
  └─ Confidence building

Day 10: 100% rollout (or keep at 50% for A/B testing)
  └─ Old code path can be removed after 2 weeks
```

### 5.2 Observability for Validation
```
┌──────────────────────────────────────────────────────────────────────┐
│                      OBSERVABILITY STACK                              │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Application Code (Instrumentation)                          │    │
│  ├─────────────────────────────────────────────────────────────┤    │
│  │  // OpenTelemetry spans                                      │    │
│  │  span := tracer.Start(ctx, "checkout")                       │    │
│  │  defer span.End()                                            │    │
│  │                                                               │    │
│  │  // Metrics (Prometheus)                                     │    │
│  │  checkoutDuration.Observe(elapsed)                           │    │
│  │  checkoutErrors.WithLabelValues(version).Inc()               │    │
│  │                                                               │    │
│  │  // Structured logs                                          │    │
│  │  log.Info("checkout completed",                              │    │
│  │    "user_id", userID,                                        │    │
│  │    "version", "v2",                                          │    │
│  │    "duration_ms", elapsed)                                   │    │
│  └─────────────────────────────────────────────────────────────┘    │
│         │                  │                  │                       │
│         ↓ Traces           ↓ Metrics          ↓ Logs                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Jaeger/    │  │  Prometheus  │  │     Loki/    │              │
│  │   Tempo      │  │              │  │  Elasticsearch│              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│         │                  │                  │                       │
│         └──────────────────┴──────────────────┘                       │
│                            ↓                                          │
│                    ┌──────────────┐                                  │
│                    │   Grafana    │                                  │
│                    │  (Dashboards)│                                  │
│                    └──────────────┘                                  │
│                            ↓                                          │
│                    ┌──────────────┐                                  │
│                    │  Alertmanager│                                  │
│                    │  (SLO alerts)│                                  │
│                    └──────────────┘                                  │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

**SLO-Based Validation**:
```yaml
# prometheus-rules.yaml
groups:
- name: slo-validation
  interval: 30s
  rules:
  
  # SLI: Request success rate
  - record: sli:request_success_rate:5m
    expr: |
      sum(rate(http_requests_total{status!~"5.."}[5m]))
      /
      sum(rate(http_requests_total[5m]))
  
  # SLO: 99.9% success rate
  - alert: SLOViolation_ErrorBudgetExhausted
    expr: sli:request_success_rate:5m < 0.999
    for: 5m
    labels:
      severity: critical
      team: platform
    annotations:
      summary: "Error budget exhausted - rollback deployment"
      description: "Success rate {{ $value }} below 99.9% SLO"
  
  # SLI: Latency p99
  - record: sli:request_duration_p99:5m
    expr: |
      histogram_quantile(0.99,
        sum(rate(http_request_duration_seconds_bucket[5m])) by (le)
      )
  
  # SLO: p99 latency < 500ms
  - alert: SLOViolation_LatencyDegraded
    expr: sli:request_duration_p99:5m > 0.5
    for: 5m
    labels:
      severity: warning
      team: platform
    annotations:
      summary: "Latency degradation detected"
      description: "p99 latency {{ $value }}s exceeds 500ms SLO"
  
  # Compare canary vs stable
  - alert: CanaryDegradation
    expr: |
      (
        sum(rate(http_requests_total{version="v2",status=~"5.."}[5m]))
        /
        sum(rate(http_requests_total{version="v2"}[5m]))
      )
      >
      (
        sum(rate(http_requests_total{version="v1",status=~"5.."}[5m]))
        /
        sum(rate(http_requests_total{version="v1"}[5m]))
      ) * 1.5  # Canary error rate 50% higher than stable
    for: 2m
    labels:
      severity: critical
      action: rollback
    annotations:
      summary: "Canary showing higher error rate than stable"
```

**Automated Rollback on SLO Violation**:
```bash
#!/bin/bash
# slo-monitor.sh (runs in CI/CD or K8s CronJob)

set -euo pipefail

NAMESPACE="prod"
DEPLOYMENT="myapp"
SLO_THRESHOLD=0.999  # 99.9%

# Query Prometheus for current SLI
SUCCESS_RATE=$(curl -s 'http://prometheus:9090/api/v1/query?query=sli:request_success_rate:5m' \
  | jq -r '.data.result[0].value[1]')

echo "Current success rate: $SUCCESS_RATE"

if (( $(echo "$SUCCESS_RATE < $SLO_THRESHOLD" | bc -l) )); then
  echo "SLO VIOLATION! Success rate $SUCCESS_RATE < $SLO_THRESHOLD"
  echo "Initiating automatic rollback..."
  
  # Rollback deployment
  kubectl rollout undo deployment/$DEPLOYMENT -n $NAMESPACE
  
  # Send alert
  curl -X POST https://hooks.slack.com/... \
    -H 'Content-Type: application/json' \
    -d "{\"text\":\"🚨 ROLLBACK: $DEPLOYMENT due to SLO violation (${SUCCESS_RATE})\"}"
  
  # Create incident
  curl -X POST https://api.pagerduty.com/incidents \
    -H 'Authorization: Token token=...' \
    -d '{
      "incident": {
        "type": "incident",
        "title": "Automatic rollback triggered",
        "service": {"id": "..."},
        "urgency": "high"
      }
    }'
  
  exit 1
fi

echo "SLO met ✓"
```

---

## 6. CI/CD SECURITY (SUPPLY CHAIN)

### 6.1 Secure CI/CD Pipeline
```
┌──────────────────────────────────────────────────────────────────────┐
│                      SECURE CI/CD PIPELINE                            │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  1. Source Code Security                                    │     │
│  ├────────────────────────────────────────────────────────────┤     │
│  │  • Branch protection (require PR reviews)                  │     │
│  │  • Commit signing (GPG/SSH)                                │     │
│  │  • Secret scanning (gitleaks, trufflehog)                  │     │
│  │  • Dependency review (Dependabot, Renovate)                │     │
│  └────────────────────────────────────────────────────────────┘     │
│                             ↓                                         │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  2. Build Environment Security                              │     │
│  ├────────────────────────────────────────────────────────────┤     │
│  │  • Ephemeral build agents (destroy after use)              │     │
│  │  • No persistent credentials on runners                    │     │
│  │  • OIDC for cloud authentication (no static keys)          │     │
│  │  • Network isolation (no internet for sensitive builds)    │     │
│  └────────────────────────────────────────────────────────────┘     │
│                             ↓                                         │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  3. Artifact Security                                       │     │
│  ├────────────────────────────────────────────────────────────┤     │
│  │  • Image scanning (Trivy, Grype, Snyk)                     │     │
│  │  • SAST (Semgrep, SonarQube)                               │     │
│  │  • SBOM generation (Syft, Cyclonedx)                       │     │
│  │  • Image signing (Cosign, Notary)                          │     │
│  │  • Provenance attestation (SLSA)                           │     │
│  └────────────────────────────────────────────────────────────┘     │
│                             ↓                                         │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  4. Registry Security                                       │     │
│  ├────────────────────────────────────────────────────────────┤     │
│  │  • Private registry (Harbor, ACR, ECR)                     │     │
│  │  • Vulnerability scanning on push                          │     │
│  │  • Image retention policies                                │     │
│  │  • Access control (RBAC)                                   │     │
│  └────────────────────────────────────────────────────────────┘     │
│                             ↓                                         │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  5. Deployment Security                                     │     │
│  ├────────────────────────────────────────────────────────────┤     │
│  │  • Admission controllers (OPA Gatekeeper, Kyverno)         │     │
│  │  • Image signature verification (Sigstore Policy)          │     │
│  │  • Runtime security (Falco, Tetragon)                      │     │
│  │  • Network policies (Cilium, Calico)                       │     │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

### 6.2 SLSA Framework (Supply Chain Levels for Software Artifacts)
```yaml
# .github/workflows/slsa.yml
name: SLSA Build & Sign

on:
  push:
    branches: [main]

permissions:
  contents: read
  id-token: write  # OIDC for keyless signing
  packages: write

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      image-digest: ${{ steps.build.outputs.digest }}
    
    steps:
    - uses: actions/checkout@v4
    
    # Build with provenance
    - name: Build image
      id: build
      uses: docker/build-push-action@v5
      with:
        context: .
        push: true
        tags: ghcr.io/${{ github.repository }}:${{ github.sha }}
        provenance: true  # Generate SLSA provenance
        sbom: true        # Generate SBOM
    
    # Sign image with Cosign (keyless via OIDC)
    - name: Sign image
      run: |
        cosign sign --yes \
          ghcr.io/${{ github.repository }}@${{ steps.build.outputs.digest }}
    
    # Attest provenance
    - name: Attest provenance
      run: |
        cosign attest --yes \
          --predicate slsa-provenance.json \
          --type slsaprovenance \
          ghcr.io/${{ github.repository }}@${{ steps.build.outputs.digest }}
  
  verify:
    needs: build
    runs-on: ubuntu-latest
    steps:
    - name: Verify signature
      run: |
        cosign verify \
          --certificate-identity-regexp='https://github.com/${{ github.repository }}' \
          --certificate-oidc-issuer=https://token.actions.githubusercontent.com \
          ghcr.io/${{ github.repository }}@${{ needs.build.outputs.image-digest }}
    
    - name: Verify provenance
      run: |
        cosign verify-attestation \
          --type slsaprovenance \
          --certificate-identity-regexp='https://github.com/${{ github.repository }}' \
          --certificate-oidc-issuer=https://token.actions.githubusercontent.com \
          ghcr.io/${{ github.repository }}@${{ needs.build.outputs.image-digest }}
```

### 6.3 Admission Control (Policy Enforcement)
```yaml
# kyverno-policy.yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-signed-images
spec:
  validationFailureAction: Enforce
  background: false
  rules:
  
  # Require all images to be signed
  - name: verify-signature
    match:
      any:
      - resources:
          kinds:
          - Pod
    verifyImages:
    - imageReferences:
      - "registry.io/*"
      attestors:
      - entries:
        - keyless:
            subject: "https://github.com/myorg/*"
            issuer: "https://token.actions.githubusercontent.com"
            rekor:
              url: https://rekor.sigstore.dev
  
  # Block images with HIGH/CRITICAL vulnerabilities
  - name: check-vulnerabilities
    match:
      any:
      - resources:
          kinds:
          - Pod
    verifyImages:
    - imageReferences:
      - "registry.io/*"
      attestors:
      - entries:
        - keyless:
            subject: "https://github.com/myorg/*"
            issuer: "https://token.actions.githubusercontent.com"
      attestations:
      - predicateType: https://cosign.sigstore.dev/attestation/vuln/v1
        conditions:
        - all:
          - key: "{{ vulnerabilities | length(@) }}"
            operator: LessThan
            value: 10  # Max 10 vulnerabilities
  
  # Require resource limits
  - name: require-limits
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "CPU and memory limits are required"
      pattern:
        spec:
          containers:
          - resources:
              limits:
                memory: "?*"
                cpu: "?*"
  
  # Block privileged containers
  - name: block-privileged
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "Privileged containers are not allowed"
      pattern:
        spec:
          containers:
          - securityContext:
              privileged: false
```

---

## 7. GITOPS WORKFLOW (DECLARATIVE CD)

### 7.1 ArgoCD Architecture
```
┌──────────────────────────────────────────────────────────────────────┐
│                         ARGOCD ARCHITECTURE                           │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Git Repository (Source of Truth)                                    │
│  ├── apps/                                                            │
│  │   ├── myapp/                                                       │
│  │   │   ├── deployment.yaml                                         │
│  │   │   ├── service.yaml                                            │
│  │   │   └── ingress.yaml                                            │
│  │   └── another-app/                                                │
│  └── argocd/                                                          │
│      └── application.yaml  (ArgoCD Application manifest)             │
│                                                                       │
└────────────────────────────┬─────────────────────────────────────────┘
                             │ (poll every 3 min or webhook)
                             ↓
┌──────────────────────────────────────────────────────────────────────┐
│                    ARGOCD CONTROL PLANE                               │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  argocd-application-controller                              │     │
│  ├────────────────────────────────────────────────────────────┤     │
│  │  1. Fetch Git repo state                                   │     │
│  │  2. Fetch cluster state (kubectl get)                      │     │
│  │  3. Diff: desired (Git) vs actual (cluster)                │     │
│  │  4. If drift detected:                                     │     │
│  │     ├─ Auto-sync: apply changes                            │     │
│  │     └─ Manual sync: wait for approval                      │     │
│  │  5. Health assessment (readiness checks)                   │     │
│  │  6. Prune orphaned resources (if enabled)                  │     │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  argocd-repo-server                                         │     │
│  ├────────────────────────────────────────────────────────────┤     │
│  │  • Render manifests (Helm, Kustomize, jsonnet)             │     │
│  │  • Cache rendered manifests                                │     │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  argocd-server (API + UI)                                   │     │
│  ├────────────────────────────────────────────────────────────┤     │
│  │  • Web UI for visualization                                │     │
│  │  • REST API for automation                                 │     │
│  │  • SSO integration (OIDC, SAML)                            │     │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                       │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ↓ (kubectl apply)
┌──────────────────────────────────────────────────────────────────────┐
│                    KUBERNETES CLUSTER                                 │
├──────────────────────────────────────────────────────────────────────┤
│  Namespaces: prod, staging, dev                                      │
│  ├─ Deployments, Services, ConfigMaps, Secrets                       │
│  └─ Continuously reconciled with Git state                           │
└──────────────────────────────────────────────────────────────────────┘
```

### 7.2 ArgoCD Application Manifest
```yaml
# argocd/myapp-prod.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp-prod
  namespace: argocd
  finalizers:
  - resources-finalizer.argocd.argoproj.io  # Cascade delete
spec:
  project: production
  
  # Source: Git repository
  source:
    repoURL: https://github.com/myorg/k8s-manifests.git
    targetRevision: main  # Branch, tag, or commit SHA
    path: apps/myapp/overlays/prod  # Kustomize overlay
    
    # For Helm:
    # chart: myapp
    # helm:
    #   parameters:
    #   - name: image.tag
    #     value: "v2.0.0"
  
  # Destination: Kubernetes cluster
  destination:
    server: https://kubernetes.default.svc  # In-cluster
    namespace: prod
  
  # Sync policy
  syncPolicy:
    automated:
      prune: true      # Delete resources removed from Git
      selfHeal: true   # Auto-correct drift
      allowEmpty: false
    
    syncOptions:
    - CreateNamespace=true
    - PruneLast=true  # Prune after applying new resources
    - RespectIgnoreDifferences=true
    
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
  
  # Health checks
  ignoreDifferences:
  - group: apps
    kind: Deployment
    jsonPointers:
    - /spec/replicas  # Ignore HPA-managed replicas
  
  # Notifications
  revisionHistoryLimit: 10
```

### 7.3 Progressive Delivery with Argo Rollouts
```yaml
# rollout.yaml (replaces Deployment)
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: myapp
spec:
  replicas: 10
  
  strategy:
    canary:
      # Traffic routing via Istio
      trafficRouting:
        istio:
          virtualService:
            name: myapp
            routes:
            - primary
      
      # Canary steps
      steps:
      - setWeight: 5    # 5% traffic to canary
      - pause: {duration: 5m}  # Automated pause
      
      - setWeight: 25
      - pause: {duration: 10m}
      
      - setWeight: 50
      - pause: {}  # Manual approval required
      
      - setWeight: 100  # Full rollout
      
      # Analysis during each step
      analysis:
        templates:
        - templateName: success-rate
        args:
        - name: service-name
          value: myapp
  
  # Pod template (same as Deployment)
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: app
        image: registry.io/app:v2.0.0
        # ... (same as before)

---
# analysis-template.yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
spec:
  args:
  - name: service-name
  
  metrics:
  - name: success-rate
    interval: 30s
    successCondition: result[0] >= 0.99
    failureLimit: 3
    provider:
      prometheus:
        address: http://prometheus:9090
        query: |
          sum(rate(
            http_requests_total{
              service="{{args.service-name}}",
              status!~"5.."
            }[5m]
          ))
          /
          sum(rate(
            http_requests_total{
              service="{{args.service-name}}"
            }[5m]
          ))
```

**Manual Promotion**:
```bash
# Check rollout status
kubectl argo rollouts get rollout myapp

# Promote to next step
kubectl argo rollouts promote myapp

# Abort (rollback)
kubectl argo rollouts abort myapp

# Restart rollout
kubectl argo rollouts restart myapp
```

---

## 8. MULTI-REGION DEPLOYMENT

### 8.1 Region-by-Region Rollout
```
┌──────────────────────────────────────────────────────────────────────┐
│                    MULTI-REGION DEPLOYMENT STRATEGY                   │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Phase 1: Deploy to canary region (us-west-1)                        │
│  ├─ 5% of global traffic                                             │
│  ├─ Monitor for 1 hour                                               │
│  └─ Validate SLOs                                                    │
│                                                                       │
│  Phase 2: Expand to next region (us-east-1)                          │
│  ├─ Now 40% of global traffic                                        │
│  ├─ Monitor for 2 hours                                              │
│  └─ If stable, continue                                              │
│                                                                       │
│  Phase 3: Roll out to EU (eu-west-1)                                 │
│  ├─ Now 75% of global traffic                                        │
│  └─ Monitor business hours overlap                                   │
│                                                                       │
│  Phase 4: Remaining regions (APAC, etc.)                             │
│  └─ 100% global coverage                                             │
│                                                                       │
│  At ANY phase: if SLO violation → halt rollout, rollback affected    │
│                regions, investigate                                  │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

**Multi-Cluster ArgoCD**:
```yaml
# argocd/applicationset.yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: myapp-global
spec:
  generators:
  - list:
      elements:
      - cluster: us-west-1
        url: https://k8s-us-west-1.example.com
        env: prod
        weight: canary
      - cluster: us-east-1
        url: https://k8s-us-east-1.example.com
        env: prod
        weight: stable
      - cluster: eu-west-1
        url: https://k8s-eu-west-1.example.com
        env: prod
        weight: stable
  
  template:
    metadata:
      name: 'myapp-{{cluster}}'
    spec:
      project: production
      source:
        repoURL: https://github.com/myorg/k8s-manifests.git
        targetRevision: main
        path: 'apps/myapp/clusters/{{cluster}}'
      destination:
        server: '{{url}}'
        namespace: prod
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
        - CreateNamespace=true
```

---

## 9. NEXT 3 STEPS

**1. Implement GitOps with ArgoCD** (next 4 hours):
```bash
# Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Access UI
kubectl port-forward svc/argocd-server -n argocd 8080:443
# Login: admin / $(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)

# Create first application
kubectl apply -f - <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp-dev
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/yourusername/k8s-configs.git
    targetRevision: HEAD
    path: apps/myapp
  destination:
    server: https://kubernetes.default.svc
    namespace: dev
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
EOF
```

**2. Set Up Observability Stack** (next 6 hours):
```bash
# Install kube-prometheus-stack (Prometheus + Grafana + Alertmanager)
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install kube-prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --set prometheus.prometheusSpec.retention=30d \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=50Gi

# Install Loki for logs
helm install loki grafana/loki-stack \
  --namespace monitoring \
  --set grafana.enabled=false

# Install Jaeger for traces
kubectl apply -f https://github.com/jaegertracing/jaeger-operator/releases/download/v1.51.0/jaeger-operator.yaml
```

**3. Implement Automated Canary with Flagger** (next 8 hours):
```bash
# Install Flagger
helm repo add flagger https://flagger.app
helm install flagger flagger/flagger \
  --namespace istio-system \
  --set meshProvider=istio \
  --set metricsServer=http://prometheus:9090

# Install Flagger load tester (for webhooks)
helm install flagger-loadtester flagger/loadtester \
  --namespace test

# Create first canary
kubectl apply -f canary.yaml  # (from section 3.2)

# Monitor
watch kubectl get canary -A
```

---

## REFERENCES

**GitOps & CD**:
- ArgoCD: https://argo-cd.readthedocs.io/
- Flux: https://fluxcd.io/docs/
- Argo Rollouts: https://argoproj.github.io/argo-rollouts/

**Progressive Delivery**:
- Flagger: https://flagger.app/
- Feature Flags: https://docs.getunleash.io/

**Security**:
- Sigstore/Cosign: https://docs.sigstore.dev/
- SLSA: https://slsa.dev/
- OPA Gatekeeper: https://open-policy-agent.github.io/gatekeeper/
- Kyverno: https://kyverno.io/

**Observability**:
- Prometheus: https://prometheus.io/docs/
- OpenTelemetry: https://opentelemetry.io/docs/
- Grafana: https://grafana.com/docs/

This guide provides production-grade CI/CD patterns for zero-impact deployments using control/data plane separation, progressive delivery, and automated validation.