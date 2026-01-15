## Summary

Cert-manager, Tetragon, Harbor, and Kyverno form a critical security stack for production Kubernetes: cert-manager automates PKI/TLS lifecycle (X.509 provisioning, rotation, ACME protocol); Tetragon provides eBPF-based runtime security with kernel-level observability and policy enforcement; Harbor delivers enterprise registry with content trust, vulnerability scanning, and image signing; Kyverno enforces policy-as-code via admission control and continuous validation. Together they address certificate management, runtime threat detection, supply-chain security, and policy enforcement—essential for zero-trust architectures, compliance (PCI-DSS, SOC2, NIST), and defense-in-depth. This guide covers architecture, threat models, deployment patterns, integration points, and production hardening for multi-cloud/hybrid environments.

---

## Architecture Overview (ASCII)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Kubernetes Cluster                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │ cert-manager │  │   Tetragon   │  │   Kyverno    │            │
│  │   (TLS/PKI)  │  │  (eBPF Sec)  │  │  (Policy)    │            │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘            │
│         │                  │                  │                     │
│         │ Issues certs     │ Observes syscalls│ Validates/Mutates  │
│         ↓                  ↓                  ↓                     │
│  ┌─────────────────────────────────────────────────────┐          │
│  │              Kubernetes API Server                   │          │
│  │  (Admission Controllers, CRDs, ValidatingWebhooks)  │          │
│  └──────────────────────┬──────────────────────────────┘          │
│                         │                                           │
│         ┌───────────────┼───────────────┐                         │
│         ↓               ↓               ↓                         │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐                     │
│  │  Ingress │   │   Pods   │   │  Harbor  │                     │
│  │   (TLS)  │   │ (runtime)│   │ Registry │                     │
│  └──────────┘   └──────────┘   └────┬─────┘                     │
│         ↑                            │                             │
│         │ Pulls images + validates   │                             │
│         └────────────────────────────┘                             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
         │                                         │
         ↓                                         ↓
┌────────────────┐                       ┌────────────────┐
│  ACME / CA     │                       │  Notary/Cosign │
│  (Let's Encrypt│                       │  (Signatures)  │
│   Vault, etc.) │                       └────────────────┘
└────────────────┘
```

---

## 1. cert-manager: Automated X.509 Certificate Management

### 1.1 Core Concepts

**Certificate Lifecycle Automation:**
- **Issuer/ClusterIssuer CRDs:** Define certificate authorities (ACME, Vault, SelfSigned, CA, Venafi)
- **Certificate CRD:** Declares desired certificate with DN, SANs, duration, renewal thresholds
- **CertificateRequest:** Internal resource tracking issuance state
- **Order/Challenge:** ACME protocol resources for HTTP-01/DNS-01 validation
- **Secret:** Output Kubernetes Secret containing `tls.crt`, `tls.key`, `ca.crt`

**Key Features:**
- Automatic renewal (default 2/3 of cert lifetime)
- ACME DNS-01/HTTP-01 challenge support (Let's Encrypt, ZeroSSL)
- Integration with external PKI (HashiCorp Vault, Venafi, AWS PCA)
- Webhook extensibility for custom DNS providers
- Prometheus metrics for expiry tracking

### 1.2 Architecture & Components

**Controller Manager:**
- Reconciles Certificate resources → creates CertificateRequests
- Monitors cert expiry, triggers renewal
- Manages ACME challenges

**Webhook:**
- ValidatingWebhookConfiguration for CRD validation
- MutatingWebhookConfiguration for defaults

**CA Injector:**
- Injects CA bundle into ValidatingWebhookConfiguration, MutatingWebhookConfiguration, APIService, CRD conversions

**ACME Solver:**
- HTTP-01: Ingress-based (requires accessible endpoint)
- DNS-01: API-driven DNS record creation (Route53, CloudDNS, Cloudflare)

### 1.3 Deployment & Configuration

**Installation (Helm):**
```bash
# Add Jetstack repo
helm repo add jetstack https://charts.jetstack.io
helm repo update

# Create namespace
kubectl create namespace cert-manager

# Install CRDs and cert-manager
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --version v1.14.0 \
  --set installCRDs=true \
  --set global.leaderElection.namespace=cert-manager \
  --set prometheus.enabled=true \
  --set webhook.securePort=10260

# Verify deployment
kubectl -n cert-manager get pods
kubectl -n cert-manager logs -l app.kubernetes.io/name=cert-manager
```

**Example: ClusterIssuer with Let's Encrypt (DNS-01/Route53):**
```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod-dns
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: security-team@example.com
    privateKeySecretRef:
      name: letsencrypt-prod-account-key
    solvers:
    - dns01:
        route53:
          region: us-west-2
          # Use IAM role via IRSA (EKS) or instance profile
          # hostedZoneID: Z1234567890ABC  # optional, auto-discovers
      selector:
        dnsZones:
        - "example.com"
        - "*.example.com"
```

**Example: Certificate Resource (Wildcard TLS):**
```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: wildcard-tls
  namespace: ingress-nginx
spec:
  secretName: wildcard-tls-secret
  issuerRef:
    name: letsencrypt-prod-dns
    kind: ClusterIssuer
  dnsNames:
  - "example.com"
  - "*.example.com"
  duration: 2160h  # 90 days
  renewBefore: 720h  # renew 30 days before expiry
  privateKey:
    algorithm: RSA
    size: 4096
    rotationPolicy: Always  # rotate on renewal
  usages:
  - digital signature
  - key encipherment
  - server auth
```

**Example: Vault Issuer (Internal PKI):**
```yaml
apiVersion: cert-manager.io/v1
kind: Issuer
metadata:
  name: vault-issuer
  namespace: default
