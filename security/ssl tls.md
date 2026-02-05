# SSL/TLS Comprehensive Deep-Dive: Cryptographic Transport Security from First Principles

**SUMMARY:** SSL/TLS provides authenticated, encrypted, integrity-protected communication channels over untrusted networks through asymmetric handshake → symmetric session encryption. Works at L4 (TCP) or L5 (session), securing HTTP→HTTPS, SMTP→SMTPS, LDAP→LDAPS, database connections, service mesh sidecars, and mTLS-authenticated microservices. Core: X.509 PKI for identity, ECDHE for forward secrecy, AEAD ciphers (AES-GCM, ChaCha20-Poly1305) for confidentiality+integrity, certificate chain validation for trust. Modern deployment: TLS 1.3 removes legacy crypto, reduces handshake RTT (0-RTT resumption), mandates perfect forward secrecy. Critical for zero-trust architectures, data-in-transit encryption compliance (PCI-DSS, HIPAA, SOC2), and preventing MITM/eavesdropping/tampering attacks.

---

## 1. FOUNDATIONAL ARCHITECTURE & PROTOCOL STACK PLACEMENT

### Where TLS Operates in the Network Stack

```
┌─────────────────────────────────────────────────────────────┐
│ L7: Application (HTTP, gRPC, SMTP, LDAP, PostgreSQL, etc.) │
├─────────────────────────────────────────────────────────────┤
│ L6/5: TLS/SSL (Presentation/Session Layer)                  │
│   ┌──────────────────────────────────────────────────────┐  │
│   │ TLS Record Protocol (fragmentation, compression*)    │  │
│   ├──────────────────────────────────────────────────────┤  │
│   │ TLS Handshake | Alert | ChangeCipherSpec | AppData  │  │
│   └──────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│ L4: TCP (reliable byte stream, flow control, retransmit)   │
│     or QUIC (UDP-based TLS 1.3 integrated transport)       │
├─────────────────────────────────────────────────────────────┤
│ L3: IP (routing, addressing)                                │
├─────────────────────────────────────────────────────────────┤
│ L2: Ethernet/WiFi (framing, MAC addressing)                 │
├─────────────────────────────────────────────────────────────┤
│ L1: Physical (cables, radio, fiber)                         │
└─────────────────────────────────────────────────────────────┘

*compression removed in TLS 1.3 due to CRIME/BREACH attacks
```

**Key Placement Implications:**
- **Above TCP:** TLS inherits TCP's reliability, ordering, flow control
- **Below Application:** Transparent to apps (sockets become SSL_CTX)
- **Not Network-Layer:** Unlike IPsec (L3), TLS is hop-by-hop, not end-to-end at IP level
- **QUIC Exception:** TLS 1.3 integrated into QUIC transport (UDP-based)

### TLS Deployment Patterns

```
┌──────────────────────────────────────────────────────────────┐
│ 1. EDGE TERMINATION (CDN, Load Balancer)                     │
│    Client ──TLS──> LB ──plaintext──> Backend                 │
│    • Offload crypto from backends                            │
│    • Risk: plaintext in internal network                     │
│    • Mitigation: VPC isolation, IPsec tunnels, mTLS mesh     │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ 2. END-TO-END (Zero-Trust, mTLS)                             │
│    Client ──TLS──> LB ──TLS──> Pod ──mTLS──> Backend        │
│    • Full path encryption                                    │
│    • Defense-in-depth: breach of LB doesn't expose traffic   │
│    • Service mesh (Istio/Linkerd): sidecar proxies          │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ 3. PASSTHROUGH (SNI Routing)                                 │
│    Client ──TLS──> L4 LB (SNI peek) ──TLS──> Backend        │
│    • LB routes on SNI without decryption                     │
│    • Backend holds private keys                              │
│    • Use case: multi-tenant SaaS, regulatory key custody     │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. CRYPTOGRAPHIC PRIMITIVES: THE BUILDING BLOCKS

### Symmetric Encryption (Session Keys)

**AES-GCM (Authenticated Encryption with Associated Data):**
- **Algorithm:** AES block cipher (128/256-bit key) + Galois Counter Mode
- **Operation:** 
  ```
  Ciphertext = AES_CTR(Key, Nonce, Plaintext)
  Tag = GHASH(Key, AAD || Ciphertext)
  Output = Ciphertext || Tag
  ```
- **Properties:**
  - **Confidentiality:** AES-CTR stream cipher
  - **Integrity:** GHASH authentication tag (prevents tampering)
  - **Performance:** HW acceleration (AES-NI on x86, ARMv8 crypto extensions)
- **Nonce Requirement:** MUST be unique per message (12 bytes for GCM)

**ChaCha20-Poly1305 (Alternative AEAD):**
- **Use Case:** Mobile devices without AES-NI, ARM Cortex-A series
- **Algorithm:** ChaCha20 stream cipher + Poly1305 MAC
- **Advantage:** Constant-time SW implementation (side-channel resistant)

**Avoid:** CBC mode (padding oracle attacks: BEAST, POODLE), RC4 (biases)

### Asymmetric Cryptography (Key Exchange & Signatures)

**RSA (Rivest-Shamir-Adleman):**
- **Key Exchange (deprecated in TLS 1.3):**
  - Client encrypts pre-master secret with server's RSA public key
  - **NO forward secrecy:** compromised private key decrypts all past sessions
- **Signature (certificate validation):**
  - Server signs handshake transcript with RSA private key
  - 2048-bit minimum (NIST), 3072-bit recommended, 4096-bit for long-term

**ECDHE (Elliptic Curve Diffie-Hellman Ephemeral):**
- **Curves:** P-256 (NIST), P-384, X25519 (Curve25519, preferred)
- **Protocol:**
  ```
  Server: generates ephemeral keypair (a, G^a)
  Client: generates ephemeral keypair (b, G^b)
  Shared Secret = (G^a)^b = (G^b)^a = G^(ab)
  Session Keys = HKDF(shared_secret, handshake_hash)
  ```
- **Forward Secrecy:** ephemeral keys discarded post-handshake
- **Performance:** X25519 faster than P-256, constant-time implementations available

**ECDSA vs RSA Signatures:**
- **ECDSA:** Smaller keys (256-bit ECDSA ≈ 3072-bit RSA), faster signing
- **EdDSA (Ed25519):** Deterministic, no nonce reuse risk, faster verification

### Hash Functions & KDFs

**SHA-256/384 (Secure Hash Algorithm):**
- **Use:** Certificate fingerprints, HMAC, transcript hashing
- **Output:** 256-bit (SHA-256), 384-bit (SHA-384)
- **Avoid:** SHA-1 (collision attacks: SHAttered), MD5 (broken)

**HKDF (HMAC-based Key Derivation Function):**
- **TLS 1.3 Key Schedule:**
  ```
  Early Secret = HKDF-Extract(0, PSK)
  Handshake Secret = HKDF-Extract(Early Secret, ECDHE_shared_secret)
  Master Secret = HKDF-Extract(Handshake Secret, 0)
  
  client_write_key = HKDF-Expand-Label(Master Secret, "client key")
  server_write_key = HKDF-Expand-Label(Master Secret, "server key")
  client_write_iv = HKDF-Expand-Label(Master Secret, "client iv")
  server_write_iv = HKDF-Expand-Label(Master Secret, "server iv")
  ```

---

## 3. TLS 1.2 vs TLS 1.3 HANDSHAKE DEEP-DIVE

### TLS 1.2 Full Handshake (2-RTT)

```
Client                                               Server

