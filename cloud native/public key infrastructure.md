# Public Key Infrastructure (PKI) – Comprehensive Systems-Level Guide

**Summary**: PKI is the cryptographic framework enabling trusted digital identities, secure communication, and authentication at internet scale. It relies on asymmetric cryptography (public/private key pairs), certificate authorities (CAs) forming trust hierarchies, X.509 certificate standards, and validation protocols (OCSP, CRL). In production, PKI underpins TLS/mTLS, code signing, SSH, VPN, container image trust, K8s admission control, service mesh identity, and hardware root-of-trust (TPM, HSM). Core security properties: confidentiality via encryption, integrity via signatures, authenticity via certificate chains, non-repudiation via private key control. Modern challenges: certificate lifecycle automation (cert-manager, ACME), short-lived certs, zero-trust identity (SPIFFE/SPIRE), post-quantum migration, and HSM-backed CA operations.

---

## 1. Core Cryptographic Primitives

### 1.1 Asymmetric Cryptography Foundation

**Key Pair Generation**:
- **RSA** (2048/4096-bit): Based on integer factorization hardness. Slower, larger keys/sigs.
- **ECDSA/EdDSA** (P-256, P-384, Ed25519): Elliptic curve discrete log. Faster, smaller (256-bit ≈ 3072-bit RSA security).
- **Post-Quantum** (Dilithium, Kyber): Lattice-based algorithms for quantum resistance (NIST standardization ongoing).

**Operations**:
```
Private Key (d): Secret, never leaves secure boundary (HSM/TPM/enclave).
Public Key (Q): Derived from d, embedded in certificates, distributed freely.

Sign: signature = Sign(d, hash(message))
Verify: Valid = Verify(Q, hash(message), signature)

Encrypt (RSA): ciphertext = Encrypt(Q, plaintext)  // Hybrid: RSA wraps AES key
Decrypt: plaintext = Decrypt(d, ciphertext)
```

**Key Security**:
- Private keys stored in HSM (FIPS 140-2 L3+), TPM 2.0, AWS KMS, GCP Cloud KMS, Azure Key Vault.
- Key extraction impossible from HSM; operations performed inside secure boundary.
- Key ceremony for root CA: air-gapped, multi-party, physical security, entropy sources.

---

## 2. X.509 Certificate Structure

### 2.1 Certificate Anatomy

```
Certificate ::= SEQUENCE {
  tbsCertificate       TBSCertificate,   // To-Be-Signed portion
  signatureAlgorithm   AlgorithmIdentifier,
  signatureValue       BIT STRING        // CA's signature over tbsCertificate
}

TBSCertificate ::= SEQUENCE {
  version              [0] EXPLICIT Version DEFAULT v1,
  serialNumber         CertificateSerialNumber,  // Unique per CA
  signature            AlgorithmIdentifier,
  issuer               Name,                    // CA's DN
  validity             Validity,                // notBefore, notAfter
  subject              Name,                    // Entity's DN (can be empty for SAN-only)
  subjectPublicKeyInfo SubjectPublicKeyInfo,
  extensions           [3] EXPLICIT Extensions OPTIONAL
}
```

**Critical Fields**:
- **Serial Number**: Unique per CA, used for revocation (CRL/OCSP).
- **Subject**: Distinguished Name (CN, O, OU, C, ST, L) – legacy, SAN preferred.
- **SubjectPublicKeyInfo**: Algorithm + public key bytes (RSA modulus/exponent, EC point).
- **Validity**: Unix timestamps. Short-lived certs (1-90 days) reduce revocation burden.

### 2.2 X.509v3 Extensions (Critical Production Extensions)

**Key Usage** (critical):
```
digitalSignature   : TLS client auth, code signing
keyEncipherment    : RSA key transport (TLS <1.3)
keyAgreement       : ECDHE key agreement
keyCertSign        : CA certificates only
cRLSign            : CRL signing authority
```

**Extended Key Usage** (critical for TLS):
```
serverAuth         : TLS server certificate
clientAuth         : mTLS client certificate
codeSigning        : Container images, binaries
emailProtection    : S/MIME
timeStamping       : RFC 3161 timestamps
```

**Subject Alternative Name (SAN)** (critical):
```
DNS:             example.com, *.example.com
IP:              192.0.2.1, 2001:db8::1
URI:             spiffe://cluster.local/ns/default/sa/workload
Email:           user@example.com
```
Modern best practice: Empty subject, identity in SAN only (SPIFFE pattern).

**Authority Key Identifier / Subject Key Identifier**:
- Links certificates to issuing CA (enables chain building).
- SHA-1 hash of CA's public key.

**CRL Distribution Points / Authority Information Access**:
```
CRL:  http://crl.example.com/ca.crl
OCSP: http://ocsp.example.com
CA Issuers: http://certs.example.com/issuing-ca.crt
```

**Basic Constraints** (critical for CAs):
```
CA: TRUE
pathLenConstraint: 0   // No subordinate CAs allowed (for intermediate)
```

**Certificate Policies / Policy Mappings**:
- OIDs defining certificate usage policies (e.g., EV SSL OID 2.23.140.1.1).
- Policy constraints enforce acceptable trust anchors.

---

## 3. PKI Hierarchy and Trust Model

### 3.1 CA Hierarchy

