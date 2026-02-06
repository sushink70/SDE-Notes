# ACME Protocol – Comprehensive Deep-Dive

**Executive Summary:**  
ACME (Automatic Certificate Management Environment, RFC 8555) is a protocol for automating X.509 certificate lifecycle management between Certificate Authorities (CAs) and clients. It eliminates manual CSR submission, domain validation, and renewal via cryptographic challenges (HTTP-01, DNS-01, TLS-ALPN-01) and RESTful JSON-over-HTTPS APIs. ACME is the backbone of Let's Encrypt (2+ billion certificates issued), used in production by Kubernetes cert-manager, Caddy, Traefik, and enterprises for zero-touch PKI. Security model: account key binds identity, order nonces prevent replay, JWS signatures ensure integrity, challenge validation proves domain control. Threat surface: DNS hijacking (DNSSEC mitigation), BGP hijacking (multi-VA), key compromise (short-lived certs + rotation).

---

## 1. ACME Protocol Architecture & Core Concepts

### 1.1 What Problem Does ACME Solve?

**Pre-ACME World:**
- Manual CSR generation → email to CA → wait hours/days → download cert → install → repeat in 1 year
- Human error: expired certs cause outages (Equifax, Microsoft Azure, LinkedIn)
- No automation → can't do short-lived certificates (90-day certs impossible manually)

**ACME Solution:**
- **Zero-touch automation**: client requests cert → proves domain control → receives cert in <60s
- **Short certificate lifetimes**: Let's Encrypt issues 90-day certs (vs industry 1-year), reducing blast radius of key compromise
- **Cryptographic proof of control**: challenges replace email/manual validation

---

### 1.2 High-Level Flow (Account → Order → Authorization → Challenge → Certificate)

```
┌──────────────┐                    ┌──────────────────┐
│ ACME Client  │                    │   ACME Server    │
│ (certbot,    │                    │  (Let's Encrypt, │
│  cert-mgr)   │                    │   Boulder, Pebble│
└──────┬───────┘                    └────────┬─────────┘
       │                                     │
       │ 1. Create Account (JWK pubkey)      │
       ├────────────────────────────────────>│
       │    POST /acme/new-acct              │
       │    {account-key-pub, contact}       │
       │                                     │
       │ 2. Account URL + Kid (Key ID)       │
       │<────────────────────────────────────┤
       │    201 Created                      │
       │    Location: /acme/acct/12345       │
       │                                     │
       │ 3. Create Order (identifiers)       │
       ├────────────────────────────────────>│
       │    POST /acme/new-order             │
       │    {identifiers: [example.com]}     │
       │                                     │
       │ 4. Order Object (authz URLs)        │
       │<────────────────────────────────────┤
       │    201 Created                      │
       │    {status: pending, authz: [...]}  │
       │                                     │
       │ 5. Fetch Authorization              │
       ├────────────────────────────────────>│
       │    POST-as-GET /acme/authz/67890    │
       │                                     │
       │ 6. Authorization + Challenges       │
       │<────────────────────────────────────┤
       │    {identifier: example.com,        │
       │     challenges: [http-01, dns-01]}  │
       │                                     │
       │ 7. Provision Challenge Response     │
       │    (e.g., create DNS TXT record     │
       │     or serve file on /.well-known)  │
       │                                     │
       │ 8. Notify Challenge Ready           │
       ├────────────────────────────────────>│
       │    POST /acme/chall/abc123 {}       │
       │                                     │
       │ 9. Server Validates (multi-VA)      │
       │                                  ┌──┴───┐
       │                                  │ VA 1 │ DNS lookup
       │                                  │ VA 2 │ HTTP GET
       │                                  │ VA 3 │ (diff regions)
       │                                  └──┬───┘
       │                                     │
       │ 10. Challenge Status: valid         │
       │<────────────────────────────────────┤
       │    {status: valid}                  │
       │                                     │
       │ 11. Finalize Order (CSR)            │
       ├────────────────────────────────────>│
       │    POST /acme/order/xyz/finalize    │
       │    {csr: base64url(DER-encoded)}    │
       │                                     │
       │ 12. Certificate URL                 │
       │<────────────────────────────────────┤
       │    {status: valid, cert: URL}       │
       │                                     │
       │ 13. Download Certificate            │
       ├────────────────────────────────────>│
       │    POST-as-GET /acme/cert/final     │
       │                                     │
       │ 14. PEM Certificate Chain           │
       │<────────────────────────────────────┤
       │    -----BEGIN CERTIFICATE-----      │
       │    (leaf + intermediates)           │
       │                                     │
```

