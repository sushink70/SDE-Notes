# Comprehensive Secure SDLC Guide

## Executive Summary (4-8 Lines)

Secure SDLC integrates security controls, threat modeling, and verification at every phase—from requirements through decommissioning—shifting security left while maintaining defense-in-depth. Core principle: **security is a continuous property, not a gate**. Modern S-SDLC combines policy-as-code, automated verification (SAST/DAST/SCA/IAST), supply chain integrity (SLSA, Sigstore), runtime protection (RASP, eBPF), and continuous threat modeling. Key success factors: immutable audit trails, zero-trust architecture, least-privilege by default, cryptographic attestation of artifacts, and automated rollback. Production-grade S-SDLC treats security findings as build failures, requires signed commits/images, enforces SBOM generation, and integrates security testing in CI/CD as mandatory gates. Failure modes: alert fatigue, false positives blocking deployments, and security theater without runtime validation.

---

## 1. Secure SDLC Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SECURE SDLC LIFECYCLE                                │
│                                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │ REQUIREMENTS │───▶│   DESIGN     │───▶│ DEVELOPMENT  │                  │
│  │  & PLANNING  │    │ & MODELING   │    │ & BUILDING   │                  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                  │
│         │                   │                   │                            │
│         ▼                   ▼                   ▼                            │
│  ┌─────────────────────────────────────────────────────┐                   │
│  │            CONTINUOUS THREAT MODELING                │                   │
│  │  • Attack Surface Analysis  • Trust Boundaries       │                   │
│  │  • STRIDE/PASTA/LINDDUN    • Security Requirements   │                   │
│  └─────────────────────────────────────────────────────┘                   │
│         │                   │                   │                            │
│         ▼                   ▼                   ▼                            │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   TESTING    │───▶│  DEPLOYMENT  │───▶│  OPERATIONS  │                  │
│  │ & VALIDATION │    │ & RELEASE    │    │ & MONITORING │                  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                  │
│         │                   │                   │                            │
│         └───────────────────┴───────────────────┘                            │
│                             │                                                 │
│                             ▼                                                 │
│                  ┌──────────────────────┐                                   │
│                  │   DECOMMISSIONING    │                                   │
│                  │  & DATA LIFECYCLE    │                                   │
│                  └──────────────────────┘                                   │
│                                                                               │
│  ═══════════════════════════════════════════════════════════════════════   │
│                     CONTINUOUS SECURITY ACTIVITIES                           │
│  ═══════════════════════════════════════════════════════════════════════   │
│                                                                               │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌──────────────────┐   │
│  │ Policy-as-Code (OPA)│  │ Secret Management   │  │ Compliance Check │   │
│  │ RBAC/ABAC Controls  │  │ Vault, KMS, HSM     │  │ CIS, PCI, SOC2   │   │
│  └─────────────────────┘  └─────────────────────┘  └──────────────────┘   │
│                                                                               │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌──────────────────┐   │
│  │ Supply Chain Sec    │  │ Vulnerability Mgmt  │  │ Incident Response│   │
│  │ SLSA, SBOM, Sigstore│  │ CVE Scanning, Patch │  │ SIEM, SOAR, IR   │   │
│  └─────────────────────┘  └─────────────────────┘  └──────────────────┘   │
└───────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────┐
│                     SECURITY TOOLING INTEGRATION                            │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Developer ──▶ Git Commit ──▶ Pre-commit Hooks ──▶ CI Pipeline             │
│    Workstation       │              │                    │                  │
│         │            │              ▼                    ▼                  │
│         │            │      ┌──────────────┐    ┌──────────────┐          │
│         │            │      │ SAST/Linters │    │  Supply Chain│          │
│         │            │      │ Semgrep, etc │    │  Validation  │          │
│         │            │      └──────────────┘    └──────────────┘          │
│         │            │              │                    │                  │
│         │            ▼              ▼                    ▼                  │
│         │      ┌──────────────────────────────────────────────┐           │
│         │      │         BUILD & ARTIFACT CREATION            │           │
│         │      │  • Reproducible Builds  • Sign Artifacts     │           │
│         │      │  • Generate SBOM        • Attest Provenance  │           │
│         │      └──────────────┬───────────────────────────────┘           │
│         │                     │                                             │
│         │                     ▼                                             │
│         │      ┌──────────────────────────────────────────────┐           │
│         │      │      CONTAINER/ARTIFACT SCANNING             │           │
│         │      │  Trivy, Grype, Clair, Snyk, Anchore          │           │
│         │      └──────────────┬───────────────────────────────┘           │
│         │                     │                                             │
│         │                     ▼                                             │
│         │      ┌──────────────────────────────────────────────┐           │
│         │      │       POLICY ENFORCEMENT (OPA/Kyverno)       │           │
│         │      │  • Image signatures  • Resource limits       │           │
│         │      │  • Network policies  • Security contexts     │           │
│         │      └──────────────┬───────────────────────────────┘           │
│         │                     │                                             │
│         │                     ▼                                             │
│         │      ┌──────────────────────────────────────────────┐           │
│         │      │          STAGING DEPLOYMENT                  │           │
│         │      │  DAST, Fuzzing, Chaos Engineering            │           │
│         │      └──────────────┬───────────────────────────────┘           │
│         │                     │                                             │
│         │                     ▼                                             │
│         │      ┌──────────────────────────────────────────────┐           │
│         │      │       PRODUCTION DEPLOYMENT                  │           │
│         │      │  • Blue/Green  • Canary  • Feature Flags     │           │
│         │      └──────────────┬───────────────────────────────┘           │
│         │                     │                                             │
│         └─────────────────────┴──────────────┐                             │
│                                               ▼                             │
│                              ┌──────────────────────────────┐              │
│                              │   RUNTIME SECURITY           │              │
│                              │  Falco, Tetragon, Tracee     │              │
│                              │  RASP, WAF, API Gateway      │              │
│                              └──────────────────────────────┘              │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Phase-by-Phase Deep Dive

### Phase 1: Requirements & Planning

**Objective**: Define security requirements as first-class functional requirements, not afterthoughts.

**Key Activities**:
- **Security Requirements Elicitation**: Identify confidentiality, integrity, availability needs; compliance obligations (GDPR, HIPAA, PCI-DSS, SOC2, FedRAMP)
- **Threat Intelligence Integration**: Incorporate known attack patterns, APT tactics (MITRE ATT&CK), industry-specific threats
- **Risk Assessment**: Classify data (PII, PHI, financial), determine impact of breach, define acceptable risk tolerance
- **Security Champions Assignment**: Embed security SMEs in each dev team

**Threat Model**:
```
THREAT: Requirements ambiguity leads to missing security controls
MITIGATION:
  • Use Security Requirements Framework (OWASP ASVS, NIST 800-53)
  • Document security user stories: "As attacker, I want to..."
  • Define abuse cases alongside use cases
  • Establish Security Level Objectives (SLOs): e.g., "99.9% auth requests <100ms"
```

**Actionable Steps**:
```bash
# 1. Initialize threat model repo
git init secure-sdlc-requirements
cd secure-sdlc-requirements

# 2. Create security requirements template
cat > security-requirements.yaml <<EOF
project: myapp
risk_level: high  # low, medium, high, critical
data_classification:
  - PII
  - financial
compliance_frameworks:
  - PCI-DSS
  - SOC2-Type2
security_requirements:
  authentication:
    - MFA required for admin access
    - OAuth2/OIDC for user auth
    - Session timeout: 15min idle
  authorization:
    - RBAC with least privilege
    - Policy-as-code (OPA)
  data_protection:
    - Encryption at rest (AES-256)
    - Encryption in transit (TLS 1.3+)
    - Key rotation every 90 days
  logging_monitoring:
    - Audit all privileged operations
    - Retain logs 1 year
    - Alert on anomalies <5min
EOF

# 3. Validate against framework
# (Use tools like OpenCRE, OWASP SAMM)
```

**Architecture Decision Record (ADR) Template**:
```markdown
# ADR-001: Encryption Key Management

## Status: Accepted

## Context
Need to protect encryption keys for data-at-rest and secrets management.

## Decision
Use AWS KMS with customer-managed keys (CMK), auto-rotation enabled.

## Consequences
- Positive: FIPS 140-2 Level 3, audit trail, multi-region
- Negative: AWS lock-in, cost per API call
- Alternatives: HashiCorp Vault (self-managed), GCP KMS, Azure Key Vault

## Security Implications
- Key material never leaves HSM
- Requires IAM policy for key usage
- CloudTrail logs all key operations
```

---

### Phase 2: Design & Threat Modeling

**Objective**: Architect systems with security boundaries, trust zones, and defense-in-depth layers.

**Threat Modeling Methodologies**:
1. **STRIDE** (Microsoft): Spoofing, Tampering, Repudiation, Info Disclosure, DoS, Elevation of Privilege
2. **PASTA** (Process for Attack Simulation and Threat Analysis): Business-driven, 7-stage
3. **LINDDUN**: Privacy threat modeling (Linkability, Identifiability, Non-repudiation, Detectability, Disclosure, Unawareness, Non-compliance)
4. **Attack Trees**: Visual representation of attack paths