```
┌─────────────────────────────────────────┐
│  Root CA (offline, air-gapped)          │
│  - 20-year validity                     │
│  - HSM-backed (FIPS 140-2 L3+)          │
│  - Self-signed                          │
│  - Distributed in OS/browser trust store│
└──────────────┬──────────────────────────┘
               │ signs
               ▼
┌─────────────────────────────────────────┐
│  Intermediate CA (online, HSM)          │
│  - 10-year validity                     │
│  - Issues end-entity certs              │
│  - OCSP responder online                │
└──────────────┬──────────────────────────┘
               │ signs
               ▼
┌─────────────────────────────────────────┐
│  End-Entity Certificate                 │
│  - 90-day validity (Let's Encrypt)      │
│  - TLS server, client, code signing     │
│  - No CA=TRUE (cannot issue certs)      │
└─────────────────────────────────────────┘
```

**Why Intermediates?**
- **Root isolation**: Root CA offline, protected from network attacks.
- **Key compromise recovery**: Revoke intermediate, root remains trusted.
- **Operational flexibility**: Multiple intermediates for different purposes (TLS, S/MIME, code signing).

### 3.2 Certificate Chain Validation

**Path Building**:
1. Start with end-entity cert.
2. Find issuer cert via AIA extension or local cache.
3. Verify signature: `Verify(issuer.publicKey, hash(cert.tbsCertificate), cert.signature)`.
4. Repeat until root CA found in trust store.

**Validation Checks** (RFC 5280):
```go
// Pseudocode for chain validation
func ValidateChain(cert *x509.Certificate, intermediates, roots []*x509.Certificate) error {
    chain := buildChain(cert, intermediates, roots)
    
    for i := 0; i < len(chain)-1; i++ {
        subject, issuer := chain[i], chain[i+1]
        
        // 1. Signature verification
        if !verifySignature(issuer.PublicKey, subject.RawTBSCertificate, subject.Signature) {
            return ErrInvalidSignature
        }
        
        // 2. Validity period (with clock skew tolerance)
        now := time.Now()
        if now.Before(subject.NotBefore.Add(-5*time.Minute)) || now.After(subject.NotAfter) {
            return ErrExpired
        }
        
        // 3. Key usage constraints
        if issuer != root && !issuer.IsCA {
            return ErrNotCA
        }
        if issuer.MaxPathLen >= 0 && pathLen > issuer.MaxPathLen {
            return ErrPathLenExceeded
        }
        
        // 4. Name constraints (if present in issuer)
        if !matchesNameConstraints(subject.DNSNames, issuer.PermittedDNSDomains) {
            return ErrNameConstraintViolation
        }
        
        // 5. Revocation check (CRL/OCSP)
        if revoked, err := checkRevocation(subject, issuer); revoked || err != nil {
            return ErrRevoked
        }
        
        pathLen++
    }
    
    // 6. Verify root is in trust store
    if !isInTrustStore(chain[len(chain)-1], roots) {
        return ErrUntrustedRoot
    }
    
    return nil
}
```

**Trust Anchors**:
- **OS trust store**: `/etc/ssl/certs` (Linux), `Keychain.app` (macOS), `certmgr.msc` (Windows).
- **Browser trust store**: Firefox uses NSS DB, Chrome/Edge use OS store.
- **Container trust**: Custom CA bundle mounted at `/etc/ssl/certs/ca-certificates.crt`.

---

## 4. Certificate Revocation

### 4.1 Certificate Revocation Lists (CRL)

**Structure**:
```
CertificateList ::= SEQUENCE {
  tbsCertList          TBSCertList,
  signatureAlgorithm   AlgorithmIdentifier,
  signatureValue       BIT STRING
}

TBSCertList ::= SEQUENCE {
  version              Version OPTIONAL,
  signature            AlgorithmIdentifier,
  issuer               Name,
  thisUpdate           Time,
  nextUpdate           Time OPTIONAL,
  revokedCertificates  SEQUENCE OF SEQUENCE {
    userCertificate      CertificateSerialNumber,
    revocationDate       Time,
    crlEntryExtensions   Extensions OPTIONAL  // Reason code
  } OPTIONAL,
  crlExtensions        [0] EXPLICIT Extensions OPTIONAL
}
```

**Revocation Reasons**:
```
0: unspecified
1: keyCompromise          // Private key exposed
2: cACompromise           // CA key compromised (reissue all certs)
3: affiliationChanged     // Entity left org
4: superseded             // New cert issued
5: cessationOfOperation   // Service decommissioned
6: certificateHold        // Temporary suspension (can be unrevoked)
9: privilegeWithdrawn
10: aACompromise          // Attribute authority compromised
```

**CRL Problems**:
- **Size**: Large CRLs (100K+ certs) cause bandwidth/parsing overhead.
- **Freshness**: `nextUpdate` may be days old; stale revocation data.
- **Soft-fail**: Many clients ignore CRL fetch failures (security gap).

**Delta CRLs**: Incremental updates since last full CRL (reduces bandwidth).

### 4.2 Online Certificate Status Protocol (OCSP)

**Request/Response**:
```
Client → OCSP Responder:
  CertID = Hash(issuer.Name) || Hash(issuer.PublicKey) || cert.SerialNumber

OCSP Responder → Client:
  Status: good | revoked | unknown
  thisUpdate, nextUpdate
  Signature (from OCSP signing cert)
```

