# Certificate Authority (CA) – Comprehensive Deep Dive

Certificate Authorities are the cryptographic trust anchors of PKI systems, issuing X.509 digital certificates that bind public keys to identities. In production systems, CAs enforce authentication, enable TLS/mTLS, sign code/containers, and establish zero-trust boundaries. Understanding CA internals—from HSM-backed root keys to OCSP/CRL revocation, certificate chain validation, and automated certificate lifecycle (ACME)—is critical for securing distributed systems, service meshes, API gateways, and multi-cloud workloads. This guide covers architectural models (offline root + intermediate CAs), cryptographic primitives (RSA/ECDSA, SHA-256/384), operational security (air-gapped roots, HSM/KMS integration), threat modeling (compromise scenarios, key escrow risks), and production deployment patterns (Vault PKI, cert-manager, SPIFFE/SPIRE, AWS Private CA).

---

## Table of Contents

1. **What is a Certificate Authority**
2. **PKI Architecture & Trust Models**
3. **X.509 Certificate Structure**
4. **CA Hierarchy: Root, Intermediate, Leaf**
5. **Certificate Lifecycle: Issuance, Renewal, Revocation**
6. **Cryptographic Primitives & Key Management**
7. **Certificate Validation & Chain of Trust**
8. **Revocation Mechanisms: CRL, OCSP, OCSP Stapling**
9. **Automated Certificate Management (ACME, cert-manager)**
10. **Hardware Security Modules (HSMs) & Key Storage**
11. **Production CA Systems (Vault PKI, CFSSL, Step-CA, AWS Private CA)**
12. **mTLS, Service Mesh, SPIFFE/SPIRE**
13. **Threat Model & Attack Surface**
14. **Monitoring, Auditing, Compliance**
15. **Deployment Architectures & Failure Modes**
16. **Hands-On Labs & Configuration Examples**
17. **Next 3 Steps**

---

## 1. What is a Certificate Authority

**Definition**: A CA is a trusted entity that issues, signs, and manages digital certificates. It cryptographically binds a public key to an identity (domain, service, user) via X.509 certificates.

**Core Functions**:
- **Identity Verification**: Validate certificate subject (DV, OV, EV for web; service identity for workloads)
- **Certificate Signing**: Use CA private key to sign certificate signing request (CSR)
- **Revocation**: Publish CRL or OCSP responses for compromised/expired certificates
- **Trust Anchor**: Root CA certificate is pre-installed in trust stores (browsers, OS, applications)

**Types**:
- **Public CAs**: Let's Encrypt, DigiCert, GlobalSign (trusted by browsers/OS)
- **Private CAs**: Internal PKI for enterprises, service mesh, mTLS (not publicly trusted)
- **Subordinate/Intermediate CAs**: Signed by root CA, used for operational issuance

**Real-World Use Cases**:
- TLS/HTTPS server authentication
- Mutual TLS (mTLS) for service-to-service auth
- Code signing (containers, binaries, firmware)
- User/device authentication (smart cards, VPNs)
- Email encryption (S/MIME)

---

## 2. PKI Architecture & Trust Models

### Trust Models

**Hierarchical (Tree)**:
```
         [Root CA] (offline, air-gapped)
              |
    +---------+---------+
    |                   |
[Intermediate CA 1] [Intermediate CA 2] (online, HSM-backed)
    |                   |
[Leaf Cert]         [Leaf Cert]
```
- Root CA signs intermediate CAs
- Intermediate CAs issue end-entity certificates
- Root CA private key kept offline for security