**Architecture Patterns**:
```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ZERO-TRUST ARCHITECTURE                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│   ┌────────────┐         ┌────────────┐         ┌────────────┐         │
│   │   User     │         │  Service   │         │  Service   │         │
│   │  Client    │         │     A      │         │     B      │         │
│   └─────┬──────┘         └─────┬──────┘         └─────┬──────┘         │
│         │                      │                      │                  │
│         │ mTLS + JWT           │ mTLS + JWT           │                  │
│         ▼                      ▼                      ▼                  │
│   ┌─────────────────────────────────────────────────────────┐          │
│   │              POLICY ENFORCEMENT POINT (PEP)             │          │
│   │  • Identity verification (SPIFFE/SPIRE)                  │          │
│   │  • Authorization (OPA, RBAC/ABAC)                        │          │
│   │  • Network policy enforcement                            │          │
│   └─────────────┬───────────────────────────────────────────┘          │
│                 │                                                         │
│                 ▼                                                         │
│   ┌─────────────────────────────────────────────────────────┐          │
│   │           POLICY DECISION POINT (PDP)                   │          │
│   │  • Centralized policy engine (OPA, Cedar)               │          │
│   │  • Context-aware decisions (user, resource, env)        │          │
│   └─────────────────────────────────────────────────────────┘          │
│                                                                           │
│   ┌─────────────────────────────────────────────────────────┐          │
│   │              TRUST BOUNDARIES                            │          │
│   │  ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐    │          │
│   │  │ Public │──▶│  DMZ   │──▶│Internal│──▶│ Private│    │          │
│   │  │Internet│   │ (WAF)  │   │Services│   │  Data  │    │          │
│   │  └────────┘   └────────┘   └────────┘   └────────┘    │          │
│   │      ▲            ▲            ▲            ▲          │          │
│   │      └────────────┴────────────┴────────────┘          │          │
│   │            Microsegmentation (Cilium/Calico)           │          │
│   └─────────────────────────────────────────────────────────┘          │
└───────────────────────────────────────────────────────────────────────┘
```

**Threat Model Example (STRIDE on Kubernetes API Server)**:
```
COMPONENT: Kubernetes API Server

THREATS:
┌───────────────┬──────────────────────────────────────┬─────────────────────┐
│ STRIDE Cat    │ Threat                               │ Mitigation          │
├───────────────┼──────────────────────────────────────┼─────────────────────┤
│ Spoofing      │ Attacker impersonates legitimate     │ • mTLS client certs │
│               │ user/service account                 │ • OIDC integration  │
│               │                                      │ • Webhook auth      │
├───────────────┼──────────────────────────────────────┼─────────────────────┤
│ Tampering     │ Unauthorized modification of etcd    │ • etcd encryption   │
│               │ data, RBAC policies                  │ • Audit logging     │
│               │                                      │ • Admission webhooks│
├───────────────┼──────────────────────────────────────┼─────────────────────┤
│ Repudiation   │ Cannot prove who made API call       │ • Audit logs (JSON) │
│               │                                      │ • Immutable logs    │
│               │                                      │ • Request tracing   │
├───────────────┼──────────────────────────────────────┼─────────────────────┤
│ Info          │ Secrets exposed in logs, responses   │ • Secret encryption │
│ Disclosure    │                                      │ • RBAC on secrets   │
│               │                                      │ • Redaction in logs │
├───────────────┼──────────────────────────────────────┼─────────────────────┤
│ DoS           │ API server overwhelmed by requests   │ • Rate limiting     │
│               │                                      │ • Resource quotas   │
│               │                                      │ • Priority classes  │
├───────────────┼──────────────────────────────────────┼─────────────────────┤
│ Elevation of  │ Container escape, privilege escalation│ • Pod Security      │
│ Privilege     │                                      │   Standards (PSS)   │
│               │                                      │ • AppArmor/SELinux  │
│               │                                      │ • seccomp profiles  │
└───────────────┴──────────────────────────────────────┴─────────────────────┘
```

**Actionable Steps**:
```bash
# 1. Install threat modeling tool
# Options: OWASP Threat Dragon, Microsoft Threat Modeling Tool, IriusRisk
docker run -p 3000:3000 owasp/threat-dragon:latest

# 2. Create Data Flow Diagram (DFD)
# Export as YAML/JSON for version control

# 3. Document trust boundaries
cat > trust-boundaries.md <<EOF
# Trust Boundaries

## Level 0: Public Internet
- No trust
- All input validated
- Rate limiting applied

## Level 1: DMZ (Load Balancer, WAF)
- Limited trust
- TLS termination
- DDoS protection

## Level 2: Application Tier
- Service-to-service mTLS
- Pod Security Standards enforced
- Network policies restrict egress

## Level 3: Data Tier
- Encryption at rest
- Private subnets
- IAM database authentication
EOF

# 4. Generate STRIDE analysis
# (Automate with tools like PyTM)
pip install pytm
cat > threat_model.py <<'EOF'
from pytm import TM, Server, Dataflow, Boundary, Actor

tm = TM("Kubernetes App")
tm.description = "Microservices on K8s"

internet = Boundary("Internet")
dmz = Boundary("DMZ")
cluster = Boundary("K8s Cluster")

user = Actor("User")
user.inBoundary = internet

lb = Server("Load Balancer")
lb.inBoundary = dmz

api = Server("API Server")
api.inBoundary = cluster

Dataflow(user, lb, "HTTPS Request")
Dataflow(lb, api, "mTLS")

tm.process()
EOF
python threat_model.py
```

---

### Phase 3: Development & Building

**Objective**: Write secure code, enforce secure coding standards, prevent vulnerabilities at commit time.

**Secure Coding Practices**:
1. **Input Validation**: Allowlist > Denylist, sanitize all external input
2. **Output Encoding**: Context-aware (HTML, SQL, JSON, LDAP)
3. **Parameterized Queries**: Prevent SQL injection
4. **Cryptography**: Use vetted libraries (NaCl, libsodium), avoid custom crypto
5. **Error Handling**: No sensitive info in errors, fail securely
6. **Least Privilege**: Service accounts with minimal permissions

**Pre-Commit Security Checks**:
```
┌────────────────────────────────────────────────────────────────┐
│              PRE-COMMIT SECURITY PIPELINE                       │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Developer Commit                                                │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────┐                                           │
│  │  Git Hooks       │                                           │
│  │  .pre-commit-    │                                           │
│  │  config.yaml     │                                           │
│  └────────┬─────────┘                                           │
│           │                                                      │
│           ├──▶ Secret Scanning (gitleaks, trufflehog)           │
│           │    └──▶ BLOCK if secrets found                      │
│           │                                                      │
│           ├──▶ SAST Linting (semgrep, gosec, bandit)            │
│           │    └──▶ FAIL on critical findings                   │
│           │                                                      │
│           ├──▶ Dependency Check (govulncheck, cargo audit)      │
│           │    └──▶ WARN on known CVEs                          │
│           │                                                      │
│           ├──▶ License Compliance (licensee)                    │
│           │    └──▶ BLOCK on incompatible licenses              │
│           │                                                      │
│           ├──▶ Commit Signature Verification                    │
│           │    └──▶ REQUIRE GPG/SSH signed commits              │
│           │                                                      │
│           └──▶ Code Formatting (gofmt, rustfmt, black)          │
│                └──▶ Auto-fix or fail                            │
│                                                                  │
│  If ALL pass ──▶ Push to Remote                                │
│  If ANY fail  ──▶ REJECT commit, show fix instructions         │
└────────────────────────────────────────────────────────────────┘
```

**Actionable Steps**:
```bash
# 1. Setup pre-commit hooks
pip install pre-commit

cat > .pre-commit-config.yaml <<EOF
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.1
    hooks:
      - id: gitleaks

  - repo: https://github.com/returntocorp/semgrep
    rev: v1.45.0
    hooks:
      - id: semgrep
        args: ['--config=auto', '--error']

  - repo: https://github.com/golangci/golangci-lint
    rev: v1.55.2
    hooks:
      - id: golangci-lint
        args: ['--enable=gosec']

  - repo: https://github.com/trufflesecurity/trufflehog
    rev: v3.63.0
    hooks:
      - id: trufflehog
        args: ['filesystem', '.', '--fail']

  - repo: local
    hooks:
      - id: verify-commit-signature
        name: Verify GPG Signature
        entry: git verify-commit HEAD
        language: system
        always_run: true
EOF

pre-commit install
pre-commit run --all-files

# 2. Configure SAST for Go
cat > .golangci.yml <<EOF
linters:
  enable:
    - gosec          # Security issues
    - govet          # Correctness
    - staticcheck    # Static analysis
    - errcheck       # Unchecked errors
    - revive         # Linting

linters-settings:
  gosec:
    severity: medium
    confidence: medium
    excludes:
      - G104  # Unchecked errors (covered by errcheck)
    config:
      G301: "0644"  # File permissions
EOF

golangci-lint run --enable-all

# 3. Enforce dependency scanning
# For Go:
go install golang.org/x/vuln/cmd/govulncheck@latest
govulncheck ./...

# For Rust:
cargo install cargo-audit
cargo audit

# For Python:
pip install safety
safety check --json

# 4. Sign commits
git config --global commit.gpgsign true
git config --global user.signingkey YOUR_GPG_KEY

# 5. Create security policy
cat > SECURITY.md <<EOF
# Security Policy

## Reporting Vulnerabilities
Email: security@yourcompany.com
PGP Key: [link]
Response SLA: 24 hours

## Supported Versions
| Version | Supported |
|---------|-----------|
| 2.x     | ✅        |
| 1.x     | ⚠️ (EOL Q2 2024) |
EOF
```