**OCSP Stapling** (TLS Certificate Status Request):
- Server fetches OCSP response, caches it, staples to TLS handshake.
- Client validates stapled response (must be signed, fresh).
- Eliminates client → OCSP responder connection (privacy + performance).
- **Must-Staple** extension: TLS handshake fails if staple missing (prevents downgrade).

**OCSP Problems**:
- **Privacy**: OCSP request reveals which cert client is validating (correlates browsing).
- **Availability**: OCSP responder outage → soft-fail allows revoked certs.
- **Performance**: Adds latency to TLS handshake.

### 4.3 Modern Revocation: Short-Lived Certificates

**Strategy**:
- Issue certs with 1-24 hour validity.
- No revocation infrastructure needed (cert expires before revocation matters).
- Compromised key? Wait <24h for expiration.

**Trade-offs**:
- **Pros**: No CRL/OCSP overhead, simpler infrastructure.
- **Cons**: Requires automated renewal (ACME, cert-manager), CA must be highly available.

**Production example** (SPIFFE):
```bash
# SPIRE agent issues SVIDs with 1-hour TTL
spire-agent api fetch x509 -socketPath /run/spire/sockets/agent.sock
# Certificate expires in 3600s, auto-renewed at 50% lifetime
```

---

## 5. PKI in TLS/mTLS

### 5.1 TLS Handshake (1.3)

```
Client                                    Server
  |                                         |
  |--- ClientHello (SNI, cipher suites) --->|
  |                                         |
  |<--- ServerHello (cipher, key share) ---|
  |<--- {EncryptedExtensions} -------------|
  |<--- {Certificate*} --------------------|  // Server cert chain
  |<--- {CertificateVerify*} --------------|  // Signature over handshake
  |<--- {Finished} -------------------------|
  |                                         |
  |--- {Certificate*} ---------------------->|  // Client cert (mTLS only)
  |--- {CertificateVerify*} --------------->|
  |--- {Finished} ------------------------->|
  |                                         |
  |<====== Encrypted Application Data ====>|
```

**Certificate Verification**:
1. Server sends cert chain in `Certificate` message.
2. Client validates chain (signature, validity, revocation, hostname match).
3. Server proves possession of private key via `CertificateVerify` (signs handshake transcript).
4. mTLS: Client sends cert, server validates + extracts identity.

**Hostname Verification**:
```go
// RFC 6125 rules
func verifyHostname(cert *x509.Certificate, hostname string) error {
    // 1. Check SAN DNS names (wildcard matching)
    for _, san := range cert.DNSNames {
        if matchHostname(san, hostname) {  // *.example.com matches foo.example.com
            return nil
        }
    }
    
    // 2. Fallback to CN (deprecated, only if SAN absent)
    if len(cert.DNSNames) == 0 {
        if matchHostname(cert.Subject.CommonName, hostname) {
            return nil
        }
    }
    
    return ErrHostnameMismatch
}
```

### 5.2 Mutual TLS (mTLS) in Production

**Kubernetes API Server**:
```bash
# API server TLS config
kube-apiserver \
  --tls-cert-file=/var/lib/kubernetes/apiserver.crt \       # Server cert
  --tls-private-key-file=/var/lib/kubernetes/apiserver.key \
  --client-ca-file=/var/lib/kubernetes/ca.crt \             # Trust anchor for client certs
  --tls-cipher-suites=TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256 \
  --tls-min-version=VersionTLS13

# Client (kubectl) config
kubectl config set-cluster prod \
  --certificate-authority=/path/to/ca.crt \   # Trust server cert
  --embed-certs=true \
  --server=https://k8s-api.example.com:6443

kubectl config set-credentials admin \
  --client-certificate=/path/to/admin.crt \   # Client cert for auth
  --client-key=/path/to/admin.key
```

**Service Mesh (Istio/Linkerd)**:
```yaml
# Workload identity via SPIFFE X.509-SVID
apiVersion: v1
kind: Pod
metadata:
  name: frontend
spec:
  serviceAccountName: frontend-sa  # K8s SA → SPIFFE ID
  containers:
  - name: app
    # Envoy sidecar injects mTLS with auto-rotated certs (1h TTL)
    # SPIFFE ID: spiffe://cluster.local/ns/default/sa/frontend-sa
```

**mTLS Termination Points**:
- **Edge**: Load balancer terminates TLS, backend uses HTTP (simpler, less secure).
- **End-to-end**: TLS from client to pod (Envoy sidecar) – full encryption, higher CPU cost.

---

## 6. Certificate Authorities (CA) Operations

### 6.1 Root CA Design

**Offline Root CA** (air-gapped):
```bash
# Generate root key in HSM
pkcs11-tool --module /usr/lib/softhsm/libsofthsm2.so \
  --login --keypairgen --key-type RSA:4096 --label root-ca-key

# Create root certificate (self-signed)
openssl req -new -x509 -days 7300 -sha256 \
  -engine pkcs11 -keyform engine -key slot_0-id_01 \
  -out root-ca.crt -subj "/C=US/O=Example Inc/CN=Example Root CA" \
  -addext "basicConstraints=critical,CA:TRUE" \
  -addext "keyUsage=critical,keyCertSign,cRLSign"

# Export public cert, destroy private key access (HSM-locked)
# Store root cert in OS trust store: /etc/pki/ca-trust/source/anchors/
```

**Root CA Key Ceremony**:
1. Multi-party key generation (3 of 5 quorum for HSM unlock).
2. Witness attestation (video, signatures).
3. Hardware entropy source validation.
4. Key backup (split PGP-encrypted shares, geographically distributed).

