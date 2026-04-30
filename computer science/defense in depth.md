# Defense in Depth: Comprehensive Security Guide

## Executive Summary

Defense in Depth (DiD) is a layered security strategy where multiple independent controls are deployed across infrastructure, network, application, and data planes—ensuring that compromise of one layer doesn't lead to total system failure. Each layer operates under the principle of **least privilege, isolation, and fail-secure**, creating overlapping security domains that increase attacker cost while providing detection/response opportunities. In modern cloud/datacenter environments, DiD spans physical hardware (HSMs, TPMs), hypervisor isolation (SEV, TDX), network segmentation (VPCs, service meshes), identity boundaries (SPIFFE/SPIRE, OPA), runtime protection (seccomp, AppArmor), and data protection (encryption-at-rest/in-transit, key hierarchies). The goal: **assume breach, minimize blast radius, enable rapid detection/response**, and architect systems where single-point compromise requires multiple independent failures across security boundaries.

---

## 1. Foundational Principles

### Core Tenets
- **Assume Breach**: Design assuming attackers have already compromised one or more layers
- **Least Privilege**: Grant minimum required permissions/access at every layer
- **Fail Secure**: System failures default to deny/safe state, not permissive
- **Defense Diversity**: Use different security mechanisms (prevent homogenous attack surface)
- **Auditability**: Every layer produces verifiable logs/telemetry for forensics
- **Blast Radius Containment**: Limit lateral movement via isolation boundaries

### Layered Security Model (Conceptual)

```
┌─────────────────────────────────────────────────────────────────┐
│                      SECURITY LAYERS (DiD)                      │
├─────────────────────────────────────────────────────────────────┤
│  7. GOVERNANCE & POLICY    │ Compliance, Audit, Change Control  │
├─────────────────────────────────────────────────────────────────┤
│  6. DATA PROTECTION        │ Encryption, DLP, Key Mgmt, Masking │
├─────────────────────────────────────────────────────────────────┤
│  5. APPLICATION SECURITY   │ Input Validation, AuthZ, Secrets   │
├─────────────────────────────────────────────────────────────────┤
│  4. COMPUTE ISOLATION      │ Containers, VMs, Sandboxes, CFI    │
├─────────────────────────────────────────────────────────────────┤
│  3. NETWORK SEGMENTATION   │ Firewalls, mTLS, Service Mesh, NSG │
├─────────────────────────────────────────────────────────────────┤
│  2. IDENTITY & ACCESS      │ RBAC, MFA, Zero Trust, Attestation │
├─────────────────────────────────────────────────────────────────┤
│  1. INFRASTRUCTURE         │ Hardware Root of Trust, Secure Boot│
└─────────────────────────────────────────────────────────────────┘
         ▲                          ▲                    ▲
         │                          │                    │
    Detection/           Monitoring/Logging        Incident Response
    Prevention           (Observability)           (Recovery)
```

---

## 2. Layer-by-Layer Breakdown

### Layer 1: Infrastructure & Physical Security

**Purpose**: Establish hardware root of trust, prevent physical tampering, ensure boot integrity

```
Physical Datacenter Security Architecture
─────────────────────────────────────────────────────────────────

┌──────────────────────────────────────────────────────────────┐
│  PHYSICAL PERIMETER                                          │
│  ├─ Biometric Access + Multi-Factor (badge + PIN/bio)       │
│  ├─ Security Guards, CCTV, Mantrap Doors                    │
│  └─ Visitor Logging, Background Checks                      │
└──────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  HARDWARE ROOT OF TRUST                                      │
│  ┌─────────────────────┐   ┌──────────────────────┐         │
│  │ TPM 2.0 / HSM       │   │ Secure Boot Chain    │         │
│  │ - Sealed Keys       │   │ - UEFI Signed        │         │
│  │ - PCR Measurements  │   │ - Bootloader Verify  │         │
│  │ - Attestation       │   │ - Kernel Signature   │         │
│  └─────────────────────┘   └──────────────────────┘         │
└──────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  CONFIDENTIAL COMPUTING                                      │
│  ├─ AMD SEV-SNP: Encrypted VM Memory + Attestation          │
│  ├─ Intel TDX: Trust Domain Extensions                      │
│  ├─ ARM CCA: Confidential Compute Architecture              │
│  └─ Prevents hypervisor/admin from reading workload memory  │
└──────────────────────────────────────────────────────────────┘
```

**Key Controls**:
- **TPM/HSM**: Store cryptographic keys in hardware, measure boot state
- **Secure Boot**: Cryptographically verify firmware → bootloader → OS kernel
- **Confidential VMs**: AMD SEV, Intel TDX for memory encryption against admin
- **Supply Chain**: Vendor attestation, firmware verification, component tracking

**Threat Model**:
- Physical access leading to cold boot attacks, hardware implants
- Compromised firmware/BIOS persistence
- Rogue admins with hypervisor access reading memory