**Supply Chain Security (SLSA Framework)**:
```
┌─────────────────────────────────────────────────────────────┐
│          SLSA LEVELS & REQUIREMENTS                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  SLSA Level 1: Documentation                                 │
│  └──▶ Build process documented and versioned                │
│                                                               │
│  SLSA Level 2: Provenance                                    │
│  └──▶ Build service generates signed provenance              │
│       • Who built it, when, from what source                 │
│       • Cosign/Sigstore signatures on container images       │
│                                                               │
│  SLSA Level 3: Hardened Builds                               │
│  └──▶ Build environment is ephemeral and isolated            │
│       • GitHub Actions, GitLab CI with isolated runners      │
│       • No persistent state between builds                   │
│                                                               │
│  SLSA Level 4: Hermetic & Reproducible                       │
│  └──▶ Builds are bit-for-bit reproducible                    │
│       • Bazel, Nix for hermetic builds                       │
│       • Two-party review required                            │
└─────────────────────────────────────────────────────────────┘
```

**Example: Signing Container Images**:
```bash
# Install cosign
go install github.com/sigstore/cosign/v2/cmd/cosign@latest

# Generate keypair
cosign generate-key-pair

# Sign image
cosign sign --key cosign.key myregistry.io/myapp:v1.0.0

# Generate SBOM
syft myregistry.io/myapp:v1.0.0 -o spdx-json > sbom.spdx.json

# Attest SBOM
cosign attest --key cosign.key --predicate sbom.spdx.json myregistry.io/myapp:v1.0.0

# Verify signature
cosign verify --key cosign.pub myregistry.io/myapp:v1.0.0

# Policy enforcement in K8s (Kyverno)
cat > require-signed-images.yaml <<EOF
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-image-signatures
spec:
  validationFailureAction: enforce
  background: false
  webhookTimeoutSeconds: 30
  rules:
    - name: check-signature
      match:
        any:
        - resources:
            kinds:
              - Pod
      verifyImages:
      - imageReferences:
        - "myregistry.io/*"
        attestors:
        - count: 1
          entries:
          - keys:
              publicKeys: |-
                -----BEGIN PUBLIC KEY-----
                [YOUR COSIGN PUBLIC KEY]
                -----END PUBLIC KEY-----
EOF
```

---

### Phase 4: Testing & Validation

**Objective**: Validate security controls through automated and manual testing before production.

**Security Testing Types**:
```
┌──────────────────────────────────────────────────────────────────┐
│                   SECURITY TESTING PYRAMID                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│                      ┌──────────────┐                             │
│                      │   MANUAL     │  ← Red Team, Pen Test       │
│                      │  SECURITY    │    (Quarterly/Annual)       │
│                      │  TESTING     │                             │
│                      └──────────────┘                             │
│                   ┌──────────────────────┐                        │
│                   │      DYNAMIC         │  ← DAST, Fuzzing       │
│                   │  APPLICATION SEC     │    API Testing         │
│                   │   TESTING (DAST)     │    (Weekly)            │
│                   └──────────────────────┘                        │
│              ┌────────────────────────────────┐                   │
│              │   INTERACTIVE APPLICATION       │  ← IAST          │
│              │     SECURITY TESTING           │    Runtime        │
│              │         (IAST)                 │    (Continuous)   │
│              └────────────────────────────────┘                   │
│         ┌────────────────────────────────────────┐                │
│         │      STATIC APPLICATION SECURITY       │  ← SAST, SCA   │
│         │          TESTING (SAST/SCA)            │    Linters     │
│         │                                        │    (Per Commit)│
│         └────────────────────────────────────────┘                │
│    ┌─────────────────────────────────────────────────┐           │
│    │           UNIT & INTEGRATION TESTS               │  ← TDD    │
│    │         WITH SECURITY ASSERTIONS                 │    BDD    │
│    │                                                   │  (Per PR) │
│    └─────────────────────────────────────────────────┘           │
└──────────────────────────────────────────────────────────────────┘
```

**Testing Techniques**:

1. **Static Analysis (SAST)**: Code scanning without execution
   - Tools: Semgrep, SonarQube, CodeQL, Bandit (Python), gosec (Go), cargo-clippy (Rust)
   
2. **Dynamic Analysis (DAST)**: Black-box testing of running app
   - Tools: OWASP ZAP, Burp Suite, Nuclei, w3af
   
3. **Interactive (IAST)**: Agent-based runtime analysis
   - Tools: Contrast Security, Synopsys Seeker
   
4. **Fuzzing**: Automated input generation to find crashes/vulnerabilities
   - Tools: AFL++, libFuzzer, go-fuzz, cargo-fuzz, Jazzer (Java)
   
5. **Dependency Scanning (SCA)**: Known vulnerabilities in libraries
   - Tools: Dependabot, Snyk, Grype, Trivy, OWASP Dependency-Check

**Fuzzing Pipeline**:
```
┌─────────────────────────────────────────────────────────────┐
│                    FUZZING WORKFLOW                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────┐                                          │
│  │  Build Fuzz    │  ← Instrument code with coverage        │
│  │   Targets      │    sanitizers (ASan, UBSan, MSan)       │
│  └───────┬────────┘                                          │
│          │                                                    │
│          ▼                                                    │
│  ┌────────────────┐                                          │
│  │  Seed Corpus   │  ← Valid inputs, regression tests       │
│  │  Generation    │    Protocol samples, edge cases         │
│  └───────┬────────┘                                          │
│          │                                                    │
│          ▼                                                    │
│  ┌────────────────┐                                          │
│  │  Run Fuzzer    │  ← AFL++, libFuzzer, Hongfuzz           │
│  │  (Continuous)  │    Mutation-based, coverage-guided      │
│  └───────┬────────┘                                          │
│          │                                                    │
│          ├──▶ Crash/Hang Detected?                           │
│          │         │                                          │
│          │         ├─Yes─▶ Minimize Testcase                 │
│          │         │       └──▶ Create Reproducer            │
│          │         │             └──▶ File Bug + Patch       │
│          │         │                                          │
│          │         └─No──▶ Continue Fuzzing                  │
│          │                                                    │
│          ▼                                                    │
│  ┌────────────────┐                                          │
│  │  Coverage      │  ← Track code paths exercised           │
│  │  Monitoring    │    Aim for >80% coverage                │
│  └────────────────┘                                          │
└─────────────────────────────────────────────────────────────┘
```

**Actionable Steps**:
```bash
# 1. Setup DAST with OWASP ZAP
docker run -t ghcr.io/zaproxy/zaproxy:stable \
  zap-baseline.py -t https://staging.myapp.com \
  -r zap-report.html

# 2. Fuzzing with AFL++ (for C/C++)
# Install AFL++
git clone https://github.com/AFLplusplus/AFLplusplus
cd AFLplusplus && make && sudo make install

# Compile target with instrumentation
afl-clang-fast++ -fsanitize=address -g myprogram.cpp -o myprogram

# Create seed corpus
mkdir inputs
echo "valid_input" > inputs/seed1

# Run fuzzer
afl-fuzz -i inputs -o findings -- ./myprogram @@

# 3. Fuzzing with libFuzzer (Go)
cat > parser_fuzz_test.go <<'EOF'
//go:build gofuzz
package parser

func FuzzParseInput(data []byte) int {
    _, err := ParseInput(string(data))
    if err != nil {
        return 0
    }
    return 1
}
EOF

go test -fuzz=FuzzParseInput -fuzztime=60s

# 4. Container scanning in CI
# .gitlab-ci.yml
cat > .gitlab-ci.yml <<'EOF'
security_scan:
  stage: test
  image: aquasec/trivy:latest
  script:
    - trivy image --severity HIGH,CRITICAL --exit-code 1 $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  allow_failure: false
EOF

# 5. API security testing with Nuclei
nuclei -u https://api.myapp.com \
  -t ~/nuclei-templates/cves/ \
  -t ~/nuclei-templates/vulnerabilities/ \
  -severity critical,high \
  -json -o nuclei-results.json

# 6. Create security test cases
cat > security_test.go <<'EOF'
func TestAuthenticationBypass(t *testing.T) {
    // Attempt to access protected resource without token
    req := httptest.NewRequest("GET", "/admin", nil)
    w := httptest.NewRecorder()
    
    handler.ServeHTTP(w, req)
    
    if w.Code != http.StatusUnauthorized {
        t.Errorf("Expected 401, got %d", w.Code)
    }
}

func TestSQLInjection(t *testing.T) {
    maliciousInput := "'; DROP TABLE users; --"
    _, err := db.Query("SELECT * FROM users WHERE name = ?", maliciousInput)
    if err != nil {
        t.Fatal("Parameterized query failed")
    }
}

func TestCSRFProtection(t *testing.T) {
    // Request without CSRF token should fail
    req := httptest.NewRequest("POST", "/transfer", strings.NewReader("amount=1000"))
    req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
    
    w := httptest.NewRecorder()
    handler.ServeHTTP(w, req)
    
    assert.Equal(t, http.StatusForbidden, w.Code)
}
EOF
```