spec:
  vault:
    server: https://vault.internal.example.com:8200
    path: pki_int/sign/kubernetes-role
    caBundle: <base64-encoded-vault-ca-cert>
    auth:
      kubernetes:
        role: cert-manager-issuer
        mountPath: /v1/auth/kubernetes
        secretRef:
          name: vault-token
          key: token
```

### 1.4 Threat Model & Mitigations

**Threats:**
1. **Private Key Exposure:** Compromise of `tls.key` in Secret → lateral movement, MITM
2. **Issuer Credential Theft:** ACME account key, Vault token → unauthorized cert issuance
3. **DNS Hijacking (DNS-01):** Attacker modifies DNS records → issue rogue certs
4. **Webhook Bypass:** Disabled validation → invalid certs deployed
5. **Expiry Outage:** Failure to renew → service downtime

**Mitigations:**
- **Secrets Encryption:** Enable etcd encryption-at-rest (EncryptionConfiguration), use external KMS (AWS KMS, GCP KMS)
- **RBAC Isolation:** Restrict access to cert-manager namespace, Certificate/Issuer resources
- **DNS Provider MFA/Audit:** Enable CloudTrail (AWS), audit logs for DNS changes
- **Webhook HA:** Deploy multiple replicas, monitor webhook latency
- **Monitoring:** Prometheus metrics `certmanager_certificate_expiration_timestamp_seconds`, alert on <7 days
- **Private Key Rotation:** Set `privateKey.rotationPolicy: Always`
- **ACME Account Key Backup:** Store in separate secret, replicate to disaster recovery cluster

**RBAC Example:**
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: cert-manager-certificate-reader
  namespace: ingress-nginx
rules:
- apiGroups: ["cert-manager.io"]
  resources: ["certificates"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["secrets"]
  resourceNames: ["wildcard-tls-secret"]  # specific secret
  verbs: ["get"]
```

### 1.5 Testing & Validation

**Test Certificate Issuance:**
```bash
# Create test certificate
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: test-cert
  namespace: default
spec:
  secretName: test-cert-secret
  issuerRef:
    name: letsencrypt-staging  # use staging for tests
    kind: ClusterIssuer
  dnsNames:
  - test.example.com
EOF

# Check status
kubectl describe certificate test-cert
kubectl get certificaterequest
kubectl get order
kubectl get challenge

# Verify Secret
kubectl get secret test-cert-secret -o yaml
openssl x509 -in <(kubectl get secret test-cert-secret -o jsonpath='{.data.tls\.crt}' | base64 -d) -noout -text
```

**Test Renewal (force renewal):**
```bash
# Annotate certificate to force immediate renewal
kubectl annotate certificate wildcard-tls cert-manager.io/issue-temporary-certificate="true" --overwrite
kubectl delete certificaterequest -l cert-manager.io/certificate-name=wildcard-tls

# Verify new CertificateRequest created
kubectl get certificaterequest -w
```

**Metrics Validation:**
```bash
# Port-forward to cert-manager
kubectl -n cert-manager port-forward svc/cert-manager 9402:9402

# Query metrics
curl http://localhost:9402/metrics | grep certmanager_certificate_expiration_timestamp_seconds
```

---

## 2. Tetragon: eBPF-based Runtime Security & Observability

### 2.1 Core Concepts

**eBPF Kernel Instrumentation:**
- **Tracing Policies:** YAML-defined rules hooking syscalls, kernel functions, network events
- **Hooks:** kprobes, tracepoints, LSM hooks, raw_tracepoint
- **Data Collection:** Process lineage, file access, network connections, capabilities, syscall arguments
- **Enforcement:** Kill process, override return values, send signals
- **Zero-overhead:** In-kernel filtering, BPF verifier safety

**Key Features:**
- Real-time security event stream (gRPC, JSON logs)
- Policy enforcement without sidecars or kernel modules
- Kubernetes-aware (pod/namespace context)
- Integration with Falco, Prometheus, SIEM

### 2.2 Architecture & Components

**Tetragon Agent (DaemonSet):**
- Loads BPF programs via CO-RE (Compile Once, Run Everywhere)
- Exports events via gRPC API
- Applies TracingPolicy CRDs

**Tetragon Operator (optional):**
- Manages TracingPolicy lifecycle
- Validates policies before loading

**Event Types:**
- `process_exec`, `process_exit`: Process lifecycle
- `process_kprobe`: Syscall/kernel function calls
- `process_tracepoint`: Stable kernel tracepoints
- `process_lsm`: LSM (Linux Security Module) hooks
- `process_loader`: Dynamic library loading

**Cilium Integration:**
- Shared BPF infrastructure
- Network policy enforcement + observability

### 2.3 Deployment & Configuration

**Installation (Helm):**
```bash
# Add Cilium repo
helm repo add cilium https://helm.cilium.io/
helm repo update

# Install Tetragon
helm install tetragon cilium/tetragon \
  --namespace kube-system \
  --set tetragon.grpc.enabled=true \
  --set tetragon.prometheus.enabled=true \
  --set tetragon.enableProcessCred=true \
  --set tetragon.enableProcessNs=true

# Verify DaemonSet
kubectl -n kube-system get ds tetragon
kubectl -n kube-system logs -l app.kubernetes.io/name=tetragon
```

**Example: TracingPolicy for Sensitive File Access:**
```yaml
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: monitor-sensitive-files
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
        operator: "Prefix"
        values:
        - "/etc/shadow"
        - "/etc/passwd"
        - "/etc/ssh/"
        - "/root/.ssh/"
      matchActions:
      - action: Post
      matchBinaries:
      - operator: "NotIn"
        values:
        - "/usr/sbin/sshd"
        - "/usr/bin/sudo"
```