**Mitigations**:
```bash
# Verify Secure Boot status
mokutil --sb-state
# Check TPM measurements
tpm2_pcrread sha256

# AMD SEV VM attestation (example)
sevctl verify --cert /path/to/cert
```

---

### Layer 2: Identity & Access Management (IAM)

**Purpose**: Authenticate all entities, authorize based on least privilege, provide continuous verification

```
Zero Trust Identity Architecture
─────────────────────────────────────────────────────────────────

                    ┌─────────────────────┐
                    │   Identity Provider │
                    │   (OIDC/SAML/SPIFFE)│
                    └──────────┬──────────┘
                               │
                               ▼
        ┌──────────────────────┴──────────────────────┐
        │                                              │
   ┌────▼────┐                                   ┌────▼────┐
   │  Human  │                                   │ Workload│
   │Identity │                                   │Identity │
   │  (MFA)  │                                   │ (SPIFFE)│
   └────┬────┘                                   └────┬────┘
        │                                              │
        │  JWT/Token                       X.509-SVID │
        │                                              │
        └──────────────┬────────────────────┬─────────┘
                       ▼                    ▼
              ┌─────────────────────────────────┐
              │     Authorization Policy       │
              │  (OPA, Cedar, RBAC/ABAC)       │
              │  ├─ Roles & Permissions        │
              │  ├─ Context-Aware (IP, time)   │
              │  └─ Just-in-Time (JIT) Access  │
              └─────────────┬───────────────────┘
                            ▼
              ┌─────────────────────────────────┐
              │      Protected Resources        │
              │   (APIs, Databases, Services)   │
              └─────────────────────────────────┘
```

**Key Controls**:
- **Strong Authentication**: MFA (FIDO2/WebAuthn), certificate-based for workloads
- **Workload Identity**: SPIFFE/SPIRE for service-to-service authentication
- **Authorization**: RBAC, ABAC with context (time, location, risk score)
- **Least Privilege**: Just-in-time access, temporary credentials
- **Session Management**: Short-lived tokens, rotation, revocation

**Real-World Blueprint**:
```yaml
# SPIFFE/SPIRE Trust Domain Example
trustDomain: "prod.example.com"

workloadAttestors:
  - k8s:
      podLabel: "app.kubernetes.io/name"
      namespace: "secure-namespace"
  - unix:
      uid: 1001

selectors:
  - k8s:sa:payments-service
  - k8s:ns:payments

# SVID TTL: 1 hour, rotation every 30 min
svid_ttl: "1h"
```

**Threat Model**:
- Credential theft (phishing, malware)
- Privilege escalation via misconfigured RBAC
- Service account token abuse in Kubernetes
- Lateral movement with stolen credentials

**Mitigations**:
- Enforce MFA for all human access
- Use hardware security keys (YubiKey, Titan)
- Implement workload identity with short-lived certificates
- Apply OPA policies for dynamic authorization
- Enable audit logging on all auth decisions

---

### Layer 3: Network Segmentation & Micro-Segmentation

**Purpose**: Isolate network traffic, enforce least-privilege connectivity, prevent lateral movement

```
Cloud Network Segmentation (AWS/Azure/GCP)
─────────────────────────────────────────────────────────────────

┌────────────────────────────────────────────────────────────────┐
│                         INTERNET                               │
└────────────────┬───────────────────────────────────────────────┘
                 │
                 ▼
    ┌────────────────────────┐
    │   Edge/WAF Layer       │ ← DDoS Protection, Bot Mitigation
    │   (CloudFlare, ALB)    │
    └────────────┬───────────┘
                 │
                 ▼
    ┌────────────────────────────────────────────────────────────┐
    │              VPC / Virtual Network                         │
    │  ┌──────────────────────┐  ┌──────────────────────────┐   │
    │  │  Public Subnet       │  │   Private Subnet         │   │
    │  │  (DMZ)               │  │   (App Tier)             │   │
    │  │  - Bastion/Jump      │  │   - Application Servers  │   │
    │  │  - NAT Gateway       │  │   - Service Mesh (Istio) │   │
    │  └──────────┬───────────┘  └──────────┬───────────────┘   │
    │             │                          │                   │
    │             │  Security Groups (SG)    │                   │
    │             │  Network ACLs (NACL)     │                   │
    │             │                          │                   │
    │             └──────────┬───────────────┘                   │
    │                        │                                   │
    │            ┌───────────▼──────────────┐                    │
    │            │   Private Subnet         │                    │
    │            │   (Data Tier)            │                    │
    │            │   - RDS, DynamoDB        │                    │
    │            │   - No Public IP         │                    │
    │            │   - Encryption in Transit│                    │
    │            └──────────────────────────┘                    │
    └────────────────────────────────────────────────────────────┘
                             │
                             ▼
             ┌───────────────────────────────┐
             │   Private Link / VPC Peering  │
             │   (Cross-VPC, On-Prem)        │
             └───────────────────────────────┘
```