---

### Phase 5: Deployment & Release

**Objective**: Deploy securely with minimal blast radius, rollback capability, and continuous validation.

**Deployment Security Architecture**:
```
┌──────────────────────────────────────────────────────────────────────┐
│                     SECURE DEPLOYMENT PIPELINE                        │
├──────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  1. BUILD ARTIFACTS (CI)                                    │     │
│  │     • Reproducible builds                                   │     │
│  │     • Sign binaries/containers (cosign)                     │     │
│  │     • Generate SBOM (syft, cyclonedx)                       │     │
│  │     • Store in artifact registry (Harbor, Artifactory)      │     │
│  └───────────────────────┬────────────────────────────────────┘     │
│                          │                                             │
│                          ▼                                             │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  2. PRE-DEPLOYMENT GATES                                    │     │
│  │     ✓ All security scans passed                             │     │
│  │     ✓ Code review approved (2+ reviewers)                   │     │
│  │     ✓ Change management ticket approved                     │     │
│  │     ✓ Rollback plan documented                              │     │
│  └───────────────────────┬────────────────────────────────────┘     │
│                          │                                             │
│                          ▼                                             │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  3. DEPLOYMENT STRATEGY                                     │     │
│  │                                                              │     │
│  │     ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │     │
│  │     │ Blue/Green  │    │   Canary    │    │   Rolling   │ │     │
│  │     └──────┬──────┘    └──────┬──────┘    └──────┬──────┘ │     │
│  │            │                   │                   │         │     │
│  │            └───────────────────┴───────────────────┘         │     │
│  │                          │                                   │     │
│  │                          ▼                                   │     │
│  │               ┌──────────────────────┐                      │     │
│  │               │  Feature Flags       │                      │     │
│  │               │  (LaunchDarkly, etc) │                      │     │
│  │               └──────────────────────┘                      │     │
│  └───────────────────────┬────────────────────────────────────┘     │
│                          │                                             │
│                          ▼                                             │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  4. PROGRESSIVE ROLLOUT                                     │     │
│  │     Stage 1: 5% traffic   (15min soak, check SLIs)          │     │
│  │     Stage 2: 25% traffic  (30min soak, check SLIs)          │     │
│  │     Stage 3: 50% traffic  (1hr soak, check SLIs)            │     │
│  │     Stage 4: 100% traffic                                   │     │
│  │                                                              │     │
│  │     At each stage:                                          │     │
│  │     • Monitor error rates, latency, saturation              │     │
│  │     • Run smoke tests, health checks                        │     │
│  │     • Auto-rollback if SLI breached                         │     │
│  └───────────────────────┬────────────────────────────────────┘     │
│                          │                                             │
│                          ▼                                             │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  5. POST-DEPLOYMENT VERIFICATION                            │     │
│  │     • Synthetic monitoring (Datadog, Pingdom)               │     │
│  │     • Security smoke tests (auth, authz, crypto)            │     │
│  │     • Compliance checks (audit logs, encryption)            │     │
│  │     • Performance regression tests                          │     │
│  └────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────────┘
```

**Policy-as-Code Enforcement**:
```yaml
# OPA policy example: Require signed images
package kubernetes.admission

deny[msg] {
    input.request.kind.kind == "Pod"
    image := input.request.object.spec.containers[_].image
    not image_is_signed(image)
    msg := sprintf("Image %v is not signed", [image])
}

image_is_signed(image) {
    # Check signature via external API or admission webhook
    # Integration with Cosign/Notary
}

# Kyverno policy: Enforce resource limits
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-resource-limits
spec:
  validationFailureAction: enforce
  rules:
    - name: validate-resources
      match:
        any:
        - resources:
            kinds:
              - Pod
      validate:
        message: "CPU and memory limits required"
        pattern:
          spec:
            containers:
            - resources:
                limits:
                  memory: "?*"
                  cpu: "?*"
```

**Actionable Steps**:
```bash
# 1. Implement Blue/Green deployment
cat > blue-green-deploy.sh <<'EOF'
#!/bin/bash
set -euo pipefail

NAMESPACE="production"
NEW_VERSION="v2.0.0"
CURRENT_COLOR=$(kubectl get svc myapp -n $NAMESPACE -o jsonpath='{.spec.selector.version}')
NEW_COLOR=$( [ "$CURRENT_COLOR" == "blue" ] && echo "green" || echo "blue" )

# Deploy new version
kubectl apply -f k8s/deployment-${NEW_COLOR}.yaml -n $NAMESPACE
kubectl set image deployment/myapp-${NEW_COLOR} app=myregistry.io/myapp:${NEW_VERSION} -n $NAMESPACE

# Wait for rollout
kubectl rollout status deployment/myapp-${NEW_COLOR} -n $NAMESPACE --timeout=5m

# Run smoke tests
./smoke-tests.sh https://myapp-${NEW_COLOR}.internal

# Switch traffic
kubectl patch svc myapp -n $NAMESPACE -p "{\"spec\":{\"selector\":{\"version\":\"${NEW_COLOR}\"}}}"

echo "Switched to ${NEW_COLOR}, ${CURRENT_COLOR} remains for rollback"
# Keep old deployment for 24h, then delete
EOF

# 2. Canary deployment with Flagger (on Istio/Linkerd)
cat > canary.yaml <<EOF
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: myapp
  namespace: production
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  service:
    port: 8080
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
      - name: security-smoke-tests
        url: http://test-runner.ci/smoke
        timeout: 30s
        metadata:
          type: pre-rollout
          cmd: "run security-tests --target=myapp-canary"
EOF

kubectl apply -f canary.yaml

# 3. Automated rollback script
cat > auto-rollback.sh <<'EOF'
#!/bin/bash
set -euo pipefail

DEPLOYMENT="myapp"
NAMESPACE="production"
ERROR_THRESHOLD=0.01  # 1% error rate

# Monitor error rate for 5 minutes
for i in {1..10}; do
    ERROR_RATE=$(kubectl exec -n monitoring prometheus-0 -- \
        promtool query instant 'rate(http_requests_total{job="myapp",status=~"5.."}[1m]) / rate(http_requests_total{job="myapp"}[1m])' | \
        jq -r '.data.result[0].value[1]')
    
    if (( $(echo "$ERROR_RATE > $ERROR_THRESHOLD" | bc -l) )); then
        echo "Error rate $ERROR_RATE exceeds threshold, rolling back..."
        kubectl rollout undo deployment/$DEPLOYMENT -n $NAMESPACE
        exit 1
    fi
    sleep 30
done
EOF

# 4. Admission webhook for runtime policy enforcement
# Deploy OPA Gatekeeper
kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/master/deploy/gatekeeper.yaml

# Create constraint template
cat > constraint-template.yaml <<EOF
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8srequiredsecuritycontext
spec:
  crd:
    spec:
      names:
        kind: K8sRequiredSecurityContext
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8srequiredsecuritycontext

        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not container.securityContext.runAsNonRoot == true
          msg := sprintf("Container %v must run as non-root", [container.name])
        }

        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not container.securityContext.readOnlyRootFilesystem == true
          msg := sprintf("Container %v must have read-only root filesystem", [container.name])
        }
EOF

kubectl apply -f constraint-template.yaml
```

---

### Phase 6: Operations & Monitoring

**Objective**: Detect, respond, and recover from security incidents in production.