**Cross-Signed/Bridge**:
- Multiple root CAs cross-sign each other (federated trust)
- Used in multi-org scenarios (gov't, healthcare)

**Web of Trust** (PGP/GPG):
- Decentralized, peer-to-peer signing
- Not used in enterprise PKI

### Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                         Root CA                             │
│  - Private Key in HSM (offline, air-gapped)                 │
│  - Self-signed root certificate                             │
│  - Ceremony-based key generation (quorum, dual control)     │
└────────────────────┬────────────────────────────────────────┘
                     │ Signs
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   Intermediate CA                           │
│  - Private Key in HSM (online/networked)                    │
│  - Certificate signed by Root CA                            │
│  - Issues end-entity certificates                           │
│  - Handles CSRs, revocation, OCSP                           │
└────────────────────┬────────────────────────────────────────┘
                     │ Issues
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Leaf Certificates                        │
│  - Server certs (TLS), client certs (mTLS)                  │
│  - Short-lived (hours to 90 days)                           │
│  - Private keys stay on workload (never sent to CA)         │
└─────────────────────────────────────────────────────────────┘
```

**Key Principles**:
- **Root CA offline**: Minimize attack surface, used only for signing intermediates
- **Intermediate CA online**: Automated issuance, API-accessible
- **Short-lived leaves**: Reduce revocation overhead, limit blast radius

---

## 3. X.509 Certificate Structure

X.509 v3 is the standard format (RFC 5280). Certificates are ASN.1 DER-encoded, often presented as PEM (Base64).

### Certificate Fields

```
Certificate:
    Data:
        Version: 3 (0x2)
        Serial Number: 0xaabbccdd
        Signature Algorithm: ecdsa-with-SHA256
        Issuer: CN=Intermediate CA, O=Example Corp
        Validity:
            Not Before: 2026-01-01 00:00:00 UTC
            Not After:  2026-04-01 00:00:00 UTC
        Subject: CN=api.example.com, O=Example Corp
        Subject Public Key Info:
            Public Key Algorithm: id-ecPublicKey (P-256)
            Public Key: 04:xx:xx:...
        X509v3 Extensions:
            X509v3 Key Usage: critical
                Digital Signature, Key Encipherment
            X509v3 Extended Key Usage:
                TLS Web Server Authentication
            X509v3 Subject Alternative Name:
                DNS:api.example.com, DNS:*.api.example.com
            X509v3 Authority Key Identifier:
                keyid:aa:bb:cc:...
            X509v3 Subject Key Identifier:
                keyid:dd:ee:ff:...
            X509v3 CRL Distribution Points:
                URI:http://crl.example.com/intermediate.crl
            Authority Information Access:
                OCSP - URI:http://ocsp.example.com
                CA Issuers - URI:http://ca.example.com/intermediate.crt
    Signature Algorithm: ecdsa-with-SHA256
    Signature: 30:xx:xx:...
```

**Key Fields**:
- **Subject**: Identity (CN=common name, O=org, OU=unit)
- **Issuer**: CA that signed the cert
- **Serial Number**: Unique ID for this cert (used in revocation)
- **Public Key**: Subject's public key (RSA 2048/4096, ECDSA P-256/P-384)
- **Validity**: notBefore, notAfter (max 398 days for public web certs)
- **Extensions**: SAN (Subject Alternative Names), Key Usage, EKU, CRL/OCSP URIs

**Extensions (X509v3)**:
- **Key Usage**: digitalSignature, keyEncipherment, keyCertSign (for CAs)
- **Extended Key Usage**: serverAuth, clientAuth, codeSigning
- **Subject Alternative Name (SAN)**: DNS names, IP addresses, URIs (critical for TLS)
- **Basic Constraints**: CA:TRUE for CA certs, pathLenConstraint
- **CRL Distribution Points**: Where to fetch revocation lists
- **Authority Info Access**: OCSP responder URL, CA issuer cert URL

---

## 4. CA Hierarchy: Root, Intermediate, Leaf

### Root CA

**Characteristics**:
- **Self-signed**: Issuer = Subject
- **Long-lived**: 10–25 years
- **Offline**: Air-gapped, HSM-backed, ceremony-based key generation
- **Trust Anchor**: Pre-installed in OS/browser trust stores (for public CAs)

**Operational Security**:
- Store private key in FIPS 140-2 Level 3/4 HSM
- Multi-party control (quorum signing, dual control)
- Physical security (vault, access logs, video surveillance)
- Annual or less frequent use (only to sign/revoke intermediate CAs)

### Intermediate CA

**Characteristics**:
- **Signed by Root CA**: Certificate chain includes root
- **Online**: API-accessible for automated cert issuance
- **Medium-lived**: 3–10 years
- **Operational**: Handles CSRs, OCSP, CRL generation

**Security**:
- Private key in networked HSM or cloud KMS (AWS KMS, GCP Cloud HSM)
- Rate limiting, access controls, audit logging
- Can be revoked and replaced without re-distributing root

### Leaf Certificates

**Characteristics**:
- **End-entity**: Cannot sign other certificates (CA:FALSE)
- **Short-lived**: 1 hour to 90 days (automation required)
- **Workload-specific**: Each service/server has unique cert

**Benefits of Short Validity**:
- Reduced revocation overhead (cert expires before revocation matters)
- Limits blast radius of key compromise
- Forces automation (manual renewal infeasible)

---

## 5. Certificate Lifecycle: Issuance, Renewal, Revocation

### Issuance Flow

```
1. Workload generates key pair (private key never leaves workload)
2. Workload creates CSR (Certificate Signing Request)
   - Subject DN, SAN, public key, signature (proves possession of private key)
3. CSR submitted to CA (API, ACME, manual)
4. CA validates identity (domain ownership, service authentication)
5. CA signs CSR with CA private key → issues certificate
6. Certificate returned to workload
7. Workload configures cert + private key in TLS server
```

**CSR Generation (OpenSSL)**:
```bash
# Generate private key
openssl ecparam -name prime256v1 -genkey -noout -out server.key

# Create CSR
openssl req -new -key server.key -out server.csr \
  -subj "/CN=api.example.com/O=Example Corp" \
  -addext "subjectAltName=DNS:api.example.com,DNS:*.api.example.com"

# Inspect CSR
openssl req -in server.csr -noout -text
```

### Renewal

**Pre-expiration Renewal**:
- Start renewal at 2/3 of cert lifetime (e.g., 60 days into 90-day cert)
- Automated via cert-manager, Vault agent, ACME

**Re-keying vs. Re-signing**:
- **Re-key**: Generate new key pair, new CSR (recommended)
- **Re-sign**: Reuse existing key pair (not recommended, forward secrecy risk)

### Revocation

**Scenarios**:
- Private key compromised
- Certificate mis-issued (wrong identity)
- Service decommissioned
- Policy violation

**Revocation Mechanisms** (see section 8):
- **CRL (Certificate Revocation List)**: Signed list of revoked serial numbers
- **OCSP (Online Certificate Status Protocol)**: Real-time revocation check
- **OCSP Stapling**: Server includes OCSP response in TLS handshake

**Revocation Process**:
```bash
# Revoke certificate (HashiCorp Vault)
vault write pki_int/revoke serial_number=39:dd:2e:...

# Verify revocation
openssl ocsp -issuer ca.crt -cert server.crt -url http://ocsp.example.com -CAfile ca.crt
```

---

## 6. Cryptographic Primitives & Key Management

### Algorithms

**Asymmetric (Public Key)**:
- **RSA**: 2048-bit (legacy), 3072/4096-bit (modern)
  - Slower, larger keys/certs
  - Widely compatible
- **ECDSA**: P-256 (secp256r1), P-384 (secp384r1)
  - Faster, smaller keys/certs
  - Modern default (TLS 1.3, service mesh)
- **EdDSA**: Ed25519, Ed448 (emerging, not yet universal)

**Hash Functions**:
- **SHA-256**: Default for signing (RSA-SHA256, ECDSA-SHA256)
- **SHA-384**: For P-384 ECDSA, high-security scenarios
- **SHA-1**: Deprecated (collision attacks)

**Signature Algorithms**:
- RSA with SHA-256: `sha256WithRSAEncryption`
- ECDSA with SHA-256: `ecdsa-with-SHA256`

### Key Generation & Storage

**Private Key Security**:
- **Never transmit**: Private key generated on workload, never sent to CA
- **Encryption at rest**: Filesystem encryption, key wrapping (AES-GCM)
- **Access control**: File permissions (0600), SELinux/AppArmor, namespaces

**HSMs (Hardware Security Modules)**:
- FIPS 140-2 Level 2/3: Tamper-resistant, key extraction impossible
- Cloud HSMs: AWS CloudHSM, GCP Cloud HSM, Azure Dedicated HSM
- Software HSMs: SoftHSMv2 (PKCS#11, testing only)

**KMS (Key Management Service)**:
- Cloud-native: AWS KMS, GCP Cloud KMS, Azure Key Vault
- Envelope encryption: KMS encrypts data encryption keys (DEKs)
- Rotation, auditing (CloudTrail, Stackdriver)

**Key Rotation**:
- **Root CA**: Rare (10+ years), requires re-distribution
- **Intermediate CA**: Every 3–5 years, gradual rollout
- **Leaf certs**: Every 1–90 days (automated)

---

## 7. Certificate Validation & Chain of Trust

### Validation Steps (TLS Client)

```
1. Receive server certificate chain from TLS handshake
2. Build chain: Leaf → Intermediate → Root
3. Verify each signature:
   - Leaf signed by Intermediate CA
   - Intermediate signed by Root CA
4. Check Root CA is in trust store
5. Validate certificate fields:
   - Validity period (notBefore <= now < notAfter)
   - Hostname matches SAN or CN
   - Key Usage / Extended Key Usage
6. Check revocation status (CRL or OCSP)
7. If all checks pass → certificate valid
```

**Chain Building**:
```
[Server Cert] → [Intermediate CA Cert] → [Root CA Cert (trust store)]
      ↑                  ↑                        ↑
   Leaf Cert      Intermediate Cert         Self-Signed Root
   (issued by     (issued by Root,          (pre-installed in
   Intermediate)   sent in TLS handshake)    /etc/ssl/certs/)
```

**AIA (Authority Information Access)**:
- Certificate contains URL to fetch issuer certificate
- Enables client to download missing intermediate certs
- Reduces configuration errors (incomplete chain)

### Trust Store Management

**System Trust Stores**:
- Linux: `/etc/ssl/certs/ca-certificates.crt`, `/etc/pki/tls/certs/ca-bundle.crt`
- macOS: Keychain Access, `/System/Library/Keychains/`
- Windows: Certificate Manager (certmgr.msc)

**Application Trust Stores**:
- Go: `x509.SystemCertPool()`, custom pool via `x509.CertPool.AppendCertsFromPEM()`
- Java: `cacerts` keystore, `keytool -import`
- Python: `certifi` package, `SSL_CERT_FILE` env var

**Adding Private CA to Trust Store (Linux)**:
```bash
# Copy root CA cert
sudo cp root-ca.crt /usr/local/share/ca-certificates/example-root-ca.crt

# Update trust store
sudo update-ca-certificates

# Verify
openssl s_client -connect api.example.com:443 -CAfile /etc/ssl/certs/ca-certificates.crt
```

---

## 8. Revocation Mechanisms: CRL, OCSP, OCSP Stapling

### CRL (Certificate Revocation List)

**Format**: X.509 CRL, signed by CA, contains list of revoked serial numbers + revocation dates

**Distribution**:
- HTTP(S) download from CRL Distribution Points (CDP) in certificate
- Updated periodically (every 24 hours to 7 days)

**Drawbacks**:
- **Scalability**: CRL grows with revocations, can reach MBs
- **Latency**: Client must download entire CRL before validation
- **Privacy**: CRL download reveals which certificates client is validating

**CRL Example**:
```bash
# Download CRL
wget http://crl.example.com/intermediate.crl

# Inspect CRL
openssl crl -in intermediate.crl -inform DER -text -noout

# Verify certificate against CRL
openssl verify -crl_check -CRLfile intermediate.crl -CAfile root-ca.crt server.crt
```

### OCSP (Online Certificate Status Protocol)

**Mechanism**: Client sends certificate serial number to OCSP responder, receives real-time status (good/revoked/unknown)

**Advantages**:
- Real-time revocation status
- Smaller response size (vs. CRL)

**Drawbacks**:
- **Privacy**: CA learns which certificates are being validated
- **Availability**: OCSP responder must be highly available (failure = validation fails or soft-fail risk)
- **Latency**: Adds round-trip to TLS handshake

**OCSP Request/Response**:
```bash
# Query OCSP
openssl ocsp \
  -issuer intermediate-ca.crt \
  -cert server.crt \
  -url http://ocsp.example.com \
  -CAfile root-ca.crt

# Response: good, revoked, or unknown
```

**OCSP Response Caching**: Clients cache OCSP responses (minutes to hours) to reduce load

### OCSP Stapling (TLS Certificate Status Request)

**Mechanism**: Server queries OCSP responder periodically, includes signed OCSP response in TLS handshake

**Advantages**:
- **Privacy**: Client doesn't contact OCSP responder
- **Performance**: No additional client round-trip
- **Reliability**: Server caches OCSP response, fallback if responder down

**Configuration (Nginx)**:
```nginx
ssl_stapling on;
ssl_stapling_verify on;
ssl_trusted_certificate /etc/ssl/certs/ca-chain.crt;
resolver 8.8.8.8 8.8.4.4 valid=300s;
```

**Verification**:
```bash
openssl s_client -connect api.example.com:443 -status
# Look for "OCSP Response" section
```

### Must-Staple Extension

**X509v3 TLS Feature: status_request** (RFC 7633):
- Certificate requires OCSP stapling
- If server doesn't staple, client rejects connection
- Prevents downgrade attacks (attacker blocks OCSP to hide revocation)

---

## 9. Automated Certificate Management (ACME, cert-manager)

### ACME Protocol (Automatic Certificate Management Environment)

**Overview**: RFC 8555, standardized by Let's Encrypt for automated domain-validated (DV) certificate issuance

**Flow**:
```
1. Client creates account with ACME server
2. Client requests certificate for domain(s)
3. ACME server issues challenge (HTTP-01, DNS-01, TLS-ALPN-01)
4. Client completes challenge (proves domain ownership)
5. ACME server validates challenge
6. Client submits CSR
7. ACME server issues certificate
```

**Challenge Types**:
- **HTTP-01**: Place file at `http://<domain>/.well-known/acme-challenge/<token>`
  - Requires port 80, doesn't work for wildcards
- **DNS-01**: Create TXT record `_acme-challenge.<domain>`
  - Works for wildcards, no port 80 required, needs DNS API
- **TLS-ALPN-01**: TLS handshake with special ALPN protocol
  - Port 443, no HTTP needed

**ACME Servers**:
- **Let's Encrypt**: Public CA, free DV certs, 90-day validity
- **Step-CA**: Private ACME server, supports custom policies
- **HashiCorp Vault**: PKI secrets engine with ACME support (Vault 1.13+)

### cert-manager (Kubernetes)

**Architecture**:
```
┌─────────────────────────────────────────────────────┐
│  Kubernetes API Server                              │
└────────┬────────────────────────────────────────────┘
         │ Watches
         ▼
┌─────────────────────────────────────────────────────┐
│  cert-manager Controller                            │
│  - Certificate CRD controller                       │
│  - Issuer/ClusterIssuer controller                  │
│  - CertificateRequest controller                    │
└────────┬────────────────────────────────────────────┘
         │ Issues CSR
         ▼
┌─────────────────────────────────────────────────────┐
│  ACME / Vault / Venafi Issuer                       │
│  - Completes challenge (HTTP-01, DNS-01)            │
│  - Submits CSR to CA                                │
└────────┬────────────────────────────────────────────┘
         │ Returns cert
         ▼
┌─────────────────────────────────────────────────────┐
│  Kubernetes Secret (TLS cert + key)                 │
│  - Auto-renewal at 2/3 lifetime                     │
│  - Referenced by Ingress, Pod, Service              │
└─────────────────────────────────────────────────────┘
```

**Installation**:
```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.0/cert-manager.yaml

# Verify
kubectl get pods -n cert-manager
```

**ClusterIssuer (Let's Encrypt)**:
```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: ops@example.com
    privateKeySecretRef:
      name: letsencrypt-prod-account-key
    solvers:
    - http01:
        ingress:
          class: nginx
```

**Certificate Resource**:
```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: api-tls
  namespace: default
spec:
  secretName: api-tls-secret
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - api.example.com
  - "*.api.example.com"
```

**Ingress Annotation (Auto-creation)**:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - api.example.com
    secretName: api-tls-secret
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 8080
```

---

## 10. Hardware Security Modules (HSMs) & Key Storage

### HSM Overview

**Purpose**: Tamper-resistant hardware for cryptographic key generation, storage, and operations

**FIPS 140-2 Levels**:
- **Level 1**: Software encryption, no physical security
- **Level 2**: Tamper-evident seals, role-based auth
- **Level 3**: Tamper-resistant enclosure, key zeroization on intrusion
- **Level 4**: Active tamper detection, environmental protections

**PKCS#11**: Standard API for HSM interaction (C library, wrapped by Go/Rust/Python)

### Cloud HSMs

**AWS CloudHSM**:
- FIPS 140-2 Level 3 validated
- Dedicated HSM cluster (not shared)
- PKCS#11, JCE, CNG APIs
- Use case: Root/intermediate CA key storage

**GCP Cloud HSM**:
- Managed via Cloud KMS
- FIPS 140-2 Level 3
- Automatic key replication across regions

**Azure Dedicated HSM**:
- Based on Thales Luna HSMs
- FIPS 140-2 Level 3
- Direct network access (VNet injection)

### Software HSMs (Development/Testing)

**SoftHSMv2**:
```bash
# Install
sudo apt install softhsm2

# Initialize token
softhsm2-util --init-token --slot 0 --label "test-ca" --so-pin 1234 --pin 5678

# List tokens
softhsm2-util --show-slots

# Use with OpenSSL (PKCS#11 engine)
openssl req -new -x509 -days 3650 -engine pkcs11 \
  -keyform engine -key "pkcs11:token=test-ca;object=ca-key;type=private" \
  -out root-ca.crt
```

### Key Ceremony (Root CA Key Generation)

**Operational Security**:
1. **Quorum**: M-of-N signers required (e.g., 3 of 5)
2. **Dual Control**: Two people required to access HSM
3. **Air-Gapped**: HSM not network-connected during key generation
4. **Audit**: Video recording, written logs, witness signatures
5. **Backup**: Encrypted key backup on tamper-evident media, stored in vault

**Steps**:
1. Initialize HSM in secure facility
2. Generate key pair in HSM
3. Export wrapped backup (encrypted with master key)
4. Generate self-signed root certificate
5. Store HSM in vault, distribute backup shares
6. Export root certificate to trust stores

---

## 11. Production CA Systems

### HashiCorp Vault PKI Secrets Engine

**Architecture**:
```
┌──────────────────────────────────────────────┐
│  Vault Server (HA, Raft/Consul backend)      │
│  ┌────────────────────────────────────────┐  │
│  │  PKI Secrets Engine (pki/)             │  │
│  │  - Root CA (offline, manual unsealing) │  │
│  │  - Intermediate CA (online, auto-seal) │  │
│  │  - Role-based cert issuance            │  │
│  │  - Automatic renewal, revocation       │  │
│  └────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
         │ API (HTTPS, mTLS)
         ▼
┌──────────────────────────────────────────────┐
│  Vault Agents (sidecar, init container)      │
│  - Fetch cert + renew before expiration      │
│  - Write to file or Kubernetes secret        │
└──────────────────────────────────────────────┘
```

**Setup**:
```bash
# Enable PKI engine (root CA)
vault secrets enable -path=pki pki
vault secrets tune -max-lease-ttl=87600h pki

# Generate root CA
vault write -field=certificate pki/root/generate/internal \
  common_name="Example Root CA" \
  ttl=87600h > root-ca.crt

# Configure CRL/OCSP URLs
vault write pki/config/urls \
  issuing_certificates="https://vault.example.com:8200/v1/pki/ca" \
  crl_distribution_points="https://vault.example.com:8200/v1/pki/crl"

# Enable intermediate CA
vault secrets enable -path=pki_int pki
vault secrets tune -max-lease-ttl=43800h pki_int

# Generate intermediate CSR
vault write -format=json pki_int/intermediate/generate/internal \
  common_name="Example Intermediate CA" \
  | jq -r '.data.csr' > pki_int.csr

# Sign intermediate CSR with root CA
vault write -format=json pki/root/sign-intermediate csr=@pki_int.csr \
  format=pem_bundle ttl=43800h \
  | jq -r '.data.certificate' > intermediate.cert.pem

# Set signed intermediate certificate
vault write pki_int/intermediate/set-signed certificate=@intermediate.cert.pem

# Create role for service certificates
vault write pki_int/roles/service-mesh \
  allowed_domains="svc.cluster.local" \
  allow_subdomains=true \
  max_ttl="720h" \
  key_type="ec" \
  key_bits=256
```

**Issue Certificate**:
```bash
# Request certificate
vault write pki_int/issue/service-mesh \
  common_name="api.svc.cluster.local" \
  ttl="24h"

# Output: certificate, private_key, ca_chain, serial_number
```

**Vault Agent Auto-Renewal**:
```hcl
# vault-agent.hcl
vault {
  address = "https://vault.example.com:8200"
}

auto_auth {
  method "kubernetes" {
    mount_path = "auth/kubernetes"
    config = {
      role = "service-mesh"
    }
  }
}

template {
  source      = "/etc/vault/cert.tpl"
  destination = "/etc/certs/tls.crt"
  command     = "systemctl reload nginx"
}

template {
  source      = "/etc/vault/key.tpl"
  destination = "/etc/certs/tls.key"
  perms       = "0600"
}
```

### CFSSL (Cloudflare PKI Toolkit)

**Components**:
- `cfssl`: CLI for cert generation, signing
- `cfssljson`: JSON output parsing
- `multirootca`: Multi-tenant CA server

**Generate Root CA**:
```bash
# CA config
cat > ca-config.json <<EOF
{
  "signing": {
    "default": {
      "expiry": "8760h"
    },
    "profiles": {
      "server": {
        "usages": ["signing", "key encipherment", "server auth"],
        "expiry": "8760h"
      },
      "client": {
        "usages": ["signing", "key encipherment", "client auth"],
        "expiry": "8760h"
      }
    }
  }
}
EOF

# Root CA CSR
cat > ca-csr.json <<EOF
{
  "CN": "Example Root CA",
  "key": {
    "algo": "ecdsa",
    "size": 256
  },
  "names": [
    {
      "C": "US",
      "ST": "California",
      "L": "San Francisco",
      "O": "Example Corp"
    }
  ]
}
EOF

# Generate root CA
cfssl gencert -initca ca-csr.json | cfssljson -bare ca

# Issue server cert
cat > server-csr.json <<EOF
{
  "CN": "api.example.com",
  "hosts": ["api.example.com", "*.api.example.com"],
  "key": {
    "algo": "ecdsa",
    "size": 256
  }
}
EOF

cfssl gencert -ca=ca.pem -ca-key=ca-key.pem \
  -config=ca-config.json -profile=server \
  server-csr.json | cfssljson -bare server
```

### Step-CA (Smallstep)

**Features**:
- ACME server for private PKI
- Short-lived certificates (default 24h)
- JWK/OIDC provisioners
- SSH certificate support

**Installation**:
```bash
# Install step CLI + step-ca
wget https://dl.step.sm/gh-release/cli/docs-ca-install/v0.25.0/step_linux_0.25.0_amd64.tar.gz
tar xf step_linux_0.25.0_amd64.tar.gz
sudo cp step_0.25.0/bin/step /usr/local/bin/

# Initialize CA
step ca init --name="Example CA" --dns="ca.example.com" --address=":443"

# Start CA
step-ca $(step path)/config/ca.json
```

**ACME Provisioner**:
```bash
# Add ACME provisioner
step ca provisioner add acme --type ACME

# Use with cert-manager
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: step-ca-acme
spec:
  acme:
    server: https://ca.example.com/acme/acme/directory
    skipTLSVerify: true
    privateKeySecretRef:
      name: step-ca-acme-account-key
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

### AWS Private CA

**Managed CA Service**:
```bash
# Create root CA
aws acm-pca create-certificate-authority \
  --certificate-authority-type ROOT \
  --certificate-authority-configuration \
    "KeyAlgorithm=RSA_2048,SigningAlgorithm=SHA256WITHRSA,Subject={Country=US,Organization=Example,CommonName=Example Root CA}"

# Get ARN
CA_ARN=$(aws acm-pca list-certificate-authorities --query 'CertificateAuthorities[0].Arn' --output text)

# Issue root certificate
aws acm-pca get-certificate-authority-csr --certificate-authority-arn $CA_ARN --output text > root-ca.csr

aws acm-pca issue-certificate \
  --certificate-authority-arn $CA_ARN \
  --csr fileb://root-ca.csr \
  --signing-algorithm SHA256WITHRSA \
  --template-arn arn:aws:acm-pca:::template/RootCACertificate/V1 \
  --validity Value=10,Type=YEARS

# Import root certificate
CERT_ARN=$(aws acm-pca issue-certificate --certificate-authority-arn $CA_ARN --csr fileb://root-ca.csr --signing-algorithm SHA256WITHRSA --template-arn arn:aws:acm-pca:::template/RootCACertificate/V1 --validity Value=10,Type=YEARS --query CertificateArn --output text)

aws acm-pca get-certificate --certificate-arn $CERT_ARN --certificate-authority-arn $CA_ARN --output text > root-ca.crt

aws acm-pca import-certificate-authority-certificate \
  --certificate-authority-arn $CA_ARN \
  --certificate fileb://root-ca.crt
```

---

## 12. mTLS, Service Mesh, SPIFFE/SPIRE

### Mutual TLS (mTLS)

**Definition**: Both client and server authenticate via X.509 certificates (vs. server-only auth in standard TLS)

**Use Cases**:
- Service-to-service authentication (zero-trust networks)
- API gateway to backend services
- Database client authentication
- IoT device authentication

**TLS Handshake (mTLS)**:
```
Client                                Server
  |                                     |
  |--- ClientHello ------------------>  |
  |<-- ServerHello, Certificate, ----- |
  |    CertificateRequest               |
  |--- Certificate, ClientKeyExchange, |
  |    CertificateVerify ------------> |
  |<-- Finished ----------------------- |
  |--- Finished ----------------------> |
  |                                     |
  |===== Encrypted Application Data ===|
```

**Go mTLS Server**:
```go
package main

import (
    "crypto/tls"
    "crypto/x509"
    "io/ioutil"
    "log"
    "net/http"
)

func main() {
    // Load CA cert (for client verification)
    caCert, _ := ioutil.ReadFile("ca.crt")
    caCertPool := x509.NewCertPool()
    caCertPool.AppendCertsFromPEM(caCert)

    // TLS config
    tlsConfig := &tls.Config{
        ClientCAs:  caCertPool,
        ClientAuth: tls.RequireAndVerifyClientCert,
        MinVersion: tls.VersionTLS13,
        CipherSuites: []uint16{
            tls.TLS_AES_128_GCM_SHA256,
            tls.TLS_AES_256_GCM_SHA384,
            tls.TLS_CHACHA20_POLY1305_SHA256,
        },
    }

    server := &http.Server{
        Addr:      ":8443",
        TLSConfig: tlsConfig,
    }

    http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        if r.TLS != nil && len(r.TLS.PeerCertificates) > 0 {
            clientCert := r.TLS.PeerCertificates[0]
            log.Printf("Client CN: %s", clientCert.Subject.CommonName)
        }
        w.Write([]byte("mTLS OK\n"))
    })

    log.Fatal(server.ListenAndServeTLS("server.crt", "server.key"))
}
```

**Go mTLS Client**:
```go
package main

import (
    "crypto/tls"
    "crypto/x509"
    "io/ioutil"
    "log"
    "net/http"
)

func main() {
    // Load client cert
    cert, _ := tls.LoadX509KeyPair("client.crt", "client.key")

    // Load CA cert (for server verification)
    caCert, _ := ioutil.ReadFile("ca.crt")
    caCertPool := x509.NewCertPool()
    caCertPool.AppendCertsFromPEM(caCert)

    // TLS config
    tlsConfig := &tls.Config{
        Certificates: []tls.Certificate{cert},
        RootCAs:      caCertPool,
        MinVersion:   tls.VersionTLS13,
    }

    client := &http.Client{
        Transport: &http.Transport{
            TLSClientConfig: tlsConfig,
        },
    }

    resp, err := client.Get("https://api.example.com:8443")
    if err != nil {
        log.Fatal(err)
    }
    defer resp.Body.Close()

    body, _ := ioutil.ReadAll(resp.Body)
    log.Printf("Response: %s", body)
}
```

### Service Mesh (Istio, Linkerd, Consul)

**Architecture**:
```
┌──────────────────────────────────────────────────┐
│  Control Plane                                   │
│  - Certificate Authority (Istiod, Linkerd)       │
│  - Policy enforcement                            │
│  - Telemetry aggregation                         │
└────────┬─────────────────────────────────────────┘
         │ Issues certs (SPIFFE SVIDs)
         ▼
┌──────────────────────────────────────────────────┐
│  Data Plane (Envoy/Linkerd2-proxy sidecars)      │
│  ┌────────────┐       ┌────────────┐            │
│  │  App Pod   │       │  App Pod   │            │
│  │ ┌────────┐ │       │ ┌────────┐ │            │
│  │ │App Cont│ │       │ │App Cont│ │            │
│  │ └────────┘ │       │ └────────┘ │            │
│  │ ┌────────┐ │       │ ┌────────┐ │            │
│  │ │ Sidecar│ │<----->│ │ Sidecar│ │ mTLS       │
│  │ │ (Envoy)│ │       │ │ (Envoy)│ │            │
│  │ └────────┘ │       │ └────────┘ │            │
│  └────────────┘       └────────────┘            │
└──────────────────────────────────────────────────┘
```

**Istio Certificate Rotation**:
- Short-lived certs (default 24h)
- Automatic rotation at 75% lifetime
- Workload identity via SPIFFE SVID (URI SAN: `spiffe://cluster.local/ns/default/sa/api`)

**Istio PeerAuthentication (Enforce mTLS)**:
```yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: istio-system
spec:
  mtls:
    mode: STRICT
```

### SPIFFE/SPIRE

**SPIFFE (Secure Production Identity Framework for Everyone)**:
- Standard for workload identity (SPIFFE ID: `spiffe://trust-domain/path`)
- SVID (SPIFFE Verifiable Identity Document): X.509 cert or JWT with SPIFFE ID in SAN

**SPIRE (SPIFFE Runtime Environment)**:
- Reference implementation of SPIFFE
- Issues short-lived SVIDs to workloads (1h default)
- Node attestation (AWS IAM, GCP GCE, Kubernetes SAT)
- Workload attestation (k8s namespace/SA, Unix user/group)

**Architecture**:
```
┌─────────────────────────────────────────┐
│  SPIRE Server (Control Plane)           │
│  - Root CA (self-signed or external)    │
│  - Node attestation plugins             │
│  - Registration API                     │
└────────┬────────────────────────────────┘
         │ Attests nodes, issues SVIDs
         ▼
┌─────────────────────────────────────────┐
│  SPIRE Agent (per node)                 │
│  - Unix domain socket: /run/spire/sockets/agent.sock │
│  - Workload attestation                 │
│  - SVID caching, rotation               │
└────────┬────────────────────────────────┘
         │ Workload API (gRPC)
         ▼
┌─────────────────────────────────────────┐
│  Workload (fetches SVID via Workload API) │
│  - X.509-SVID: cert + private key + bundle │
│  - JWT-SVID: signed JWT token            │
└─────────────────────────────────────────┘
```

**SPIRE Server Config** (`server.conf`):
```hcl
server {
  bind_address = "0.0.0.0"
  bind_port = "8081"
  trust_domain = "example.com"
  data_dir = "/var/lib/spire/server"
}

plugins {
  DataStore "sql" {
    plugin_data {
      database_type = "sqlite3"
      connection_string = "/var/lib/spire/server/datastore.sqlite3"
    }
  }

  NodeAttestor "k8s_psat" {
    plugin_data {
      clusters = {
        "prod-cluster" = {
          service_account_allow_list = ["spire:spire-agent"]
        }
      }
    }
  }

  KeyManager "disk" {
    plugin_data {
      keys_path = "/var/lib/spire/server/keys.json"
    }
  }
}
```

**Workload Registration**:
```bash
# Register workload (API service)
spire-server entry create \
  -spiffeID spiffe://example.com/api \
  -parentID spiffe://example.com/k8s-node \
  -selector k8s:ns:default \
  -selector k8s:sa:api-service

# List entries
spire-server entry show
```

**Fetch SVID (Workload)**:
```go
package main

import (
    "context"
    "log"

    "github.com/spiffe/go-spiffe/v2/workloadapi"
)

func main() {
    ctx := context.Background()

    // Fetch X.509 SVID
    source, err := workloadapi.NewX509Source(ctx)
    if err != nil {
        log.Fatalf("Unable to create X509Source: %v", err)
    }
    defer source.Close()

    svid, err := source.GetX509SVID()
    if err != nil {
        log.Fatalf("Unable to get SVID: %v", err)
    }

    log.Printf("SPIFFE ID: %s", svid.ID)
    log.Printf("Certificate expires: %s", svid.Certificates[0].NotAfter)
}
```

---

## 13. Threat Model & Attack Surface

### Attack Vectors

**CA Compromise**:
- **Root CA private key stolen**: Attacker can issue arbitrary certs, impersonate any service
  - Mitigation: Offline root, HSM, multi-party control, key ceremony
- **Intermediate CA compromise**: Attacker issues rogue certs within CA hierarchy
  - Mitigation: Revoke intermediate CA, re-issue from new intermediate, CT logs detect rogue certs
- **Certificate Transparency (CT) logs**: Public append-only logs of all issued certs (detect mis-issuance)

**Private Key Theft (Leaf Cert)**:
- **Workload compromise**: Attacker extracts private key from filesystem/memory
  - Mitigation: Short-lived certs (limit exposure window), revocation, HSM/TPM for key storage
- **Side-channel attacks**: Timing, cache, speculative execution (e.g., Spectre)
  - Mitigation: Constant-time crypto, isolated execution (SGX, SEV)

**Man-in-the-Middle (MitM)**:
- **Rogue CA in trust store**: User tricked into installing attacker CA cert
  - Mitigation: Certificate pinning, HPKP (deprecated), expect-CT header
- **DNS spoofing**: Redirect to attacker server with valid cert for wrong domain
  - Mitigation: DNSSEC, strict hostname validation

**Revocation Bypass**:
- **CRL/OCSP unavailable**: Client performs soft-fail (accepts cert despite revocation check failure)
  - Mitigation: Must-staple, fail-closed policy
- **OCSP replay**: Attacker serves old "good" OCSP response for revoked cert
  - Mitigation: OCSP response nonce, short OCSP validity

**Certificate Validation Bugs**:
- **Hostname mismatch**: Accept cert for `attacker.com` when connecting to `example.com`
  - Mitigation: Strict SAN validation, avoid wildcard trust
- **Chain building errors**: Accept partial chain without validating to root
  - Mitigation: Enforce chain validation, reject incomplete chains

### Defense in Depth

**Layers**:
1. **Root CA Isolation**: Offline, air-gapped, HSM, ceremony
2. **Intermediate CA Hardening**: Online HSM/KMS, rate limiting, access control
3. **Short-Lived Certificates**: 1h-24h for workloads, reduce revocation reliance
4. **Certificate Transparency**: Detect rogue issuance via CT logs (crt.sh, Facebook CT monitor)
5. **OCSP Stapling + Must-Staple**: Prevent revocation bypass
6. **Network Segmentation**: Isolate CA infrastructure, no internet egress
7. **Audit Logging**: All CA operations logged to SIEM (Splunk, ELK, CloudWatch)
8. **Incident Response**: Revocation runbook, re-keying playbook, communication plan

---

## 14. Monitoring, Auditing, Compliance

### Metrics to Monitor

**Certificate Inventory**:
- Total certs issued (by CA, by role)
- Cert expiration distribution (days to expiry)
- Renewal rate (certs/day)
- Revocation rate

**CA Health**:
- API latency (p50, p95, p99)
- Error rate (failed CSRs, validation errors)
- OCSP responder uptime, response time
- CRL size, update frequency

**Security Events**:
- Failed cert validations (hostname mismatch, expired, revoked)
- Anomalous issuance patterns (rate spike, unusual SANs)
- Root/intermediate CA key usage events

### Audit Logging

**Log Events**:
- Cert issuance: timestamp, requester, subject, SAN, serial, CA
- Cert revocation: timestamp, reason, serial
- CA config changes: policy updates, role creation
- Key generation/rotation: key type, algorithm, key ID

**Log Aggregation**:
- Centralize logs to SIEM (Splunk, Datadog, ELK)
- Correlation with other security events (auth failures, network anomalies)
- Alerting on suspicious patterns (unusual issuer, rapid revocations)

**Example (Vault Audit Log)**:
```json
{
  "time": "2026-02-06T10:15:30Z",
  "type": "response",
  "auth": {
    "client_token": "hmac-sha256:...",
    "accessor": "hmac-sha256:...",
    "policies": ["service-mesh-policy"]
  },
  "request": {
    "operation": "write",
    "path": "pki_int/issue/service-mesh"
  },
  "response": {
    "data": {
      "certificate": "-----BEGIN CERTIFICATE-----...",
      "serial_number": "39:dd:2e:..."
    }
  }
}
```

### Compliance & Standards

**Frameworks**:
- **SOC 2 Type II**: Audit CA operations, access controls, change management
- **PCI-DSS**: Key management, certificate lifecycle for payment systems
- **HIPAA**: Encryption at rest/in transit, audit logging for healthcare
- **FedRAMP**: FIPS 140-2 validated HSMs, continuous monitoring

**CA/Browser Forum Baseline Requirements**:
- Max 398 days for DV/OV certs
- CT logging mandatory for publicly-trusted certs
- OCSP/CRL required

**Internal Policies**:
- Cert lifetime: 90 days for workloads, 1 year for user certs
- Key algorithm: ECDSA P-256 minimum, RSA 3072+
- Revocation SLA: 1 hour from compromise detection to revocation
- Root CA access: Multi-party approval, logged ceremony

---

## 15. Deployment Architectures & Failure Modes

### High Availability (HA) CA

**Architecture**:
```
┌──────────────────────────────────────────────────┐
│  Load Balancer (TLS termination)                 │
└────────┬─────────────────────────────────────────┘
         │ Distributes CSRs
         ▼
┌──────────────────────────────────────────────────┐
│  CA Cluster (Active-Active)                      │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐          │
│  │ CA Node │  │ CA Node │  │ CA Node │          │
│  │   #1    │  │   #2    │  │   #3    │          │
│  └────┬────┘  └────┬────┘  └────┬────┘          │
│       └───────────┬─────────────┘               │
│                   │ Shared HSM/KMS              │
│                   ▼                             │
│         ┌───────────────────┐                   │
│         │  HSM Cluster      │                   │
│         │  (replicated keys)│                   │
│         └───────────────────┘                   │
└──────────────────────────────────────────────────┘
         │ Persist certs/CRL
         ▼
┌──────────────────────────────────────────────────┐
│  Database (PostgreSQL, etcd, Raft)               │
│  - Certificate metadata (serial, expiry, status) │
│  - CRL, OCSP cache                               │
│  - Replication across AZs                        │
└──────────────────────────────────────────────────┘
```

**Failure Modes**:
- **HSM failure**: Backup HSM takes over, KMS auto-replicates
- **CA node failure**: LB routes to healthy nodes, stateless design
- **DB failure**: Failover to replica, RTO < 5 min
- **Network partition**: Split-brain prevention via quorum (Raft, Paxos)

### Multi-Region/Multi-Cloud

**Strategy**:
- **Regional Intermediate CAs**: Each region has own intermediate CA (reduces latency, blast radius)
- **Global Root CA**: Single offline root, signs regional intermediates
- **Cross-Region CRL/OCSP**: Replicate revocation data via CDN (CloudFront, Fastly)

**Disaster Recovery**:
- **Root CA key backup**: Encrypted, stored in geographically distributed vaults
- **Runbook**: Steps to restore intermediate CA from backup, re-sign from root
- **RTO/RPO**: RTO 1 hour (intermediate CA restore), RPO 0 (synchronous DB replication)

### Zero-Downtime Rotation

**Intermediate CA Rotation**:
```
1. Generate new intermediate CA key pair
2. Submit CSR to root CA, obtain new intermediate cert
3. Configure CA to issue from both old and new intermediate (dual-issuer)
4. Gradually shift issuance to new intermediate (canary rollout)
5. Wait for old certs to expire (or force re-issuance)
6. Revoke old intermediate CA, remove from trust bundles
```

**Leaf Cert Rotation**:
- **Overlapping validity**: Issue new cert before old expires (overlap period)
- **Blue-Green**: Deploy new cert to 50% of instances, validate, deploy to rest
- **Automated**: cert-manager, Vault agent handle renewal automatically

---

## 16. Hands-On Labs & Configuration Examples

### Lab 1: Build Private PKI with OpenSSL

**Generate Root CA**:
```bash
# Root CA config
cat > root-ca.conf <<EOF
[ req ]
default_bits        = 4096
default_md          = sha256
prompt              = no
encrypt_key         = no
distinguished_name  = dn
x509_extensions     = v3_ca

[ dn ]
CN = Example Root CA
O  = Example Corp
C  = US

[ v3_ca ]
basicConstraints     = critical,CA:TRUE
keyUsage             = critical,keyCertSign,cRLSign
subjectKeyIdentifier = hash
EOF

# Generate root CA
openssl req -new -x509 -days 7300 -config root-ca.conf \
  -keyout root-ca.key -out root-ca.crt

# Verify
openssl x509 -in root-ca.crt -noout -text
```

**Generate Intermediate CA**:
```bash
# Intermediate CA config
cat > intermediate-ca.conf <<EOF
[ req ]
default_bits        = 2048
default_md          = sha256
prompt              = no
encrypt_key         = no
distinguished_name  = dn
req_extensions      = v3_req

[ dn ]
CN = Example Intermediate CA
O  = Example Corp
C  = US

[ v3_req ]
basicConstraints = critical,CA:TRUE,pathlen:0
keyUsage         = critical,keyCertSign,cRLSign
EOF

# Generate intermediate CSR
openssl req -new -config intermediate-ca.conf \
  -keyout intermediate-ca.key -out intermediate-ca.csr

# Sign intermediate CSR with root CA
cat > sign-intermediate.conf <<EOF
[ v3_intermediate_ca ]
basicConstraints     = critical,CA:TRUE,pathlen:0
keyUsage             = critical,keyCertSign,cRLSign
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always
crlDistributionPoints = URI:http://crl.example.com/root.crl
authorityInfoAccess   = OCSP;URI:http://ocsp.example.com
EOF

openssl x509 -req -in intermediate-ca.csr -CA root-ca.crt -CAkey root-ca.key \
  -CAcreateserial -out intermediate-ca.crt -days 3650 \
  -extfile sign-intermediate.conf -extensions v3_intermediate_ca

# Create cert chain
cat intermediate-ca.crt root-ca.crt > ca-chain.crt
```

**Issue Leaf Certificate**:
```bash
# Server cert config
cat > server.conf <<EOF
[ req ]
default_bits       = 2048
default_md         = sha256
prompt             = no
encrypt_key        = no
distinguished_name = dn
req_extensions     = v3_req

[ dn ]
CN = api.example.com
O  = Example Corp

[ v3_req ]
basicConstraints = CA:FALSE
keyUsage         = digitalSignature,keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName   = @alt_names

[ alt_names ]
DNS.1 = api.example.com
DNS.2 = *.api.example.com
IP.1  = 10.0.1.100
EOF

# Generate server CSR
openssl req -new -config server.conf -keyout server.key -out server.csr

# Sign server CSR with intermediate CA
cat > sign-server.conf <<EOF
[ v3_server ]
basicConstraints       = CA:FALSE
keyUsage               = digitalSignature,keyEncipherment
extendedKeyUsage       = serverAuth
subjectKeyIdentifier   = hash
authorityKeyIdentifier = keyid:always
crlDistributionPoints  = URI:http://crl.example.com/intermediate.crl
authorityInfoAccess    = OCSP;URI:http://ocsp.example.com
EOF

openssl x509 -req -in server.csr -CA intermediate-ca.crt -CAkey intermediate-ca.key \
  -CAcreateserial -out server.crt -days 90 \
  -extfile sign-server.conf -extensions v3_server

# Verify chain
openssl verify -CAfile ca-chain.crt server.crt
```

### Lab 2: Deploy Vault PKI in Kubernetes

**Install Vault**:
```bash
# Add Helm repo
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

# Install Vault
kubectl create namespace vault
helm install vault hashicorp/vault --namespace vault \
  --set server.ha.enabled=true \
  --set server.ha.raft.enabled=true

# Initialize and unseal
kubectl exec -n vault vault-0 -- vault operator init -key-shares=5 -key-threshold=3
kubectl exec -n vault vault-0 -- vault operator unseal <key-1>
kubectl exec -n vault vault-0 -- vault operator unseal <key-2>
kubectl exec -n vault vault-0 -- vault operator unseal <key-3>
```

**Configure PKI** (see section 11 for full setup)

**Integrate with cert-manager**:
```yaml
apiVersion: cert-manager.io/v1
kind: Issuer
metadata:
  name: vault-issuer
  namespace: default
spec:
  vault:
    server: https://vault.vault.svc.cluster.local:8200
    path: pki_int/sign/service-mesh
    caBundle: LS0tLS1...  # Base64-encoded CA bundle
    auth:
      kubernetes:
        role: cert-manager
        mountPath: /v1/auth/kubernetes
        secretRef:
          name: cert-manager-vault-token
          key: token
---
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: api-cert
  namespace: default
spec:
  secretName: api-tls
  issuerRef:
    name: vault-issuer
    kind: Issuer
  commonName: api.default.svc.cluster.local
  dnsNames:
  - api.default.svc.cluster.local
  duration: 24h
  renewBefore: 8h
```

### Lab 3: SPIRE in Kubernetes

**Install SPIRE**:
```bash
# Apply SPIRE server manifests
kubectl apply -f https://raw.githubusercontent.com/spiffe/spire-tutorials/main/k8s/quickstart/spire-server.yaml

# Apply SPIRE agent (DaemonSet)
kubectl apply -f https://raw.githubusercontent.com/spiffe/spire-tutorials/main/k8s/quickstart/spire-agent.yaml

# Verify
kubectl get pods -n spire
```

**Register Workload**:
```bash
# Exec into server
kubectl exec -n spire spire-server-0 -c spire-server -- \
  /opt/spire/bin/spire-server entry create \
    -spiffeID spiffe://example.com/frontend \
    -parentID spiffe://example.com/node \
    -selector k8s:ns:default \
    -selector k8s:sa:frontend
```

**Fetch SVID from Workload**:
```go
// See section 12 for Go code example
```

---

## 17. Threat Model Deep Dive

### Attack Scenarios

**Scenario 1: Intermediate CA Key Compromise**

**Attack Path**:
1. Attacker exploits RCE vulnerability in CA API server
2. Escalates privileges, dumps intermediate CA key from HSM backup or memory
3. Issues rogue certificates for `*.example.com`
4. MitM attacks on internal services

**Detection**:
- Certificate Transparency logs show unexpected issuance
- Monitoring alerts on unusual cert issuance rate
- Anomaly detection on SANs (e.g., wildcard certs not normally issued)

**Mitigation**:
- **Immediate**: Revoke intermediate CA cert, publish updated CRL/OCSP
- **Short-term**: Re-issue all active certs from new intermediate CA
- **Long-term**: Root cause analysis, patch vulnerability, improve HSM isolation

**Blast Radius**: All certs issued by compromised intermediate (potentially thousands)

**Recovery Time**: 2-4 hours (revoke intermediate, deploy new intermediate, force rotation)

---

**Scenario 2: OCSP Responder DDoS**

**Attack Path**:
1. Attacker floods OCSP responder with requests (amplification via botnet)
2. OCSP responder becomes unavailable
3. Clients fail to validate revocation status
4. If soft-fail policy, clients accept revoked certs

**Detection**:
- OCSP responder CPU/bandwidth saturation
- Spike in OCSP queries from anomalous IPs

**Mitigation**:
- **Immediate**: Rate limiting at CDN/LB (Cloudflare, AWS WAF)
- **Short-term**: Scale OCSP responders horizontally, deploy anycast
- **Long-term**: Enable OCSP stapling (shift load to servers), implement must-staple

**Blast Radius**: Clients using soft-fail may accept revoked certs during outage

**Recovery Time**: Minutes (scale responders, enable rate limiting)

---

**Scenario 3: Certificate Validation Bug (Hostname Mismatch)**

**Attack Path**:
1. Bug in TLS library allows hostname mismatch (accepts `attacker.com` cert for `example.com`)
2. Attacker obtains valid cert for `attacker.com`
3. Performs MitM, presents `attacker.com` cert to victim connecting to `example.com`
4. Vulnerable client accepts cert, establishes TLS to attacker

**Detection**:
- Security research, CVE disclosure, vendor advisory
- User reports of unexpected cert warnings

**Mitigation**:
- **Immediate**: Patch TLS library (OpenSSL, BoringSSL, rustls)
- **Short-term**: Enforce certificate pinning for critical services
- **Long-term**: Fuzzing, formal verification of TLS stack

**Blast Radius**: All clients using vulnerable TLS library

**Recovery Time**: Hours to days (deploy patches across fleet)

---

## Next 3 Steps

1. **Deploy Private CA (Vault PKI or Step-CA)**
   - Stand up root CA (offline HSM or cloud KMS-backed)
   - Configure intermediate CA with automated issuance (API, ACME)
   - Integrate with cert-manager for Kubernetes workloads
   - **Goal**: Issue short-lived certs (24h) for all services, enable mTLS in service mesh

2. **Implement Certificate Transparency Monitoring**
   - Subscribe to CT log feeds (crt.sh, Facebook CT API)
   - Alert on unexpected issuance (unusual domains, wildcard certs, public CAs)
   - **Goal**: Detect rogue cert issuance within 1 hour

3. **Build Automated Revocation & Rotation Pipeline**
   - Create runbook for intermediate CA compromise (revoke, re-issue, deploy)
   - Automate cert rotation (Vault agent, cert-manager renewal)
   - Test failover: Simulate HSM failure, intermediate CA revocation, OCSP outage
   - **Goal**: RTO < 1 hour for intermediate CA compromise, zero-downtime rotation

---

## References

### RFCs & Standards
- **RFC 5280**: X.509 v3 Certificate and CRL Profile
- **RFC 6960**: OCSP (Online Certificate Status Protocol)
- **RFC 8555**: ACME (Automatic Certificate Management Environment)
- **RFC 6962**: Certificate Transparency
- **RFC 7633**: OCSP Must-Staple Extension

### Tools & Projects
- **OpenSSL**: https://www.openssl.org/docs/
- **HashiCorp Vault PKI**: https://developer.hashicorp.com/vault/docs/secrets/pki
- **cert-manager**: https://cert-manager.io/docs/
- **CFSSL**: https://github.com/cloudflare/cfssl
- **Step-CA**: https://smallstep.com/docs/step-ca/
- **SPIRE**: https://spiffe.io/docs/latest/spire-about/
- **Istio mTLS**: https://istio.io/latest/docs/tasks/security/authentication/mtls/

### Books & Papers
- **Bulletproof SSL and TLS** (Ivan Ristić)
- **PKI Uncovered** (Andre Karamanian)
- **TLS 1.3 RFC 8446** (formal spec)

### Compliance & Standards Bodies
- **CA/Browser Forum**: https://cabforum.org/baseline-requirements-documents/
- **NIST SP 800-57**: Key Management Recommendations
- **FIPS 140-2**: Cryptographic Module Validation

---

This guide provides end-to-end coverage of Certificate Authority concepts, from cryptographic primitives to production deployment. Each section includes architectural diagrams, security considerations, code examples, and operational best practices. For production systems, prioritize short-lived certificates, offline root CAs, HSM-backed keys, comprehensive monitoring, and automated rotation to minimize attack surface and operational overhead.