**State Machine:**
```
Account: pending → valid (or deactivated/revoked)
Order: pending → ready → processing → valid (or invalid)
Authorization: pending → valid (or invalid/deactivated/expired)
Challenge: pending → processing → valid (or invalid)
```

---

## 2. Deep-Dive: ACME Components

### 2.1 Account Object

**Purpose:** Cryptographic identity binding for all operations.

**Account Creation Request (JWS-signed):**
```json
POST /acme/new-account HTTP/1.1
Host: acme-v02.api.letsencrypt.org
Content-Type: application/jose+json

{
  "protected": "base64url({
    \"alg\": \"RS256\",
    \"jwk\": {
      \"kty\": \"RSA\",
      \"n\": \"<modulus>\",
      \"e\": \"AQAB\"
    },
    \"nonce\": \"<server-nonce>\",
    \"url\": \"https://acme-v02.api.letsencrypt.org/acme/new-account\"
  })",
  "payload": "base64url({
    \"termsOfServiceAgreed\": true,
    \"contact\": [\"mailto:admin@example.com\"]
  })",
  "signature": "<JWS-signature>"
}
```

**Server Response:**
```http
HTTP/1.1 201 Created
Location: https://acme-v02.api.letsencrypt.org/acme/acct/123456789
Content-Type: application/json

{
  "status": "valid",
  "contact": ["mailto:admin@example.com"],
  "orders": "https://acme-v02.api.letsencrypt.org/acme/acct/123456789/orders"
}
```

**Key Security Properties:**
- **Account key = identity**: All subsequent requests signed with this key (no password/session token)
- **Key ID (kid)**: After account creation, use `kid` header instead of `jwk` (prevents key substitution)
- **External Account Binding (EAB)**: For private CAs, requires pre-shared HMAC key to link ACME account to billing/policy system

**Account Key Rollover:**
```
Client generates new keypair → signs rollover request with OLD key → 
payload contains NEW key → server validates both signatures → updates account
```

---

### 2.2 Order Object

**Purpose:** Container for certificate request lifecycle.

**Order Creation:**
```json
POST /acme/new-order
{
  "protected": "base64url({\"alg\":\"RS256\",\"kid\":\"<account-url>\",\"nonce\":\"...\"})",
  "payload": "base64url({
    \"identifiers\": [
      {\"type\": \"dns\", \"value\": \"example.com\"},
      {\"type\": \"dns\", \"value\": \"*.example.com\"}
    ],
    \"notBefore\": \"2026-02-06T10:00:00Z\",
    \"notAfter\": \"2026-05-07T10:00:00Z\"
  })",
  "signature": "..."
}
```

**Order Response:**
```json
{
  "status": "pending",
  "expires": "2026-02-13T10:00:00Z",
  "identifiers": [
    {"type": "dns", "value": "example.com"},
    {"type": "dns", "value": "*.example.com"}
  ],
  "authorizations": [
    "https://acme-v02.api.letsencrypt.org/acme/authz/abc123",
    "https://acme-v02.api.letsencrypt.org/acme/authz/def456"
  ],
  "finalize": "https://acme-v02.api.letsencrypt.org/acme/order/xyz789/finalize"
}
```

**Wildcard Certificates:**
- Require DNS-01 challenge (HTTP-01 not allowed for `*.example.com`)
- CAA record check: `issue` or `issuewild` must permit CA

---

### 2.3 Authorization & Challenges

**Authorization Object:**
```json
{
  "identifier": {"type": "dns", "value": "example.com"},
  "status": "pending",
  "expires": "2026-02-13T10:00:00Z",
  "challenges": [
    {
      "type": "http-01",
      "url": "https://.../acme/chall/http-aaa",
      "token": "evaGxfADs6pSRb2LAv9IZf17Dt3juxGJ-PCt92wr-oA"
    },
    {
      "type": "dns-01",
      "url": "https://.../acme/chall/dns-bbb",
      "token": "evaGxfADs6pSRb2LAv9IZf17Dt3juxGJ-PCt92wr-oA"
    },
    {
      "type": "tls-alpn-01",
      "url": "https://.../acme/chall/tls-ccc",
      "token": "evaGxfADs6pSRb2LAv9IZf17Dt3juxGJ-PCt92wr-oA"
    }
  ]
}
```

---

#### **Challenge Type 1: HTTP-01**

**How It Works:**
1. Client receives `token` from server
2. Client computes `key-authorization = token || '.' || base64url(SHA256(account-JWK))`
3. Client serves file at `http://<domain>/.well-known/acme-challenge/<token>` containing `key-authorization`
4. CA fetches from **multiple vantage points** (e.g., AWS us-east-1, us-west-2, eu-central-1)
5. CA verifies response == expected key-authorization