**Security Monitoring Architecture**:
```
┌───────────────────────────────────────────────────────────────────────┐
│                   RUNTIME SECURITY MONITORING                          │
├───────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  DATA SOURCES                                                    │ │
│  │                                                                   │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │ │
│  │  │ App Logs │  │ Audit    │  │ Network  │  │  System  │       │ │
│  │  │ (stdout/ │  │ Logs     │  │ Traffic  │  │ Metrics  │       │ │
│  │  │  stderr) │  │ (K8s API)│  │ (eBPF)   │  │ (node_exp)│      │ │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │ │
│  │       │             │             │             │               │ │
│  │       └─────────────┴─────────────┴─────────────┘               │ │
│  │                          │                                       │ │
│  └──────────────────────────┼───────────────────────────────────── │ │
│                             ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  COLLECTION & AGGREGATION                                        │ │
│  │                                                                   │ │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐       │ │
│  │  │  Fluentd/     │  │  Prometheus   │  │  Falco/       │       │ │
│  │  │  Fluent Bit   │  │  (metrics)    │  │  Tetragon     │       │ │
│  │  │  (logs)       │  │               │  │  (runtime     │       │ │
│  │  │               │  │               │  │   behavior)   │       │ │
│  │  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘       │ │
│  │          │                  │                  │                 │ │
│  └──────────┼──────────────────┼──────────────────┼─────────────── │ │
│             │                  │                  │                   │
│             ▼                  ▼                  ▼                   │
│  ┌──────────────────────────────────────────────────┐ │
│  │  STORAGE & INDEXING                                              │ │
│  │                                                                   │ │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐       │ │
│  │  │  Elasticsearch│  │  Loki         │  │  VictoriaMetrics│      │ │
│  │  │  (full-text)  │  │  (log agg)    │  │  (TSDB)       │       │ │
│  │  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘       │ │
│  │          │                  │                  │                 │ │
│  └──────────┼──────────────────┼──────────────────┼─────────────── │ │
│             │                  │                  │                   │
│             ▼                  ▼                  ▼                   │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  DETECTION & ALERTING                                            │ │
│  │                                                                   │ │
│  │  ┌────────────────────────────────────────────────────────────┐ │ │
│  │  │  Rule Engine (Prometheus Alerts, Elastalert)               │ │ │
│  │  │  • Failed authentication attempts (>5 in 1min)              │ │ │
│  │  │  • Privilege escalation attempts                            │ │ │
│  │  │  • Container escape indicators                              │ │ │
│  │  │  • Anomalous network connections                            │ │ │
│  │  │  • Unexpected process execution                             │ │ │
│  │  └────────────────┬───────────────────────────────────────────┘ │ │
│  │                   │                                               │ │
│  │                   ▼                                               │ │
│  │  ┌────────────────────────────────────────────────────────────┐ │ │
│  │  │  SIEM/SOAR (Splunk, ELK, Wazuh, TheHive)                   │ │ │
│  │  │  • Correlation across data sources                          │ │ │
│  │  │  • Incident prioritization (severity scoring)               │ │ │
│  │  │  • Automated response playbooks                             │ │ │
│  │  └────────────────┬───────────────────────────────────────────┘ │ │
│  │                   │                                               │ │
│  └───────────────────┼───────────────────────────────────────────── │ │
│                      ▼                                                 │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  INCIDENT RESPONSE                                               │ │
│  │                                                                   │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │ │
│  │  │ Detect   │─▶│ Contain  │─▶│ Eradicate│─▶│ Recover  │       │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │ │
│  │       │             │             │             │               │ │
│  │       └─────────────┴─────────────┴─────────────┘               │ │
│  │                          │                                       │ │
│  │                          ▼                                       │ │
│  │                  Post-Mortem / Lessons Learned                  │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────┘
```

**Runtime Security with eBPF**:
```
┌────────────────────────────────────────────────────────────────┐
│           eBPF-BASED RUNTIME SECURITY (Falco/Tetragon)         │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  KERNEL SPACE (eBPF Programs)                             │ │
│  │                                                             │ │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐     │ │
│  │  │ syscall │  │ network │  │  file   │  │ process │     │ │
│  │  │  hooks  │  │  hooks  │  │  hooks  │  │  hooks  │     │ │
│  │  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘     │ │
│  │       │            │            │            │            │ │
│  │       └────────────┴────────────┴────────────┘            │ │
│  │                    │                                       │ │
│  │                    ▼                                       │ │
│  │         ┌──────────────────────┐                          │ │
│  │         │  eBPF Maps (ring     │                          │ │
│  │         │  buffers, hash maps) │                          │ │
│  │         └──────────┬───────────┘                          │ │
│  └────────────────────┼───────────────────────────────────── │ │
│                       │                                         │
│  ═════════════════════▼═══════════════════════════════════════ │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  USER SPACE (Security Agent)                              │ │
│  │                                                             │ │
│  │  ┌───────────────────────────────────────────────────────┐ │ │
│  │  │  Event Processing Engine                              │ │ │
│  │  │  • Parse eBPF events                                  │ │ │
│  │  │  • Enrich with context (pod, namespace, image)        │ │ │
│  │  │  • Apply detection rules                              │ │ │
│  │  └───────────────────┬───────────────────────────────────┘ │ │
│  │                      │                                       │ │
│  │                      ▼                                       │ │
│  │  ┌───────────────────────────────────────────────────────┐ │ │
│  │  │  Detection Rules (Falco Rules, Tetragon Policies)    │ │ │
│  │  │  • Shell spawned in container                         │ │ │
│  │  │  • Sensitive file access (/etc/shadow)                │ │ │
│  │  │  • Outbound connection to suspicious IP               │ │ │
│  │  │  • Privilege escalation (setuid, capabilities)        │ │ │
│  │  └───────────────────┬───────────────────────────────────┘ │ │
│  │                      │                                       │ │
│  │                      ▼                                       │ │
│  │  ┌───────────────────────────────────────────────────────┐ │ │
│  │  │  Response Actions                                     │ │ │
│  │  │  • Alert (Slack, PagerDuty, email)                    │ │ │
│  │  │  • Block (kill process, quarantine pod)               │ │ │
│  │  │  • Log to SIEM                                         │ │ │
│  │  └───────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘

EXAMPLE FALCO RULE:
- rule: Shell Spawned in Container
  desc: Detect shell execution inside container (potential compromise)
  condition: >
    container.id != host and 
    proc.name in (sh, bash, zsh) and 
    container.image.repository != "debug-tools"
  output: >
    Shell spawned in container (user=%user.name container=%container.name 
    image=%container.image.repository:%container.image.tag 
    command=%proc.cmdline)
  priority: WARNING
  tags: [container, shell, mitre_execution]
```

**Actionable Steps**:
```bash
# 1. Deploy Falco for runtime security
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm install falco falcosecurity/falco \
  --namespace falco --create-namespace \
  --set falco.grpc.enabled=true \
  --set falco.grpcOutput.enabled=true

# Create custom Falco rule
cat > custom-rules.yaml <<EOF
- rule: Unauthorized File Access
  desc: Detect access to sensitive configuration files
  condition: >
    open_read and
    fd.name in (/etc/shadow, /etc/passwd, /root/.ssh/id_rsa) and
    not proc.name in (sshd, systemd)
  output: >
    Sensitive file accessed (user=%user.name file=%fd.name 
    command=%proc.cmdline container=%container.name)
  priority: CRITICAL
EOF

kubectl create configmap falco-custom-rules --from-file=custom-rules.yaml -n falco
kubectl rollout restart daemonset/falco -n falco

# 2. Setup Prometheus alerts for security metrics
cat > security-alerts.yaml <<EOF
groups:
  - name: security
    interval: 30s
    rules:
      - alert: HighFailedAuthRate
        expr: rate(http_requests_total{path="/auth/login",status="401"}[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High failed authentication rate"
          description: "{{ $value }} failed logins per second"

      - alert: PodSecurityViolation
        expr: increase(kubernetes_admission_webhook_rejections_total{name="pod-security"}[5m]) > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Pod security policy violation detected"

      - alert: ContainerEscapeAttempt
        expr: falco_events_total{rule=~".*escape.*|.*privilege.*"} > 0
        for: 0m
        labels:
          severity: critical
        annotations:
          summary: "Potential container escape detected"
EOF

kubectl apply -f security-alerts.yaml

# 3. Configure audit logging
# Enable Kubernetes audit logging
cat > audit-policy.yaml <<EOF
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  # Log all Secret access
  - level: RequestResponse
    resources:
    - group: ""
      resources: ["secrets"]
  
  # Log privileged pod creation
  - level: Request
    verbs: ["create", "update", "patch"]
    resources:
    - group: ""
      resources: ["pods"]
    omitStages:
    - RequestReceived
  
  # Log RBAC changes
  - level: RequestResponse
    verbs: ["create", "update", "patch", "delete"]
    resources:
    - group: "rbac.authorization.k8s.io"
      resources: ["roles", "clusterroles", "rolebindings", "clusterrolebindings"]
EOF

# Add to kube-apiserver flags:
# --audit-policy-file=/etc/kubernetes/audit-policy.yaml
# --audit-log-path=/var/log/kubernetes/audit.log
# --audit-log-maxage=30
# --audit-log-maxbackup=10
# --audit-log-maxsize=100

# 4. Deploy intrusion detection (Wazuh)
kubectl apply -f https://raw.githubusercontent.com/wazuh/wazuh-kubernetes/master/wazuh/wazuh-agent-daemonset.yaml

# 5. Implement security baselines scanning (kube-bench)
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml

# View results
kubectl logs job/kube-bench

# 6. Setup anomaly detection with ML
# (Example: Sysdig Secure, Datadog Security Monitoring)
# or use open-source: https://github.com/Netflix/spectator

# 7. Create incident response runbook
cat > incident-response.md <<EOF
# Security Incident Response Runbook

## Phase 1: Detection (Time: T+0)
- Alert received via PagerDuty/Slack
- Triage: Severity assessment (P0-P4)
- Initiate incident channel: #incident-$(date +%Y%m%d-%H%M)

## Phase 2: Containment (Time: T+5min)
### Network Isolation
\`\`\`bash
# Isolate compromised pod
kubectl label pod <pod-name> quarantine=true
kubectl apply -f network-policy-quarantine.yaml

# Block egress for namespace
kubectl apply -f - <<YAML
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-egress
  namespace: compromised-namespace
spec:
  podSelector: {}
  policyTypes:
  - Egress
YAML
\`\`\`

### Preserve Evidence
\`\`\`bash
# Snapshot pod filesystem
kubectl cp <namespace>/<pod>:/path /tmp/evidence/

# Export logs
kubectl logs <pod> --previous > /tmp/evidence/logs.txt

# Capture network traffic
kubectl exec <pod> -- tcpdump -w /tmp/evidence/traffic.pcap
\`\`\`

## Phase 3: Eradication (Time: T+30min)
- Patch vulnerable component
- Rotate compromised credentials
- Rebuild affected images

## Phase 4: Recovery (Time: T+2hr)
- Deploy patched version
- Verify security controls
- Resume normal operations

## Phase 5: Post-Mortem (Time: T+24hr)
- Root cause analysis
- Update detection rules
- Improve response procedures
EOF
```

