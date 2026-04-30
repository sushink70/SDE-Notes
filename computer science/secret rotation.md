# Secret Rotation: Comprehensive Security Engineering Guide

## Executive Summary

Secret rotation is the systematic replacement of cryptographic credentials (keys, tokens, passwords, certificates) on a periodic or event-driven basis to minimize blast radius from compromise, enforce time-bounded trust, and satisfy compliance requirements. Proper rotation requires coordinated state transitions across distributed systems, atomic credential updates, zero-downtime cutover, comprehensive audit trails, and fallback mechanisms. The security benefit derives from limiting credential lifetime (reducing exposure window), forcing attackers to re-compromise systems, and enabling cryptographic agility. Production implementations must handle concurrent access, partial failures, version skew, and the distributed systems challenges of eventually-consistent secret propagation while maintaining strict isolation boundaries and preventing credential leakage during transition states.

---

## 1. Core Taxonomy & Rotation Types

### 1.1 Secret Categories by Rotation Characteristics

```
┌─────────────────────────────────────────────────────────────────┐
│                    SECRET TAXONOMY BY ROTATION                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  STATIC SECRETS (manual/scheduled rotation)                      │
│  ├─ Root Credentials (AWS root, GCP owner)                       │
│  ├─ Master Encryption Keys (KEK, CMK)                            │
│  ├─ CA Private Keys (PKI root/intermediate)                      │
│  └─ Break-glass Emergency Access                                 │
│                                                                   │
│  DYNAMIC SECRETS (automated/on-demand)                           │
│  ├─ Service Tokens (OAuth2, JWT)                                 │
│  ├─ Database Credentials (temp users)                            │
│  ├─ Cloud IAM Short-lived Tokens (STS)                           │
│  └─ Workload Identity Certificates                               │
│                                                                   │
│  EPHEMERAL SECRETS (session-bound)                               │
│  ├─ TLS Session Keys                                             │
│  ├─ Kerberos Tickets                                             │
│  ├─ OIDC ID Tokens                                               │
│  └─ SSH Session Keys                                             │
│                                                                   │
│  CRYPTOGRAPHIC MATERIAL                                          │
│  ├─ Symmetric Keys (AES-256-GCM DEK)                             │
│  ├─ Asymmetric Keypairs (RSA, ECDSA, Ed25519)                    │
│  ├─ Signing Keys (JWK, GPG)                                      │
│  └─ API Keys/Tokens                                              │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Rotation Trigger Types

**Time-based**: Scheduled (30/60/90-day cycles), enforced by policy  
**Event-based**: Compromise detection, employee departure, security incident  
**Risk-based**: Elevated threat level, failed auth attempts, anomalous access  
**Compliance-driven**: PCI-DSS (90-day), SOC2, HIPAA requirements  

---

## 2. Architecture Patterns & State Machines

### 2.1 Overlapping Rotation (Dual-Active Pattern)

```
                    OVERLAPPING ROTATION STATE MACHINE
┌──────────────────────────────────────────────────────────────────────┐
│                                                                        │
│   Time: T0          T1            T2            T3            T4     │
│   ─────────────────────────────────────────────────────────────────  │
│                                                                        │
│   SECRET-V1:  [████████████████████ACTIVE████████████]                │
│                                     ↓                                  │
│   SECRET-V2:                  [████OVERLAP████][███ACTIVE███]         │
│                                     ↑                  ↓               │
│   SECRET-V3:                                     [████OVERLAP████]... │
│                                                                        │
│   States:                                                              │
│   ├─ PENDING:     Generated, not yet distributed                      │
│   ├─ STAGING:     Propagating to consumers                            │
│   ├─ ACTIVE:      Primary credential, fully propagated                │
│   ├─ OVERLAPPING: Both V1+V2 valid (grace period)                     │
│   ├─ DEPRECATED:  V1 marked for removal, still accepted               │
│   └─ REVOKED:     V1 destroyed, access denied                         │
│                                                                        │
│   Transition Rules:                                                    │
│   • Overlap window = 2x max propagation delay                         │
│   • Min 2 versions active during rotation                             │
│   • Rollback requires V(n-1) still valid                              │
│   • Hard cutover only after 100% consumer migration                   │
│                                                                        │
└──────────────────────────────────────────────────────────────────────┘

Phase Breakdown:
T0→T1: Generate V2, stage to secret store
T1→T2: Propagate V2 to all consumers, both V1+V2 valid
T2→T3: Verify V2 adoption, monitor for V1 usage
T3→T4: Revoke V1, V2 becomes sole active credential
```

**Overlap Window Calculation**:  
```
overlap_duration = (max_propagation_latency × 2) + verification_period + safety_buffer
                 = (5min × 2) + 10min + 5min = 25min minimum