**Example:**
```bash
# Token from server
TOKEN="evaGxfADs6pSRb2LAv9IZf17Dt3juxGJ-PCt92wr-oA"

# Compute thumbprint of account key
THUMBPRINT=$(echo -n '{"e":"AQAB","kty":"RSA","n":"<modulus>"}' | \
  openssl dgst -sha256 -binary | base64url)

# Key authorization
KEY_AUTH="${TOKEN}.${THUMBPRINT}"

# Serve on HTTP server
mkdir -p /var/www/.well-known/acme-challenge
echo "$KEY_AUTH" > /var/www/.well-known/acme-challenge/$TOKEN

# Nginx config
location /.well-known/acme-challenge/ {
    alias /var/www/.well-known/acme-challenge/;
}
```

**Security Model:**
- **Proves HTTP control** (not DNS control)
- **Redirects allowed** (301/302 to HTTPS OK), but HTTPS-only domains must use TLS-ALPN-01
- **Cannot be used for wildcards**

**Failure Modes:**
- Firewall blocks port 80 → use DNS-01 or TLS-ALPN-01
- CDN caching → ensure `.well-known/acme-challenge/*` bypasses cache
- Load balancer sticky sessions → all backends must serve token

---

#### **Challenge Type 2: DNS-01**

**How It Works:**
1. Client receives `token`
2. Client computes `key-authorization` (same as HTTP-01)
3. Client creates TXT record: `_acme-challenge.<domain>` = `base64url(SHA256(key-authorization))`
4. CA performs DNS lookup from multiple resolvers
5. CA verifies TXT record matches expected digest

**Example:**
```bash
# Token
TOKEN="evaGxfADs6pSRb2LAv9IZf17Dt3juxGJ-PCt92wr-oA"

# Key authorization
KEY_AUTH="${TOKEN}.${THUMBPRINT}"

# DNS TXT value
TXT_VALUE=$(echo -n "$KEY_AUTH" | openssl dgst -sha256 -binary | base64url)

# Create DNS record
aws route53 change-resource-record-sets --hosted-zone-id Z1234 --change-batch '{
  "Changes": [{
    "Action": "UPSERT",
    "ResourceRecordSet": {
      "Name": "_acme-challenge.example.com",
      "Type": "TXT",
      "TTL": 60,
      "ResourceRecords": [{"Value": "\"'"$TXT_VALUE"'\""}]
    }
  }]
}'

# Wait for propagation (check from CA's resolvers)
dig +short _acme-challenge.example.com TXT @8.8.8.8
```

**Security Model:**
- **Proves DNS control** (required for wildcards)
- **Works behind firewall** (no inbound ports)
- **Vulnerable to DNS hijacking** → use DNSSEC or CAA with `validationmethods`

**DNS-01 for Wildcard + Apex:**
```bash
# Order for example.com + *.example.com requires 1 authz (same base domain)
# BUT Let's Encrypt validates both:
_acme-challenge.example.com TXT "<digest>"  # for both identifiers
```

**Production DNS Providers with APIs:**
- Cloudflare API, Route53, Google Cloud DNS, Azure DNS
- cert-manager supports 20+ DNS providers via plugins

---

#### **Challenge Type 3: TLS-ALPN-01**

**How It Works:**
1. Client receives `token`
2. Client generates self-signed cert with:
   - SAN = domain being validated
   - Extension `1.3.6.1.5.5.7.1.31` (id-pe-acmeIdentifier) containing `key-authorization`
3. Client serves cert on port 443 with ALPN protocol `acme-tls/1`
4. CA connects via TLS, validates ALPN + extension