**Kubernetes Network Policy (Micro-Segmentation)**:
```
Pod-to-Pod Network Isolation
─────────────────────────────────────────────────────────────────

Namespace: payments
┌────────────────────────────────────────────────────────┐
│  ┌──────────────┐          ┌──────────────┐            │
│  │ Payment API  │─────────▶│ Payment DB   │            │
│  │ (Pod)        │   ✓      │ (Pod)        │            │
│  └──────────────┘          └──────────────┘            │
│         │                                               │
│         │ NetworkPolicy: DENY default                  │
│         │ ALLOW: payments-api → payments-db:5432       │
│         │                                               │
│         ▼                                               │
│    ┌──────────────┐                                    │
│    │ Fraud ML     │ ✗ Blocked from DB                  │
│    │ (Pod)        │                                    │
│    └──────────────┘                                    │
└────────────────────────────────────────────────────────┘

Namespace: public-web (Different NS)
┌────────────────────────────────────────────────────────┐
│  ┌──────────────┐                                      │
│  │ Web Frontend │ ✗ CANNOT reach payments namespace    │
│  │ (Pod)        │   (Namespace isolation)              │
│  └──────────────┘                                      │
└────────────────────────────────────────────────────────┘
```

**Key Controls**:
- **VPC/VNet Segmentation**: Isolate workloads by trust boundary (DMZ, app, data)
- **Security Groups**: Stateful firewall at instance/ENI level (whitelist approach)
- **Network ACLs**: Stateless subnet-level firewall (defense diversity)
- **Service Mesh mTLS**: Cilium, Istio, Linkerd for encrypted pod-to-pod
- **Zero Trust Networks**: No implicit trust, verify every connection

**Kubernetes NetworkPolicy Example**:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: payments-db-ingress
  namespace: payments
spec:
  podSelector:
    matchLabels:
      app: payments-db
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: payments-api
    ports:
    - protocol: TCP
      port: 5432
```

**Threat Model**:
- Lateral movement after initial compromise
- Data exfiltration via unrestricted egress
- Container breakout accessing host network
- Man-in-the-middle on unencrypted traffic

**Mitigations**:
- Default-deny NetworkPolicies in Kubernetes
- Enforce mTLS with service mesh (automatic SPIFFE identity)
- Use PrivateLink/Service Endpoints for PaaS (avoid public internet)
- Deploy IDS/IPS at network choke points
- Implement egress filtering (allow-list external domains)

---

### Layer 4: Compute & Runtime Isolation

**Purpose**: Isolate workloads at process/container/VM level, prevent breakout, enforce execution policies

```
Container Security Stack (Defense in Depth)
─────────────────────────────────────────────────────────────────

┌────────────────────────────────────────────────────────────────┐
│                     Application Code                           │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────┐
│  LAYER 4A: Runtime Security                                    │
│  ├─ Seccomp: Restrict syscalls (e.g., deny ptrace, mount)     │
│  ├─ AppArmor/SELinux: Mandatory Access Control (MAC)          │
│  ├─ Capabilities: Drop CAP_SYS_ADMIN, CAP_NET_RAW, etc.       │
│  └─ Read-Only Root FS: Prevent malicious writes               │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────┐
│  LAYER 4B: Container Runtime                                   │
│  ├─ gVisor (runsc): User-space kernel sandbox                 │
│  ├─ Kata Containers: Lightweight VM per container             │
│  ├─ Firecracker: MicroVM isolation (AWS Lambda)               │
│  └─ runc (default): Namespace + cgroup isolation              │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────┐
│  LAYER 4C: Kernel Isolation                                    │
│  ├─ Namespaces: PID, NET, MNT, UTS, IPC, USER                 │
│  ├─ Cgroups: Resource limits (CPU, memory, I/O)               │
│  ├─ Seccomp-BPF: eBPF filters for syscall inspection          │
│  └─ LSMs: SELinux, AppArmor for MAC policies                  │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────┐
│  LAYER 4D: Hypervisor (if VM-based)                            │
│  ├─ KVM, Xen, Hyper-V: Hardware virtualization (VT-x/AMD-V)   │
│  ├─ SEV/TDX: Encrypted memory isolation                       │
│  └─ SR-IOV: Direct hardware passthrough with isolation        │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         ▼
               ┌─────────────────────┐
               │   Hardware (CPU)    │
               │   Ring 0 / SGX      │
               └─────────────────────┘
```

**Key Controls**:
- **Namespace Isolation**: PID, network, mount, IPC, UTS, user namespaces
- **Seccomp Profiles**: Restrict syscalls to minimum required (deny ptrace, reboot)
- **AppArmor/SELinux**: MAC policies enforcing file/network access
- **Read-Only Root FS**: Prevent tampering with container filesystem
- **Dropped Capabilities**: Remove dangerous Linux capabilities (CAP_SYS_ADMIN)
- **User Namespace Remapping**: Run containers as non-root inside user NS
- **Runtime Protection**: Falco, Tetragon for runtime behavior monitoring

**Kubernetes Pod Security Standards**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 10001
    fsGroup: 10001
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: myapp:v1.0.0
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
    volumeMounts:
    - name: tmp
      mountPath: /tmp
  volumes:
  - name: tmp
    emptyDir: {}
```

