# Kubernetes Security: Complete In-Depth Guide

> **Audience:** Senior security/systems engineers building production-grade, security-first Kubernetes infrastructure.  
> **Scope:** Every security domain from kernel primitives to supply-chain integrity, with Go implementations, real ASCII diagrams, threat models, and operational runbooks.  
> **Version baseline:** Kubernetes 1.29+ / Go 1.22+

---

## Table of Contents

1. [Kubernetes Security Architecture — First Principles](#1-kubernetes-security-architecture--first-principles)
2. [Control Plane Hardening](#2-control-plane-hardening)
3. [Authentication — Every Mechanism Deep-Dive](#3-authentication--every-mechanism-deep-dive)
4. [Authorization — RBAC, ABAC, Webhook, Node](#4-authorization--rbac-abac-webhook-node)
5. [Admission Controllers — Mutating & Validating](#5-admission-controllers--mutating--validating)
6. [etcd Security](#6-etcd-security)
7. [TLS Everywhere — PKI Architecture](#7-tls-everywhere--pki-architecture)
8. [Pod Security — Namespaces, Capabilities, Seccomp, AppArmor, SELinux](#8-pod-security--namespaces-capabilities-seccomp-apparmor-selinux)
9. [Network Policy & Micro-Segmentation](#9-network-policy--micro-segmentation)
10. [Secrets Management](#10-secrets-management)
11. [Service Account Security](#11-service-account-security)
12. [Container Runtime Security](#12-container-runtime-security)
13. [Supply Chain Security — SBOM, Sigstore, Cosign, SLSA](#13-supply-chain-security--sbom-sigstore-cosign-slsa)
14. [Runtime Threat Detection — eBPF, Falco, Audit](#14-runtime-threat-detection--ebpf-falco-audit)
15. [Service Mesh Security — mTLS, Authorization Policies](#15-service-mesh-security--mtls-authorization-policies)
16. [Multi-Tenancy Isolation Models](#16-multi-tenancy-isolation-models)
17. [Workload Identity & SPIFFE/SPIRE](#17-workload-identity--spiffespire)
18. [Kubernetes CIS Benchmark & Compliance](#18-kubernetes-cis-benchmark--compliance)
19. [Threat Modeling — STRIDE across K8s](#19-threat-modeling--stride-across-k8s)
20. [CVE Deep-Dives & Exploit Chains](#20-cve-deep-dives--exploit-chains)
21. [Incident Response & Forensics](#21-incident-response--forensics)
22. [Go Security Tooling — Full Implementations](#22-go-security-tooling--full-implementations)

---

## 1. Kubernetes Security Architecture — First Principles

### 1.1 The Security Perimeter Model

Kubernetes has **no single security boundary**. Every component is a trust boundary. The mental model is a series of concentric enforcement rings:

```
┌─────────────────────────────────────────────────────────────────────┐
│  PHYSICAL / HYPERVISOR LAYER                                        │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  OS KERNEL  (Linux 5.15+ with seccomp, LSM, namespaces)      │  │
│  │  ┌─────────────────────────────────────────────────────────┐  │  │
│  │  │  CONTAINER RUNTIME  (containerd 1.7 / crun 1.14)       │  │  │
│  │  │  ┌───────────────────────────────────────────────────┐  │  │  │
│  │  │  │  KUBERNETES NODE AGENT  (kubelet :10250)          │  │  │  │
│  │  │  │  ┌─────────────────────────────────────────────┐  │  │  │  │
│  │  │  │  │  POD  (network ns, pid ns, mnt ns, uts ns)  │  │  │  │  │
│  │  │  │  │  ┌───────────────────────────────────────┐  │  │  │  │  │
│  │  │  │  │  │  CONTAINER  (cgroups v2, capabilities) │  │  │  │  │  │
│  │  │  │  │  │  ┌─────────────────────────────────┐  │  │  │  │  │  │
│  │  │  │  │  │  │  APPLICATION PROCESS  (uid 1000) │  │  │  │  │  │  │
│  │  │  │  │  │  └─────────────────────────────────┘  │  │  │  │  │  │
│  │  │  │  │  └───────────────────────────────────────┘  │  │  │  │  │
│  │  │  │  └─────────────────────────────────────────────┘  │  │  │  │
│  │  │  └───────────────────────────────────────────────────┘  │  │  │
│  │  └─────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘

Each boundary = independent enforcement point with its own policy engine.
Breaching one layer does NOT automatically breach the next.
Defense-in-depth: every layer must be independently hardened.
```

### 1.2 Kubernetes Component Trust Topology

```
                        INTERNET / CLIENTS
                               │
                        ┌──────▼──────┐
                        │  Ingress /  │  TCP:443
                        │  LB/Proxy   │
                        └──────┬──────┘
                               │ TLS termination
                    ╔══════════▼═══════════╗
                    ║   CONTROL PLANE      ║
                    ║  ┌────────────────┐  ║
                    ║  │  kube-apiserver│  ║  TCP:6443 (ext), TCP:8080 (insecure — DISABLE)
                    ║  │  :6443         │  ║
                    ║  └───┬────────────┘  ║
                    ║      │               ║
                    ║  ┌───▼────────────┐  ║
                    ║  │kube-controller │  ║  TCP:10257 (metrics/health, mTLS)
                    ║  │-manager :10257 │  ║
                    ║  └───┬────────────┘  ║
                    ║      │               ║
                    ║  ┌───▼────────────┐  ║
                    ║  │kube-scheduler  │  ║  TCP:10259 (metrics/health, mTLS)
                    ║  │:10259          │  ║
                    ║  └───┬────────────┘  ║
                    ║      │               ║
                    ║  ┌───▼────────────┐  ║
                    ║  │  etcd cluster  │  ║  TCP:2379 (client), TCP:2380 (peer)
                    ║  │  :2379,:2380   │  ║  mTLS required on BOTH ports
                    ║  └────────────────┘  ║
                    ╚══════════════════════╝
                               │
              ┌────────────────┼────────────────┐
              │                │                │
       ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
       │   NODE 1    │  │   NODE 2    │  │   NODE 3    │
       │  kubelet    │  │  kubelet    │  │  kubelet    │
       │  :10250     │  │  :10250     │  │  :10250     │
       │  kube-proxy │  │  kube-proxy │  │  kube-proxy │
       │  :10256     │  │  :10256     │  │  :10256     │
       │  CNI plugin │  │  CNI plugin │  │  CNI plugin │
       └─────────────┘  └─────────────┘  └─────────────┘

Port reference (actual):
  6443   - API server (TLS, client cert or token auth)
  2379   - etcd client API (mTLS mandatory)
  2380   - etcd peer (mTLS mandatory)
  10250  - kubelet API (mTLS mandatory; anonymous=false)
  10255  - kubelet read-only — MUST BE DISABLED (was unauthenticated)
  10256  - kube-proxy health
  10257  - controller-manager (mTLS)
  10259  - scheduler (mTLS)
  4194   - cAdvisor — DISABLE or firewall (was unauthenticated)
```

### 1.3 The 4C Security Model

```
┌──────────────────────────────────────────────────────────────────────────┐
│  4C: Cloud → Cluster → Container → Code                                  │
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  CLOUD  (IAM roles, VPC/firewall, KMS, node identity, audit log)  │  │
│  │  ┌──────────────────────────────────────────────────────────────┐  │  │
│  │  │  CLUSTER  (RBAC, AdmissionWebhook, NetworkPolicy, PSA, TLS) │  │  │
│  │  │  ┌────────────────────────────────────────────────────────┐  │  │  │
│  │  │  │  CONTAINER  (seccomp, capabilities, ro-fs, no-root)   │  │  │  │
│  │  │  │  ┌──────────────────────────────────────────────────┐  │  │  │  │
│  │  │  │  │  CODE  (dep scan, SAST, SBOM, runtime RASP)      │  │  │  │  │
│  │  │  │  └──────────────────────────────────────────────────┘  │  │  │  │
│  │  │  └────────────────────────────────────────────────────────┘  │  │  │
│  │  └──────────────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  Weakness in outer layer amplifies risk in inner layers.                 │
│  A compromised node bypasses all cluster-level pod isolation.             │
│  Cloud IAM misconfiguration gives cluster-admin to any VM in the account.│
└──────────────────────────────────────────────────────────────────────────┘
```

### 1.4 Attack Surface Taxonomy

| Surface | Default Exposure | Key Risk | Hardening |
|---|---|---|---|
| API server :6443 | Internet if not firewalled | Unauthn API calls, credential theft | OIDC + RBAC + audit |
| etcd :2379 | Internal only | Full cluster data exfil, secret theft | mTLS + encryption-at-rest |
| kubelet :10250 | Node network | Exec into pods, secret access | Webhook authn, cert rotation |
| kubelet :10255 | Node network | Info leak (no auth) | **DISABLE** |
| Dashboard | ClusterIP (often exposed) | UI auth bypass → cluster-admin | Remove or NodePort+auth |
| Container registry | External pull | Malicious image injection | Image signing + admission |
| Pod → cloud metadata | Node network | Cloud credential theft | IMDSv2 + NetworkPolicy block |
| Service account JWT | In-pod filesystem | Lateral movement | Bound tokens + audience |

---

## 2. Control Plane Hardening

### 2.1 API Server Hardening — Every Flag Explained

```
kube-apiserver \
  # TLS
  --tls-cert-file=/etc/kubernetes/pki/apiserver.crt \
  --tls-private-key-file=/etc/kubernetes/pki/apiserver.key \
  --client-ca-file=/etc/kubernetes/pki/ca.crt \

  # Auth
  --anonymous-auth=false \                          # Disable anonymous access
  --authorization-mode=Node,RBAC \                  # NEVER AlwaysAllow
  --enable-admission-plugins=NodeRestriction,PodSecurity,\
    ResourceQuota,LimitRanger,ServiceAccount,\
    TLSBootstrap,ValidatingAdmissionWebhook,\
    MutatingAdmissionWebhook \

  # etcd client
  --etcd-cafile=/etc/kubernetes/pki/etcd/ca.crt \
  --etcd-certfile=/etc/kubernetes/pki/apiserver-etcd-client.crt \
  --etcd-keyfile=/etc/kubernetes/pki/apiserver-etcd-client.key \
  --etcd-servers=https://127.0.0.1:2379 \

  # Service account token validation
  --service-account-issuer=https://kubernetes.default.svc.cluster.local \
  --service-account-signing-key-file=/etc/kubernetes/pki/sa.key \
  --service-account-key-file=/etc/kubernetes/pki/sa.pub \

  # Audit
  --audit-log-path=/var/log/kubernetes/audit.log \
  --audit-log-maxage=30 \
  --audit-log-maxbackup=10 \
  --audit-log-maxsize=100 \
  --audit-policy-file=/etc/kubernetes/audit-policy.yaml \

  # Encryption at rest
  --encryption-provider-config=/etc/kubernetes/encryption-config.yaml \

  # Disable insecure port (default in 1.20+)
  --insecure-port=0 \

  # Bind only to internal IP
  --bind-address=0.0.0.0 \       # or specific internal IP
  --secure-port=6443 \

  # Request limits (DoS protection)
  --max-requests-inflight=400 \
  --max-mutating-requests-inflight=200 \

  # Profiling off (information leak)
  --profiling=false \

  # Feature gates
  --feature-gates=BoundServiceAccountTokenVolume=true \

  # OIDC (when using external IdP)
  --oidc-issuer-url=https://accounts.google.com \
  --oidc-client-id=kubernetes \
  --oidc-username-claim=email \
  --oidc-groups-claim=groups \

  # Aggregation layer (for metrics-server, etc.)
  --requestheader-client-ca-file=/etc/kubernetes/pki/front-proxy-ca.crt \
  --requestheader-allowed-names=front-proxy-client \
  --requestheader-extra-headers-prefix=X-Remote-Extra- \
  --requestheader-group-headers=X-Remote-Group \
  --requestheader-username-headers=X-Remote-User \
  --proxy-client-cert-file=/etc/kubernetes/pki/front-proxy-client.crt \
  --proxy-client-key-file=/etc/kubernetes/pki/front-proxy-client.key
```

### 2.2 Encryption-at-Rest Configuration

The API server encrypts secrets before writing to etcd. The config defines provider priority (first = encrypt, rest = decrypt fallback):

```yaml
# /etc/kubernetes/encryption-config.yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
      - configmaps      # encrypt ConfigMaps too if they carry sensitive data
    providers:
      - aescbc:          # AES-CBC with PKCS#7 padding
          keys:
            - name: key1
              secret: <base64-encoded-32-byte-key>  # openssl rand -base64 32
      - identity: {}     # fallback: reads unencrypted (existing secrets)
  - resources:
      - events           # never encrypt events (high volume, no sensitive data)
    providers:
      - identity: {}
```

**AES-CBC vs AES-GCM:**
- `aescbc`: no authentication tag → malleable (use with caution, use only with TLS + etcd mTLS)
- `aesgcm`: authenticated encryption, better, but key rotation is manual and complex
- `kms`: envelope encryption via external KMS (AWS KMS, GCP CKMS, HashiCorp Vault) — **recommended for production**

**KMS v2 Provider (K8s 1.29 stable):**
```yaml
providers:
  - kms:
      apiVersion: v2
      name: aws-kms
      endpoint: unix:///var/run/kmsplugin/socket.sock
      timeout: 3s
      cachesize: 1000
```

After updating encryption config, re-encrypt all existing secrets:
```bash
kubectl get secrets --all-namespaces -o json | \
  kubectl replace -f -
```

### 2.3 etcd Hardening

```
etcd \
  --name=etcd-0 \
  --data-dir=/var/lib/etcd \

  # Peer mTLS
  --peer-client-cert-auth=true \
  --peer-trusted-ca-file=/etc/etcd/pki/ca.crt \
  --peer-cert-file=/etc/etcd/pki/peer.crt \
  --peer-key-file=/etc/etcd/pki/peer.key \

  # Client mTLS
  --client-cert-auth=true \
  --trusted-ca-file=/etc/etcd/pki/ca.crt \
  --cert-file=/etc/etcd/pki/server.crt \
  --key-file=/etc/etcd/pki/server.key \

  # Bind only to internal
  --listen-client-urls=https://127.0.0.1:2379 \
  --advertise-client-urls=https://10.0.1.10:2379 \
  --listen-peer-urls=https://10.0.1.10:2380 \
  --initial-advertise-peer-urls=https://10.0.1.10:2380 \

  # Quotas (prevent unbounded growth)
  --quota-backend-bytes=8589934592 \  # 8GiB

  # Auto compaction
  --auto-compaction-retention=1 \
  --auto-compaction-mode=revision
```

**etcd Threat Model:**
```
Attacker gains etcd :2379 access (no mTLS) →
  GET /v3/kv/range '' '' → ALL cluster state + ALL secrets (plaintext if no encryption-at-rest) →
  Extract service account signing keys → Forge tokens → cluster-admin
```

**etcd Backup with Encryption Verification:**
```bash
# Snapshot
ETCDCTL_API=3 etcdctl snapshot save /backup/etcd-$(date +%Y%m%d).db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/etcd/pki/ca.crt \
  --cert=/etc/etcd/pki/client.crt \
  --key=/etc/etcd/pki/client.key

# Verify secret is encrypted in snapshot (should NOT show plaintext value)
ETCDCTL_API=3 etcdctl get /registry/secrets/default/my-secret \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/etcd/pki/ca.crt \
  --cert=/etc/etcd/pki/client.crt \
  --key=/etc/etcd/pki/client.key | hexdump -C | head
# First bytes should be: 6b 38 73 3a 65 6e 63 3a  ("k8s:enc:")
```

### 2.4 kubelet Hardening

```yaml
# /var/lib/kubelet/config.yaml
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration

# Authentication
authentication:
  anonymous:
    enabled: false          # CRITICAL: disable anonymous access
  webhook:
    enabled: true           # Use API server for auth decisions
    cacheTTL: 2m
  x509:
    clientCAFile: /etc/kubernetes/pki/ca.crt

# Authorization
authorization:
  mode: Webhook             # Delegate to API server
  webhook:
    cacheAuthorizedTTL: 5m
    cacheUnauthorizedTTL: 30s

# TLS
tlsCertFile: /var/lib/kubelet/pki/kubelet.crt
tlsPrivateKeyFile: /var/lib/kubelet/pki/kubelet.key
tlsMinVersion: VersionTLS12
tlsCipherSuites:
  - TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
  - TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
  - TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
  - TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
  - TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256
  - TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256

# Runtime
containerRuntimeEndpoint: unix:///run/containerd/containerd.sock
cgroupDriver: systemd
cgroupsPerQOS: true

# Security
readOnlyPort: 0             # DISABLE: was unauthenticated :10255
protectKernelDefaults: true # Ensure kernel params match kubelet expectations
makeIPTablesUtilChains: true
eventRecordQPS: 5

# Pod eviction (also security-relevant: prevent resource starvation)
evictionHard:
  memory.available: "100Mi"
  nodefs.available: "10%"
  imagefs.available: "15%"

# Rotate server cert
rotateCertificates: true
serverTLSBootstrap: true

# Limit node-level secret access
enableDebuggingHandlers: false  # production: disable /exec /attach via kubelet directly
```

---

## 3. Authentication — Every Mechanism Deep-Dive

### 3.1 Authentication Flow

```
Client Request
    │
    ▼
┌──────────────────────────────────────────────────────────────────┐
│  kube-apiserver Authentication Chain                             │
│                                                                  │
│  1. X.509 Client Certificate  ──────────────────────────────┐   │
│     CN=system:masters → cluster-admin                       │   │
│     CN=system:node:node-1 → Node auth                       │   │
│     CN=system:kube-controller-manager → controller          │   │
│                                                              │   │
│  2. Bearer Token                                             │   │
│     a. Static token file (--token-auth-file) — DEPRECATED   │   │
│     b. Service Account JWT (OIDC-compatible)                 │   │
│        iss: kubernetes.default.svc / external OIDC           │   │
│        sub: system:serviceaccount:<ns>:<name>                │   │
│     c. Bootstrap tokens: system:bootstrappers               │   │
│                                                              │   │
│  3. OIDC Token (external IdP)                                │   │
│     JWT verified against OIDC discovery endpoint            │   │
│     Claims mapped: username-claim, groups-claim              │   │
│                                                              │   │
│  4. Webhook Token Auth                                       │   │
│     POST /authenticate with TokenReview to external service  │   │
│                                                              │   │
│  5. Authenticating Proxy                                     │   │
│     X-Remote-User, X-Remote-Group headers from front-proxy  │   │
│                                                              ▼   │
│  Result: UserInfo{Username, UID, Groups, Extra}              │   │
│          or 401 Unauthorized                                 │   │
└──────────────────────────────────────────────────────────────────┘
    │ UserInfo passed to Authorization
    ▼
  RBAC / Webhook / Node Authorizer
```

### 3.2 X.509 Certificate Authentication — Deep Dive

Every Kubernetes certificate encodes identity in the Subject field:

```
Certificate Subject → Kubernetes Identity
──────────────────────────────────────────────────────────────
CN=admin,O=system:masters           → cluster-admin (any SA)
CN=system:kube-apiserver            → API server identity (to etcd/kubelet)
CN=system:kube-controller-manager   → controller-manager
CN=system:kube-scheduler            → scheduler
CN=system:node:worker-1,O=system:nodes → Node authenticator
CN=system:kube-proxy                → kube-proxy
CN=front-proxy-client               → aggregation layer
```

**CSR Workflow for User Certificate:**
```bash
# 1. Generate private key
openssl genrsa -out alice.key 4096

# 2. Create CSR with K8s subject
openssl req -new -key alice.key -out alice.csr \
  -subj "/CN=alice/O=team-platform/O=org-security"
  # O= maps to RBAC groups — multiple O= allowed

# 3. Submit as CertificateSigningRequest
cat <<EOF | kubectl apply -f -
apiVersion: certificates.k8s.io/v1
kind: CertificateSigningRequest
metadata:
  name: alice
spec:
  request: $(base64 -w0 alice.csr)
  signerName: kubernetes.io/kube-apiserver-client
  expirationSeconds: 86400   # 24h — short-lived preferred
  usages:
  - client auth
EOF

# 4. Approve (requires certificates.k8s.io/certificatesigningrequests/approval)
kubectl certificate approve alice

# 5. Retrieve
kubectl get csr alice -o jsonpath='{.status.certificate}' | base64 -d > alice.crt

# 6. Verify
openssl x509 -in alice.crt -noout -subject -issuer -enddate
```

### 3.3 Service Account Token Authentication

**Legacy Token (pre-1.22) — Mounted as long-lived secret, INSECURE:**
```
/var/run/secrets/kubernetes.io/serviceaccount/token
JWT payload:
{
  "iss": "kubernetes/serviceaccount",
  "kubernetes.io/serviceaccount/namespace": "default",
  "kubernetes.io/serviceaccount/secret.name": "default-token-xxxxx",
  "kubernetes.io/serviceaccount/service-account.name": "default",
  "kubernetes.io/serviceaccount/service-account.uid": "...",
  "sub": "system:serviceaccount:default:default"
}
No exp claim → NEVER expires → stolen token is valid forever
```

**Bound Service Account Token (1.22+ default, 1.20+ opt-in) — SECURE:**
```
JWT payload:
{
  "aud": ["https://kubernetes.default.svc.cluster.local"],
  "exp": 1704067200,    # expires in 1hr (default) or configurable
  "iat": 1704063600,
  "iss": "https://kubernetes.default.svc.cluster.local",
  "kubernetes.io": {
    "namespace": "production",
    "pod": {
      "name": "my-pod-xxxx",
      "uid": "550e8400-e29b-41d4-a716-446655440000"
    },
    "serviceaccount": {
      "name": "my-svc",
      "uid": "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
    }
  },
  "nbf": 1704063600,
  "sub": "system:serviceaccount:production:my-svc"
}
Token is:
  - audience-bound (aud must match --service-account-audiences)
  - time-bound (exp: 1h default, kubelet rotates before expiry)
  - pod-bound (invalidated when pod is deleted)
  - node-bound (kubelet that requested it)
```

### 3.4 OIDC Authentication — Production Setup

```
User Browser
     │
     │ 1. Authorization Code Flow
     ▼
┌─────────────┐           ┌──────────────────────┐
│  Identity   │◄──────────│  User authenticates  │
│  Provider   │           │  (Okta, Dex, Google) │
│  (OIDC IdP) │──────────►│                      │
└──────┬──────┘           └──────────────────────┘
       │ 2. id_token (JWT signed by IdP)
       ▼
┌─────────────┐
│  kubectl    │  kubectl --token=<id_token>
│  / kubelogin│  or kubeconfig exec credential plugin
└──────┬──────┘
       │ 3. Bearer: <id_token>
       ▼
┌─────────────────────────────────────┐
│  kube-apiserver                     │
│  Validates JWT:                     │
│    - Signature against IdP JWKS URI │
│    - iss == --oidc-issuer-url        │
│    - aud == --oidc-client-id         │
│    - exp not expired                 │
│  Extracts:                          │
│    username = claims[email]          │
│    groups   = claims[groups]         │
└─────────────────────────────────────┘
       │ 4. UserInfo → RBAC
       ▼
  Authorization Decision
```

**Dex OIDC Setup (common production pattern):**
```yaml
# dex-config.yaml
issuer: https://dex.example.com:5556/dex
storage:
  type: kubernetes
  config:
    inCluster: true
web:
  https: 0.0.0.0:5556
  tlsCert: /etc/dex/tls.crt
  tlsKey: /etc/dex/tls.key
connectors:
- type: ldap
  name: LDAP
  id: ldap
  config:
    host: ldap.example.com:636
    rootCAData: <base64-ca>
    bindDN: cn=service-account,dc=example,dc=com
    bindPW: <password>
    userSearch:
      baseDN: ou=users,dc=example,dc=com
      username: uid
      idAttr: uid
      emailAttr: mail
      nameAttr: displayName
    groupSearch:
      baseDN: ou=groups,dc=example,dc=com
      filter: "(objectClass=posixGroup)"
      userAttr: uid
      groupAttr: memberUid
      nameAttr: cn
staticClients:
- id: kubernetes
  secret: <client-secret>
  name: Kubernetes
  redirectURIs:
  - http://localhost:8000
  - http://localhost:18000
```

---

## 4. Authorization — RBAC, ABAC, Webhook, Node

### 4.1 Authorization Chain Architecture

```
Authenticated Request (UserInfo known)
          │
          ▼
┌────────────────────────────────────────────────────────────────┐
│  Authorizer Chain (evaluated in order, first decision wins)    │
│                                                                │
│  1. Node Authorizer                                            │
│     Only for system:node:<nodeName> principal                  │
│     Limits what each node can access:                          │
│       - Only pods SCHEDULED on that node                       │
│       - Only secrets/configmaps referenced by those pods       │
│       - Only node's own Node object                            │
│     Prevents node compromise from accessing other nodes' data  │
│                                                                │
│  2. RBAC Authorizer                                            │
│     Role + RoleBinding (namespace-scoped)                      │
│     ClusterRole + ClusterRoleBinding (cluster-scoped)          │
│     Decision: Allow | Deny | NoOpinion                         │
│     Note: RBAC is purely ALLOW rules. No explicit DENY.        │
│     Absent rule = implicit deny.                               │
│                                                                │
│  3. Webhook Authorizer (optional)                              │
│     SubjectAccessReview sent to external endpoint              │
│     Response: allowed:true/false, reason string                │
│                                                                │
│  Final: If ANY authorizer allows → Allowed                     │
│         If NONE allow → 403 Forbidden                          │
└────────────────────────────────────────────────────────────────┘
```

### 4.2 RBAC — Complete Object Model

```
                    RBAC Object Relationships
                    ─────────────────────────

  ┌──────────────┐     ┌───────────────────────────────────┐
  │ ClusterRole  │     │ Rules:                            │
  │ (cluster or  │────►│   apiGroups: ["apps"]             │
  │  ns scope)   │     │   resources: ["deployments"]      │
  └──────────────┘     │   verbs: ["get","list","watch"]   │
         │             └───────────────────────────────────┘
         │
  ┌──────▼──────────────────────────────────────────────────────┐
  │ ClusterRoleBinding                                          │
  │   subjects:                                                 │
  │     - kind: User        name: alice                        │
  │     - kind: Group       name: team-platform                 │
  │     - kind: ServiceAccount name: my-svc ns: production      │
  │   roleRef:                                                  │
  │     kind: ClusterRole   name: deployment-reader             │
  └─────────────────────────────────────────────────────────────┘

  ┌────────────┐     ┌───────────────────────────────────────┐
  │  Role      │     │ Rules (namespace-scoped):             │
  │ (namespace │────►│   apiGroups: [""]                     │
  │  scoped)   │     │   resources: ["pods","pods/log"]      │
  └────────────┘     │   verbs: ["get","list"]               │
        │            └───────────────────────────────────────┘
        │
  ┌─────▼────────────────────────────────────────────────────┐
  │ RoleBinding  (namespace: production)                     │
  │   subjects:                                              │
  │     - kind: ServiceAccount  name: ci-runner  ns: ci      │
  │   roleRef:                                               │
  │     kind: Role  name: pod-reader                         │
  └──────────────────────────────────────────────────────────┘

  Note: ClusterRoleBinding to a Role is NOT valid.
        RoleBinding can reference a ClusterRole (grants in that NS only).
        This is how you create reusable roles across namespaces.
```

### 4.3 Dangerous RBAC Patterns — Privilege Escalation Paths

```
ESCALATION PATH 1: Pods create → cluster-admin
───────────────────────────────────────────────
User has: pods/create in namespace X
User creates a pod with:
  serviceAccountName: cluster-admin-sa  (if exists)
  OR
  hostPID: true + privileged: true → nsenter -t 1 -a -- bash
→ Full node compromise → access all other pods → steal tokens

ESCALATION PATH 2: secrets/get → service account token theft
──────────────────────────────────────────────────────────────
User has: secrets/get /* in namespace production
User reads secret/default-token → gets SA JWT
→ Uses token to perform SA's RBAC-permitted actions

ESCALATION PATH 3: rolebindings/create → privilege escalation
───────────────────────────────────────────────────────────────
User has: rolebindings/create
User creates RoleBinding: binds themselves to cluster-admin role
→ Escalated if cluster-admin ClusterRole exists (it always does)
K8s blocks this ONLY if --authorization-mode has RBAC escalation prevention
Prevention: You cannot grant permissions you don't have yourself.

ESCALATION PATH 4: exec/portforward → lateral movement
────────────────────────────────────────────────────────
User has: pods/exec in namespace X
User execs into pod → reads /var/run/secrets/ → uses other service account tokens

ESCALATION PATH 5: impersonate → any identity
───────────────────────────────────────────────
User has: users/impersonate or groups/impersonate
User sends: Impersonate-User: system:masters
→ cluster-admin instantly
NEVER grant impersonate except to very specific automation.
```

**RBAC Audit Script — Find Dangerous Permissions:**
```bash
# Find all subjects with cluster-admin
kubectl get clusterrolebindings -o json | jq -r '
  .items[] | 
  select(.roleRef.name == "cluster-admin") |
  .subjects[]? | 
  [.kind, .name, .namespace // "cluster"] | 
  @tsv'

# Find subjects who can create pods
kubectl auth can-i --list --as=system:serviceaccount:production:my-sa

# Find who can access secrets
kubectl get rolebindings,clusterrolebindings --all-namespaces -o json | \
  jq -r '.items[] | 
    select(.rules? // .roleRef) | 
    . as $rb | 
    .subjects[]? | 
    [$rb.metadata.namespace // "cluster", $rb.roleRef.name, .kind, .name] | 
    @tsv' 2>/dev/null

# Check for wildcard resources
kubectl get clusterroles -o json | jq -r '
  .items[] | 
  select(.rules[]?.resources[]? == "*") | 
  .metadata.name'
```

### 4.4 Node Authorizer — How It Works Internally

The Node authorizer is a specialized authorizer that ensures a compromised node cannot access data for pods not scheduled on it. This is a critical isolation boundary.

```
Node Authorizer Rules:
──────────────────────

ALLOW: GET/LIST/WATCH
  - pods (only those bound to this node: spec.nodeName == this node)
  - nodes (only this node's own Node object)
  - services (all — needed for endpoint resolution)
  - endpoints (all — needed for service resolution)
  - configmaps (only those referenced by pods on this node)
  - secrets (only those referenced by pods on this node)
  - persistentvolumeclaims (only those referenced by pods on this node)
  - persistentvolumes (only those referenced by pods on this node)

ALLOW: UPDATE
  - nodes/status (only this node)
  - pods/status (only pods on this node)
  - events (create events about pods on this node)

DENY everything else.

Example attack blocked:
  - Node worker-1 is compromised
  - Attacker tries: GET /api/v1/namespaces/production/secrets/database-password
  - Pod using that secret is on worker-2
  - Node authorizer: "worker-1's pods don't reference this secret" → 403 Forbidden

This is why --authorization-mode=Node,RBAC (not just RBAC) is critical.
```

### 4.5 Webhook Authorization — Implementation

```go
// pkg/auth/webhook_authorizer.go
// External webhook authorizer — receives SubjectAccessReview from API server
package main

import (
	"context"
	"encoding/json"
	"log/slog"
	"net/http"
	"time"

	authorizationv1 "k8s.io/api/authorization/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// Policy engine — replace with OPA/Cedar in production
type PolicyEngine struct {
	rules []AuthzRule
}

type AuthzRule struct {
	SubjectPattern string // regex on username/group
	Namespace      string // "" = all
	Resource       string
	Verbs          []string
	Allow          bool
}

type webhookAuthorizer struct {
	policies *PolicyEngine
	logger   *slog.Logger
}

func (wa *webhookAuthorizer) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "POST only", http.StatusMethodNotAllowed)
		return
	}

	var sar authorizationv1.SubjectAccessReview
	if err := json.NewDecoder(r.Body).Decode(&sar); err != nil {
		http.Error(w, "invalid body", http.StatusBadRequest)
		return
	}

	start := time.Now()
	allowed, reason, err := wa.authorize(r.Context(), &sar)
	elapsed := time.Since(start)

	wa.logger.Info("authz decision",
		"user", sar.Spec.User,
		"groups", sar.Spec.Groups,
		"resource", sar.Spec.ResourceAttributes.Resource,
		"verb", sar.Spec.ResourceAttributes.Verb,
		"namespace", sar.Spec.ResourceAttributes.Namespace,
		"allowed", allowed,
		"reason", reason,
		"latency_ms", elapsed.Milliseconds(),
	)

	sar.Status = authorizationv1.SubjectAccessReviewStatus{
		Allowed: allowed,
		Reason:  reason,
	}
	if err != nil {
		sar.Status.EvaluationError = err.Error()
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(sar)
}

func (wa *webhookAuthorizer) authorize(
	ctx context.Context,
	sar *authorizationv1.SubjectAccessReview,
) (allowed bool, reason string, err error) {
	spec := sar.Spec

	// Non-resource URL (e.g., /healthz)
	if spec.NonResourceAttributes != nil {
		return wa.authorizeNonResource(spec)
	}

	ra := spec.ResourceAttributes
	if ra == nil {
		return false, "missing resource attributes", nil
	}

	// Check all subjects (user + groups)
	subjects := append([]string{spec.User}, spec.Groups...)
	for _, sub := range subjects {
		if a, r := wa.policies.evaluate(sub, ra); a {
			return true, r, nil
		}
	}

	return false, "no matching allow policy", nil
}

func (wa *webhookAuthorizer) authorizeNonResource(
	spec authorizationv1.SubjectAccessReviewSpec,
) (bool, string, error) {
	nra := spec.NonResourceAttributes
	// Allow health checks from any authenticated user
	if nra.Path == "/healthz" || nra.Path == "/readyz" || nra.Path == "/livez" {
		return true, "health endpoint", nil
	}
	return false, "non-resource URL denied", nil
}

func (pe *PolicyEngine) evaluate(
	subject string,
	ra *authorizationv1.ResourceAttributes,
) (bool, string) {
	for _, rule := range pe.rules {
		if !matchesSubject(rule.SubjectPattern, subject) {
			continue
		}
		if rule.Namespace != "" && rule.Namespace != ra.Namespace {
			continue
		}
		if rule.Resource != "*" && rule.Resource != ra.Resource {
			continue
		}
		for _, v := range rule.Verbs {
			if v == "*" || v == ra.Verb {
				if rule.Allow {
					return true, "policy match: " + rule.SubjectPattern
				}
				return false, "explicit deny: " + rule.SubjectPattern
			}
		}
	}
	return false, ""
}

func matchesSubject(pattern, subject string) bool {
	// Simplified — use regexp in production
	return pattern == "*" || pattern == subject
}

func main() {
	engine := &PolicyEngine{
		rules: []AuthzRule{
			{SubjectPattern: "system:masters", Resource: "*", Verbs: []string{"*"}, Allow: true},
			{SubjectPattern: "ci-runner", Namespace: "production",
				Resource: "deployments", Verbs: []string{"get", "list", "patch"}, Allow: true},
		},
	}

	wa := &webhookAuthorizer{
		policies: engine,
		logger:   slog.Default(),
	}

	mux := http.NewServeMux()
	mux.Handle("/authorize", wa)

	srv := &http.Server{
		Addr:         ":8443",
		Handler:      mux,
		ReadTimeout:  5 * time.Second,
		WriteTimeout: 5 * time.Second,
	}

	slog.Info("webhook authorizer listening on :8443")
	if err := srv.ListenAndServeTLS("/etc/webhook/tls.crt", "/etc/webhook/tls.key"); err != nil {
		slog.Error("server failed", "err", err)
	}
}
```

---

## 5. Admission Controllers — Mutating & Validating

### 5.1 Admission Control Pipeline

```
API Server Request Flow (after AuthN + AuthZ)
─────────────────────────────────────────────

  Authenticated + Authorized Request
           │
           ▼
  ┌──────────────────────────────────────────────────────────────┐
  │  MUTATING ADMISSION (run in parallel, then serialized)       │
  │                                                              │
  │  1. MutatingWebhookConfiguration webhooks (order: undefined) │
  │     - Inject sidecars (Istio, Linkerd, Datadog)              │
  │     - Add default SecurityContext                             │
  │     - Inject environment variables                           │
  │     - Modify resource limits                                 │
  │  2. Built-in mutating plugins                                │
  │     - ServiceAccount (add default SA token if missing)       │
  │     - LimitRanger (apply default limits from LimitRange)     │
  │     - DefaultStorageClass                                     │
  │     - DefaultTolerationSeconds                                │
  │                                                              │
  │  Result: Object may be modified (JSONPatch in response)       │
  └──────────────────────────────────────────────────────────────┘
           │ (mutated object)
           ▼
  ┌──────────────────────────────────────────────────────────────┐
  │  SCHEMA VALIDATION (OpenAPI validation against CRD/built-in) │
  └──────────────────────────────────────────────────────────────┘
           │
           ▼
  ┌──────────────────────────────────────────────────────────────┐
  │  VALIDATING ADMISSION (run in parallel)                      │
  │                                                              │
  │  1. ValidatingWebhookConfiguration webhooks                  │
  │     - OPA/Gatekeeper policy evaluation                       │
  │     - Kyverno policy evaluation                              │
  │     - Custom security checks                                 │
  │  2. Built-in validating plugins                              │
  │     - PodSecurity (PSA levels: privileged/baseline/restricted)│
  │     - ResourceQuota (enforce namespace quotas)               │
  │     - NodeRestriction (limit what kubelet can modify)        │
  │     - PersistentVolumeClaimProtection                        │
  │                                                              │
  │  Result: Allow or Deny (any single Deny → 403)               │
  └──────────────────────────────────────────────────────────────┘
           │
           ▼
  ┌─────────────┐
  │  Persist to │
  │    etcd     │
  └─────────────┘
```

### 5.2 Pod Security Admission (PSA) — Replacing PSP

PSP was deprecated in 1.21 and removed in 1.25. PSA is the replacement, but it's less flexible. For production, combine PSA with OPA Gatekeeper or Kyverno.

```
PSA Levels:
──────────────────────────────────────────────────────────────────────

privileged:
  No restrictions. For system namespaces (kube-system).
  Allows: hostPID, hostNetwork, hostPath, privileged containers.

baseline:
  Minimal restrictions. Blocks known privilege escalations.
  Blocks:
    - Privileged containers
    - hostPID, hostIPC
    - hostNetwork
    - hostPath volumes
    - hostPort
    - Linux capabilities: add NET_RAW, SYS_ADMIN, ...
    - AppArmor runtime/default override
    - Seccomp: Unconfined blocked from being explicitly set
    - /proc mount type: Default required
  Allows:
    - Running as root
    - All capabilities not explicitly blocked

restricted:
  Maximally hardened. Following security best practices.
  All baseline restrictions PLUS:
    - Volumes: only projected, secret, configMap, emptyDir, csi, ephemeral
    - Privilege escalation: must be false (allowPrivilegeEscalation: false)
    - Run as non-root: must be true
    - Seccomp: RuntimeDefault or Localhost required
    - Capabilities: must drop ALL, may only add NET_BIND_SERVICE
```

**Namespace-Level PSA Configuration:**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    # enforce: pod is rejected if it violates
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: v1.29

    # audit: violations logged but pod admitted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/audit-version: v1.29

    # warn: warning returned to user on kubectl apply
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/warn-version: v1.29
```

**Global PSA Configuration via AdmissionConfiguration:**
```yaml
# /etc/kubernetes/psa.yaml
apiVersion: apiserver.config.k8s.io/v1
kind: AdmissionConfiguration
plugins:
- name: PodSecurity
  configuration:
    apiVersion: pod-security.admission.config.k8s.io/v1
    kind: PodSecurityConfiguration
    defaults:
      enforce: "baseline"
      enforce-version: "latest"
      audit: "restricted"
      audit-version: "latest"
      warn: "restricted"
      warn-version: "latest"
    exemptions:
      usernames: []
      runtimeClasses: []
      namespaces:
        - kube-system
        - kube-public
        - monitoring  # Prometheus needs hostNetwork
```

### 5.3 Custom Validating Admission Webhook — Go Implementation

This is a production-grade webhook that enforces security policies beyond what PSA provides:

```go
// cmd/security-webhook/main.go
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	admissionv1 "k8s.io/api/admission/v1"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/runtime/serializer"
)

var (
	scheme  = runtime.NewScheme()
	codecs  = serializer.NewCodecFactory(scheme)
	logger  = slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo}))
)

func init() {
	_ = corev1.AddToScheme(scheme)
	_ = admissionv1.AddToScheme(scheme)
}

// PolicyViolation describes a specific policy failure
type PolicyViolation struct {
	Policy      string
	Container   string
	Description string
	Severity    string // critical, high, medium
}

func (v PolicyViolation) Error() string {
	return fmt.Sprintf("[%s] %s/%s: %s", v.Severity, v.Policy, v.Container, v.Description)
}

// SecurityPolicyChecker enforces security policies on pods
type SecurityPolicyChecker struct {
	// AllowedRegistries: only images from these registries allowed
	AllowedRegistries []string
	// RequiredLabels: pods must have these labels
	RequiredLabels []string
	// BlockedCapabilities: these capabilities are never allowed
	BlockedCapabilities []corev1.Capability
	// RequireReadOnlyRootFS: all containers must have readOnlyRootFilesystem
	RequireReadOnlyRootFS bool
	// RequireNonRoot: all containers must run as non-root
	RequireNonRoot bool
	// AllowedSeccompProfiles: allowed seccomp profile types
	AllowedSeccompProfiles []corev1.SeccompProfileType
}

func NewProductionPolicyChecker() *SecurityPolicyChecker {
	return &SecurityPolicyChecker{
		AllowedRegistries:   []string{"registry.example.com", "gcr.io/distroless"},
		RequiredLabels:      []string{"app.kubernetes.io/name", "app.kubernetes.io/version"},
		BlockedCapabilities: []corev1.Capability{"NET_RAW", "SYS_ADMIN", "SYS_PTRACE", "DAC_OVERRIDE"},
		RequireReadOnlyRootFS: true,
		RequireNonRoot:       true,
		AllowedSeccompProfiles: []corev1.SeccompProfileType{
			corev1.SeccompProfileTypeRuntimeDefault,
			corev1.SeccompProfileTypeLocalhost,
		},
	}
}

func (pc *SecurityPolicyChecker) Validate(pod *corev1.Pod) []PolicyViolation {
	var violations []PolicyViolation

	// Check required labels
	for _, label := range pc.RequiredLabels {
		if _, ok := pod.Labels[label]; !ok {
			violations = append(violations, PolicyViolation{
				Policy:      "required-labels",
				Description: fmt.Sprintf("missing required label: %s", label),
				Severity:    "medium",
			})
		}
	}

	// Check pod-level security context
	psc := pod.Spec.SecurityContext
	if psc != nil {
		if psc.RunAsRoot() {
			violations = append(violations, PolicyViolation{
				Policy:      "no-root",
				Description: "pod securityContext explicitly runs as root (runAsUser=0)",
				Severity:    "critical",
			})
		}
	}

	// Check host namespaces
	if pod.Spec.HostPID {
		violations = append(violations, PolicyViolation{
			Policy:      "no-host-namespaces",
			Description: "hostPID: true is not allowed",
			Severity:    "critical",
		})
	}
	if pod.Spec.HostIPC {
		violations = append(violations, PolicyViolation{
			Policy:      "no-host-namespaces",
			Description: "hostIPC: true is not allowed",
			Severity:    "critical",
		})
	}
	if pod.Spec.HostNetwork {
		violations = append(violations, PolicyViolation{
			Policy:      "no-host-network",
			Description: "hostNetwork: true is not allowed",
			Severity:    "critical",
		})
	}

	// Check all containers (init + regular + ephemeral)
	allContainers := append(pod.Spec.InitContainers, pod.Spec.Containers...)
	for _, c := range allContainers {
		v := pc.validateContainer(pod, c)
		violations = append(violations, v...)
	}

	return violations
}

func (pc *SecurityPolicyChecker) validateContainer(
	pod *corev1.Pod,
	c corev1.Container,
) []PolicyViolation {
	var violations []PolicyViolation

	// Registry check
	if !pc.isAllowedImage(c.Image) {
		violations = append(violations, PolicyViolation{
			Policy:      "allowed-registries",
			Container:   c.Name,
			Description: fmt.Sprintf("image %q is not from an allowed registry", c.Image),
			Severity:    "critical",
		})
	}

	// Image must have digest, not just tag (prevents tag mutation)
	if !strings.Contains(c.Image, "@sha256:") {
		violations = append(violations, PolicyViolation{
			Policy:      "image-digest",
			Container:   c.Name,
			Description: fmt.Sprintf("image %q must use digest (@sha256:...), not just tag", c.Image),
			Severity:    "high",
		})
	}

	sc := c.SecurityContext
	if sc == nil {
		violations = append(violations, PolicyViolation{
			Policy:      "security-context-required",
			Container:   c.Name,
			Description: "container has no securityContext",
			Severity:    "critical",
		})
		return violations // can't validate further without SC
	}

	// Privileged check
	if sc.Privileged != nil && *sc.Privileged {
		violations = append(violations, PolicyViolation{
			Policy:      "no-privileged",
			Container:   c.Name,
			Description: "privileged: true is not allowed",
			Severity:    "critical",
		})
	}

	// Privilege escalation
	if sc.AllowPrivilegeEscalation == nil || *sc.AllowPrivilegeEscalation {
		violations = append(violations, PolicyViolation{
			Policy:      "no-privilege-escalation",
			Container:   c.Name,
			Description: "allowPrivilegeEscalation must be explicitly set to false",
			Severity:    "high",
		})
	}

	// Read-only root filesystem
	if pc.RequireReadOnlyRootFS && (sc.ReadOnlyRootFilesystem == nil || !*sc.ReadOnlyRootFilesystem) {
		violations = append(violations, PolicyViolation{
			Policy:      "readonly-rootfs",
			Container:   c.Name,
			Description: "readOnlyRootFilesystem must be true",
			Severity:    "high",
		})
	}

	// Non-root
	if pc.RequireNonRoot {
		if sc.RunAsNonRoot == nil || !*sc.RunAsNonRoot {
			violations = append(violations, PolicyViolation{
				Policy:      "non-root",
				Container:   c.Name,
				Description: "runAsNonRoot must be true",
				Severity:    "high",
			})
		}
		if sc.RunAsUser != nil && *sc.RunAsUser == 0 {
			violations = append(violations, PolicyViolation{
				Policy:      "non-root",
				Container:   c.Name,
				Description: "runAsUser: 0 (root) is not allowed",
				Severity:    "critical",
			})
		}
	}

	// Capabilities
	if sc.Capabilities != nil {
		for _, cap := range sc.Capabilities.Add {
			for _, blocked := range pc.BlockedCapabilities {
				if cap == blocked {
					violations = append(violations, PolicyViolation{
						Policy:      "blocked-capabilities",
						Container:   c.Name,
						Description: fmt.Sprintf("capability %s is blocked", cap),
						Severity:    "critical",
					})
				}
			}
		}
		// Must drop ALL
		hasDropAll := false
		for _, cap := range sc.Capabilities.Drop {
			if cap == "ALL" {
				hasDropAll = true
				break
			}
		}
		if !hasDropAll {
			violations = append(violations, PolicyViolation{
				Policy:      "drop-all-caps",
				Container:   c.Name,
				Description: "capabilities.drop must include ALL",
				Severity:    "high",
			})
		}
	} else {
		violations = append(violations, PolicyViolation{
			Policy:      "capabilities-required",
			Container:   c.Name,
			Description: "securityContext.capabilities not set; must drop ALL",
			Severity:    "high",
		})
	}

	// Seccomp (pod-level or container-level)
	if sc.SeccompProfile != nil {
		if !pc.isAllowedSeccompProfile(sc.SeccompProfile.Type) {
			violations = append(violations, PolicyViolation{
				Policy:      "seccomp-profile",
				Container:   c.Name,
				Description: fmt.Sprintf("seccomp profile %s is not allowed", sc.SeccompProfile.Type),
				Severity:    "high",
			})
		}
	} else if pod.Spec.SecurityContext == nil || pod.Spec.SecurityContext.SeccompProfile == nil {
		violations = append(violations, PolicyViolation{
			Policy:      "seccomp-required",
			Container:   c.Name,
			Description: "seccomp profile not set at container or pod level",
			Severity:    "high",
		})
	}

	return violations
}

func (pc *SecurityPolicyChecker) isAllowedImage(image string) bool {
	for _, reg := range pc.AllowedRegistries {
		if strings.HasPrefix(image, reg) {
			return true
		}
	}
	return false
}

func (pc *SecurityPolicyChecker) isAllowedSeccompProfile(t corev1.SeccompProfileType) bool {
	for _, allowed := range pc.AllowedSeccompProfiles {
		if t == allowed {
			return true
		}
	}
	return false
}

// HTTP handler
type admissionHandler struct {
	checker *SecurityPolicyChecker
}

func (ah *admissionHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	body := make([]byte, r.ContentLength)
	if _, err := r.Body.Read(body); err != nil && r.ContentLength > 0 {
		http.Error(w, "read error", http.StatusBadRequest)
		return
	}

	var ar admissionv1.AdmissionReview
	if _, _, err := codecs.UniversalDeserializer().Decode(body, nil, &ar); err != nil {
		logger.Error("decode error", "err", err)
		http.Error(w, "decode error", http.StatusBadRequest)
		return
	}

	response := ah.handle(ar.Request)
	ar.Response = response
	ar.Response.UID = ar.Request.UID

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(ar); err != nil {
		logger.Error("encode error", "err", err)
	}
}

func (ah *admissionHandler) handle(req *admissionv1.AdmissionRequest) *admissionv1.AdmissionResponse {
	// Only handle Pod resources
	if req.Kind.Kind != "Pod" {
		return &admissionv1.AdmissionResponse{Allowed: true}
	}

	var pod corev1.Pod
	if err := json.Unmarshal(req.Object.Raw, &pod); err != nil {
		logger.Error("unmarshal pod", "err", err)
		return deny("internal error: could not parse pod")
	}

	violations := ah.checker.Validate(&pod)

	if len(violations) == 0 {
		logger.Info("pod admitted",
			"name", req.Name,
			"namespace", req.Namespace,
		)
		return &admissionv1.AdmissionResponse{Allowed: true}
	}

	// Aggregate violations into message
	var msgs []string
	for _, v := range violations {
		msgs = append(msgs, v.Error())
		logger.Warn("policy violation",
			"policy", v.Policy,
			"container", v.Container,
			"severity", v.Severity,
			"pod", req.Name,
			"namespace", req.Namespace,
		)
	}

	return deny(fmt.Sprintf("Security policy violations:\n%s", strings.Join(msgs, "\n")))
}

func deny(msg string) *admissionv1.AdmissionResponse {
	return &admissionv1.AdmissionResponse{
		Allowed: false,
		Result: &metav1.Status{
			Code:    http.StatusForbidden,
			Message: msg,
		},
	}
}

func main() {
	checker := NewProductionPolicyChecker()
	handler := &admissionHandler{checker: checker}

	mux := http.NewServeMux()
	mux.Handle("/validate", handler)
	mux.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("ok"))
	})

	srv := &http.Server{
		Addr:         ":8443",
		Handler:      mux,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGTERM, syscall.SIGINT)
	defer stop()

	go func() {
		logger.Info("security webhook listening on :8443")
		if err := srv.ListenAndServeTLS("/etc/webhook/tls.crt", "/etc/webhook/tls.key"); err != nil &&
			err != http.ErrServerClosed {
			logger.Error("server error", "err", err)
			os.Exit(1)
		}
	}()

	<-ctx.Done()
	logger.Info("shutting down")
	shutCtx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()
	_ = srv.Shutdown(shutCtx)
}
```

**Webhook Registration:**
```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: security-policy-webhook
  annotations:
    # cert-manager injects the CA bundle
    cert-manager.io/inject-ca-from: security-system/webhook-cert
webhooks:
- name: pods.security.example.com
  admissionReviewVersions: ["v1"]
  clientConfig:
    service:
      name: security-webhook
      namespace: security-system
      port: 8443
      path: /validate
    # caBundle injected by cert-manager
  rules:
  - apiGroups: [""]
    apiVersions: ["v1"]
    operations: ["CREATE", "UPDATE"]
    resources: ["pods"]
    scope: "Namespaced"
  namespaceSelector:
    matchExpressions:
    - key: pod-security.kubernetes.io/enforce
      operator: In
      values: ["restricted", "baseline"]
  failurePolicy: Fail          # CRITICAL: Fail means deny if webhook unavailable
  sideEffects: None
  timeoutSeconds: 10
```

**Critical failurePolicy consideration:**
```
failurePolicy: Fail   → If webhook is down, ALL pods rejected (safe but operational risk)
failurePolicy: Ignore → If webhook is down, pods admitted (availability over security)

Production recommendation:
  - Run webhook with 3+ replicas
  - Use PodDisruptionBudget (minAvailable: 2)
  - Use failurePolicy: Fail
  - Monitor webhook availability as P1 alert
  - Use topologySpreadConstraints across zones
```

---

## 6. etcd Security

### 6.1 etcd Data Model — What Lives Where

```
etcd Key Namespace (real paths in a production cluster):
──────────────────────────────────────────────────────────

/registry/
├── apiregistration.k8s.io/apiservices/
│   └── v1.apps  → API service registration
├── clusterrolebindings/
│   └── cluster-admin  → JSON of ClusterRoleBinding object
├── clusterroles/
│   └── cluster-admin
├── configmaps/
│   └── kube-system/
│       ├── kube-proxy
│       └── kubeadm-config  ← cluster bootstrap config
├── deployments/
│   └── production/
│       └── my-app
├── events/
│   └── production/
│       └── my-pod.event-xxxx
├── namespaces/
│   ├── production
│   └── kube-system
├── pods/
│   └── production/
│       └── my-pod-abc123
├── secrets/
│   └── production/
│       ├── database-password   ← k8s:enc:aescbc:v1:key1:<encrypted>
│       └── tls-cert
├── serviceaccounts/
│   └── production/
│       └── my-service-account
└── services/
    └── specs/
        └── production/
            └── my-svc

Value format (unencrypted): application/vnd.kubernetes.protobuf
Value format (encrypted):   k8s:enc:aescbc:v1:key1:<nonce><ciphertext>
```

### 6.2 etcd Access Controls

```
┌─────────────────────────────────────────────────────────────────────┐
│  etcd Access Control Model                                          │
│                                                                     │
│  etcd has its OWN user/role model (separate from K8s RBAC)         │
│                                                                     │
│  etcd Roles:                                                        │
│    root    - all permissions on all keys                            │
│    readwrite - read+write on specific key prefixes                  │
│    readonly  - read-only on specific key prefixes                   │
│                                                                     │
│  In K8s, etcd auth is via mTLS cert CN, not etcd users.             │
│  API server cert CN is trusted as root-equivalent.                  │
│                                                                     │
│  Important: etcd RBAC is SEPARATE from K8s RBAC.                   │
│  If etcd's own auth is disabled (--no-client-cert-auth), then       │
│  anyone with network access to :2379 can read all secrets.          │
│                                                                     │
│  Defense:                                                           │
│  1. etcd only listens on loopback or dedicated mgmt network         │
│  2. mTLS required for both client and peer ports                    │
│  3. Host firewall: iptables -A INPUT -p tcp --dport 2379            │
│       -s 10.0.1.0/24 -j ACCEPT && -j DROP                          │
│  4. Encryption-at-rest for secrets                                  │
│  5. etcd nodes in separate security group/zone                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 7. TLS Everywhere — PKI Architecture

### 7.1 Kubernetes PKI Certificate Hierarchy

```
Kubernetes Certificate Authority Structure (kubeadm-generated):
───────────────────────────────────────────────────────────────

/etc/kubernetes/pki/
│
├── ca.crt / ca.key            ← ROOT CA for cluster
│   Issued to: kubernetes      Serial: 0x...
│   Signs:
│     ├── apiserver.crt                (API server TLS serving cert)
│     │   SAN: kubernetes, kubernetes.default, kubernetes.default.svc
│     │       kubernetes.default.svc.cluster.local, 10.96.0.1, <master-IP>
│     ├── apiserver-kubelet-client.crt (API server → kubelet auth)
│     │   CN: kube-apiserver-kubelet-client, O: system:masters
│     ├── controller-manager.crt       CN: system:kube-controller-manager
│     ├── scheduler.crt                CN: system:kube-scheduler
│     └── [kubelet certs per node]     CN: system:node:<nodename>, O: system:nodes
│
├── etcd/
│   ├── ca.crt / ca.key        ← SEPARATE etcd CA (best practice)
│   │   Signs:
│   │     ├── server.crt       (etcd server TLS — SANs: etcd-node IPs)
│   │     ├── peer.crt         (etcd peer TLS)
│   │     └── healthcheck-client.crt
│   └── apiserver-etcd-client.crt   ← API server's etcd client cert
│       CN: kube-apiserver-etcd-client, O: system:masters
│
├── front-proxy-ca.crt / key   ← Separate CA for aggregation layer
│   Signs:
│     └── front-proxy-client.crt
│         CN: front-proxy-client
│
└── sa.key / sa.pub            ← Service Account signing keypair (NOT a cert)
    RSA-2048 or ECDSA P-256
    Used to sign/verify service account JWTs
    (API server uses sa.key to sign, verifies with sa.pub)

Certificate lifetimes (kubeadm default):
  CA certificates:      10 years
  Component certs:       1 year (auto-rotated by kubeadm certs renew)
  Node client certs:     1 year (auto-rotated by kubelet)
  Bound SA tokens:       1 hour (rotated by kubelet)
```

### 7.2 Certificate Rotation

```bash
# Check expiry for all control plane certs
kubeadm certs check-expiration
# Output:
# CERTIFICATE                EXPIRES                  RESIDUAL TIME   CERTIFICATE AUTHORITY
# admin.conf                 Dec 15, 2024 10:00 UTC   364d            ca
# apiserver                  Dec 15, 2024 10:00 UTC   364d            ca
# apiserver-etcd-client      Dec 15, 2024 10:00 UTC   364d            etcd-ca
# apiserver-kubelet-client   Dec 15, 2024 10:00 UTC   364d            ca
# controller-manager.conf    Dec 15, 2024 10:00 UTC   364d            ca
# etcd-healthcheck-client    Dec 15, 2024 10:00 UTC   364d            etcd-ca
# etcd-peer                  Dec 15, 2024 10:00 UTC   364d            etcd-ca
# etcd-server                Dec 15, 2024 10:00 UTC   364d            etcd-ca
# front-proxy-client         Dec 15, 2024 10:00 UTC   364d            front-proxy-ca
# scheduler.conf             Dec 15, 2024 10:00 UTC   364d            ca

# Renew all (before expiry — do this annually or automate)
kubeadm certs renew all

# Verify new cert
openssl x509 -in /etc/kubernetes/pki/apiserver.crt -noout -enddate -subject -issuer
```

### 7.3 Go: mTLS Client Implementation for Kubernetes API

```go
// pkg/k8sclient/mtls.go
// mTLS client that authenticates to kube-apiserver using X.509 certs
package k8sclient

import (
	"crypto/tls"
	"crypto/x509"
	"fmt"
	"net/http"
	"os"
	"time"
)

type MTLSConfig struct {
	CACertFile     string // /etc/kubernetes/pki/ca.crt
	ClientCertFile string // client cert signed by K8s CA
	ClientKeyFile  string // client private key
	APIServerURL   string // https://10.0.1.10:6443
}

// NewMTLSHTTPClient creates an HTTP client with mTLS configured for K8s API access.
// The client cert CN must match an existing K8s user or service account.
func NewMTLSHTTPClient(cfg MTLSConfig) (*http.Client, error) {
	// Load client cert+key
	clientCert, err := tls.LoadX509KeyPair(cfg.ClientCertFile, cfg.ClientKeyFile)
	if err != nil {
		return nil, fmt.Errorf("load client cert: %w", err)
	}

	// Load CA cert pool
	caCert, err := os.ReadFile(cfg.CACertFile)
	if err != nil {
		return nil, fmt.Errorf("read CA cert: %w", err)
	}
	caPool := x509.NewCertPool()
	if !caPool.AppendCertsFromPEM(caCert) {
		return nil, fmt.Errorf("failed to parse CA cert")
	}

	// Inspect the client cert for debugging
	if len(clientCert.Certificate) > 0 {
		leaf, err := x509.ParseCertificate(clientCert.Certificate[0])
		if err == nil {
			fmt.Printf("Client cert: CN=%s, O=%v, expires=%s\n",
				leaf.Subject.CommonName,
				leaf.Subject.Organization,
				leaf.NotAfter.Format(time.RFC3339),
			)
			// Warn if cert expires within 7 days
			if time.Until(leaf.NotAfter) < 7*24*time.Hour {
				fmt.Printf("WARNING: client cert expires in %s\n",
					time.Until(leaf.NotAfter).Round(time.Hour))
			}
		}
	}

	tlsConfig := &tls.Config{
		Certificates: []tls.Certificate{clientCert},
		RootCAs:      caPool,
		MinVersion:   tls.VersionTLS13,
		CurvePreferences: []tls.CurveID{
			tls.X25519,
			tls.CurveP256,
		},
	}

	transport := &http.Transport{
		TLSClientConfig:     tlsConfig,
		MaxIdleConns:        100,
		MaxIdleConnsPerHost: 10,
		IdleConnTimeout:     90 * time.Second,
		TLSHandshakeTimeout: 10 * time.Second,
	}

	return &http.Client{
		Transport: transport,
		Timeout:   30 * time.Second,
	}, nil
}

// TokenClient creates an HTTP client that authenticates with a Bearer token
// (for service account token auth)
func NewTokenClient(caCertFile, token, apiServerURL string) (*http.Client, error) {
	caCert, err := os.ReadFile(caCertFile)
	if err != nil {
		return nil, fmt.Errorf("read CA: %w", err)
	}
	caPool := x509.NewCertPool()
	if !caPool.AppendCertsFromPEM(caCert) {
		return nil, fmt.Errorf("parse CA")
	}

	return &http.Client{
		Transport: &bearerTokenTransport{
			token: token,
			inner: &http.Transport{
				TLSClientConfig: &tls.Config{
					RootCAs:    caPool,
					MinVersion: tls.VersionTLS13,
				},
			},
		},
		Timeout: 30 * time.Second,
	}, nil
}

type bearerTokenTransport struct {
	token string
	inner http.RoundTripper
}

func (t *bearerTokenTransport) RoundTrip(req *http.Request) (*http.Response, error) {
	// Clone request to avoid modifying original
	r := req.Clone(req.Context())
	r.Header.Set("Authorization", "Bearer "+t.token)
	return t.inner.RoundTrip(r)
}
```

---

## 8. Pod Security — Namespaces, Capabilities, Seccomp, AppArmor, SELinux

### 8.1 Linux Namespaces — How Container Isolation Works

```
Linux Namespace Types and What They Isolate:
────────────────────────────────────────────

PID namespace:
  Container process tree is isolated from host.
  PID 1 in container ≠ PID 1 on host (init/systemd).
  Container PID 1 = actual host PID e.g. 12453.
  hostPID: true destroys this isolation.
  Attack: if hostPID:true, process can kill host processes, read /proc/<pid>/mem

Network namespace:
  Each pod gets its own network stack:
    - eth0 (veth pair to bridge)
    - lo
    - iptables rules
  hostNetwork: true means pod shares host's TCP stack.
  Attack: if hostNetwork:true, pod can bind to any host port, sniff host traffic

Mount namespace:
  Pod has isolated filesystem view.
  hostPath volumes punch holes through this.
  Attack: hostPath:/etc mounted into pod → read/modify host config files

UTS namespace:
  Isolated hostname/domainname.
  hostUTS: true → pod can change host's hostname.

IPC namespace:
  Isolated SysV IPC, POSIX message queues.
  hostIPC: true → pod can access host's shared memory segments.
  Attack: read/write memory of other processes using same IPC namespace.

User namespace:
  Map UIDs/GIDs (root in container ≠ root on host).
  NOT enabled by default in K8s (requires UserNamespacesSupport feature gate).
  When enabled: UID 0 in container → UID 65536+N on host.
  This is the strongest isolation — K8s 1.30 beta, production-ready in 1.31+.
```

**Namespace Isolation Verification:**
```bash
# From inside a pod — verify isolation
cat /proc/1/status | grep NSpid
# NSpid: 1 <-- PID 1 inside container
# (on host, this process has a different PID)

# From host — find container's PIDs
crictl ps  # get container ID
crictl inspect <container-id> | jq '.info.pid'
# 12453  <-- actual host PID
ls -la /proc/12453/ns/
# lrwxrwxrwx net -> net:[4026532123]   <-- unique namespace inode
# lrwxrwxrwx pid -> pid:[4026532124]
# (compare to host: ls /proc/1/ns/)
```

### 8.2 Linux Capabilities — Full Reference

```
Capabilities divide root's privileges into ~40 distinct units.
A process can have capabilities without being uid=0.

Capabilities critical to Kubernetes security:

CAP_SYS_ADMIN  ← The "new root"
  - Mount filesystems (escape container via bind mount)
  - Load kernel modules (arbitrary kernel code)
  - ptrace any process (read memory of any process)
  - Bypass DAC for almost everything
  - nsenter, unshare system calls
  NEVER grant in production.

CAP_NET_RAW    ← Network attacks
  - Create raw sockets (send arbitrary IP packets)
  - ARP spoofing, ICMP amplification, traffic sniffing
  - Bypass NetworkPolicy via raw sockets
  Drop this cap — most apps don't need it.
  K8s adds this by default — PSA restricted removes it.

CAP_NET_ADMIN
  - Configure network interfaces
  - Modify routing tables
  - Configure iptables
  Only needed for CNI plugins, network operators.

CAP_SYS_PTRACE
  - ptrace() any process (same/other user)
  - Access /proc/<pid>/mem
  - Debug and modify running processes
  Attack: exec into pod with SYS_PTRACE → ptrace other pods on same node.

CAP_DAC_OVERRIDE
  - Bypass file read/write/execute permission checks
  - Read any file on the filesystem regardless of permissions.

CAP_SETUID / CAP_SETGID
  - Change UID/GID to any value including 0 (root).
  - Exploit: setuid(0) → full root.

CAP_SYS_BOOT      - Reboot the system
CAP_SYS_MODULE    - Load/unload kernel modules → arbitrary kernel code
CAP_SYS_CHROOT    - Use chroot() → filesystem escape if combined with other caps
CAP_MKNOD         - Create device files → /dev/mem etc.
CAP_AUDIT_WRITE   - Write to kernel audit log (can flood audit subsystem)

Default Kubernetes capabilities (bitmask 0x00000000a80425fb):
  AUDIT_WRITE, CHOWN, DAC_OVERRIDE, FOWNER, FSETID, KILL,
  MKNOD, NET_BIND_SERVICE, NET_RAW, SETFCAP, SETGID, SETPCAP,
  SETUID, SYS_CHROOT

Production pod should drop ALL, add only what's needed:
  capabilities:
    drop: [ALL]
    add:  [NET_BIND_SERVICE]   # if binding to port < 1024
```

### 8.3 Seccomp — System Call Filtering

```
Seccomp (secure computing mode) limits which syscalls a process can make.
A seccomp filter is a BPF program loaded into the kernel.

When a filtered syscall is called:
  - SECCOMP_RET_ALLOW  → proceed normally
  - SECCOMP_RET_ERRNO  → return error (EPERM or custom)
  - SECCOMP_RET_KILL   → kill the process with SIGSYS
  - SECCOMP_RET_TRAP   → deliver SIGTRAP (used for debugging)

Container escape syscalls blocked by RuntimeDefault:
  - mount()           → can't remount or bind-mount
  - pivot_root()      → can't change root filesystem
  - ptrace()          → can't trace other processes
  - init_module()     → can't load kernel modules
  - kexec_load()      → can't load new kernel
  - syslog()          → can't read kernel logs
  - acct()            → can't enable process accounting
  - settimeofday()    → can't change system time
  - reboot()          → can't reboot
  - clock_adjtime()   → can't adjust clock
  - nfsservctl()      → deprecated NFS server call
  - vm86()            → x86 virtual 8086 mode

Kubernetes Seccomp Profile Types:
  RuntimeDefault    → Use container runtime's default profile (containerd/runc)
                      This is the OCI default seccomp profile (~300 allowed syscalls)
  Localhost         → Load profile from /var/lib/kubelet/seccomp/<path>
  Unconfined        → No filtering (insecure, should never be used)
```

**Custom Seccomp Profile (deny-all + allow list approach):**
```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64", "SCMP_ARCH_X86", "SCMP_ARCH_X32"],
  "syscalls": [
    {
      "names": [
        "accept4", "arch_prctl", "bind", "brk", "close", "connect",
        "dup2", "epoll_create1", "epoll_ctl", "epoll_wait", "epoll_pwait",
        "exit", "exit_group", "fcntl", "fstat", "futex", "getcwd",
        "getdents64", "getegid", "geteuid", "getgid", "getpid",
        "getppid", "getrandom", "getuid", "ioctl", "listen",
        "lseek", "madvise", "mmap", "mprotect", "munmap",
        "nanosleep", "newfstatat", "open", "openat", "poll",
        "prctl", "pread64", "pwrite64", "read", "readlink",
        "recvfrom", "recvmsg", "rt_sigaction", "rt_sigprocmask",
        "rt_sigreturn", "sched_getaffinity", "sched_yield",
        "sendmsg", "sendto", "set_robust_list", "set_tid_address",
        "setgid", "setgroups", "setuid", "sigaltstack", "socket",
        "stat", "statfs", "sysinfo", "tgkill", "uname",
        "wait4", "write", "writev"
      ],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
```

```yaml
# Pod spec using custom seccomp profile
apiVersion: v1
kind: Pod
spec:
  securityContext:
    seccompProfile:
      type: Localhost
      localhostProfile: profiles/my-app-strict.json  # relative to /var/lib/kubelet/seccomp/
  containers:
  - name: app
    securityContext:
      seccompProfile:
        type: RuntimeDefault  # container-level overrides pod-level
```

### 8.4 AppArmor — Mandatory Access Control Profiles

```
AppArmor is an LSM (Linux Security Module) that implements MAC.
Profiles are path-based (vs SELinux which is label-based).
Loaded into kernel: aa-status shows loaded profiles.

AppArmor modes:
  enforce  → violations are blocked and logged
  complain → violations only logged (use for profiling)

Profile for a Go HTTP server (deny file writes outside /tmp):
```

```
# /etc/apparmor.d/containers/go-http-server
#include <tunables/global>

profile go-http-server flags=(attach_disconnected) {
  #include <abstractions/base>

  # Network
  network inet tcp,
  network inet udp,
  network inet6 tcp,

  # Allow reading own binary and libraries
  /usr/local/bin/server   mr,
  /lib/**                 mr,
  /usr/lib/**             mr,

  # Allow /proc (limited)
  /proc/sys/kernel/hostname r,
  /proc/@{pid}/status       r,

  # Temp files
  /tmp/**                rw,

  # Deny everything else
  deny /etc/**           w,
  deny /var/run/**       w,
  deny /sys/**           w,
  deny @{HOME}/**        rw,
  deny /root/**          rw,
}
```

```yaml
# Apply to pod (K8s 1.30+ uses securityContext.appArmorProfile, pre-1.30 uses annotations)
apiVersion: v1
kind: Pod
metadata:
  annotations:
    # Pre-1.30 syntax
    container.apparmor.security.beta.kubernetes.io/app: localhost/go-http-server
spec:
  containers:
  - name: app
    securityContext:
      # 1.30+ syntax (beta)
      appArmorProfile:
        type: Localhost
        localhostProfile: go-http-server
```

### 8.5 SELinux — Label-Based MAC

```
SELinux uses labels (contexts) on every object (file, process, socket).
Policy defines which context can access which other context.
More powerful than AppArmor, but more complex.

SELinux context format:  user:role:type:level
  Example:  system_u:system_r:container_t:s0:c123,c456
  The "type" is the policy-enforced domain.

container_t     → default container domain (confined)
container_init_t → container init process
svirt_lxc_net_t → network-enabled container

For K8s pods:
```
```yaml
securityContext:
  seLinuxOptions:
    user:  "system_u"
    role:  "system_r"
    type:  "container_t"   # most restrictive container domain
    level: "s0:c123,c456"  # MLS level (Multi-Level Security)
```

### 8.6 Production Security Context — Complete Pod Spec

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: hardened-app
  namespace: production
  labels:
    app.kubernetes.io/name: hardened-app
    app.kubernetes.io/version: "1.2.3"
spec:
  # Pod-level security context
  securityContext:
    runAsNonRoot: true
    runAsUser: 10001
    runAsGroup: 10001
    fsGroup: 10001
    fsGroupChangePolicy: OnRootMismatch  # performance: only chown if needed
    seccompProfile:
      type: RuntimeDefault
    supplementalGroups: []
    sysctls: []  # never modify kernel params in pods

  # Node selection — don't run next to untrusted workloads
  nodeSelector:
    node-role.kubernetes.io/worker: "true"
    security-tier: "high"

  # Don't mount default service account token unless needed
  automountServiceAccountToken: false

  # Use dedicated SA with minimal permissions if API access needed
  serviceAccountName: hardened-app

  # No host namespace sharing
  hostPID: false
  hostIPC: false
  hostNetwork: false

  # Priority class for eviction behavior
  priorityClassName: high-priority

  containers:
  - name: app
    image: registry.example.com/hardened-app@sha256:abc123...  # digest pinned
    imagePullPolicy: Always  # Always re-validate with registry

    securityContext:
      runAsNonRoot: true
      runAsUser: 10001
      runAsGroup: 10001
      allowPrivilegeEscalation: false
      privileged: false
      readOnlyRootFilesystem: true
      capabilities:
        drop: [ALL]
        add:  []  # add NET_BIND_SERVICE only if binding <1024
      seccompProfile:
        type: RuntimeDefault
      # SELinux
      seLinuxOptions:
        type: container_t
        level: "s0:c100,c200"
      # AppArmor (1.30+)
      appArmorProfile:
        type: RuntimeDefault

    # Resource limits — prevent resource exhaustion DoS
    resources:
      requests:
        cpu: "100m"
        memory: "128Mi"
      limits:
        cpu: "500m"
        memory: "256Mi"
        # ephemeral-storage prevents disk exhaustion
        ephemeral-storage: "1Gi"

    # Writable directories via emptyDir (since rootfs is read-only)
    volumeMounts:
    - name: tmp
      mountPath: /tmp
    - name: cache
      mountPath: /app/cache
    - name: secrets
      mountPath: /etc/secrets
      readOnly: true

    # Liveness/Readiness — don't use exec probes (creates subprocess)
    livenessProbe:
      httpGet:
        path: /healthz
        port: 8080
        scheme: HTTP
      initialDelaySeconds: 10
      periodSeconds: 30
      failureThreshold: 3

    ports:
    - containerPort: 8080
      protocol: TCP
      name: http

  volumes:
  - name: tmp
    emptyDir:
      medium: Memory  # tmpfs — not persisted to disk
      sizeLimit: 64Mi
  - name: cache
    emptyDir:
      sizeLimit: 256Mi
  - name: secrets
    projected:
      sources:
      - secret:
          name: app-secrets
          items:
          - key: db-password
            path: db-password
            mode: 0400  # owner read-only
      - serviceAccountToken:
          audience: "https://my-api.example.com"
          expirationSeconds: 3600  # 1 hour
          path: sa-token

  # Security: prevent scheduling on nodes with taint
  tolerations: []

  # Spread across zones
  topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: topology.kubernetes.io/zone
    whenUnsatisfiable: DoNotSchedule
    labelSelector:
      matchLabels:
        app.kubernetes.io/name: hardened-app

  imagePullSecrets:
  - name: registry-credentials
```

---

## 9. Network Policy & Micro-Segmentation

### 9.1 Network Policy Architecture

```
Without NetworkPolicy: All pods can reach all pods in the cluster.
This is a flat, open network — catastrophic for multi-tenant clusters.

With NetworkPolicy: Default-deny, then explicitly allow required flows.

NetworkPolicy is enforced by the CNI plugin:
  - Calico:  iptables/eBPF, GlobalNetworkPolicy, HostEndpoint
  - Cilium:  eBPF, CiliumNetworkPolicy, L7 HTTP/gRPC policies
  - Weave:   iptables
  - Flannel: NO NetworkPolicy support
  - Canal:   Flannel + Calico policy

NetworkPolicy scope: namespace-scoped, ingress/egress rules.
```

**Production Network Policy Pattern — Three-Tier App:**
```
Internet → LB → [ingress-nginx ns] → [app ns] → [database ns]
                                          ↑              ↑
                                     allow only      allow only
                                     from ingress    from app
```

```yaml
# 1. Default deny all in each namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}   # selects ALL pods in namespace
  policyTypes:
  - Ingress
  - Egress
  # No ingress/egress rules = deny all

---
# 2. Allow DNS resolution (critical — without this, pods can't resolve names)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - ports:
    - port: 53
      protocol: UDP
    - port: 53
      protocol: TCP

---
# 3. Allow app to receive traffic from ingress controller only
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-ingress-to-app
  namespace: production
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: my-app
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: ingress-nginx
      podSelector:
        matchLabels:
          app.kubernetes.io/name: ingress-nginx
    ports:
    - port: 8080
      protocol: TCP

---
# 4. Allow app to reach database
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-app-to-db
  namespace: production
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: my-app
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: database
      podSelector:
        matchLabels:
          app.kubernetes.io/name: postgres
    ports:
    - port: 5432
      protocol: TCP

---
# 5. Allow app to reach external APIs (by CIDR — limit blast radius)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-app-egress-external
  namespace: production
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: my-app
  policyTypes:
  - Egress
  egress:
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0
        except:
        - 10.0.0.0/8       # Block internal ranges
        - 172.16.0.0/12
        - 192.168.0.0/16
        - 169.254.0.0/16   # Block metadata service (AWS/GCP IMDS)
    ports:
    - port: 443
      protocol: TCP
```

### 9.2 Cilium L7 Network Policy (Beyond IP/Port)

```yaml
# CiliumNetworkPolicy — HTTP-layer policies
# Requires Cilium CNI with L7 proxy enabled
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: app-l7-policy
  namespace: production
spec:
  endpointSelector:
    matchLabels:
      app.kubernetes.io/name: api-gateway
  ingress:
  - fromEndpoints:
    - matchLabels:
        app.kubernetes.io/name: frontend
    toPorts:
    - ports:
      - port: "8080"
        protocol: TCP
      rules:
        http:
        - method: GET
          path: "^/api/v1/public/.*"    # only GET on public paths
        - method: POST
          path: "^/api/v1/orders$"
          headers:
          - "Content-Type: application/json"
  # Block access to internal debug endpoints
  ingress:
  - fromEndpoints:
    - matchLabels:
        app.kubernetes.io/name: frontend
    toPorts:
    - ports:
      - port: "8080"
        protocol: TCP
      rules:
        http:
        - method: ".*"
          path: "^/debug/.*"
          # No rule = deny
```

### 9.3 Block Cloud Metadata Access

```yaml
# Critical: Block access to cloud instance metadata service
# AWS: 169.254.169.254 (IMDSv1 — no auth, direct access to instance role credentials)
# GCP: 169.254.169.254 / metadata.google.internal
# Azure: 169.254.169.254

apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: block-metadata-service
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0
        except:
        - 169.254.169.254/32   # Block ALL cloud metadata

# Additionally: Use IMDSv2 on EC2 (requires PUT hop-limit=1 — pods can't reach it)
# aws ec2 modify-instance-metadata-options \
#   --instance-id i-xxxxx \
#   --http-tokens required \
#   --http-put-response-hop-limit 1
```

---

## 10. Secrets Management

### 10.1 Kubernetes Secrets — What They Are and Aren't

```
Kubernetes Secret is NOT secure by default:
  - Stored in etcd as base64 (NOT encrypted)
  - base64 is encoding, not encryption
  - Any principal with secrets/get can read them

Security layers for secrets:
  1. Encryption at rest in etcd (encryption-provider-config)
  2. RBAC to restrict access (limit who can GET secrets)
  3. Projected volumes with bound SA tokens (limit which pods)
  4. External secret stores (Vault, AWS Secrets Manager)
  5. Sealed Secrets (encrypt secret manifest itself)
  6. ESO (External Secrets Operator)
```

### 10.2 Vault Integration — Production Pattern

```
Architecture:
─────────────

Developer/CI                  Kubernetes                    Vault
──────────────────────────────────────────────────────────────────
                          Pod starts
                              │
                          kubelet creates
                          projected SA token
                          (audience: vault)
                              │
                          Vault Agent Sidecar ─────────────────►│
                          (injected by mutating webhook)         │
                              │                                  │ Kubernetes Auth
                              │                            Vault verifies SA JWT
                              │                            against K8s TokenReview
                              │                                  │
                              │◄─── Vault Token (TTL: 1h) ──────│
                              │
                          Vault Agent reads secrets
                          Writes to shared memory volume
                          App reads from /vault/secrets/
                              │
                          App starts (after agent init)
```

```go
// pkg/vault/k8s_auth.go
// Authenticate to Vault using Kubernetes service account JWT
package vault

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"time"
)

const (
	defaultSATokenPath = "/var/run/secrets/kubernetes.io/serviceaccount/token"
	vaultK8sAuthPath   = "/v1/auth/kubernetes/login"
)

type VaultK8sAuth struct {
	VaultAddr string
	Role      string
	JWTPath   string
	client    *http.Client
}

type VaultAuthRequest struct {
	JWT  string `json:"jwt"`
	Role string `json:"role"`
}

type VaultAuthResponse struct {
	Auth struct {
		ClientToken   string            `json:"client_token"`
		Accessor      string            `json:"accessor"`
		Policies      []string          `json:"policies"`
		LeaseDuration int               `json:"lease_duration"`
		Renewable     bool              `json:"renewable"`
		Metadata      map[string]string `json:"metadata"`
	} `json:"auth"`
	Errors []string `json:"errors"`
}

type VaultToken struct {
	Token     string
	ExpiresAt time.Time
	Policies  []string
}

// Login exchanges the pod's SA JWT for a Vault token.
// The Vault Kubernetes auth method validates the JWT against the K8s TokenReview API.
func (v *VaultK8sAuth) Login(ctx context.Context) (*VaultToken, error) {
	jwtPath := v.JWTPath
	if jwtPath == "" {
		jwtPath = defaultSATokenPath
	}

	jwt, err := os.ReadFile(jwtPath)
	if err != nil {
		return nil, fmt.Errorf("read SA token: %w", err)
	}

	reqBody, err := json.Marshal(VaultAuthRequest{
		JWT:  string(jwt),
		Role: v.Role,
	})
	if err != nil {
		return nil, fmt.Errorf("marshal auth request: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost,
		v.VaultAddr+vaultK8sAuthPath, bytes.NewReader(reqBody))
	if err != nil {
		return nil, fmt.Errorf("create request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := v.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("vault auth request: %w", err)
	}
	defer resp.Body.Close()

	var authResp VaultAuthResponse
	if err := json.NewDecoder(resp.Body).Decode(&authResp); err != nil {
		return nil, fmt.Errorf("decode vault response: %w", err)
	}
	if len(authResp.Errors) > 0 {
		return nil, fmt.Errorf("vault auth error: %v", authResp.Errors)
	}
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("vault auth HTTP %d", resp.StatusCode)
	}

	ttl := time.Duration(authResp.Auth.LeaseDuration) * time.Second
	return &VaultToken{
		Token:     authResp.Auth.ClientToken,
		ExpiresAt: time.Now().Add(ttl),
		Policies:  authResp.Auth.Policies,
	}, nil
}

// GetSecret reads a KV v2 secret from Vault.
func GetSecret(ctx context.Context, vaultAddr, token, path string) (map[string]string, error) {
	client := &http.Client{Timeout: 10 * time.Second}
	req, err := http.NewRequestWithContext(ctx, http.MethodGet,
		vaultAddr+"/v1/secret/data/"+path, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("X-Vault-Token", token)

	resp, err := client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("get secret: %w", err)
	}
	defer resp.Body.Close()

	var result struct {
		Data struct {
			Data     map[string]string `json:"data"`
			Metadata struct {
				Version    int       `json:"version"`
				CreatedAt  time.Time `json:"created_time"`
				Destroyed  bool      `json:"destroyed"`
			} `json:"metadata"`
		} `json:"data"`
		Errors []string `json:"errors"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("decode: %w", err)
	}
	if len(result.Errors) > 0 {
		return nil, fmt.Errorf("vault error: %v", result.Errors)
	}
	if result.Data.Metadata.Destroyed {
		return nil, fmt.Errorf("secret version is destroyed")
	}
	return result.Data.Data, nil
}
```

### 10.3 External Secrets Operator Pattern

```yaml
# ESO pulls secrets from AWS Secrets Manager into K8s Secrets
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secretsmanager
  namespace: production
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef:
            name: external-secrets-sa  # SA with IRSA/Workload Identity
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: database-credentials
  namespace: production
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secretsmanager
    kind: SecretStore
  target:
    name: database-credentials
    creationPolicy: Owner
    # Automatically delete K8s secret when ExternalSecret is deleted
    deletionPolicy: Delete
  data:
  - secretKey: password       # K8s secret key
    remoteRef:
      key: production/database  # AWS Secrets Manager path
      property: password        # JSON field in the secret
  - secretKey: username
    remoteRef:
      key: production/database
      property: username
```

### 10.4 Sealed Secrets — GitOps-Safe Secrets

```bash
# SealedSecret: encrypted K8s secret safe to store in Git
# Uses asymmetric encryption: public key encrypts, controller private key decrypts

# Install controller
helm repo add sealed-secrets https://bitnami-labs.github.io/sealed-secrets
helm install sealed-secrets sealed-secrets/sealed-secrets -n kube-system

# Get controller public key (safe to share)
kubeseal --fetch-cert --controller-namespace kube-system > pub-cert.pem

# Create a secret and seal it
kubectl create secret generic db-password \
  --from-literal=password=supersecret \
  --dry-run=client -o yaml | \
  kubeseal --cert pub-cert.pem \
    --scope namespace-wide \   # or cluster-wide or strict
    -o yaml > sealed-db-password.yaml
# sealed-db-password.yaml is safe to commit to Git

# Scope options:
# strict:         bound to name+namespace (most secure)
# namespace-wide: reuse across names in same namespace
# cluster-wide:   reuse anywhere (least secure)
```

---

## 11. Service Account Security

### 11.1 Service Account Token Deep Dive

```
Service Account Token flow (Bound Token, K8s 1.22+):
─────────────────────────────────────────────────────

                    kubelet                   API Server
                      │                           │
Pod scheduled          │                           │
                       │ TokenRequest API          │
                       │ POST /api/v1/namespaces/ns│
                       │   /serviceaccounts/sa     │
                       │   /token                  │
                       │ {                         │
                       │   audiences: [aud],       │
                       │   expirationSeconds: 3600 │
                       │ }                         │──────────────►│
                       │                           │  Verify SA    │
                       │                           │  exists, RBAC │
                       │◄─ JWT (signed by SA key) ─│               │
                       │                           │               │
kubelet writes JWT to  │                           │               │
/var/run/secrets/...   │                           │               │
/token (projected vol) │                           │               │

JWT Claims:
{
  "aud": ["https://kubernetes.default.svc.cluster.local"],
  "exp": 1704067200,         // hard expiry
  "iat": 1704063600,
  "iss": "https://kubernetes.default.svc.cluster.local",
  "kubernetes.io": {
    "namespace": "production",
    "node": {
      "name": "worker-1",
      "uid": "node-uid"
    },
    "pod": {
      "name": "my-pod-abc",
      "uid": "pod-uid"           // bound to specific pod instance
    },
    "serviceaccount": {
      "name": "my-sa",
      "uid": "sa-uid"
    },
    "warnafter": 1704065400     // warn at 30min to renew
  },
  "nbf": 1704063600,
  "sub": "system:serviceaccount:production:my-sa"
}

Kubelet rotates token before expiry (at warnafter time).
Token is invalidated if:
  - Pod is deleted
  - SA is deleted
  - Token expires
  - Node restarts (new kubelet-bound token required)
```

### 11.2 IRSA — IAM Roles for Service Accounts (AWS)

```
IRSA allows pods to assume AWS IAM roles without node-level credentials.
Uses OIDC federation: K8s SA tokens are accepted by AWS STS.

Flow:
─────
       Pod                   K8s OIDC Endpoint              AWS STS / IAM
        │                         │                              │
        │ Read projected           │                              │
        │ SA token (audience:      │                              │
        │   sts.amazonaws.com)     │                              │
        │                         │                              │
        │ AssumeRoleWithWebIdentity│                              │
        │──────────────────────────────────────────────────────►│
        │  Token: <sa-jwt>         │                              │
        │  RoleArn: arn:aws:iam::  │                              │
        │    123456789:role/MyRole │                              │
        │                         │                              │
        │                         │ STS calls OIDC jwks_uri      │
        │                         │◄────────────────────────────│
        │                         │ Returns JWKS                 │
        │                         │─────────────────────────────►│
        │                         │                              │ Verify JWT sig
        │                         │                              │ Check iss, aud, sub
        │                         │                              │ sub matches trust policy
        │◄──────────────────────── Temp credentials (15min TTL) ─│
        │  AccessKeyId             │                              │
        │  SecretAccessKey         │                              │
        │  SessionToken            │                              │
```

```yaml
# IAM Trust Policy for IRSA
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Federated": "arn:aws:iam::123456789:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/EXAMPLED539D4633E53DE1B716D3041E"
    },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "oidc.eks.us-east-1.amazonaws.com/id/EXAMPLED539D4633E53DE1B716D3041E:sub":
          "system:serviceaccount:production:my-service-account",
        "oidc.eks.us-east-1.amazonaws.com/id/EXAMPLED539D4633E53DE1B716D3041E:aud":
          "sts.amazonaws.com"
      }
    }
  }]
}
```

```yaml
# Service Account annotation
apiVersion: v1
kind: ServiceAccount
metadata:
  name: my-service-account
  namespace: production
  annotations:
    eks.amazonaws.com/role-arn: "arn:aws:iam::123456789:role/MyRole"
    eks.amazonaws.com/token-expiration: "3600"  # 1h token
```

---

## 12. Container Runtime Security

### 12.1 Container Runtime Hierarchy

```
Linux Kernel
     │
     ├── cgroups v2 (resource control: cpu, memory, io, pid count)
     ├── namespaces  (isolation: pid, net, mnt, ipc, uts, user)
     ├── LSMs        (AppArmor, SELinux)
     └── seccomp     (syscall filter)
          │
     ┌────▼─────────────────────────────────────────────────────────────┐
     │  OCI Runtime Interface                                           │
     │                                                                  │
     │  runc         → reference OCI runtime (most common)             │
     │  crun         → C reimplementation (faster startup, lower mem)   │
     │  youki        → Rust reimplementation (safer memory handling)    │
     │  gVisor/runsc → Sandboxed runtime (user-space kernel intercept)  │
     │  kata-containers → VM-based isolation (separate kernel per pod)  │
     └────┬─────────────────────────────────────────────────────────────┘
          │
     ┌────▼──────────────────────────────────────────────────────────────┐
     │  High-Level Container Runtime (CRI)                               │
     │                                                                   │
     │  containerd 1.7  → default in K8s 1.24+                          │
     │  CRI-O           → Red Hat / OpenShift focused                   │
     │  (docker daemon  → removed from K8s 1.24, via dockershim)        │
     └────┬──────────────────────────────────────────────────────────────┘
          │ CRI (gRPC)
     ┌────▼──────┐
     │  kubelet  │  :10250
     └───────────┘
```

### 12.2 gVisor — Application Kernel Interception

```
gVisor intercepts all syscalls from the container process.
Instead of passing syscalls to the host kernel, they go to:
  - Sentry: user-space kernel reimplementation in Go
  - Gofer: file proxy

                Container Process (nginx, app, etc.)
                         │ syscalls
                ─────────▼─────────────────────────
                │  Sentry (user-space kernel)      │
                │  Implements Linux syscall ABI    │
                │  In Go, sandboxed                │
                │  Limited host syscall surface    │
                │  (~50 syscalls vs ~300+ for runc) │
                ─────────┬─────────────────────────
                         │ limited syscalls
                ─────────▼─────────────────────────
                │  Host Linux Kernel               │
                ─────────────────────────────────────

Attack blocked:
  Container kernel exploit (e.g., Dirty Pipe, DirtyCow) → doesn't affect host
  because the exploit runs against Sentry, not the real kernel.

Overhead:
  ~10-20% CPU overhead for syscall-heavy workloads
  ~5-10% overhead for network-heavy workloads
  Not suitable for DPDK/RDMA or high-syscall-rate workloads

RuntimeClass configuration:
```
```yaml
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: gvisor
handler: runsc      # maps to containerd shim
overhead:
  podFixed:
    memory: "40Mi"  # Sentry memory overhead
    cpu: "50m"
scheduling:
  nodeClassifier:
    matchLabels:
      gvisor-enabled: "true"  # only schedule on nodes with gVisor installed
---
apiVersion: v1
kind: Pod
spec:
  runtimeClassName: gvisor    # use gVisor for this pod
```

### 12.3 containerd Security Configuration

```toml
# /etc/containerd/config.toml
version = 2

[grpc]
  address = "/run/containerd/containerd.sock"
  uid = 0
  gid = 0

[plugins."io.containerd.grpc.v1.cri"]
  [plugins."io.containerd.grpc.v1.cri".containerd]
    default_runtime_name = "runc"
    discard_unpacked_layers = false
    no_pivot = false          # use pivot_root (safer)
    snapshotter = "overlayfs"

    [plugins."io.containerd.grpc.v1.cri".containerd.runtimes]
      [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc]
        runtime_type = "io.containerd.runc.v2"
        [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]
          SystemdCgroup = true    # use systemd cgroup driver
          NoPivotRoot = false

      [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.gvisor]
        runtime_type = "io.containerd.runsc.v1"

      [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.kata]
        runtime_type = "io.containerd.kata.v2"

  [plugins."io.containerd.grpc.v1.cri".image_decryption]
    key_model = "node"

  [plugins."io.containerd.grpc.v1.cri".registry]
    [plugins."io.containerd.grpc.v1.cri".registry.mirrors]
      [plugins."io.containerd.grpc.v1.cri".registry.mirrors."docker.io"]
        endpoint = ["https://registry.example.com"]  # mirror only allowed registries
    [plugins."io.containerd.grpc.v1.cri".registry.configs]
      [plugins."io.containerd.grpc.v1.cri".registry.configs."registry.example.com".tls]
        ca_file   = "/etc/containerd/certs.d/registry.example.com/ca.crt"
        cert_file = "/etc/containerd/certs.d/registry.example.com/client.crt"
        key_file  = "/etc/containerd/certs.d/registry.example.com/client.key"
      [plugins."io.containerd.grpc.v1.cri".registry.configs."registry.example.com".auth]
        username = "robot$ci"
        password = "<token>"    # or use imagePullSecret in pod spec

[plugins."io.containerd.runtime.v1.linux"]
  no_shim = false
  runtime = "runc"
  runtime_root = ""
  shim = "containerd-shim"
  shim_debug = false
```

---

## 13. Supply Chain Security — SBOM, Sigstore, Cosign, SLSA

### 13.1 Supply Chain Attack Surface

```
Supply chain attacks target the build and delivery pipeline:

  Developer Laptop  →  Source Repo  →  CI/CD  →  Registry  →  K8s Cluster
        │                   │            │            │              │
   Compromise:         Dependency      Build       Image          Deploy
   - IDE plugin        injection       system      tampering      malicious
   - Git config        (typosquat,     exploit     (MITM,         image
   - SSH key           left-pad,       (CVE in     tag           (compromised
                       malicious       Jenkins)    mutation)      registry)
                       transitive)

Famous examples:
  SolarWinds:   Build system compromise → malicious DLL in signed package
  xz-utils:     Backdoor in compression library (CVE-2024-3094)
  left-pad:     Dependency unpublishing broke thousands of builds
  codecov:      CI script tampered → stole env vars (secrets) from CI jobs

Kubernetes-specific threats:
  - Malicious base image (FROM ubuntu → compromised ubuntu image)
  - Compromised dependency with container escape code
  - Registry MITM (tag pointing to different digest between CI and runtime)
  - Unverified kubectl plugins executing on developer machines
```

### 13.2 Cosign — Image Signing

```bash
# Generate signing keypair (or use keyless with OIDC)
cosign generate-key-pair \
  --kms awskms:///arn:aws:kms:us-east-1:123456789:key/mrk-abc123

# Sign image after build (in CI)
cosign sign \
  --key awskms:///arn:aws:kms:us-east-1:123456789:key/mrk-abc123 \
  --annotations git-sha=$(git rev-parse HEAD) \
  --annotations built-by=github-actions \
  --annotations repo=github.com/example/app \
  registry.example.com/app@sha256:abc123...

# Verify before deploy
cosign verify \
  --key cosign.pub \
  registry.example.com/app@sha256:abc123... | jq .

# Keyless signing (uses Sigstore Fulcio CA + Rekor transparency log)
# Identity is tied to OIDC token from CI (GitHub Actions, etc.)
COSIGN_EXPERIMENTAL=1 cosign sign \
  --identity-token=${ACTIONS_ID_TOKEN_REQUEST_TOKEN} \
  registry.example.com/app@sha256:abc123...

# Verify keyless
COSIGN_EXPERIMENTAL=1 cosign verify \
  --certificate-identity-regexp=".*@github.com" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com" \
  registry.example.com/app@sha256:abc123...
```

### 13.3 Policy Controller — Enforce Signature at Admission

```yaml
# Sigstore Policy Controller (Kubernetes admission webhook)
# Rejects pods that use unsigned images

apiVersion: policy.sigstore.dev/v1beta1
kind: ClusterImagePolicy
metadata:
  name: require-signed-images
spec:
  images:
  - glob: "registry.example.com/**"    # applies to all images from our registry
  authorities:
  - key:
      kms: "awskms:///arn:aws:kms:us-east-1:123456789:key/mrk-abc123"
    attestations:
    - name: sbom
      predicateType: "https://spdx.dev/Document"  # require SBOM attestation
      policy:
        type: cue
        data: |
          import "list"
          // SBOM must reference the image digest
          predicateType: "https://spdx.dev/Document"
  - keyless:
      url: "https://fulcio.sigstore.dev"
      identities:
      - issuer: "https://token.actions.githubusercontent.com"
        subject: "https://github.com/example/app/.github/workflows/build.yml@refs/heads/main"
```

### 13.4 SBOM Generation and Attestation

```bash
# Generate SBOM for a container image
syft registry.example.com/app:v1.2.3 -o spdx-json > app-sbom.spdx.json

# Attest SBOM to image (attach to registry as OCI artifact)
cosign attest \
  --key awskms:///arn:aws:kms:us-east-1:123456789:key/mrk-abc123 \
  --type spdx \
  --predicate app-sbom.spdx.json \
  registry.example.com/app@sha256:abc123...

# Verify attestation
cosign verify-attestation \
  --key cosign.pub \
  --type spdx \
  registry.example.com/app@sha256:abc123... | \
  jq '.payload | @base64d | fromjson | .predicate.packages[] | .name' | head -20

# Scan SBOM for vulnerabilities
grype sbom:app-sbom.spdx.json --fail-on high
```

### 13.5 Go: Image Signature Verification

```go
// pkg/imagesec/verify.go
// Verify cosign image signatures before deploying
package imagesec

import (
	"context"
	"crypto"
	"crypto/ecdsa"
	"crypto/x509"
	"encoding/pem"
	"fmt"
	"os"

	"github.com/google/go-containerregistry/pkg/authn"
	"github.com/google/go-containerregistry/pkg/name"
	"github.com/google/go-containerregistry/pkg/v1/remote"
	"github.com/sigstore/cosign/v2/pkg/cosign"
	"github.com/sigstore/cosign/v2/pkg/oci"
	sigs "github.com/sigstore/sigstore/pkg/signature"
)

type VerificationResult struct {
	Verified    bool
	ImageDigest string
	Signatures  []SignatureInfo
	Errors      []string
}

type SignatureInfo struct {
	KeyID      string
	Annotations map[string]string
	Chain      []string // certificate chain if keyless
}

// VerifyImageSignature checks that a container image has been signed by a trusted key.
// imageRef must include a digest: registry/image@sha256:...
func VerifyImageSignature(
	ctx context.Context,
	imageRef string,
	publicKeyPEM []byte,
) (*VerificationResult, error) {
	ref, err := name.ParseReference(imageRef)
	if err != nil {
		return nil, fmt.Errorf("parse image ref %q: %w", imageRef, err)
	}

	// Load the verification public key
	verifier, err := loadECDSAVerifier(publicKeyPEM)
	if err != nil {
		return nil, fmt.Errorf("load verifier: %w", err)
	}

	checkOpts := &cosign.CheckOpts{
		SigVerifier:     verifier,
		IgnoreTlog:      false, // Check Rekor transparency log
		IgnoreSCT:       false, // Check certificate transparency
		RekorURL:        "https://rekor.sigstore.dev",
	}

	// Fetch remote image with auth from environment
	remoteOpts := []remote.Option{
		remote.WithAuthFromKeychain(authn.DefaultKeychain),
		remote.WithContext(ctx),
	}

	sigs, bundleVerified, err := cosign.VerifyImageSignatures(ctx, ref, checkOpts)
	if err != nil {
		return &VerificationResult{
			Verified: false,
			Errors:   []string{err.Error()},
		}, nil
	}
	_ = remoteOpts
	_ = bundleVerified

	result := &VerificationResult{
		Verified: true,
	}

	// Extract signature metadata
	for _, sig := range sigs {
		payload, err := sig.Payload()
		if err != nil {
			continue
		}

		// The payload is a SimpleContainerImage JSON
		var info SignatureInfo
		ann, err := sig.Annotations()
		if err == nil {
			info.Annotations = ann
		}

		result.Signatures = append(result.Signatures, info)
		_ = payload
	}

	return result, nil
}

func loadECDSAVerifier(publicKeyPEM []byte) (sigs.Verifier, error) {
	block, _ := pem.Decode(publicKeyPEM)
	if block == nil {
		return nil, fmt.Errorf("failed to decode PEM block")
	}

	pub, err := x509.ParsePKIXPublicKey(block.Bytes)
	if err != nil {
		return nil, fmt.Errorf("parse public key: %w", err)
	}

	ecPub, ok := pub.(*ecdsa.PublicKey)
	if !ok {
		return nil, fmt.Errorf("not an ECDSA public key")
	}

	return sigs.LoadECDSAVerifier(ecPub, crypto.SHA256)
}

// VerifyFromFile is a convenience wrapper that reads the public key from a file.
func VerifyFromFile(ctx context.Context, imageRef, publicKeyFile string) (*VerificationResult, error) {
	keyPEM, err := os.ReadFile(publicKeyFile)
	if err != nil {
		return nil, fmt.Errorf("read public key: %w", err)
	}
	return VerifyImageSignature(ctx, imageRef, keyPEM)
}
```

---

## 14. Runtime Threat Detection — eBPF, Falco, Audit

### 14.1 Kubernetes Audit Policy — Complete Configuration

```yaml
# /etc/kubernetes/audit-policy.yaml
# Structured audit policy — captures security-relevant events without noise
apiVersion: audit.k8s.io/v1
kind: Policy

# Global omit rules (high volume, low security value)
omitStages:
- RequestReceived   # every request — too noisy

rules:
# 1. Never log data from these resources (noisy, not security-relevant)
- level: None
  resources:
  - group: ""
    resources: ["events"]
- level: None
  resources:
  - group: "coordination.k8s.io"
    resources: ["leases"]
- level: None
  nonResourceURLs:
  - "/healthz*"
  - "/readyz*"
  - "/livez*"
  - "/version"

# 2. Secrets, ConfigMaps, TokenReviews: log Metadata only (no data — prevent secret leakage in audit log)
- level: Metadata
  resources:
  - group: ""
    resources: ["secrets", "configmaps", "serviceaccounts/token"]
  - group: "authentication.k8s.io"
    resources: ["*"]

# 3. Exec and Attach: full RequestResponse (detect container escapes)
- level: RequestResponse
  resources:
  - group: ""
    resources: ["pods/exec", "pods/attach", "pods/portforward"]

# 4. RBAC changes: full RequestResponse (detect privilege escalation)
- level: RequestResponse
  resources:
  - group: "rbac.authorization.k8s.io"
    resources: ["roles", "rolebindings", "clusterroles", "clusterrolebindings"]

# 5. Admission webhook changes: full
- level: RequestResponse
  resources:
  - group: "admissionregistration.k8s.io"
    resources: ["*"]

# 6. NetworkPolicy changes
- level: RequestResponse
  resources:
  - group: "networking.k8s.io"
    resources: ["networkpolicies"]

# 7. All other resource modifications: Request body only
- level: Request
  verbs: ["create", "update", "patch", "delete", "deletecollection"]

# 8. Read-only operations on workloads: Metadata
- level: Metadata
  verbs: ["get", "list", "watch"]
  resources:
  - group: ""
    resources: ["pods", "services", "endpoints", "namespaces"]
  - group: "apps"
    resources: ["deployments", "daemonsets", "statefulsets"]

# 9. Default: log metadata for everything else
- level: Metadata
```

### 14.2 Falco Rules — Kubernetes-Specific Detections

```yaml
# /etc/falco/k8s_rules.yaml
# Real production Falco rules for Kubernetes threat detection

# Detect container escape via privilege escalation
- rule: Privileged Container Spawned
  desc: >
    A privileged container was started. Privileged containers can escape isolation.
  condition: >
    container.privileged = true and
    not (container.image.repository in (trusted_privileged_images))
  output: >
    Privileged container started
    (user=%user.name user_uid=%user.uid image=%container.image.repository:%container.image.tag
     container=%container.id pod=%k8s.pod.name ns=%k8s.ns.name node=%k8s.node.name)
  priority: CRITICAL
  tags: [container, privilege_escalation]

# Detect exec into containers (common lateral movement step)
- rule: Terminal Shell in Container
  desc: >
    A shell was opened inside a container. May indicate interactive access or escape.
  condition: >
    spawned_process and container and
    shell_procs and
    not proc.pname in (shell_binaries)
  output: >
    Shell opened in container
    (user=%user.name container=%container.id image=%container.image.repository
     cmd=%proc.cmdline pod=%k8s.pod.name ns=%k8s.ns.name)
  priority: WARNING
  tags: [container, shell]

# Detect attempts to read service account tokens
- rule: Service Account Token Read
  desc: >
    A process attempted to read the Kubernetes service account token.
    May indicate credential harvesting.
  condition: >
    open_read and
    fd.name startswith "/var/run/secrets/kubernetes.io/serviceaccount/token" and
    not k8s_containers and
    not proc.name in (allowed_sa_readers)
  output: >
    Service account token read
    (user=%user.name proc=%proc.name cmd=%proc.cmdline
     container=%container.id pod=%k8s.pod.name)
  priority: HIGH
  tags: [kubernetes, credential_access]

# Detect crypto miners (common after container compromise)
- rule: Cryptocurrency Mining Process
  desc: >
    A process with characteristics of a cryptocurrency miner was detected.
  condition: >
    spawned_process and container and
    (proc.name in (known_miner_binaries) or
     proc.cmdline contains "--pool " or
     proc.cmdline contains "stratum+" or
     proc.cmdline contains "xmrig" or
     proc.cmdline contains "minerd")
  output: >
    Cryptocurrency mining detected
    (user=%user.name proc=%proc.name cmd=%proc.cmdline
     container=%container.id image=%container.image.repository
     pod=%k8s.pod.name ns=%k8s.ns.name)
  priority: CRITICAL
  tags: [process, cryptocurrency]

# Detect host filesystem access from container
- rule: Write Below Root
  desc: >
    An attempt to write to files in the root filesystem (not in container overlay).
  condition: >
    open_write and
    container and
    not (fd.name startswith /tmp or
         fd.name startswith /var/tmp or
         fd.name startswith /dev or
         fd.name startswith /proc)
  output: >
    File write outside expected paths
    (user=%user.name file=%fd.name proc=%proc.name
     container=%container.id pod=%k8s.pod.name)
  priority: ERROR
  tags: [filesystem, container]

# Detect network scanning tools
- rule: Network Tool Execution in Container
  desc: >
    Network reconnaissance tools executed inside a container.
  condition: >
    spawned_process and container and
    proc.name in (nmap, masscan, zmap, nc, netcat, socat, ncat)
  output: >
    Network tool executed in container
    (user=%user.name proc=%proc.name cmd=%proc.cmdline
     container=%container.id pod=%k8s.pod.name ns=%k8s.ns.name)
  priority: WARNING
  tags: [network, container]

# K8s API server audit — suspicious RBAC changes
- rule: K8s ClusterRole Granted to System Account
  desc: >
    A ClusterRoleBinding was created granting cluster-admin to a service account.
  condition: >
    ka.target.resource = "clusterrolebindings" and
    ka.verb = "create" and
    ka.requestBody contains "cluster-admin"
  output: >
    ClusterRoleBinding cluster-admin granted
    (user=%ka.user.name body=%ka.request.body
     sourceip=%ka.source.ip ns=%ka.target.namespace)
  priority: CRITICAL
  source: k8s_audit
  tags: [kubernetes, rbac, privilege_escalation]
```

### 14.3 Go: Kubernetes Audit Event Processor

```go
// pkg/audit/processor.go
// Process K8s audit log events and generate security alerts
package audit

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log/slog"
	"strings"
	"time"

	auditv1 "k8s.io/apiserver/pkg/apis/audit/v1"
)

// SecurityAlert represents a detected security event
type SecurityAlert struct {
	Timestamp   time.Time         `json:"timestamp"`
	Severity    string            `json:"severity"`   // CRITICAL, HIGH, MEDIUM, LOW
	Rule        string            `json:"rule"`
	Description string            `json:"description"`
	User        string            `json:"user"`
	SourceIP    string            `json:"source_ip"`
	Resource    string            `json:"resource"`
	Namespace   string            `json:"namespace"`
	Verb        string            `json:"verb"`
	AuditID     string            `json:"audit_id"`
	Extra       map[string]string `json:"extra,omitempty"`
}

// DetectionRule defines a pattern to match in audit events
type DetectionRule struct {
	Name        string
	Description string
	Severity    string
	Match       func(event *auditv1.Event) bool
}

// productionRules is the set of security detection rules
var productionRules = []DetectionRule{
	{
		Name:        "cluster-admin-granted",
		Description: "ClusterRoleBinding with cluster-admin role created",
		Severity:    "CRITICAL",
		Match: func(e *auditv1.Event) bool {
			return e.ObjectRef != nil &&
				e.ObjectRef.Resource == "clusterrolebindings" &&
				(e.Verb == "create" || e.Verb == "update") &&
				requestBodyContains(e, "cluster-admin")
		},
	},
	{
		Name:        "secret-accessed-in-bulk",
		Description: "Bulk list of secrets (potential credential harvesting)",
		Severity:    "HIGH",
		Match: func(e *auditv1.Event) bool {
			return e.ObjectRef != nil &&
				e.ObjectRef.Resource == "secrets" &&
				e.Verb == "list" &&
				e.ObjectRef.Namespace == "" // cluster-scoped list = ALL namespaces
		},
	},
	{
		Name:        "exec-into-production-pod",
		Description: "kubectl exec into production namespace pod",
		Severity:    "HIGH",
		Match: func(e *auditv1.Event) bool {
			return e.ObjectRef != nil &&
				e.ObjectRef.Subresource == "exec" &&
				e.ObjectRef.Namespace == "production" &&
				e.ResponseStatus != nil &&
				e.ResponseStatus.Code < 400
		},
	},
	{
		Name:        "anonymous-api-access",
		Description: "API server accessed by anonymous user (should never happen with --anonymous-auth=false)",
		Severity:    "CRITICAL",
		Match: func(e *auditv1.Event) bool {
			return e.User.Username == "system:anonymous" ||
				containsGroup(e.User.Groups, "system:unauthenticated")
		},
	},
	{
		Name:        "admission-webhook-modified",
		Description: "Admission webhook configuration modified (policy bypass risk)",
		Severity:    "CRITICAL",
		Match: func(e *auditv1.Event) bool {
			return e.ObjectRef != nil &&
				(e.ObjectRef.Resource == "mutatingwebhookconfigurations" ||
					e.ObjectRef.Resource == "validatingwebhookconfigurations") &&
				(e.Verb == "create" || e.Verb == "update" || e.Verb == "delete")
		},
	},
	{
		Name:        "network-policy-deleted",
		Description: "NetworkPolicy deleted (potential network isolation bypass)",
		Severity:    "HIGH",
		Match: func(e *auditv1.Event) bool {
			return e.ObjectRef != nil &&
				e.ObjectRef.Resource == "networkpolicies" &&
				e.Verb == "delete"
		},
	},
	{
		Name:        "node-system-account-impersonation",
		Description: "User impersonating a node (system:node:*) account",
		Severity:    "CRITICAL",
		Match: func(e *auditv1.Event) bool {
			for _, extra := range e.User.Extra {
				for _, v := range extra {
					if strings.HasPrefix(v, "system:node:") {
						return true
					}
				}
			}
			return false
		},
	},
	{
		Name:        "pod-security-annotation-removed",
		Description: "Pod security label removed from namespace (PSA bypass)",
		Severity:    "HIGH",
		Match: func(e *auditv1.Event) bool {
			if e.ObjectRef == nil || e.ObjectRef.Resource != "namespaces" {
				return false
			}
			if e.Verb != "patch" && e.Verb != "update" {
				return false
			}
			body := requestBodyStr(e)
			return strings.Contains(body, "pod-security.kubernetes.io") &&
				strings.Contains(body, "null") // removing label
		},
	},
}

// AuditProcessor reads and analyzes K8s audit log events
type AuditProcessor struct {
	rules   []DetectionRule
	alertCh chan SecurityAlert
	logger  *slog.Logger
}

func NewAuditProcessor(alertCh chan SecurityAlert) *AuditProcessor {
	return &AuditProcessor{
		rules:   productionRules,
		alertCh: alertCh,
		logger:  slog.Default(),
	}
}

// ProcessStream reads JSON audit events from reader and emits alerts.
// Each line in the audit log is a JSON-encoded Event.
func (ap *AuditProcessor) ProcessStream(ctx context.Context, r io.Reader) error {
	scanner := bufio.NewScanner(r)
	scanner.Buffer(make([]byte, 1*1024*1024), 1*1024*1024) // 1MB per line

	for scanner.Scan() {
		if ctx.Err() != nil {
			return ctx.Err()
		}

		line := scanner.Bytes()
		if len(line) == 0 {
			continue
		}

		var event auditv1.Event
		if err := json.Unmarshal(line, &event); err != nil {
			ap.logger.Warn("failed to parse audit event", "err", err)
			continue
		}

		ap.processEvent(&event)
	}

	return scanner.Err()
}

func (ap *AuditProcessor) processEvent(event *auditv1.Event) {
	for _, rule := range ap.rules {
		if !rule.Match(event) {
			continue
		}

		alert := SecurityAlert{
			Timestamp:   event.RequestReceivedTimestamp.Time,
			Severity:    rule.Severity,
			Rule:        rule.Name,
			Description: rule.Description,
			User:        event.User.Username,
			SourceIP:    sourceIP(event),
			Verb:        event.Verb,
			AuditID:     string(event.AuditID),
		}

		if event.ObjectRef != nil {
			alert.Resource = fmt.Sprintf("%s/%s/%s",
				event.ObjectRef.APIGroup,
				event.ObjectRef.Resource,
				event.ObjectRef.Name)
			alert.Namespace = event.ObjectRef.Namespace
		}

		select {
		case ap.alertCh <- alert:
		default:
			ap.logger.Warn("alert channel full, dropping alert",
				"rule", rule.Name,
				"user", alert.User,
			)
		}
	}
}

// Helper functions
func requestBodyContains(e *auditv1.Event, s string) bool {
	if e.RequestObject == nil {
		return false
	}
	return strings.Contains(string(e.RequestObject.Raw), s)
}

func requestBodyStr(e *auditv1.Event) string {
	if e.RequestObject == nil {
		return ""
	}
	return string(e.RequestObject.Raw)
}

func containsGroup(groups []string, target string) bool {
	for _, g := range groups {
		if g == target {
			return true
		}
	}
	return false
}

func sourceIP(e *auditv1.Event) string {
	if len(e.SourceIPs) > 0 {
		return e.SourceIPs[0]
	}
	return ""
}
```

---

## 15. Service Mesh Security — mTLS, Authorization Policies

### 15.1 Istio Security Architecture

```
Istio Security Components:
──────────────────────────

  istiod (control plane):
    ├── Citadel (CA): Issues SVID X.509 certs to workloads
    │                 Identity = SPIFFE URI in SAN
    │                 spiffe://<trust-domain>/ns/<namespace>/sa/<service-account>
    ├── Pilot:        Distributes AuthorizationPolicy, PeerAuthentication to proxies
    └── Galley:       Config validation

  Envoy sidecar (data plane):
    ├── Intercepts all inbound/outbound traffic (iptables redirect)
    ├── Terminates mTLS (MTLS PeerAuthentication)
    ├── Enforces AuthorizationPolicy (L4/L7)
    ├── Reports telemetry (traces, metrics, access logs)
    └── Gets cert rotation from Istio CA via xDS (SDS — Secret Discovery Service)

mTLS Flow:
──────────

  Pod A (Envoy)                              Pod B (Envoy)
       │                                          │
       │ App traffic to B:8080                    │
       ▼                                          │
  iptables redirect (port 15001)                 │
       │                                          │
  Envoy outbound                                 │
       │ TLS Client Hello                         │
       │   SAN: spiffe://cluster.local/ns/a/sa/a  │
       ├──────────────────────────────────────────►
       │                                          │ iptables redirect (port 15006)
       │                                          ▼
       │                                     Envoy inbound
       │ TLS Server Hello                         │
       │   SAN: spiffe://cluster.local/ns/b/sa/b  │
       ◄──────────────────────────────────────────┤
       │                                          │
       │ mTLS established                         │
       │ Both sides verified by Istio CA          │
       │ ───────────────────────────────────────► │
       │                                          │ AuthorizationPolicy checked
       │                                          │ by Envoy inbound proxy
       │                                          │
       │                                          ▼
       │                                     App receives request
       │                                     from 127.0.0.1:8080
```

### 15.2 Istio PeerAuthentication and AuthorizationPolicy

```yaml
# STRICT mTLS for entire mesh — no plaintext connections allowed
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: istio-system  # applies mesh-wide
spec:
  mtls:
    mode: STRICT  # DISABLE, PERMISSIVE, STRICT

---
# Namespace-scoped strict mTLS
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: production
spec:
  mtls:
    mode: STRICT

---
# AuthorizationPolicy: deny-all by default, explicit allow
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: deny-all
  namespace: production
spec: {}   # empty spec = deny all

---
# Allow frontend → backend only on specific paths
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: allow-frontend-to-backend
  namespace: production
spec:
  selector:
    matchLabels:
      app: backend
  action: ALLOW
  rules:
  - from:
    - source:
        # Verify principal (SPIFFE identity)
        principals:
        - "cluster.local/ns/production/sa/frontend"
    to:
    - operation:
        methods: ["GET", "POST"]
        paths:
        - "/api/v1/*"
        notPaths:
        - "/api/v1/admin/*"  # admin path denied
        ports: ["8080"]
    when:
    - key: request.headers[x-user-id]
      notValues: [""]  # require user ID header

---
# JWT authentication + authorization (end-user identity)
apiVersion: security.istio.io/v1beta1
kind: RequestAuthentication
metadata:
  name: jwt-auth
  namespace: production
spec:
  selector:
    matchLabels:
      app: backend
  jwtRules:
  - issuer: "https://accounts.google.com"
    jwksUri: "https://www.googleapis.com/oauth2/v3/certs"
    audiences: ["my-api"]
    forwardOriginalToken: false  # don't forward raw JWT to upstream

---
# Require valid JWT for all requests
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: require-jwt
  namespace: production
spec:
  selector:
    matchLabels:
      app: backend
  action: ALLOW
  rules:
  - when:
    - key: request.auth.claims[iss]
      values: ["https://accounts.google.com"]
    - key: request.auth.claims[aud]
      values: ["my-api"]
```

---

## 16. Multi-Tenancy Isolation Models

### 16.1 Isolation Spectrum

```
ISOLATION SPECTRUM
──────────────────────────────────────────────────────────────────────────────

Weakest                                                              Strongest
  │                                                                        │
  ▼                                                                        ▼
Namespace    →  NetworkPolicy  →  PSA/Gatekeeper  →  VM-based      →  Separate
Separation      Namespace         + LimitRange       (Kata/gVisor)    Cluster
               Isolation         ResourceQuota       per tenant        per tenant

  Shared kernel          Shared kernel             Separate kernel    Separate
  Shared node            Shared node               Shared node        control plane
  Soft isolation         Network isolated          Hardware isolated  Full isolation

Use cases:
  Namespace:     Dev/staging/prod separation. Internal teams.
  NetworkPolicy: Stronger isolation. Different teams.
  VM-based:      Hostile tenant code. External parties.
  Separate:      Regulatory compliance. Financial / healthcare tenants.

Cost (low to high):
  Namespace < NetworkPolicy < VM-based < Separate cluster
```

### 16.2 Namespace Isolation — Complete Setup

```yaml
# Namespace with all isolation controls
apiVersion: v1
kind: Namespace
metadata:
  name: tenant-a
  labels:
    tenant: tenant-a
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: v1.29
---
# ResourceQuota — prevent resource exhaustion
apiVersion: v1
kind: ResourceQuota
metadata:
  name: tenant-a-quota
  namespace: tenant-a
spec:
  hard:
    requests.cpu: "10"
    requests.memory: "20Gi"
    limits.cpu: "20"
    limits.memory: "40Gi"
    pods: "50"
    services: "20"
    persistentvolumeclaims: "10"
    secrets: "50"
    configmaps: "50"
    count/deployments.apps: "20"
    count/replicationcontrollers: "0"  # disallow, use Deployments
---
# LimitRange — set defaults and max/min
apiVersion: v1
kind: LimitRange
metadata:
  name: tenant-a-limits
  namespace: tenant-a
spec:
  limits:
  - type: Container
    default:
      cpu: "500m"
      memory: "512Mi"
    defaultRequest:
      cpu: "100m"
      memory: "128Mi"
    max:
      cpu: "2"
      memory: "2Gi"
    min:
      cpu: "50m"
      memory: "64Mi"
  - type: Pod
    max:
      cpu: "4"
      memory: "4Gi"
  - type: PersistentVolumeClaim
    max:
      storage: "50Gi"
    min:
      storage: "1Gi"
---
# Default deny NetworkPolicy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
  namespace: tenant-a
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
```

---

## 17. Workload Identity & SPIFFE/SPIRE

### 17.1 SPIFFE Architecture

```
SPIFFE (Secure Production Identity Framework for Everyone)
Provides cryptographic identities to workloads.

SVID (SPIFFE Verifiable Identity Document):
  Type 1: X.509 SVID
    - X.509 certificate with SPIFFE URI in SAN
    - spiffe://<trust-domain>/<path>
    - Example: spiffe://cluster.local/ns/production/sa/payment-service
    - Short-lived (1h default), auto-rotated
    - Used by Istio, Consul Connect, SPIRE

  Type 2: JWT SVID
    - JWT token with SPIFFE URI as sub claim
    - Short-lived (1h)
    - Used for HTTP bearer token flows

SPIRE (SPIFFE Runtime Environment):
  ┌──────────────────────────────────────────────────────────┐
  │  SPIRE Server (control plane)                            │
  │    - Registration API (register workload selectors)      │
  │    - CA (signs X.509 SVIDs)                              │
  │    - Datastore (SQLite / PostgreSQL)                     │
  │    - Federation with other SPIRE servers                 │
  └──────────────────────────────────────────────────────────┘
          │ attests node identity via node attestor
          │ (K8s: validates kubelet cert, AWS: validates IID)
          ▼
  ┌──────────────────────────────────────────────────────────┐
  │  SPIRE Agent (on each node, as DaemonSet)                │
  │    - Node attestation to SPIRE server                    │
  │    - Workload attestation (K8s pod selectors)            │
  │    - SVID delivery via Workload API (Unix socket)        │
  └──────────────────────────────────────────────────────────┘
          │ Unix socket /run/spire/sockets/agent.sock
          ▼
  ┌──────────────────────────────────────────────────────────┐
  │  Workload Process                                        │
  │    - Calls Workload API (gRPC)                           │
  │    - Receives X.509 SVID + trust bundle                  │
  │    - Uses SVID for mTLS to other services                │
  └──────────────────────────────────────────────────────────┘
```

### 17.2 Go: SPIFFE Workload API Client

```go
// pkg/spiffe/client.go
// Retrieve SVID from SPIRE agent and use for mTLS
package spiffe

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"fmt"
	"net/http"
	"sync"
	"time"

	"github.com/spiffe/go-spiffe/v2/spiffeid"
	"github.com/spiffe/go-spiffe/v2/spiffetls/tlsconfig"
	"github.com/spiffe/go-spiffe/v2/workloadapi"
)

const (
	socketPath = "unix:///run/spire/sockets/agent.sock"
)

// SPIFFEClient holds a SPIFFE workload API client and
// provides mTLS-capable HTTP clients.
type SPIFFEClient struct {
	mu        sync.RWMutex
	source    *workloadapi.X509Source
	trustDomain spiffeid.TrustDomain
}

func NewSPIFFEClient(ctx context.Context, trustDomain string) (*SPIFFEClient, error) {
	td, err := spiffeid.TrustDomainFromString(trustDomain)
	if err != nil {
		return nil, fmt.Errorf("parse trust domain: %w", err)
	}

	// Connect to SPIRE agent via Workload API
	source, err := workloadapi.NewX509Source(
		ctx,
		workloadapi.WithClientOptions(
			workloadapi.WithAddr(socketPath),
		),
	)
	if err != nil {
		return nil, fmt.Errorf("create x509 source: %w", err)
	}

	return &SPIFFEClient{
		source:      source,
		trustDomain: td,
	}, nil
}

// NewMTLSClient creates an HTTP client that uses the workload's SVID for mTLS.
// It only connects to servers with SVIDs in the same trust domain.
func (c *SPIFFEClient) NewMTLSClient(authorizedID spiffeid.ID) (*http.Client, error) {
	// TLS config: use our SVID as client cert, authorize specific server SPIFFE ID
	tlsConfig := tlsconfig.MTLSClientConfig(
		c.source,           // our X.509 SVID source
		c.source,           // trust bundle source
		tlsconfig.AuthorizeID(authorizedID), // authorize exact server ID
	)

	return &http.Client{
		Transport: &http.Transport{
			TLSClientConfig: tlsConfig,
			// Force HTTP/2
			ForceAttemptHTTP2: true,
		},
		Timeout: 30 * time.Second,
	}, nil
}

// NewMTLSServer creates TLS config for a server that requires mTLS.
// Only clients with SVIDs from the same trust domain are accepted.
func (c *SPIFFEClient) NewMTLSServerConfig() *tls.Config {
	return tlsconfig.MTLSServerConfig(
		c.source,
		c.source,
		tlsconfig.AuthorizeMemberOf(c.trustDomain),
	)
}

// GetCurrentSVID returns the current X.509 SVID for inspection.
func (c *SPIFFEClient) GetCurrentSVID() (*x509.Certificate, error) {
	svids, err := c.source.GetX509SVIDsForWorkload()
	if err != nil {
		return nil, fmt.Errorf("get SVIDs: %w", err)
	}
	if len(svids) == 0 {
		return nil, fmt.Errorf("no SVIDs available")
	}
	return svids[0].Certificates[0], nil
}

// Close releases the workload API source.
func (c *SPIFFEClient) Close() error {
	return c.source.Close()
}

// Example usage: HTTP server with SPIFFE mTLS
func ExampleSPIFFEServer(ctx context.Context) error {
	client, err := NewSPIFFEClient(ctx, "cluster.local")
	if err != nil {
		return fmt.Errorf("init SPIFFE client: %w", err)
	}
	defer client.Close()

	tlsConfig := client.NewMTLSServerConfig()

	srv := &http.Server{
		Addr:      ":8443",
		TLSConfig: tlsConfig,
		Handler:   http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// At this point, mTLS is verified — extract peer identity
			if r.TLS != nil && len(r.TLS.PeerCertificates) > 0 {
				cert := r.TLS.PeerCertificates[0]
				for _, san := range cert.URIs {
					fmt.Printf("Peer SPIFFE ID: %s\n", san.String())
				}
			}
			w.WriteHeader(http.StatusOK)
		}),
	}

	return srv.ListenAndServeTLS("", "") // empty = use TLSConfig certs
}
```

---

## 18. Kubernetes CIS Benchmark & Compliance

### 18.1 CIS Benchmark Critical Controls

```
CIS Kubernetes Benchmark v1.9 — Critical Findings Summary
───────────────────────────────────────────────────────────

1.1 Control Plane Configuration
  1.1.1  API server pod spec file permissions: 600
  1.1.11 etcd data dir permissions: 700
  1.1.19 Container network interface file permissions: 600

1.2 API Server
  1.2.1  --anonymous-auth=false             [Level 1]
  1.2.5  --kubelet-https=true               [Level 1]
  1.2.6  --insecure-bind-address removed    [Level 1]
  1.2.7  --insecure-port=0                  [Level 1]
  1.2.9  --profiling=false                  [Level 1]
  1.2.14 --admission-control includes NodeRestriction [Level 1]
  1.2.17 --audit-log-path set               [Level 1]
  1.2.22 --request-timeout=300              [Level 1]
  1.2.24 --service-account-lookup=true      [Level 1]
  1.2.26 --service-account-key-file set     [Level 1]
  1.2.27 --etcd-certfile and --etcd-keyfile set [Level 1]
  1.2.32 --encryption-provider-config set   [Level 1]

1.3 Controller Manager
  1.3.2  --profiling=false                  [Level 1]
  1.3.6  --feature-gates=RotateKubeletServerCertificate=true [Level 1]
  1.3.7  --bind-address=127.0.0.1           [Level 1]

1.4 Scheduler
  1.4.2  --profiling=false                  [Level 1]
  1.4.1  --bind-address=127.0.0.1           [Level 1]

3.1 Authentication
  3.1.1  Client certificate authentication not used for users [Level 2]
  3.1.2  Service account token authentication not used for users [Level 1]

4.1 Worker Nodes
  4.1.1  kubelet service file permissions: 600 [Level 1]
  4.1.6  kubelet.conf permissions: 600       [Level 1]
  4.2.1  --anonymous-auth=false             [Level 1]
  4.2.2  --authorization-mode=Webhook       [Level 1]
  4.2.4  --read-only-port=0                 [Level 1]
  4.2.6  --protect-kernel-defaults=true     [Level 1]
  4.2.10 --tls-cert-file and --tls-private-key-file set [Level 1]

5. Policies
  5.1.1  cluster-admin ClusterRole not used unnecessarily [Level 1]
  5.1.3  Minimize wildcard use in Roles/ClusterRoles [Level 1]
  5.1.6  Ensure serviceAccountToken not auto-mounted if not needed [Level 1]
  5.2.1  Ensure privileged containers not admitted [Level 1]
  5.2.2  Ensure host PID not admitted [Level 1]
  5.2.5  Ensure CAP_NET_RAW not admitted [Level 1]
  5.2.7  Ensure NET_RAW dropped [Level 1]
  5.3.2  All namespaces have NetworkPolicy [Level 2]
  5.4.1  No secrets as env vars [Level 2]
  5.4.2  Use mounted secrets, not env vars [Level 2]
  5.7.2  Ensure seccomp profile set to RuntimeDefault [Level 2]
  5.7.3  Apply AppArmor or SELinux profile [Level 2]
  5.7.4  Ensure namespaces not use default [Level 2]
```

**Run CIS Benchmark with kube-bench:**
```bash
# Run as a Job on each node
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml

# Or run directly on node
docker run --pid=host --network=host --rm \
  -v /etc:/etc:ro \
  -v /var:/var:ro \
  -v /etc/passwd:/etc/passwd:ro \
  -v /etc/group:/etc/group:ro \
  -v /usr/bin/containerd:/usr/bin/containerd:ro \
  aquasec/kube-bench:latest \
  --benchmark cis-1.8 \
  2>&1 | tee kube-bench-results.txt

# Parse failures
grep "FAIL\|WARN" kube-bench-results.txt
```

---

## 19. Threat Modeling — STRIDE across K8s

### 19.1 STRIDE Threat Model

```
STRIDE Applied to Kubernetes
──────────────────────────────────────────────────────────────────────────

S — Spoofing
  Threat: Attacker forges service account token or TLS cert to impersonate a pod/user.
  Controls:
    - Bound SA tokens (pod-bound, time-bound)
    - Certificate pinning / short-lived certs
    - OIDC token validation (iss, aud, exp)
    - SPIFFE mTLS (cryptographic identity per workload)
  Attack scenarios:
    - Long-lived SA token leaked → attacker reuses indefinitely
    - etcd compromised → steal SA signing key → forge any token

T — Tampering
  Threat: Attacker modifies audit logs, policy objects, or code in transit.
  Controls:
    - Audit log write-once storage (immutable S3, Loki)
    - Signed image attestations (Cosign/Sigstore)
    - RBAC limiting who can modify NetworkPolicy/WebhookConfig
    - etcd encryption (prevents at-rest tampering)
    - TLS on all control plane communications
  Attack scenarios:
    - Attacker with API access deletes NetworkPolicy → unrestricted traffic
    - MITM on image pull → substitute malicious image

R — Repudiation
  Threat: Attacker denies performing actions. No audit trail.
  Controls:
    - Kubernetes audit log (all API calls + user identity)
    - Immutable audit backend (write-only storage)
    - Structured logging with request ID correlation
    - Access log at every tier (ingress, service mesh, app)
  Attack scenarios:
    - Compromised admin deletes audit logs → can't prove what happened
    - Shared kubeconfig → can't attribute actions to specific humans

I — Information Disclosure
  Threat: Sensitive data exposed (secrets, pod specs, node info).
  Controls:
    - Encryption at rest (etcd encryption-provider-config)
    - RBAC restricting secrets/get
    - Network Policy blocking lateral movement
    - Seccomp/AppArmor preventing /proc snooping
    - Disable :10255 (unauthenticated metrics)
    - Disable dashboard public exposure
  Attack scenarios:
    - Pod with broad RBAC reads all secrets in namespace
    - /proc/1/environ leak from sibling container (hostPID)
    - Metadata server (169.254.169.254) gives cloud credentials

D — Denial of Service
  Threat: Exhaust cluster resources to prevent legitimate workloads.
  Controls:
    - ResourceQuota per namespace
    - LimitRange per pod/container
    - PriorityClass to protect system pods
    - API server request limits (--max-requests-inflight)
    - etcd quota (--quota-backend-bytes)
    - PodDisruptionBudget for critical workloads
  Attack scenarios:
    - Pod in namespace spawns 10000 children → OOM kills everything
    - Malicious webhook floods API server with slow responses
    - etcd grows to disk full → cluster becomes read-only

E — Elevation of Privilege
  Threat: Container escapes host; pod escalates to cluster-admin.
  Controls:
    - PSA restricted + Gatekeeper/Kyverno
    - No privileged containers
    - Seccomp RuntimeDefault
    - Capabilities: drop ALL
    - No hostPID/hostNetwork/hostPath
    - Kernel CVE patching
    - gVisor/Kata for untrusted workloads
    - Node isolation (taints + dedicated node pools)
  Attack scenarios:
    - Pod with hostPID:true + nsenter → node escape
    - CVE-2022-0185 (Linux kernel heap overflow via unshare) → root
    - CVE-2022-23648 (containerd TOCTOU → arbitrary host read)
    - Runc CVE-2019-5736 → overwrite host runc binary
```

### 19.2 MITRE ATT&CK for Kubernetes

```
MITRE ATT&CK Kubernetes Matrix — Key Techniques
──────────────────────────────────────────────────

Initial Access
  T1190 Exploit Public-Facing App   → Exploit app to get pod shell
  T1078 Valid Accounts              → Stolen kubeconfig/SA token
  T1133 External Remote Services    → Exposed dashboard, Prometheus, etc.

Execution
  T1609 Container Administration    → kubectl exec into pod
  T1610 Deploy Container            → Deploy backdoor container
  T1059 Command/Script Interpreter  → sh/bash spawned in pod

Persistence
  T1525 Implant Internal Image      → Backdoored image in cluster registry
  T1078 Valid Accounts              → Create new SA with permissions
  T1136 Create Account              → Create K8s user/SA/RBAC

Privilege Escalation
  T1611 Escape to Host              → hostPID/hostPath/privileged container
  T1548 Abuse Elevation Control     → Exploit RBAC misconfiguration

Defense Evasion
  T1578 Modify Cloud Compute Infra  → Delete audit logs, modify webhook
  T1070 Indicator Removal           → Clear pod logs, delete events
  T1562 Impair Defenses             → Disable Falco, delete NetworkPolicy

Credential Access
  T1552 Unsecured Credentials       → Read SA token, env vars, secrets
  T1528 Steal Application Token     → Steal OIDC token from pod

Discovery
  T1613 Container and Resource Disc → kubectl get all --all-namespaces
  T1046 Network Service Discovery   → Scan pod network range

Lateral Movement
  T1021 Remote Services             → Use stolen SA token to access other NS
  T1610 Deploy Container            → Deploy container in new namespace

Collection
  T1530 Data from Cloud Storage     → Access cloud storage via instance role
  T1552 Credentials in Files        → Read secrets from /etc/secrets

Impact
  T1485 Data Destruction            → Delete PVCs, corrupt databases
  T1496 Resource Hijacking          → Deploy crypto miners
  T1499 Endpoint DoS                → Resource exhaustion attack
```

---

## 20. CVE Deep-Dives & Exploit Chains

### 20.1 CVE-2018-1002105 — API Server Request Smuggling (CVSS 9.8)

```
Vulnerability: Privilege escalation via API server proxy upgrade.
Affected: Kubernetes <= 1.10.11, <= 1.11.5, <= 1.12.3

Attack Flow:
────────────
1. Attacker has ANY permission that allows connection to a backend service
   via the API server's proxy feature (e.g., pods/exec, pods/attach, or
   access to any service/endpoint).

2. Attacker sends a specially crafted upgrade request to the API server.

3. The API server proxies the connection BUT the connection upgrade header
   causes the API server to:
   a. Forward the connection as an upgraded websocket
   b. Lose control of the connection
   c. The backend now has a direct connection to the attacker
   d. The API server NO LONGER AUTHENTICATES or AUTHORIZES subsequent
      requests on this upgraded connection

4. Attacker sends arbitrary API server requests DIRECTLY to etcd, kubelet,
   or any other backend through this now-unauthenticated tunnel.

5. Result: ANY authenticated user (even with minimal permissions) can
   escalate to cluster-admin.

Detection:
  - Unusual upgrade requests in API server audit log
  - Connections to backends from unexpected users
  - Requests without proper audit entries after upgrade

Mitigation:
  - Upgrade to patched version immediately
  - Restrict pod/exec, pods/attach permissions
  - Use APIServer audit logs to detect exploitation attempts
```

### 20.2 CVE-2019-11246 — Helm Directory Traversal

```
Vulnerability: Helm tar extraction path traversal → arbitrary file write on client.
Affected: Helm < 2.14.1, < 3.0.0

Attack:
  Malicious chart tar contains: ../../../../.bashrc or
  ../../../../etc/cron.d/backdoor
  When rendered: helm fetch / helm install extracts to host filesystem.
  
  Attacker publishes malicious Helm chart to public repository.
  Developer runs: helm install malicious-chart/malicious-1.0.0.tgz
  Arbitrary file written to developer's machine.

Lesson for K8s security:
  - Verify Helm chart provenance (helm pull --verify)
  - Use private Helm registries with signature checking
  - Run Helm in CI with restricted filesystem access
  - Use OCI-based Helm charts (more secure distribution)
```

### 20.3 CVE-2022-3294 — Node Address Auth Bypass

```
Vulnerability: Credential bypass in kubelet authentication.
Affected: Kubernetes 1.25.0 - 1.25.3, 1.24.0 - 1.24.7

Attack:
  The kubelet's webhook authenticator checks the "status.addresses" field of
  the Node object. By manipulating the node's address (via update to the Node
  object), an attacker could cause the kubelet to forward auth requests to
  an attacker-controlled server.
  
  If the node's address is changed to an attacker's IP, the kubelet sends
  all auth webhook requests to the attacker → attacker always returns "success"
  → all requests to kubelet are authenticated.

Why it matters:
  Node objects can be updated by processes with node permission.
  This is why NodeRestriction admission plugin is critical —
  it prevents nodes from modifying other nodes' addresses.

Mitigation:
  - Upgrade to 1.25.4+ / 1.24.8+
  - Enable NodeRestriction admission plugin
  - Monitor Node object modifications in audit log
```

### 20.4 Container Escape Chain — CVE-2022-0185

```
CVE-2022-0185: Linux kernel heap overflow in fs/legacy_fs.c
Affects: Linux kernel < 5.16.2, < 5.15.16, < 5.10.93

Exploit chain for Kubernetes escape:

1. Attacker has code execution inside a container.

2. Container is running without seccomp (Unconfined).
   (Seccomp RuntimeDefault would have blocked unshare() syscall)

3. Attacker calls unshare(CLONE_NEWNS) to create new mount namespace.
   (Requires CAP_SYS_ADMIN — but with user namespaces enabled, can be
   done without any caps from a user namespace)

4. Calls msghdr() with carefully crafted data → heap overflow.

5. Overwrites kernel memory → gains CAP_SYS_ADMIN in initial namespace.

6. Mounts host / via nsenter -t 1 -m -- mount -o bind / /tmp/hostroot

7. Has full host filesystem access → reads /etc/kubernetes/pki/
   Steals admin.conf → cluster-admin.

Defenses that would have stopped this:
  Step 2: Seccomp RuntimeDefault → blocked unshare()
  Step 3: User namespaces disabled (CONFIG_USER_NS=n or sysctl user.max_user_namespaces=0)
  Step 5: Not running as root in container (runAsNonRoot)
  Step 6: Read-only root filesystem
  Step 7: No node-level access to /etc/kubernetes (etcd on separate nodes)

This is why defense-in-depth matters. Each layer independently could stop the attack.
```

---

## 21. Incident Response & Forensics

### 21.1 Kubernetes IR Playbook

```
DETECTION PHASE
───────────────
1. Identify anomaly:
   - Falco alert: "shell in container"
   - Audit log: unexpected exec into pod
   - Metrics: unusual CPU spike (crypto miner)
   - Network traffic: unusual outbound connections

TRIAGE PHASE (first 15 minutes)
────────────────────────────────
2. Identify affected resources:
   kubectl get events --all-namespaces --sort-by='.lastTimestamp' | tail -50
   kubectl get pods --all-namespaces --field-selector=status.phase=Running

3. Check for suspicious pods:
   kubectl get pods -A -o json | jq '.items[] | 
     select(.spec.containers[].securityContext.privileged == true)'

4. Check RBAC changes in audit log:
   grep "clusterrolebindings\|rolebindings" /var/log/kubernetes/audit.log | \
     grep '"verb":"create"\|"verb":"delete"' | tail -20

CONTAINMENT PHASE
──────────────────
5. Isolate compromised pod (network isolation without deleting evidence):
   kubectl label pod <pod-name> -n <ns> network-policy=isolated
   # Apply NetworkPolicy that blocks all traffic to/from pods with this label
   
6. Cordon node if compromised:
   kubectl cordon <node-name>  # prevent new pod scheduling
   # Do NOT drain — preserves evidence

7. Capture pod state before deletion:
   kubectl get pod <pod-name> -n <ns> -o yaml > pod-spec.yaml
   kubectl logs <pod-name> -n <ns> --all-containers > pod-logs.txt
   kubectl exec <pod-name> -n <ns> -- ps aux > pod-processes.txt
   kubectl exec <pod-name> -n <ns> -- netstat -tulpn > pod-netstat.txt

8. Freeze node memory (if available):
   # Use virsh dump / cloud snapshot before rebooting
```

### 21.2 Go: Forensics Collector

```go
// cmd/k8s-forensics/main.go
// Collect forensic artifacts from suspicious pods/nodes
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"

	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/clientcmd"
)

type ForensicsCollector struct {
	client    kubernetes.Interface
	outputDir string
}

type ForensicsReport struct {
	Timestamp    time.Time              `json:"timestamp"`
	PodName      string                 `json:"pod_name"`
	Namespace    string                 `json:"namespace"`
	NodeName     string                 `json:"node_name"`
	PodSpec      *corev1.Pod            `json:"pod_spec"`
	Events       []corev1.Event         `json:"events"`
	Processes    string                 `json:"processes,omitempty"`
	NetworkConns string                 `json:"network_connections,omitempty"`
	Logs         map[string]string      `json:"logs"`
	EnvVars      map[string][]corev1.EnvVar `json:"env_vars"`
	Mounts       map[string][]corev1.VolumeMount `json:"mounts"`
}

func NewForensicsCollector(kubeconfig, outputDir string) (*ForensicsCollector, error) {
	var config *rest.Config
	var err error

	if kubeconfig == "" {
		config, err = rest.InClusterConfig()
	} else {
		config, err = clientcmd.BuildConfigFromFlags("", kubeconfig)
	}
	if err != nil {
		return nil, fmt.Errorf("build kubeconfig: %w", err)
	}

	client, err := kubernetes.NewForConfig(config)
	if err != nil {
		return nil, fmt.Errorf("create client: %w", err)
	}

	if err := os.MkdirAll(outputDir, 0700); err != nil {
		return nil, fmt.Errorf("create output dir: %w", err)
	}

	return &ForensicsCollector{
		client:    client,
		outputDir: outputDir,
	}, nil
}

func (fc *ForensicsCollector) CollectPod(ctx context.Context, namespace, podName string) (*ForensicsReport, error) {
	report := &ForensicsReport{
		Timestamp: time.Now().UTC(),
		PodName:   podName,
		Namespace: namespace,
		Logs:      make(map[string]string),
		EnvVars:   make(map[string][]corev1.EnvVar),
		Mounts:    make(map[string][]corev1.VolumeMount),
	}

	// Collect pod spec
	pod, err := fc.client.CoreV1().Pods(namespace).Get(ctx, podName, metav1.GetOptions{})
	if err != nil {
		return nil, fmt.Errorf("get pod: %w", err)
	}
	report.PodSpec = pod
	report.NodeName = pod.Spec.NodeName

	// Collect per-container data
	for _, c := range pod.Spec.Containers {
		// Logs (last 10000 lines)
		req := fc.client.CoreV1().Pods(namespace).GetLogs(podName, &corev1.PodLogOptions{
			Container: c.Name,
			TailLines: int64Ptr(10000),
		})
		logs, err := req.DoRaw(ctx)
		if err != nil {
			report.Logs[c.Name] = fmt.Sprintf("ERROR: %v", err)
		} else {
			report.Logs[c.Name] = string(logs)
		}

		// Env vars (be careful — may contain secrets)
		report.EnvVars[c.Name] = c.Env
		report.Mounts[c.Name] = c.VolumeMounts
	}

	// Collect events related to this pod
	events, err := fc.client.CoreV1().Events(namespace).List(ctx, metav1.ListOptions{
		FieldSelector: fmt.Sprintf("involvedObject.name=%s", podName),
	})
	if err == nil {
		report.Events = events.Items
	}

	// Try to exec into pod for live forensics (if pod is still running)
	if pod.Status.Phase == corev1.PodRunning {
		// Note: In production, use exec subresource with controlled commands
		// This is simplified for illustration
		fmt.Printf("Pod %s is running — consider: kubectl exec %s -n %s -- ps aux\n",
			podName, podName, namespace)
	}

	// Write report
	reportPath := filepath.Join(fc.outputDir,
		fmt.Sprintf("forensics-%s-%s-%s.json", namespace, podName,
			time.Now().Format("20060102-150405")))

	data, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		return nil, fmt.Errorf("marshal report: %w", err)
	}

	if err := os.WriteFile(reportPath, data, 0600); err != nil {
		return nil, fmt.Errorf("write report: %w", err)
	}

	fmt.Printf("Forensics report written to: %s\n", reportPath)
	return report, nil
}

func int64Ptr(i int64) *int64 { return &i }

func main() {
	if len(os.Args) < 3 {
		fmt.Fprintln(os.Stderr, "Usage: k8s-forensics <namespace> <pod-name>")
		os.Exit(1)
	}

	namespace := os.Args[1]
	podName := os.Args[2]

	collector, err := NewForensicsCollector(
		os.Getenv("KUBECONFIG"),
		"/var/forensics",
	)
	if err != nil {
		fmt.Fprintf(os.Stderr, "init error: %v\n", err)
		os.Exit(1)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
	defer cancel()

	report, err := collector.CollectPod(ctx, namespace, podName)
	if err != nil {
		fmt.Fprintf(os.Stderr, "collection error: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Collected forensics for %s/%s on node %s\n",
		report.Namespace, report.PodName, report.NodeName)
	fmt.Printf("Events: %d, Containers logged: %d\n",
		len(report.Events), len(report.Logs))
}
```

---

## 22. Go Security Tooling — Full Implementations

### 22.1 RBAC Analyzer — Detect Dangerous Permissions

```go
// cmd/rbac-analyzer/main.go
// Analyze RBAC configuration for dangerous permission patterns
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"strings"

	rbacv1 "k8s.io/api/rbac/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/tools/clientcmd"
)

type RBACRisk struct {
	Severity    string   // CRITICAL, HIGH, MEDIUM
	Subject     string
	Namespace   string
	Resource    string
	Verbs       []string
	Description string
	References  []string
}

type RBACAnalyzer struct {
	client kubernetes.Interface
}

// Dangerous permission patterns
type DangerousPermission struct {
	Resources   []string
	Verbs       []string
	Severity    string
	Description string
}

var dangerousPatterns = []DangerousPermission{
	{
		Resources:   []string{"*"},
		Verbs:       []string{"*"},
		Severity:    "CRITICAL",
		Description: "Wildcard resource+verb: equivalent to cluster-admin",
	},
	{
		Resources:   []string{"pods"},
		Verbs:       []string{"create"},
		Severity:    "CRITICAL",
		Description: "pods/create: can escape to cluster-admin via privileged pod",
	},
	{
		Resources:   []string{"pods/exec", "pods/attach"},
		Verbs:       []string{"create"},
		Severity:    "HIGH",
		Description: "pods/exec: can execute arbitrary code in running pods",
	},
	{
		Resources:   []string{"secrets"},
		Verbs:       []string{"get", "list"},
		Severity:    "CRITICAL",
		Description: "secrets/get: can read all secrets including credentials",
	},
	{
		Resources:   []string{"roles", "clusterroles", "rolebindings", "clusterrolebindings"},
		Verbs:       []string{"create", "update", "patch"},
		Severity:    "CRITICAL",
		Description: "RBAC write: can escalate own privileges",
	},
	{
		Resources:   []string{"users", "groups", "serviceaccounts"},
		Verbs:       []string{"impersonate"},
		Severity:    "CRITICAL",
		Description: "impersonate: can act as any user including system:masters",
	},
	{
		Resources:   []string{"validatingwebhookconfigurations", "mutatingwebhookconfigurations"},
		Verbs:       []string{"create", "update", "patch", "delete"},
		Severity:    "CRITICAL",
		Description: "Webhook config write: can bypass admission control",
	},
	{
		Resources:   []string{"namespaces"},
		Verbs:       []string{"delete"},
		Severity:    "HIGH",
		Description: "namespace/delete: can destroy isolation boundaries",
	},
	{
		Resources:   []string{"networkpolicies"},
		Verbs:       []string{"delete"},
		Severity:    "HIGH",
		Description: "networkpolicies/delete: can remove network isolation",
	},
	{
		Resources:   []string{"certificatesigningrequests"},
		Verbs:       []string{"create", "update"},
		Severity:    "HIGH",
		Description: "CSR write: can issue arbitrary X.509 certs",
	},
}

func (a *RBACAnalyzer) Analyze(ctx context.Context) ([]RBACRisk, error) {
	var risks []RBACRisk

	// Analyze ClusterRoleBindings
	crbs, err := a.client.RbacV1().ClusterRoleBindings().List(ctx, metav1.ListOptions{})
	if err != nil {
		return nil, fmt.Errorf("list CRBs: %w", err)
	}

	for _, crb := range crbs.Items {
		// Get the referenced ClusterRole
		cr, err := a.client.RbacV1().ClusterRoles().Get(ctx, crb.RoleRef.Name, metav1.GetOptions{})
		if err != nil {
			continue
		}

		for _, subject := range crb.Subjects {
			subjectRisks := a.analyzeRules(cr.Rules, subject, "cluster-wide")
			risks = append(risks, subjectRisks...)
		}
	}

	// Analyze RoleBindings in all namespaces
	rbs, err := a.client.RbacV1().RoleBindings("").List(ctx, metav1.ListOptions{})
	if err != nil {
		return nil, fmt.Errorf("list RBs: %w", err)
	}

	for _, rb := range rbs.Items {
		var rules []rbacv1.PolicyRule

		if rb.RoleRef.Kind == "ClusterRole" {
			cr, err := a.client.RbacV1().ClusterRoles().Get(ctx, rb.RoleRef.Name, metav1.GetOptions{})
			if err != nil {
				continue
			}
			rules = cr.Rules
		} else {
			r, err := a.client.RbacV1().Roles(rb.Namespace).Get(ctx, rb.RoleRef.Name, metav1.GetOptions{})
			if err != nil {
				continue
			}
			rules = r.Rules
		}

		for _, subject := range rb.Subjects {
			subjectRisks := a.analyzeRules(rules, subject, rb.Namespace)
			risks = append(risks, subjectRisks...)
		}
	}

	return risks, nil
}

func (a *RBACAnalyzer) analyzeRules(
	rules []rbacv1.PolicyRule,
	subject rbacv1.Subject,
	namespace string,
) []RBACRisk {
	var risks []RBACRisk
	subjectStr := fmt.Sprintf("%s:%s", subject.Kind, subject.Name)
	if subject.Namespace != "" {
		subjectStr += "/" + subject.Namespace
	}

	for _, rule := range rules {
		for _, pattern := range dangerousPatterns {
			if matchesPattern(rule, pattern) {
				risks = append(risks, RBACRisk{
					Severity:    pattern.Severity,
					Subject:     subjectStr,
					Namespace:   namespace,
					Resource:    strings.Join(rule.Resources, ","),
					Verbs:       rule.Verbs,
					Description: pattern.Description,
				})
			}
		}
	}
	return risks
}

func matchesPattern(rule rbacv1.PolicyRule, pattern DangerousPermission) bool {
	hasResource := false
	for _, pr := range pattern.Resources {
		for _, rr := range rule.Resources {
			if rr == pr || rr == "*" {
				hasResource = true
				break
			}
		}
	}
	if !hasResource {
		return false
	}

	for _, pv := range pattern.Verbs {
		for _, rv := range rule.Verbs {
			if rv == pv || rv == "*" {
				return true
			}
		}
	}
	return false
}

func main() {
	kubeconfig := os.Getenv("KUBECONFIG")
	if kubeconfig == "" {
		kubeconfig = os.ExpandEnv("$HOME/.kube/config")
	}

	config, err := clientcmd.BuildConfigFromFlags("", kubeconfig)
	if err != nil {
		fmt.Fprintf(os.Stderr, "kubeconfig: %v\n", err)
		os.Exit(1)
	}

	client, err := kubernetes.NewForConfig(config)
	if err != nil {
		fmt.Fprintf(os.Stderr, "client: %v\n", err)
		os.Exit(1)
	}

	analyzer := &RBACAnalyzer{client: client}
	risks, err := analyzer.Analyze(context.Background())
	if err != nil {
		fmt.Fprintf(os.Stderr, "analyze: %v\n", err)
		os.Exit(1)
	}

	// Output as JSON
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")

	// Sort by severity
	critical, high, medium := []RBACRisk{}, []RBACRisk{}, []RBACRisk{}
	for _, r := range risks {
		switch r.Severity {
		case "CRITICAL":
			critical = append(critical, r)
		case "HIGH":
			high = append(high, r)
		default:
			medium = append(medium, r)
		}
	}

	type Summary struct {
		CriticalCount int        `json:"critical_count"`
		HighCount     int        `json:"high_count"`
		MediumCount   int        `json:"medium_count"`
		Critical      []RBACRisk `json:"critical"`
		High          []RBACRisk `json:"high"`
		Medium        []RBACRisk `json:"medium"`
	}

	_ = enc.Encode(Summary{
		CriticalCount: len(critical),
		HighCount:     len(high),
		MediumCount:   len(medium),
		Critical:      critical,
		High:          high,
		Medium:        medium,
	})

	if len(critical) > 0 || len(high) > 0 {
		os.Exit(1) // Non-zero exit for CI integration
	}
}
```

### 22.2 Network Policy Verifier

```go
// pkg/netpol/verifier.go
// Verify NetworkPolicy coverage — find pods without policies
package netpol

import (
	"context"
	"fmt"

	corev1 "k8s.io/api/core/v1"
	networkingv1 "k8s.io/api/networking/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/labels"
	"k8s.io/client-go/kubernetes"
)

type PolicyCoverage struct {
	Namespace    string
	Pod          string
	Labels       map[string]string
	IngressRules int
	EgressRules  int
	Covered      bool
	Risks        []string
}

// VerifyNamespace checks all pods in a namespace for NetworkPolicy coverage.
func VerifyNamespace(ctx context.Context, client kubernetes.Interface, namespace string) ([]PolicyCoverage, error) {
	pods, err := client.CoreV1().Pods(namespace).List(ctx, metav1.ListOptions{})
	if err != nil {
		return nil, fmt.Errorf("list pods: %w", err)
	}

	policies, err := client.NetworkingV1().NetworkPolicies(namespace).List(ctx, metav1.ListOptions{})
	if err != nil {
		return nil, fmt.Errorf("list policies: %w", err)
	}

	var coverages []PolicyCoverage
	for _, pod := range pods.Items {
		cov := analyzePodCoverage(pod, policies.Items)
		coverages = append(coverages, cov)
	}

	return coverages, nil
}

func analyzePodCoverage(pod corev1.Pod, policies []networkingv1.NetworkPolicy) PolicyCoverage {
	cov := PolicyCoverage{
		Namespace: pod.Namespace,
		Pod:       pod.Name,
		Labels:    pod.Labels,
	}

	podLabels := labels.Set(pod.Labels)

	for _, policy := range policies {
		selector, err := metav1.LabelSelectorAsSelector(&policy.Spec.PodSelector)
		if err != nil {
			continue
		}

		// Empty selector = matches all pods
		if selector.Empty() || selector.Matches(podLabels) {
			for _, pt := range policy.Spec.PolicyTypes {
				switch pt {
				case networkingv1.PolicyTypeIngress:
					cov.IngressRules += len(policy.Spec.Ingress)
				case networkingv1.PolicyTypeEgress:
					cov.EgressRules += len(policy.Spec.Egress)
				}
			}
		}
	}

	cov.Covered = cov.IngressRules > 0 || cov.EgressRules > 0

	// Identify risks
	if cov.IngressRules == 0 {
		cov.Risks = append(cov.Risks, "no ingress policy: all incoming traffic allowed")
	}
	if cov.EgressRules == 0 {
		cov.Risks = append(cov.Risks, "no egress policy: all outgoing traffic allowed (including metadata service)")
	}

	return cov
}
```

### 22.3 Secret Scanner — Find Secrets in ConfigMaps/Environment

```go
// pkg/secretscanner/scanner.go
// Scan cluster for secrets stored insecurely (in ConfigMaps or env vars)
package secretscanner

import (
	"context"
	"fmt"
	"regexp"
	"strings"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
)

type SecretFinding struct {
	Type      string // "configmap-key", "env-var", "pod-annotation"
	Namespace string
	Resource  string
	Key       string
	Pattern   string
	Severity  string
}

type SecretPattern struct {
	Name     string
	Pattern  *regexp.Regexp
	Severity string
}

var patterns = []SecretPattern{
	{Name: "AWS Access Key", Pattern: regexp.MustCompile(`AKIA[0-9A-Z]{16}`), Severity: "CRITICAL"},
	{Name: "AWS Secret Key", Pattern: regexp.MustCompile(`(?i)aws.{0,20}secret.{0,20}[0-9a-zA-Z/+]{40}`), Severity: "CRITICAL"},
	{Name: "GCP Service Account Key", Pattern: regexp.MustCompile(`-----BEGIN (RSA |EC )?PRIVATE KEY-----`), Severity: "CRITICAL"},
	{Name: "JWT Token", Pattern: regexp.MustCompile(`eyJ[a-zA-Z0-9]{10,}\.[a-zA-Z0-9]{10,}\.[a-zA-Z0-9_-]{10,}`), Severity: "HIGH"},
	{Name: "GitHub Token", Pattern: regexp.MustCompile(`ghp_[0-9a-zA-Z]{36}`), Severity: "CRITICAL"},
	{Name: "Generic Password", Pattern: regexp.MustCompile(`(?i)(password|passwd|secret|token)[=:]\s*[^\s]{8,}`), Severity: "MEDIUM"},
	{Name: "Database URL", Pattern: regexp.MustCompile(`(?i)(postgres|mysql|mongodb)://[^:]+:[^@]+@`), Severity: "HIGH"},
	{Name: "Private Key Header", Pattern: regexp.MustCompile(`-----BEGIN.*(PRIVATE|CERTIFICATE).*(KEY)?-----`), Severity: "CRITICAL"},
	{Name: "Kubernetes Token", Pattern: regexp.MustCompile(`[a-z0-9]{6}\.[a-z0-9]{16}`), Severity: "HIGH"},
}

func scanValue(value string) []SecretPattern {
	var found []SecretPattern
	for _, p := range patterns {
		if p.Pattern.MatchString(value) {
			found = append(found, p)
		}
	}
	return found
}

// ScanConfigMaps checks all ConfigMaps for credential patterns
func ScanConfigMaps(ctx context.Context, client kubernetes.Interface) ([]SecretFinding, error) {
	var findings []SecretFinding

	cms, err := client.CoreV1().ConfigMaps("").List(ctx, metav1.ListOptions{})
	if err != nil {
		return nil, fmt.Errorf("list configmaps: %w", err)
	}

	for _, cm := range cms.Items {
		for key, value := range cm.Data {
			for _, pattern := range scanValue(value) {
				findings = append(findings, SecretFinding{
					Type:      "configmap-key",
					Namespace: cm.Namespace,
					Resource:  fmt.Sprintf("configmap/%s", cm.Name),
					Key:       key,
					Pattern:   pattern.Name,
					Severity:  pattern.Severity,
				})
			}
		}
	}
	return findings, nil
}

// ScanPodEnvVars checks all pods for credentials in environment variables
func ScanPodEnvVars(ctx context.Context, client kubernetes.Interface) ([]SecretFinding, error) {
	var findings []SecretFinding

	pods, err := client.CoreV1().Pods("").List(ctx, metav1.ListOptions{})
	if err != nil {
		return nil, fmt.Errorf("list pods: %w", err)
	}

	for _, pod := range pods.Items {
		for _, c := range pod.Spec.Containers {
			for _, env := range c.Env {
				if env.Value == "" {
					continue
				}
				// Check key name for suspicious patterns
				keyLower := strings.ToLower(env.Name)
				if strings.Contains(keyLower, "password") ||
					strings.Contains(keyLower, "secret") ||
					strings.Contains(keyLower, "token") ||
					strings.Contains(keyLower, "key") {
					findings = append(findings, SecretFinding{
						Type:      "env-var-suspicious-name",
						Namespace: pod.Namespace,
						Resource:  fmt.Sprintf("pod/%s/container/%s", pod.Name, c.Name),
						Key:       env.Name,
						Pattern:   "suspicious env var name",
						Severity:  "MEDIUM",
					})
				}

				// Scan value for actual secrets
				for _, pattern := range scanValue(env.Value) {
					findings = append(findings, SecretFinding{
						Type:      "env-var-value",
						Namespace: pod.Namespace,
						Resource:  fmt.Sprintf("pod/%s/container/%s", pod.Name, c.Name),
						Key:       env.Name,
						Pattern:   pattern.Name,
						Severity:  pattern.Severity,
					})
				}
			}
		}
	}
	return findings, nil
}
```

---

## Appendix A: Next 3 Steps Roadmap

### For Each Topic Area:

**Authentication & RBAC:**
1. Deploy Dex OIDC + kubelogin, eliminate individual user X.509 certs
2. Run RBAC Analyzer weekly in CI, fail build if CRITICAL findings found
3. Implement just-in-time access: no permanent cluster-admin bindings, use impersonation via Teleport/Pomerium

**Pod Security:**
1. Enable PSA `restricted` enforcement on all non-system namespaces today
2. Deploy OPA Gatekeeper with constraint library for image digest enforcement
3. Test seccomp profile with strace profiling: `strace -c -p <pid>` → allowlist actual syscalls

**Network Policy:**
1. Audit all namespaces for missing default-deny: `kubectl get netpol -A | grep default-deny`
2. Block metadata service (169.254.169.254) in all egress policies immediately
3. Move to Cilium for L7 policy enforcement if using L4-only CNI

**Secrets:**
1. Deploy ESO (External Secrets Operator) + AWS Secrets Manager / Vault
2. Audit secrets in ConfigMaps: run SecretScanner above, fix all CRITICAL findings
3. Enable encryption-at-rest for secrets + configmaps in API server config

**Supply Chain:**
1. Enable Cosign signing in CI pipeline for all image builds
2. Deploy Sigstore Policy Controller to reject unsigned images in production
3. Integrate Grype/Trivy into CI, fail on CRITICAL CVEs

---

## Appendix B: References

- CIS Kubernetes Benchmark: https://www.cisecurity.org/benchmark/kubernetes
- NIST SP 800-190 Container Security: https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-190.pdf
- Kubernetes Security Docs: https://kubernetes.io/docs/concepts/security/
- MITRE ATT&CK for Containers: https://attack.mitre.org/matrices/enterprise/containers/
- CNCF Security Whitepaper: https://github.com/cncf/tag-security/blob/main/security-whitepaper/v2/CNCF_cloud-native-security-whitepaper-May2022-v2.pdf
- NSA/CISA Kubernetes Hardening Guide: https://media.defense.gov/2022/Aug/29/2003066362/-1/-1/0/CTR_KUBERNETES_HARDENING_GUIDANCE_1.2_20220829.PDF
- SPIFFE Spec: https://spiffe.io/docs/latest/spiffe-about/spiffe-concepts/
- Sigstore: https://docs.sigstore.dev/
- OPA/Gatekeeper: https://open-policy-agent.github.io/gatekeeper/
- Falco: https://falco.org/docs/
- Trivy: https://aquasecurity.github.io/trivy/
- kube-bench: https://github.com/aquasecurity/kube-bench