**Example (Go):**
```go
package main

import (
    "crypto/rand"
    "crypto/rsa"
    "crypto/sha256"
    "crypto/tls"
    "crypto/x509"
    "crypto/x509/pkix"
    "encoding/asn1"
    "math/big"
    "time"
)

// ACME TLS-ALPN-01 extension OID
var oidPeAcmeIdentifier = asn1.ObjectIdentifier{1, 3, 6, 1, 5, 5, 7, 1, 31}

func tlsAlpn01Cert(domain, keyAuth string) (tls.Certificate, error) {
    priv, _ := rsa.GenerateKey(rand.Reader, 2048)
    
    // SHA256 digest of key authorization
    digest := sha256.Sum256([]byte(keyAuth))
    
    // ASN.1 encode digest
    extValue, _ := asn1.Marshal(digest[:])
    
    template := &x509.Certificate{
        SerialNumber: big.NewInt(1),
        Subject:      pkix.Name{CommonName: domain},
        DNSNames:     []string{domain},
        NotBefore:    time.Now(),
        NotAfter:     time.Now().Add(24 * time.Hour),
        KeyUsage:     x509.KeyUsageDigitalSignature,
        ExtKeyUsage:  []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth},
        ExtraExtensions: []pkix.Extension{{
            Id:       oidPeAcmeIdentifier,
            Critical: true,
            Value:    extValue,
        }},
    }
    
    certDER, _ := x509.CreateCertificate(rand.Reader, template, template, &priv.PublicKey, priv)
    return tls.Certificate{
        Certificate: [][]byte{certDER},
        PrivateKey:  priv,
    }, nil
}

func main() {
    cert, _ := tlsAlpn01Cert("example.com", "token.thumbprint")
    
    cfg := &tls.Config{
        Certificates: []tls.Certificate{cert},
        NextProtos:   []string{"acme-tls/1"},
    }
    
    ln, _ := tls.Listen("tcp", ":443", cfg)
    defer ln.Close()
    
    for {
        conn, _ := ln.Accept()
        conn.Close() // CA just needs TLS handshake
    }
}
```

**Use Cases:**
- HTTPS-only servers (HSTS preloaded)
- Port 80 blocked by firewall
- CDN/reverse proxy doesn't support HTTP-01

**Security:**
- More complex than HTTP-01 (requires TLS manipulation)
- Vulnerable to BGP hijacking (multi-VA mitigates)

---

### 2.4 Order Finalization (CSR Submission)

**CSR Generation:**
```bash
# Generate private key (RSA 2048 or ECDSA P-256)
openssl ecparam -name prime256v1 -genkey -noout -out domain.key

# Create CSR with SANs
openssl req -new -key domain.key -out domain.csr -subj "/CN=example.com" \
  -addext "subjectAltName=DNS:example.com,DNS:www.example.com"

# Convert to DER for ACME
openssl req -in domain.csr -outform DER -out domain.csr.der
```

**Finalize Request:**
```json
POST /acme/order/xyz789/finalize
{
  "protected": "base64url({...})",
  "payload": "base64url({
    \"csr\": \"<base64url(domain.csr.der)>\"
  })",
  "signature": "..."
}
```

**Server Validation:**
- CSR public key ≠ account key (prevents self-signing)
- All SANs in CSR were authorized
- CSR signature valid
- Key meets CA policy (min 2048-bit RSA, P-256/P-384/P-521 ECDSA)

**Certificate Issuance:**
```json
{
  "status": "valid",
  "expires": "2026-02-13T10:00:00Z",
  "certificate": "https://acme-v02.api.letsencrypt.org/acme/cert/abc123"
}
```

**Download Certificate:**
```bash
# POST-as-GET (empty signed payload)
curl -X POST https://acme-v02.api.letsencrypt.org/acme/cert/abc123 \
  -H "Content-Type: application/jose+json" \
  --data '{"protected":"...","payload":"","signature":"..."}'

# Response (PEM chain)
-----BEGIN CERTIFICATE-----
MIIFXzCCBEegAwIBAgISA... (leaf cert)
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
MIIFFjCCAv6gAwIBAgIRAJ... (intermediate R3)
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
MIIFYDCCBEigAwIBAgIQQAF... (root ISRG Root X1)
-----END CERTIFICATE-----
```

---

## 3. Security Deep-Dive

### 3.1 JWS (JSON Web Signature) & Replay Protection

**Every ACME request is JWS-signed:**
```json
{
  "protected": "base64url({
    \"alg\": \"ES256\",
    \"kid\": \"https://acme-v02.api.letsencrypt.org/acme/acct/123\",
    \"nonce\": \"oFvnlFP1wIhRlYS2jTaXbA\",
    \"url\": \"https://acme-v02.api.letsencrypt.org/acme/new-order\"
  })",
  "payload": "base64url({...})",
  "signature": "base64url(ECDSA-SHA256(protected || '.' || payload))"
}
```

**Nonce Mechanism (Anti-Replay):**
1. Client fetches fresh nonce: `HEAD /acme/new-nonce` → `Replay-Nonce: xyz`
2. Client includes nonce in `protected` header
3. Server validates:
   - Nonce exists in Redis (TTL 60s)
   - Nonce not previously used
   - Deletes nonce after use (single-use token)
4. Response includes new nonce in `Replay-Nonce` header