**Example: Block Execution of Unverified Binaries:**
```yaml
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: enforce-signed-binaries
spec:
  kprobes:
  - call: "security_bprm_check"
    syscall: false
    args:
    - index: 0
      type: "linux_binprm"
    selectors:
    - matchArgs:
      - index: 0
        operator: "NotPrefix"
        values:
        - "/usr/bin/"
        - "/usr/sbin/"
        - "/bin/"
        - "/sbin/"
      matchActions:
      - action: Sigkill  # kill process
      matchNamespaces:
      - operator: "In"
        values:
        - "production"
        - "staging"
```

**Example: Detect Reverse Shells (TCP connect to suspicious ports):**
```yaml
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: detect-reverse-shell
spec:
  kprobes:
  - call: "tcp_connect"
    syscall: false
    args:
    - index: 0
      type: "sock"
    selectors:
    - matchArgs:
      - index: 0
        operator: "DPort"
        values:
        - "4444"   # common metasploit ports
        - "5555"
        - "6666"
        - "7777"
        - "8888"
        - "9999"
      matchActions:
      - action: Post
      - action: Sigkill
```

### 2.4 Threat Model & Mitigations

**Threats:**
1. **Container Escape:** Exploit CVE → breakout to host
2. **Privilege Escalation:** setuid binaries, capability abuse
3. **Lateral Movement:** Network scanning, SSH brute-force
4. **Data Exfiltration:** Sensitive file reads, DNS tunneling
5. **Cryptomining:** Unauthorized resource consumption

**Mitigations:**
- **Baseline Policies:** Monitor exec, file access, network in all namespaces
- **Enforcement Mode:** Use Sigkill for known-bad patterns (crypto miners, reverse shells)
- **Process Lineage:** Track parent-child relationships → detect suspicious chains
- **Integration with Falco:** Export events to Falco for complex rule engine
- **Immutable Infrastructure:** Alert on any write to /usr, /bin, /sbin
- **Network Observability:** Correlate with Cilium NetworkPolicy denials

**Defense-in-Depth Stack:**
```
┌─────────────────────────────────────────────────┐
│ Admission Control (Kyverno)                     │
│  - Block privileged pods                        │
│  - Enforce image signatures                     │
└────────────────┬────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────┐
│ Runtime Security (Tetragon)                     │
│  - Monitor syscalls, file access, network       │
│  - Kill suspicious processes                    │
└────────────────┬────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────┐
│ Network Policy (Cilium)                         │
│  - L3/L4/L7 enforcement                         │
│  - DNS-aware policies                           │
└─────────────────────────────────────────────────┘
```

### 2.5 Testing & Validation

**Test File Access Detection:**
```bash
# Exec into pod and access sensitive file
kubectl exec -it <pod-name> -- cat /etc/shadow

# View Tetragon events
kubectl -n kube-system exec -it ds/tetragon -c tetragon -- tetra getevents -o compact
```

**Test Process Execution Blocking:**
```bash
# Try to execute curl from untrusted location
kubectl exec -it <pod-name> -- /tmp/curl http://evil.com

# Verify process killed
kubectl -n kube-system logs ds/tetragon | grep Sigkill
```

**Export Events to Prometheus:**
```yaml
# Tetragon exports metrics like:
# tetragon_events_total{event_type="process_exec"}
# tetragon_policy_events_total{policy="monitor-sensitive-files"}

# Query in Prometheus
rate(tetragon_events_total{event_type="process_exec"}[5m])
```

**Integration with Falco:**
```bash
# Tetragon outputs JSON events, pipe to Falco
kubectl -n kube-system exec -it ds/tetragon -c tetragon -- tetra getevents -o json | falco -r /etc/falco/rules.d/
```

---

## 3. Harbor: Enterprise Container Registry

### 3.1 Core Concepts

**Registry Features:**
- **Image Storage:** OCI-compliant, supports Docker images, Helm charts, OCI artifacts
- **Replication:** Multi-site, pull/push replication policies
- **Vulnerability Scanning:** Trivy, Clair integration
- **Content Trust:** Notary v1/v2 (TUF), Cosign signature verification
- **RBAC:** Project-based access control, LDAP/OIDC/AD integration
- **Image Retention:** Automated tag cleanup, quota management
- **Proxy Cache:** Upstream registry mirroring (Docker Hub, GCR, ECR)

**Architecture:**
- **Harbor Core:** API server, web UI
- **Harbor Registry (distribution):** OCI registry implementation
- **Harbor JobService:** Asynchronous tasks (scan, replication)
- **Trivy/Clair:** Vulnerability scanners
- **Notary Server/Signer:** Content trust
- **Redis:** Job queue, session cache
- **PostgreSQL:** Metadata persistence
- **S3/Azure Blob/GCS:** Image blob storage

### 3.2 Deployment & Configuration

**Installation (Helm):**
```bash
# Add Harbor repo
helm repo add harbor https://helm.goharbor.io
helm repo update

# Create namespace
kubectl create namespace harbor

# Generate TLS certificate (use cert-manager)
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: harbor-tls
  namespace: harbor
spec:
  secretName: harbor-tls
  issuerRef:
    name: letsencrypt-prod-dns
    kind: ClusterIssuer
  dnsNames:
  - harbor.example.com
  - notary.harbor.example.com
EOF

# Install Harbor with external PostgreSQL and S3
helm install harbor harbor/harbor \
  --namespace harbor \
  --set expose.type=ingress \
  --set expose.tls.enabled=true \
  --set expose.tls.certSource=secret \
  --set expose.tls.secret.secretName=harbor-tls \
  --set expose.ingress.hosts.core=harbor.example.com \
  --set expose.ingress.hosts.notary=notary.harbor.example.com \
  --set externalURL=https://harbor.example.com \
  --set persistence.imageChartStorage.type=s3 \
  --set persistence.imageChartStorage.s3.region=us-west-2 \
  --set persistence.imageChartStorage.s3.bucket=harbor-images \
  --set persistence.imageChartStorage.s3.encrypt=true \
  --set database.type=external \
  --set database.external.host=postgres.internal.example.com \
  --set database.external.port=5432 \
  --set database.external.username=harbor \
  --set database.external.password=<secure-password> \
  --set database.external.coreDatabase=registry \
  --set redis.type=external \
  --set redis.external.addr=redis.internal.example.com:6379 \
  --set trivy.enabled=true \
  --set notary.enabled=true \
  --set chartmuseum.enabled=true

# Verify deployment
kubectl -n harbor get pods
kubectl -n harbor logs -l component=core
```