---

### Phase 7: Decommissioning & Data Lifecycle

**Objective**: Securely dispose of systems, sanitize data, and ensure no residual security risks.

**Data Sanitization Hierarchy**:
```
┌────────────────────────────────────────────────────────────────┐
│               DATA SANITIZATION METHODS                         │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  LEVEL 1: DELETION (WEAKEST)                              │ │
│  │  • File deletion (rm, del)                                │ │
│  │  • Risk: Data recoverable with forensic tools             │ │
│  │  • Use case: Non-sensitive test data                      │ │
│  └───────────────────────────────────────────────────────────┘ │
│                          ▼                                       │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  LEVEL 2: OVERWRITING                                     │ │
│  │  • Multi-pass overwrite (DoD 5220.22-M: 7 passes)        │ │
│  │  • Tools: shred, srm, DBAN                                │ │
│  │  • Use case: Moderate sensitivity, reusable storage       │ │
│  └───────────────────────────────────────────────────────────┘ │
│                          ▼                                       │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  LEVEL 3: CRYPTOGRAPHIC ERASURE                           │ │
│  │  • Delete encryption keys                                 │ │
│  │  • Data becomes cryptographically unrecoverable           │ │
│  │  • Use case: Cloud storage, encrypted volumes             │ │
│  │  • Example: AWS KMS key deletion (7-30 day wait)          │ │
│  └───────────────────────────────────────────────────────────┘ │
│                          ▼                                       │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  LEVEL 4: PHYSICAL DESTRUCTION (STRONGEST)                │ │
│  │  • Degaussing (magnetic media)                            │ │
│  │  • Shredding/pulverizing (HDDs, SSDs)                     │ │
│  │  • Incineration                                            │ │
│  │  • Use case: High-value data, decommissioned hardware     │ │
│  └───────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
```

**Decommissioning Workflow**:
```
┌────────────────────────────────────────────────────────────────┐
│              SYSTEM DECOMMISSIONING WORKFLOW                    │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. PLANNING                                                    │
│     ├─▶ Inventory assets (VMs, containers, databases)          │
│     ├─▶ Identify data classification                           │
│     ├─▶ Document dependencies                                  │
│     └─▶ Create decom timeline                                  │
│                                                                  │
│  2. DATA BACKUP (if required)                                   │
│     ├─▶ Compliance retention (7 years for SOX, etc)            │
│     ├─▶ Encrypted backup to cold storage                       │
│     └─▶ Verify backup integrity                                │
│                                                                  │
│  3. CERTIFICATE & KEY REVOCATION                                │
│     ├─▶ Revoke TLS certificates                                │
│     ├─▶ Delete service account keys                            │
│     ├─▶ Remove from key management systems                     │
│     └─▶ Update DNS records                                     │
│                                                                  │
│  4. ACCESS REMOVAL                                              │
│     ├─▶ Disable IAM users/roles                                │
│     ├─▶ Remove from LDAP/AD                                    │
│     ├─▶ Revoke API tokens                                      │
│     └─▶ Delete service accounts                                │
│                                                                  │
│  5. DATA SANITIZATION                                           │
│     ├─▶ Crypto-shred: Delete KMS keys                          │
│     ├─▶ Overwrite: shred -vfz -n 7 /data/*                     │
│     ├─▶ Database: TRUNCATE + DROP                              │
│     └─▶ Cloud: Delete S3 buckets with MFA delete              │
│                                                                  │
│  6. RESOURCE DELETION                                           │
│     ├─▶ Terminate compute instances                            │
│     ├─▶ Delete Kubernetes resources                            │
│     ├─▶ Remove load balancers, IPs                             │
│     └─▶ Deprovision storage volumes                            │
│                                                                  │
│  7. AUDIT TRAIL                                                 │
│     ├─▶ Document all actions taken                             │
│     ├─▶ Generate decom certificate                             │
│     ├─▶ Archive logs for compliance                            │
│     └─▶ Sign-off by security & compliance                      │
│                                                                  │
│  8. VERIFICATION                                                │
│     ├─▶ Scan for residual data                                 │
│     ├─▶ Confirm no active connections                          │
│     ├─▶ Verify DNS/firewall rules removed                      │
│     └─▶ Check no references in monitoring                      │
└────────────────────────────────────────────────────────────────┘
```