```

### 2.2 Zero-Downtime Rotation Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│              ZERO-DOWNTIME ROTATION ORCHESTRATION                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────┐                                                    │
│  │ Secret Store │ (Vault, AWS Secrets Manager, GCP Secret Manager)  │
│  │  HSM-backed  │                                                    │
│  └──────┬───────┘                                                    │
│         │                                                             │
│         │ 1. Generate V(n+1)                                         │
│         │    • KMS Envelope Encryption                               │
│         │    • Audit log entry                                       │
│         │    • Version tagging                                       │
│         ▼                                                             │
│  ┌─────────────────┐                                                 │
│  │ Control Plane   │ (Rotation Controller)                          │
│  │ ├─ State FSM    │                                                 │
│  │ ├─ Versioning   │                                                 │
│  │ └─ Observers    │                                                 │
│  └────┬────────┬───┘                                                 │
│       │        │                                                      │
│       │        │ 2. Propagate via secure channels                    │
│       │        │    • mTLS to consumers                              │
│       │        │    • Workload identity auth                         │
│       │        │    • Policy-based distribution                      │
│       │        │                                                      │
│  ┌────▼────┐  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │Consumer │  └─►│Consumer  │  │Consumer  │  │Consumer  │          │
│  │  Pod-1  │     │  Pod-2   │  │  Pod-3   │  │  Pod-N   │          │
│  │         │     │          │  │          │  │          │          │
│  │ V1+V2   │     │ V1→V2    │  │ V1+V2    │  │ V1+V2    │          │
│  └─────────┘     └──────────┘  └──────────┘  └──────────┘          │
│       │              │              │              │                 │
│       └──────────────┴──────────────┴──────────────┘                │
│                      │                                                │
│                      │ 3. Health checks with V2                      │
│                      │    • Synthetic transactions                   │
│                      │    • Canary deployments                       │
│                      │    • Metrics: auth_success_rate               │
│                      ▼                                                │
│             ┌─────────────────┐                                      │
│             │ Observability   │                                      │
│             │ ├─ Metrics      │ (Prometheus, Datadog)               │
│             │ ├─ Traces       │ (Jaeger, Tempo)                     │
│             │ └─ Audit Logs   │ (SIEM ingestion)                    │
│             └─────────────────┘                                      │
│                      │                                                │
│                      │ 4. Verification complete?                     │
│                      │    YES → Revoke V1                            │
│                      │    NO  → Rollback, investigate               │
│                      ▼                                                │
│             ┌─────────────────┐                                      │
│             │ Finalization    │                                      │
│             │ ├─ Revoke V1    │                                      │
│             │ ├─ Update policy│                                      │
│             │ ├─ Compliance   │                                      │
│             │ └─ Alert close  │                                      │
│             └─────────────────┘                                      │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### 2.3 Distributed System Challenges

```
┌────────────────────────────────────────────────────────────────┐
│         DISTRIBUTED ROTATION FAILURE SCENARIOS                  │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Problem: Partial Propagation Failure                           │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐                   │
│  │ Zone-A  │     │ Zone-B  │     │ Zone-C  │                   │
│  │  ✓ V2   │     │  ✓ V2   │     │  ✗ V1   │  ← Stuck on old  │
│  └─────────┘     └─────────┘     └─────────┘                   │
│  Mitigation: Heartbeat validation, retry with exponential       │
│              backoff, health-based routing exclusion            │
│                                                                  │
│  Problem: Clock Skew / TTL Drift                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Host-1: T=1000  V2 expires at T=1100  (OK)              │  │
│  │ Host-2: T=1105  V2 expired at T=1100  (REJECTED)        │  │
│  └──────────────────────────────────────────────────────────┘  │
│  Mitigation: NTP sync enforcement (chrony), grace periods,      │
│              server-side expiry validation                      │
│                                                                  │
│  Problem: Split-Brain Rotation                                  │
│  ┌───────────┐                        ┌───────────┐            │
│  │ Region-US │ generates V2-A         │ Region-EU │            │
│  └─────┬─────┘                        └─────┬─────┘            │
│        │   ┌───────────────────────────┐    │                  │
│        └──►│ Network Partition (5min) │◄───┘                  │
│            └───────────────────────────┘                        │
│               Both generate V2-A, V2-B (conflict)              │
│  Mitigation: Distributed locking (etcd, Consul), leader         │
│              election, monotonic version counters               │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

---

## 3. Secret Store Integration Patterns

### 3.1 Vault (HashiCorp) Dynamic Secrets

```
┌─────────────────────────────────────────────────────────────────┐
│              VAULT DYNAMIC SECRETS ARCHITECTURE                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Vault Cluster (HA)                       │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │ │
│  │  │ Active Node │  │ Standby (1) │  │ Standby (2) │        │ │
│  │  └──────┬──────┘  └─────────────┘  └─────────────┘        │ │
│  │         │ Raft/Consul/etcd backend (consensus)            │ │
│  │         │                                                   │ │
│  │  ┌──────▼──────────────────────────────────────────────┐  │ │
│  │  │           Secret Engines (Plugins)                   │  │ │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │  │ │
│  │  │  │Database  │  │AWS       │  │PKI/Cert  │           │  │ │
│  │  │  │(postgres)│  │(STS)     │  │(x509)    │           │  │ │
│  │  │  └────┬─────┘  └────┬─────┘  └────┬─────┘           │  │ │
│  │  └───────┼─────────────┼─────────────┼─────────────────┘  │ │
│  └──────────┼─────────────┼─────────────┼────────────────────┘ │
│             │             │             │                       │
│  Rotation   │             │             │  Issuance            │
│  Triggered  │             │             │  On-Demand           │
│             │             │             │                       │
│  ┌──────────▼──────┐   ┌──▼─────────┐  ┌─▼──────────────┐     │
│  │ PostgreSQL      │   │ AWS API    │  │ mTLS Clients   │     │
│  │ ├─ CREATE USER  │   │ ├─ AssumeR.│  │ ├─ CSR signing │     │
│  │ ├─ GRANT privs  │   │ ├─ Session │  │ ├─ CRL checks  │     │
│  │ └─ DROP old usr │   │ └─ Token   │  │ └─ OCSP staple │     │
│  └─────────────────┘   └────────────┘  └────────────────┘     │
│                                                                  │
│  Lease Management:                                              │
│  • Default TTL: 1h (configurable)                               │
│  • Max TTL: 24h (hard limit)                                    │
│  • Renewal: Client-driven (exponential backoff)                 │
│  • Revocation: Immediate via API or on compromise               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

Example Config (blueprint):
---
path "database/creds/app-readonly" {
  capabilities = ["read"]
  # Dynamic credentials, rotate on read
}

# Lease config
lease {
  ttl = "1h"
  max_ttl = "24h"
  renewable = true
}

# Rotation policy for static secrets
rotation_policy "pg-root" {
  type = "static"
  rotation_period = "30d"
  username = "root@postgres"
}
```

