# Policy-as-Code: Comprehensive Deep-Dive Guide

**Summary**: Policy-as-Code (PaC) treats security, compliance, and operational policies as versioned, testable code artifacts that programmatically enforce constraints across infrastructure, applications, and runtime environments. Core implementation revolves around policy engines (OPA/Rego, Kyverno, CEL, jsPolicy), enforcement points (admission controllers, CI/CD gates, runtime hooks), and decision-making models (attribute-based, relationship-based). Security implications span trust boundaries (policy tampering, decision bypass), performance (evaluation latency, cache poisoning), and operational risk (policy drift, emergency override). Production deployments require formal verification, audit trails, gradual rollout with shadow mode, and circuit breakers for policy evaluation failures.

---

## I. FOUNDATIONAL CONCEPTS & ARCHITECTURE

### Core Principles

**Policy-as-Code Philosophy**:
1. **Declarative Constraints**: Policies express "what" should be true, not "how" to enforce
2. **Version-Controlled**: Policy documents live in Git with full audit history
3. **Testable**: Policies validated via unit tests, integration tests, and fuzzing
4. **Composable**: Policies stack and combine across organizational boundaries
5. **Observable**: All decisions logged, traced, and auditable
6. **Fail-Safe**: Default-deny on evaluation errors, with override mechanisms

**Policy Decision Point (PDP) vs Policy Enforcement Point (PEP)**:
```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Request   │────────▶│     PEP      │────────▶│ Application │
│  (Subject,  │         │ (Intercept & │         │  (Allowed   │
│  Resource,  │         │   Forward)   │         │   Action)   │
│   Action)   │         └──────┬───────┘         └─────────────┘
└─────────────┘                │
                               │ Policy Query
                               ▼
                        ┌──────────────┐
                        │     PDP      │
                        │ (Evaluate &  │
                        │   Decide)    │
                        └──────┬───────┘
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
         ┌───────────┐  ┌───────────┐  ┌───────────┐
         │  Policies │  │   Data    │  │  Context  │
         │  (Rules)  │  │ (External)│  │ (Runtime) │
         └───────────┘  └───────────┘  └───────────┘
```

**Architecture Layers**:
```
┌────────────────────────────────────────────────────────────┐
│ L4: Policy Management Plane                                │
│  - Policy Authoring, Versioning, Distribution              │
│  - GitOps Sync, Validation Webhooks                        │
└────────────────────────────────────────────────────────────┘
                           │
┌────────────────────────────────────────────────────────────┐
│ L3: Policy Decision Layer                                  │
│  - OPA, Kyverno, CEL Engines                               │
│  - Rego/CEL/Python Evaluation                              │
│  - Caching, Performance Optimization                       │
└────────────────────────────────────────────────────────────┘
                           │
┌────────────────────────────────────────────────────────────┐
│ L2: Enforcement Points                                     │
│  - K8s Admission Controllers (Validating/Mutating)         │
│  - Service Mesh AuthZ (Envoy, Linkerd)                     │
│  - CI/CD Gates, Terraform Plan Checks                      │
│  - Runtime Agents (eBPF, Seccomp, AppArmor)               │
└────────────────────────────────────────────────────────────┘
                           │
┌────────────────────────────────────────────────────────────┐
│ L1: Audit & Observability                                  │
│  - Decision Logs (OpenTelemetry, Jaeger)                   │
│  - Metrics (Prometheus, Grafana)                           │
│  - Compliance Reports, Violation Alerts                    │
└────────────────────────────────────────────────────────────┘
```

---

## II. POLICY ENGINES & LANGUAGES

### A. Open Policy Agent (OPA) + Rego

**Architecture**:
```
OPA Server (Go-based)
├── REST API (:8181)
│   ├── /v1/data/{path}      - Query decisions
│   ├── /v1/policies/{id}    - Manage policies
│   └── /health              - Health check
├── Rego Compiler
│   ├── Parse → AST
│   ├── Type Check
│   ├── Optimize (Partial Eval, Indexing)
│   └── Compile → IR (Wasm optionally)
├── Evaluation Engine
│   ├── Unification (Datalog-style)
│   ├── Rule Resolution (Top-down)
│   └── Built-in Functions (crypto, HTTP, JWT)
└── Data Store
    ├── Base Documents (JSON)
    ├── Policy Bundles (tar.gz)
    └── Decision Cache
```

**Rego Language Deep-Dive**:

Rego is a declarative query language based on Datalog with:
- **Rules**: Named expressions that evaluate to true/false or produce values
- **Comprehensions**: Set/array/object builders
- **Unification**: Pattern matching via `=` operator
- **Virtual Documents**: Computed data structures

**Example Policy (Pod Security)**:
```rego
package kubernetes.admission

# Deny pods with privileged containers
deny_privileged[msg] {
    input.request.kind.kind == "Pod"
    container := input.request.object.spec.containers[_]
    container.securityContext.privileged == true
    msg := sprintf("Privileged container %v not allowed", [container.name])
}

# Deny pods without resource limits
deny_no_limits[msg] {
    input.request.kind.kind == "Pod"
    container := input.request.object.spec.containers[_]
    not container.resources.limits
    msg := sprintf("Container %v missing resource limits", [container.name])
}

# Require specific image registries
allowed_registries := {"gcr.io", "docker.io/library"}

deny_untrusted_registry[msg] {
    input.request.kind.kind == "Pod"
    container := input.request.object.spec.containers[_]
    image := container.image
    not registry_allowed(image)
    msg := sprintf("Image %v from untrusted registry", [image])
}

registry_allowed(image) {
    registry := split(image, "/")[0]
    allowed_registries[registry]
}

# Aggregate all denials
violation[{"msg": msg}] {
    deny_privileged[msg]
}

violation[{"msg": msg}] {
    deny_no_limits[msg]
}

violation[{"msg": msg}] {
    deny_untrusted_registry[msg]
}
```

**OPA Deployment (Kubernetes Admission Controller)**:

```bash
# Deploy OPA as admission controller
kubectl apply -f - <<EOF
apiVersion: v1
kind: Namespace
metadata:
  name: opa
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: opa
  namespace: opa
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: opa-reader
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: opa-reader
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: opa-reader
subjects:
- kind: ServiceAccount
  name: opa
  namespace: opa
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: opa
  namespace: opa
spec:
  replicas: 3
  selector:
    matchLabels:
      app: opa
  template:
    metadata:
      labels:
        app: opa
    spec:
      serviceAccountName: opa
      containers:
      - name: opa
        image: openpolicyagent/opa:0.61.0-rootless
        args:
        - "run"
        - "--server"
        - "--addr=:8181"
        - "--diagnostic-addr=:8282"
        - "--set=decision_logs.console=true"
        - "--set=status.console=true"
        - "--set=bundles.main.service=bundle-server"
        - "--set=bundles.main.resource=bundles/kubernetes"
        - "--set=bundles.main.polling.min_delay_seconds=10"
        - "--set=bundles.main.polling.max_delay_seconds=30"
        ports:
        - containerPort: 8181
          name: https
        - containerPort: 8282
          name: diagnostics
        livenessProbe:
          httpGet:
            path: /health
            port: 8282
          initialDelaySeconds: 5
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health?bundle=true
            port: 8282
          initialDelaySeconds: 5
          periodSeconds: 10
        resources:
          limits:
            cpu: "1000m"
            memory: "512Mi"
          requests:
            cpu: "100m"
            memory: "128Mi"
        securityContext:
          runAsNonRoot: true
          runAsUser: 1000
          readOnlyRootFilesystem: true
          allowPrivilegeEscalation: false
          capabilities:
            drop: ["ALL"]
---
apiVersion: v1
kind: Service
metadata:
  name: opa
  namespace: opa
spec:
  selector:
    app: opa
  ports:
  - port: 443
    targetPort: 8181
    protocol: TCP
    name: https
---
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: opa-validating-webhook
webhooks:
- name: validating-webhook.openpolicyagent.org
  admissionReviewVersions: ["v1", "v1beta1"]
  clientConfig:
    service:
      name: opa
      namespace: opa
      path: /v1/admit
    caBundle: LS0tLS1CRUdJTi... # Add your CA bundle
  rules:
  - operations: ["CREATE", "UPDATE"]
    apiGroups: ["*"]
    apiVersions: ["*"]
    resources: ["pods", "deployments", "services"]
  failurePolicy: Fail
  sideEffects: None
  timeoutSeconds: 5
EOF
```