**Attack Mitigation:**
- **Replay attack:** Nonce prevents re-sending captured requests
- **MITM:** TLS 1.2+ required, signature binds request to account key
- **Key substitution:** `kid` header (vs `jwk`) prevents attacker swapping keys

---

### 3.2 Multi-Perspective Validation (Multi-VA)

**Problem:** BGP hijacking can redirect validation traffic to attacker.

**Let's Encrypt Multi-VA (since 2020):**
- Primary VA in us-east-1
- Secondary VAs in us-west-2, eu-central-1, ap-southeast-1
- **Quorum:** 2/4 validators must succeed

**Implementation (Boulder VA):**
```
┌──────────────────────────────────────────────┐
│ Challenge Validation Request                 │
│ (authz ID, challenge type)                   │
└─────────────────┬────────────────────────────┘
                  │
      ┌───────────┴───────────┐
      │  Primary VA (VA1)     │
      │  us-east-1            │
      └───────────┬───────────┘
                  │ RPC → Remote VAs
      ┌───────────┴──────────────────────────┐
      │  VA2        VA3          VA4         │
      │  us-west-2  eu-central-1 ap-se-1     │
      └───────────┬──────────────────────────┘
                  │
                  │ All perform:
                  │ • DNS lookup (recursive from diff resolvers)
                  │ • HTTP GET / TLS handshake
                  │ • Response validation
                  │
      ┌───────────┴──────────────────────────┐
      │  Quorum Logic                        │
      │  If ≥2 VAs return valid → Success    │
      │  Else → Fail                         │
      └──────────────────────────────────────┘
```

**DNSSEC Validation (DNS-01):**
- Some CAs validate DNSSEC chain (if domain has DNSSEC)
- Prevents DNS spoofing via cache poisoning

---

### 3.3 CAA (Certificate Authority Authorization)

**RFC 8659:** DNS record restricting which CAs can issue certs.

**CAA Record Check:**
```bash
# CA must check CAA before issuance
dig CAA example.com +short
0 issue "letsencrypt.org"
0 issuewild "letsencrypt.org"
0 iodef "mailto:security@example.com"

# Wildcard cert requires 'issuewild' or 'issue'
# If no CAA → any CA can issue
# If CAA exists without CA → issuance blocked
```

**CAA Validation Methods (RFC 8657):**
```
0 issue "letsencrypt.org; validationmethods=dns-01"
```
Forces DNS-01 (prevents HTTP-01 downgrade attack).

**Tree Climbing:**
If `_acme-challenge.sub.example.com` has no CAA, CA checks:
1. `sub.example.com`
2. `example.com`
3. Stop at first CAA (or TLD)

---

### 3.4 Certificate Transparency (CT)

**All public CAs submit certs to CT logs (RFC 6962):**
```
CA issues cert → submits to ≥2 CT logs → 
logs return Signed Certificate Timestamp (SCT) → 
CA embeds SCT in cert (or TLS extension)
```

**Benefits:**
- Detect mis-issuance (crt.sh, Censys)
- Revocation monitoring
- Compliance (Chrome requires CT for trust)

**ACME + CT:**
Let's Encrypt auto-submits to Google Argon, Cloudflare Nimbus, etc.

---

## 4. Production Deployment Patterns

### 4.1 Kubernetes cert-manager

**Architecture:**
```
┌─────────────────────────────────────────────────┐
│ Kubernetes Cluster                              │
│                                                 │
│ ┌─────────────────────────────────────────────┐ │
│ │ cert-manager (Deployment)                   │ │
│ │ • Controller watches Certificate CRDs       │ │
│ │ • Manages ACME Orders/Challenges            │ │
│ │ • Renews 30d before expiry                  │ │
│ └──────────────┬──────────────────────────────┘ │
│                │                                 │
│ ┌──────────────┴──────────────────────────────┐ │
│ │ Certificate (CRD)                           │ │
│ │ apiVersion: cert-manager.io/v1              │ │
│ │ kind: Certificate                           │ │
│ │ spec:                                       │ │
│ │   secretName: tls-secret                    │ │
│ │   dnsNames: [example.com, www.example.com]  │ │
│ │   issuerRef:                                │ │
│ │     name: letsencrypt-prod                  │ │
│ └──────────────┬──────────────────────────────┘ │
│                │                                 │
│ ┌──────────────┴──────────────────────────────┐ │
│ │ ClusterIssuer (CRD)                         │ │
│ │ spec:                                       │ │
│ │   acme:                                     │ │
│ │     server: https://acme-v02.api...         │ │
│ │     email: admin@example.com                │ │
│ │     privateKeySecretRef: {name: acme-key}   │ │
│ │     solvers:                                │ │
│ │     - dns01:                                │ │
│ │         route53: {region: us-east-1}        │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ ┌─────────────────────────────────────────────┐ │
│ │ Secret (tls-secret)                         │ │
│ │ type: kubernetes.io/tls                     │ │
│ │ data:                                       │ │
│ │   tls.crt: <PEM cert>                       │ │
│ │   tls.key: <PEM private key>                │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ ┌─────────────────────────────────────────────┐ │
│ │ Ingress (uses Secret)                       │ │
│ │ spec:                                       │ │
│ │   tls:                                      │ │
│ │   - hosts: [example.com]                    │ │
│ │     secretName: tls-secret                  │ │
│ └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

**Installation:**
```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.0/cert-manager.yaml