### 6.2 Intermediate CA (Online)

```bash
# Generate intermediate key (also HSM-backed)
openssl genrsa -out intermediate-ca.key 4096

# Create CSR
openssl req -new -key intermediate-ca.key -out intermediate-ca.csr \
  -subj "/C=US/O=Example Inc/CN=Example Issuing CA"

# Sign with root CA (offline operation)
openssl x509 -req -in intermediate-ca.csr -CA root-ca.crt -CAkey root-ca.key \
  -CAcreateserial -out intermediate-ca.crt -days 3650 -sha256 \
  -extfile <(cat <<EOF
basicConstraints=critical,CA:TRUE,pathlen:0
keyUsage=critical,digitalSignature,keyCertSign,cRLSign
authorityKeyIdentifier=keyid:always
subjectKeyIdentifier=hash
crlDistributionPoints=URI:http://crl.example.com/root.crl
authorityInfoAccess=OCSP;URI:http://ocsp.example.com,caIssuers;URI:http://certs.example.com/root.crt
EOF
)

# Concatenate chain (intermediate + root) for distribution
cat intermediate-ca.crt root-ca.crt > ca-chain.crt
```

### 6.3 Issuing End-Entity Certificates

**Manual Process**:
```bash
# 1. Generate key (on client)
openssl genrsa -out server.key 2048

# 2. Create CSR
openssl req -new -key server.key -out server.csr \
  -subj "/C=US/O=Example Inc/CN=api.example.com" \
  -addext "subjectAltName=DNS:api.example.com,DNS:www.example.com"

# 3. CA signs CSR
openssl x509 -req -in server.csr -CA intermediate-ca.crt -CAkey intermediate-ca.key \
  -CAcreateserial -out server.crt -days 90 -sha256 \
  -extfile <(cat <<EOF
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=DNS:api.example.com,DNS:www.example.com
authorityKeyIdentifier=keyid:always
subjectKeyIdentifier=hash
crlDistributionPoints=URI:http://crl.example.com/intermediate.crl
authorityInfoAccess=OCSP;URI:http://ocsp.example.com
EOF
)
```

**Automated (ACME Protocol)**:
```bash
# Let's Encrypt via certbot
certbot certonly --standalone -d api.example.com -d www.example.com \
  --non-interactive --agree-tos --email admin@example.com

# ACME challenge types:
# - HTTP-01: Place file at http://domain/.well-known/acme-challenge/TOKEN
# - DNS-01: Add TXT record _acme-challenge.domain with hash (wildcard certs)
# - TLS-ALPN-01: TLS handshake with ALPN extension (port 443 only)
```

---

## 7. PKI in Kubernetes and Cloud-Native

### 7.1 Kubernetes PKI Architecture

```
┌──────────────────────────────────────────────────────────┐
│ /etc/kubernetes/pki/                                     │
│                                                          │
│  ca.crt, ca.key              ← Cluster CA (signs kubelet,│
│                                 API server, controllers) │
│                                                          │
│  apiserver.crt/key           ← API server TLS cert      │
│  apiserver-kubelet-client.crt← API → kubelet client cert│
│                                                          │
│  front-proxy-ca.crt/key      ← Aggregation layer CA     │
│  front-proxy-client.crt/key  ← API aggregator client    │
│                                                          │
│  etcd/ca.crt, etcd/server.crt← Separate etcd PKI        │
│  etcd/peer.crt               ← etcd peer mTLS           │
│                                                          │
│  sa.key, sa.pub              ← ServiceAccount token sign│
└──────────────────────────────────────────────────────────┘
```

**Certificate Rotation**:
```bash
# Kubelet auto-rotates client cert (enabled via --rotate-certificates)
# API server cert rotation requires manual renewal + API restart

# Check cert expiration
kubeadm certs check-expiration

# Renew all certs (except CA)
kubeadm certs renew all
systemctl restart kubelet
```

### 7.2 cert-manager (Kubernetes Certificate Automation)

```yaml
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.0/cert-manager.yaml

# ClusterIssuer (ACME Let's Encrypt)
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-account-key
    solvers:
    - http01:
        ingress:
          class: nginx

# Certificate resource (auto-renewal)
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
  - www.example.com
  duration: 2160h      # 90 days
  renewBefore: 720h    # Renew 30 days before expiry

# Ingress consumes certificate
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
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
              number: 80
```

### 7.3 SPIFFE/SPIRE (Workload Identity)

**SPIFFE ID**: `spiffe://trust-domain/path/to/workload`

```bash
# Install SPIRE server (manages CA, issues SVIDs)
kubectl apply -f https://raw.githubusercontent.com/spiffe/spire-tutorials/main/k8s/quickstart/server-statefulset.yaml

# Install SPIRE agent (daemonset, talks to kubelet)
kubectl apply -f https://raw.githubusercontent.com/spiffe/spire-tutorials/main/k8s/quickstart/agent-daemonset.yaml

# Register workload (creates SPIFFE ID)
kubectl exec -n spire spire-server-0 -- \
  /opt/spire/bin/spire-server entry create \
  -spiffeID spiffe://example.org/ns/default/sa/frontend \
  -parentID spiffe://example.org/spire/agent/k8s_psat/demo-cluster/default \
  -selector k8s:sa:frontend \
  -selector k8s:ns:default \
  -ttl 3600

# Workload fetches SVID (X.509 cert + key)
# Cert contains SAN URI: spiffe://example.org/ns/default/sa/frontend
# Auto-rotated every 30 min (configurable)
```