ClientHello
  + version (TLS 1.2)
  + random (32 bytes)
  + session_id
  + cipher_suites (list)
  + extensions (SNI, ALPN, etc.)
                          ────────────────────────>
                                                 ServerHello
                                                   + random
                                                   + cipher_suite (chosen)
                                                   + session_id
                                                 Certificate
                                                   + X.509 chain
                                                 ServerKeyExchange (ECDHE params)
                                                   + curve, public_key, signature
                                                 CertificateRequest (optional mTLS)
                                                 ServerHelloDone
                          <────────────────────────
Certificate (if requested)
ClientKeyExchange
  + ECDHE public_key
CertificateVerify (if client cert sent)
  + signature over handshake hash
[ChangeCipherSpec]
Finished (encrypted with session keys)
  + verify_data = PRF(master_secret, "client finished", handshake_hash)
                          ────────────────────────>
                                                 [ChangeCipherSpec]
                                                 Finished (encrypted)
                          <────────────────────────

Application Data (encrypted)
                          <═══════════════════════>
```

**Key Operations:**
1. **Client → Server:** Propose ciphers, send random nonce
2. **Server → Client:** Choose cipher, send cert chain, ECDHE params signed with cert key
3. **Client:** Validate cert chain → ECDHE shared secret → derive session keys
4. **Both:** Switch to encrypted channel, verify Finished messages

**Weaknesses:**
- **2-RTT latency:** handshake before application data
- **Cipher suite negotiation complexity:** CBC/GCM, RSA/ECDHE combinations
- **Downgrade attacks:** version/cipher downgrade (POODLE, FREAK)

### TLS 1.3 Handshake (1-RTT, 0-RTT Resumption)

```
Client                                               Server

ClientHello
  + version (TLS 1.3)
  + random
  + cipher_suites (only AEAD)
  + key_share (ECDHE public keys for X25519, P-256)
  + signature_algorithms
  + psk_key_exchange_modes (for 0-RTT)
  + pre_shared_key (if resuming)
                          ────────────────────────>
                                                 ServerHello
                                                   + key_share (chosen curve)
                                                   + pre_shared_key (if resuming)
                                                 {EncryptedExtensions}
                                                 {Certificate}
                                                 {CertificateVerify}
                                                 {Finished}
                          <────────────────────────
{Certificate} (if mTLS)
{CertificateVerify}
{Finished}
                          ────────────────────────>
[Application Data]        ═══════════════════════> [Application Data]
```

**{ } = encrypted with handshake traffic keys**
**[ ] = encrypted with application traffic keys**

**1-RTT Handshake Changes:**
- **Client sends key_share in ClientHello:** Server can derive keys immediately
- **All post-ServerHello messages encrypted:** Certificate, extensions encrypted
- **No ChangeCipherSpec:** Removed, implicit key activation

**0-RTT Resumption (Session Tickets):**
```
[Previous Session]
Server → Client: NewSessionTicket
  + ticket (encrypted state: PSK, cipher, timeout)
  
[New Session]
ClientHello
  + early_data extension
  + pre_shared_key (ticket)
  + key_share (for 1-RTT fallback)
[Application Data] (encrypted with early_data_key)
                          ────────────────────────>
                                                 ServerHello
                                                   + pre_shared_key (accept/reject)
                          <────────────────────────