**Actionable Steps**:
```bash
# 1. Automated decommissioning script
cat > decommission.sh <<'EOF'
#!/bin/bash
set -euo pipefail

APP_NAME="${1:?APP_NAME required}"
NAMESPACE="${2:?NAMESPACE required}"
BACKUP_REQUIRED="${3:-false}"

echo "===== DECOMMISSIONING ${APP_NAME} in ${NAMESPACE} ====="

# Step 1: Backup if required
if [ "$BACKUP_REQUIRED" = "true" ]; then
    echo "[1/7] Creating backup..."
    kubectl exec -n "$NAMESPACE" "$APP_NAME"-db-0 -- \
        pg_dump -U postgres mydb | \
        gpg --encrypt --recipient security@company.com > \
        "/backups/${APP_NAME}-$(date +%Y%m%d).sql.gpg"
fi

# Step 2: Revoke certificates
echo "[2/7] Revoking certificates..."
cert-manager -n "$NAMESPACE" kubectl delete certificate "$APP_NAME"-tls

# Step 3: Remove access
echo "[3/7] Removing access..."
kubectl delete serviceaccount "$APP_NAME" -n "$NAMESPACE"
kubectl delete rolebinding "$APP_NAME"-binding -n "$NAMESPACE"

# Step 4: Crypto-shred data
echo "[4/7] Crypto-shredding data..."
# Delete KMS keys (AWS example)
aws kms schedule-key-deletion --key-id "$APP_KMS_KEY_ID" --pending-window-in-days 7

# Step 5: Delete resources
echo "[5/7] Deleting Kubernetes resources..."
kubectl delete all -l app="$APP_NAME" -n "$NAMESPACE"
kubectl delete pvc -l app="$APP_NAME" -n "$NAMESPACE"
kubectl delete secret -l app="$APP_NAME" -n "$NAMESPACE"

# Step 6: Remove from service mesh
echo "[6/7] Removing from Istio..."
kubectl delete virtualservice "$APP_NAME" -n "$NAMESPACE"
kubectl delete destinationrule "$APP_NAME" -n "$NAMESPACE"

# Step 7: Audit log
echo "[7/7] Creating audit trail..."
cat > "/audit/decom-${APP_NAME}-$(date +%Y%m%d).log" <<LOG
Decommissioned: $APP_NAME
Namespace: $NAMESPACE
Timestamp: $(date -Iseconds)
Performed by: $(whoami)
Backup created: $BACKUP_REQUIRED
Actions:
  - Certificates revoked
  - Service accounts deleted
  - KMS keys scheduled for deletion
  - All K8s resources removed
LOG

echo "===== DECOMMISSIONING COMPLETE ====="
EOF

chmod +x decommission.sh

# 2. Secure data overwriting
# For persistent volumes
cat > secure-wipe-pv.yaml <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: secure-wipe
spec:
  template:
    spec:
      containers:
      - name: wipe
        image: alpine:latest
        command:
        - sh
        - -c
        - |
          apk add --no-cache coreutils
          shred -vfz -n 7 /data/*
          echo "Wipe complete"
        volumeMounts:
        - name: data
          mountPath: /data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: my-app-data
      restartPolicy: Never
EOF

kubectl apply -f secure-wipe-pv.yaml

# 3. Cloud resource cleanup with Terraform destroy
cat > terraform-destroy.sh <<'EOF'
#!/bin/bash
set -euo pipefail

# Backup state
cp terraform.tfstate terraform.tfstate.backup-$(date +%Y%m%d)

# Enable deletion protection checks
terraform plan -destroy -out=destroy.tfplan

# Review plan
echo "Review destroy plan before proceeding..."
terraform show destroy.tfplan

# Confirm and destroy
read -p "Proceed with destruction? (yes/no): " confirm
if [ "$confirm" = "yes" ]; then
    terraform apply destroy.tfplan
    
    # Verify deletion
    echo "Verifying resources deleted..."
    aws ec2 describe-instances --filters "Name=tag:Project,Values=myapp" | \
        jq '.Reservations[] | length' | \
        grep -q '^0$' && echo "All EC2 instances deleted"
fi
EOF

# 4. Database sanitization
cat > sanitize-db.sql <<EOF
-- Drop all application tables
DROP SCHEMA IF EXISTS myapp CASCADE;

-- Overwrite backup tables
UPDATE users_backup SET 
    email = 'deleted@deleted.com',
    password_hash = 'REDACTED',
    ssn = NULL
WHERE deleted_at < NOW() - INTERVAL '90 days';

-- Vacuum to reclaim space
VACUUM FULL;

-- Final verification
SELECT COUNT(*) FROM information_schema.tables 
WHERE table_schema = 'myapp';  -- Should be 0
EOF

psql -U postgres -f sanitize-db.sql

# 5. Generate decommissioning certificate
cat > generate-decom-cert.sh <<'EOF'
#!/bin/bash

APP_NAME="$1"
cat > "decom-cert-${APP_NAME}.txt" <<CERT
═══════════════════════════════════════════════════════
          SYSTEM DECOMMISSIONING CERTIFICATE
═══════════════════════════════════════════════════════

Application: ${APP_NAME}
Decommissioned Date: $(date -Iseconds)
Performed By: $(whoami)

ACTIONS COMPLETED:
✓ Data backed up and encrypted
✓ Encryption keys deleted (KMS key ID: ${APP_KMS_KEY_ID})
✓ All compute resources terminated
✓ Storage volumes securely wiped (DoD 5220.22-M)
✓ Network resources removed
✓ Access credentials revoked
✓ Service accounts deleted
✓ DNS records updated
✓ Monitoring alerts disabled
✓ Audit logs archived

VERIFICATION:
✓ No active network connections
✓ No residual data detected
✓ All dependencies notified

Approved By:
  Security: _______________________  Date: ___________
  Compliance: _____________________  Date: ___________

═══════════════════════════════════════════════════════
CERT

gpg --clearsign "decom-cert-${APP_NAME}.txt"
EOF
```

---

## 3. Cross-Cutting Security Concerns

### Supply Chain Security (SLSA Framework)

```
┌────────────────────────────────────────────────────────────────┐
│            SOFTWARE SUPPLY CHAIN ATTACK SURFACE                 │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  SOURCE CODE                                                    │
│  ├─▶ Threats: Compromised commits, backdoored repos            │
│  └─▶ Mitigations: Signed commits, branch protection,           │
│      code review, CODEOWNERS                                    │
│                                                                  │
│  DEPENDENCIES                                                   │
│  ├─▶ Threats: Malicious packages, typosquatting,               │
│  │   dependency confusion                                       │
│  └─▶ Mitigations: SCA scanning, SBOM, private registries,      │
│      dependency pinning, reproducible builds                    │
│                                                                  │
│  BUILD SYSTEM                                                   │
│  ├─▶ Threats: Compromised CI/CD, poisoned cache,               │
│  │   build parameter injection                                  │
│  └─▶ Mitigations: Ephemeral build environments,                │
│      provenance attestation, SLSA Level 3+                      │
│                                                                  │
│  ARTIFACTS                                                      │
│  ├─▶ Threats: Unsigned images, registry compromise             │
│  └─▶ Mitigations: Image signing (Cosign), admission            │
│      controllers, private registries                            │
│                                                                  │
│  DEPLOYMENT                                                     │
│  ├─▶ Threats: Configuration drift, unauthorized changes        │
│  └─▶ Mitigations: GitOps, policy-as-code, drift detection      │
└────────────────────────────────────────────────────────────────┘
```

**SBOM Generation and Verification**:
```bash
# Generate SBOM with Syft
syft myapp:latest -o spdx-json > sbom.spdx.json

# Generate SBOM with CycloneDX
cyclonedx-cli generate -i . -o sbom.cyclonedx.json

# Sign SBOM
cosign sign-blob --key cosign.key sbom.spdx.json > sbom.sig

# Verify vulnerabilities in SBOM
grype sbom:./sbom.spdx.json --fail-on high

# Upload to dependency track
curl -X POST "https://deptrack.company.com/api/v1/bom" \
  -H "X-API-Key: ${DEPTRACK_API_KEY}" \
  -H "Content-Type: multipart/form-data" \
  -F "project=uuid" \
  -F "bom=@sbom.cyclonedx.json"
```

---

### Secrets Management

```
┌────────────────────────────────────────────────────────────────┐
│                 SECRETS MANAGEMENT ARCHITECTURE                 │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  SECRETS SOURCES (DO NOT USE)                            │ │
│  │  ❌ Hardcoded in code                                    │ │
│  │  ❌ Environment variables (clear text)                   │ │
│  │  ❌ Config files in repo                                 │ │
│  │  ❌ Kubernetes Secrets (base64 encoded only)             │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  SECRETS VAULT (USE THIS)                                │ │
│  │  ✅ HashiCorp Vault                                      │ │
│  │  ✅ AWS Secrets Manager / KMS                            │ │
│  │  ✅ Azure Key Vault                                      │ │
│  │  ✅ GCP Secret Manager                                   │ │
│  │  ✅ External Secrets Operator (K8s)                      │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                  │
│  SECRETS INJECTION FLOW:                                        │
│                                                                  │
│  App Start ──▶ Init Container ──▶ Vault Agent                  │
│                      │                  │                        │
│                      │                  ▼                        │
│                      │            ┌──────────┐                  │
│                      │            │  Vault   │                  │
│                      │            │  Server  │                  │
│                      │            └──────────┘                  │
│                      │                  │                        │
│                      │                  ▼                        │
│                      └──────▶  Mount secrets at                 │
│                               /vault/secrets/                    │
│                                                                  │
│  ROTATION:                                                      │
│  • Automatic rotation every 90 days                             │
│  • Zero-downtime credential rotation                            │
│  • Audit trail of all access                                    │
└────────────────────────────────────────────────────────────────┘
```

**Example: Vault Integration**:
```bash
# Deploy Vault in K8s
helm install vault hashicorp/vault \
  --set "server.ha.enabled=true" \
  --set "server.ha.replicas=3"

# Enable Kubernetes auth
vault auth enable kubernetes
vault write auth/kubernetes/config \
  kubernetes_host="https://kubernetes.default.svc"

# Create policy
vault policy write myapp - <<EOF
path "secret/data/myapp/*" {
  capabilities = ["read"]
}
EOF

# Create role
vault write auth/kubernetes/role/myapp \
  bound_service_account_names=myapp \
  bound_service_account_namespaces=production \
  policies=myapp \
  ttl=24h

# Inject secrets into pod
cat > pod-with-vault.yaml <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: myapp
  annotations:
    vault.hashicorp.com/agent-inject: "true"
    vault.hashicorp.com/role: "myapp"
    vault.hashicorp.com/agent-inject-secret-db: "secret/data/myapp/db"
    vault.hashicorp.com/agent-inject-template-db: |
      {{- with secret "secret/data/myapp/db" -}}
      export DB_USER="{{ .Data.data.username }}"
      export DB_PASS="{{ .Data.data.password }}"
      {{- end }}
spec:
  serviceAccountName: myapp
  containers:
  - name: app
    image: myapp:latest
    command: ["/bin/sh", "-c"]
    args: ["source /vault/secrets/db && ./myapp"]
EOF
```

---

## 4. Compliance & Governance