**SPIRE Integration** (Envoy sidecar):
```yaml
# Envoy fetches certs from SPIRE agent via Unix socket
static_resources:
  listeners:
  - name: listener_0
    address:
      socket_address: { address: 0.0.0.0, port_value: 8080 }
    filter_chains:
    - transport_socket:
        name: envoy.transport_sockets.tls
        typed_config:
          "@type": type.googleapis.com/envoy.extensions.transport_sockets.tls.v3.DownstreamTlsContext
          common_tls_context:
            tls_certificate_sds_secret_configs:
            - name: spiffe://example.org/ns/default/sa/frontend
              sds_config:
                api_config_source:
                  api_type: GRPC
                  grpc_services:
                  - envoy_grpc:
                      cluster_name: spire_agent
            validation_context_sds_secret_config:
              name: spiffe://example.org
              sds_config:
                api_config_source:
                  api_type: GRPC
                  grpc_services:
                  - envoy_grpc:
                      cluster_name: spire_agent

  clusters:
  - name: spire_agent
    type: STATIC
    load_assignment:
      cluster_name: spire_agent
      endpoints:
      - lb_endpoints:
        - endpoint:
            address:
              pipe: { path: /run/spire/sockets/agent.sock }
```

---

## 8. HSM and Key Management

### 8.1 Hardware Security Module (HSM)

**Purpose**: Tamper-resistant hardware protecting cryptographic keys.

**FIPS 140-2 Levels**:
- **L1**: Software crypto (no physical security).
- **L2**: Tamper-evident seals, role-based auth.
- **L3**: Tamper-responsive (zeroizes keys on physical intrusion), identity-based auth.
- **L4**: Environmental failure protection (voltage/temp attacks), side-channel resistance.

**Operations**:
```c
// PKCS#11 API (C)
#include <pkcs11.h>

CK_SESSION_HANDLE session;
CK_MECHANISM mechanism = { CKM_RSA_PKCS, NULL_PTR, 0 };

// Find private key
CK_OBJECT_HANDLE privKey;
CK_ATTRIBUTE template[] = { {CKA_LABEL, "root-ca-key", 11} };
C_FindObjectsInit(session, template, 1);
C_FindObjects(session, &privKey, 1, &count);

// Sign operation (key never leaves HSM)
CK_BYTE hash[32] = { /* SHA-256 hash */ };
CK_BYTE signature[512];
CK_ULONG sigLen = sizeof(signature);

C_SignInit(session, &mechanism, privKey);
C_Sign(session, hash, sizeof(hash), signature, &sigLen);
```

**Cloud HSM**:
```bash
# AWS CloudHSM (FIPS 140-2 L3)
aws cloudhsmv2 create-cluster --hsm-type hsm1.medium \
  --subnet-ids subnet-abc123 subnet-def456

# Initialize cluster, create users
cloudhsm-cli user create --username admin --role admin

# Use with OpenSSL PKCS#11 engine
openssl req -new -x509 -days 3650 -sha256 \
  -engine pkcs11 -keyform engine \
  -key "pkcs11:token=cloudhsm;object=root-ca-key;type=private" \
  -out root-ca.crt
```

### 8.2 TPM 2.0 (Trusted Platform Module)

**Use Cases**: Device attestation, disk encryption (BitLocker, LUKS), measured boot.

```bash
# Generate key in TPM (non-exportable)
tpm2_createprimary -C o -g sha256 -G rsa -c primary.ctx
tpm2_create -C primary.ctx -g sha256 -G rsa -r priv.key -u pub.key \
  -a "fixedtpm|fixedparent|sensitivedataorigin|userwithauth|sign"

# Load key into TPM
tpm2_load -C primary.ctx -r priv.key -u pub.key -c key.ctx

# Sign with TPM key
echo "data" | tpm2_sign -c key.ctx -g sha256 -o signature.dat

# Attestation (prove TPM state)
tpm2_quote -c key.ctx -l sha256:0,1,2 -q NONCE -m quote.msg -s quote.sig -o pcr.out
```

**Remote Attestation** (Azure Attestation Service):
```bash
# VM boot creates TPM quote (signed PCR values + measurement log)
# Client sends quote to Azure Attestation Service
# Service validates quote signature (TPM endorsement key), checks PCR values against policy
# Returns JWT token if VM trusted (used for key release from Azure Key Vault)
```

---

## 9. Code Signing and Software Supply Chain

### 9.1 Binary Code Signing

**Purpose**: Prove software authenticity, detect tampering.

```bash
# Sign binary with Authenticode (Windows)
signtool sign /f codesign.pfx /p PASSWORD /t http://timestamp.digicert.com \
  /fd sha256 /v app.exe

# Sign binary with Apple codesign
codesign --sign "Developer ID Application: Example Inc" \
  --timestamp --options runtime app.app

# Verify signature
codesign --verify --verbose app.app
spctl --assess --verbose app.app  # Gatekeeper check
```

**Linux: GPG/PGP Signing**:
```bash
# Generate GPG key
gpg --full-generate-key --expert
# Select: (9) ECC (sign only), Curve 25519, no expiry

# Sign binary
gpg --detach-sign --armor --output app.sig app.bin

# Verify
gpg --verify app.sig app.bin
```