**Threat Model**:
- Container breakout to host kernel
- Privilege escalation via misconfigured capabilities
- Malicious syscalls (mount, reboot, ptrace)
- Supply chain attack via compromised base image

**Mitigations**:
- Use distroless/minimal base images (Google Distroless, Chainguard)
- Sign and verify container images (Sigstore Cosign)
- Enforce Pod Security Standards (Restricted profile)
- Deploy gVisor/Kata for high-security workloads
- Run eBPF-based runtime security (Falco, Tetragon)
- Regularly scan images for CVEs (Trivy, Grype)

---

### Layer 5: Application Security

**Purpose**: Secure application code, validate inputs, manage secrets, prevent injection attacks

```
Application Security Controls
─────────────────────────────────────────────────────────────────

┌────────────────────────────────────────────────────────────────┐
│  INPUT VALIDATION                                              │
│  ├─ Schema Validation (JSON Schema, Protobuf)                 │
│  ├─ Type Safety (strong typing in Go/Rust)                    │
│  ├─ Allowlist over Denylist                                   │
│  └─ Sanitize: SQL, XSS, Command Injection                     │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────┐
│  AUTHENTICATION & AUTHORIZATION                                │
│  ├─ JWT with RS256/ES256 (not HS256 with shared secrets)      │
│  ├─ OIDC/OAuth2 for delegation                                │
│  ├─ Per-request AuthZ checks (not session-based only)         │
│  └─ Rate Limiting + CAPTCHA for brute-force                   │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────┐
│  SECRETS MANAGEMENT                                            │
│  ├─ Never hardcode secrets in code/config                     │
│  ├─ Use Vault, AWS Secrets Manager, K8s Secrets + CSI         │
│  ├─ Short-lived credentials (rotating tokens)                 │
│  ├─ Envelope encryption for secrets-at-rest                   │
│  └─ Audit all secret access                                   │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────┐
│  SECURE COMMUNICATION                                          │
│  ├─ TLS 1.3 for all network traffic                           │
│  ├─ mTLS for service-to-service (via service mesh)            │
│  ├─ Certificate rotation + pinning                            │
│  └─ HSTS, CSP, X-Frame-Options headers                        │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────┐
│  VULNERABILITY MANAGEMENT                                      │
│  ├─ SAST: Static analysis (Semgrep, CodeQL)                   │
│  ├─ DAST: Runtime testing (ZAP, Burp)                         │
│  ├─ SCA: Dependency scanning (Snyk, Dependabot)               │
│  └─ Fuzzing: AFL++, libFuzzer for input validation            │
└────────────────────────────────────────────────────────────────┘
```

**Key Controls**:
- **Input Validation**: Strict schema validation, type safety
- **Output Encoding**: Context-aware encoding (HTML, SQL, JSON)
- **Parameterized Queries**: Prevent SQL injection
- **AuthZ at Every Layer**: Verify permissions on each request
- **Secrets Management**: Vault, Sealed Secrets, CSI drivers
- **Dependency Management**: Automated CVE scanning, SBOM generation

**Secrets Management (Kubernetes + Vault)**:
```yaml
# External Secrets Operator (sync from Vault to K8s)
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: db-credentials
spec:
  refreshInterval: 15m
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: db-secret
    creationPolicy: Owner
  data:
  - secretKey: password
    remoteRef:
      key: secret/data/postgres
      property: password
```

**Threat Model**:
- SQL injection, XSS, CSRF attacks
- Hardcoded secrets leaked in Git/logs
- Deserialization vulnerabilities
- Dependency confusion, supply chain attacks

**Mitigations**:
- Use prepared statements/ORMs for database queries
- Implement CSP headers to mitigate XSS
- Store secrets in Vault/HSM, inject at runtime
- Sign and verify all dependencies (SLSA provenance)
- Enable WAF for HTTP traffic (ModSecurity, AWS WAF)

---

### Layer 6: Data Protection

**Purpose**: Protect data confidentiality and integrity at rest and in transit