### 3.2 Cloud-Native Secret Managers

**AWS Secrets Manager**:
- Automatic rotation via Lambda (RotationLambdaARN)
- Version staging (AWSCURRENT, AWSPENDING, AWSPREVIOUS)
- KMS envelope encryption per secret
- VPC endpoint for private access

**GCP Secret Manager**:
- Manual rotation (create new version)
- Automatic deletion schedules
- IAM-based access (roles/secretmanager.secretAccessor)
- Customer-managed encryption keys (CMEK)

**Azure Key Vault**:
- Key rotation via Azure Functions
- Soft-delete + purge protection (90-day recovery)
- HSM-backed (Managed HSM tier)
- Private endpoint via Private Link

---

## 4. Implementation Patterns by Secret Type

### 4.1 Database Credential Rotation

```
┌───────────────────────────────────────────────────────────────┐
│          DATABASE CREDENTIAL ROTATION STRATEGY                 │
├───────────────────────────────────────────────────────────────┤
│                                                                 │
│  Pattern: Dual-User Rotation (PostgreSQL example)             │
│                                                                 │
│  Initial State:                                                │
│  • app_user_v1 (ACTIVE)   → Application uses this             │
│  • app_user_v2 (INACTIVE) → Pre-created, not used             │
│                                                                 │
│  Rotation Steps:                                               │
│  ┌─────────────────────────────────────────────────┐          │
│  │ 1. CREATE USER app_user_v2                      │          │
│  │    WITH PASSWORD 'new_generated_password'       │          │
│  │    VALID UNTIL 'now+90days';                    │          │
│  │                                                  │          │
│  │ 2. GRANT SELECT, INSERT, UPDATE, DELETE         │          │
│  │    ON ALL TABLES IN SCHEMA public               │          │
│  │    TO app_user_v2;                               │          │
│  │                                                  │          │
│  │ 3. UPDATE secret store with v2 credentials      │          │
│  │    (tag as AWSPENDING)                           │          │
│  │                                                  │          │
│  │ 4. Propagate to applications                    │          │
│  │    • Rolling restart / sidecar refresh          │          │
│  │    • Connection pool drain + reconnect          │          │
│  │                                                  │          │
│  │ 5. Verify: SELECT current_user; → app_user_v2  │          │
│  │    Check query success rate = 100%              │          │
│  │                                                  │          │
│  │ 6. Tag v2 as AWSCURRENT                         │          │
│  │    Tag v1 as AWSPREVIOUS                        │          │
│  │                                                  │          │
│  │ 7. REVOKE ALL PRIVILEGES ON ALL TABLES          │          │
│  │    IN SCHEMA public FROM app_user_v1;           │          │
│  │                                                  │          │
│  │ 8. DROP USER app_user_v1; (after grace period) │          │
│  └─────────────────────────────────────────────────┘          │
│                                                                 │
│  Failure Modes:                                                │
│  • Grant failure: Rollback to v1, alert on insufficient privs │
│  • Propagation timeout: Keep v1 active, retry with backoff    │
│  • Connection spike: Rate limit via PgBouncer connection pool │
│                                                                 │
└───────────────────────────────────────────────────────────────┘
```

### 4.2 TLS Certificate Rotation (mTLS)