```

**0-RTT Risks:**
- **No forward secrecy for early data:** PSK compromise decrypts early data
- **Replay attacks:** Early data can be replayed if server doesn't track tickets
- **Mitigation:** 
  - Use for idempotent requests (GET, not POST/PUT)
  - Anti-replay: single-use tickets, client address binding, time windows

---

## 4. X.509 CERTIFICATE CHAIN VALIDATION

### Certificate Structure

```
Certificate:
    Data:
        Version: 3 (0x2)
        Serial Number: 0x4a:b2:3f:... (unique per CA)
        Signature Algorithm: sha256WithRSAEncryption
        Issuer: C=US, O=Let's Encrypt, CN=R3 (intermediate CA)
        Validity:
            Not Before: Jan  1 00:00:00 2025 UTC
            Not After : Apr  1 23:59:59 2025 UTC
        Subject: CN=example.com (server identity)
        Subject Public Key Info:
            Public Key Algorithm: id-ecPublicKey
                Public-Key: (256 bit)
                pub: 04:a3:... (X25519 or P-256 point)
                ASN1 OID: prime256v1
        X509v3 Extensions:
            X509v3 Subject Alternative Name: 
                DNS:example.com, DNS:*.example.com
            X509v3 Key Usage: critical
                Digital Signature, Key Encipherment
            X509v3 Extended Key Usage:
                TLS Web Server Authentication
            Authority Information Access:
                OCSP - URI:http://r3.o.lencr.org
            X509v3 CRL Distribution Points:
                Full Name: URI:http://r3.c.lencr.org/
    Signature Algorithm: sha256WithRSAEncryption
        Signature: 5a:3f:... (issuer's signature over tbsCertificate)
```

### Chain Validation Steps (RFC 5280)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. CHAIN BUILDING                                            │
│    Server Cert → Intermediate CA → Root CA (trust anchor)   │
│    - Server sends leaf + intermediates (not root)           │
│    - Client has root CA store (OS/browser trust store)      │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. SIGNATURE VERIFICATION (bottom-up)                        │
│    foreach cert in chain:                                    │
│      verify cert.signature using issuer.public_key           │
│      if issuer == root_ca: verify root is trusted           │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. VALIDITY PERIOD CHECK                                     │
│    current_time >= notBefore && current_time <= notAfter    │
│    - Reject expired certs                                    │
│    - Risk: time sync issues, cert renewal lag               │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. REVOCATION CHECK                                          │
│    CRL (Certificate Revocation List):                        │
│      - Download CRL from cert.crlDistributionPoints         │
│      - Check if cert.serialNumber in CRL                     │
│      - Slow, large files, caching issues                     │
│    OCSP (Online Certificate Status Protocol):               │
│      - Query OCSP responder: cert.authorityInfoAccess       │
│      - Response: good | revoked | unknown                    │
│      - Privacy leak: CA sees every site you visit            │
│    OCSP Stapling (TLS extension):                            │
│      - Server fetches OCSP response, sends with cert         │
│      - No client→CA connection, better privacy               │
│    OCSP Must-Staple (cert extension):                        │
│      - Cert requires OCSP stapling, reject if missing        │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. NAME VALIDATION (RFC 6125)                                │
│    Hostname matches cert.subjectAltName (SAN):               │
│      - Exact match: example.com                              │
│      - Wildcard: *.example.com (matches foo.example.com)     │
│      - NOT: *.*.example.com, *.com (limited to one level)   │
│    Legacy: cert.subject.commonName (deprecated)              │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. KEY USAGE / EXTENDED KEY USAGE                            │
│    cert.keyUsage: digitalSignature, keyEncipherment          │
│    cert.extKeyUsage: serverAuth (id-kp-serverAuth OID)       │
│    - Reject if cert not authorized for TLS server auth       │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. CONSTRAINTS (CA certs only)                               │
│    basicConstraints: CA:TRUE, pathLenConstraint:0            │
│    nameConstraints: permitted/excluded subtrees              │
│    - Prevent intermediate CA from issuing certs outside scope│
└─────────────────────────────────────────────────────────────┘
```

### Trust Store Management

**System Trust Stores:**
- **Linux:** `/etc/ssl/certs/ca-certificates.crt` (Debian/Ubuntu), `/etc/pki/tls/certs/ca-bundle.crt` (RHEL)
- **macOS:** Keychain Access → System Roots
- **Windows:** Certificate Manager (certmgr.msc) → Trusted Root CAs

**Application Trust Stores:**
- **Go:** `x509.SystemCertPool()` + custom `x509.CertPool`
- **OpenSSL:** `SSL_CTX_set_default_verify_paths()` or `SSL_CTX_load_verify_locations()`
- **Rust (rustls):** `webpki-roots` crate (Mozilla CA bundle)

**Custom CA (internal PKI, mTLS):**
```bash
# Add custom CA to system store (Ubuntu)
sudo cp internal-ca.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates

# Go: load custom CA
caCert, _ := os.ReadFile("internal-ca.crt")
caCertPool := x509.NewCertPool()
caCertPool.AppendCertsFromPEM(caCert)
tlsConfig := &tls.Config{RootCAs: caCertPool}
```

---

## 5. MUTUAL TLS (mTLS) FOR ZERO-TRUST

### mTLS Handshake Extension

```
Standard TLS:
  Server → Client: Certificate + CertificateVerify
  Client validates server identity

mTLS (TLS 1.3):
  Server → Client: CertificateRequest
    + signature_algorithms
    + certificate_authorities (acceptable CA DNs)
  Client → Server: Certificate + CertificateVerify
  Server validates client identity

Result: Bidirectional authentication
```

### Implementation Patterns

**1. Service Mesh (Istio, Linkerd, Consul Connect):**
```
┌──────────────────────────────────────────────────────────────┐
│ Pod A                                    Pod B                │
│ ┌────────┐  mTLS   ┌──────────┐  mTLS  ┌────────┐           │
│ │ App    │◄────────►│ Envoy    │◄───────►│ Envoy  │◄────► App│
│ └────────┘ localhost└──────────┘  mesh  └────────┘ localhost │
│                ▲                            ▲                 │
│                │ SPIFFE ID: spiffe://trust-domain/ns/sa      │
│                │ Cert lifetime: 1h, auto-rotation            │
│                └────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘

Envoy sidecar:
- Intercepts outbound traffic on iptables REDIRECT
- Presents client cert (SVID) issued by Istio CA (or Vault PKI)
- Validates server cert against trust bundle
- Enforces AuthorizationPolicy (L7 RBAC)
```

**2. SPIFFE/SPIRE (Identity Framework):**
```bash
# SPIRE agent provisions workload with X.509 SVID
# SVID (SPIFFE Verifiable Identity Document):
#   Subject: spiffe://example.com/ns/default/sa/backend
#   Issuer: SPIRE Server CA
#   Lifetime: 1 hour (short-lived)

# Workload attestation (k8s)
spire-server entry create \
  -spiffeID spiffe://example.com/ns/default/sa/backend \
  -parentID spiffe://example.com/spire/agent/k8s_psat/cluster1 \
  -selector k8s:ns:default \
  -selector k8s:sa:backend

# Go client: fetch SVID from Workload API (Unix socket)
source, _ := workloadapi.NewX509Source(ctx)
svid, _ := source.GetX509SVID()
tlsConfig := &tls.Config{
    Certificates: []tls.Certificate{svid},
    RootCAs:      source.GetX509BundleForTrustDomain(trustDomain),
}
```

**3. Certificate Rotation Strategies:**
```go
// Automatic cert reload (filesystem watch)
func watchCerts(certFile, keyFile string) (*tls.Config, error) {
    cert, err := tls.LoadX509KeyPair(certFile, keyFile)
    if err != nil {
        return nil, err
    }
    
    cfg := &tls.Config{
        GetCertificate: func(*tls.ClientHelloInfo) (*tls.Certificate, error) {
            // Reload cert on every handshake (or cache with TTL)
            cert, err := tls.LoadX509KeyPair(certFile, keyFile)
            return &cert, err
        },
    }
    return cfg, nil
}

// SPIFFE X509Source (polls Workload API)
source, _ := workloadapi.NewX509Source(ctx, workloadapi.WithClientOptions(
    workloadapi.WithAddr("unix:///run/spire/sockets/agent.sock"),
))
defer source.Close()

tlsConfig := tlsconfig.MTLSServerConfig(source, source, tlsconfig.AuthorizeAny())
```

---

## 6. CIPHER SUITE SELECTION & SECURITY

### TLS 1.3 Cipher Suites (Simplified)

```
TLS_AES_128_GCM_SHA256          (mandatory, fast, HW-accelerated)
TLS_AES_256_GCM_SHA384          (stronger key, slower)
TLS_CHACHA20_POLY1305_SHA256    (mobile, no AES-NI)

Removed from TLS 1.3:
- RSA key exchange (no forward secrecy)
- CBC mode (padding oracle attacks)
- Static DH (no forward secrecy)
- Export ciphers (FREAK, Logjam)
- RC4, 3DES, MD5, SHA-1
```

### TLS 1.2 Recommended Ciphers (Backward Compat)

```
Priority order (prefer ECDHE + AEAD):
1. TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
2. TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
3. TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
4. TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
5. TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256
6. TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256

Disable:
- NULL ciphers (no encryption)
- EXPORT ciphers (weak 40-56 bit keys)
- DES, 3DES (64-bit block size, Sweet32)
- RC4 (biases in keystream)
- MD5, SHA-1 in signatures
- CBC mode without encrypt-then-MAC extension
```

### OpenSSL Configuration

```bash
# TLS 1.3 only (modern)
openssl s_server -accept 443 -cert server.crt -key server.key \
  -tls1_3 -ciphersuites TLS_AES_128_GCM_SHA256:TLS_CHACHA20_POLY1305_SHA256

# TLS 1.2+ with strong ciphers
openssl s_server -accept 443 -cert server.crt -key server.key \
  -cipher 'ECDHE+AESGCM:ECDHE+CHACHA20:!aNULL:!MD5:!DSS' \
  -no_tls1 -no_tls1_1

# Test connection
openssl s_client -connect example.com:443 -tls1_3 -showcerts
```

### Go TLS Config (Production-Grade)

```go
package main

import (
    "crypto/tls"
    "crypto/x509"
    "os"
)

func secureTLSConfig(certFile, keyFile, caFile string) (*tls.Config, error) {
    // Load server cert/key
    cert, err := tls.LoadX509KeyPair(certFile, keyFile)
    if err != nil {
        return nil, err
    }

    // Load CA for client verification (mTLS)
    caCert, err := os.ReadFile(caFile)
    if err != nil {
        return nil, err
    }
    caCertPool := x509.NewCertPool()
    caCertPool.AppendCertsFromPEM(caCert)

    return &tls.Config{
        Certificates: []tls.Certificate{cert},
        ClientCAs:    caCertPool,
        ClientAuth:   tls.RequireAndVerifyClientCert, // mTLS enforcement
        
        MinVersion: tls.VersionTLS13, // Force TLS 1.3
        MaxVersion: tls.VersionTLS13,
        
        // TLS 1.3 cipher suites (optional, defaults are secure)
        CipherSuites: []uint16{
            tls.TLS_AES_128_GCM_SHA256,
            tls.TLS_CHACHA20_POLY1305_SHA256,
            tls.TLS_AES_256_GCM_SHA384,
        },
        
        // Curve preferences
        CurvePreferences: []tls.CurveID{
            tls.X25519, // Fastest, most secure
            tls.CurveP256,
        },
        
        // Disable session tickets for stricter security (no 0-RTT)
        SessionTicketsDisabled: true,
        
        // OCSP stapling
        // (Server must fetch OCSP response separately and set in GetCertificate)
        
    }, nil
}
```

---

## 7. THREAT MODEL & MITIGATIONS

```
┌─────────────────────────────────────────────────────────────────┐
│ THREAT: Man-in-the-Middle (MITM)                                │
│ ATTACK: Intercept ClientHello, present fake server certificate  │
│ MITIGATION:                                                      │
│   - Certificate chain validation (trust anchor)                 │
│   - HSTS (HTTP Strict Transport Security): force HTTPS          │
│   - Certificate Transparency (CT): detect rogue certs           │
│   - Public Key Pinning (deprecated, use CT instead)             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ THREAT: Eavesdropping (Passive Monitoring)                      │
│ ATTACK: Capture encrypted traffic, decrypt later if keys leak   │
│ MITIGATION:                                                      │
│   - Perfect Forward Secrecy (ECDHE): session keys ephemeral     │
│   - Disable RSA key exchange (no PFS)                           │
│   - Short session ticket lifetime (<24h)                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ THREAT: Downgrade Attacks (POODLE, FREAK, Logjam)               │
│ ATTACK: Force client/server to negotiate weak cipher/version    │
│ MITIGATION:                                                      │
│   - Disable SSLv3, TLS 1.0, TLS 1.1                             │
│   - TLS_FALLBACK_SCSV: prevent version downgrade                │
│   - Enforce TLS 1.3 only (removes legacy negotiation)           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ THREAT: Timing Attacks (Lucky 13, BEAST on CBC)                 │
│ ATTACK: Measure decryption time to infer plaintext bits         │
│ MITIGATION:                                                      │
│   - Use AEAD ciphers (GCM, ChaCha20-Poly1305)                   │
│   - Constant-time crypto implementations                        │
│   - Disable CBC mode                                            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ THREAT: Compression Attacks (CRIME, BREACH)                     │
│ ATTACK: Observe compressed size to leak secrets (cookies, CSRF) │
│ MITIGATION:                                                      │
│   - Disable TLS compression (removed in TLS 1.3)                │
│   - Disable HTTP compression for sensitive headers              │
│   - CSRF tokens: random, not secret-dependent                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ THREAT: Certificate Revocation Bypass                           │
│ ATTACK: Present revoked cert, client doesn't check CRL/OCSP     │
│ MITIGATION:                                                      │
│   - OCSP stapling (server provides fresh OCSP response)         │
│   - OCSP Must-Staple cert extension                             │
│   - CRLSets (Chrome), OneCRL (Firefox): pushed revocation lists │
│   - Short cert lifetimes (Let's Encrypt: 90 days)               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ THREAT: 0-RTT Replay Attacks                                    │
│ ATTACK: Replay ClientHello + early_data to execute duplicate req│
│ MITIGATION:                                                      │
│   - Use 0-RTT only for idempotent requests (GET, not POST)      │
│   - Anti-replay: track ClientHello.random in cache (Redis)      │
│   - Single-use session tickets                                  │
│   - Time-based replay window (5 min)                            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ THREAT: Weak Randomness (Debian OpenSSL 2008, Dual_EC_DRBG)     │
│ ATTACK: Predict session keys if RNG is weak/backdoored          │
│ MITIGATION:                                                      │
│   - Use /dev/urandom (Linux), getrandom() syscall               │
│   - Seed from hardware RNG (RDRAND on x86, if available)        │
│   - Go: crypto/rand.Reader (uses getrandom or /dev/urandom)     │
│   - Test: RNG output statistical tests (dieharder, NIST STS)    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ THREAT: Side-Channel Attacks (Cache Timing, Spectre)            │
│ ATTACK: Leak key bits via CPU cache/branch prediction           │
│ MITIGATION:                                                      │
│   - Constant-time crypto: BoringSSL, libsodium                  │
│   - Blinding for RSA operations                                 │
│   - Avoid secret-dependent branches/memory access               │
│   - Use ChaCha20 (no table lookups) over AES on non-AES-NI CPUs │
└─────────────────────────────────────────────────────────────────┘
```

### HSTS (HTTP Strict Transport Security)

```
HTTP Response Header:
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload

Effects:
1. Browser refuses HTTP, auto-upgrades to HTTPS
2. Rejects invalid certs (no click-through warning)
3. Lifetime: 1 year (31536000 sec)
4. Subdomains: applies to *.example.com
5. Preload: submit to browser HSTS preload list (Chrome, Firefox)

First-visit vulnerability:
- Initial HTTP request interceptable
- Mitigation: HSTS preload list (baked into browsers)
```

### Certificate Transparency (CT)

```
┌────────────────────────────────────────────────────────────────┐
│ CA issues cert → Log to public CT logs (Google, Cloudflare)    │
│ CT log returns Signed Certificate Timestamp (SCT)              │
│ Server presents SCT in TLS handshake (or embedded in cert)     │
│ Browser verifies SCT against known CT logs                     │
│ Monitors (crt.sh, Censys) watch logs for rogue certs           │
└────────────────────────────────────────────────────────────────┘

Deployment:
- Let's Encrypt, DigiCert: auto-submit to CT logs
- Self-signed/internal certs: no CT requirement
- Chrome: requires CT for public certs (since 2018)

Monitoring:
curl "https://crt.sh/?q=%.example.com&output=json" | jq .
```

---

## 8. PRACTICAL DEPLOYMENT SCENARIOS

### Scenario 1: Nginx Reverse Proxy (TLS Termination)

```nginx
# /etc/nginx/nginx.conf
http {
    # Mozilla Intermediate compatibility (TLS 1.2+)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305';
    ssl_prefer_server_ciphers on;
    
    # Diffie-Hellman parameter for DHE (if using DHE ciphers)
    ssl_dhparam /etc/nginx/dhparam.pem;
    
    # OCSP stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/nginx/chain.pem;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    
    # Session cache (10MB ~ 40k sessions)
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off; # Disable for PFS strictness
    
    server {
        listen 443 ssl http2;
        server_name example.com;
        
        ssl_certificate /etc/nginx/certs/example.com.crt;
        ssl_certificate_key /etc/nginx/certs/example.com.key;
        
        # HSTS (1 year)
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
        
        location / {
            proxy_pass http://backend:8080;
            proxy_set_header X-Forwarded-Proto https;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
    
    # Redirect HTTP to HTTPS
    server {
        listen 80;
        server_name example.com;
        return 301 https://$server_name$request_uri;
    }
}
```

**Generate DH params:**
```bash
openssl dhparam -out /etc/nginx/dhparam.pem 2048
```

**Test config:**
```bash
nginx -t
systemctl reload nginx

# SSL Labs test
https://www.ssllabs.com/ssltest/analyze.html?d=example.com

# Manual test
openssl s_client -connect example.com:443 -tls1_3 -status
```

### Scenario 2: Go HTTP Server (mTLS, SPIFFE)

```go
package main

import (
    "context"
    "crypto/tls"
    "crypto/x509"
    "log"
    "net/http"
    "github.com/spiffe/go-spiffe/v2/workloadapi"
    "github.com/spiffe/go-spiffe/v2/svid/x509svid"
    "github.com/spiffe/go-spiffe/v2/bundle/x509bundle"
)

func main() {
    ctx := context.Background()
    
    // Fetch X.509 SVID from SPIRE Workload API
    source, err := workloadapi.NewX509Source(ctx)
    if err != nil {
        log.Fatalf("Unable to create X509Source: %v", err)
    }
    defer source.Close()
    
    // Create mTLS server config
    tlsConfig := &tls.Config{
        MinVersion: tls.VersionTLS13,
        ClientAuth: tls.RequireAndVerifyClientCert,
        
        // GetCertificate: dynamic cert from SPIFFE source
        GetCertificate: func(*tls.ClientHelloInfo) (*tls.Certificate, error) {
            svid, err := source.GetX509SVID()
            if err != nil {
                return nil, err
            }
            return &svid.Certificates[0], nil
        },
        
        // GetClientCertificate: for client-side mTLS
        GetClientCertificate: func(*tls.CertificateRequestInfo) (*tls.Certificate, error) {
            svid, err := source.GetX509SVID()
            if err != nil {
                return nil, err
            }
            return &svid.Certificates[0], nil
        },
        
        // VerifyPeerCertificate: custom validation (SPIFFE ID authz)
        VerifyPeerCertificate: func(rawCerts [][]byte, verifiedChains [][]*x509.Certificate) error {
            if len(verifiedChains) == 0 {
                return x509.UnknownAuthorityError{}
            }
            cert := verifiedChains[0][0]
            
            // Extract SPIFFE ID from URI SAN
            if len(cert.URIs) == 0 {
                return x509.UnknownAuthorityError{}
            }
            spiffeID := cert.URIs[0].String()
            
            // Enforce SPIFFE ID allowlist
            allowed := []string{
                "spiffe://example.com/ns/default/sa/frontend",
                "spiffe://example.com/ns/default/sa/backend",
            }
            for _, id := range allowed {
                if spiffeID == id {
                    return nil
                }
            }
            return x509.UnknownAuthorityError{}
        },
        
        // ClientCAs: trust bundle from SPIFFE
        GetConfigForClient: func(*tls.ClientHelloInfo) (*tls.Config, error) {
            bundle := source.GetX509BundleForTrustDomain(source.GetX509SVID().ID.TrustDomain())
            return &tls.Config{ClientCAs: bundle.X509Authorities()}, nil
        },
    }
    
    // HTTP handler
    http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        // Extract client SPIFFE ID from TLS connection
        if r.TLS != nil && len(r.TLS.PeerCertificates) > 0 {
            clientCert := r.TLS.PeerCertificates[0]
            if len(clientCert.URIs) > 0 {
                log.Printf("Request from SPIFFE ID: %s", clientCert.URIs[0])
            }
        }
        w.Write([]byte("Hello mTLS\n"))
    })
    
    server := &http.Server{
        Addr:      ":8443",
        TLSConfig: tlsConfig,
    }
    
    log.Fatal(server.ListenAndServeTLS("", "")) // Cert from GetCertificate
}
```

**Test with curl + client cert:**
```bash
# Fetch SVID from SPIRE
spire-agent api fetch x509 -write /tmp/svid

# Test
curl --cacert /tmp/svid/bundle.0.pem \
     --cert /tmp/svid/svid.0.pem \
     --key /tmp/svid/svid.0.key \
     https://localhost:8443
```

### Scenario 3: Kubernetes Ingress (cert-manager, Let's Encrypt)

```yaml
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.0/cert-manager.yaml

# ClusterIssuer (Let's Encrypt ACME)
---
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-prod-key
    solvers:
    - http01:
        ingress:
          class: nginx

# Ingress with TLS
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: example-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-protocols: "TLSv1.3"
    nginx.ingress.kubernetes.io/ssl-ciphers: "TLS_AES_128_GCM_SHA256:TLS_CHACHA20_POLY1305_SHA256"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - example.com
    secretName: example-com-tls # cert-manager creates this Secret
  rules:
  - host: example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: backend
            port:
              number: 80
```

**Verify cert issuance:**
```bash
kubectl get certificate example-com-tls
kubectl describe certificaterequest

# Check cert in Secret
kubectl get secret example-com-tls -o jsonpath='{.data.tls\.crt}' | base64 -d | openssl x509 -noout -text
```

---

## 9. TESTING & VALIDATION

### Unit Tests (Go)

```go
package tlstest

import (
    "crypto/tls"
    "crypto/x509"
    "testing"
)

func TestTLSHandshake(t *testing.T) {
    // Start test server
    cert, _ := tls.LoadX509KeyPair("testdata/server.crt", "testdata/server.key")
    serverCfg := &tls.Config{
        Certificates: []tls.Certificate{cert},
        MinVersion:   tls.VersionTLS13,
    }
    
    ln, _ := tls.Listen("tcp", "127.0.0.1:0", serverCfg)
    defer ln.Close()
    
    go func() {
        conn, _ := ln.Accept()
        conn.Write([]byte("hello"))
        conn.Close()
    }()
    
    // Client connects
    caCert, _ := os.ReadFile("testdata/ca.crt")
    caCertPool := x509.NewCertPool()
    caCertPool.AppendCertsFromPEM(caCert)
    
    clientCfg := &tls.Config{
        RootCAs:    caCertPool,
        ServerName: "localhost",
    }
    
    conn, err := tls.Dial("tcp", ln.Addr().String(), clientCfg)
    if err != nil {
        t.Fatalf("TLS handshake failed: %v", err)
    }
    defer conn.Close()
    
    // Verify negotiated protocol
    if conn.ConnectionState().Version != tls.VersionTLS13 {
        t.Errorf("Expected TLS 1.3, got %x", conn.ConnectionState().Version)
    }
}
```

### Fuzzing TLS Parsers

```go
// fuzz_test.go
package tlsfuzz

import (
    "crypto/tls"
    "testing"
)

func FuzzTLSHandshake(f *testing.F) {
    f.Add([]byte("valid seed data"))
    
    f.Fuzz(func(t *testing.T, data []byte) {
        // Fuzz TLS record parsing
        cfg := &tls.Config{InsecureSkipVerify: true}
        conn := tls.Client(fakeConn{data}, cfg)
        conn.Handshake() // Should not panic on malformed input
    })
}

type fakeConn struct{ data []byte }
func (c fakeConn) Read(b []byte) (int, error) {
    n := copy(b, c.data)
    c.data = c.data[n:]
    return n, nil
}
func (c fakeConn) Write(b []byte) (int, error) { return len(b), nil }
func (c fakeConn) Close() error                { return nil }
```

**Run fuzzing:**
```bash
go test -fuzz=FuzzTLSHandshake -fuzztime=1h
```

### Integration Tests (testcontainers)

```go
func TestNginxTLS(t *testing.T) {
    ctx := context.Background()
    
    // Start Nginx container
    req := testcontainers.ContainerRequest{
        Image:        "nginx:alpine",
        ExposedPorts: []string{"443/tcp"},
        Files: []testcontainers.ContainerFile{
            {HostFilePath: "testdata/nginx.conf", ContainerFilePath: "/etc/nginx/nginx.conf"},
            {HostFilePath: "testdata/server.crt", ContainerFilePath: "/etc/nginx/cert.crt"},
            {HostFilePath: "testdata/server.key", ContainerFilePath: "/etc/nginx/cert.key"},
        },
    }
    
    nginx, _ := testcontainers.GenericContainer(ctx, testcontainers.GenericContainerRequest{
        ContainerRequest: req,
        Started:          true,
    })
    defer nginx.Terminate(ctx)
    
    // Test TLS connection
    host, _ := nginx.Host(ctx)
    port, _ := nginx.MappedPort(ctx, "443")
    
    cfg := &tls.Config{InsecureSkipVerify: true}
    conn, err := tls.Dial("tcp", host+":"+port.Port(), cfg)
    if err != nil {
        t.Fatalf("TLS connection failed: %v", err)
    }
    defer conn.Close()
}
```

### Scanning Tools

```bash
# SSLyze: comprehensive TLS scanner
docker run --rm nablac0d3/sslyze:latest \
  --regular example.com:443

# testssl.sh: shell-based TLS tester
git clone https://github.com/drwetter/testssl.sh.git
cd testssl.sh
./testssl.sh --full example.com:443

# nmap NSE scripts
nmap --script ssl-enum-ciphers -p 443 example.com

# Check for vulnerabilities
nmap --script ssl-heartbleed,ssl-poodle,ssl-ccs-injection -p 443 example.com
```

---

## 10. PERFORMANCE OPTIMIZATION

### Connection Pooling & Reuse

```go
// HTTP client with connection reuse
transport := &http.Transport{
    MaxIdleConns:        100,
    MaxIdleConnsPerHost: 10,
    IdleConnTimeout:     90 * time.Second,
    
    TLSClientConfig: &tls.Config{
        MinVersion: tls.VersionTLS13,
        // Session cache for TLS resumption
        ClientSessionCache: tls.NewLRUClientSessionCache(128),
    },
    
    // TCP keepalive
    DialContext: (&net.Dialer{
        Timeout:   30 * time.Second,
        KeepAlive: 30 * time.Second,
    }).DialContext,
}

client := &http.Client{Transport: transport}
```

### Hardware Acceleration

```bash
# Check for AES-NI (x86_64)
grep -o 'aes' /proc/cpuinfo | head -1

# OpenSSL benchmark
openssl speed -evp aes-128-gcm    # With AES-NI
openssl speed -evp chacha20-poly1305

# BoringSSL crypto tests
go test -bench=. crypto/aes crypto/cipher
```

**Expected throughput (AES-128-GCM on Intel Xeon with AES-NI):**
- **Software AES:** ~500 MB/s per core
- **AES-NI:** ~3-5 GB/s per core
- **ChaCha20 (SW):** ~700 MB/s per core (constant-time)

### Session Resumption Metrics

```go
// Prometheus metrics for TLS handshakes
var (
    tlsHandshakes = prometheus.NewCounterVec(
        prometheus.CounterOpts{Name: "tls_handshakes_total"},
        []string{"resumed"},
    )
    tlsHandshakeDuration = prometheus.NewHistogram(
        prometheus.HistogramOpts{
            Name:    "tls_handshake_duration_seconds",
            Buckets: prometheus.ExponentialBuckets(0.001, 2, 10),
        },
    )
)

// Instrument server
http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
    start := time.Now()
    defer func() {
        tlsHandshakeDuration.Observe(time.Since(start).Seconds())
    }()
    
    if r.TLS != nil {
        resumed := "false"
        if r.TLS.DidResume {
            resumed = "true"
        }
        tlsHandshakes.With(prometheus.Labels{"resumed": resumed}).Inc()
    }
    
    w.Write([]byte("ok"))
})
```

---

## 11. ROLLOUT & ROLLBACK PLAN

### Phase 1: Audit Current State (Week 1)
```bash
# Inventory all TLS endpoints
nmap -p 443 -sV 10.0.0.0/24 -oG - | grep open

# Scan each service
for host in $(cat endpoints.txt); do
    testssl.sh --jsonfile-pretty results/$host.json $host:443
done

# Aggregate findings
jq '.[] | select(.severity == "HIGH" or .severity == "CRITICAL")' results/*.json
```

**Checklist:**
- [ ] List all protocols in use (TLS 1.0/1.1/1.2/1.3)
- [ ] Identify weak ciphers (CBC, RC4, 3DES)
- [ ] Check cert expiry, key sizes, signature algorithms
- [ ] Document internal PKI vs public CA usage

### Phase 2: Lab Testing (Week 2-3)
```bash
# Staging environment
terraform apply -var="tls_min_version=1.3" -target=module.staging

# Run integration tests
kubectl apply -f tests/tls-test-suite.yaml
kubectl wait --for=condition=complete job/tls-tests --timeout=600s
kubectl logs job/tls-tests

# Performance baseline
wrk -t4 -c100 -d30s --latency https://staging.example.com/health
```

### Phase 3: Gradual Rollout (Week 4-6)

```yaml
# Feature flag (LaunchDarkly, Unleash)
tls_v13_enforcement:
  enabled: true
  rollout:
    percentage: 10  # Start with 10% of traffic
    userGroups:
      - internal-users
      - beta-testers

# Nginx canary config
upstream backend {
    server backend-tls12.internal:8080 weight=90;
    server backend-tls13.internal:8080 weight=10;
}
```

**Monitoring:**
```promql
# Error rate by TLS version
rate(http_requests_total{status=~"5..",tls_version="1.2"}[5m])
rate(http_requests_total{status=~"5..",tls_version="1.3"}[5m])

# Handshake failures
rate(tls_handshake_errors_total[5m]) > 0.01

# Alert on latency regression
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 0.5
```

### Phase 4: Full Deployment (Week 7)
```bash
# Update production config
kubectl set env deployment/nginx TLS_MIN_VERSION=1.3
kubectl rollout status deployment/nginx

# Verify
for pod in $(kubectl get pods -l app=nginx -o name); do
    kubectl exec $pod -- nginx -T | grep ssl_protocols
done
```

### Rollback Procedure

```bash
# Immediate rollback (< 5 min)
kubectl rollout undo deployment/nginx

# Gradual rollback (circuit breaker)
# If error rate > 1% for 5 min, auto-rollback
alert:
  - alert: TLSRolloutFailure
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
    for: 5m
    annotations:
      action: "kubectl rollout undo deployment/nginx"
```

**Post-Rollback Diagnostics:**
```bash
# Capture traffic during failure
tcpdump -i any -s0 -w /tmp/tls-failure.pcap port 443

# Analyze with Wireshark
wireshark /tmp/tls-failure.pcap
# Filter: tls.alert or tls.handshake.type == 2 (ServerHello)

# Check client compatibility
# Common issue: legacy clients (Android <5.0, Java <8u252) don't support TLS 1.3
```

---

## 12. REFERENCES & NEXT STEPS

### Core RFCs
- **RFC 8446:** TLS 1.3 (2018)
- **RFC 5246:** TLS 1.2 (superseded)
- **RFC 5280:** X.509 Certificate and CRL Profile
- **RFC 6125:** Domain Name Validation
- **RFC 7540:** HTTP/2 (requires TLS 1.2+ ALPN)
- **RFC 9000:** QUIC (TLS 1.3 integrated)

### Security Advisories
- **OpenSSL:** https://www.openssl.org/news/vulnerabilities.html
- **BoringSSL:** https://boringssl.googlesource.com/boringssl/
- **NSS (Firefox):** https://developer.mozilla.org/en-US/docs/Mozilla/Projects/NSS/NSS_Releases

### Tools & Libraries
- **Go:** `crypto/tls`, `golang.org/x/crypto/acme`
- **Rust:** `rustls`, `tokio-rustls`
- **C/C++:** OpenSSL, BoringSSL, LibreSSL, mbedTLS
- **SPIFFE/SPIRE:** https://spiffe.io/docs/latest/spire/

### Testing Resources
- **SSL Labs:** https://www.ssllabs.com/ssltest/
- **testssl.sh:** https://testssl.sh/
- **BadSSL:** https://badssl.com/ (test invalid certs, mixed content)
- **How's My SSL:** https://www.howsmyssl.com/

### Attack Research
- **BEAST (2011):** CBC IV prediction (TLS 1.0)
- **CRIME (2012):** TLS compression side-channel
- **Heartbleed (2014):** OpenSSL buffer over-read (CVE-2014-0160)
- **POODLE (2014):** SSLv3 CBC padding oracle
- **FREAK (2015):** Export cipher downgrade
- **Logjam (2015):** DHE weak parameters
- **DROWN (2016):** SSLv2 cross-protocol attack
- **Sweet32 (2016):** 64-bit block cipher birthday bound (3DES)

---

## NEXT 3 STEPS

### 1. Deploy TLS 1.3-Only in Staging
```bash
# Update Nginx config
ssl_protocols TLSv1.3;

# Generate new ECDSA cert (faster than RSA)
openssl ecparam -genkey -name prime256v1 -out ecdsa.key
openssl req -new -x509 -key ecdsa.key -out ecdsa.crt -days 365

# Test client compatibility
docker run --rm curlimages/curl:latest curl -v https://staging.example.com
```

### 2. Implement mTLS for East-West Traffic
```bash
# Install SPIRE in Kubernetes
helm install spire-server spire/spire \
  --set trustDomain=example.com

# Configure workload attestation
kubectl apply -f - <<EOF
apiVersion: spire.spiffe.io/v1alpha1
kind: ClusterSPIFFEID
metadata:
  name: backend
spec:
  spiffeIDTemplate: "spiffe://example.com/ns/{{ .PodMeta.Namespace }}/sa/{{ .PodSpec.ServiceAccountName }}"
  podSelector:
    matchLabels:
      app: backend
EOF
```

### 3. Monitor & Alert on TLS Anomalies
```yaml
# Prometheus alerts
groups:
- name: tls
  rules:
  - alert: TLSHandshakeFailures
    expr: rate(tls_handshake_errors_total[5m]) > 0.01
    annotations:
      summary: "High TLS handshake failure rate"
  
  - alert: WeakCipherNegotiated
    expr: tls_cipher_suite{cipher!~"TLS_AES.*|TLS_CHACHA20.*"} > 0
    annotations:
      summary: "Non-AEAD cipher in use"
```

---

**CRITICAL SECURITY REMINDER:** TLS is a moving target. Subscribe to security mailing lists (oss-security, OpenSSL announce), automate cert renewal (cert-manager, ACME), enforce short cert lifetimes (90 days max), and treat private keys as crown jewels (HSM for CA roots, envelope encryption for at-rest keys, never commit to Git).