```
Data Encryption & Key Management Architecture
─────────────────────────────────────────────────────────────────

┌────────────────────────────────────────────────────────────────┐
│              KEY HIERARCHY (Envelope Encryption)               │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌────────────────────────────────────────────────────┐       │
│  │  Root Key (HSM/KMS)                                │       │
│  │  - AWS KMS, Azure Key Vault, GCP KMS              │       │
│  │  - FIPS 140-2 Level 3 HSM                         │       │
│  │  - Never leaves HSM                               │       │
│  └──────────────────┬─────────────────────────────────┘       │
│                     │ Encrypts                                │
│                     ▼                                         │
│  ┌────────────────────────────────────────────────────┐       │
│  │  Data Encryption Keys (DEKs)                      │       │
│  │  - Per-tenant, per-table, per-object              │       │
│  │  - Stored encrypted by Root Key                   │       │
│  │  - Short TTL (hourly rotation)                    │       │
│  └──────────────────┬─────────────────────────────────┘       │
│                     │ Encrypts                                │
│                     ▼                                         │
│  ┌────────────────────────────────────────────────────┐       │
│  │  Actual Data                                       │       │
│  │  - Database records, S3 objects, disk blocks      │       │
│  │  - AES-256-GCM, ChaCha20-Poly1305                 │       │
│  └────────────────────────────────────────────────────┘       │
└────────────────────────────────────────────────────────────────┘

           DATA PROTECTION IN TRANSIT
┌────────────────────────────────────────────────────────────────┐
│  Client ◄──TLS 1.3 (AES-256-GCM)──► Load Balancer             │
│            ◄──mTLS (Service Mesh)──► Application              │
│                      ◄──TLS 1.3──► Database                    │
│                                                                │
│  Certificate Management:                                      │
│  - cert-manager (K8s), Let's Encrypt, Venafi                  │
│  - Automated rotation (90-day certs)                          │
│  - OCSP stapling for revocation checks                        │
└────────────────────────────────────────────────────────────────┘
```

**Key Controls**:
- **Encryption at Rest**: AES-256 for block storage, databases, object storage
- **Encryption in Transit**: TLS 1.3, mTLS for service-to-service
- **Key Management**: Envelope encryption with HSM-backed root keys
- **Data Classification**: Label sensitive data (PII, PCI, PHI)
- **Data Loss Prevention (DLP)**: Scan for sensitive data leakage
- **Backup Encryption**: Encrypted backups with separate key hierarchy

**AWS S3 Encryption Example**:
```bash
# Server-Side Encryption with KMS
aws s3api put-object \
  --bucket my-secure-bucket \
  --key sensitive-data.json \
  --body data.json \
  --server-side-encryption aws:kms \
  --ssekms-key-id arn:aws:kms:us-east-1:123456789012:key/abc-123

# Enforce encryption in bucket policy
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Deny",
    "Principal": "*",
    "Action": "s3:PutObject",
    "Resource": "arn:aws:s3:::my-secure-bucket/*",
    "Condition": {
      "StringNotEquals": {
        "s3:x-amz-server-side-encryption": "aws:kms"
      }
    }
  }]
}
```

**Threat Model**:
- Data exfiltration via stolen disks/snapshots
- Man-in-the-middle attacks on unencrypted traffic
- Key compromise leading to bulk data decryption
- Insider threats accessing plaintext data

**Mitigations**:
- Enable encryption by default on all storage
- Use separate KMS keys per tenant/environment
- Implement key rotation (automated, 90-day cycles)
- Deploy mTLS with short-lived certificates (cert-manager)
- Monitor certificate expiry and anomalous decryption requests

---

### Layer 7: Governance, Compliance & Monitoring

**Purpose**: Continuous monitoring, audit logging, policy enforcement, incident response

```
Security Observability & Governance Stack
─────────────────────────────────────────────────────────────────

┌────────────────────────────────────────────────────────────────┐
│  POLICY AS CODE (Preventive Controls)                         │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ OPA/Gatekeeper: K8s admission control                   │ │
│  │ - Block privileged pods                                 │ │
│  │ - Enforce image signing (Sigstore)                      │ │
│  │ - Require resource limits                               │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────────┐
│  LOGGING & AUDIT (Detective Controls)                         │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Infrastructure: CloudTrail, Azure Monitor, GCP Ops      │ │
│  │ Application: Structured JSON logs (Zap, Logrus)         │ │
│  │ Kubernetes: Audit logs (API server events)              │ │
│  │ Network: Flow logs (VPC, NSG)                           │ │
│  │ Runtime: Falco (syscall monitoring)                     │ │
│  └────────────────┬─────────────────────────────────────────┘ │
│                   │ Ship to SIEM                              │
│                   ▼                                           │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ SIEM / Log Aggregation                                  │ │
│  │ - Splunk, Elastic Security, Datadog Security            │ │
│  │ - Correlation rules for attack patterns                 │ │
│  │ - Anomaly detection (ML-based)                          │ │
│  └────────────────┬─────────────────────────────────────────┘ │
└────────────────────┼───────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────────┐
│  ALERTING & INCIDENT RESPONSE                                 │
│  ├─ PagerDuty, Opsgenie for on-call                           │
│  ├─ Runbooks for common incidents                             │
│  ├─ Automated response (SOAR): Isolate compromised pods       │
│  └─ Forensics: Snapshot, preserve logs, timeline analysis     │
└────────────────────────────────────────────────────────────────┘
```

**Key Controls**:
- **Audit Logging**: Immutable logs for all API/resource access
- **SIEM Integration**: Centralized log aggregation + correlation
- **Compliance Scanning**: CIS benchmarks, NIST 800-53, PCI-DSS automation
- **Policy Enforcement**: OPA for admission control, runtime policies
- **Vulnerability Scanning**: Continuous CVE detection in images/infra
- **Incident Response**: Automated playbooks, forensics tooling