```
┌────────────────────────────────────────────────────────────────┐
│           TLS/mTLS CERTIFICATE ROTATION (SPIFFE/SPIRE)         │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   SPIRE Server (CA)                      │   │
│  │  ┌────────────────────────────────────────────────┐     │   │
│  │  │  CA Bundle:                                     │     │   │
│  │  │  • Root CA (self-signed, 10yr)                 │     │   │
│  │  │  • Intermediate CA (signed by root, 5yr)       │     │   │
│  │  │  • Automatic intermediate rotation (yearly)    │     │   │
│  │  └────────────────────────────────────────────────┘     │   │
│  └────────────────┬────────────────────────────────────────┘   │
│                   │ SVID Issuance (SPIFFE Verifiable ID)       │
│                   │ • TTL: 1 hour default                       │
│                   │ • x509 or JWT format                        │
│                   │                                             │
│       ┌───────────┴──────────┬──────────────┬─────────────┐    │
│       ▼                      ▼              ▼             ▼    │
│  ┌─────────┐          ┌─────────┐    ┌─────────┐   ┌─────────┐│
│  │ Agent-1 │          │ Agent-2 │    │ Agent-3 │   │ Agent-N ││
│  │(Pod A)  │          │(Pod B)  │    │(Pod C)  │   │(Pod N)  ││
│  └────┬────┘          └────┬────┘    └────┬────┘   └────┬────┘│
│       │ Workload API      │              │              │      │
│       │ (Unix socket)     │              │              │      │
│       ▼                   ▼              ▼              ▼      │
│  ┌─────────┐          ┌─────────┐    ┌─────────┐   ┌─────────┐│
│  │ App-1   │◄────────►│ App-2   │    │ App-3   │   │ App-N   ││
│  │ mTLS    │  Verify  │ mTLS    │    │ mTLS    │   │ mTLS    ││
│  └─────────┘          └─────────┘    └─────────┘   └─────────┘│
│                                                                  │
│  Rotation Flow (per workload):                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ T=0:    Issue SVID-1 (expires T=3600)                    │  │
│  │ T=2700: Pre-rotate, issue SVID-2 (75% of TTL)           │  │
│  │         • App holds both SVID-1 + SVID-2                 │  │
│  │         • Serves SVID-2 in ServerHello                   │  │
│  │         • Accepts both in ClientHello verification       │  │
│  │ T=3600: SVID-1 expires, purge from memory               │  │
│  │ T=6300: Pre-rotate, issue SVID-3                        │  │
│  │ ...cycle continues                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Security Properties:                                           │
│  • Automatic rotation (no manual intervention)                  │
│  • Short-lived certs (1h) limit compromise window              │
│  • No CRL required (short TTL makes revocation implicit)       │
│  • Workload attestation (node + kernel proof)                  │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

### 4.3 API Key / Service Account Token Rotation

```
┌──────────────────────────────────────────────────────────────┐
│          API KEY ROTATION (Kubernetes SA Token)               │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  Kubernetes Service Account Tokens (Projected Volumes)       │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ apiVersion: v1                                          │  │
│  │ kind: Pod                                               │  │
│  │ spec:                                                   │  │
│  │   serviceAccountName: my-app                            │  │
│  │   containers:                                           │  │
│  │   - name: app                                           │  │
│  │     volumeMounts:                                       │  │
│  │     - name: token                                       │  │
│  │       mountPath: /var/run/secrets/tokens                │  │
│  │   volumes:                                              │  │
│  │   - name: token                                         │  │
│  │     projected:                                          │  │
│  │       sources:                                          │  │
│  │       - serviceAccountToken:                            │  │
│  │           path: token                                   │  │
│  │           expirationSeconds: 3600  ← 1hr TTL            │  │
│  │           audience: my-api-server                       │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                                │
│  Rotation Mechanism:                                          │
│  • kubelet auto-refreshes token at 80% of TTL (48min)        │
│  • Atomic write to mounted file (inotify triggers reload)    │
│  • Application watches file via fsnotify/inotify             │
│  • On change: re-read token, update HTTP client              │
│                                                                │
│  Application Pattern (Go example skeleton):                   │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ watcher, _ := fsnotify.NewWatcher()                     │  │
│  │ watcher.Add("/var/run/secrets/tokens/token")            │  │
│  │                                                          │  │
│  │ for event := range watcher.Events {                     │  │
│  │   if event.Op&fsnotify.Write == fsnotify.Write {        │  │
│  │     newToken := readToken(tokenPath)                    │  │
│  │     atomic.StorePointer(&currentToken, &newToken)       │  │
│  │     // Existing connections continue with old token     │  │
│  │     // New connections use new token                    │  │
│  │   }                                                      │  │
│  │ }                                                        │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                                │
└──────────────────────────────────────────────────────────────┘
```

---

## 5. Threat Model & Attack Scenarios

### 5.1 Threat Matrix

```
┌────────────────────────────────────────────────────────────────────┐
│                 SECRET ROTATION THREAT MODEL                        │
├────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Threat: Credential Theft During Rotation                          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Attack Vector: MITM during propagation                       │  │
│  │ • Attacker intercepts secret delivery over unencrypted chan. │  │
│  │ • Captures both old and new credentials                      │  │
│  │                                                               │  │
│  │ Mitigations:                                                  │  │
│  │ ✓ mTLS for all secret distribution channels                  │  │
│  │ ✓ Mutual authentication (SPIFFE IDs)                         │  │
│  │ ✓ Envelope encryption (secrets encrypted at rest + transit) │  │
│  │ ✓ Network segmentation (secret store on isolated subnet)    │  │
│  │ ✓ Deny egress from secret store except to known consumers   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  Threat: Replay Attack with Revoked Credentials                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Attack Vector: Use old credential after rotation             │  │
│  │ • Attacker holds V1, rotation occurs to V2                   │  │
│  │ • Attacker attempts to use V1 during overlap window          │  │
│  │ • If backend doesn't validate version, access granted        │  │
│  │                                                               │  │
│  │ Mitigations:                                                  │  │
│  │ ✓ Version-aware authentication (check secret version ID)     │  │
│  │ ✓ Explicit revocation lists (CRLs, OCSP for certs)          │  │
│  │ ✓ Short overlap windows (< 5min for high-security)          │  │
│  │ ✓ Audit logging of all auth attempts with version tags      │  │
│  │ ✓ Anomaly detection on old version usage post-rotation      │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  Threat: Rotation Controller Compromise                            │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Attack Vector: Attacker gains control of rotation orchestrat.│  │
│  │ • Issue malicious credentials to workloads                   │  │
│  │ • Extract current secrets from controller memory             │  │
│  │ • Disable rotation entirely (freeze on known compromise)     │  │
│  │                                                               │  │
│  │ Mitigations:                                                  │  │
│  │ ✓ HSM-backed key generation (controller never sees DEK)      │  │
│  │ ✓ Audit logs signed with witness (Trillian, Rekor)          │  │
│  │ ✓ Least-privilege: controller can only trigger rotation      │  │
│  │ ✓ Secrets sealed to workload identity (Vault entity IDs)     │  │
│  │ ✓ Multi-party approval for manual rotations (PagerDuty)      │  │
│  │ ✓ Runtime integrity monitoring (Falco rules on controller)   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  Threat: Timing Attack / Race Condition                            │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Attack Vector: Exploit race between rotate + revoke          │  │
│  │ T=0: Rotation starts, V2 issued                              │  │
│  │ T=1: Attacker uses V1 (still valid)                          │  │
│  │ T=2: V1 revoked, but attacker's request already in-flight    │  │
│  │ T=3: Backend processes request with now-revoked V1           │  │
│  │                                                               │  │
│  │ Mitigations:                                                  │  │
│  │ ✓ Server-side timestamp validation (not client-provided)     │  │
│  │ ✓ Request-scoped nonces (prevent replay)                     │  │
│  │ ✓ Grace period must exceed max request latency (p99)        │  │
│  │ ✓ Monotonic version counters (reject V1 if V2 seen)         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
└────────────────────────────────────────────────────────────────────┘
```

### 5.2 Defense-in-Depth Controls

```
Layer 1 - Secret Generation
├─ Cryptographically secure RNG (CSPRNG, /dev/urandom)
├─ Minimum entropy requirements (256-bit for symmetric keys)
├─ HSM/TPM backing for high-value keys
└─ Avoid predictable patterns (timestamps, sequential IDs)