# Verify
kubectl get pods -n cert-manager
# cert-manager-<hash>          1/1  Running
# cert-manager-cainjector-...  1/1  Running
# cert-manager-webhook-...     1/1  Running
```

**ClusterIssuer (DNS-01 with Route53):**
```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: security@example.com
    privateKeySecretRef:
      name: letsencrypt-prod-account-key
    solvers:
    - dns01:
        route53:
          region: us-east-1
          accessKeyIDSecretRef:
            name: route53-credentials
            key: access-key-id
          secretAccessKeySecretRef:
            name: route53-credentials
            key: secret-access-key
```

**Certificate Resource:**
```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: example-tls
  namespace: default
spec:
  secretName: example-tls-secret
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - example.com
  - "*.example.com"
  privateKey:
    algorithm: ECDSA
    size: 256
  duration: 2160h  # 90d
  renewBefore: 720h  # 30d before expiry
```

**Challenge Flow:**
```bash
# 1. cert-manager creates Order
kubectl get orders -n default
# example-tls-1234567890  pending

# 2. Creates Challenge
kubectl get challenges -n default
# example-tls-1234567890-dns  pending

# 3. Challenge creates DNS record (via Route53)
dig _acme-challenge.example.com TXT
# "AbCd1234..."

# 4. Notifies ACME server
kubectl describe challenge example-tls-1234567890-dns
# Status: valid

# 5. Downloads cert → stores in Secret
kubectl get secret example-tls-secret -o yaml
# data:
#   tls.crt: LS0tLS1CRUdJTi...
#   tls.key: LS0tLS1CRUdJTi...
```

---

### 4.2 Caddy Server (Zero-Config TLS)

**Caddy automatically obtains/renews certs:**
```
Caddyfile:
example.com {
    reverse_proxy localhost:8080
}
```

**Under the hood:**
1. Caddy detects `example.com` in config
2. Checks `/var/lib/caddy/.local/share/caddy/certificates/acme-v02.api.letsencrypt.org-directory/`
3. If no cert or <30d remaining → starts ACME
4. Uses HTTP-01 by default (serves on :80)
5. Stores cert in `$CADDY_DATA_DIR`
6. Auto-renews every 24h (checks expiry)

**Production Caddyfile (DNS-01):**
```
{
    email security@example.com
    acme_dns route53 {
        access_key_id {env.AWS_ACCESS_KEY_ID}
        secret_access_key {env.AWS_SECRET_ACCESS_KEY}
    }
}

*.example.com, example.com {
    tls {
        dns route53
    }
    reverse_proxy backend:8080
}
```

**Monitoring:**
```bash
# Check cert expiry
echo | openssl s_client -connect example.com:443 2>/dev/null | \
  openssl x509 -noout -enddate
# notAfter=May  7 12:34:56 2026 GMT

# Caddy logs
journalctl -u caddy -f
# certificate obtained successfully
```

---

### 4.3 Traefik (Dynamic TLS)

**Traefik configuration:**
```yaml
# traefik.yml
certificatesResolvers:
  letsencrypt:
    acme:
      email: security@example.com
      storage: /letsencrypt/acme.json
      dnsChallenge:
        provider: cloudflare
        resolvers:
        - "1.1.1.1:53"
        - "8.8.8.8:53"

# docker-compose.yml
services:
  traefik:
    image: traefik:v2.11
    command:
      - --providers.docker=true
      - --certificatesresolvers.letsencrypt.acme.dnschallenge.provider=cloudflare
    environment:
      CF_API_EMAIL: admin@example.com
      CF_API_KEY: <api-key>
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./letsencrypt:/letsencrypt

  app:
    image: myapp:latest
    labels:
      - "traefik.http.routers.app.rule=Host(`example.com`)"
      - "traefik.http.routers.app.tls.certresolver=letsencrypt"