### 9.2 Container Image Signing (Sigstore/Cosign)

**Cosign** (keyless signing with Fulcio CA, transparency log Rekor):
```bash
# Install cosign
go install github.com/sigstore/cosign/v2/cmd/cosign@latest

# Sign image (OIDC auth, ephemeral key, Fulcio issues short-lived cert)
cosign sign --yes registry.example.com/app:v1.0

# Verification flow:
# 1. Cosign fetches signature from registry (OCI referrers API)
# 2. Signature contains ephemeral public key + Fulcio cert
# 3. Validate Fulcio cert chain (roots in TUF repository)
# 4. Check transparency log (Rekor) for signature entry (prevents post-hoc forgery)
# 5. Verify image digest signature

# Verify image
cosign verify --certificate-identity user@example.com \
  --certificate-oidc-issuer https://accounts.google.com \
  registry.example.com/app:v1.0

# Admission controller (enforce signatures)
kubectl apply -f https://raw.githubusercontent.com/sigstore/policy-controller/main/config/policy-controller.yaml

# ClusterImagePolicy (require cosign signature)
apiVersion: policy.sigstore.dev/v1beta1
kind: ClusterImagePolicy
metadata:
  name: require-signed-images
spec:
  images:
  - glob: "registry.example.com/**"
  authorities:
  - keyless:
      url: https://fulcio.sigstore.dev
      identities:
      - issuer: https://accounts.google.com
        subject: ci-bot@example.com
```

**Notary v2** (OCI artifact signing, CNCF project):
```bash
# Add signature to OCI registry
notation sign registry.example.com/app:v1.0

# Verification policy (trust specific cert)
cat > trustpolicy.json <<EOF
{
  "version": "1.0",
  "trustPolicies": [
    {
      "name": "prod-images",
      "registryScopes": ["registry.example.com/*"],
      "signatureVerification": {
        "level": "strict"
      },
      "trustStores": ["ca:example-ca"],
      "trustedIdentities": ["x509.subject:CN=Example CI"]
    }
  ]
}
EOF

notation verify registry.example.com/app:v1.0
```

---

## 10. PKI in SSH

### 10.1 SSH Certificates vs SSH Keys

**Traditional SSH** (public key authentication):
```bash
# Client has private key, server stores public key in ~/.ssh/authorized_keys
# No expiration, manual key distribution/revocation
```

**SSH Certificates**:
```bash
# CA signs user public key, creates certificate with principals, validity
# Server trusts CA public key (in sshd_config), accepts any cert signed by CA

# Generate SSH CA
ssh-keygen -t ed25519 -f ssh-ca -C "SSH CA"

# Sign user key (create certificate)
ssh-keygen -s ssh-ca -I user@example.com -n ubuntu,root \
  -V +52w user.pub
# Output: user-cert.pub (certificate)

# User connects with certificate
ssh -i user ubuntu@server
# Server validates: certificate signature, principals (ubuntu), validity period

# Server config
echo "TrustedUserCAKeys /etc/ssh/ssh-ca.pub" >> /etc/sshd_config
systemctl reload sshd
```

**SSH Host Certificates** (prevent TOFU attacks):
```bash
# Sign host key
ssh-keygen -s ssh-ca -I server.example.com -h -n server.example.com \
  -V +520w /etc/ssh/ssh_host_ed25519_key.pub

# Client trusts CA
echo "@cert-authority *.example.com $(cat ssh-ca.pub)" >> ~/.ssh/known_hosts

# No more "unknown host" warnings for example.com hosts
```

### 10.2 SSH Certificate Automation (Vault, step-ca)

**HashiCorp Vault**:
```bash
# Enable SSH secrets engine
vault secrets enable ssh

# Configure CA
vault write ssh/config/ca generate_signing_key=true

# Create signing role
vault write ssh/roles/prod-servers \
  key_type=ca \
  allowed_users=ubuntu,admin \
  default_user=ubuntu \
  ttl=8h \
  max_ttl=24h

# Client requests signed certificate
vault write -field=signed_key ssh/sign/prod-servers \
  public_key=@~/.ssh/id_ed25519.pub > ~/.ssh/id_ed25519-cert.pub

# SSH with certificate (auto-expires in 8h)
ssh ubuntu@server
```

---

## 11. PKI Testing, Threat Modeling, and Hardening

### 11.1 Certificate Validation Testing