Layer 2 - Storage
├─ Encryption at rest (AES-256-GCM with KMS-managed KEK)
├─ Access control (IAM policies, RBAC, ACLs)
├─ Audit logging (immutable, signed logs)
└─ Physical security (HSM tamper protection)

Layer 3 - Distribution
├─ Encrypted channels (TLS 1.3, mTLS, WireGuard)
├─ Authentication (SPIFFE IDs, workload attestation)
├─ Authorization (OPA policies, admission controllers)
└─ Rate limiting (prevent secret enumeration)

Layer 4 - Usage
├─ Memory protection (mlock, encrypted memory)
├─ Process isolation (seccomp, AppArmor, SELinux)
├─ Short-lived credentials (reduce exposure window)
└─ Least privilege (scope to exact required access)

Layer 5 - Rotation
├─ Automated rotation (no manual intervention)
├─ Graceful cutover (zero-downtime overlap)
├─ Verification (synthetic transactions, health checks)
└─ Rollback capability (keep N-1 version)

Layer 6 - Revocation
├─ Immediate revocation API (emergency kill switch)
├─ Propagation verification (confirm all consumers updated)
├─ Grace period enforcement (coordinate with consumers)
└─ Cryptographic erasure (secure memory wipe)

Layer 7 - Monitoring
├─ Anomaly detection (unusual access patterns)
├─ Failed auth tracking (threshold-based alerts)
├─ Secret age tracking (rotation SLO violations)
└─ Compliance reporting (audit trail retention)
```

---

## 6. Operational Procedures & Runbooks

### 6.1 Emergency Rotation Procedure

```
┌────────────────────────────────────────────────────────────────┐
│               EMERGENCY ROTATION RUNBOOK                        │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Trigger: Suspected credential compromise                       │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐│
│  │ PHASE 1: CONTAINMENT (T+0 to T+5min)                       ││
│  ├────────────────────────────────────────────────────────────┤│
│  │ 1. Declare incident (PagerDuty severity-1)                 ││
│  │    # incident-cli create --title "Secret compromise" \     ││
│  │        --severity SEV1 --service auth-backend              ││
│  │                                                             ││
│  │ 2. Revoke compromised credential immediately               ││
│  │    # vault token revoke <TOKEN_ID>                         ││
│  │    # aws iam delete-access-key --access-key-id <KEY>       ││
│  │                                                             ││
│  │ 3. Block suspicious IPs at perimeter                       ││
│  │    # iptables -A INPUT -s <IP> -j DROP                     ││
│  │    # Update WAF rules, CDN block list                      ││
│  │                                                             ││
│  │ 4. Enable enhanced logging                                 ││
│  │    # kubectl patch configmap audit-policy \                ││
│  │        -p '{"data":{"level":"RequestResponse"}}'           ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐│
│  │ PHASE 2: ROTATION (T+5 to T+15min)                         ││
│  ├────────────────────────────────────────────────────────────┤│
│  │ 1. Generate new credentials                                ││
│  │    # rotation-controller trigger \                         ││
│  │        --secret-id prod/api-key \                          ││
│  │        --priority emergency \                               ││
│  │        --overlap-window 0                                   ││
│  │                                                             ││
│  │ 2. Force propagation to all consumers                      ││
│  │    # kubectl rollout restart deployment/api-server         ││
│  │    # helm upgrade --reuse-values --force app ./chart       ││
│  │                                                             ││
│  │ 3. Verify new credentials active                           ││
│  │    # for pod in $(kubectl get pods -l app=api -o name); do││
│  │        kubectl exec $pod -- curl -H "Auth: NEW_TOKEN" \    ││
│  │          http://localhost/health                           ││
│  │      done                                                   ││
│  │                                                             ││
│  │ 4. Confirm zero traffic on old credentials                 ││
│  │    # prometheus query: auth_attempts{version="old"} == 0   ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐│
│  │ PHASE 3: VERIFICATION (T+15 to T+30min)                    ││
│  ├────────────────────────────────────────────────────────────┤│
│  │ 1. Run security scan                                       ││
│  │    # trivy image --scanners secret app:latest              ││
│  │    # git-secrets --scan-history                            ││
│  │    # Check for hardcoded secrets in logs                   ││
│  │                                                             ││
│  │ 2. Review access logs                                      ││
│  │    # grep "401\|403" /var/log/auth.log | tail -1000       ││
│  │    # Identify source IPs of failed attempts                ││
│  │                                                             ││
│  │ 3. Check lateral movement indicators                       ││
│  │    # osquery: SELECT * FROM processes WHERE name LIKE '%'  ││
│  │    # Falco alerts for suspicious syscalls                  ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐│
│  │ PHASE 4: POST-INCIDENT (T+30min onward)                    ││
│  ├────────────────────────────────────────────────────────────┤│
│  │ 1. Root cause analysis (5 Whys)                            ││
│  │ 2. Update threat model                                     ││
│  │ 3. Patch vulnerability that led to compromise              ││
│  │ 4. Incident retrospective (blameless)                      ││
│  │ 5. Update runbook with learnings                           ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                  │
│  Rollback Criteria:                                             │
│  • >5% error rate after rotation → Revert to old credential    │
│  • Service degradation (p99 latency > SLO) → Investigate       │
│  • New credential rejected by backend → Verify IAM policy      │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

### 6.2 Testing Strategy