```

---

## 5. Threat Modeling & Mitigations

### 5.1 Attack Surface

| Attack Vector | Impact | Mitigation |
|--------------|--------|-----------|
| **DNS Hijacking** | Attacker gets cert for your domain via DNS-01 | DNSSEC, CAA records, monitor CT logs |
| **BGP Hijacking** | Redirect HTTP-01/TLS-ALPN-01 validation | Multi-VA (Let's Encrypt does 4 perspectives) |
| **Account Key Compromise** | Attacker can issue/revoke your certs | Rotate account key, revoke certs, use EAB |
| **Certificate Key Compromise** | TLS MITM until expiry | Short-lived certs (90d), OCSP Must-Staple, revoke via API |
| **CA Compromise** | Mass mis-issuance | CT logs detect, browser distrust CA (DigiNotar 2011) |
| **Replay Attack** | Reuse old ACME requests | Nonce mechanism (60s TTL, single-use) |
| **Subdomain Takeover** | Attacker proves control via dangling DNS | Monitor DNS, delete unused records |

---

### 5.2 Defense-in-Depth Checklist

**Pre-Issuance:**
- [ ] CAA records with `validationmethods=dns-01` (if using DNS-01)
- [ ] DNSSEC on domain (prevents DNS spoofing)
- [ ] Restrict DNS API credentials (IAM role for Route53, not root key)
- [ ] Monitor account key usage (alert on unknown IPs)

**Post-Issuance:**
- [ ] Pin intermediate CA in code (detect CA compromise)
- [ ] Enable OCSP Must-Staple in CSR (`status_request` extension)
- [ ] CT log monitoring (crt.sh API, Facebook CT Monitor)
- [ ] Automated revocation on key compromise (`POST /acme/revoke-cert`)

**Operational:**
- [ ] Renew at 2/3 lifetime (60d for 90d certs)
- [ ] Redundant ACME clients (cert-manager + backup cron)
- [ ] Test revocation procedure (pre-stage revoke requests)
- [ ] Rate limit awareness (Let's Encrypt: 50 certs/week/domain)

---

## 6. Testing & Validation

### 6.1 Local ACME Server (Pebble)

**Pebble = Let's Encrypt test server:**
```bash
# Start Pebble
docker run -d -p 14000:14000 -p 15000:15000 \
  letsencrypt/pebble:latest \
  pebble -config /test/config/pebble-config.json

# Point certbot to Pebble
certbot certonly --standalone \
  --server https://localhost:14000/dir \
  --no-verify-ssl \
  -d test.example.com

# Pebble features:
# • No rate limits
# • Instant issuance
# • Invalid nonces every 5th request (tests retry logic)
# • Random VA failures (tests quorum)
```

---

### 6.2 Challenge Simulation

**HTTP-01 Test:**
```bash
# Simulate CA validation
TOKEN="abc123"
KEY_AUTH="abc123.thumbprint"

# Server side
python3 -m http.server 5002 --directory /tmp/acme-challenge &

# Client side
mkdir -p /tmp/acme-challenge/.well-known/acme-challenge
echo "$KEY_AUTH" > /tmp/acme-challenge/.well-known/acme-challenge/$TOKEN

# Test from "CA"
curl http://localhost:5002/.well-known/acme-challenge/$TOKEN
# Should return: abc123.thumbprint
```

**DNS-01 Test:**
```bash
# Set up local DNS server (CoreDNS)
# Corefile
.:5053 {
    file /etc/coredns/db.example.com example.com
}

# db.example.com
$ORIGIN example.com.
@   IN SOA  ns1 admin 2024020601 3600 1800 604800 86400
@   IN NS   ns1
_acme-challenge IN TXT "base64url-digest"

# Start CoreDNS
coredns -conf Corefile &

# Test
dig @localhost -p 5053 _acme-challenge.example.com TXT +short
# "base64url-digest"
```

---

### 6.3 Fuzzing ACME Client

**Fuzz JWS Parsing:**
```go
// fuzz_jws_test.go
package acme

import (
    "testing"
)

func FuzzJWSVerify(f *testing.F) {
    f.Add([]byte(`{"protected":"...","payload":"...","signature":"..."}`))
    
    f.Fuzz(func(t *testing.T, data []byte) {
        var jws JWS
        _ = json.Unmarshal(data, &jws)
        // Should not panic
        _ = jws.Verify(accountPubKey)
    })
}