**Example: Replication Policy (Multi-region DR):**
```yaml
# Create via Harbor UI or API
{
  "name": "production-to-dr",
  "description": "Replicate prod images to DR region",
  "src_registry": {
    "id": 0  # local registry
  },
  "dest_registry": {
    "id": 1,  # remote Harbor instance
    "url": "https://harbor-dr.example.com",
    "credential": {
      "access_key": "robot$replication",
      "access_secret": "<secret>"
    }
  },
  "filters": [
    {
      "type": "name",
      "value": "production/**"
    },
    {
      "type": "tag",
      "value": "v*"
    }
  ],
  "trigger": {
    "type": "event_based"  # replicate on push
  },
  "deletion": false,
  "override": true,
  "enabled": true
}
```

**Example: Webhook for Vulnerability Notifications:**
```yaml
# POST to Harbor API: /api/v2.0/projects/1/webhook/policies
{
  "name": "slack-vuln-alert",
  "description": "Alert on critical CVEs",
  "targets": [
    {
      "type": "slack",
      "address": "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX",
      "skip_cert_verify": false
    }
  ],
  "event_types": [
    "SCANNING_COMPLETED"
  ],
  "enabled": true
}
```

### 3.3 Content Trust & Image Signing

**Notary Setup (TUF):**
```bash
# Enable content trust in Harbor UI: Administration > Configuration > Project Quotas
# Enable "Content Trust" for project

# Client-side: Docker Content Trust
export DOCKER_CONTENT_TRUST=1
export DOCKER_CONTENT_TRUST_SERVER=https://notary.harbor.example.com

# Login to Harbor
docker login harbor.example.com

# Push signed image (generates root + targets keys)
docker tag myapp:latest harbor.example.com/production/myapp:v1.0.0
docker push harbor.example.com/production/myapp:v1.0.0
# Prompts for passphrase, creates ~/.docker/trust/

# Verify signature
docker trust inspect --pretty harbor.example.com/production/myapp:v1.0.0
```

**Cosign Integration (Sigstore):**
```bash
# Generate key pair
cosign generate-key-pair

# Sign image
cosign sign --key cosign.key harbor.example.com/production/myapp:v1.0.0

# Upload public key to Harbor (via UI or ConfigMap)
kubectl create configmap cosign-pubkey --from-file=cosign.pub -n harbor

# Verify signature
cosign verify --key cosign.pub harbor.example.com/production/myapp:v1.0.0
```

**Kyverno Policy: Require Signed Images:**
```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-image-signature
spec:
  validationFailureAction: Enforce
  background: false
  rules:
  - name: check-signature
    match:
      any:
      - resources:
          kinds:
          - Pod
    verifyImages:
    - imageReferences:
      - "harbor.example.com/production/*"
      attestors:
      - count: 1
        entries:
        - keys:
            publicKeys: |-
              -----BEGIN PUBLIC KEY-----
              <cosign-public-key>
              -----END PUBLIC KEY-----
```

### 3.4 Threat Model & Mitigations

**Threats:**
1. **Unsigned/Unverified Images:** Malicious images deployed → supply-chain attack
2. **Vulnerable Images:** Unpatched CVEs (Log4Shell, OpenSSL) → RCE
3. **Registry Compromise:** Attacker gains admin → tamper with images
4. **Image Tampering:** MITM during pull → inject backdoor
5. **Credential Leakage:** Robot account tokens → unauthorized push/pull

**Mitigations:**
- **Mandatory Signing:** Enforce Notary/Cosign in Harbor + Kyverno admission
- **Automated Scanning:** Trivy scans on push, block images with HIGH/CRITICAL CVEs
- **Immutable Tags:** Enable immutability for release tags (v1.0.0, prod-*)
- **RBAC:** Principle of least privilege, use robot accounts with scoped permissions
- **Audit Logs:** Enable audit logging, forward to SIEM (Splunk, ELK)
- **Network Segmentation:** Restrict registry access via NetworkPolicy
- **Replication Validation:** Verify checksums post-replication
- **Secrets Management:** Rotate robot tokens quarterly, use Vault for storage

**RBAC Example:**
```bash
# Create project-scoped robot account (via UI or API)
# Permissions: pull-only for "production" project
# Token: robot$production-readonly+<token>

# Use in Kubernetes Secret
kubectl create secret docker-registry harbor-pull-secret \
  --docker-server=harbor.example.com \
  --docker-username='robot$production-readonly' \
  --docker-password='<token>' \
  -n production
```

### 3.5 Testing & Validation

**Test Image Push/Pull:**
```bash
# Push test image
docker build -t harbor.example.com/test-project/nginx:latest .
docker push harbor.example.com/test-project/nginx:latest

# Verify scan results
curl -u admin:<password> https://harbor.example.com/api/v2.0/projects/test-project/repositories/nginx/artifacts/latest?with_scan_overview=true | jq '.scan_overview'
```

**Test Replication:**
```bash
# Trigger manual replication
curl -X POST -u admin:<password> https://harbor.example.com/api/v2.0/replication/executions \
  -H "Content-Type: application/json" \
  -d '{"policy_id": 1}'

# Check replication status
curl -u admin:<password> https://harbor.example.com/api/v2.0/replication/executions/1 | jq '.status'
```