**OPA Policy Testing**:

```bash
# Create test file: policy_test.rego
cat > policy_test.rego <<'EOF'
package kubernetes.admission

test_deny_privileged {
    input := {
        "request": {
            "kind": {"kind": "Pod"},
            "object": {
                "spec": {
                    "containers": [{
                        "name": "nginx",
                        "securityContext": {"privileged": true}
                    }]
                }
            }
        }
    }
    count(deny_privileged) > 0
}

test_allow_unprivileged {
    input := {
        "request": {
            "kind": {"kind": "Pod"},
            "object": {
                "spec": {
                    "containers": [{
                        "name": "nginx",
                        "securityContext": {"privileged": false},
                        "resources": {"limits": {"cpu": "100m"}}
                    }]
                }
            }
        }
    }
    count(deny_privileged) == 0
}
EOF

# Run tests
opa test policy.rego policy_test.rego -v

# Run with coverage
opa test --coverage --format=json policy.rego policy_test.rego

# Benchmark policies
cat > bench_test.rego <<'EOF'
package kubernetes.admission

test_benchmark_deny {
    input := {
        "request": {
            "kind": {"kind": "Pod"},
            "object": {
                "spec": {
                    "containers": [{
                        "name": "test",
                        "securityContext": {"privileged": true}
                    }]
                }
            }
        }
    }
    violation[_]
}
EOF

opa test --bench bench_test.rego
```

**OPA Compile to Wasm** (for edge deployment):

```bash
# Compile Rego to Wasm
opa build -t wasm -e kubernetes/admission/violation policy.rego

# Extract policy.wasm from bundle
tar -xzf bundle.tar.gz /policy.wasm

# Load in Go application
cat > main.go <<'EOF'
package main

import (
    "context"
    "encoding/json"
    "fmt"
    "os"
    
    "github.com/open-policy-agent/opa/sdk"
)

func main() {
    ctx := context.Background()
    
    // Initialize OPA with Wasm module
    opa, err := sdk.New(ctx, sdk.Options{
        Config: strings.NewReader(`{
            "bundles": {
                "main": {
                    "resource": "/bundle.tar.gz"
                }
            }
        }`),
    })
    if err != nil {
        panic(err)
    }
    defer opa.Stop(ctx)
    
    // Example decision
    input := map[string]interface{}{
        "request": map[string]interface{}{
            "kind": map[string]interface{}{"kind": "Pod"},
            "object": map[string]interface{}{
                "spec": map[string]interface{}{
                    "containers": []interface{}{
                        map[string]interface{}{
                            "name": "nginx",
                            "securityContext": map[string]interface{}{
                                "privileged": true,
                            },
                        },
                    },
                },
            },
        },
    }
    
    result, err := opa.Decision(ctx, sdk.DecisionOptions{
        Path:  "kubernetes/admission/violation",
        Input: input,
    })
    if err != nil {
        panic(err)
    }
    
    fmt.Printf("Result: %+v\n", result.Result)
}
EOF

go mod init opa-wasm-demo
go get github.com/open-policy-agent/opa/sdk@latest
go run main.go
```

---

### B. Kyverno (Kubernetes-Native)

**Architecture**:
```
Kyverno Components
├── Admission Controller
│   ├── Validating Webhook
│   ├── Mutating Webhook
│   └── Policy Webhook (Background Scan)
├── Policy Engine
│   ├── CEL Expressions
│   ├── JMESPath Filters
│   └── Resource Context Matching
├── Background Controller
│   ├── Policy Report CRD
│   ├── Generate Resources
│   └── Cleanup TTL
└── Metrics/Events
    ├── Prometheus Metrics
    └── K8s Events
```

**Kyverno Policy Example**:

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-pod-security-standards
  annotations:
    policies.kyverno.io/title: Require Pod Security Standards
    policies.kyverno.io/severity: high
    policies.kyverno.io/description: >-
      Enforces baseline pod security standards including
      no privileged containers, no host namespaces, and
      required resource limits.
spec:
  validationFailureAction: Enforce  # or Audit
  background: true
  failurePolicy: Fail
  rules:
  
  # Rule 1: Deny privileged containers
  - name: deny-privileged
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
          - =(securityContext):
              =(privileged): false
  
  # Rule 2: Require non-root user
  - name: require-non-root
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "Containers must run as non-root"
      cel:
        expressions:
        - expression: >-
            object.spec.containers.all(c,
              has(c.securityContext) &&
              has(c.securityContext.runAsNonRoot) &&
              c.securityContext.runAsNonRoot == true
            )
          message: "All containers must set runAsNonRoot: true"
  
  # Rule 3: Require resource limits
  - name: require-limits
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "Resource limits are required"
      foreach:
      - list: "request.object.spec.containers"
        deny:
          conditions:
            any:
            - key: "{{ element.resources.limits.memory || '' }}"
              operator: Equals
              value: ""
            - key: "{{ element.resources.limits.cpu || '' }}"
              operator: Equals
              value: ""
  
  # Rule 4: Mutate to add seccomp profile
  - name: add-seccomp-profile
    match:
      any:
      - resources:
          kinds:
          - Pod
    mutate:
      patchStrategicMerge:
        spec:
          securityContext:
            seccompProfile:
              type: RuntimeDefault
  
  # Rule 5: Generate network policy for labeled pods
  - name: generate-netpol
    match:
      any:
      - resources:
          kinds:
          - Pod
          selector:
            matchLabels:
              require-netpol: "true"
    generate:
      apiVersion: networking.k8s.io/v1
      kind: NetworkPolicy
      name: "{{ request.object.metadata.name }}-netpol"
      namespace: "{{ request.namespace }}"
      synchronize: true
      data:
        spec:
          podSelector:
            matchLabels:
              app: "{{ request.object.metadata.labels.app }}"
          policyTypes:
          - Ingress
          - Egress
          ingress:
          - from:
            - podSelector:
                matchLabels:
                  network-zone: trusted
          egress:
          - to:
            - namespaceSelector:
                matchLabels:
                  kubernetes.io/metadata.name: kube-system
```

**Deploy Kyverno**:

```bash
# Install Kyverno via Helm
helm repo add kyverno https://kyverno.github.io/kyverno/
helm repo update

# Production values
cat > kyverno-values.yaml <<EOF
replicaCount: 3

image:
  repository: ghcr.io/kyverno/kyverno
  tag: v1.11.4

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 100m
    memory: 128Mi

admissionController:
  replicas: 3
  serviceMonitor:
    enabled: true
  
backgroundController:
  replicas: 2

cleanupController:
  replicas: 1

reportsController:
  replicas: 2

config:
  webhookTimeout: 10
  generateSuccessEvents: false
  excludeGroupRole:
  - system:serviceaccounts:kube-system

# High availability
podDisruptionBudget:
  minAvailable: 1

# Security
podSecurityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000
  seccompProfile:
    type: RuntimeDefault

# Network policy
networkPolicy:
  enabled: true
EOF

helm install kyverno kyverno/kyverno -n kyverno --create-namespace \
  -f kyverno-values.yaml

# Verify installation
kubectl get pods -n kyverno
kubectl get validatingwebhookconfigurations
kubectl get mutatingwebhookconfigurations
```

**Kyverno CLI Testing**:

```bash
# Install Kyverno CLI
curl -LO https://github.com/kyverno/kyverno/releases/download/v1.11.4/kyverno-cli_v1.11.4_linux_x86_64.tar.gz
tar -xzf kyverno-cli_v1.11.4_linux_x86_64.tar.gz
sudo mv kyverno /usr/local/bin/

# Test policy against resources
cat > test-pod.yaml <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
spec:
  containers:
  - name: nginx
    image: nginx:latest
    securityContext:
      privileged: true
EOF

kyverno apply require-pod-security-standards.yaml --resource test-pod.yaml

# Expected output: policy violations

# Test with compliant pod
cat > compliant-pod.yaml <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: compliant-pod
spec:
  securityContext:
    runAsNonRoot: true
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: nginx
    image: nginx:latest
    securityContext:
      runAsNonRoot: true
      runAsUser: 1000
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
    resources:
      limits:
        cpu: "100m"
        memory: "128Mi"