// Run fuzzer
// go test -fuzz=FuzzJWSVerify -fuzztime=30s
```

---

## 7. Rollout & Rollback

### 7.1 Staged ACME Migration

**Phase 1: Staging Environment (Week 1-2)**
```bash
# Test against Let's Encrypt staging
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-staging
spec:
  acme:
    server: https://acme-staging-v02.api.letsencrypt.org/directory
    email: security@example.com
    privateKeySecretRef:
      name: letsencrypt-staging-key
    solvers:
    - dns01:
        route53: {region: us-east-1}
EOF

# Verify staging cert
kubectl get cert -n staging
# Check CT logs (won't appear, staging certs not logged)
```

**Phase 2: Canary (Week 3)**
```yaml
# Single non-critical subdomain
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: canary-tls
spec:
  secretName: canary-tls
  issuerRef:
    name: letsencrypt-prod  # Production!
  dnsNames:
  - canary.example.com
```

**Phase 3: Production Rollout (Week 4+)**
```bash
# Bulk convert
for cert in $(kubectl get cert -o name); do
  kubectl patch $cert --type merge -p '{"spec":{"issuerRef":{"name":"letsencrypt-prod"}}}'
done

# Monitor renewal
kubectl get cert --watch
```

**Rollback Plan:**
```bash
# Emergency: Revert to manual certs
kubectl create secret tls emergency-tls \
  --cert=/path/to/backup.crt \
  --key=/path/to/backup.key

kubectl patch ingress myapp --type merge -p '{
  "spec": {"tls": [{"secretName": "emergency-tls"}]}
}'
```

---

### 7.2 Monitoring & Alerts

**Prometheus Metrics (cert-manager):**
```yaml
# ServiceMonitor
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: cert-manager
spec:
  selector:
    matchLabels:
      app: cert-manager
  endpoints:
  - port: tcp-prometheus

# Alerting rules
groups:
- name: acme
  rules:
  - alert: CertificateRenewalFailed
    expr: certmanager_certificate_ready_status{condition="False"} == 1
    for: 1h
    annotations:
      summary: "Certificate {{ $labels.name }} renewal failed"
  
  - alert: CertificateExpiringSoon
    expr: (certmanager_certificate_expiration_timestamp_seconds - time()) < 604800
    annotations:
      summary: "Certificate {{ $labels.name }} expires in <7 days"
```

**Custom Exporter (Go):**
```go
package main

import (
    "crypto/tls"
    "net/http"
    "time"
    "github.com/prometheus/client_golang/prometheus"
)

var certExpiry = prometheus.NewGaugeVec(
    prometheus.GaugeOpts{
        Name: "tls_cert_expiry_seconds",
        Help: "Seconds until certificate expiry",
    },
    []string{"domain"},
)

func checkCert(domain string) {
    conn, _ := tls.Dial("tcp", domain+":443", &tls.Config{})
    defer conn.Close()
    
    expiry := conn.ConnectionState().PeerCertificates[0].NotAfter
    certExpiry.WithLabelValues(domain).Set(float64(time.Until(expiry).Seconds()))
}

func main() {
    prometheus.MustRegister(certExpiry)
    
    go func() {
        for range time.Tick(1 * time.Hour) {
            checkCert("example.com")
        }
    }()
    
    http.Handle("/metrics", promhttp.Handler())
    http.ListenAndServe(":9090", nil)
}
```

---

## 8. References & Further Reading

**RFCs:**
- RFC 8555: ACME Protocol
- RFC 8737: ACME TLS-ALPN-01
- RFC 8659: CAA with ACME
- RFC 6962: Certificate Transparency

**Production Implementations:**
- Let's Encrypt Boulder: https://github.com/letsencrypt/boulder
- cert-manager: https://cert-manager.io/docs/
- Caddy ACME: https://caddyserver.com/docs/automatic-https
- lego (Go library): https://github.com/go-acme/lego

**Security Research:**
- "The Web's Identity Crisis" (Princeton): https://www.ndss-symposium.org/wp-content/uploads/2020/02/24303.pdf
- Let's Encrypt Multi-VA: https://letsencrypt.org/2020/02/19/multi-perspective-validation.html

**Monitoring:**
- crt.sh (CT log search): https://crt.sh
- Facebook CT Monitor: https://github.com/facebook/certificate-transparency-monitoring

---

## Next 3 Steps

1. **Deploy Pebble locally** → test full ACME flow with HTTP-01/DNS-01 challenges (validate JWS signing, nonce handling, multi-VA).

2. **Instrument cert-manager in staging K8s** → configure Route53 DNS-01, enable Prometheus metrics, set up alerting for renewal failures + expiry <7d.

3. **Build custom ACME client in Go/Rust** → implement account creation, order flow, DNS-01 challenge, CSR finalization; fuzz JWS parser; compare performance vs certbot/lego.