**Test Vulnerability Blocking:**
```bash
# Configure project to prevent vulnerable images
# Project > Configuration > Deployment Security > "Prevent vulnerable images from running" > Severity: High

# Try to pull vulnerable image
kubectl run test --image=harbor.example.com/test-project/vulnerable:latest
# Should fail if CVEs present
```

---

## 4. Kyverno: Kubernetes Policy Engine

### 4.1 Core Concepts

**Policy Types:**
- **ClusterPolicy:** Cluster-wide policies
- **Policy:** Namespace-scoped policies

**Rule Types:**
- **Validation:** Admit/deny resources based on conditions
- **Mutation:** Modify resources (add labels, sidecars, defaults)
- **Generation:** Create new resources (NetworkPolicy, LimitRange)
- **Verification:** Validate image signatures (Cosign, Notary)

**Execution Modes:**
- **Admission Control:** Webhook-based (ValidatingWebhookConfiguration, MutatingWebhookConfiguration)
- **Background Scanning:** Continuous validation of existing resources
- **Audit Mode:** Report violations without blocking

**Policy Structure:**
```yaml
spec:
  validationFailureAction: Enforce | Audit
  background: true | false
  rules:
  - name: <rule-name>
    match:  # resource selection
      any/all:
      - resources: {}
      - subjects: {}
    exclude: {}  # exceptions
    validate | mutate | generate | verifyImages: {}
```

### 4.2 Deployment & Configuration

**Installation (Helm):**
```bash
# Add Kyverno repo
helm repo add kyverno https://kyverno.github.io/kyverno/
helm repo update

# Install Kyverno
helm install kyverno kyverno/kyverno \
  --namespace kyverno \
  --create-namespace \
  --set replicaCount=3 \
  --set podSecurityStandard=restricted \
  --set admissionController.replicas=3 \
  --set backgroundController.replicas=2 \
  --set cleanupController.replicas=2 \
  --set reportsController.replicas=2

# Install policy reporter (UI)
helm install policy-reporter kyverno/policy-reporter \
  --namespace kyverno \
  --set ui.enabled=true \
  --set kyvernoPlugin.enabled=true

# Verify deployment
kubectl -n kyverno get pods
kubectl get clusterpolicies
```

**Example: Require Resource Limits:**
```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-resource-limits
  annotations:
    policies.kyverno.io/title: Require Resource Limits
    policies.kyverno.io/category: Best Practices
    policies.kyverno.io/severity: medium
spec:
  validationFailureAction: Enforce
  background: true
  rules:
  - name: validate-resources
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
```

**Example: Add Sidecar (Mutation):**
```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: inject-sidecar
spec:
  rules:
  - name: inject-logging-sidecar
    match:
      any:
      - resources:
          kinds:
          - Deployment
          namespaces:
          - production
          selector:
            matchLabels:
              inject-sidecar: "true"
    mutate:
      patchStrategicMerge:
        spec:
          template:
            spec:
              containers:
              - name: log-shipper
                image: fluent/fluent-bit:2.0
                env:
                - name: LOG_LEVEL
                  value: info
                volumeMounts:
                - name: varlog
                  mountPath: /var/log
              volumes:
              - name: varlog
                emptyDir: {}
```

**Example: Generate NetworkPolicy:**
```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: generate-default-networkpolicy
spec:
  rules:
  - name: default-deny-ingress
    match:
      any:
      - resources:
          kinds:
          - Namespace
    generate:
      apiVersion: networking.k8s.io/v1
      kind: NetworkPolicy
      name: default-deny-ingress
      namespace: "{{request.object.metadata.name}}"
      synchronize: true
      data:
        spec:
          podSelector: {}
          policyTypes:
          - Ingress
```

**Example: Block Privileged Containers:**
```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: disallow-privileged
spec:
  validationFailureAction: Enforce
  background: true
  rules:
  - name: check-privileged
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
```

**Example: Require Non-root User:**
```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-non-root
spec:
  validationFailureAction: Enforce
  background: true
  rules:
  - name: check-runAsNonRoot
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "Containers must run as non-root"
      pattern:
        spec:
          securityContext:
            runAsNonRoot: true
          containers:
          - securityContext:
              runAsNonRoot: true
```

### 4.3 Image Verification & Supply Chain Security

**Verify Cosign Signatures:**
```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-cosign-signature
spec:
  validationFailureAction: Enforce
  background: false
  rules:
  - name: verify-signature
    match:
      any:
      - resources:
          kinds:
          - Pod
    verifyImages:
    - imageReferences:
      - "harbor.example.com/production/*"
      attestors:
      - count: 1
        entries:
        - keys:
            publicKeys: |-
              -----BEGIN PUBLIC KEY-----
              MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...
              -----END PUBLIC KEY-----
```

**Verify SBOM Attestations:**
```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-sbom-attestation
spec:
  validationFailureAction: Enforce
  background: false
  rules:
  - name: check-sbom
    match:
      any:
      - resources:
          kinds:
          - Pod
    verifyImages:
    - imageReferences:
      - "harbor.example.com/production/*"
      attestations:
      - predicateType: https://spdx.dev/Document
        attestors:
        - count: 1
          entries:
          - keys:
              publicKeys: |-
                -----BEGIN PUBLIC KEY-----
                <public-key>
                -----END PUBLIC KEY-----
```

**Enforce Image Registry Allowlist:**
```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: restrict-image-registries
spec:
  validationFailureAction: Enforce
  background: true
  rules:
  - name: check-registry
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "Images must come from approved registries"
      pattern:
        spec:
          containers:
          - image: "harbor.example.com/* | gcr.io/my-project/* | registry.internal.example.com/*"
```

### 4.4 Threat Model & Mitigations