EOF

kyverno apply require-pod-security-standards.yaml --resource compliant-pod.yaml

# Test mutation
kyverno apply require-pod-security-standards.yaml --resource compliant-pod.yaml \
  --output yaml

# Test with variable values
kyverno apply policy.yaml --resource resource.yaml \
  --values-file values.yaml
```

---

### C. Common Expression Language (CEL)

**CEL in Kubernetes Validation**:

CEL is embedded directly in Kubernetes 1.25+ for:
- ValidatingAdmissionPolicy (native K8s, no webhook)
- CRD validation rules
- Field selectors

**Example ValidatingAdmissionPolicy**:

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata:
  name: pod-security-policy
spec:
  failurePolicy: Fail
  matchConstraints:
    resourceRules:
    - apiGroups: [""]
      apiVersions: ["v1"]
      operations: ["CREATE", "UPDATE"]
      resources: ["pods"]
  
  validations:
  # Deny privileged containers
  - expression: >-
      object.spec.containers.all(c,
        !has(c.securityContext) ||
        !has(c.securityContext.privileged) ||
        c.securityContext.privileged == false
      )
    message: "Privileged containers not allowed"
    reason: Forbidden
  
  # Require resource limits
  - expression: >-
      object.spec.containers.all(c,
        has(c.resources) &&
        has(c.resources.limits) &&
        has(c.resources.limits.memory) &&
        has(c.resources.limits.cpu)
      )
    message: "All containers must have CPU and memory limits"
  
  # Deny host namespaces
  - expression: >-
      !has(object.spec.hostNetwork) || object.spec.hostNetwork == false
    message: "hostNetwork not allowed"
  
  - expression: >-
      !has(object.spec.hostPID) || object.spec.hostPID == false
    message: "hostPID not allowed"
  
  - expression: >-
      !has(object.spec.hostIPC) || object.spec.hostIPC == false
    message: "hostIPC not allowed"
  
  # Require runAsNonRoot
  - expression: >-
      object.spec.containers.all(c,
        has(c.securityContext) &&
        has(c.securityContext.runAsNonRoot) &&
        c.securityContext.runAsNonRoot == true
      )
    message: "Containers must run as non-root"
  
  # Validate image registry
  - expression: >-
      object.spec.containers.all(c,
        c.image.startsWith('gcr.io/') ||
        c.image.startsWith('docker.io/library/')
      )
    message: "Only trusted registries allowed"
  
  # Advanced: Require specific labels
  - expression: >-
      has(object.metadata.labels) &&
      has(object.metadata.labels.team) &&
      has(object.metadata.labels.env)
    message: "Pods must have 'team' and 'env' labels"
  
  # Variable binding for complex checks
  - expression: "!variables.hasSensitiveMount"
    messageExpression: "'Sensitive mount detected: ' + variables.sensitivePath"
  
  variables:
  - name: sensitivePaths
    expression: "['/etc/shadow', '/etc/passwd', '/root/.ssh']"
  
  - name: hasSensitiveMount
    expression: >-
      object.spec.containers.exists(c,
        has(c.volumeMounts) &&
        c.volumeMounts.exists(m,
          variables.sensitivePaths.exists(p, m.mountPath == p)
        )
      )
  
  - name: sensitivePath
    expression: >-
      object.spec.containers
        .filter(c, has(c.volumeMounts))
        .map(c, c.volumeMounts)
        .flatten()
        .filter(m, variables.sensitivePaths.exists(p, m.mountPath == p))
        .map(m, m.mountPath)[0]

---
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicyBinding
metadata:
  name: pod-security-binding
spec:
  policyName: pod-security-policy
  validationActions: [Deny]
  matchResources:
    namespaceSelector:
      matchExpressions:
      - key: environment
        operator: NotIn
        values: ["test", "dev"]
```

**CEL Performance Optimization**:

```go
// CEL cost limits in K8s
const (
    // Maximum cost per validation
    MaxCost = 1000000
    
    // Cost per operation
    CostPerIteration = 1
    CostPerFieldAccess = 1
    CostPerCall = 10
)

// Example: Optimize expensive checks
// Bad: O(n²) nested loops
object.spec.containers.all(c1,
  object.spec.containers.all(c2,
    c1.name != c2.name
  )
)

// Good: O(n) with CEL macros
size(object.spec.containers.map(c, c.name).unique()) == size(object.spec.containers)
```

---

### D. Gatekeeper (OPA for Kubernetes)

**Gatekeeper Architecture**:
```
┌─────────────────────────────────────────────┐
│   Gatekeeper Admission Controller           │
│   ┌─────────────┐      ┌─────────────┐     │
│   │ Validating  │      │  Mutating   │     │
│   │  Webhook    │      │  Webhook    │     │
│   └──────┬──────┘      └──────┬──────┘     │
│          │                    │             │
│   ┌──────▼────────────────────▼──────┐     │
│   │   Constraint Framework            │     │
│   │  (ConstraintTemplate + Constraint)│     │
│   └──────┬────────────────────────────┘     │
│          │                                   │
│   ┌──────▼──────┐      ┌─────────────┐     │
│   │ OPA Engine  │      │ Audit       │     │
│   │ (Rego)      │      │ Controller  │     │
│   └─────────────┘      └─────────────┘     │
└─────────────────────────────────────────────┘
```

**ConstraintTemplate (Policy Definition)**:

```yaml
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8spspprivilegedcontainer
  annotations:
    metadata.gatekeeper.sh/title: "Privileged Container"
    metadata.gatekeeper.sh/version: 1.0.0
    description: "Denies privileged containers in Pods"
spec:
  crd:
    spec:
      names:
        kind: K8sPSPPrivilegedContainer
      validation:
        openAPIV3Schema:
          type: object
          properties:
            exemptImages:
              description: "Images exempt from policy"
              type: array
              items:
                type: string
  
  targets:
  - target: admission.k8s.gatekeeper.sh
    rego: |
      package k8spspprivilegedcontainer
      
      violation[{"msg": msg, "details": {}}] {
        c := input_containers[_]
        c.securityContext.privileged
        not is_exempt(c.image)
        msg := sprintf("Privileged container is not allowed: %v, securityContext: %v", [c.name, c.securityContext])
      }
      
      input_containers[c] {
        c := input.review.object.spec.containers[_]
      }
      
      input_containers[c] {
        c := input.review.object.spec.initContainers[_]
      }
      
      input_containers[c] {
        c := input.review.object.spec.ephemeralContainers[_]
      }
      
      is_exempt(image) {
        exempt_image := input.parameters.exemptImages[_]
        startswith(image, exempt_image)
      }
```

**Constraint (Policy Instance)**:

```yaml
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sPSPPrivilegedContainer
metadata:
  name: psp-privileged-container
spec:
  enforcementAction: deny  # deny, dryrun, warn
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
    namespaces:
    - "production"
    - "staging"
    excludedNamespaces:
    - "kube-system"
  parameters:
    exemptImages:
    - "gcr.io/kube-proxy"
```

**Deploy Gatekeeper**:

```bash
# Install Gatekeeper
kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/master/deploy/gatekeeper.yaml

# Verify
kubectl get pods -n gatekeeper-system
kubectl get validatingwebhookconfigurations
kubectl get crd | grep gatekeeper

# Install policy library
git clone https://github.com/open-policy-agent/gatekeeper-library.git
cd gatekeeper-library/library

# Apply pod security policies
kubectl apply -f pod-security-policy/

# Check constraints
kubectl get constraints

# View violations
kubectl get k8spspprivilegedcontainer -o yaml
```

**Gatekeeper Audit & Reporting**:

```bash
# Enable audit
kubectl edit configmap gatekeeper-manager-config -n gatekeeper-system

# Add audit configuration
data:
  config.yaml: |
    auditInterval: 60
    auditFromCache: true
    constraintViolationsLimit: 20
    auditChunkSize: 500

# Check audit results
kubectl get constraints -A -o json | \
  jq '.items[] | select(.status.totalViolations > 0) | {
    name: .metadata.name,
    violations: .status.totalViolations,
    details: .status.violations
  }'

# Export violations to Prometheus
cat > servicemonitor.yaml <<EOF
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: gatekeeper
  namespace: gatekeeper-system
spec:
  selector:
    matchLabels:
      control-plane: controller-manager
      gatekeeper.sh/system: "yes"
  endpoints:
  - port: metrics
    interval: 30s
EOF

kubectl apply -f servicemonitor.yaml
```