**OPA Admission Policy (Block Privileged Pods)**:
```rego
package kubernetes.admission

deny[msg] {
  input.request.kind.kind == "Pod"
  container := input.request.object.spec.containers[_]
  container.securityContext.privileged == true
  msg := sprintf("Privileged containers not allowed: %v", [container.name])
}
```

**Falco Rule (Detect Shell in Container)**:
```yaml
- rule: Shell spawned in container
  desc: Detect shell execution inside container
  condition: >
    spawned_process and container and
    proc.name in (bash, sh, zsh)
  output: >
    Shell spawned in container (user=%user.name container=%container.name
    image=%container.image.repository:%container.image.tag)
  priority: WARNING
```

**Threat Model**:
- Undetected breaches due to insufficient logging
- Policy drift leading to misconfigurations
- Slow incident response times
- Compliance violations (GDPR, HIPAA)

**Mitigations**:
- Enable audit logs on all control planes (K8s API, cloud APIs)
- Forward logs to immutable storage (S3 with Object Lock)
- Deploy runtime security (Falco, Tetragon) for anomaly detection
- Automate compliance scanning (Prowler, ScoutSuite)
- Practice incident response with tabletop exercises

---

## 3. Cross-Cutting Concerns

### Supply Chain Security

```
Software Supply Chain Security
─────────────────────────────────────────────────────────────────

┌──────────────────────────────────────────────────────────────┐
│  Source Code                                                 │
│  ├─ Signed commits (GPG)                                     │
│  ├─ Branch protection rules                                 │
│  └─ Code review requirements                                │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────┐
│  Build Pipeline                                              │
│  ├─ Ephemeral build environments (no persistent state)      │
│  ├─ SLSA Level 3 provenance generation                      │
│  ├─ SCA scanning (dependencies)                             │
│  └─ SAST/Linting                                            │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────┐
│  Artifact Signing                                            │
│  ├─ Sigstore Cosign: Sign container images                  │
│  ├─ SBOM generation (SPDX, CycloneDX)                       │
│  ├─ Store signatures in OCI registry                        │
│  └─ Attestations for build provenance                       │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────┐
│  Deployment                                                  │
│  ├─ Verify image signatures (Kyverno, OPA)                  │
│  ├─ Check SBOM for vulnerable dependencies                  │
│  ├─ Enforce SLSA provenance requirements                    │
│  └─ Audit trail of what was deployed                        │
└──────────────────────────────────────────────────────────────┘
```

**Key Controls**:
- Sign all commits and tags (GPG, SSH signing)
- Generate SLSA provenance for builds
- Sign container images with Cosign
- Verify signatures at deployment time
- Maintain SBOM for all artifacts

---

### Zero Trust Architecture

```
Zero Trust Principles Applied
─────────────────────────────────────────────────────────────────

Traditional Perimeter Model         Zero Trust Model
────────────────────────           ──────────────────────
┌────────────────────┐             ┌──────────────────────┐
│   Trusted Internal │             │  Every Request       │
│   Network          │             │  Authenticated +     │
│   (implicit trust) │             │  Authorized          │
└────────────────────┘             └──────────────────────┘
        │                                   │
        ▼                                   ▼
┌────────────────────┐             ┌──────────────────────┐
│  Firewall Perimeter│             │  Policy Decision     │
│  (static rules)    │             │  Point (PDP)         │
└────────────────────┘             │  - Context-aware     │
                                   │  - Continuous verify │
                                   └──────────────────────┘

Zero Trust Pillars:
─────────────────────────────────────────────────────────────────
1. Verify Explicitly
   - Authenticate every request (no implicit trust)
   - Use all available data points (identity, device, location, behavior)

2. Use Least Privilege Access
   - Just-in-time + just-enough-access
   - Risk-based adaptive policies

3. Assume Breach
   - Minimize blast radius (segmentation)
   - End-to-end encryption
   - Continuous monitoring + analytics
```

---

## 4. Practical Implementation Patterns

### Multi-Tenant Kubernetes Security

```
Kubernetes Multi-Tenancy Defense in Depth
─────────────────────────────────────────────────────────────────

┌────────────────────────────────────────────────────────────────┐
│  Tenant A Namespace                    Tenant B Namespace      │
│  ┌─────────────────┐                  ┌─────────────────┐     │
│  │ Pod (workload)  │                  │ Pod (workload)  │     │
│  └─────────────────┘                  └─────────────────┘     │
│         │                                      │               │
│         │ Network Policy                       │               │
│         │ (deny inter-tenant)                  │               │
│         └──────────────┬───────────────────────┘               │
│                        │                                       │
│                        ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Control Plane Isolation                                  │ │
│  │ ├─ RBAC: Tenant-specific roles (no cluster-admin)       │ │
│  │ ├─ ResourceQuotas: CPU/memory limits per namespace      │ │
│  │ ├─ Pod Security Standards: Enforce restricted profile   │ │
│  │ ├─ NetworkPolicies: Default deny + explicit allow       │ │
│  │ └─ Admission Control: OPA/Kyverno for policy            │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘

Isolation Strategies:
- Namespace per tenant (soft multi-tenancy)
- Virtual clusters (vCluster, Kamaji) for stronger isolation
- Separate clusters per tenant (strongest isolation, highest cost)
```