```
┌────────────────────────────────────────────────────────────────┐
│              ROTATION TESTING & VALIDATION                      │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Unit Tests (per component)                                     │
│  ├─ Secret generation: entropy validation, format checks       │
│  ├─ State machine: FSM transition correctness                  │
│  ├─ Versioning: monotonic counter, conflict detection          │
│  └─ Rollback: revert to N-1, N-2 versions                      │
│                                                                  │
│  Integration Tests (subsystem)                                  │
│  ┌────────────────────────────────────────────────────────────┐│
│  │ # Testcontainers setup                                     ││
│  │ vault := testcontainers.Vault()                            ││
│  │ postgres := testcontainers.Postgres()                      ││
│  │                                                             ││
│  │ // Test: Rotation preserves access                         ││
│  │ oldCreds := postgres.GetCreds()                            ││
│  │ assert(postgres.Query(oldCreds) == success)                ││
│  │                                                             ││
│  │ newCreds := vault.RotateDBCreds(postgres)                  ││
│  │                                                             ││
│  │ // Both should work during overlap                         ││
│  │ assert(postgres.Query(oldCreds) == success)                ││
│  │ assert(postgres.Query(newCreds) == success)                ││
│  │                                                             ││
│  │ vault.FinalizeRotation()                                   ││
│  │                                                             ││
│  │ // Only new should work post-rotation                      ││
│  │ assert(postgres.Query(oldCreds) == error)                  ││
│  │ assert(postgres.Query(newCreds) == success)                ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                  │
│  Chaos Tests (failure injection)                               │
│  ├─ Network partition during rotation (Chaos Mesh)             │
│  ├─ Secret store outage (kill Vault leader)                    │
│  ├─ Consumer pod crash mid-rotation                            │
│  ├─ Clock skew simulation (libfaketime)                        │
│  └─ Race condition: concurrent rotation requests               │
│                                                                  │
│  Load Tests (stress rotation under load)                       │
│  ┌────────────────────────────────────────────────────────────┐│
│  │ # k6 load test                                             ││
│  │ import http from 'k6/http';                                ││
│  │                                                             ││
│  │ export default function() {                                ││
│  │   // Sustained load: 10k RPS                               ││
│  │   http.get('https://api/endpoint', {                       ││
│  │     headers: { 'Authorization': getToken() }              ││
│  │   });                                                       ││
│  │ }                                                           ││
│  │                                                             ││
│  │ // Trigger rotation during test                            ││
│  │ // Measure: latency spike, error rate, recovery time      ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                  │
│  E2E Tests (production-like)                                    │
│  ├─ Staging environment rotation (weekly)                      │
│  ├─ Canary deployment with rotation                            │
│  ├─ Multi-region rotation coordination                         │
│  └─ Compliance audit simulation (PCI-DSS checks)               │
│                                                                  │
│  Observability Validation                                       │
│  ├─ Metrics: rotation_duration_seconds (target: <5min p99)     │
│  ├─ Alerts: rotation_failures_total (threshold: 0)             │
│  ├─ Traces: end-to-end rotation span (Jaeger)                  │
│  └─ Logs: audit trail completeness (SIEM ingestion)            │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

---

## 7. Production Considerations & Best Practices

### 7.1 Rotation Scheduling & SLOs

```
Secret Type          | Rotation Frequency | Max TTL | Overlap Window
─────────────────────┼───────────────────┼─────────┼────────────────
Root CA Keys         | 5-10 years         | N/A     | 6 months
Intermediate CA      | 1-2 years          | N/A     | 3 months
Service Certs (mTLS) | 1 hour             | 24 hours| 15 minutes
Database Passwords   | 30 days            | 90 days | 5 minutes
API Keys (static)    | 90 days            | 1 year  | 24 hours
IAM Access Keys      | 90 days            | 1 year  | 7 days
Kubernetes SA Tokens | 1 hour             | 24 hours| Auto (80% TTL)
Encryption Keys (DEK)| 30 days            | 1 year  | Until re-encrypt
SSH Host Keys        | Never (unless comp)| N/A     | N/A
Break-glass Accounts | After each use     | N/A     | None (revoke)
```

### 7.2 Compliance Mapping

```
┌─────────────────────────────────────────────────────────────────┐
│            COMPLIANCE REQUIREMENTS FOR ROTATION                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  PCI-DSS 3.2.1                                                   │
│  ├─ Req 8.2.4: Change user passwords every 90 days              │
│  ├─ Req 8.3.2: Strong cryptography for transmission             │
│  └─ Req 10.2: Automated audit trails for key management         │
│                                                                   │
│  SOC 2 Type II                                                   │
│  ├─ CC6.1: Logical access controls (rotation as control)        │
│  ├─ CC6.6: Encryption key management                             │
│  └─ CC7.2: System monitoring (rotation events)                  │
│                                                                   │
│  NIST 800-57                                                     │
│  ├─ Key lifetime recommendations (Table 4-4)                     │
│  ├─ Cryptoperiod enforcement                                     │
│  └─ Key compromise procedures (Section 9)                        │
│                                                                   │
│  HIPAA Security Rule                                             │
│  ├─ §164.312(a)(2)(iv): Encryption/decryption                    │
│  ├─ §164.308(a)(5)(ii)(C): Log-in monitoring                     │
│  └─ §164.312(b): Audit controls (rotation audit trail)           │
│                                                                   │
│  GDPR (Indirect)                                                 │
│  ├─ Art 32: Security of processing (rotation as control)        │
│  └─ Art 33: Breach notification (compromise → rotation)          │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 7.3 Anti-Patterns to Avoid

```
❌ Manual rotation without automation
   → Human error, inconsistent timing, forgotten systems

❌ Rotating without overlap window
   → Service outages during cutover, connection failures

❌ Hardcoding grace period as constant
   → Use (max_propagation_latency × 2) + buffer

❌ Not versioning secrets
   → Cannot track which consumers use old credentials

❌ Storing secrets in version control
   → Use secret stores, not git (even private repos)

❌ Rotating without verification
   → Broken rotations go unnoticed until incident

❌ Single secret for all environments
   → Prod compromise = dev/staging also compromised

❌ Ignoring partial failures
   → One consumer stuck on old credential → entire rotation fails

❌ No rollback plan
   → If rotation breaks prod, no way to recover quickly

❌ Logging secrets during rotation
   → Audit logs should log secret ID, not plaintext value
```