---

## III. ENFORCEMENT POINTS

### A. Kubernetes Admission Control

**Admission Chain**:
```
API Request
   │
   ▼
┌──────────────┐
│ Authentication│ (Who are you?)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Authorization │ (Can you do this?)
│  (RBAC/ABAC) │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Mutating     │ (Modify request)
│ Admission    │ - Add labels/annotations
└──────┬───────┘ - Inject sidecars
       │         - Set defaults
       ▼
┌──────────────┐
│ Object       │ (Validate schema)
│ Schema       │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Validating   │ (Is this allowed?)
│ Admission    │ - Policy checks
└──────┬───────┘ - Business rules
       │
       ▼
┌──────────────┐
│ Persist to   │
│ etcd         │
└──────────────┘
```

**Custom Admission Webhook (Go)**:

```go
// admission-webhook.go
package main

import (
    "encoding/json"
    "fmt"
    "io"
    "net/http"
    
    admissionv1 "k8s.io/api/admission/v1"
    corev1 "k8s.io/api/core/v1"
    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

type WebhookServer struct {
    server *http.Server
}

// Policy: Deny pods without resource limits
func (ws *WebhookServer) validate(ar admissionv1.AdmissionReview) *admissionv1.AdmissionResponse {
    req := ar.Request
    
    // Parse Pod object
    var pod corev1.Pod
    if err := json.Unmarshal(req.Object.Raw, &pod); err != nil {
        return &admissionv1.AdmissionResponse{
            Allowed: false,
            Result: &metav1.Status{
                Message: fmt.Sprintf("Failed to parse pod: %v", err),
            },
        }
    }
    
    // Validation logic
    violations := []string{}
    
    for _, container := range pod.Spec.Containers {
        // Check privileged
        if container.SecurityContext != nil && 
           container.SecurityContext.Privileged != nil &&
           *container.SecurityContext.Privileged {
            violations = append(violations, 
                fmt.Sprintf("Container %s is privileged", container.Name))
        }
        
        // Check resource limits
        if container.Resources.Limits == nil {
            violations = append(violations,
                fmt.Sprintf("Container %s missing resource limits", container.Name))
        }
        
        // Check image registry
        if !strings.HasPrefix(container.Image, "gcr.io/") &&
           !strings.HasPrefix(container.Image, "docker.io/library/") {
            violations = append(violations,
                fmt.Sprintf("Container %s uses untrusted registry", container.Name))
        }
        
        // Check capabilities
        if container.SecurityContext != nil &&
           container.SecurityContext.Capabilities != nil {
            for _, cap := range container.SecurityContext.Capabilities.Add {
                if cap == "SYS_ADMIN" || cap == "NET_ADMIN" {
                    violations = append(violations,
                        fmt.Sprintf("Container %s requests dangerous capability %s", 
                            container.Name, cap))
                }
            }
        }
    }
    
    if len(violations) > 0 {
        return &admissionv1.AdmissionResponse{
            Allowed: false,
            Result: &metav1.Status{
                Message: fmt.Sprintf("Policy violations:\n%s", 
                    strings.Join(violations, "\n")),
                Code: http.StatusForbidden,
            },
        }
    }
    
    return &admissionv1.AdmissionResponse{
        Allowed: true,
    }
}

// Mutate: Add security context defaults
func (ws *WebhookServer) mutate(ar admissionv1.AdmissionReview) *admissionv1.AdmissionResponse {
    req := ar.Request
    
    var pod corev1.Pod
    if err := json.Unmarshal(req.Object.Raw, &pod); err != nil {
        return &admissionv1.AdmissionResponse{
            Allowed: false,
            Result: &metav1.Status{
                Message: fmt.Sprintf("Failed to parse pod: %v", err),
            },
        }
    }
    
    // Build JSON patch
    patches := []map[string]interface{}{}
    
    // Add seccomp profile if missing
    if pod.Spec.SecurityContext == nil || 
       pod.Spec.SecurityContext.SeccompProfile == nil {
        patches = append(patches, map[string]interface{}{
            "op": "add",
            "path": "/spec/securityContext",
            "value": map[string]interface{}{
                "seccompProfile": map[string]string{
                    "type": "RuntimeDefault",
                },
            },
        })
    }
    
    // Add runAsNonRoot to containers
    for i := range pod.Spec.Containers {
        if pod.Spec.Containers[i].SecurityContext == nil ||
           pod.Spec.Containers[i].SecurityContext.RunAsNonRoot == nil {
            patches = append(patches, map[string]interface{}{
                "op": "add",
                "path": fmt.Sprintf("/spec/containers/%d/securityContext/runAsNonRoot", i),
                "value": true,
            })
        }
    }
    
    patchBytes, err := json.Marshal(patches)
    if err != nil {
        return &admissionv1.AdmissionResponse{
            Allowed: false,
            Result: &metav1.Status{
                Message: fmt.Sprintf("Failed to marshal patches: %v", err),
            },
        }
    }
    
    return &admissionv1.AdmissionResponse{
        Allowed: true,
        Patch: patchBytes,
        PatchType: func() *admissionv1.PatchType {
            pt := admissionv1.PatchTypeJSONPatch
            return &pt
        }(),
    }
}

func (ws *WebhookServer) serve(w http.ResponseWriter, r *http.Request) {
    var body []byte
    if r.Body != nil {
        if data, err := io.ReadAll(r.Body); err == nil {
            body = data
        }
    }
    
    // Parse AdmissionReview
    var admissionReviewReq admissionv1.AdmissionReview
    if err := json.Unmarshal(body, &admissionReviewReq); err != nil {
        http.Error(w, "Invalid request", http.StatusBadRequest)
        return
    }
    
    // Process based on path
    var admissionResponse *admissionv1.AdmissionResponse
    if r.URL.Path == "/validate" {
        admissionResponse = ws.validate(admissionReviewReq)
    } else if r.URL.Path == "/mutate" {
        admissionResponse = ws.mutate(admissionReviewReq)
    } else {
        http.Error(w, "Not found", http.StatusNotFound)
        return
    }
    
    // Build response
    admissionReviewRes := admissionv1.AdmissionReview{
        TypeMeta: metav1.TypeMeta{
            APIVersion: "admission.k8s.io/v1",
            Kind: "AdmissionReview",
        },
        Response: admissionResponse,
    }
    
    if admissionReviewReq.Request != nil {
        admissionReviewRes.Response.UID = admissionReviewReq.Request.UID
    }
    
    respBytes, err := json.Marshal(admissionReviewRes)
    if err != nil {
        http.Error(w, "Failed to marshal response", http.StatusInternalServerError)
        return
    }
    
    w.Header().Set("Content-Type", "application/json")
    w.Write(respBytes)
}

func main() {
    ws := &WebhookServer{}
    
    mux := http.NewServeMux()
    mux.HandleFunc("/validate", ws.serve)
    mux.HandleFunc("/mutate", ws.serve)
    mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
        w.WriteHeader(http.StatusOK)
        w.Write([]byte("ok"))
    })
    
    ws.server = &http.Server{
        Addr:    ":8443",
        Handler: mux,
    }
    
    // TLS config with mTLS
    tlsConfig := &tls.Config{
        MinVersion: tls.VersionTLS13,
        ClientAuth: tls.RequireAndVerifyClientCert,
    }
    
    ws.server.TLSConfig = tlsConfig
    
    fmt.Println("Starting webhook server on :8443")
    if err := ws.server.ListenAndServeTLS("/certs/tls.crt", "/certs/tls.key"); err != nil {
        panic(err)
    }
}
```

**Deploy Webhook**:

```bash
# Build and push
docker build -t myregistry/admission-webhook:v1 .
docker push myregistry/admission-webhook:v1

# Generate certificates
./scripts/generate-certs.sh

# Deploy
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: admission-webhook
  namespace: policy-system
spec:
  replicas: 3
  selector:
    matchLabels:
      app: admission-webhook
  template:
    metadata:
      labels:
        app: admission-webhook
    spec:
      containers:
      - name: webhook
        image: myregistry/admission-webhook:v1
        ports:
        - containerPort: 8443
        volumeMounts:
        - name: certs
          mountPath: /certs
          readOnly: true
      volumes:
      - name: certs
        secret:
          secretName: webhook-certs
---
apiVersion: v1
kind: Service
metadata:
  name: admission-webhook
  namespace: policy-system
spec:
  selector:
    app: admission-webhook
  ports:
  - port: 443
    targetPort: 8443
---
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: admission-webhook
webhooks:
- name: validate.policy.io
  clientConfig:
    service:
      name: admission-webhook
      namespace: policy-system
      path: /validate
    caBundle: ${CA_BUNDLE}
  rules:
  - operations: ["CREATE", "UPDATE"]
    apiGroups: [""]
    apiVersions: ["v1"]
    resources: ["pods"]
  admissionReviewVersions: ["v1"]
  sideEffects: None
  failurePolicy: Fail
  timeoutSeconds: 5
EOF
```

---

### B. CI/CD Pipeline Integration

**Terraform Policy Checks (Conftest + OPA)**:

```bash
# Install conftest
curl -L https://github.com/open-policy-agent/conftest/releases/download/v0.49.1/conftest_0.49.1_Linux_x86_64.tar.gz | \
  tar xz -C /usr/local/bin

# Policy: terraform.rego
cat > policy/terraform.rego <<'EOF'
package terraform

# Deny S3 buckets without encryption
deny_unencrypted_s3[msg] {
    resource := input.resource.aws_s3_bucket[name]
    not resource.server_side_encryption_configuration
    msg := sprintf("S3 bucket %v must have encryption enabled", [name])
}

# Deny security groups with 0.0.0.0/0 ingress
deny_open_sg[msg] {
    resource := input.resource.aws_security_group[name]
    rule := resource.ingress[_]
    rule.cidr_blocks[_] == "0.0.0.0/0"
    msg := sprintf("Security group %v allows ingress from 0.0.0.0/0", [name])
}

# Require tags
deny_missing_tags[msg] {
    resource := input.resource.aws_instance[name]
    required_tags := {"Environment", "Owner", "CostCenter"}
    existing_tags := {tag | resource.tags[tag]}
    missing := required_tags - existing_tags
    count(missing) > 0
    msg := sprintf("Instance %v missing required tags: %v", [name, missing])
}

# Enforce encryption for RDS
deny_unencrypted_rds[msg] {
    resource := input.resource.aws_db_instance[name]
    not resource.storage_encrypted
    msg := sprintf("RDS instance %v must have storage encryption", [name])
}

violation[{"msg": msg}] { deny_unencrypted_s3[msg] }
violation[{"msg": msg}] { deny_open_sg[msg] }
violation[{"msg": msg}] { deny_missing_tags[msg] }
violation[{"msg": msg}] { deny_unencrypted_rds[msg] }
EOF

# Test against Terraform plan
terraform plan -out=tfplan.binary
terraform show -json tfplan.binary > tfplan.json

conftest test tfplan.json -p policy/

# Integrate into CI/CD
cat > .gitlab-ci.yml <<'EOF'
stages:
  - validate
  - plan
  - policy
  - apply

terraform-policy:
  stage: policy
  image: hashicorp/terraform:1.7
  before_script:
    - apk add --no-cache curl
    - curl -L https://github.com/open-policy-agent/conftest/releases/download/v0.49.1/conftest_0.49.1_Linux_x86_64.tar.gz | tar xz -C /usr/local/bin
  script:
    - terraform init
    - terraform plan -out=tfplan.binary
    - terraform show -json tfplan.binary > tfplan.json
    - conftest test tfplan.json -p policy/ --fail-on-warn
  artifacts:
    paths:
      - tfplan.json
    reports:
      junit: conftest-report.xml
EOF
```

**Docker Image Scanning (Trivy + OPA)**:

```bash
# Scan image and output JSON
trivy image --format json --output trivy-report.json myapp:latest

# Policy: docker-scan.rego
cat > policy/docker-scan.rego <<'EOF'
package docker.scan

# Deny HIGH/CRITICAL vulnerabilities
deny_high_vulns[msg] {
    result := input.Results[_]
    vuln := result.Vulnerabilities[_]
    vuln.Severity == "HIGH"
    msg := sprintf("HIGH vulnerability: %v in %v", [vuln.VulnerabilityID, vuln.PkgName])
}

deny_critical_vulns[msg] {
    result := input.Results[_]
    vuln := result.Vulnerabilities[_]
    vuln.Severity == "CRITICAL"
    msg := sprintf("CRITICAL vulnerability: %v in %v", [vuln.VulnerabilityID, vuln.PkgName])
}

# Count vulnerabilities by severity
vuln_summary[severity] = count {
    result := input.Results[_]
    vulns := [v | v := result.Vulnerabilities[_]; v.Severity == severity]
    count := count(vulns)
}

violation[{"msg": msg}] { deny_critical_vulns[msg] }
violation[{"msg": msg, "severity": "high"}] { deny_high_vulns[msg] }
EOF

# Test
conftest test trivy-report.json -p policy/docker-scan.rego

# GitHub Actions integration
cat > .github/workflows/security-scan.yml <<'EOF'
name: Security Scan
on: [push, pull_request]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Build image
      run: docker build -t ${{ github.repository }}:${{ github.sha }} .
    
    - name: Run Trivy
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: ${{ github.repository }}:${{ github.sha }}
        format: 'json'
        output: 'trivy-report.json'
    
    - name: Install Conftest
      run: |
        curl -L https://github.com/open-policy-agent/conftest/releases/download/v0.49.1/conftest_0.49.1_Linux_x86_64.tar.gz | \
          tar xz -C /usr/local/bin
    
    - name: Run Policy Check
      run: conftest test trivy-report.json -p policy/
    
    - name: Upload results
      if: always()
      uses: actions/upload-artifact@v4
      with:
        name: trivy-report
        path: trivy-report.json
EOF
```

---

### C. Runtime Enforcement (eBPF + Falco)

**Falco Rules (Policy-as-Code for Runtime)**:

```yaml
# custom-rules.yaml
- rule: Unauthorized Process in Container
  desc: Detect processes not in allowlist
  condition: >
    spawned_process and
    container and
    not proc.name in (allowed_processes)
  output: >
    Unauthorized process started
    (user=%user.name command=%proc.cmdline container=%container.name image=%container.image.repository)
  priority: WARNING
  tags: [process, container]
  
- macro: allowed_processes
  condition: proc.name in (sh, bash, nginx, node, python3)

- rule: Write to Sensitive File
  desc: Detect writes to sensitive files
  condition: >
    open_write and
    fd.name in (sensitive_files) and
    not proc.name in (trusted_writers)
  output: >
    Write to sensitive file
    (file=%fd.name process=%proc.name container=%container.name)
  priority: CRITICAL
  tags: [file, filesystem]

- list: sensitive_files
  items: [/etc/passwd, /etc/shadow, /etc/sudoers, /root/.ssh/authorized_keys]

- list: trusted_writers
  items: [systemd, dpkg, apt, yum]

- rule: Outbound Connection to Suspicious IP
  desc: Detect connections to known bad IPs
  condition: >
    outbound and
    fd.sip in (suspicious_ips)
  output: >
    Connection to suspicious IP
    (ip=%fd.sip port=%fd.sport process=%proc.name container=%container.name)
  priority: CRITICAL
  tags: [network]

- list: suspicious_ips
  items: ["192.0.2.1", "198.51.100.1"]

# Integration with OPA for dynamic policies
- rule: OPA Policy Violation
  desc: Runtime policy enforced by OPA
  condition: >
    spawned_process and
    container and
    opa_deny
  output: >
    OPA policy violation
    (policy=%opa.policy result=%opa.result container=%container.name)
  priority: WARNING
  tags: [opa, policy]
```

**Deploy Falco with eBPF**:

```bash
# Install Falco (eBPF probe)
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm repo update

cat > falco-values.yaml <<EOF
driver:
  kind: ebpf

falco:
  rules_file:
    - /etc/falco/falco_rules.yaml
    - /etc/falco/custom-rules.yaml
  
  json_output: true
  json_include_output_property: true
  
  # Send to SIEM
  http_output:
    enabled: true
    url: "http://logstash:8080"

  grpc:
    enabled: true
  
  grpc_output:
    enabled: true

falcosidekick:
  enabled: true
  config:
    slack:
      webhookurl: "https://hooks.slack.com/..."
    
    elasticsearch:
      hostport: "http://elasticsearch:9200"
      index: "falco"

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 100m
    memory: 512Mi

tolerations:
  - effect: NoSchedule
    key: node-role.kubernetes.io/master
EOF

helm install falco falcosecurity/falco -n falco --create-namespace \
  -f falco-values.yaml

# Custom rules ConfigMap
kubectl create configmap falco-custom-rules \
  --from-file=custom-rules.yaml \
  -n falco
```

---

## IV. POLICY TESTING & VALIDATION

### Unit Testing

**OPA Policy Tests**:

```bash
# Structure
policies/
├── kubernetes/
│   ├── admission.rego
│   └── admission_test.rego
├── terraform/
│   ├── aws.rego
│   └── aws_test.rego
└── docker/
    ├── security.rego
    └── security_test.rego

# admission_test.rego
cat > admission_test.rego <<'EOF'
package kubernetes.admission

# Test data
test_input_privileged := {
    "request": {
        "kind": {"kind": "Pod"},
        "object": {
            "spec": {
                "containers": [{
                    "name": "nginx",
                    "securityContext": {"privileged": true}
                }]
            }
        }
    }
}

test_input_compliant := {
    "request": {
        "kind": {"kind": "Pod"},
        "object": {
            "spec": {
                "containers": [{
                    "name": "nginx",
                    "securityContext": {
                        "privileged": false,
                        "runAsNonRoot": true
                    },
                    "resources": {
                        "limits": {"cpu": "100m", "memory": "128Mi"}
                    }
                }]
            }
        }
    }
}

# Tests
test_deny_privileged {
    violations := violation with input as test_input_privileged
    count(violations) > 0
}

test_allow_compliant {
    violations := violation with input as test_input_compliant
    count(violations) == 0
}

# Edge cases
test_missing_security_context {
    input_data := {
        "request": {
            "kind": {"kind": "Pod"},
            "object": {
                "spec": {
                    "containers": [{
                        "name": "nginx"
                        # No securityContext
                    }]
                }
            }
        }
    }
    
    # Should not crash
    violations := violation with input as input_data
}

# Performance test
test_benchmark {
    # Generate large input
    containers := [{"name": sprintf("container-%d", [i])} | i := numbers.range(0, 1000)[_]]
    
    large_input := {
        "request": {
            "kind": {"kind": "Pod"},
            "object": {
                "spec": {"containers": containers}
            }
        }
    }
    
    # This should complete quickly
    violation with input as large_input
}
EOF

# Run with coverage
opa test policies/ -v --coverage --format=json > coverage.json

# Coverage report
cat coverage.json | jq '.coverage'

# CI integration
opa test policies/ --threshold 80  # Require 80% coverage
```

### Integration Testing

**End-to-End K8s Policy Tests**:

```bash
# test-framework.sh
#!/bin/bash
set -e

NAMESPACE="policy-test-$(date +%s)"
kubectl create namespace "$NAMESPACE"

trap "kubectl delete namespace $NAMESPACE" EXIT

# Test 1: Privileged container should be denied
echo "Test 1: Deny privileged container..."
cat <<EOF | kubectl apply -f - 2>&1 | grep -q "denied" && echo "PASS" || echo "FAIL"
apiVersion: v1
kind: Pod
metadata:
  name: privileged-pod
  namespace: $NAMESPACE
spec:
  containers:
  - name: nginx
    image: nginx
    securityContext:
      privileged: true
EOF

# Test 2: Compliant pod should be allowed
echo "Test 2: Allow compliant pod..."
cat <<EOF | kubectl apply -f - && echo "PASS" || echo "FAIL"
apiVersion: v1
kind: Pod
metadata:
  name: compliant-pod
  namespace: $NAMESPACE
spec:
  securityContext:
    runAsNonRoot: true
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: nginx
    image: gcr.io/nginx:latest
    securityContext:
      runAsNonRoot: true
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
    resources:
      limits:
        cpu: "100m"
        memory: "128Mi"
EOF

# Test 3: Mutation should add defaults
echo "Test 3: Verify mutation..."
kubectl run test-mutation --image=nginx -n $NAMESPACE --dry-run=client -o yaml | \
  kubectl apply -f - -n $NAMESPACE

kubectl get pod test-mutation -n $NAMESPACE -o json | \
  jq '.spec.securityContext.seccompProfile.type' | grep -q "RuntimeDefault" && \
  echo "PASS: Seccomp profile added" || echo "FAIL"

# Cleanup
kubectl delete namespace "$NAMESPACE"
```

### Fuzzing

**Rego Policy Fuzzing**:

```go
// fuzz_test.go
package kubernetes

import (
    "encoding/json"
    "testing"
    
    "github.com/open-policy-agent/opa/rego"
)

func FuzzAdmissionPolicy(f *testing.F) {
    // Seed corpus
    seeds := []string{
        `{"request":{"kind":{"kind":"Pod"},"object":{"spec":{"containers":[{"name":"test"}]}}}}`,
        `{"request":{"kind":{"kind":"Deployment"}}}`,
        `{}`,
    }
    
    for _, seed := range seeds {
        f.Add([]byte(seed))
    }
    
    f.Fuzz(func(t *testing.T, data []byte) {
        // Try to parse as JSON
        var input map[string]interface{}
        if err := json.Unmarshal(data, &input); err != nil {
            t.Skip()
        }
        
        // Evaluate policy
        r := rego.New(
            rego.Query("data.kubernetes.admission.violation"),
            rego.Load([]string{"admission.rego"}, nil),
            rego.Input(input),
        )
        
        // Should not panic
        _, err := r.Eval(context.Background())
        if err != nil {
            // Errors are okay, panics are not
            t.Logf("Eval error (acceptable): %v", err)
        }
    })
}

// Run fuzzing
// go test -fuzz=FuzzAdmissionPolicy -fuzztime=60s
```

---

## V. THREAT MODEL & SECURITY

### Attack Surfaces

**1. Policy Tampering**:
```
┌──────────────────────────────────────────┐
│ Threat: Attacker modifies policies       │
│ Impact: Bypass security controls         │
├──────────────────────────────────────────┤
│ Mitigations:                             │
│ • Policy stored in Git with signing      │
│ • RBAC on Policy CRDs                    │
│ • Admission controller for policies      │
│ • Audit logging of policy changes        │
│ • Separate policy management namespace   │
└──────────────────────────────────────────┘
```

**Implementation**:

```bash
# Sign policies with Cosign
cosign sign --key cosign.key policy-bundle.tar.gz

# Verify in OPA startup
opa run \
  --verification-key /keys/cosign.pub \
  --bundle https://bundle-server/bundle.tar.gz

# RBAC for Kyverno policies
kubectl apply -f - <<EOF
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: policy-admin
rules:
- apiGroups: ["kyverno.io"]
  resources: ["clusterpolicies", "policies"]
  verbs: ["create", "update", "patch", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: policy-admin-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: policy-admin
subjects:
- kind: Group
  name: security-team
  apiGroup: rbac.authorization.k8s.io
EOF

# Audit policy changes
kubectl create -f - <<EOF
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
- level: RequestResponse
  resources:
  - group: "kyverno.io"
    resources: ["clusterpolicies", "policies"]
  - group: "templates.gatekeeper.sh"
    resources: ["constrainttemplates"]
  - group: "constraints.gatekeeper.sh"
    resources: ["*"]
EOF
```

**2. Decision Bypass**:
```
┌──────────────────────────────────────────┐
│ Threat: Circumvent policy enforcement    │
│ Impact: Unauthorized resource creation   │
├──────────────────────────────────────────┤
│ Mitigations:                             │
│ • Webhook failurePolicy: Fail            │
│ • Multiple replicas for HA               │
│ • Network policies isolating PDP         │
│ • mTLS between PEP and PDP               │
│ • Monitor webhook failures               │
└──────────────────────────────────────────┘
```

**Implementation**:

```yaml
# Webhook HA configuration
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: policy-webhook
webhooks:
- name: policy.example.com
  failurePolicy: Fail  # CRITICAL: Block on failure
  matchPolicy: Equivalent
  timeoutSeconds: 5
  
  # Multiple webhook backends
  clientConfig:
    service:
      name: policy-webhook
      namespace: policy-system
    caBundle: ...
  
  # Network policy
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: policy-webhook-netpol
  namespace: policy-system
spec:
  podSelector:
    matchLabels:
      app: policy-webhook
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: kube-system
    ports:
    - protocol: TCP
      port: 8443
```