**Compliance Frameworks Mapping**:
```
┌──────────────┬──────────────────────────────────────────────────┐
│  Framework   │  Key S-SDLC Requirements                         │
├──────────────┼──────────────────────────────────────────────────┤
│  PCI-DSS     │  • Secure coding (6.3.2)                         │
│              │  • Code reviews (6.3.2)                          │
│              │  • Vulnerability management (6.1, 11.3)          │
│              │  • Change control (6.4)                          │
├──────────────┼──────────────────────────────────────────────────┤
│  SOC 2       │  • Access controls (CC6.1)                       │
│              │  • Change management (CC8.1)                     │
│              │  • Vulnerability scanning (CC7.1)                │
│              │  • Incident response (CC7.4)                     │
├──────────────┼──────────────────────────────────────────────────┤
│  GDPR        │  • Privacy by design (Article 25)                │
│              │  • Data minimization                             │
│              │  • Right to erasure (Article 17)                 │
│              │  • Breach notification (Article 33)              │
├──────────────┼──────────────────────────────────────────────────┤
│  HIPAA       │  • Access controls (§164.312(a)(1))              │
│              │  • Encryption (§164.312(a)(2)(iv))               │
│              │  • Audit controls (§164.312(b))                  │
│              │  • Integrity controls (§164.312(c)(1))           │
├──────────────┼──────────────────────────────────────────────────┤
│  FedRAMP     │  • Continuous monitoring (CA-7)                  │
│              │  • Configuration management (CM-2)               │
│              │  • Vulnerability scanning (RA-5)                 │
│              │  • Incident response (IR-4)                      │
└──────────────┴──────────────────────────────────────────────────┘
```

---

## 5. Security Testing Strategy

**Comprehensive Testing Matrix**:
```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│   Testing    │   Frequency  │     Tools    │   Coverage   │
│     Type     │              │              │              │
├──────────────┼──────────────┼──────────────┼──────────────┤
│  Unit Tests  │  Per commit  │  Go test,    │  >80% code   │
│  (Security)  │              │  pytest      │   coverage   │
├──────────────┼──────────────┼──────────────┼──────────────┤
│  SAST        │  Per commit  │  Semgrep,    │  All code    │
│              │              │  CodeQL      │              │
├──────────────┼──────────────┼──────────────┼──────────────┤
│  SCA         │  Per commit  │  Dependabot, │  All deps    │
│              │              │  Snyk, Grype │              │
├──────────────┼──────────────┼──────────────┼──────────────┤
│  Secret Scan │  Pre-commit  │  gitleaks,   │  All files   │
│              │              │  trufflehog  │              │
├──────────────┼──────────────┼──────────────┼──────────────┤
│  Container   │  Per build   │  Trivy,      │  All images  │
│  Scanning    │              │  Grype       │              │
├──────────────┼──────────────┼──────────────┼──────────────┤
│  DAST        │  Nightly     │  OWASP ZAP,  │  All APIs    │
│              │              │  Nuclei      │              │
├──────────────┼──────────────┼──────────────┼──────────────┤
│  Fuzzing     │  Continuous  │  AFL++,      │  Parsers,    │
│              │              │  libFuzzer   │  protocols   │
├──────────────┼──────────────┼──────────────┼──────────────┤
│  Pen Test    │  Quarterly   │  Manual +    │  Critical    │
│              │              │  Metasploit  │  systems     │
├──────────────┼──────────────┼──────────────┼──────────────┤
│  Red Team    │  Annual      │  Custom      │  Full stack  │
│              │              │  tooling     │              │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

---

## 6. Threat Modeling Deep Dive

**Attack Surface Analysis**:
```
┌────────────────────────────────────────────────────────────────┐
│                    ATTACK SURFACE INVENTORY                     │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  EXTERNAL FACING:                                               │
│  ├─▶ Web Application (HTTPS)                                   │
│  │   • Threats: XSS, CSRF, injection, authN/authZ bypass       │
│  │   • Controls: WAF, input validation, CSP, CORS              │
│  ├─▶ API Gateway (REST/gRPC)                                   │
│  │   • Threats: API abuse, broken authN, rate limit bypass     │
│  │   • Controls: OAuth, rate limiting, API keys rotation       │
│  └─▶ CDN / Static Assets                                       │
│      • Threats: Cache poisoning, DDoS                           │
│      • Controls: Signed URLs, DDoS protection, SRI              │
│                                                                  │
│  INTERNAL:                                                      │
│  ├─▶ Service Mesh (mTLS)                                       │
│  │   • Threats: Cert compromise, MITM                          │
│  │   • Controls: Short-lived certs, cert rotation              │
│  ├─▶ Message Queue                                             │
│  │   • Threats: Message tampering, unauthorized access         │
│  │   • Controls: Encryption in transit, ACLs                   │
│  └─▶ Internal APIs                                             │
│      • Threats: SSRF, privilege escalation                      │
│      • Controls: Network policies, RBAC                         │
│                                                                  │
│  DATA STORES:                                                   │
│  ├─▶ Databases (PostgreSQL, MySQL)                             │
│  │   • Threats: SQL injection, data exfiltration               │
│  │   • Controls: Parameterized queries, encryption at rest     │
│  ├─▶ Object Storage (S3, GCS)                                  │
│  │   • Threats: Public bucket exposure, unauthorized access    │
│  │   • Controls: IAM policies, bucket policies, versioning     │
│  └─▶ Cache (Redis, Memcached)                                  │
│      • Threats: Cache poisoning, data leakage                   │
│      • Controls: AUTH, TLS, short TTLs                          │
└────────────────────────────────────────────────────────────────┘
```

---

## 7. Rollout & Rollback Plan

**Progressive Delivery Strategy**:
```yaml
# Flagger canary with security gates
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: myapp
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  progressDeadlineSeconds: 600
  service:
    port: 8080
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
      - name: security-violations
        thresholdRange:
          max: 0
        interval: 1m
        templateRef:
          name: security-violations
    webhooks:
      - name: security-scan
        type: pre-rollout
        url: http://security-scanner/scan
        timeout: 5m
        metadata:
          cmd: "trivy image myapp:canary"
      - name: smoke-tests
        type: pre-rollout
        url: http://test-runner/smoke
        timeout: 3m
      - name: load-test
        type: rollout
        url: http://load-tester/run
        timeout: 5m
        metadata:
          duration: "5m"
          rps: "1000"
```

---

## 8. Key Performance Indicators (KPIs)

**Security Metrics**:
```
┌─────────────────────────────────────────────────────────────┐
│                  SECURE SDLC METRICS                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  PREVENTIVE (Leading Indicators):                            │
│  • % of commits with signed GPG signatures                   │
│  • Mean time to patch critical vulnerabilities (MTTPCV)      │
│  • % of code covered by security tests                       │
│  • Security training completion rate                         │
│  • Number of security reviews before release                 │
│                                                               │
│  DETECTIVE (Lagging Indicators):                             │
│  • Number of vulnerabilities found in production             │
│  • Mean time to detect incidents (MTTD)                      │
│  • False positive rate in security scans                     │
│  • % of deploys blocked by security gates                    │
│                                                               │
│  CORRECTIVE (Response Metrics):                              │
│  • Mean time to respond to incidents (MTTR)                  │
│  • Mean time to recover (MTTR)                               │
│  • Number of security hotfixes per quarter                   │
│                                                               │
│  TARGETS:                                                     │
│  • MTTPCV: <24 hours for critical                            │
│  • MTTD: <15 minutes                                          │
│  • MTTR: <2 hours                                             │
│  • Vulnerability escape rate: <1%                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Next 3 Steps

1. **Immediate (Week 1)**:
   - Implement pre-commit hooks (gitleaks, semgrep)
   - Enable GitHub/GitLab security scanning
   - Create initial threat model for one critical component

2. **Short-term (Month 1)**:
   - Deploy runtime security (Falco/Tetragon)
   - Implement SBOM generation and signing
   - Establish security metrics dashboard

3. **Medium-term (Quarter 1)**:
   - Achieve SLSA Level 3 for build process
   - Conduct first purple team exercise
   - Implement full policy-as-code enforcement

---

## References

**Standards & Frameworks**:
- NIST SP 800-218: Secure Software Development Framework (SSDF)
- OWASP SAMM: Software Assurance Maturity Model
- ISO/IEC 27034: Application Security
- BSIMM: Building Security In Maturity Model
- SLSA: Supply-chain Levels for Software Artifacts

**Tools Ecosystem**:
- CNCF Security TAG: https://github.com/cncf/tag-security
- Sigstore: https://www.sigstore.dev/
- Falco: https://falco.org/docs/
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- CIS Benchmarks: https://www.cisecurity.org/cis-benchmarks

**Verification Commands**:
```bash
# Verify S-SDLC implementation
echo "1. Check signed commits:"
git log --show-signature -1

echo "2. Verify image signatures:"
cosign verify --key cosign.pub myregistry.io/myapp:latest

echo "3. Check runtime security:"
kubectl get pods -l app=falco -n falco

echo "4. Verify policy enforcement:"
kubectl get clusterpolicy

echo "5. Check audit logs:"
kubectl logs -n kube-system kube-apiserver-* | grep audit
```

This comprehensive guide covers the full Secure SDLC lifecycle with production-grade practices. Adapt based on your organization's risk tolerance, compliance requirements, and operational maturity.