---

## 8. Advanced Topics

### 8.1 Multi-Region Rotation Coordination

```
┌────────────────────────────────────────────────────────────────┐
│          MULTI-REGION ROTATION (Active-Active)                  │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Challenge: Coordinate rotation across geographically           │
│             distributed systems without centralized lock        │
│                                                                  │
│  ┌──────────────┐       ┌──────────────┐       ┌──────────────┐│
│  │ Region: US   │       │ Region: EU   │       │ Region: APAC ││
│  │  ┌────────┐  │       │  ┌────────┐  │       │  ┌────────┐  ││
│  │  │ Vault  │  │◄─────►│  │ Vault  │  │◄─────►│  │ Vault  │  ││
│  │  │Cluster │  │ Raft  │  │Cluster │  │ Raft  │  │Cluster │  ││
│  │  └────────┘  │       │  └────────┘  │       │  └────────┘  ││
│  └──────┬───────┘       └──────┬───────┘       └──────┬───────┘│
│         │                      │                      │         │
│         │   Global Coordination Layer (etcd/Consul)   │         │
│         └──────────────────────┼──────────────────────┘         │
│                                │                                 │
│                    ┌───────────▼───────────┐                    │
│                    │ Rotation Orchestrator │                    │
│                    │ ├─ Leader Election    │                    │
│                    │ ├─ Version Consensus  │                    │
│                    │ └─ Phase Coordination │                    │
│                    └───────────────────────┘                    │
│                                                                  │
│  Rotation Phases (with consensus):                              │
│  ┌────────────────────────────────────────────────────────────┐│
│  │ Phase 1: PROPOSE (Leader election)                         ││
│  │   • Single region elected as rotation leader               ││
│  │   • Generates new secret version                           ││
│  │   • Proposes to other regions (2PC prepare)                ││
│  │                                                             ││
│  │ Phase 2: VALIDATE (All regions ack)                        ││
│  │   • Each region checks: can I accept this rotation?        ││
│  │   • Verify no conflicts, sufficient capacity               ││
│  │   • Vote: ACCEPT or REJECT                                 ││
│  │                                                             ││
│  │ Phase 3: COMMIT (Quorum reached)                           ││
│  │   • If >50% regions vote ACCEPT → proceed                  ││
│  │   • Each region propagates to local consumers              ││
│  │   • Atomic version bump across all regions                 ││
│  │                                                             ││
│  │ Phase 4: FINALIZE (Old version revoke)                     ││
│  │   • After global overlap period expires                    ││
│  │   • Coordinated revocation (all regions simultaneously)    ││
│  │   • Audit log aggregation to central SIEM                  ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                  │
│  Failure Handling:                                              │
│  • Network partition: Abort rotation, retry after heal         │
│  • Region timeout: Proceed if quorum reached (>50%)            │
│  • Split-brain: Raft consensus prevents dual-issue             │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

### 8.2 Cryptographic Key Rotation vs Re-Encryption

```
Key Rotation (KEK): Change the key that encrypts data keys
├─ Rotate master key in KMS (AWS KMS, GCP Cloud KMS)
├─ Re-wrap DEKs with new KEK (no data re-encryption)
├─ Fast: O(number of DEKs), not O(data size)
└─ Use case: KEK compromise, compliance requirement

Re-Encryption (DEK): Change the data encryption key itself
├─ Decrypt data with old DEK
├─ Encrypt data with new DEK
├─ Slow: O(data size), requires full data scan
└─ Use case: DEK compromise, algorithm migration (AES-128→256)

Envelope Encryption Pattern:
  Data → Encrypt with DEK → Ciphertext
  DEK → Encrypt with KEK → Wrapped DEK
  Store: Ciphertext + Wrapped DEK

Rotation Strategy:
  1. Rotate KEK quarterly (fast, no downtime)
  2. Re-encrypt DEK annually (schedule during low-traffic)
  3. Emergency: Both if DEK compromised
```

---

## 9. Actionable Implementation Checklist

```
┌────────────────────────────────────────────────────────────────┐
│         SECRET ROTATION IMPLEMENTATION ROADMAP                  │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│ Phase 1: Foundation (Week 1-2)                                 │
│ ☐ Inventory all secrets (spreadsheet: type, location, owner)   │
│ ☐ Deploy secret store (Vault, AWS Secrets Manager)             │
│ ☐ Migrate static secrets from env vars → secret store          │
│ ☐ Implement secret injection (k8s CSI driver, Vault agent)     │
│ ☐ Enable audit logging (immutable, signed)                     │
│                                                                  │
│ Phase 2: Dynamic Secrets (Week 3-4)                            │
│ ☐ Enable dynamic DB secrets (Vault database engine)            │
│ ☐ Configure TTLs (start: 24h, iterate down to 1h)              │
│ ☐ Implement client-side token renewal (exponential backoff)    │
│ ☐ Test: connection pool behavior during renewal                │
│ ☐ Monitor: secret age, renewal success rate                    │
│                                                                  │
│ Phase 3: Automated Rotation (Week 5-6)                         │
│ ☐ Build rotation controller (Go/Rust preferred)                │
│ ☐ Implement state machine (PENDING→ACTIVE→DEPRECATED→REVOKED)  │
│ ☐ Add overlap window logic (configurable per secret type)      │
│ ☐ Integration tests (Testcontainers, chaos injection)          │
│ ☐ Deploy to staging, rotate test secrets                       │
│                                                                  │
│ Phase 4: Production Rollout (Week 7-8)                         │
│ ☐ Rotate non-critical secrets first (dev API keys)             │
│ ☐ Canary: 5% of prod traffic with rotated secrets              │
│ ☐ Monitor: error rate, latency, auth failures                  │
│ ☐ Full rollout: all secrets on automated rotation schedule     │
│ ☐ Document runbooks (emergency rotation, rollback)             │
│                                                                  │
│ Phase 5: Advanced Features (Week 9+)                           │
│ ☐ Multi-region coordination (if applicable)                    │
│ ☐ mTLS certificate rotation (SPIRE/Istio)                      │
│ ☐ Encryption key rotation (KEK + DEK)                          │
│ ☐ Compliance reporting (PCI-DSS audit trail)                   │
│ ☐ Continuous improvement (reduce TTLs, shorten overlap)        │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