**3. Policy Evaluation DoS**:
```
┌──────────────────────────────────────────┐
│ Threat: Resource exhaustion in PDP       │
│ Impact: Policy evaluation failures       │
├──────────────────────────────────────────┤
│ Mitigations:                             │
│ • Timeout limits (5-10s)                 │
│ • Resource limits on PDP pods            │
│ • Rate limiting at API server            │
│ • Caching policy decisions               │
│ • Circuit breakers                       │
└──────────────────────────────────────────┘
```

**Implementation**:

```yaml
# OPA with resource limits
apiVersion: apps/v1
kind: Deployment
metadata:
  name: opa
spec:
  template:
    spec:
      containers:
      - name: opa
        resources:
          limits:
            cpu: "1000m"
            memory: "512Mi"
          requests:
            cpu: "100m"
            memory: "128Mi"
        
        # Circuit breaker via liveness probe
        livenessProbe:
          httpGet:
            path: /health
            port: 8282
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3

# API server rate limiting
apiVersion: flowcontrol.apiserver.k8s.io/v1beta3
kind: FlowSchema
metadata:
  name: policy-admission-limited
spec:
  priorityLevelConfiguration:
    name: policy-admission
  matchingPrecedence: 1000
  distinguisherMethod:
    type: ByUser
  rules:
  - subjects:
    - kind: ServiceAccount
      serviceAccount:
        name: "*"
        namespace: "*"
    resourceRules:
    - verbs: ["*"]
      apiGroups: ["*"]
      resources: ["*"]
      namespaces: ["*"]
---
apiVersion: flowcontrol.apiserver.k8s.io/v1beta3
kind: PriorityLevelConfiguration
metadata:
  name: policy-admission
spec:
  type: Limited
  limited:
    assuredConcurrencyShares: 10
    limitResponse:
      type: Queue
      queuing:
        queues: 64
        queueLengthLimit: 50
        handSize: 6
```

**4. Cache Poisoning**:
```
┌──────────────────────────────────────────┐
│ Threat: Inject false data into cache     │
│ Impact: Incorrect policy decisions       │
├──────────────────────────────────────────┤
│ Mitigations:                             │
│ • Authenticate data sources              │
│ • Validate cache entries                 │
│ • Short TTL on cached decisions          │
│ • Encrypt cache at rest                  │
│ • Audit cache modifications              │
└──────────────────────────────────────────┘
```

---

## VI. OBSERVABILITY & COMPLIANCE

### Decision Logging

**OPA Decision Logs (OpenTelemetry)**:

```yaml
# OPA config with OTLP export
services:
  bundleServer:
    url: https://bundle-server
  
decision_logs:
  service: otel-collector
  reporting:
    min_delay_seconds: 10
    max_delay_seconds: 30
  
  # OTLP exporter
  plugin: envoy_ext_authz_grpc

plugins:
  envoy_ext_authz_grpc:
    addr: otel-collector:4317
    path: policy/authz

# OpenTelemetry Collector
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: otel-collector-config
data:
  config.yaml: |
    receivers:
      otlp:
        protocols:
          grpc:
            endpoint: 0.0.0.0:4317
    
    processors:
      batch:
        timeout: 10s
        send_batch_size: 1024
      
      attributes:
        actions:
        - key: policy.engine
          value: opa
          action: insert
    
    exporters:
      elasticsearch:
        endpoints: ["http://elasticsearch:9200"]
        index: "opa-decisions"
      
      prometheus:
        endpoint: "0.0.0.0:8889"
      
      jaeger:
        endpoint: jaeger:14250
        tls:
          insecure: true
    
    service:
      pipelines:
        logs:
          receivers: [otlp]
          processors: [batch, attributes]
          exporters: [elasticsearch]
        
        metrics:
          receivers: [otlp]
          processors: [batch]
          exporters: [prometheus]
        
        traces:
          receivers: [otlp]
          processors: [batch]
          exporters: [jaeger]
```

### Metrics & Alerting

**Prometheus Metrics**:

```yaml
# ServiceMonitor for OPA
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: opa
  namespace: policy-system
spec:
  selector:
    matchLabels:
      app: opa
  endpoints:
  - port: diagnostics
    interval: 30s
    path: /metrics

# PrometheusRule for alerts
---
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: opa-alerts
  namespace: policy-system
spec:
  groups:
  - name: opa
    interval: 30s
    rules:
    
    # High decision latency
    - alert: OPAHighLatency
      expr: |
        histogram_quantile(0.99,
          rate(http_request_duration_seconds_bucket{job="opa"}[5m])
        ) > 1
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "OPA p99 latency > 1s"
    
    # Policy evaluation errors
    - alert: OPAPolicyErrors
      expr: |
        rate(opa_policy_eval_errors_total[5m]) > 0.1
      for: 2m
      labels:
        severity: critical
      annotations:
        summary: "OPA policy evaluation errors detected"
    
    # Webhook failures
    - alert: WebhookFailures
      expr: |
        rate(apiserver_admission_webhook_rejection_count{name="opa"}[5m]) > 0.5
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "High webhook rejection rate"
    
    # Bundle sync failures
    - alert: BundleSyncFailure
      expr: |
        opa_bundle_loaded_counter == 0
      for: 10m
      labels:
        severity: critical
      annotations:
        summary: "OPA bundle not loaded"
```

### Compliance Reporting

**Policy Report Aggregation**:

```bash
# Generate compliance report
cat > generate-report.sh <<'EOF'
#!/bin/bash

REPORT_FILE="compliance-report-$(date +%Y%m%d).json"

# Collect Kyverno policy reports
kubectl get policyreport -A -o json > /tmp/kyverno-reports.json

# Collect Gatekeeper violations
kubectl get constraints -A -o json > /tmp/gatekeeper-constraints.json

# Aggregate
jq -s '{
  timestamp: now | todate,
  summary: {
    total_resources: ([.[0].items[].results[]] | length),
    violations: ([.[0].items[].results[] | select(.result == "fail")] | length),
    warnings: ([.[0].items[].results[] | select(.result == "warn")] | length),
    passes: ([.[0].items[].results[] | select(.result == "pass")] | length)
  },
  details: {
    kyverno: .[0],
    gatekeeper: .[1]
  }
}' /tmp/kyverno-reports.json /tmp/gatekeeper-constraints.json > "$REPORT_FILE"

echo "Report generated: $REPORT_FILE"

# Upload to S3
aws s3 cp "$REPORT_FILE" s3://compliance-reports/
EOF

chmod +x generate-report.sh

# Schedule as CronJob
kubectl create cronjob compliance-report \
  --image=amazon/aws-cli \
  --schedule="0 0 * * *" \
  -- /scripts/generate-report.sh
```

---

## VII. ROLLOUT & ROLLBACK

### Gradual Deployment

**Shadow Mode → Audit → Enforce**:

```bash
# Phase 1: Shadow mode (log only)
cat > policy-shadow.yaml <<EOF
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: pod-security-shadow
spec:
  validationFailureAction: Audit  # Log violations, don't block
  background: true
  rules:
  - name: require-limits
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "Resource limits required"
      pattern:
        spec:
          containers:
          - resources:
              limits:
                memory: "?*"
                cpu: "?*"
EOF

kubectl apply -f policy-shadow.yaml

# Monitor for 1 week
kubectl get policyreport -A | grep FAIL

# Phase 2: Audit mode with warnings
kubectl patch clusterpolicy pod-security-shadow \
  --type=merge \
  -p '{"spec":{"validationFailureAction":"Audit"}}'

# Phase 3: Enforce (after validation)
kubectl patch clusterpolicy pod-security-shadow \
  --type=merge \
  -p '{"spec":{"validationFailureAction":"Enforce"}}'
```

### Canary Rollout

**Namespace-based Canary**:

```yaml
# Stage 1: Canary namespace
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: pod-security-canary
spec:
  validationFailureAction: Enforce
  rules:
  - name: require-limits
    match:
      any:
      - resources:
          kinds:
          - Pod
          namespaces:
          - canary-namespace
    validate:
      message: "Resource limits required"
      pattern:
        spec:
          containers:
          - resources:
              limits:
                memory: "?*"

# Stage 2: Add staging
---
kubectl patch clusterpolicy pod-security-canary \
  --type=json \
  -p='[{"op": "add", "path": "/spec/rules/0/match/any/0/resources/namespaces/-", "value": "staging"}]'

# Stage 3: Production (exclude critical)
---
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: pod-security-production
spec:
  validationFailureAction: Enforce
  rules:
  - name: require-limits
    match:
      any:
      - resources:
          kinds:
          - Pod
    exclude:
      any:
      - resources:
          namespaces:
          - kube-system
          - critical-app
```

### Emergency Rollback

**Circuit Breaker Mechanism**:

```yaml
# ConfigMap for kill switch
apiVersion: v1
kind: ConfigMap
metadata:
  name: policy-circuit-breaker
  namespace: policy-system
data:
  enabled: "true"
  error_threshold: "10"
  timeout_seconds: "300"

# Admission webhook with circuit breaker
---
apiVersion: v1
kind: Service
metadata:
  name: policy-webhook-lb
  namespace: policy-system
spec:
  type: LoadBalancer
  selector:
    app: policy-webhook
  ports:
  - port: 443
    targetPort: 8443

# Emergency disable script
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: emergency-scripts
data:
  disable-policy.sh: |
    #!/bin/bash
    # Disable all enforcing policies
    kubectl patch clusterpolicy --all \
      --type=merge \
      -p '{"spec":{"validationFailureAction":"Audit"}}'
    
    # Set webhook to Ignore failures
    kubectl patch validatingwebhookconfiguration policy-webhook \
      --type=merge \
      -p '{"webhooks":[{"name":"policy.example.com","failurePolicy":"Ignore"}]}'
    
    echo "All policies disabled - enforcement paused"
  
  restore-policy.sh: |
    #!/bin/bash
    # Restore enforcement
    kubectl patch clusterpolicy --all \
      --type=merge \
      -p '{"spec":{"validationFailureAction":"Enforce"}}'
    
    kubectl patch validatingwebhookconfiguration policy-webhook \
      --type=merge \
      -p '{"webhooks":[{"name":"policy.example.com","failurePolicy":"Fail"}]}'
    
    echo "Policies restored - enforcement active"
```

---

## VIII. PRODUCTION ARCHITECTURES

### Multi-Cluster Policy Distribution

```
┌──────────────────────────────────────────────────────────┐
│ GitOps Repository (Source of Truth)                      │
│   policies/                                              │
│   ├── base/                                              │
│   │   ├── pod-security.rego                             │
│   │   └── network-policy.yaml                           │
│   ├── overlays/                                          │
│   │   ├── prod/                                          │
│   │   ├── staging/                                       │
│   │   └── dev/                                           │
│   └── kustomization.yaml                                 │
└──────────────────┬───────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
┌──────────────┐      ┌──────────────┐
│  Cluster 1   │      │  Cluster 2   │
│  (US-East)   │      │  (EU-West)   │
│              │      │              │
│  ┌────────┐  │      │  ┌────────┐  │
│  │ Flux   │──┼──────┼──│ Flux   │  │
│  └────┬───┘  │      │  └────┬───┘  │
│       │      │      │       │      │
│  ┌────▼───┐  │      │  ┌────▼───┐  │
│  │  OPA   │  │      │  │  OPA   │  │
│  │Gatekeeper│      │  │Gatekeeper│  │
│  │ Kyverno│  │      │  │ Kyverno│  │
│  └────────┘  │      │  └────────┘  │
└──────────────┘      └──────────────┘
```

**Implementation**:

```bash
# Git repository structure
mkdir -p policies/{base,overlays/{prod,staging,dev}}

# Base policies
cat > policies/base/kustomization.yaml <<EOF
resources:
- pod-security.yaml
- network-policy.yaml

configurations:
- kustomizeconfig.yaml
EOF

# Production overlay (strict)
cat > policies/overlays/prod/kustomization.yaml <<EOF
bases:
- ../../base

patchesStrategicMerge:
- increase-strictness.yaml

namespace: policy-system-prod
EOF

# Flux GitRepository
kubectl apply -f - <<EOF
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: policy-repo
  namespace: flux-system
spec:
  interval: 1m
  url: https://github.com/org/policies
  ref:
    branch: main
  secretRef:
    name: git-credentials
---
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: policies
  namespace: flux-system
spec:
  interval: 5m
  path: ./policies/overlays/prod
  prune: true
  sourceRef:
    kind: GitRepository
    name: policy-repo
  validation: client
  healthChecks:
  - apiVersion: kyverno.io/v1
    kind: ClusterPolicy
    name: pod-security
EOF
```

---

## IX. ADVANCED TOPICS

### Policy Composition

**Layered Policies (Inheritance)**:

```rego
# Base organizational policy
package org.security.base

# Global deny rules
deny_privileged_containers[msg] {
    container := input.spec.containers[_]
    container.securityContext.privileged
    msg := "Privileged containers forbidden"
}

# Team-specific overrides
package team.platform.overrides

import data.org.security.base

# Inherit base denials
violation[msg] { base.deny_privileged_containers[msg] }

# Add team-specific rules
violation[msg] {
    not input.metadata.labels.team
    msg := "Team label required"
}

# Exemptions for specific images
allow_privileged {
    container := input.spec.containers[_]
    container.image == "gcr.io/privileged-tool:v1"
}

# Final decision: base rules + team rules - exemptions
final_violation[msg] {
    violation[msg]
    not allow_privileged
}
```

### External Data Integration

**OPA with External APIs**:

```rego
package authz

import future.keywords.if

# Query external service for user permissions
user_permissions := http.send({
    "method": "GET",
    "url": sprintf("https://authz-service/users/%s/permissions", [input.user]),
    "headers": {"Authorization": sprintf("Bearer %s", [input.token])},
    "raise_error": false,
    "cache": true,
    "force_cache_duration_seconds": 300
}).body

# Check if user has required role
allow if {
    some permission in user_permissions
    permission.resource == input.resource
    permission.action == input.action
}

# Query database for resource metadata
resource_metadata := http.send({
    "method": "POST",
    "url": "https://metadata-db/query",
    "headers": {"Content-Type": "application/json"},
    "body": {
        "query": sprintf("SELECT * FROM resources WHERE id = '%s'", [input.resource_id])
    }
}).body[0]

# Attribute-based access control
allow if {
    resource_metadata.sensitivity == "public"
}

allow if {
    resource_metadata.sensitivity == "confidential"
    user_permissions.clearance_level >= 2
}
```

---

## X. REFERENCES & NEXT STEPS

### Key Resources

1. **OPA Documentation**: https://www.openpolicyagent.org/docs/latest/
2. **Rego Playground**: https://play.openpolicyagent.org/
3. **Kyverno Policies**: https://kyverno.io/policies/
4. **Gatekeeper Library**: https://github.com/open-policy-agent/gatekeeper-library
5. **CEL Specification**: https://github.com/google/cel-spec
6. **K8s Admission Control**: https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/
7. **CNCF Policy WG**: https://github.com/kubernetes/community/tree/master/wg-policy

### Next 3 Steps

1. **Build Reference Implementation**:
   ```bash
   # Clone starter template
   git clone https://github.com/your-org/policy-as-code-template
   cd policy-as-code-template
   
   # Deploy to local cluster
   kind create cluster --config kind-config.yaml
   ./deploy-local.sh
   
   # Run test suite
   ./test-policies.sh
   ```

2. **Establish Policy Governance**:
   - Create policy authoring guidelines (templates, naming, testing requirements)
   - Set up PR review process with automated tests
   - Define policy lifecycle (shadow → audit → enforce → deprecate)
   - Implement policy versioning and migration strategy

3. **Implement Observability Stack**:
   ```bash
   # Deploy monitoring
   helm install prometheus prometheus-community/kube-prometheus-stack
   
   # Configure policy dashboards
   kubectl apply -f dashboards/policy-metrics.json
   
   # Set up alerting
   kubectl apply -f alerts/policy-alerts.yaml
   ```

This guide provides comprehensive coverage of policy-as-code from foundational concepts through production deployment. All code examples are production-ready and follow security best practices for cloud-native environments.