**Threats:**
1. **Policy Bypass:** Attacker disables webhook → deploy malicious workload
2. **Privilege Escalation:** Privileged pods, hostPath mounts
3. **Unsigned Images:** Unverified container images → supply-chain compromise
4. **Resource Exhaustion:** No limits → noisy neighbor, DoS
5. **Network Exposure:** Missing NetworkPolicy → lateral movement

**Mitigations:**
- **Webhook HA:** 3+ replicas, PodDisruptionBudget, readiness probes
- **Fail-Closed:** Set webhook `failurePolicy: Fail` (block on webhook failure)
- **RBAC Protection:** Restrict ClusterPolicy/Policy creation to admins
- **Policy Testing:** Use `kubectl kyverno test` for CI/CD validation
- **Audit Mode:** Enable for new policies, monitor for false positives
- **Background Scanning:** Detect drift from policy (existing non-compliant resources)
- **Metrics:** Prometheus metrics for policy violations, webhook latency

**RBAC Example:**
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: kyverno-policy-admin
rules:
- apiGroups: ["kyverno.io"]
  resources: ["clusterpolicies", "policies"]
  verbs: ["create", "update", "patch", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: kyverno-policy-admin-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: kyverno-policy-admin
subjects:
- kind: Group
  name: security-team
  apiGroup: rbac.authorization.k8s.io
```

### 4.5 Testing & Validation

**Test Policy in Audit Mode:**
```bash
# Apply policy in audit mode
kubectl apply -f policy.yaml

# Create violating resource
kubectl run nginx --image=nginx  # no resource limits

# Check policy reports
kubectl get policyreports -A
kubectl describe policyreport <report-name>

# View violations
kubectl get clusterpolicyreport -o yaml | grep -A 10 "result: fail"
```

**Test Policy with kubectl kyverno:**
```bash
# Install kyverno CLI
go install github.com/kyverno/kyverno/cmd/cli/kubectl-kyverno@latest

# Test policy against resource
kubectl kyverno apply policy.yaml --resource test-pod.yaml

# Run policy test suite
cat <<EOF > kyverno-test.yaml
name: require-resource-limits
policies:
- policy.yaml
resources:
- test-pod.yaml
results:
- policy: require-resource-limits
  rule: validate-resources
  resource: test-pod
  result: fail
EOF

kubectl kyverno test kyverno-test.yaml
```

**Simulate Image Verification:**
```bash
# Sign image with Cosign
cosign sign --key cosign.key harbor.example.com/production/app:v1.0.0

# Create pod (Kyverno verifies signature on admission)
kubectl run test --image=harbor.example.com/production/app:v1.0.0

# Check admission webhook logs
kubectl -n kyverno logs -l app.kubernetes.io/component=admission-controller | grep verify
```

**Monitor Policy Violations:**
```bash
# Prometheus metrics
kubectl port-forward -n kyverno svc/kyverno-svc-metrics 8000:8000

curl http://localhost:8000/metrics | grep kyverno_policy_results_total

# Example query: violation rate
rate(kyverno_policy_results_total{policy_result="fail"}[5m])
```

---

## 5. Integration & End-to-End Workflow

### 5.1 Secure CI/CD Pipeline

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│  Git Push    │──────>│  CI Build    │──────>│ Harbor Push  │
└──────────────┘       └──────────────┘       └──────┬───────┘
                            │                         │
                            │ Trivy scan              │ Cosign sign
                            ↓                         ↓
                       ┌──────────────┐       ┌──────────────┐
                       │  Fail on CVE │       │ Upload SBOM  │
                       └──────────────┘       └──────┬───────┘
                                                     │
                       ┌─────────────────────────────┘
                       │
                       ↓
                ┌──────────────┐       ┌──────────────┐
                │ kubectl apply│──────>│  Kyverno     │
                └──────────────┘       │  Verify Sig  │
                                       └──────┬───────┘
                                              │ Pass
                                              ↓
                                       ┌──────────────┐
                                       │ Tetragon     │
                                       │ Monitor      │
                                       └──────────────┘
```

**GitHub Actions Example:**
```yaml
name: Secure Build
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Build image
      run: docker build -t harbor.example.com/prod/app:${{ github.sha }} .
    
    - name: Scan with Trivy
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: harbor.example.com/prod/app:${{ github.sha }}
        exit-code: 1  # fail on HIGH/CRITICAL
        severity: HIGH,CRITICAL
    
    - name: Push to Harbor
      run: |
        echo "${{ secrets.HARBOR_PASSWORD }}" | docker login harbor.example.com -u robot$ci-pusher --password-stdin
        docker push harbor.example.com/prod/app:${{ github.sha }}
    
    - name: Sign with Cosign
      run: |
        cosign sign --key env://COSIGN_KEY harbor.example.com/prod/app:${{ github.sha }}
      env:
        COSIGN_KEY: ${{ secrets.COSIGN_PRIVATE_KEY }}
        COSIGN_PASSWORD: ${{ secrets.COSIGN_PASSWORD }}
    
    - name: Generate SBOM
      run: |
        syft harbor.example.com/prod/app:${{ github.sha }} -o spdx-json > sbom.spdx.json
        cosign attest --key env://COSIGN_KEY --predicate sbom.spdx.json harbor.example.com/prod/app:${{ github.sha }}
```

### 5.2 Unified Policy Enforcement

**ClusterPolicy: Comprehensive Security Baseline:**
```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: security-baseline
spec:
  validationFailureAction: Enforce
  background: true
  rules:
  # Rule 1: Verify image signatures
  - name: verify-signature
    match:
      any:
      - resources:
          kinds: [Pod]
    verifyImages:
    - imageReferences:
      - "harbor.example.com/production/*"
      attestors:
      - count: 1
        entries:
        - keys:
            publicKeys: |-
              -----BEGIN PUBLIC KEY-----
              <pubkey>
              -----END PUBLIC KEY-----
  
  # Rule 2: Block privileged
  - name: no-privileged
    match:
      any:
      - resources:
          kinds: [Pod]
    validate:
      message: "Privileged containers not allowed"
      pattern:
        spec:
          containers:
          - =(securityContext):
              =(privileged): false
  
  # Rule 3: Require resource limits
  - name: require-limits
    match:
      any:
      - resources:
          kinds: [Pod]
    validate:
      message: "Resource limits required"
      pattern:
        spec:
          containers:
          - resources:
              limits:
                memory: "?*"
                cpu: "?*"
  
  # Rule 4: Drop capabilities
  - name: drop-capabilities
    match:
      any:
      - resources:
          kinds: [Pod]
    validate:
      message: "Drop ALL capabilities"
      pattern:
        spec:
          containers:
          - securityContext:
              capabilities:
                drop:
                - ALL
  
  # Rule 5: No host namespaces
  - name: no-host-namespaces
    match:
      any:
      - resources:
          kinds: [Pod]
    validate:
      message: "Host namespaces not allowed"
      pattern:
        spec:
          =(hostNetwork): false
          =(hostPID): false
          =(hostIPC): false
```

### 5.3 Observability & Alerting

**Prometheus Alerts:**
```yaml
groups:
- name: certificate-alerts
  rules:
  - alert: CertificateExpiringSoon
    expr: certmanager_certificate_expiration_timestamp_seconds - time() < 604800  # 7 days
    for: 1h
    labels:
      severity: warning
    annotations:
      summary: "Certificate {{ $labels.name }} expires in <7 days"
  
  - alert: CertificateRenewalFailed
    expr: certmanager_certificate_ready_status{condition="False"} == 1
    for: 15m
    labels:
      severity: critical
    annotations:
      summary: "Certificate {{ $labels.name }} renewal failed"

- name: tetragon-alerts
  rules:
  - alert: SuspiciousProcessExecution
    expr: rate(tetragon_events_total{event_type="process_exec",binary=~".*/tmp/.*"}[5m]) > 0
    labels:
      severity: high
    annotations:
      summary: "Suspicious binary executed from /tmp"
  
  - alert: SensitiveFileAccess
    expr: rate(tetragon_policy_events_total{policy="monitor-sensitive-files"}[5m]) > 0
    labels:
      severity: critical
    annotations:
      summary: "Sensitive file accessed"

- name: harbor-alerts
  rules:
  - alert: VulnerableImagePushed
    expr: harbor_artifact_vulnerabilities{severity="Critical"} > 0
    labels:
      severity: high
    annotations:
      summary: "Image {{ $labels.repository }}:{{ $labels.tag }} has critical CVEs"
  
  - alert: ReplicationFailed
    expr: harbor_replication_status{status="failed"} > 0
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "Replication policy {{ $labels.policy }} failed"

- name: kyverno-alerts
  rules:
  - alert: PolicyViolationRate
    expr: rate(kyverno_policy_results_total{policy_result="fail"}[5m]) > 1
    labels:
      severity: warning
    annotations:
      summary: "High policy violation rate: {{ $value }}/sec"
  
  - alert: WebhookFailure
    expr: kyverno_admission_requests_total{webhook_result="error"} > 10
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Kyverno webhook errors detected"
```

**Grafana Dashboard (JSON snippet):**
```json
{
  "dashboard": {
    "title": "Security Stack Overview",
    "panels": [
      {
        "title": "Certificate Expiry Timeline",
        "targets": [
          {
            "expr": "(certmanager_certificate_expiration_timestamp_seconds - time()) / 86400"
          }
        ]
      },
      {
        "title": "Tetragon Event Rate",
        "targets": [
          {
            "expr": "sum by(event_type) (rate(tetragon_events_total[5m]))"
          }
        ]
      },
      {
        "title": "Harbor Image Vulnerabilities",
        "targets": [
          {
            "expr": "sum by(severity) (harbor_artifact_vulnerabilities)"
          }
        ]
      },
      {
        "title": "Kyverno Policy Compliance",
        "targets": [
          {
            "expr": "(sum(kyverno_policy_results_total{policy_result=\"pass\"}) / sum(kyverno_policy_results_total)) * 100"
          }
        ]
      }
    ]
  }
}
```

---

## 6. Production Rollout Plan

### Phase 1: Staging Validation (Week 1-2)
```bash
# Deploy to staging cluster
kubectl config use-context staging

# Install cert-manager
helm install cert-manager jetstack/cert-manager -n cert-manager --create-namespace --set installCRDs=true

# Install Tetragon (audit mode)
helm install tetragon cilium/tetragon -n kube-system --set tetragon.enablePolicyAudit=true

# Install Harbor
helm install harbor harbor/harbor -n harbor --create-namespace -f harbor-values.yaml

# Install Kyverno (audit mode)
helm install kyverno kyverno/kyverno -n kyverno --create-namespace --set validationFailureAction=Audit

# Deploy test workloads
kubectl apply -f test-deployments/

# Monitor for 1 week
kubectl get policyreports -A
kubectl -n kube-system exec -it ds/tetragon -c tetragon -- tetra getevents -o compact | tee tetragon-staging.log
```

### Phase 2: Production Pilot (Week 3-4)
```bash
# Deploy to production (single namespace)
kubectl config use-context production

# Install components with HA
helm install cert-manager jetstack/cert-manager -n cert-manager --set replicaCount=3
helm install tetragon cilium/tetragon -n kube-system
helm install harbor harbor/harbor -n harbor -f harbor-prod-values.yaml
helm install kyverno kyverno/kyverno -n kyverno --set replicaCount=3

# Enable policies for pilot namespace
kubectl label namespace pilot-app kyverno.io/policy-enforcement=enabled

# Deploy pilot app
kubectl apply -f pilot-app/ -n pilot-app

# Monitor metrics
kubectl port-forward -n kyverno svc/kyverno-svc-metrics 8000:8000
curl http://localhost:8000/metrics | grep kyverno_admission_requests_total
```

### Phase 3: Production Rollout (Week 5-6)
```bash
# Enable enforcement cluster-wide
kubectl patch clusterpolicy security-baseline --type=merge -p '{"spec":{"validationFailureAction":"Enforce"}}'

# Enable Tetragon policies
kubectl apply -f tetragon-policies/

# Migrate images to Harbor
for img in $(kubectl get pods -A -o jsonpath='{.items[*].spec.containers[*].image}' | tr ' ' '\n' | sort -u); do
  docker pull $img
  docker tag $img harbor.example.com/migrated/$(basename $img)
  docker push harbor.example.com/migrated/$(basename $img)
done

# Update deployments to use Harbor
kubectl set image deployment/<name> <container>=harbor.example.com/migrated/<image>
```

### Rollback Plan
```bash
# Emergency: Disable Kyverno enforcement
kubectl patch clusterpolicy security-baseline --type=merge -p '{"spec":{"validationFailureAction":"Audit"}}'

# Disable Tetragon kill actions
kubectl patch tracingpolicy <policy-name> --type=json -p='[{"op":"replace","path":"/spec/kprobes/0/selectors/0/matchActions","value":[{"action":"Post"}]}]'

# Bypass Harbor (emergency pull from upstream)
kubectl patch deployment <name> --type=json -p='[{"op":"replace","path":"/spec/template/spec/imagePullSecrets","value":[]}]'

# Rollback cert-manager
helm rollback cert-manager -n cert-manager

# Full rollback
helm uninstall kyverno -n kyverno
helm uninstall tetragon -n kube-system
```

---

## 7. Operational Runbook

### Incident: Certificate Expiry
```bash
# Identify expired/expiring certs
kubectl get certificates -A -o json | jq -r '.items[] | select(.status.notAfter | fromdateiso8601 < (now + 604800)) | "\(.metadata.namespace)/\(.metadata.name)"'

# Force renewal
kubectl annotate certificate <name> -n <namespace> cert-manager.io/issue-temporary-certificate="true" --overwrite
kubectl delete certificaterequest -l cert-manager.io/certificate-name=<name> -n <namespace>

# Verify new cert issued
kubectl get certificate <name> -n <namespace> -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}'
```

### Incident: Image Signature Verification Failure
```bash
# Check Kyverno admission logs
kubectl -n kyverno logs -l app.kubernetes.io/component=admission-controller | grep "image verification failed"

# Manually verify signature
cosign verify --key cosign.pub harbor.example.com/production/app:v1.0.0

# Re-sign if needed
cosign sign --key cosign.key harbor.example.com/production/app:v1.0.0

# Override for emergency (NOT recommended)
kubectl label namespace <ns> kyverno.io/policy-enforcement=disabled
```

### Incident: Tetragon Process Kill False Positive
```bash
# Identify killed process
kubectl -n kube-system exec -it ds/tetragon -c tetragon -- tetra getevents -o compact | grep Sigkill

# Update policy to exclude process
kubectl edit tracingpolicy <policy-name>
# Add to matchBinaries.NotIn: - "/path/to/legitimate/binary"

# Or disable specific policy
kubectl patch tracingpolicy <policy-name> --type=merge -p '{"spec":{"enabled":false}}'
```

---

## 8. References & Next Steps

**Official Documentation:**
- cert-manager: https://cert-manager.io/docs/
- Tetragon: https://tetragon.io/docs/
- Harbor: https://goharbor.io/docs/
- Kyverno: https://kyverno.io/docs/

**Security Standards:**
- CIS Kubernetes Benchmark: https://www.cisecurity.org/benchmark/kubernetes
- NIST SP 800-190 (Container Security): https://csrc.nist.gov/publications/detail/sp/800-190/final
- PCI-DSS v4.0 (for payment workloads)
- SLSA Framework (Supply Chain Levels): https://slsa.dev/

**Threat Intelligence:**
- MITRE ATT&CK for Containers: https://attack.mitre.org/matrices/enterprise/containers/
- Kubernetes CVE Database: https://kubernetes.io/docs/reference/issues-security/official-cve-feed/

---

## Next 3 Steps

1. **Deploy to Lab Cluster:**
   ```bash
   # Create lab cluster (kind/minikube/k3s)
   kind create cluster --name security-lab
   
   # Install full stack
   ./install-security-stack.sh
   
   # Run compliance scan
   kube-bench run --targets master,node,policies
   ```

2. **Implement GitOps Pipeline:**
   ```bash
   # ArgoCD + Kyverno policy sync
   kubectl apply -f argocd-app-kyverno-policies.yaml
   
   # Pre-commit hook for policy validation
   echo 'kubectl kyverno apply policies/ --resource test-manifests/' > .git/hooks/pre-commit
   ```

3. **Harden etcd & API Server:**
   ```bash
   # Enable etcd encryption
   kubectl create secret generic etcd-encryption-key --from-literal=key=$(head -c 32 /dev/urandom | base64)
   
   # API server flags (kubeadm config)
   # --encryption-provider-config=/etc/kubernetes/enc/encryption-config.yaml
   # --audit-log-path=/var/log/k8s-audit.log
   # --audit-policy-file=/etc/kubernetes/audit-policy.yaml
   ```

**Questions for clarity?** Specify: (a) deployment target (EKS/GKE/AKS/on-prem), (b) compliance requirements (PCI/HIPAA/FedRAMP), (c) existing CA infrastructure, (d) image scanning requirements.