### Cloud-Agnostic IAM with SPIFFE

```bash
# SPIRE Server deployment (trust domain: prod.company.com)
spire-server run \
  -config /etc/spire/server.conf \
  -trustDomain prod.company.com

# SPIRE Agent attestation (Kubernetes)
spire-agent run \
  -config /etc/spire/agent.conf \
  -joinToken $(cat /run/spire/token)

# Register workload identity
spire-server entry create \
  -parentID spiffe://prod.company.com/spire/agent/k8s_psat/prod-cluster/node1 \
  -spiffeID spiffe://prod.company.com/payments/api \
  -selector k8s:ns:payments \
  -selector k8s:sa:payments-api \
  -ttl 3600

# Application fetches X.509-SVID certificate
curl --unix-socket /tmp/spire-agent/public/api.sock \
  http://localhost/svids -d '{"spiffe_id": "spiffe://prod.company.com/payments/api"}'
```

---

## 5. Threat Models & Attack Scenarios

### Scenario 1: Container Escape to Host

**Attack Path**:
1. Attacker gains RCE in container via app vulnerability
2. Exploits kernel vulnerability to escape container
3. Gains host access, pivots to other nodes

**Defense Layers Triggered**:
- **Layer 5 (App)**: Input validation should prevent initial RCE
- **Layer 4 (Runtime)**: Seccomp blocks dangerous syscalls
- **Layer 4 (Runtime)**: gVisor/Kata prevents kernel access
- **Layer 7 (Monitoring)**: Falco detects abnormal syscalls
- **Layer 2 (IAM)**: Pod has no ServiceAccount token to pivot

### Scenario 2: Stolen Credentials Lateral Movement

**Attack Path**:
1. Phishing compromises employee laptop
2. Attacker steals AWS credentials from ~/.aws/credentials
3. Attempts to access production resources

**Defense Layers Triggered**:
- **Layer 2 (IAM)**: MFA required, stolen long-term creds insufficient
- **Layer 2 (IAM)**: Workload identities use short-lived tokens (no static creds)
- **Layer 3 (Network)**: PrivateLink prevents direct database access from internet
- **Layer 7 (Monitoring)**: Anomalous API calls trigger CloudTrail alerts
- **Layer 7 (Response)**: Automated revocation of compromised credentials

### Scenario 3: Supply Chain Compromise

**Attack Path**:
1. Attacker compromises upstream dependency
2. Malicious code injected into container image
3. Deployed to production

**Defense Layers Triggered**:
- **Supply Chain**: SBOM scanning detects unknown dependency
- **Supply Chain**: Unsigned image blocked by admission controller
- **Layer 4 (Runtime)**: Seccomp blocks malicious syscalls
- **Layer 7 (Monitoring)**: Runtime behavior anomaly detected by Falco
- **Layer 7 (Response)**: Automated pod termination and forensic snapshot

---

## 6. Testing & Validation

### Security Testing Pyramid

```
Security Testing Layers
─────────────────────────────────────────────────────────────────

              ┌─────────────────────────┐
              │  Red Team / Pen Test    │  ← Manual, Infrequent
              │  (Full attack sim)      │
              └─────────────────────────┘
                        │
          ┌─────────────┴──────────────┐
          │  Chaos Engineering         │  ← Periodic
          │  (Fault injection)         │
          └────────────────────────────┘
                      │
        ┌─────────────┴──────────────────┐
        │  Integration Security Tests    │  ← CI/CD
        │  (DAST, API fuzzing)           │
        └────────────────────────────────┘
                    │
      ┌─────────────┴─────────────────────┐
      │  Unit Security Tests               │  ← Every commit
      │  (SAST, SCA, secret scanning)      │
      └────────────────────────────────────┘
```

### Commands for Security Validation

```bash
# 1. SAST (Static Analysis)
semgrep --config=auto --error --strict .

# 2. SCA (Dependency Scanning)
trivy fs --severity HIGH,CRITICAL .
grype dir:.

# 3. Secret Scanning
gitleaks detect --source . --verbose

# 4. Container Image Scan
trivy image --severity HIGH,CRITICAL myapp:latest

# 5. Infrastructure as Code Scan
checkov -d ./terraform/
tfsec ./terraform/

# 6. Kubernetes Manifest Scan
kubesec scan pod.yaml
kube-score score pod.yaml

# 7. Runtime Security (Falco)
kubectl apply -f https://raw.githubusercontent.com/falcosecurity/charts/master/falco/values.yaml

# 8. Network Policy Testing
kubectl auth can-i --as=system:serviceaccount:payments:payments-api \
  create pods -n other-namespace  # Should be 'no'

# 9. Penetration Testing (OWASP ZAP)
docker run -v $(pwd):/zap/wrk:rw -t owasp/zap2docker-stable \
  zap-baseline.py -t https://myapp.example.com -r report.html

# 10. Chaos Testing (Litmus)
kubectl apply -f https://litmuschaos.github.io/litmus/litmus-operator-latest.yaml
```