---

## 10. Threat Modeling Exercise

**Scenario**: API key rotation for microservice fleet (100 services)

```
Asset: API keys for inter-service authentication
Threat Actors: External attacker, malicious insider, supply chain
Attack Surface: Secret store, distribution channels, consumer memory

Critical Threats:
1. Secret Store Compromise (Vault breach)
   → Defense: HSM backing, access audit, intrusion detection
   
2. MITM During Propagation (network intercept)
   → Defense: mTLS, SPIFFE IDs, encrypted channels
   
3. Consumer Memory Dump (core dump contains secret)
   → Defense: mlock(), encrypted memory, no core dumps
   
4. Replay Attack (old key used after rotation)
   → Defense: Version validation, short overlap, CRL
   
5. Rotation Timing Attack (exploit cutover window)
   → Defense: Atomic updates, request nonces, monotonic versions

Risk Matrix:
  Likelihood × Impact = Priority
  - Secret Store Compromise: Medium × Critical = HIGH
  - MITM: Low × High = MEDIUM
  - Memory Dump: Medium × High = HIGH
  - Replay Attack: High × Medium = HIGH
  - Timing Attack: Low × Low = LOW

Mitigations Prioritized by ROI:
  1. HSM-backed secret store (high impact, low effort)
  2. mTLS for distribution (high impact, medium effort)
  3. Memory protection (high impact, high effort)
  4. Version validation (medium impact, low effort)
  5. Timing attack defenses (low impact, high effort) ← defer
```

---

## 11. Monitoring & Observability

```
Key Metrics (Prometheus/Datadog):

# Rotation health
secret_rotation_duration_seconds{secret_type, status}
  → Target: p99 < 300s (5min)
  → Alert: p99 > 600s

secret_rotation_failures_total{secret_type, reason}
  → Target: 0 failures/hour
  → Alert: > 0 failures

secret_age_seconds{secret_id}
  → Target: < rotation_period
  → Alert: > rotation_period + 7d (grace)

# Usage patterns
secret_usage_by_version{secret_id, version}
  → Detect: old version usage post-rotation (replay attack)

auth_failures_total{secret_id, consumer}
  → Spike detection: rotation-induced outages

# Propagation
secret_propagation_lag_seconds{region, consumer}
  → Target: < 60s (1min)
  → Alert: > 300s (5min)

Logging (Structured JSON):
{
  "event": "secret_rotation",
  "secret_id": "prod/db/api-user",
  "old_version": "v42",
  "new_version": "v43",
  "overlap_start": "2026-01-07T10:00:00Z",
  "overlap_end": "2026-01-07T10:25:00Z",
  "status": "completed",
  "duration_ms": 245000,
  "consumers_updated": 127,
  "consumers_failed": 0
}

Alerting Rules:
- Page on-call: rotation failure, emergency rotation needed
- Slack warn: rotation SLO violation, high propagation lag
- Email: rotation scheduled (24h notice), completion report
```

---

## 12. References & Standards

**Standards**:
- NIST SP 800-57: Key Management Recommendations  
- FIPS 140-2/140-3: Cryptographic Module Requirements  
- NIST SP 800-131A: Transitioning to Cryptographic Algorithms  
- OWASP Secrets Management Cheat Sheet

**Tools**:
- HashiCorp Vault: https://www.vaultproject.io/  
- SPIFFE/SPIRE: https://spiffe.io/  
- AWS Secrets Manager: https://aws.amazon.com/secrets-manager/  
- GCP Secret Manager: https://cloud.google.com/secret-manager  
- cert-manager (Kubernetes): https://cert-manager.io/  
- Sealed Secrets: https://github.com/bitnami-labs/sealed-secrets

**Papers**:
- "Zanzibar: Google's Consistent Global Authorization System" (ACL versioning)  
- "Keywhiz: Secret Distribution" (Square's approach)  
- "Tink: Cryptographic Library" (Google, key rotation patterns)

**CNCF Projects**:
- External Secrets Operator: Sync secrets from external stores  
- Bank-Vaults: Vault operator for Kubernetes  
- cert-manager: Automated certificate lifecycle

---

## Next 3 Steps

1. **Inventory & Classify** (Day 1):  
   ```bash
   # Audit current secrets
   find /etc -name "*key*" -o -name "*secret*" 2>/dev/null
   grep -r "password\|api.key" /app/config/
   # Classify: static vs dynamic, rotation freq, blast radius
   ```

2. **Deploy Secret Store** (Week 1):  
   ```bash
   # Vault PoC (dev mode for testing)
   vault server -dev -dev-root-token-id=root
   vault secrets enable -path=myapp kv-v2
   vault write myapp/db password="$(openssl rand -base64 32)"
   # Production: HA cluster with Raft/Consul backend
   ```

3. **Implement First Rotation** (Week 2):  
   ```bash
   # Start with low-risk secret (dev DB password)
   # Test overlap window, verify zero-downtime
   # Document learnings, iterate on prod secrets
   # Build runbook for emergency rotation
   ```

**Success Criteria**: All production secrets rotated automatically within 90 days, zero-downtime cutover, audit trail compliance-ready, emergency rotation playbook tested quarterly.