```go
// Test harness for chain validation
package main

import (
    "crypto/x509"
    "encoding/pem"
    "os"
    "testing"
)

func TestCertificateChainValidation(t *testing.T) {
    // Load test certs
    certPEM, _ := os.ReadFile("testdata/leaf.crt")
    intermediatePEM, _ := os.ReadFile("testdata/intermediate.crt")
    rootPEM, _ := os.ReadFile("testdata/root.crt")
    
    block, _ := pem.Decode(certPEM)
    cert, _ := x509.ParseCertificate(block.Bytes)
    
    block, _ = pem.Decode(intermediatePEM)
    intermediate, _ := x509.ParseCertificate(block.Bytes)
    
    block, _ = pem.Decode(rootPEM)
    root, _ := x509.ParseCertificate(block.Bytes)
    
    // Test cases
    tests := []struct {
        name        string
        cert        *x509.Certificate
        intermediates []*x509.Certificate
        roots       []*x509.Certificate
        hostname    string
        wantErr     bool
    }{
        {"valid chain", cert, []*x509.Certificate{intermediate}, []*x509.Certificate{root}, "api.example.com", false},
        {"expired cert", createExpiredCert(), []*x509.Certificate{intermediate}, []*x509.Certificate{root}, "api.example.com", true},
        {"hostname mismatch", cert, []*x509.Certificate{intermediate}, []*x509.Certificate{root}, "wrong.example.com", true},
        {"missing intermediate", cert, nil, []*x509.Certificate{root}, "api.example.com", true},
        {"untrusted root", cert, []*x509.Certificate{intermediate}, nil, "api.example.com", true},
    }
    
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            roots := x509.NewCertPool()
            for _, r := range tt.roots {
                roots.AddCert(r)
            }
            
            intermediates := x509.NewCertPool()
            for _, i := range tt.intermediates {
                intermediates.AddCert(i)
            }
            
            opts := x509.VerifyOptions{
                Roots:         roots,
                Intermediates: intermediates,
                DNSName:       tt.hostname,
            }
            
            _, err := tt.cert.Verify(opts)
            if (err != nil) != tt.wantErr {
                t.Errorf("Verify() error = %v, wantErr %v", err, tt.wantErr)
            }
        })
    }
}
```

**Fuzzing Certificate Parsing**:
```bash
# Go fuzzing
go test -fuzz=FuzzParseCertificate -fuzztime=60s

# LibFuzzer (C/C++)
clang++ -g -fsanitize=fuzzer,address cert_fuzzer.cc -lcrypto -o cert_fuzzer
./cert_fuzzer corpus/ -max_len=10000 -runs=1000000
```

### 11.2 Threat Model

**Attack Vectors**:
1. **Private Key Compromise**:
   - Mitigation: HSM storage, key rotation, logging/alerting on key use.
   
2. **CA Compromise**:
   - Mitigation: Offline root, intermediate revocation, certificate transparency (CT logs).
   
3. **Man-in-the-Middle**:
   - Mitigation: Certificate pinning, HSTS, CAA DNS records.
   
4. **Revocation Bypass**:
   - Mitigation: OCSP stapling + must-staple, short-lived certs, CRLSets.
   
5. **Hostname Verification Bypass**:
   - Mitigation: Strict SAN matching, no CN fallback, HSTS preload.

**Certificate Transparency**:
```bash
# CT log monitors all CA-issued certs (public append-only log)
# Detect mis-issued certs (rogue CA, compromised CA)

# Check if cert is in CT logs
curl -s "https://crt.sh/?q=example.com&output=json" | jq .

# Enforce CT in TLS (Chrome requires 2+ SCTs for EV certs)
# SCT = Signed Certificate Timestamp from CT log
```

**CAA Records** (DNS):
```bash
# Restrict which CAs can issue certs for domain
dig CAA example.com

# Response:
example.com. 3600 IN CAA 0 issue "letsencrypt.org"
example.com. 3600 IN CAA 0 issuewild "letsencrypt.org"
example.com. 3600 IN CAA 0 iodef "mailto:security@example.com"

# CA must check CAA before issuance (ACME validation)
```

### 11.3 Hardening Checklist

```yaml
# Production PKI hardening
hardening:
  ca:
    - Offline root CA (air-gapped, HSM FIPS 140-2 L3+)
    - Intermediate CA key rotation every 2-5 years
    - Multi-party key ceremony (3 of 5 quorum)
    - Audit logging (all CA operations, tamper-proof)
    - Disaster recovery (encrypted key backups, geographic distribution)
  
  certificates:
    - Short-lived certs (90 days max, 1-24h for workload identity)
    - Automated renewal (cert-manager, ACME, SPIRE)
    - No wildcard certs in prod (use SAN for specific hosts)
    - ECDSA P-256 or Ed25519 (no RSA <3072-bit)
    - TLS 1.3 only, no CBC ciphers
  
  revocation:
    - OCSP stapling + must-staple extension
    - CRL distribution points (CDN-backed)
    - Short-lived certs preferred over revocation
  
  validation:
    - Strict hostname verification (no CN fallback)
    - Certificate pinning for high-value APIs
    - CT log monitoring (crt.sh alerts)
    - CAA records for all domains
  
  monitoring:
    - Cert expiration alerts (30/14/7 days)
    - OCSP responder uptime SLO 99.9%
    - TLS handshake failures (Prometheus metrics)
    - HSM tamper events (immediate pager)
```

---

## 12. Production Deployment Architecture

### 12.1 Multi-Region PKI

```
┌────────────────────────────────────────────────────────────┐
│  Offline Root CA (on-prem, HSM)                            │
│  - Signs intermediates only                                │
│  - Key ceremony every 5 years                              │
└────────────────┬───────────────────────────────────────────┘
                 │ issues
                 ├────────────────┬────────────────┐
                 ▼                ▼                ▼
     ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
     │ Intermediate CA  │ │ Intermediate CA  │ │ Intermediate CA  │
     │ (us-east-1, HSM) │ │ (eu-west-1, HSM) │ │ (ap-south-1, HSM)│
     │ - Issues TLS     │ │ - Issues TLS     │ │ - Issues TLS     │
     │ - OCSP responder │ │ - OCSP responder │ │ - OCSP responder │
     └──────────────────┘ └──────────────────┘ └──────────────────┘
```