---

## 7. Rollout & Rollback Strategy

### Progressive Rollout with Security Gates

```
Deployment Pipeline with Security Checkpoints
─────────────────────────────────────────────────────────────────

┌───────────┐     ┌───────────┐     ┌───────────┐     ┌──────────┐
│   DEV     │────▶│  STAGING  │────▶│   CANARY  │────▶│   PROD   │
└───────────┘     └───────────┘     └───────────┘     └──────────┘
     │                  │                  │                 │
     ▼                  ▼                  ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Security Gates (Must Pass Before Promotion)                     │
│ ├─ Image signature verification (Cosign)                        │
│ ├─ CVE scan (zero HIGH/CRITICAL)                                │
│ ├─ SBOM validation                                              │
│ ├─ Policy compliance (OPA/Kyverno)                              │
│ ├─ Runtime behavior baseline (no anomalies)                     │
│ └─ Automated rollback on security alert                         │
└─────────────────────────────────────────────────────────────────┘

Canary Analysis:
- Deploy to 5% of traffic
- Monitor for 30 minutes:
  * Security alerts (Falco, WAF)
  * Error rate < 0.1%
  * Latency p99 < baseline + 10%
- Auto-rollback if thresholds breached
```

### Emergency Rollback Procedure

```bash
# 1. Immediate traffic cutover
kubectl set image deployment/myapp myapp=myapp:previous-good-version

# 2. Isolate compromised resources
kubectl label pod -l app=myapp compromised=true
kubectl apply -f emergency-network-policy.yaml  # Deny all

# 3. Preserve forensic evidence
kubectl exec compromised-pod -- tar czf /tmp/forensics.tar.gz /var/log /proc
kubectl cp compromised-pod:/tmp/forensics.tar.gz ./forensics/

# 4. Revoke compromised credentials
aws iam delete-access-key --access-key-id AKIA...
vault token revoke -self

# 5. Trigger incident response runbook
pagerduty incident create --title "Security Incident: Container Escape" \
  --urgency high --service myapp
```

---

## 8. References & Standards

### Industry Frameworks
- **NIST Cybersecurity Framework**: Risk-based security controls
- **CIS Benchmarks**: Hardening guidelines for OS, cloud, K8s
- **MITRE ATT&CK**: Adversary tactics, techniques, procedures
- **SLSA**: Supply chain security levels (L1-L4)
- **OWASP Top 10**: Web application security risks

### Cloud Security
- **AWS Well-Architected (Security Pillar)**: IAM, encryption, logging
- **Azure Security Benchmark**: CIS-aligned security controls
- **GCP Security Best Practices**: VPC Service Controls, IAM, encryption
- **CSA STAR**: Cloud security certification program

### Kubernetes Security
- **NSA/CISA Kubernetes Hardening Guide**: Official gov't hardening guide
- **CIS Kubernetes Benchmark**: Automated compliance scanning
- **Pod Security Standards**: Privileged, Baseline, Restricted profiles

### Compliance
- **PCI-DSS**: Payment card data security
- **HIPAA**: Healthcare data protection
- **GDPR**: EU data privacy regulation
- **SOC 2**: Trust service criteria audit

---

## Next 3 Steps

1. **Assess Current State**: Run automated security scans across all layers
   ```bash
   # Audit Kubernetes cluster
   kube-bench run --targets master,node,policies
   
   # Scan container images in registry
   trivy image --list-all-pkgs $(kubectl get pods -A -o jsonpath='{.items[*].spec.containers[*].image}' | tr ' ' '\n' | sort -u)
   
   # Review IAM permissions
   aws iam get-account-authorization-details > iam-audit.json
   ```

2. **Implement Missing Controls**: Prioritize by risk (high-impact, low-effort first)
   - Enable audit logging on all API servers (K8s, cloud control planes)
   - Deploy NetworkPolicies with default-deny
   - Enforce Pod Security Standards (Restricted profile)
   - Implement workload identity (SPIFFE/SPIRE)

3. **Continuous Validation**: Automate security testing in CI/CD
   - Add security gates to deployment pipelines
   - Schedule regular penetration testing (quarterly)
   - Conduct tabletop exercises for incident response
   - Measure Mean Time to Detect (MTTD) and Mean Time to Respond (MTTR)

**Key Principle**: Defense in Depth is not "set and forget"—it requires continuous monitoring, testing, and evolution as threats adapt. Prioritize automation, assume breach, and minimize blast radius at every layer.