**Deployment**:
```bash
# Terraform: Deploy intermediate CAs in each region
resource "aws_cloudhsm_v2_cluster" "ca_hsm" {
  for_each   = toset(["us-east-1", "eu-west-1", "ap-south-1"])
  provider   = aws.${each.key}
  hsm_type   = "hsm1.medium"
  subnet_ids = var.subnet_ids[each.key]
}

# OCSP responder (high availability)
resource "kubernetes_deployment" "ocsp_responder" {
  metadata {
    name = "ocsp-responder"
  }
  spec {
    replicas = 3
    template {
      spec {
        containers {
          image = "ocsp-responder:latest"
          env {
            name  = "CA_CERT"
            value = file("intermediate-ca.crt")
          }
          env {
            name = "HSM_PKCS11_LIB"
            value = "/usr/lib/cloudhsm/libnethsm.so"
          }
          liveness_probe {
            http_get {
              path = "/healthz"
              port = 8080
            }
          }
        }
      }
    }
  }
}

# CRL distribution (CDN)
resource "aws_cloudfront_distribution" "crl_cdn" {
  origin {
    domain_name = aws_s3_bucket.crl_bucket.bucket_regional_domain_name
    origin_id   = "crl-s3"
  }
  enabled = true
  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "crl-s3"
    viewer_protocol_policy = "https-only"
    min_ttl                = 3600
    max_ttl                = 86400
  }
}
```

### 12.2 Rollout and Rollback Plan

**New Root CA Deployment**:
```bash
# Phase 1: Dual root (old + new)
# 1. Generate new root CA (offline ceremony)
# 2. Issue new intermediates (signed by new root)
# 3. Distribute new root cert to trust stores (OS updates, container base images)
# 4. Serve both old and new cert chains from endpoints

# Phase 2: Monitor adoption (90 days)
# - Track TLS handshakes (which root validated)
# - Alert on old root usage >5%

# Phase 3: Deprecate old root (180 days)
# - Stop issuing from old intermediates
# - Monitor for old cert validation failures
# - Keep old OCSP responder running

# Phase 4: Revoke old root (365 days)
# - Add old root to blocklist
# - Remove old root from trust stores (next OS update cycle)

# Rollback: If new root issues detected <30 days
# - Stop issuing from new intermediates
# - Revert to old intermediates
# - Incident review
```

**Intermediate CA Rotation**:
```bash
# Zero-downtime rotation
# 1. Issue new intermediate from root
# 2. Deploy new intermediate to CA servers (blue-green)
# 3. Start issuing certs from new intermediate (include both in chain)
# 4. Wait for old certs to expire (90 days)
# 5. Revoke old intermediate
# 6. Remove old intermediate from OCSP responders
```

---

## 13. Testing and Benchmarking

```bash
# TLS handshake benchmarking
openssl s_time -connect api.example.com:443 -new -time 60

# OCSP response time
time openssl ocsp -issuer intermediate-ca.crt -cert server.crt \
  -url http://ocsp.example.com -resp_text

# Certificate chain building performance
go test -bench=BenchmarkChainValidation -benchtime=10s -benchmem

# HSM signing throughput
pkcs11-tool --module /usr/lib/softhsm/libsofthsm2.so \
  --login --test --test-sign-speed 1000

# TLS handshake load test (100K connections)
vegeta attack -duration=60s -rate=1667/s -targets=targets.txt | vegeta report

# targets.txt:
GET https://api.example.com:443
```

---

## 14. Next 3 Steps

1. **Set up internal PKI lab**:
   ```bash
   # Deploy step-ca (lightweight ACME CA)
   docker run -d -p 9000:9000 -v $PWD/step:/home/step smallstep/step-ca
   step ca init --deployment-type=standalone --name="Lab CA" --dns=step-ca.local
   
   # Issue test cert
   step ca certificate localhost localhost.crt localhost.key --provisioner=admin
   
   # Test mTLS
   openssl s_server -cert localhost.crt -key localhost.key -CAfile root_ca.crt -verify 1
   ```

2. **Implement SPIRE in dev cluster**:
   ```bash
   kubectl apply -k https://github.com/spiffe/spire-tutorials/k8s/quickstart
   
   # Deploy test workload with SPIFFE identity
   kubectl apply -f workload.yaml
   
   # Verify SVID issuance
   kubectl exec -n spire spire-server-0 -- \
     /opt/spire/bin/spire-server entry show
   ```

3. **Automate cert monitoring**:
   ```bash
   # Deploy x509-certificate-exporter (Prometheus)
   helm install cert-exporter enix/x509-certificate-exporter \
     --set secretsExporter.enabled=true
   
   # Alert rule (Prometheus)
   - alert: CertificateExpiringSoon
     expr: x509_cert_not_after - time() < 86400 * 30
     annotations:
       summary: "Certificate {{ $labels.subject_CN }} expires in <30 days"
   ```

---

## References

- **RFC 5280**: X.509 PKI Certificate and CRL Profile
- **RFC 8446**: TLS 1.3
- **RFC 8555**: ACME Protocol
- **NIST SP 800-57**: Key Management Recommendations
- **SPIFFE Spec**: https://github.com/spiffe/spiffe/tree/main/standards
- **cert-manager docs**: https://cert-manager.io/docs/
- **Sigstore architecture**: https://docs.sigstore.dev/system_config/architecture/
- **HashiCorp Vault PKI**: https://developer.hashicorp.com/vault/docs/secrets/pki
- **AWS CloudHSM**: https://docs.aws.amazon.com/cloudhsm/latest/userguide/