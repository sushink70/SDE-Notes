# SSL/TLS: A Complete, In-Depth Technical Reference

> **Reading guide:** This document is structured from foundational concepts upward. Each section builds on the previous. The ASCII protocol diagrams show the actual wire-level message flow. The C and Rust implementations are production-quality reference code.

---

## Table of Contents

1. [History and Motivation](#1-history-and-motivation)
2. [Protocol Versions and Deprecation](#2-protocol-versions-and-deprecation)
3. [Cryptographic Foundations](#3-cryptographic-foundations)
4. [Public Key Infrastructure and X.509 Certificates](#4-public-key-infrastructure-and-x509-certificates)
5. [Protocol Architecture: The Four Sub-Protocols](#5-protocol-architecture-the-four-sub-protocols)
6. [The TLS Record Protocol](#6-the-tls-record-protocol)
7. [The TLS Handshake Protocol (TLS 1.2)](#7-the-tls-12-handshake-protocol)
8. [The TLS Handshake Protocol (TLS 1.3)](#8-the-tls-13-handshake-protocol)
9. [The Alert Protocol](#9-the-alert-protocol)
10. [The Change Cipher Spec Protocol](#10-the-change-cipher-spec-protocol)
11. [Cipher Suites In Depth](#11-cipher-suites-in-depth)
12. [Key Exchange Mechanisms](#12-key-exchange-mechanisms)
13. [Session Resumption](#13-session-resumption)
14. [Extensions](#14-extensions)
15. [Mutual TLS (mTLS)](#15-mutual-tls-mtls)
16. [Certificate Lifecycle and Revocation](#16-certificate-lifecycle-and-revocation)
17. [Protocol Attack Surface and Historical Vulnerabilities](#17-protocol-attack-surface-and-historical-vulnerabilities)
18. [Implementation in C (OpenSSL)](#18-implementation-in-c-openssl)
19. [Implementation in Rust (rustls + native)](#19-implementation-in-rust)
20. [Deployment Best Practices](#20-deployment-best-practices)
21. [Mental Model Summary](#21-mental-model-summary)

---

## 1. History and Motivation

### The Problem TLS Solves

Before TLS existed, application protocols (HTTP, FTP, SMTP) transmitted data as plaintext over TCP. Any node between the client and server — a router, an ISP's switch, a rogue Wi-Fi access point — could read, record, or modify the data stream. This created three distinct attack classes:

- **Eavesdropping:** A passive observer reads credentials, cookies, private data.
- **Tampering:** An active attacker modifies data in transit (inject malicious scripts, alter financial transfers).
- **Impersonation:** An attacker poses as the legitimate server; the client has no way to verify identity.

TLS solves all three by providing:

1. **Confidentiality:** Data is encrypted; interceptors see only ciphertext.
2. **Integrity:** A message authentication code (MAC) detects any modification.
3. **Authentication:** The server's certificate proves its identity via a chain of trust to a trusted Certificate Authority (CA).

### Netscape and SSL Origins (1994–1995)

SSL (Secure Sockets Layer) was designed by Netscape Communications in 1994 to secure HTTP traffic for e-commerce. SSL 1.0 was never released publicly — it had severe design flaws discovered internally. SSL 2.0 shipped with Netscape Navigator 1.1 in 1995. SSL 3.0 (1996, RFC 6101) was a complete redesign by Paul Kocher, Phil Karlton, and Alan Freier that became the basis for all future TLS versions.

### IETF Standardization (1999–Present)

The IETF took over SSL standardization and renamed it TLS to avoid Netscape's trademark. Each version is a published RFC:

| Version    | Year | RFC       | Status        |
|------------|------|-----------|---------------|
| SSL 2.0    | 1995 | —         | Prohibited    |
| SSL 3.0    | 1996 | RFC 6101  | Prohibited    |
| TLS 1.0    | 1999 | RFC 2246  | Deprecated    |
| TLS 1.1    | 2006 | RFC 4346  | Deprecated    |
| TLS 1.2    | 2008 | RFC 5246  | Widely used   |
| TLS 1.3    | 2018 | RFC 8446  | Current/recommended |

---

## 2. Protocol Versions and Deprecation

### SSL 2.0 — Never Use

SSL 2.0 had fundamental design flaws:
- The MAC did not cover the handshake message type, enabling message truncation attacks.
- Weak cipher suites were mandatory.
- No protection against cipher suite downgrade.
- Used the same key for both encryption and MAC derivation (key reuse).

RFC 6176 (2011) explicitly prohibits any TLS implementation from negotiating SSL 2.0.

### SSL 3.0 — Never Use

SSL 3.0 fixed the SSL 2.0 problems but introduced its own:
- Used MD5/SHA-1 for the PRF (vulnerable to length extension and collision attacks).
- CBC padding was not authenticated properly — exploitable by POODLE (2014).
- No support for AEAD ciphers.

RFC 7568 (2015) prohibits negotiation of SSL 3.0.

### TLS 1.0 and 1.1 — Deprecated

TLS 1.0 is essentially SSL 3.1. It fixed some padding oracle weaknesses but retained:
- RC4 support (completely broken).
- CBC mode without explicit IV (enables BEAST attack).
- SHA-1 in the PRF.

TLS 1.1 added explicit IVs to fix BEAST but kept SHA-1. Both were deprecated by RFC 8996 (2021). Major browsers dropped support in 2020–2021.

### TLS 1.2 — Current (but aging)

TLS 1.2 (RFC 5246, 2008) was a significant improvement:
- Replaced the MD5/SHA-1 PRF with a configurable PRF (SHA-256 default).
- Added support for AEAD cipher suites (GCM, CCM).
- Added support for SHA-256 in certificate signatures.
- Flexible cipher suite negotiation.

TLS 1.2 is still widely deployed and secure when configured properly (disabling weak cipher suites, requiring ephemeral key exchange).

### TLS 1.3 — The Right Design

TLS 1.3 (RFC 8446, 2018) is a clean-room redesign:
- Removed all legacy algorithms (RSA key exchange, DH static, RC4, DES, 3DES, MD5, SHA-1, export ciphers).
- Reduced handshake to 1-RTT (one round-trip time), with 0-RTT for resumption.
- Mandatory forward secrecy via ephemeral key exchange (ECDHE/DHE).
- Encrypted handshake extensions after the first server message.
- Redesigned key schedule using HKDF.

---

## 3. Cryptographic Foundations

Understanding TLS requires understanding the cryptographic primitives it relies on. Each serves a precise purpose.

### 3.1 Symmetric Encryption

Symmetric encryption uses the same key for encryption and decryption. In TLS, symmetric ciphers encrypt the actual application data after the handshake establishes a shared key.

**Block Ciphers:**

A block cipher operates on fixed-size blocks of data (AES: 128-bit blocks). Raw block ciphers are deterministic — the same plaintext block always produces the same ciphertext block, which leaks structural information. Block cipher modes of operation solve this.

**AES-CBC (Cipher Block Chaining):**

```
Encryption:
  C[i] = Encrypt(P[i] XOR C[i-1])
  C[0] = IV (Initialization Vector, random)

Decryption:
  P[i] = Decrypt(C[i]) XOR C[i-1]
```

CBC mode requires padding when the plaintext is not a multiple of the block size (typically PKCS#7 padding). Padding oracles were a major attack vector against TLS 1.0/1.1 (BEAST, Lucky13, POODLE).

**AES-GCM (Galois/Counter Mode) — Preferred:**

GCM combines counter mode encryption with a Galois-field-based authentication tag. It is an AEAD (Authenticated Encryption with Associated Data) cipher — it provides both confidentiality AND integrity/authenticity in a single operation, with no separate MAC needed.

```
Counter Mode:
  Keystream[i] = Encrypt(IV || Counter[i])
  C[i] = P[i] XOR Keystream[i]

GHASH (Authentication):
  Tag = GHASH(H, AAD, C) XOR Encrypt(IV || 0)
  where H = Encrypt(0^128)
```

The nonce/IV in GCM must be unique per (key, nonce) pair. If a nonce is reused, both confidentiality and integrity are completely broken. TLS enforces nonce uniqueness via sequence numbers.

**ChaCha20-Poly1305:**

ChaCha20 is a stream cipher by Daniel Bernstein. Poly1305 is a one-time MAC. Together (RFC 8439) they form an AEAD construction that is:
- Faster than AES-GCM on hardware without AES-NI acceleration (mobile, IoT).
- Immune to timing side-channels from table lookups (pure arithmetic).
- Standardized in TLS 1.2 (RFC 7905) and TLS 1.3.

### 3.2 Asymmetric (Public-Key) Cryptography

Asymmetric cryptography uses key pairs: a public key (shareable) and a private key (secret). These two keys are mathematically related such that:
- Data encrypted with the public key can only be decrypted with the private key.
- Data signed with the private key can be verified with the public key.

**RSA:**

RSA security is based on the difficulty of factoring the product of two large primes.

```
Key Generation:
  1. Choose large primes p, q
  2. n = p * q  (public modulus)
  3. φ(n) = (p-1)(q-1)  (Euler's totient)
  4. Choose e: gcd(e, φ(n)) = 1, typically e = 65537
  5. d = e^(-1) mod φ(n)  (modular inverse)
  Public key:  (n, e)
  Private key: (n, d)

Encryption:  C = M^e mod n
Decryption:  M = C^d mod n
Signature:   S = M^d mod n
Verify:      M = S^e mod n
```

RSA key exchange in TLS (pre-1.3): The client generates a random PreMasterSecret, encrypts it with the server's RSA public key. Only the server (with the private key) can decrypt it. **No forward secrecy** — if the private key is ever compromised, all past sessions can be decrypted from recorded traffic.

RSA is still used for **signatures** in TLS 1.3 (to authenticate the key exchange), not for key exchange itself.

Minimum recommended key size: 2048 bits (3072+ for new deployments, 4096 for long-term certificates).

**Elliptic Curve Cryptography (ECC):**

ECC security is based on the difficulty of the elliptic curve discrete logarithm problem (ECDLP). An elliptic curve is defined as:

```
y² = x³ + ax + b  (over a finite field F_p)
```

A point on the curve can be multiplied by a scalar k:
```
Q = k * G  (G is the generator/base point)
```

Given Q and G, finding k is computationally infeasible (ECDLP). ECC achieves equivalent security to RSA with much smaller keys:

| RSA Key Size | ECC Key Size | Security Level |
|--------------|--------------|----------------|
| 1024 bits    | 160 bits     | 80 bits        |
| 2048 bits    | 224 bits     | 112 bits       |
| 3072 bits    | 256 bits     | 128 bits       |
| 7680 bits    | 384 bits     | 192 bits       |
| 15360 bits   | 521 bits     | 256 bits       |

**Standard Curves:**

- **P-256 (secp256r1/prime256v1):** NIST curve, most widely used. Some concern about NIST's curve constants.
- **P-384 (secp384r1):** Higher security, used in government/sensitive contexts.
- **X25519 (Curve25519):** Designed by Bernstein for Diffie-Hellman. Faster, simpler, no secret constants controversy. Default in TLS 1.3.
- **X448 (Curve448):** 224-bit security, used when P-384 equivalent is needed.

**ECDSA (Elliptic Curve Digital Signature Algorithm):**

```
Sign(private key d, message m):
  k = random nonce (MUST be unique per signature, or private key leaks)
  R = k * G; r = R.x mod n
  s = k^(-1) * (hash(m) + d*r) mod n
  Signature = (r, s)

Verify(public key Q, message m, (r, s)):
  w = s^(-1) mod n
  u1 = hash(m) * w mod n
  u2 = r * w mod n
  X = u1*G + u2*Q
  Valid if X.x mod n == r
```

**Critical:** ECDSA nonce reuse (same k for two signatures) exposes the private key. This is how PlayStation 3's private key was recovered. TLS implementations use deterministic nonce generation (RFC 6979).

**EdDSA (Edwards-curve Digital Signature Algorithm) / Ed25519:**

Ed25519 is a Schnorr-like signature scheme over Curve25519 (twisted Edwards form). It is:
- Deterministic (no random nonce needed — nonce derived from private key + message).
- Faster than ECDSA.
- Immune to nonce reuse disasters.
- Supported in TLS 1.3 certificates.

### 3.3 Diffie-Hellman Key Exchange

Diffie-Hellman allows two parties to establish a shared secret over an insecure channel without any prior shared secret.

**Classic DH (RFC 3526 groups):**

```
Setup: Public parameters (p, g)
  p = large prime
  g = generator (primitive root mod p)

Alice:
  a = random private value
  A = g^a mod p  (public value, sent to Bob)

Bob:
  b = random private value
  B = g^b mod p  (public value, sent to Alice)

Shared Secret:
  Alice: S = B^a mod p = g^(ab) mod p
  Bob:   S = A^b mod p = g^(ab) mod p
```

An eavesdropper sees p, g, A, B but cannot compute g^(ab) without solving the discrete log problem.

**ECDH (Elliptic Curve DH):**

```
Alice:
  a = random scalar (private key)
  A = a * G  (public key, sent to Bob)

Bob:
  b = random scalar (private key)
  B = b * G  (public key, sent to Alice)

Shared Secret:
  Alice: S = a * B = a * b * G
  Bob:   S = b * A = b * a * G
  (S.x coordinate is the shared secret)
```

**Ephemeral DH (DHE/ECDHE):**

"Ephemeral" means the DH keys are freshly generated for each session and discarded afterward. This provides **forward secrecy** (also called perfect forward secrecy, PFS): compromising the server's long-term private key does not allow decryption of past sessions, because each session used a unique ephemeral DH key pair that no longer exists.

TLS 1.3 mandates ephemeral key exchange. TLS 1.2 supports it but requires configuration to enforce it.

### 3.4 Hash Functions

Hash functions map arbitrary-length input to a fixed-length digest. Properties required:

- **Pre-image resistance:** Given H(m), cannot find m.
- **Second pre-image resistance:** Given m, cannot find m' ≠ m such that H(m) = H(m').
- **Collision resistance:** Cannot find any m, m' such that H(m) = H(m').

| Hash   | Output  | Status in TLS         |
|--------|---------|-----------------------|
| MD5    | 128-bit | Broken, prohibited    |
| SHA-1  | 160-bit | Deprecated            |
| SHA-256| 256-bit | Widely used           |
| SHA-384| 384-bit | High-security use     |
| SHA-512| 512-bit | Rare                  |

SHA-256, SHA-384, SHA-512 are all part of SHA-2 (FIPS 180-4). SHA-3 (Keccak) exists but is not yet widely deployed in TLS.

### 3.5 HMAC (Hash-based Message Authentication Code)

HMAC (RFC 2104) is a MAC construction based on a hash function:

```
HMAC(K, m) = H((K XOR opad) || H((K XOR ipad) || m))

where:
  opad = 0x5c repeated to block length
  ipad = 0x36 repeated to block length
  K    = key (padded/truncated to block length)
```

HMAC-SHA256 is used in TLS 1.2's PRF and in record MAC computation (for non-AEAD cipher suites).

Properties:
- Even if the underlying hash has weaknesses (length-extension attacks), HMAC remains secure because the key prevents the attacker from computing HMACs without it.
- Proven secure as long as the hash is a pseudorandom function.

### 3.6 PRF (Pseudorandom Function)

TLS uses a PRF to derive keys from the master secret. In TLS 1.2:

```
PRF(secret, label, seed) = P_<hash>(secret, label || seed)

P_hash(secret, seed) = HMAC_hash(secret, A(1) || seed)     ||
                        HMAC_hash(secret, A(2) || seed)     ||
                        HMAC_hash(secret, A(3) || seed)     || ...

A(0) = seed
A(i) = HMAC_hash(secret, A(i-1))
```

This is an HMAC-based construction that can produce an arbitrary number of pseudorandom bytes.

### 3.7 HKDF (HMAC-based Key Derivation Function)

TLS 1.3 replaced the ad-hoc PRF with HKDF (RFC 5869), a two-phase construction:

```
HKDF-Extract(salt, IKM):
  PRK = HMAC-Hash(salt, IKM)
  → PRK (pseudorandom key, fixed-length)

HKDF-Expand(PRK, info, L):
  T(0) = ""
  T(i) = HMAC-Hash(PRK, T(i-1) || info || i)
  → first L bytes of T(1) || T(2) || ...
```

HKDF separates "extraction" (compressing high-entropy but non-uniform input keying material into a PRK) from "expansion" (stretching PRK into multiple keys with context-specific `info` strings). This design is formally proven secure.

### 3.8 AEAD (Authenticated Encryption with Associated Data)

AEAD ciphers are the modern standard. They combine encryption and authentication atomically. The "Associated Data" (AD) is authenticated but not encrypted — it is the TLS record header (content type, version, length) in TLS 1.3, and (seq_num, content_type, version, length) in TLS 1.2.

```
Encryption:
  (ciphertext, tag) = AEAD_Encrypt(key, nonce, plaintext, associated_data)

Decryption:
  plaintext = AEAD_Decrypt(key, nonce, ciphertext, tag, associated_data)
  (fails with error if tag is invalid — plaintext is never revealed)
```

**Why AEAD is superior to MAC-then-Encrypt (older approach):**

The older approach was: Compute MAC over plaintext, then encrypt (plaintext || MAC). The problem is that decryption requires decrypting first before MAC verification, creating padding oracle vulnerabilities. AEAD makes the tag cover the ciphertext; authentication can be verified before any decryption, eliminating the oracle.

---

## 4. Public Key Infrastructure and X.509 Certificates

### 4.1 The Trust Problem

Asymmetric cryptography solves key exchange but not identity verification. If a client connects to a server and receives a public key, how does it know that public key actually belongs to the legitimate server and not to an attacker performing a man-in-the-middle attack?

PKI (Public Key Infrastructure) solves this by establishing a hierarchy of trust. A Certificate Authority (CA) is an entity that clients trust by default (its root certificate is installed in the OS/browser trust store). The CA signs server certificates, binding a public key to an identity (domain name).

### 4.2 X.509 Certificate Structure

An X.509 v3 certificate is an ASN.1 DER-encoded data structure (defined in RFC 5280):

```
Certificate  ::=  SEQUENCE  {
    tbsCertificate       TBSCertificate,       -- to-be-signed
    signatureAlgorithm   AlgorithmIdentifier,  -- CA's sig algorithm
    signatureValue       BIT STRING            -- CA's signature
}

TBSCertificate  ::=  SEQUENCE  {
    version          [0]  EXPLICIT INTEGER DEFAULT v1,  -- v3 = 2
    serialNumber          CertificateSerialNumber,      -- unique per CA
    signature             AlgorithmIdentifier,          -- must match outer
    issuer                Name,                         -- CA's DN
    validity              Validity {
                              notBefore  Time,
                              notAfter   Time
                          },
    subject               Name,                         -- server's DN
    subjectPublicKeyInfo  SubjectPublicKeyInfo {
                              algorithm   AlgorithmIdentifier,
                              subjectPublicKey BIT STRING
                          },
    extensions        [3]  EXPLICIT Extensions OPTIONAL
}
```

**Distinguished Name (DN) fields:**
- CN (Common Name): Historically the hostname; now superseded by SAN.
- O (Organization)
- OU (Organizational Unit)
- C (Country)
- ST (State)
- L (Locality)

**Critical Extensions (v3):**

| Extension | Purpose |
|-----------|---------|
| Subject Alternative Name (SAN) | DNS names, IPs, emails this cert is valid for |
| Basic Constraints | Is this a CA cert? Max path length |
| Key Usage | digitalSignature, keyEncipherment, etc. |
| Extended Key Usage | serverAuth, clientAuth, codeSigning |
| Authority Key Identifier | Identifies the CA key that signed this cert |
| Subject Key Identifier | Identifies this cert's public key |
| CRL Distribution Points | URLs for Certificate Revocation List |
| Authority Info Access | URL for OCSP responder, issuer cert |
| Certificate Policies | OID indicating validation level (DV/OV/EV) |
| Signed Certificate Timestamp (SCT) | Certificate Transparency proof |

### 4.3 Certificate Chain / Chain of Trust

A single root CA cannot sign every certificate on the internet practically. Instead, a hierarchy exists:

```
Root CA Certificate
  └── Intermediate CA Certificate (signed by Root)
        └── Server Certificate (signed by Intermediate)
```

During the TLS handshake, the server sends its certificate plus all intermediate certificates (the "chain"). The client validates:

1. Each certificate in the chain is signed by the one above it.
2. The root at the top of the chain is in the client's trust store.
3. No certificate in the chain is expired.
4. The server's certificate's SAN matches the hostname being connected to.
5. No certificate in the chain is revoked.

Root CA certificates are self-signed (the CA signed its own certificate) and are trusted unconditionally because they're pre-installed.

### 4.4 Certificate Validation Types

| Type | Abbreviation | Verification | Trust level |
|------|-------------|--------------|-------------|
| Domain Validated | DV | CA verifies control of domain (DNS/HTTP challenge) | Low |
| Organization Validated | OV | CA verifies organization identity | Medium |
| Extended Validation | EV | CA verifies legal entity rigorously | High |

### 4.5 Certificate Encoding Formats

| Format | Encoding | Extension | Contents |
|--------|----------|-----------|---------|
| DER | Binary ASN.1 | .der, .cer | Single cert |
| PEM | Base64 DER + headers | .pem, .crt | One or more certs/keys |
| PKCS#12 | Binary | .p12, .pfx | Cert + private key (password protected) |
| PKCS#7 | DER or PEM | .p7b | Certificate chain (no private key) |

PEM (Privacy Enhanced Mail) is the most common text format:

```
-----BEGIN CERTIFICATE-----
MIIFazCCA1OgAwIBAgIRAIIQz7DSQONZRGPgu2OCiwAwDQYJKoZIhvcNAQELBQAw
...
-----END CERTIFICATE-----
```

### 4.6 How a CA Signs a Certificate

```
1. Server operator generates key pair:
   openssl genrsa -out server.key 2048
   
2. Creates Certificate Signing Request (CSR):
   openssl req -new -key server.key -out server.csr
   (CSR contains: subject DN, public key, requested extensions, signed with private key)

3. CA verifies the request (domain control proof, identity documents, etc.)

4. CA signs the CSR:
   CA_Signature = Sign(CA_PrivateKey, hash(TBSCertificate))
   
5. CA issues the certificate (TBSCertificate + CA_Signature)

6. Server operator installs cert + private key
```

---

## 5. Protocol Architecture: The Four Sub-Protocols

TLS is structured as a layered protocol. The **Record Protocol** is the lowest layer, transporting messages for three higher-layer sub-protocols:

```
+------------------------------------------------------+
|            Application Data (HTTP, SMTP, etc.)       |
+------------------------------------------------------+
|    Handshake  |   Alert   |  ChangeCipherSpec | AppData|  <-- Content Types
+------------------------------------------------------+
|                   TLS Record Protocol                |
+------------------------------------------------------+
|                        TCP                           |
+------------------------------------------------------+
|                        IP                            |
+------------------------------------------------------+
```

The four content types carried by the Record Protocol:

| Content Type | Value | Description |
|-------------|-------|-------------|
| change_cipher_spec | 20 | Signal to switch to negotiated cipher |
| alert | 21 | Error/warning notifications |
| handshake | 22 | Handshake negotiation messages |
| application_data | 23 | Encrypted application payload |

In TLS 1.3, the content type in the record header is often `application_data` (23) even for handshake messages after a certain point — the actual content type is inside the encrypted payload (inner content type), and the outer header shows 23 to prevent fingerprinting.

---

## 6. The TLS Record Protocol

The Record Protocol fragments, compresses (obsolete in TLS 1.3), and protects all data from the upper layers. Every message is wrapped in a **TLS Record**.

### 6.1 TLS Record Wire Format

```
+----------+--------+--------+------- ... -------+
|  type    | ver_hi | ver_lo |      length        |   fragment
| (1 byte) |(1 byte)|(1 byte)|(2 bytes big-endian)| (0..2^14 bytes)
+----------+--------+--------+------- ... -------+

Total header: 5 bytes
Max fragment: 16384 bytes (2^14)
```

**Field details:**

- **type (ContentType):** 20, 21, 22, or 23.
- **version:** TLS 1.2 uses `{0x03, 0x03}`. TLS 1.3 uses `{0x03, 0x03}` for compatibility (the actual version is negotiated via the Supported Versions extension in the handshake).
- **length:** Length of the fragment in bytes (up to 16384 for plaintext; with encryption overhead, the record can be up to 16384 + 256 = 16640 bytes).

### 6.2 TLS 1.2 Record Processing (Non-AEAD)

For CBC cipher suites in TLS 1.2:

```
Fragment (plaintext):
  content = application data fragment

Compute MAC:
  MAC = HMAC_hash(MAC_key, seq_num || type || version || length || content)
  seq_num is 8-byte big-endian counter, reset to 0 at renegotiation

Add Padding (PKCS#7 style):
  padding_length = block_size - ((len(content) + len(MAC) + 1) % block_size)
  padding = padding_length bytes all equal to padding_length

Construct:
  plaintext_to_encrypt = content || MAC || padding || padding_length_byte

Prepend IV:
  TLS_fragment = IV (16 bytes random) || CBC_Encrypt(key, IV, plaintext_to_encrypt)
```

**Why seq_num is in the MAC:** To prevent replay attacks. The MAC covers the sequence number, so replaying an old record produces a MAC mismatch (the sequence number doesn't match what the receiver expects).

### 6.3 TLS 1.2 Record Processing (AEAD — GCM)

For AES-GCM in TLS 1.2:

```
Nonce construction:
  nonce = implicit_IV (4 bytes, from key schedule) || explicit_nonce (8 bytes, sent in record)
  The explicit nonce is typically the sequence number.

Associated data:
  AAD = seq_num || content_type || version || plaintext_length (13 bytes total)

Encryption:
  (ciphertext, tag) = AES_GCM_Encrypt(write_key, nonce, plaintext, AAD)

Record fragment:
  explicit_nonce (8 bytes) || ciphertext || tag (16 bytes)
```

### 6.4 TLS 1.3 Record Processing

TLS 1.3 always uses AEAD. All records after the initial unencrypted handshake are encrypted:

```
Inner plaintext structure:
  plaintext = content || content_type (1 byte) || zero_padding (optional)

Nonce construction (XOR-based):
  padded_seq_num = seq_num left-padded to IV length with zeros
  nonce = write_IV XOR padded_seq_num

Associated data (record header as seen on wire):
  AAD = 0x17 (23, application_data) || 0x03 0x03 || length_of_encrypted_record

Encryption:
  encrypted_record = AEAD_Encrypt(write_key, nonce, inner_plaintext, AAD)
```

The content type (handshake, alert, or application_data) is hidden inside the encrypted payload. The outer record always shows type 23 (application_data) for all post-handshake records, preventing traffic analysis of message types.

### 6.5 Record Layer Sequence Numbers

Each direction (client→server, server→client) maintains independent sequence numbers starting at 0. The sequence number is incremented for each record sent. In TLS 1.3 it is used to derive the nonce (XOR with static IV). In TLS 1.2 it is included in the MAC/AAD.

Sequence numbers reset on:
- TLS 1.2: Each key renegotiation.
- TLS 1.3: Each key update (KeyUpdate message).

Sequence number overflow (exceeding 2^64 - 1) is prohibited; implementations must either terminate the connection or perform a key update before overflow.

---

## 7. The TLS 1.2 Handshake Protocol

The handshake is the most complex part of TLS. It establishes the protocol version, cipher suite, keys, and authenticates the server (and optionally the client).

### 7.1 Full TLS 1.2 Handshake — ASCII Diagram

```
Client                                              Server
  |                                                    |
  |--- ClientHello ---------------------------------->|
  |    + random (32 bytes)                            |
  |    + session_id (0 or previous ID)                |
  |    + cipher_suites (list of supported)            |
  |    + compression_methods (always [null])          |
  |    + extensions:                                  |
  |        server_name (SNI)                          |
  |        supported_groups (curves)                  |
  |        ec_point_formats                           |
  |        signature_algorithms                       |
  |        session_ticket                             |
  |        heartbeat (if supported)                   |
  |                                                    |
  |<-- ServerHello -----------------------------------+
  |    + random (32 bytes)                            |
  |    + session_id                                   |
  |    + cipher_suite (selected one)                  |
  |    + compression_method (null)                    |
  |    + extensions:                                  |
  |        server_name (empty)                        |
  |        supported_groups                           |
  |        session_ticket (if supported)              |
  |                                                    |
  |<-- Certificate -----------------------------------+
  |    + certificate_list (DER-encoded chain)         |
  |                                                    |
  |<-- ServerKeyExchange (if ECDHE/DHE) --------------+
  |    + server_dh_params (ECDH public key, etc.)     |
  |    + signature (over server_random + client_random|
  |                  + server_dh_params)              |
  |                                                    |
  |<-- CertificateRequest (if mTLS) ------------------+
  |    + certificate_types                            |
  |    + signature_algorithms                         |
  |    + certificate_authorities (list of accepted)   |
  |                                                    |
  |<-- ServerHelloDone --------------------------------+
  |    (empty — signals end of server hello flight)   |
  |                                                    |
  |--- Certificate (if mTLS) ----------------------->|
  |    + client's certificate chain                   |
  |                                                    |
  |--- ClientKeyExchange --------------------------->|
  |    For RSA:  EncryptedPreMasterSecret             |
  |    For ECDHE: client ECDH public key              |
  |                                                    |
  |--- CertificateVerify (if mTLS) ----------------->|
  |    + signature over handshake transcript          |
  |                                                    |
  |--- ChangeCipherSpec ---------------------------->|
  |    (switches to negotiated cipher)                |
  |                                                    |
  |--- Finished ------------------------------------>|
  |    + verify_data = PRF(master_secret,             |
  |                        "client finished",         |
  |                        Hash(handshake_messages))  |
  |    [ENCRYPTED with new keys]                      |
  |                                                    |
  |<-- ChangeCipherSpec ------------------------------+
  |                                                    |
  |<-- Finished --------------------------------------+
  |    + verify_data = PRF(master_secret,             |
  |                        "server finished",         |
  |                        Hash(handshake_messages))  |
  |    [ENCRYPTED with new keys]                      |
  |                                                    |
  |<====== Application Data (encrypted) =============>|
  |                                                    |
```

### 7.2 Handshake Message Format

Each handshake message is wrapped in a common header:

```
+------+--------+--------+--------+------- ... ------+
| type | length (3 bytes, big-endian)  |    body      |
|(1 B) |   MSB   |   mid   |   LSB   |               |
+------+---------+---------+---------+------- ... ---+
```

Handshake message types:

| Type | Value | Direction |
|------|-------|-----------|
| hello_request | 0 | S→C |
| client_hello | 1 | C→S |
| server_hello | 2 | S→C |
| certificate | 11 | S→C, C→S |
| server_key_exchange | 12 | S→C |
| certificate_request | 13 | S→C |
| server_hello_done | 14 | S→C |
| certificate_verify | 15 | C→S |
| client_key_exchange | 16 | C→S |
| finished | 20 | C→S, S→C |

### 7.3 ClientHello — Detailed Wire Format

```
struct {
    ProtocolVersion client_version;     // 0x0303 (TLS 1.2)
    Random random;                      // 4-byte timestamp (deprecated, now just random)
                                        // + 28 bytes random
    SessionID session_id;               // 0..32 bytes
    CipherSuite cipher_suites<2..2^16-2>;  // list of 2-byte cipher suite codes
    CompressionMethod compression_methods<1..2^8-1>;  // [0x00] = null
    Extension extensions<0..2^16-1>;   // optional extensions list
} ClientHello;
```

**ClientHello Random (32 bytes):**

In TLS 1.2, the first 4 bytes were a Unix timestamp (for clock skew detection). RFC 5246 deprecated this. The random bytes are used as part of the master secret derivation and to prevent replay attacks.

TLS 1.3 downgrade protection: When a TLS 1.3 server is forced to negotiate TLS 1.2, it sets the last 8 bytes of its ServerHello random to a specific sentinel value (`44 4F 57 4E 47 52 44 01` for TLS 1.2, `44 4F 57 4E 47 52 44 00` for TLS 1.1 or below). This allows TLS 1.3 clients to detect illegitimate downgrade attacks.

### 7.4 Key Derivation in TLS 1.2

After the handshake establishes cryptographic material:

**Step 1: PreMasterSecret**

For RSA key exchange:
```
pre_master_secret = client_version (2 bytes) || random_bytes (46 bytes)
(generated by client, encrypted with server's RSA public key)
```

For ECDHE:
```
pre_master_secret = x-coordinate of (client_ephemeral_private * server_ephemeral_public)
```

**Step 2: MasterSecret**

```
master_secret = PRF(pre_master_secret,
                    "master secret",
                    ClientHello.random || ServerHello.random) [48 bytes]
```

The "master secret" label and the client/server randoms prevent the same pre-master secret from producing the same master secret in two different sessions.

**Step 3: Key Material Expansion**

```
key_block = PRF(master_secret,
                "key expansion",
                ServerHello.random || ClientHello.random)
                [as many bytes as needed]

Slice key_block:
  client_write_MAC_key  [mac_key_length bytes]
  server_write_MAC_key  [mac_key_length bytes]
  client_write_key      [enc_key_length bytes]
  server_write_key      [enc_key_length bytes]
  client_write_IV       [iv_length bytes]  (for AEAD)
  server_write_IV       [iv_length bytes]  (for AEAD)
```

Six distinct keys are derived, one for each direction and purpose. The client uses `client_write_*` for encryption and `server_write_*` for decryption. The server uses the reverse. This prevents key reuse between directions.

### 7.5 The Finished Message — Handshake Authentication

The Finished message is the most important message in the handshake. It proves that:
1. Both sides negotiated the same cipher suite and parameters.
2. The handshake was not tampered with.
3. Both sides derived the same keys (because the Finished is encrypted and MACed).

```
verify_data = PRF(master_secret,
                  finished_label,       -- "client finished" or "server finished"
                  Hash(handshake_messages))  -- running hash of ALL handshake messages

Length: 12 bytes (default for SHA-256 PRF)
```

The `Hash(handshake_messages)` is a running digest of every handshake message sent/received, in order, from ClientHello through CertificateVerify (excluding ChangeCipherSpec). If an attacker modified any handshake message, the hash would differ, the verify_data would differ, and the connection would fail.

The Finished message itself is sent encrypted with the newly negotiated cipher. If the peer can decrypt and verify the Finished, it confirms the keys are correct.

---

## 8. The TLS 1.3 Handshake Protocol

TLS 1.3 radically redesigns the handshake to:
1. Reduce it to **1 round-trip** (1-RTT) instead of 2.
2. Encrypt more of the handshake earlier.
3. Remove all non-PFS key exchange.
4. Formalize the key schedule with HKDF.

### 8.1 TLS 1.3 Full 1-RTT Handshake — ASCII Diagram

```
Client                                              Server
  |                                                    |
  |--- ClientHello ---------------------------------->|
  |    + legacy_version = 0x0303                      |
  |    + random (32 bytes)                            |
  |    + legacy_session_id (for compatibility)        |
  |    + cipher_suites:                               |
  |        TLS_AES_128_GCM_SHA256                     |
  |        TLS_AES_256_GCM_SHA384                     |
  |        TLS_CHACHA20_POLY1305_SHA256               |
  |    + legacy_compression_methods = [0]             |
  |    + extensions:                                  |
  |        supported_versions: [0x0304 (TLS1.3)]     |
  |        supported_groups: [x25519, P-256, ...]    |
  |        key_share: (client ECDH public key         |
  |                    for preferred group)           |
  |        signature_algorithms: [rsa_pss_rsae_sha256,|
  |                                ecdsa_secp256r1, ..]|
  |        server_name: [hostname]                    |
  |        psk_key_exchange_modes (if resuming)       |
  |        pre_shared_key (if resuming)               |
  |                                                    |
  |     [Server derives handshake keys immediately    |
  |      from client's key_share — no round trip!]    |
  |                                                    |
  |<-- ServerHello -----------------------------------+
  |    + legacy_version = 0x0303                      |
  |    + random (32 bytes)                            |
  |    + legacy_session_id_echo                       |
  |    + cipher_suite (selected)                      |
  |    + extensions:                                  |
  |        supported_versions: 0x0304                 |
  |        key_share: (server ECDH public key)        |
  |       [optional: pre_shared_key (if resuming)]    |
  |                                                    |
  |    [Both sides compute handshake_secret now]      |
  |                                                    |
  |<-- {EncryptedExtensions} ------------------------+  <-- Encrypted!
  |    + server extensions that need encryption:     |
  |        server_name (confirmation)                 |
  |        alpn (selected protocol)                   |
  |        heartbeat, etc.                            |
  |                                                    |
  |<-- {CertificateRequest} (if mTLS) ---------------+  <-- Encrypted
  |                                                    |
  |<-- {Certificate} ---------------------------------+  <-- Encrypted
  |    + certificate_list                             |
  |      each entry: cert DER + extensions            |
  |        (e.g., status_request → OCSP staple)       |
  |                                                    |
  |<-- {CertificateVerify} ---------------------------+  <-- Encrypted
  |    + algorithm                                    |
  |    + signature over:                              |
  |        0x20 * 64 (space padding)                  |
  |        "TLS 1.3, server CertificateVerify"        |
  |        0x00                                       |
  |        Transcript-Hash(ClientHello...Certificate) |
  |                                                    |
  |<-- {Finished} ------------------------------------+  <-- Encrypted
  |    + HMAC(finished_key, Transcript-Hash(...))     |
  |                                                    |
  |    [Client verifies cert chain + CertVerify sig]  |
  |    [Client derives application keys]              |
  |                                                    |
  |--- {Certificate} (if mTLS) --------------------->|  <-- Encrypted
  |--- {CertificateVerify} (if mTLS) --------------->|  <-- Encrypted
  |--- {Finished} ---------------------------------->|  <-- Encrypted
  |                                                    |
  |<====== {Application Data} (encrypted) ============>|
  |                                                    |
```

Curly braces `{...}` indicate encrypted messages.

### 8.2 TLS 1.3 Key Schedule

The TLS 1.3 key schedule is the heart of the protocol. Every key is derived from a chain of HKDF operations with specific transcript inputs. This is what makes the security proofs work.

```
                    0
                    |
                    v
PSK (or 0) ---> HKDF-Extract = Early Secret
                    |
                    +---> Derive-Secret(., "ext binder" | "res binder", "")
                    |                    = binder_key
                    |
                    +---> Derive-Secret(., "c e traffic", ClientHello)
                    |                    = client_early_traffic_secret
                    |
                    +---> Derive-Secret(., "e exp master", ClientHello)
                    |                    = early_exporter_master_secret
                    |
                    v
(EC)DHE  ------> HKDF-Extract = Handshake Secret
                    |
                    +---> Derive-Secret(., "c hs traffic", CH..SH)
                    |                    = client_handshake_traffic_secret
                    |
                    +---> Derive-Secret(., "s hs traffic", CH..SH)
                    |                    = server_handshake_traffic_secret
                    |
                    v
0        ------> HKDF-Extract = Master Secret
                    |
                    +---> Derive-Secret(., "c ap traffic", CH..server Finished)
                    |                    = client_application_traffic_secret_0
                    |
                    +---> Derive-Secret(., "s ap traffic", CH..server Finished)
                    |                    = server_application_traffic_secret_0
                    |
                    +---> Derive-Secret(., "exp master",   CH..server Finished)
                    |                    = exporter_master_secret
                    |
                    +---> Derive-Secret(., "res master",   CH..client Finished)
                                         = resumption_master_secret
```

**Where:**
```
Derive-Secret(Secret, Label, Messages) =
  HKDF-Expand-Label(Secret, Label, Transcript-Hash(Messages), Hash.length)

HKDF-Expand-Label(Secret, Label, Context, Length) =
  HKDF-Expand(Secret, HkdfLabel, Length)

HkdfLabel = Length (2 bytes) || "tls13 " (6 bytes) || Label || Context
```

**Deriving actual keys from traffic secrets:**

```
[sender]_write_key = HKDF-Expand-Label(traffic_secret, "key", "", key_length)
[sender]_write_IV  = HKDF-Expand-Label(traffic_secret, "iv",  "", iv_length)
finished_key       = HKDF-Expand-Label(traffic_secret, "finished", "", Hash.length)
```

### 8.3 Three Encryption Phases in TLS 1.3

**Phase 1: Initial Plaintext (unencrypted)**
- ClientHello
- ServerHello

**Phase 2: Handshake Encryption (handshake_traffic_secret)**
- Server: EncryptedExtensions, CertificateRequest, Certificate, CertificateVerify, Finished
- Client: Certificate (if requested), CertificateVerify (if requested), Finished

**Phase 3: Application Encryption (application_traffic_secret_0)**
- All application data
- Post-handshake messages: NewSessionTicket, KeyUpdate, CertificateRequest

### 8.4 TLS 1.3 0-RTT Early Data

TLS 1.3 supports 0-RTT resumption where the client can send application data with the ClientHello before the handshake completes. This is possible because the client and server share a Pre-Shared Key (PSK) from a previous session (via NewSessionTicket).

```
Client                                              Server
  |                                                    |
  |--- ClientHello ---------------------------------->|
  |    + pre_shared_key extension                     |
  |    + early_data extension                         |
  |    + psk_key_exchange_modes                       |
  |                                                    |
  |--- {Early Data} (encrypted with early_secret) --->|
  |    (Application data sent before server responds) |
  |                                                    |
  |<-- ServerHello (PSK accepted or rejected) --------+
  |<-- EncryptedExtensions                            |
  |    + early_data extension (if accepted)           |
  |<-- Finished                                       |
  |                                                    |
  |--- EndOfEarlyData -------------------------------->|
  |--- Finished ------------------------------------>|
  |                                                    |
```

**0-RTT Security Limitations:**

0-RTT data does NOT provide forward secrecy — it's protected only by the PSK (which is derived from the previous session). More critically:

- **Replay attacks:** A network attacker can record the 0-RTT data and replay it to another server instance. Servers must implement anti-replay mechanisms (session ticket database, one-time use tracking) or only accept idempotent requests (GET) in 0-RTT.
- TLS 1.3 explicitly warns that applications must account for replay risk.

### 8.5 TLS 1.3 Post-Handshake Messages

After the handshake completes, TLS 1.3 supports several encrypted post-handshake messages:

**NewSessionTicket:**
Server sends a resumption ticket for future 0-RTT or 1-RTT PSK resumption.

```
struct {
    uint32 ticket_lifetime;     // seconds (max 604800 = 7 days)
    uint32 ticket_age_add;      // random obfuscation factor
    opaque ticket_nonce<0..255>;
    opaque ticket<1..2^16-1>;   // opaque server state
    Extension extensions<0..2^16-2>;
        // early_data: max_early_data_size
} NewSessionTicket;
```

**KeyUpdate:**
Requests the peer to update traffic keys. Both sides ratchet the traffic secret:

```
application_traffic_secret_N+1 =
  HKDF-Expand-Label(application_traffic_secret_N, "traffic upd", "", Hash.length)
```

---

## 9. The Alert Protocol

Alerts signal error conditions or warnings. An alert is a 2-byte structure:

```
struct {
    AlertLevel    level;       // 1 = warning, 2 = fatal
    AlertDescription description;
} Alert;
```

The entire 2-byte alert is sent as a TLS record (content type 21). In TLS 1.3, all alerts are sent encrypted.

**Alert Levels:**
- **Warning (1):** The connection may continue. TLS 1.3 largely deprecated most warnings.
- **Fatal (2):** The connection is immediately terminated. Both sides must invalidate any session IDs/tickets.

**Common Alert Descriptions:**

| Value | Name | Meaning |
|-------|------|---------|
| 0 | close_notify | Orderly shutdown — sender will send no more data |
| 10 | unexpected_message | Received inappropriate message |
| 20 | bad_record_mac | MAC verification failure |
| 21 | decryption_failed_RESERVED | Historic, prohibited |
| 22 | record_overflow | Record too long |
| 40 | handshake_failure | No acceptable cipher suite |
| 42 | bad_certificate | Certificate corrupt |
| 43 | unsupported_certificate | Certificate type not supported |
| 44 | certificate_revoked | Certificate was revoked |
| 45 | certificate_expired | Certificate is expired |
| 46 | certificate_unknown | Other cert issue |
| 47 | illegal_parameter | Handshake field out of range |
| 48 | unknown_ca | CA not trusted |
| 49 | access_denied | Client cert rejected |
| 50 | decode_error | Field could not be decoded |
| 51 | decrypt_error | Handshake crypto operation failed |
| 70 | protocol_version | Version not supported |
| 71 | insufficient_security | Cipher suites too weak |
| 80 | internal_error | Internal error unrelated to peer |
| 86 | inappropriate_fallback | Rejected TLS_FALLBACK_SCSV |
| 90 | user_canceled | User canceled |
| 100 | no_renegotiation | TLS 1.2 renegotiation declined |
| 109 | missing_extension | Required extension absent |
| 110 | unsupported_extension | Extension in wrong message |
| 112 | unrecognized_name | SNI name not served |
| 113 | bad_certificate_status_response | OCSP invalid |
| 115 | unknown_psk_identity | PSK identity not found |
| 116 | certificate_required | Client cert required (TLS 1.3) |
| 120 | no_application_protocol | ALPN: no mutual protocol |

**close_notify Shutdown Sequence:**

A proper TLS shutdown requires sending `close_notify` before closing the TCP connection. This prevents truncation attacks where an attacker forces a TCP RST to cut the connection short without the application knowing data may be missing.

```
Sender:  AlertLevel=1 (warning), AlertDescription=0 (close_notify)
           → "I will send no more data"
Receiver: Should also send close_notify
           → "I acknowledge; I will send no more data either"
```

In TLS 1.3, `close_notify` is always a warning. Fatal alerts immediately terminate both directions without waiting for acknowledgment.

---

## 10. The Change Cipher Spec Protocol

CCS is the simplest sub-protocol: a single byte `0x01` sent as a record with content type 20. In TLS 1.2, it signals: "I am now switching to the negotiated cipher suite and keys. Everything I send after this is encrypted."

```
Content of CCS record:
  0x01  (1 byte)

Processing:
  1. Client sends CCS after ClientKeyExchange (and CertificateVerify if mTLS)
  2. Server activates client's write keys as its read keys
  3. Client sends Finished (encrypted)
  4. Server sends CCS after receiving client Finished
  5. Client activates server's write keys as its read keys
  6. Server sends Finished (encrypted)
```

**TLS 1.3 and CCS:**

TLS 1.3 eliminated CCS from the protocol design — it has no CCS record in normal operation. However, for middlebox compatibility, TLS 1.3 implementations send a fake CCS record (in the style of TLS 1.2) during the handshake so that TLS-unaware middleboxes (firewalls, load balancers) don't drop the connection. This is the "compatibility mode" (RFC 8446, Appendix D.4).

---

## 11. Cipher Suites In Depth

A cipher suite is a named combination of algorithms used in a TLS session. Each has a standardized 2-byte code.

### 11.1 TLS 1.2 Cipher Suite Naming Convention

```
TLS_[KeyExchange]_[Authentication]_WITH_[BulkCipher]_[Mode]_[MAC]

Examples:
  TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
  TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
  TLS_DHE_RSA_WITH_AES_128_CBC_SHA256
  TLS_RSA_WITH_AES_128_CBC_SHA

Components:
  KeyExchange:  RSA, DHE, ECDHE, PSK, ...
  Auth:         RSA, ECDSA, DSA, PSK
  BulkCipher:   AES_128, AES_256, CHACHA20, 3DES, RC4 (broken)
  Mode:         GCM, CCM, CBC (GCM/CCM are AEAD, CBC is not)
  MAC:          SHA256, SHA384, SHA (SHA-1, weak)
```

**Recommended TLS 1.2 cipher suites (2024+):**

```
TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256   0xC02B
TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256     0xC02F
TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384   0xC02C
TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384     0xC030
TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256  0xCCA9
TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256    0xCCA8
TLS_DHE_RSA_WITH_AES_128_GCM_SHA256       0x009E
TLS_DHE_RSA_WITH_AES_256_GCM_SHA384       0x009F
```

**Cipher suites to disable immediately:**

```
Any with RC4:    RC4 is completely broken (statistical biases)
Any with NULL:   No encryption
Any with EXPORT: Intentionally weakened (40-bit keys)
Any with anon:   No authentication (DH_anon, ECDH_anon)
Any with DES:    56-bit, brute-forceable
Any with 3DES:   SWEET32 birthday attack (64-bit block cipher)
RSA key exchange: No forward secrecy
```

### 11.2 TLS 1.3 Cipher Suites

TLS 1.3 dramatically simplified cipher suites. The key exchange and authentication are specified separately in extensions (supported_groups, signature_algorithms). The cipher suite only specifies the AEAD + hash function for HKDF:

| Cipher Suite | Code | AEAD | Hash |
|-------------|------|------|------|
| TLS_AES_128_GCM_SHA256 | 0x1301 | AES-128-GCM | SHA-256 |
| TLS_AES_256_GCM_SHA384 | 0x1302 | AES-256-GCM | SHA-384 |
| TLS_CHACHA20_POLY1305_SHA256 | 0x1303 | ChaCha20-Poly1305 | SHA-256 |
| TLS_AES_128_CCM_SHA256 | 0x1304 | AES-128-CCM | SHA-256 |
| TLS_AES_128_CCM_8_SHA256 | 0x1305 | AES-128-CCM-8 | SHA-256 |

All TLS 1.3 cipher suites provide AEAD (both confidentiality and integrity). CCM-8 uses a truncated 8-byte tag (vs 16 bytes for GCM), which slightly weakens authentication — avoid unless constrained devices require it.

### 11.3 The TLS_FALLBACK_SCSV Pseudo-Cipher

`TLS_FALLBACK_SCSV` (`0x5600`) is a pseudo-cipher suite that clients include in ClientHello when they are retrying a failed connection at a lower protocol version. When a server sees this value and the ClientHello version is below the server's maximum, it sends `inappropriate_fallback` alert, detecting that a downgrade attack is in progress. This was critical for defeating POODLE-style attacks.

---

## 12. Key Exchange Mechanisms

### 12.1 RSA Key Exchange (Legacy, No Forward Secrecy)

```
                     Server                  Client
                        |                      |
Server has:             |                      |
  public_key (cert)     |--- Certificate ----->|
  private_key           |                      |
                        |                      |
                        |   Client generates:  |
                        |   PMS = 2-byte ver   |
                        |         + 46 random  |
                        |                      |
                        |<-- ClientKeyExchange -|
                        |    EncryptedPMS =     |
                        |    RSA_Encrypt(       |
                        |      server_pubkey,   |
                        |      PMS)             |
                        |                      |
Server:                 |                      |
  PMS = RSA_Decrypt(    |                      |
    private_key,        |                      |
    EncryptedPMS)       |                      |
```

Both sides then derive the master secret from PMS + client_random + server_random.

**Why it's broken for forward secrecy:** If an adversary records all traffic and later obtains the server's RSA private key (breach, legal order, key compromise), they can decrypt all past sessions by decrypting the EncryptedPMS from each recorded ClientKeyExchange.

### 12.2 ECDHE Key Exchange (TLS 1.2 and 1.3)

```
Server (before handshake):
  Generate ephemeral key pair:
    server_privkey = random scalar s
    server_pubkey  = s * G  (G is curve generator)

Client (before sending ClientKeyExchange):
  Generate ephemeral key pair:
    client_privkey = random scalar c
    client_pubkey  = c * G

ServerKeyExchange message (TLS 1.2):
  Server sends: curve_name, server_pubkey
  Server signs: client_random || server_random || server_params
               (proves server has the private key for the certificate)

ClientKeyExchange (TLS 1.2):
  Client sends: client_pubkey

Shared Secret:
  Server: S = s * (c * G) = s*c*G
  Client: S = c * (s * G) = c*s*G
  (Same point — elliptic curve multiplication is commutative)

  pre_master_secret = S.x  (x-coordinate only)
```

**In TLS 1.3:** Key shares are in extensions (key_share in ClientHello, key_share in ServerHello). There is no separate ServerKeyExchange message.

**Forward Secrecy:** The ephemeral private keys (s, c) are discarded immediately after the shared secret is computed. Even if the certificate's private key is later compromised, the attacker cannot reconstruct s or c, so they cannot compute the shared secret for any past session.

### 12.3 DHE (Finite-Field Diffie-Hellman Ephemeral)

Same concept as ECDHE but using modular arithmetic with finite field:

```
Public parameters: p (large prime), g (generator)
  Standard groups defined in RFC 3526 (1024, 2048, 3072, 4096, 6144, 8192 bits)
  RFC 7919 defines FFDHE groups for TLS: ffdhe2048, ffdhe3072, etc.

Server: a = random; A = g^a mod p; sends A
Client: b = random; B = g^b mod p; sends B

Shared: g^(ab) mod p (= A^b mod p = B^a mod p)
```

DHE is slower than ECDHE and requires larger keys for equivalent security. ECDHE is preferred. Minimum DHE group size: 2048 bits (ffdhe2048). 1024-bit DHE is broken (Logjam attack).

### 12.4 Key Exchange in TLS 1.3 — Client Key Share Prediction

In TLS 1.3, the client sends its ECDH public key in the ClientHello (in the `key_share` extension) without waiting to know which group the server supports. To avoid a round-trip if the server prefers a different group:

- The client sends key shares for its most preferred group(s) (usually X25519, possibly also P-256).
- If the server supports the client's group: it uses the provided key share in ServerHello → 1-RTT.
- If the server doesn't support any offered group: it sends `HelloRetryRequest` with its preferred group → the client regenerates a key share for that group → 2-RTT.

HelloRetryRequest is a special ServerHello with a specific random value (`CF 21 AD 74 E5 9A 61 11 BE 1D 8C 02 1E 65 B8 91 C2 A2 11 16 7A BB 8C 5E 07 9E 09 E2 C8 A8 33 9C`).

---

## 13. Session Resumption

Resumption allows clients to reconnect to a server without performing a full handshake, saving a round-trip and CPU cycles.

### 13.1 TLS 1.2 Session IDs

```
First connection:
  Server includes session_id in ServerHello
  Server stores: session_id → {master_secret, cipher_suite, certificates, ...}

Resumption:
  Client includes previous session_id in ClientHello
  Server finds matching session in cache
  Server echoes the session_id in ServerHello

Abbreviated Handshake:
Client                          Server
  |--- ClientHello (session_id)->|
  |<-- ServerHello (same ID) ---+
  |<-- ChangeCipherSpec --------+
  |<-- Finished ----------------+
  |--- ChangeCipherSpec -------->|
  |--- Finished ---------------->|
  |<== Application Data =======>|

Only 1 RTT instead of 2!
```

Limitation: Session state must be stored server-side. Problematic with load balancers (session must go to the same server, or state must be shared across servers).

### 13.2 TLS 1.2 Session Tickets (RFC 5077)

Session tickets solve the server-side storage problem by encrypting the session state and sending it to the client.

```
Ticket structure (opaque to client):
  HMAC_SHA256(ticket_key, data) || 
  AES_128_CBC_Encrypt(ticket_key, {master_secret, cipher_suite, timestamps, ...})

Resumption:
  Client sends ticket in SessionTicket extension of ClientHello
  Server decrypts ticket with its ticket_key, restores session state
  Server can accept without any stored state!

Ticket Key Rotation:
  Ticket keys should be rotated regularly (e.g., every 24 hours)
  Old keys kept for decryption of existing tickets
  Ticket lifetime typically 24 hours
```

**Forward Secrecy Issue:** If the ticket key is compromised, all sessions whose tickets were issued with that key can be decrypted (the ticket contains the master secret). Ticket key rotation mitigates this but doesn't eliminate it. TLS 1.3 addressed this structurally.

### 13.3 TLS 1.3 PSK Resumption

TLS 1.3 unifies session resumption under the PSK (Pre-Shared Key) mechanism. After a successful handshake, the server sends a `NewSessionTicket` message:

```
resumption_master_secret (from key schedule)
  + ticket_nonce
  → PSK = HKDF-Expand-Label(resumption_master_secret, "resumption", ticket_nonce, Hash.length)
```

The PSK and the opaque ticket (for server state recovery) are given to the client. On the next connection:

```
Client:
  Sends pre_shared_key extension: identity = ticket, obfuscated_ticket_age
  Sends psk_key_exchange_modes: psk_dhe_ke (required for forward secrecy)
  Computes binder = HMAC(binder_key, Transcript-Hash(partial_ClientHello))

Server:
  Recovers PSK from ticket
  Verifies binder (proves client has the PSK)
  Accepts PSK in ServerHello's pre_shared_key extension

Key Schedule with PSK:
  HKDF-Extract(PSK, 0) = Early Secret
  (rest proceeds as normal, but (EC)DHE also mixed in for forward secrecy)
```

**PSK with (EC)DHE:** Mode `psk_dhe_ke` mixes both the PSK and a fresh (EC)DHE exchange into the key schedule. This means:
- The PSK provides fast resumption (client can even send 0-RTT data).
- The (EC)DHE provides forward secrecy (session keys change each time, PSK compromise doesn't expose sessions).

**Ticket Age Obfuscation:** The client sends `obfuscated_ticket_age = (age_ms + ticket_age_add) mod 2^32`. The `ticket_age_add` is a random value from the server (in NewSessionTicket). This prevents observers from correlating connections by ticket age.

---

## 14. Extensions

TLS extensions are a mechanism to add new features without changing the base protocol. They appear in ClientHello, ServerHello, EncryptedExtensions, CertificateRequest, and Certificate messages.

```
Extension wire format:
  struct {
      ExtensionType extension_type;   // 2 bytes
      opaque extension_data<0..2^16-1>;
  } Extension;
```

### 14.1 Critical Extensions

**SNI — Server Name Indication (RFC 6066, ext type 0):**

SNI allows a client to tell the server which hostname it's trying to reach before the TLS handshake completes. This enables one IP address to host multiple TLS-enabled virtual hosts (like HTTP Host header).

```
Extension data:
  struct {
      NameType name_type;    // 0 = host_name
      opaque name<1..2^16-1>;  // e.g., "www.example.com"
  } ServerName;
```

The server uses the SNI to select the appropriate certificate and configuration. In TLS 1.3, SNI is encrypted (it's in EncryptedExtensions from server → client, and the client's SNI in ClientHello is still visible — Encrypted Client Hello / ECH is being standardized to fix this).

**ALPN — Application Layer Protocol Negotiation (RFC 7301, ext type 16):**

ALPN allows negotiating the application protocol (HTTP/1.1, h2, h3, spdy, ftp, etc.) within the TLS handshake, avoiding an extra round-trip.

```
ClientHello extension:
  ["h2", "http/1.1"]  (in preference order)

ServerHello/EncryptedExtensions (TLS 1.3) response:
  "h2"  (selected protocol, or error if none match)
```

**Supported Groups (ext type 10):**

Client advertises which elliptic curves or FFDHE groups it supports:
```
[x25519, secp256r1, secp384r1, secp521r1, ffdhe2048, ffdhe3072]
```

**Key Share (TLS 1.3, ext type 51):**

Client includes ECDH public keys:
```
struct {
    NamedGroup group;
    opaque key_exchange<1..2^16-1>;
} KeyShareEntry;
```

**Signature Algorithms (ext type 13):**

Client lists acceptable signature algorithm + hash combinations for certificates:
```
[ecdsa_secp256r1_sha256, ecdsa_secp384r1_sha384, rsa_pss_rsae_sha256,
 rsa_pss_rsae_sha384, rsa_pss_pss_sha256, rsa_pkcs1_sha256, ...]
```

**Session Ticket (RFC 5077, ext type 35):**

For TLS 1.2 session ticket resumption.

**Status Request / OCSP Stapling (RFC 6066, ext type 5):**

Client requests OCSP status to be stapled into the Certificate message:
```
CertificateStatus message (TLS 1.2) or Certificate extension (TLS 1.3):
  status_type = ocsp
  response = DER-encoded OCSP response signed by CA
```

This allows real-time certificate revocation status without the client making a separate OCSP request (which leaks browsing behavior to the CA).

**Extended Master Secret (RFC 7627, ext type 23):**

In TLS 1.2, changes the master secret derivation to include the full handshake hash, preventing triple handshake attacks:
```
master_secret = PRF(pre_master_secret,
                    "extended master secret",
                    session_hash)   ← instead of client_random || server_random
```

**Encrypt-then-MAC (RFC 7366, ext type 22):**

For TLS 1.2 CBC cipher suites: switches MAC order from MAC-then-encrypt to Encrypt-then-MAC, mitigating padding oracle attacks.

**Supported Versions (TLS 1.3, ext type 43):**

In ClientHello, lists supported TLS versions. In ServerHello, the selected version. This is how TLS 1.3 negotiation works (the legacy version field is always 0x0303 for TLS 1.2 compatibility).

**Pre-Shared Key (TLS 1.3, ext type 41):**

For PSK resumption: contains PSK identities and binders.

**Early Data (TLS 1.3, ext type 42):**

Signals intent to send 0-RTT early data.

**Heartbeat (RFC 6520, ext type 15):**

Keep-alive mechanism. **This is the extension exploited by Heartbleed (CVE-2014-0160).**

---

## 15. Mutual TLS (mTLS)

Standard TLS only authenticates the server. mTLS (mutual TLS) also authenticates the client via a client certificate. This is used in:
- API security between microservices
- Zero-trust networking
- IoT device authentication
- VPN gateways

### 15.1 mTLS Handshake Flow

```
Client                                              Server
  |--- ClientHello ---------------------------------->|
  |<-- ServerHello -----------------------------------+
  |<-- Certificate (server cert) --------------------+
  |<-- ServerKeyExchange (if ECDHE) -----------------+
  |<-- CertificateRequest ---------------------------+
  |    + certificate_types: [rsa_sign, ecdsa_sign]  |
  |    + signature_algorithms: [...]                 |
  |    + certificate_authorities: [list of DN]       |
  |<-- ServerHelloDone --------------------------------+
  |                                                    |
  |--- Certificate (client cert) ------------------>|
  |    (empty if client has none: server may          |
  |     send handshake_failure or proceed)            |
  |--- ClientKeyExchange --------------------------->|
  |                                                    |
  |--- CertificateVerify --------------------------->|
  |    algorithm: rsa_pss_rsae_sha256                 |
  |    signature: Sign(client_privkey,                |
  |       handshake_messages_hash)                    |
  |    (proves client possesses private key for cert) |
  |                                                    |
  |--- ChangeCipherSpec --------------------------->|
  |--- Finished ------------------------------------>|
  |<-- ChangeCipherSpec ----------------------------+
  |<-- Finished ------------------------------------+
```

### 15.2 CertificateVerify in TLS 1.3

In TLS 1.3, the CertificateVerify signature covers a carefully constructed message to prevent cross-protocol attacks:

```
Digital Signature Input:
  0x20 repeated 64 times (space characters)
  || context string:
     "TLS 1.3, server CertificateVerify" (server)
     "TLS 1.3, client CertificateVerify" (client)
  || 0x00 (separator byte)
  || Transcript-Hash(ClientHello ... Certificate)

Signature Algorithm: From supported signature_algorithms extension
  rsa_pss_rsae_sha256, ecdsa_secp256r1_sha256, ed25519, etc.
```

The 64 space bytes prevent a TLS 1.3 signature from being misinterpreted as a signature in another protocol context.

---

## 16. Certificate Lifecycle and Revocation

### 16.1 CRL (Certificate Revocation List)

A CA periodically publishes a signed list of serial numbers of revoked certificates:

```
CRL structure (DER-encoded):
  version, issuer (CA DN)
  thisUpdate, nextUpdate
  revokedCertificates: [
    {serialNumber, revocationDate, reason (optional)}
  ]
  signature by CA
```

**Limitations:**
- CRLs can be large (megabytes for large CAs).
- Clients must download and cache CRLs.
- Revocation is only reflected in the next CRL publication (up to 7 days).
- Clients historically often soft-fail (ignore CRL errors).

### 16.2 OCSP (Online Certificate Status Protocol, RFC 6960)

OCSP allows point-in-time revocation queries for individual certificates:

```
OCSP Request:
  hashAlgorithm
  issuerNameHash = Hash(certificate.issuer)
  issuerKeyHash  = Hash(issuer's public key)
  serialNumber   = certificate.serialNumber

OCSP Response (signed by OCSP responder, delegated by CA):
  responseStatus (successful, malformedRequest, internalError, ...)
  certStatus: good | revoked {revocationTime, reason} | unknown
  thisUpdate, nextUpdate
  producedAt timestamp
  signature
```

**OCSP Stapling:**

Instead of the client querying OCSP (which reveals what sites they visit to the CA), the server queries OCSP, caches the signed response, and staples it to the TLS handshake:

```
TLS 1.2:
  Client: status_request extension in ClientHello
  Server: CertificateStatus message with OCSP response

TLS 1.3:
  OCSP response in the Certificate message extensions
  (one per certificate entry in the chain)
```

**OCSP Must-Staple:**

An X.509 extension (`id-pe-tlsfeature`) that demands OCSP stapling. If a browser connects to a server with a Must-Staple certificate but no valid OCSP staple is provided, the connection fails. This prevents soft-fail behavior.

### 16.3 Certificate Transparency (CT, RFC 9162)

Certificate Transparency is a public audit mechanism. CAs are required to log every certificate they issue to publicly auditable CT logs (append-only Merkle tree logs). A Signed Certificate Timestamp (SCT) is proof that a log accepted the certificate.

```
CT Log (Merkle Tree):
  Each leaf = hash(log_entry) where log_entry = {cert, timestamp, extensions}
  Root hash = Merkle root (publicly auditable)

SCT format:
  version (1 byte)
  log_id (32 bytes — SHA-256 of log's public key)
  timestamp (8 bytes)
  extensions (variable)
  signature (ECDSA or RSA)
```

**How CT prevents mis-issuance:**
- If a CA issues a fraudulent certificate (e.g., attacker bribes CA to issue cert for google.com), it must submit it to a CT log.
- CT monitors (Google, Mozilla, etc.) watch all logs for suspicious certificates.
- Domain owners can set up alerts for unauthorized certificates.

**SCT delivery:**
1. Embedded in the certificate X.509 extension (v2 SCT list).
2. In the TLS handshake via OCSP response.
3. Via TLS extension `signed_certificate_timestamp`.

---

## 17. Protocol Attack Surface and Historical Vulnerabilities

Understanding attacks builds the mental model for why TLS 1.3 made the design choices it did.

### 17.1 BEAST (Browser Exploit Against SSL/TLS, 2011)

**Target:** TLS 1.0 and SSL 3.0 CBC mode.

**Root cause:** In TLS 1.0, the IV for CBC was the last ciphertext block of the previous record (implicit IV). This means the IV was predictable.

**Attack:** An attacker who can inject JavaScript into the victim's browser (same-origin or CRIME-style) can choose plaintexts that, when CBC-encrypted with the known (predictable) IV, reveal the secret (e.g., session cookie) byte by byte.

```
TLS 1.0 CBC:
  C[n] = Encrypt(P[n] XOR C[n-1])   ← C[n-1] is the PREVIOUS record's last block
                                          (IV for next record is KNOWN to attacker)
  
  If attacker can guess P[n], they can check: Encrypt(P[n] XOR C[n-1]) == C[n]?
  → Confirms or denies their guess
  → Repeat byte by byte → cookie recovered
```

**Fix:** TLS 1.1 introduced explicit random IVs per record. Browser mitigations (1/n-1 record splitting) also helped. TLS 1.3 eliminated CBC entirely.

### 17.2 CRIME (Compression Ratio Info-leak Made Easy, 2012)

**Target:** TLS compression (DEFLATE) combined with HTTPS.

**Root cause:** If TLS compresses data before encrypting, the compressed length leaks information. The attacker can inject guesses alongside the secret (in the same HTTPS request), and a shorter compressed ciphertext indicates the guess matched.

**Attack:**
```
Request with secret cookie:
  "Cookie: session=ABC123\r\nCookie-Prefix: A"
  
  If the guess is correct, DEFLATE finds "A" twice in the cookie header
  → compressed size is smaller
  → attacker observes shorter ciphertext length
  → confirms guess for first character, repeats for each byte
```

**Fix:** TLS compression was completely removed from all implementations. HTTP response compression (BREACH, 2013) is a related attack with different mitigations.

### 17.3 POODLE (Padding Oracle On Downgraded Legacy Encryption, 2014)

**Target:** SSL 3.0 CBC padding.

**Root cause:** SSL 3.0's CBC padding verification only checked the last byte (padding length). The content of padding bytes was not specified and not checked. This creates a padding oracle.

```
SSL 3.0 padding:
  Last byte: padding_length
  Preceding bytes: undefined (can be anything)

If Decrypt(C[n]) XOR C[n-1] has valid last byte → MAC check proceeds
  (even if MAC fails, attacker learns the XOR value of the last block)
```

A timing or error oracle lets the attacker recover plaintext byte by byte.

**Fix:** RFC 7568 prohibited SSL 3.0. TLS_FALLBACK_SCSV prevents downgrade to SSL 3.0.

### 17.4 FREAK (Factoring RSA Export Keys, 2015)

**Target:** Servers that still supported EXPORT cipher suites (40-bit RSA, required by US export controls until 1992).

**Root cause:** A MITM could force the client to use export-grade RSA, factor the 512-bit export key (~$100 on EC2), then MITM the session.

**Fix:** Remove all EXPORT cipher suites from servers and clients. Browser vendors removed support.

### 17.5 Logjam (2015)

**Target:** DHE key exchange with 512-bit or 1024-bit groups.

**Root cause:** The Number Field Sieve algorithm can break discrete log for specific prime groups. If many servers use the same 1024-bit prime (as they did — OpenSSL used two primes for all DHE), the precomputation is amortized across millions of connections.

**Attack:** Precompute NFS for the common 1024-bit primes. Then use a MITM to force DHE with that prime. Compute DH exponent in minutes. Decrypt the session.

NSA was suspected of doing exactly this for years at the national level for 1024-bit groups.

**Fix:** Use DHE groups of at least 2048 bits. Better: use ECDHE.

### 17.6 DROWN (Decrypting RSA with Obsolete and Weakened eNcryption, 2016)

**Target:** Servers sharing an RSA private key between a TLS 1.2 host and an SSL 2.0 host (even if the SSL 2.0 host is a different service).

**Root cause:** SSL 2.0's RSA key exchange oracle (SSLv2 allowed known-plaintext attacks on RSA PKCS#1 v1.5). If the same RSA key is used for both SSL 2.0 and TLS 1.2, the oracle on the SSL 2.0 server allows attacking TLS 1.2 sessions.

**Fix:** Disable SSL 2.0 everywhere. Never share RSA private keys across services.

### 17.7 Heartbleed (CVE-2014-0160)

**Target:** OpenSSL 1.0.1 through 1.0.1f.

**Root cause:** The RFC 6520 Heartbeat extension allows a peer to send a HeartbeatRequest with a payload and payload_length. The server reads `payload_length` bytes from memory and echoes them. OpenSSL failed to validate that `payload_length ≤ actual payload length`.

```
HeartbeatRequest:
  type = 1 (request)
  payload_length = 65535  (claimed)
  payload = "A"           (actual: 1 byte)

OpenSSL response:
  Read 65535 bytes starting from payload → reads 65534 bytes past the payload
  → Echoes process heap memory (private keys, session data, passwords)
```

**Fix:** Validate payload_length. OpenSSL 1.0.1g fixed this. Organizations revoked and reissued all affected certificates.

### 17.8 ROBOT (Return Of Bleichenbacher's Oracle Threat, 2017)

**Target:** RSA PKCS#1 v1.5 encryption in TLS key exchange.

**Root cause:** Daniel Bleichenbacher's 1998 attack: RSA PKCS#1 v1.5 ciphertext decryption oracles (different error codes for "conforming" vs "non-conforming" PKCS#1 structure) allow adaptive chosen-ciphertext attacks. With ~1 million oracle queries, an attacker recovers the decrypted plaintext.

Many implementations in 2017 still had the oracle (timing differences, different error codes). Facebook, Cisco, Citrix, and others were affected.

**Fix:** Use constant-time PKCS#1 v1.5 decryption or, better, use OAEP padding or switch to ECDHE. TLS 1.3 removed RSA key exchange entirely.

### 17.9 Lucky Thirteen (2013)

**Target:** TLS 1.0/1.1/1.2 CBC with MAC-then-Encrypt.

**Root cause:** MAC verification timing. Depending on how many padding bytes need to be checked, MAC computation takes different amounts of time. Precise timing measurements over the network can distinguish between "wrong padding" and "correct padding but bad MAC."

This is a statistical attack requiring thousands of connections and precise timing, but it works.

**Fix:** Encrypt-then-MAC (RFC 7366). Constant-time MAC computation. TLS 1.3 eliminated CBC.

### 17.10 Downgrade Attacks in General

**Protocol Version Downgrade:** An attacker modifies the ClientHello to advertise only TLS 1.0. Vulnerable servers accept. TLS 1.3 added the random sentinel downgrade detection. TLS_FALLBACK_SCSV also helps.

**Cipher Suite Downgrade:** An attacker removes strong cipher suites from the ClientHello. TLS 1.2 doesn't detect this (the Finished message catches it but only after the weak cipher is used). TLS 1.3 hashes the entire transcript into the Finished, so any modification is detected.

**Renegotiation Attack (CVE-2009-3555):** Pre-RFC-5746 TLS 1.2 renegotiation was not bound to the original connection. An attacker could inject data into a renegotiated connection. RFC 5746 (Renegotiation Indication Extension) and TLS 1.3 (removed renegotiation entirely) fixed this.

### 17.11 SWEET32 (Birthday Attack on 64-bit Block Ciphers, 2016)

**Target:** 3DES and Blowfish (64-bit block ciphers) in CBC mode.

**Root cause:** Birthday paradox: with 64-bit blocks, after 2^32 blocks (~32 GB), block collisions become likely. CBC block collisions leak plaintext XOR differences.

**Fix:** Retire 3DES. Limit session lifetime before rekeying when 3DES must be used. TLS 1.3 does not include 3DES.

### 17.12 Triple Handshake Attack (2014)

**Root cause:** In TLS 1.2 without Extended Master Secret, the master secret was derived from just `pre_master_secret || client_random || server_random`. Two different TLS sessions could share the same master secret if they used the same pre-master secret and randoms.

A sophisticated attack allowed an attacker to arrange for a server to authenticate a session that it didn't actually establish.

**Fix:** RFC 7627 Extended Master Secret extension hashes the full handshake transcript into the master secret, making each session's master secret unique.

---

## 18. Implementation in C (OpenSSL)

OpenSSL is the most widely deployed TLS library. Understanding it at the API level reveals how the protocol concepts map to code.

### 18.1 TLS Server in C (OpenSSL)

```c
/*
 * tls_server.c — Production-quality TLS 1.3 server using OpenSSL 3.x
 *
 * Compile: gcc -o tls_server tls_server.c -lssl -lcrypto -Wall -Wextra
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <openssl/ssl.h>
#include <openssl/err.h>
#include <openssl/x509.h>
#include <openssl/x509v3.h>

#define PORT        8443
#define BACKLOG     10
#define BUFFER_SIZE 16384
#define CERT_FILE   "server.crt"
#define KEY_FILE    "server.key"
#define CA_FILE     "ca.crt"      /* For mutual TLS client verification */

/* ─────────────────────────────────────────────────────────────────────────
 * Error utilities
 * ───────────────────────────────────────────────────────────────────────── */

static void ssl_die(const char *msg) {
    fprintf(stderr, "%s\n", msg);
    ERR_print_errors_fp(stderr);
    exit(EXIT_FAILURE);
}

static void sys_die(const char *msg) {
    perror(msg);
    exit(EXIT_FAILURE);
}

/* ─────────────────────────────────────────────────────────────────────────
 * SSL Context Setup — this is where policy lives
 * ───────────────────────────────────────────────────────────────────────── */

static SSL_CTX *create_server_ctx(void) {
    /* Use TLS_server_method() — accepts TLS 1.0 through TLS 1.3.
     * We restrict the minimum version below. */
    const SSL_METHOD *method = TLS_server_method();
    SSL_CTX *ctx = SSL_CTX_new(method);
    if (!ctx)
        ssl_die("Failed to create SSL_CTX");

    /* ── Version constraints ──────────────────────────────────────────── */
    /* Only accept TLS 1.2 and above */
    if (SSL_CTX_set_min_proto_version(ctx, TLS1_2_VERSION) != 1)
        ssl_die("Failed to set minimum TLS version");

    /* Allow up to TLS 1.3 (TLS1_3_VERSION = maximum known) */
    if (SSL_CTX_set_max_proto_version(ctx, TLS1_3_VERSION) != 1)
        ssl_die("Failed to set maximum TLS version");

    /* ── Cipher suite configuration ───────────────────────────────────── */
    /* TLS 1.2 cipher suites — ECDHE + AEAD only, ordered by preference.
     * The colon-separated OpenSSL cipher string.
     * !aNULL  = no anonymous key exchange
     * !eNULL  = no null encryption
     * !EXPORT = no export-grade ciphers
     * !RC4    = no RC4
     * !3DES   = no triple DES
     * !MD5    = no MD5 MAC */
    if (SSL_CTX_set_cipher_list(ctx,
            "ECDHE-ECDSA-AES256-GCM-SHA384:"
            "ECDHE-RSA-AES256-GCM-SHA384:"
            "ECDHE-ECDSA-AES128-GCM-SHA256:"
            "ECDHE-RSA-AES128-GCM-SHA256:"
            "ECDHE-ECDSA-CHACHA20-POLY1305:"
            "ECDHE-RSA-CHACHA20-POLY1305:"
            "!aNULL:!eNULL:!EXPORT:!RC4:!3DES:!MD5") != 1)
        ssl_die("Failed to set TLS 1.2 cipher list");

    /* TLS 1.3 cipher suites — OpenSSL uses a separate API */
    if (SSL_CTX_set_ciphersuites(ctx,
            "TLS_AES_256_GCM_SHA384:"
            "TLS_CHACHA20_POLY1305_SHA256:"
            "TLS_AES_128_GCM_SHA256") != 1)
        ssl_die("Failed to set TLS 1.3 cipher suites");

    /* ── Elliptic curve preference ────────────────────────────────────── */
    /* Prefer X25519 (fastest, simplest), then P-256, then P-384 */
    if (SSL_CTX_set1_groups_list(ctx, "X25519:P-256:P-384") != 1)
        ssl_die("Failed to set EC groups");

    /* ── Options / security flags ─────────────────────────────────────── */
    long opts = SSL_OP_NO_SSLv2          /* Belt and suspenders */
              | SSL_OP_NO_SSLv3
              | SSL_OP_NO_TLSv1
              | SSL_OP_NO_TLSv1_1
              | SSL_OP_NO_COMPRESSION    /* Disable TLS compression (CRIME) */
              | SSL_OP_CIPHER_SERVER_PREFERENCE  /* Server chooses cipher, not client */
              | SSL_OP_SINGLE_DH_USE             /* New DH key per handshake */
              | SSL_OP_SINGLE_ECDH_USE;          /* New ECDH key per handshake */
    SSL_CTX_set_options(ctx, opts);

    /* ── Certificate and private key ──────────────────────────────────── */
    if (SSL_CTX_use_certificate_chain_file(ctx, CERT_FILE) != 1)
        ssl_die("Failed to load certificate chain");

    if (SSL_CTX_use_PrivateKey_file(ctx, KEY_FILE, SSL_FILETYPE_PEM) != 1)
        ssl_die("Failed to load private key");

    /* Verify that the private key matches the certificate's public key */
    if (SSL_CTX_check_private_key(ctx) != 1)
        ssl_die("Certificate and private key do not match");

    /* ── Mutual TLS: verify client certificates ───────────────────────── */
    /* Load the CA cert(s) that are trusted for client auth.
     * SSL_VERIFY_PEER:                require client to send cert
     * SSL_VERIFY_FAIL_IF_NO_PEER_CERT: reject if no cert sent
     * SSL_VERIFY_CLIENT_ONCE:         only verify once (not on renegotiation) */
    if (access(CA_FILE, R_OK) == 0) {
        if (SSL_CTX_load_verify_locations(ctx, CA_FILE, NULL) != 1)
            ssl_die("Failed to load CA certificate for client auth");
        SSL_CTX_set_verify(ctx,
            SSL_VERIFY_PEER | SSL_VERIFY_FAIL_IF_NO_PEER_CERT,
            NULL  /* use default verification callback */);
        SSL_CTX_set_verify_depth(ctx, 4);
        printf("mTLS: client certificate verification enabled\n");
    }

    /* ── Session caching (TLS 1.2) ────────────────────────────────────── */
    /* SSL_SESS_CACHE_SERVER: cache sessions server-side (for session ID resumption)
     * Session tickets are enabled by default unless explicitly disabled. */
    SSL_CTX_set_session_cache_mode(ctx, SSL_SESS_CACHE_SERVER);
    SSL_CTX_set_session_id_context(ctx, (const unsigned char *)"tls_demo", 8);
    SSL_CTX_sess_set_cache_size(ctx, 1024);
    SSL_CTX_set_timeout(ctx, 300);  /* Session timeout: 5 minutes */

    /* ── ALPN ─────────────────────────────────────────────────────────── */
    /* The callback selects from the client's offered protocols.
     * Here we prefer h2, fall back to http/1.1. */
    SSL_CTX_set_alpn_select_cb(ctx,
        (SSL_CTX_alpn_select_cb_func) [](SSL *ssl,
                const unsigned char **out, unsigned char *outlen,
                const unsigned char *in, unsigned int inlen, void *arg) -> int {
            /* Wire format: length-prefixed strings, e.g.: \x02h2\x08http/1.1 */
            const unsigned char *p = in;
            const unsigned char *end = in + inlen;
            /* Try to select h2 first */
            while (p < end) {
                unsigned char len = *p++;
                if (p + len > end) break;
                if (len == 2 && memcmp(p, "h2", 2) == 0) {
                    *out = p; *outlen = len; return SSL_TLSEXT_ERR_OK;
                }
                p += len;
            }
            /* Fall back to http/1.1 */
            p = in;
            while (p < end) {
                unsigned char len = *p++;
                if (p + len > end) break;
                if (len == 8 && memcmp(p, "http/1.1", 8) == 0) {
                    *out = p; *outlen = len; return SSL_TLSEXT_ERR_OK;
                }
                p += len;
            }
            return SSL_TLSEXT_ERR_NOACK;  /* No match — connection continues without ALPN */
        },
        NULL);

    return ctx;
}

/* ─────────────────────────────────────────────────────────────────────────
 * Print TLS session info for debugging
 * ───────────────────────────────────────────────────────────────────────── */

static void print_session_info(SSL *ssl) {
    printf("\n=== TLS Session Info ===\n");
    printf("Protocol:     %s\n", SSL_get_version(ssl));
    printf("Cipher:       %s\n", SSL_get_cipher_name(ssl));

    /* Key bits */
    int bits = 0;
    SSL_get_cipher_bits(ssl, &bits);
    printf("Key bits:     %d\n", bits);

    /* Session resumption */
    if (SSL_session_reused(ssl))
        printf("Resumed:      yes (session reuse)\n");
    else
        printf("Resumed:      no (full handshake)\n");

    /* ALPN */
    const unsigned char *alpn;
    unsigned int alpn_len;
    SSL_get0_alpn_selected(ssl, &alpn, &alpn_len);
    if (alpn_len > 0)
        printf("ALPN:         %.*s\n", alpn_len, alpn);

    /* Server name (SNI) */
    const char *sni = SSL_get_servername(ssl, TLSEXT_NAMETYPE_host_name);
    if (sni)
        printf("SNI:          %s\n", sni);

    /* Peer certificate (for mTLS) */
    X509 *peer = SSL_get_peer_certificate(ssl);
    if (peer) {
        char buf[256];
        X509_NAME_oneline(X509_get_subject_name(peer), buf, sizeof(buf));
        printf("Client cert:  %s\n", buf);

        /* Verify result */
        long verify_result = SSL_get_verify_result(ssl);
        if (verify_result == X509_V_OK)
            printf("Cert verify:  OK\n");
        else
            printf("Cert verify:  FAILED (%s)\n",
                   X509_verify_cert_error_string(verify_result));
        X509_free(peer);
    }
    printf("========================\n\n");
}

/* ─────────────────────────────────────────────────────────────────────────
 * Handle a single client connection
 * ───────────────────────────────────────────────────────────────────────── */

static void handle_client(SSL_CTX *ctx, int client_fd) {
    SSL *ssl = SSL_new(ctx);
    if (!ssl) {
        ssl_die("SSL_new failed");
    }

    /* Associate the SSL object with the socket fd */
    SSL_set_fd(ssl, client_fd);

    /* Perform the TLS handshake.
     * SSL_accept() returns 1 on success, 0 on controlled shutdown,
     * negative on error. */
    int ret = SSL_accept(ssl);
    if (ret != 1) {
        int err = SSL_get_error(ssl, ret);
        fprintf(stderr, "SSL_accept failed: error code %d\n", err);
        ERR_print_errors_fp(stderr);
        goto cleanup;
    }

    print_session_info(ssl);

    /* Read/write application data */
    char buf[BUFFER_SIZE];
    int bytes;

    while ((bytes = SSL_read(ssl, buf, sizeof(buf) - 1)) > 0) {
        buf[bytes] = '\0';
        printf("Received (%d bytes): %s\n", bytes, buf);

        /* Echo back with HTTP/1.1 response */
        const char *response =
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/plain\r\n"
            "Connection: close\r\n"
            "\r\n"
            "Hello from TLS server!\r\n";

        if (SSL_write(ssl, response, (int)strlen(response)) <= 0) {
            fprintf(stderr, "SSL_write failed\n");
            ERR_print_errors_fp(stderr);
            break;
        }
        break;  /* Simple: one request, one response */
    }

    if (bytes < 0) {
        int err = SSL_get_error(ssl, bytes);
        if (err != SSL_ERROR_ZERO_RETURN && err != SSL_ERROR_SYSCALL)
            ERR_print_errors_fp(stderr);
    }

    /* Orderly shutdown: send close_notify alert */
    /* SSL_shutdown returns 0 if close_notify sent but not received.
     * Call again to wait for peer's close_notify. */
    ret = SSL_shutdown(ssl);
    if (ret == 0)
        SSL_shutdown(ssl);

cleanup:
    SSL_free(ssl);
    close(client_fd);
}

/* ─────────────────────────────────────────────────────────────────────────
 * Main
 * ───────────────────────────────────────────────────────────────────────── */

int main(void) {
    /* OpenSSL 3.x auto-initializes, but for OpenSSL 1.x: */
    /* SSL_library_init();
     * SSL_load_error_strings();
     * OpenSSL_add_all_algorithms(); */

    SSL_CTX *ctx = create_server_ctx();

    /* Create TCP socket */
    int server_fd = socket(AF_INET6, SOCK_STREAM, 0);
    if (server_fd < 0)
        sys_die("socket");

    /* Enable dual-stack (IPv4 + IPv6) */
    int no = 0;
    setsockopt(server_fd, IPPROTO_IPV6, IPV6_V6ONLY, &no, sizeof(no));

    /* SO_REUSEADDR avoids "Address already in use" on restart */
    int yes = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(yes));

    struct sockaddr_in6 addr = {
        .sin6_family = AF_INET6,
        .sin6_port   = htons(PORT),
        .sin6_addr   = in6addr_any,
    };

    if (bind(server_fd, (struct sockaddr *)&addr, sizeof(addr)) < 0)
        sys_die("bind");
    if (listen(server_fd, BACKLOG) < 0)
        sys_die("listen");

    printf("TLS server listening on port %d...\n", PORT);

    while (1) {
        struct sockaddr_in6 client_addr;
        socklen_t client_len = sizeof(client_addr);
        int client_fd = accept(server_fd, (struct sockaddr *)&client_addr, &client_len);
        if (client_fd < 0) {
            perror("accept");
            continue;
        }

        char addr_str[INET6_ADDRSTRLEN];
        inet_ntop(AF_INET6, &client_addr.sin6_addr, addr_str, sizeof(addr_str));
        printf("Client connected: %s\n", addr_str);

        /* In production: fork(), or thread pool, or async I/O */
        handle_client(ctx, client_fd);
    }

    SSL_CTX_free(ctx);
    close(server_fd);
    return 0;
}
```

### 18.2 TLS Client in C (OpenSSL)

```c
/*
 * tls_client.c — TLS 1.3 client with full certificate verification
 *
 * Compile: gcc -o tls_client tls_client.c -lssl -lcrypto -Wall -Wextra
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netdb.h>
#include <openssl/ssl.h>
#include <openssl/err.h>
#include <openssl/x509v3.h>

/* ─────────────────────────────────────────────────────────────────────────
 * Verify that the certificate's Subject Alternative Name (or CN)
 * matches the hostname we connected to.
 * OpenSSL 1.1.0+ has SSL_set1_host() which does this automatically.
 * ───────────────────────────────────────────────────────────────────────── */

static int verify_hostname(SSL *ssl, const char *hostname) {
    /* X509_check_host is the correct modern API (RFC 6125 conforming).
     * X509_CHECK_FLAG_NO_PARTIAL_WILDCARDS: disallow *.*.example.com */
    X509 *cert = SSL_get_peer_certificate(ssl);
    if (!cert) {
        fprintf(stderr, "No certificate presented by server\n");
        return 0;
    }

    int result = X509_check_host(cert, hostname, strlen(hostname),
                                  X509_CHECK_FLAG_NO_PARTIAL_WILDCARDS, NULL);
    X509_free(cert);

    if (result != 1) {
        fprintf(stderr, "Certificate hostname mismatch\n");
        return 0;
    }
    return 1;
}

/* ─────────────────────────────────────────────────────────────────────────
 * Create a hardened client SSL_CTX
 * ───────────────────────────────────────────────────────────────────────── */

static SSL_CTX *create_client_ctx(void) {
    SSL_CTX *ctx = SSL_CTX_new(TLS_client_method());
    if (!ctx) {
        ERR_print_errors_fp(stderr);
        exit(EXIT_FAILURE);
    }

    /* Require TLS 1.2 minimum */
    SSL_CTX_set_min_proto_version(ctx, TLS1_2_VERSION);

    /* Certificate verification: use OS trust store */
    /* On Linux: /etc/ssl/certs/ca-certificates.crt or /etc/pki/tls/certs/ca-bundle.crt
     * SSL_CTX_set_default_verify_paths() finds the system's default CA store */
    if (SSL_CTX_set_default_verify_paths(ctx) != 1) {
        fprintf(stderr, "Warning: Failed to load system CA store\n");
        /* Fall back to explicit CA file */
        if (SSL_CTX_load_verify_locations(ctx, "ca-bundle.crt", NULL) != 1) {
            ERR_print_errors_fp(stderr);
            SSL_CTX_free(ctx);
            exit(EXIT_FAILURE);
        }
    }

    /* Require server certificate verification.
     * SSL_VERIFY_PEER: Verify the server's certificate chain.
     * The default callback returns 0 (fail) if verification fails. */
    SSL_CTX_set_verify(ctx, SSL_VERIFY_PEER, NULL);
    SSL_CTX_set_verify_depth(ctx, 10);

    /* Disable compression (CRIME) */
    SSL_CTX_set_options(ctx, SSL_OP_NO_COMPRESSION);

    /* TLS 1.2 cipher suites: AEAD + ECDHE only */
    SSL_CTX_set_cipher_list(ctx,
        "ECDHE-ECDSA-AES256-GCM-SHA384:"
        "ECDHE-RSA-AES256-GCM-SHA384:"
        "ECDHE-ECDSA-AES128-GCM-SHA256:"
        "ECDHE-RSA-AES128-GCM-SHA256:"
        "ECDHE-ECDSA-CHACHA20-POLY1305:"
        "ECDHE-RSA-CHACHA20-POLY1305");

    /* TLS 1.3 cipher suites */
    SSL_CTX_set_ciphersuites(ctx,
        "TLS_AES_256_GCM_SHA384:"
        "TLS_CHACHA20_POLY1305_SHA256:"
        "TLS_AES_128_GCM_SHA256");

    /* mTLS: Load client certificate and key if available */
    if (access("client.crt", R_OK) == 0 && access("client.key", R_OK) == 0) {
        if (SSL_CTX_use_certificate_chain_file(ctx, "client.crt") != 1 ||
            SSL_CTX_use_PrivateKey_file(ctx, "client.key", SSL_FILETYPE_PEM) != 1) {
            ERR_print_errors_fp(stderr);
            SSL_CTX_free(ctx);
            exit(EXIT_FAILURE);
        }
        printf("mTLS: client certificate loaded\n");
    }

    return ctx;
}

/* ─────────────────────────────────────────────────────────────────────────
 * Connect TCP socket to host:port
 * ───────────────────────────────────────────────────────────────────────── */

static int tcp_connect(const char *host, const char *port) {
    struct addrinfo hints = {
        .ai_family   = AF_UNSPEC,     /* IPv4 or IPv6 */
        .ai_socktype = SOCK_STREAM,
    };
    struct addrinfo *res;

    int err = getaddrinfo(host, port, &hints, &res);
    if (err != 0) {
        fprintf(stderr, "getaddrinfo: %s\n", gai_strerror(err));
        return -1;
    }

    int fd = -1;
    for (struct addrinfo *r = res; r; r = r->ai_next) {
        fd = socket(r->ai_family, r->ai_socktype, r->ai_protocol);
        if (fd < 0) continue;
        if (connect(fd, r->ai_addr, r->ai_addrlen) == 0) break;
        close(fd);
        fd = -1;
    }
    freeaddrinfo(res);

    if (fd < 0) {
        perror("connect");
        return -1;
    }
    return fd;
}

/* ─────────────────────────────────────────────────────────────────────────
 * Main
 * ───────────────────────────────────────────────────────────────────────── */

int main(int argc, char *argv[]) {
    const char *host = argc > 1 ? argv[1] : "example.com";
    const char *port = argc > 2 ? argv[2] : "443";

    SSL_CTX *ctx = create_client_ctx();

    int fd = tcp_connect(host, port);
    if (fd < 0) {
        SSL_CTX_free(ctx);
        return EXIT_FAILURE;
    }

    SSL *ssl = SSL_new(ctx);

    /* SNI: Tell the server which hostname we want (critical for virtual hosting).
     * Must be set before SSL_connect(). */
    SSL_set_tlsext_host_name(ssl, host);

    /* Modern equivalent: also sets hostname for verification */
    SSL_set1_host(ssl, host);

    /* ALPN: Prefer HTTP/2 */
    /* Wire format: length-prefixed strings */
    unsigned char alpn_protos[] = "\x02h2\x08http/1.1";
    SSL_set_alpn_protos(ssl, alpn_protos, sizeof(alpn_protos) - 1);

    SSL_set_fd(ssl, fd);

    /* Perform TLS handshake */
    int ret = SSL_connect(ssl);
    if (ret != 1) {
        int err = SSL_get_error(ssl, ret);
        fprintf(stderr, "SSL_connect failed: %d\n", err);
        ERR_print_errors_fp(stderr);
        goto cleanup;
    }

    /* Verify certificate chain result */
    long verify = SSL_get_verify_result(ssl);
    if (verify != X509_V_OK) {
        fprintf(stderr, "Certificate verification failed: %s\n",
                X509_verify_cert_error_string(verify));
        goto cleanup;
    }

    /* Verify hostname (belt and suspenders when not using SSL_set1_host) */
    if (!verify_hostname(ssl, host))
        goto cleanup;

    /* Session info */
    printf("Connected: %s with %s\n", SSL_get_version(ssl), SSL_get_cipher_name(ssl));

    /* Print server certificate info */
    X509 *cert = SSL_get_peer_certificate(ssl);
    if (cert) {
        char buf[256];
        X509_NAME_oneline(X509_get_subject_name(cert), buf, sizeof(buf));
        printf("Server cert subject: %s\n", buf);
        X509_NAME_oneline(X509_get_issuer_name(cert), buf, sizeof(buf));
        printf("Server cert issuer:  %s\n", buf);

        /* Certificate expiry */
        ASN1_TIME *notAfter = X509_get_notAfter(cert);
        printf("Expires: ");
        ASN1_TIME_print(BIO_new_fp(stdout, BIO_NOCLOSE), notAfter);
        printf("\n");

        X509_free(cert);
    }

    /* Send HTTP/1.1 GET request */
    char request[1024];
    int req_len = snprintf(request, sizeof(request),
        "GET / HTTP/1.1\r\n"
        "Host: %s\r\n"
        "Connection: close\r\n"
        "User-Agent: TLS-demo/1.0\r\n"
        "\r\n", host);

    if (SSL_write(ssl, request, req_len) <= 0) {
        fprintf(stderr, "SSL_write failed\n");
        goto cleanup;
    }

    /* Read response */
    char buf[BUFSIZ];
    int bytes;
    printf("\n--- Response ---\n");
    while ((bytes = SSL_read(ssl, buf, sizeof(buf) - 1)) > 0) {
        buf[bytes] = '\0';
        fwrite(buf, 1, bytes, stdout);
    }

    /* Check for error vs clean EOF */
    if (bytes < 0) {
        int err = SSL_get_error(ssl, bytes);
        if (err != SSL_ERROR_ZERO_RETURN)
            ERR_print_errors_fp(stderr);
    }

    /* Orderly shutdown */
    SSL_shutdown(ssl);

cleanup:
    SSL_free(ssl);
    close(fd);
    SSL_CTX_free(ctx);
    return EXIT_SUCCESS;
}
```

### 18.3 Certificate Generation (OpenSSL CLI)

```bash
# ── Generate a CA ──────────────────────────────────────────────────────────

# Generate CA private key (EC P-256)
openssl ecparam -name prime256v1 -genkey -noout -out ca.key

# Generate self-signed CA certificate
openssl req -new -x509 -days 3650 \
    -key ca.key \
    -out ca.crt \
    -subj "/C=US/ST=California/O=My CA/CN=My Root CA"

# ── Generate Server Certificate ───────────────────────────────────────────

# Generate server key (EC P-256)
openssl ecparam -name prime256v1 -genkey -noout -out server.key

# Generate CSR
openssl req -new \
    -key server.key \
    -out server.csr \
    -subj "/C=US/O=My Org/CN=example.com"

# Create extension file with SAN
cat > server_ext.cnf << EOF
[req]
distinguished_name = req_dn
x509_extensions    = v3_req
prompt = no

[req_dn]
CN = example.com

[v3_req]
subjectAltName = @alt_names
keyUsage = digitalSignature
extendedKeyUsage = serverAuth

[alt_names]
DNS.1 = example.com
DNS.2 = www.example.com
IP.1  = 127.0.0.1
EOF

# Sign with CA
openssl x509 -req \
    -in server.csr \
    -CA ca.crt \
    -CAkey ca.key \
    -CAcreateserial \
    -out server.crt \
    -days 365 \
    -extfile server_ext.cnf \
    -extensions v3_req

# Verify the chain
openssl verify -CAfile ca.crt server.crt

# Inspect the certificate
openssl x509 -in server.crt -text -noout

# ── Test with OpenSSL s_client ─────────────────────────────────────────────

# Connect and show full handshake detail:
openssl s_client \
    -connect example.com:443 \
    -tls1_3 \
    -servername example.com \
    -CAfile ca.crt \
    -msg \       # show record layer messages
    -tlsextdebug # show extensions

# Test TLS 1.2 cipher suites:
openssl s_client -connect example.com:443 \
    -tls1_2 \
    -cipher ECDHE-RSA-AES128-GCM-SHA256

# Check certificate transparency:
openssl s_client -connect example.com:443 -status 2>/dev/null | \
    openssl x509 -noout -text | grep -A5 "CT Precertificate"
```

---

## 19. Implementation in Rust

### 19.1 Using rustls — Pure-Rust TLS Implementation

`rustls` is a modern TLS library written entirely in Rust. It only supports TLS 1.2 and 1.3, with no legacy algorithms.

```toml
# Cargo.toml
[dependencies]
rustls = { version = "0.23", features = ["ring"] }
rustls-pemfile = "2"
tokio = { version = "1", features = ["full"] }
tokio-rustls = "0.26"
webpki-roots = "0.26"
rcgen = "0.13"   # for generating test certificates
```

```rust
// tls_server.rs — Async TLS server with tokio + rustls

use std::{
    fs::File,
    io::{self, BufReader},
    net::SocketAddr,
    sync::Arc,
};

use rustls::{
    pki_types::{CertificateDer, PrivateKeyDer},
    ServerConfig,
};
use rustls_pemfile::{certs, private_key};
use tokio::net::TcpListener;
use tokio_rustls::TlsAcceptor;

/// Load PEM-encoded certificate chain from a file.
/// Returns Vec<CertificateDer<'static>>.
fn load_certs(path: &str) -> io::Result<Vec<CertificateDer<'static>>> {
    let f = File::open(path)?;
    let mut reader = BufReader::new(f);
    // certs() returns an iterator of Results; collect and propagate errors
    certs(&mut reader).collect()
}

/// Load a PEM-encoded private key from a file.
/// Tries PKCS#8, PKCS#1 RSA, EC key formats in order.
fn load_private_key(path: &str) -> io::Result<PrivateKeyDer<'static>> {
    let f = File::open(path)?;
    let mut reader = BufReader::new(f);
    // private_key() returns the first key found
    private_key(&mut reader)?
        .ok_or_else(|| io::Error::new(io::ErrorKind::InvalidData, "no private key found"))
}

/// Build a rustls::ServerConfig with hardened settings.
///
/// rustls by default:
///   - Only supports TLS 1.2 and 1.3
///   - Uses safe cipher suites (AES-GCM, ChaCha20-Poly1305)
///   - Requires forward secrecy (ECDHE)
///   - Performs proper certificate verification
fn build_server_config(
    cert_file: &str,
    key_file: &str,
) -> Result<Arc<ServerConfig>, Box<dyn std::error::Error>> {
    let certs = load_certs(cert_file)?;
    let key = load_private_key(key_file)?;

    // rustls::ServerConfig is a builder. The final call resolves the cipher suites.
    // with_ring_crypto_provider() uses the 'ring' cryptographic backend.
    let config = ServerConfig::builder()
        // .with_ring_crypto_provider()  // if feature "ring" used
        // Specify protocol versions: only TLS 1.2 and 1.3
        .with_protocol_versions(&[
            &rustls::version::TLS13,
            &rustls::version::TLS12,
        ])?
        // No client certificate required (change to with_client_cert_verifier for mTLS)
        .with_no_client_auth()
        // Provide the server's certificate chain and private key
        .with_single_cert(certs, key)?;

    // ALPN protocols: prefer HTTP/2, fall back to HTTP/1.1
    // rustls stores these as raw bytes (the wire format)
    let mut config = config;
    config.alpn_protocols = vec![
        b"h2".to_vec(),
        b"http/1.1".to_vec(),
    ];

    // Session resumption via tickets is on by default in rustls.
    // Ticket keys are rotated automatically.

    Ok(Arc::new(config))
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let config = build_server_config("server.crt", "server.key")?;
    let acceptor = TlsAcceptor::from(config);

    let addr: SocketAddr = "0.0.0.0:8443".parse()?;
    let listener = TcpListener::bind(addr).await?;
    println!("TLS server listening on {}", addr);

    loop {
        let (tcp_stream, peer_addr) = listener.accept().await?;
        let acceptor = acceptor.clone();
        println!("Connection from {}", peer_addr);

        tokio::spawn(async move {
            // Perform the TLS handshake
            match acceptor.accept(tcp_stream).await {
                Ok(tls_stream) => {
                    // Access session info via the TlsStream wrapper
                    let (_, server_conn) = tls_stream.get_ref();

                    // Protocol version negotiated
                    if let Some(version) = server_conn.protocol_version() {
                        println!("Protocol: {:?}", version);
                    }

                    // ALPN selected
                    if let Some(alpn) = server_conn.alpn_protocol() {
                        println!("ALPN: {}", String::from_utf8_lossy(alpn));
                    }

                    // Cipher suite
                    if let Some(suite) = server_conn.negotiated_cipher_suite() {
                        println!("Cipher: {:?}", suite.suite());
                    }

                    // Use the tls_stream as a normal AsyncRead + AsyncWrite
                    handle_tls_stream(tls_stream).await;
                }
                Err(e) => {
                    eprintln!("TLS handshake error from {}: {}", peer_addr, e);
                }
            }
        });
    }
}

async fn handle_tls_stream(
    mut stream: tokio_rustls::server::TlsStream<tokio::net::TcpStream>,
) {
    use tokio::io::{AsyncReadExt, AsyncWriteExt};

    let mut buf = vec![0u8; 4096];
    match stream.read(&mut buf).await {
        Ok(n) if n > 0 => {
            let request = String::from_utf8_lossy(&buf[..n]);
            println!("Request: {}", &request[..request.len().min(100)]);

            let response = b"HTTP/1.1 200 OK\r\nContent-Length: 13\r\n\r\nHello, TLS!\n";
            let _ = stream.write_all(response).await;
        }
        Ok(_) => {}
        Err(e) => eprintln!("Read error: {}", e),
    }

    // Shutdown sends TLS close_notify
    let _ = stream.shutdown().await;
}
```

### 19.2 TLS Client in Rust

```rust
// tls_client.rs — Async TLS client with full certificate verification

use std::{io, sync::Arc};
use rustls::{ClientConfig, RootCertStore};
use tokio::net::TcpStream;
use tokio_rustls::TlsConnector;
use tokio::io::{AsyncReadExt, AsyncWriteExt};

/// Build a client config that verifies certificates against
/// the WebPKI (Mozilla) root certificate store.
fn build_client_config() -> Result<Arc<ClientConfig>, Box<dyn std::error::Error>> {
    // Load Mozilla's root CA bundle (maintained by the webpki-roots crate)
    let mut root_store = RootCertStore::empty();
    root_store.extend(webpki_roots::TLS_SERVER_ROOTS.iter().cloned());

    let config = ClientConfig::builder()
        // Only TLS 1.2 and 1.3
        .with_protocol_versions(&[
            &rustls::version::TLS13,
            &rustls::version::TLS12,
        ])?
        // Use Mozilla's trusted root CAs for server cert verification
        .with_root_certificates(root_store)
        // No client certificate (add with_client_auth_cert for mTLS)
        .with_no_client_auth();

    let mut config = config;
    // ALPN: prefer HTTP/2
    config.alpn_protocols = vec![b"h2".to_vec(), b"http/1.1".to_vec()];

    Ok(Arc::new(config))
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let host = "example.com";
    let port = 443u16;

    let config = build_client_config()?;
    let connector = TlsConnector::from(config);

    // 1. Establish TCP connection
    let addr = format!("{}:{}", host, port);
    let tcp = TcpStream::connect(&addr).await?;
    println!("TCP connected to {}", addr);

    // 2. TLS handshake
    // The ServerName is used for:
    //   a) SNI extension in ClientHello
    //   b) Certificate hostname verification
    let server_name = rustls::pki_types::ServerName::try_from(host)
        .map_err(|_| io::Error::new(io::ErrorKind::InvalidInput, "invalid hostname"))?;

    let mut tls = connector.connect(server_name, tcp).await?;
    println!("TLS handshake complete");

    // 3. Session info
    {
        let (_, conn) = tls.get_ref();
        if let Some(v) = conn.protocol_version() {
            println!("Protocol: {:?}", v);
        }
        if let Some(suite) = conn.negotiated_cipher_suite() {
            println!("Cipher: {:?}", suite.suite());
        }
        if let Some(alpn) = conn.alpn_protocol() {
            println!("ALPN: {}", String::from_utf8_lossy(alpn));
        }
        // Peer certificate chain
        if let Some(certs) = conn.peer_certificates() {
            for (i, cert) in certs.iter().enumerate() {
                println!("Cert[{}]: {} bytes", i, cert.len());
            }
        }
    }

    // 4. Send HTTP/1.1 GET request
    let request = format!(
        "GET / HTTP/1.1\r\nHost: {}\r\nConnection: close\r\n\r\n",
        host
    );
    tls.write_all(request.as_bytes()).await?;
    println!("Request sent");

    // 5. Read response
    let mut response = Vec::new();
    tls.read_to_end(&mut response).await?;
    println!("Response ({} bytes):", response.len());
    println!("{}", String::from_utf8_lossy(&response[..response.len().min(500)]));

    // 6. Orderly shutdown (sends TLS close_notify)
    tls.shutdown().await?;

    Ok(())
}
```

### 19.3 Low-Level TLS 1.3 Key Schedule in Rust (Educational)

```rust
//! tls13_key_schedule.rs — Educational implementation of the TLS 1.3 key schedule.
//!
//! This shows the exact HKDF computations that a TLS 1.3 implementation performs.
//! Uses the sha2 and hmac crates.
//!
//! [dependencies]
//! sha2 = "0.10"
//! hmac = "0.12"
//! hex = "0.4"

use hmac::{Hmac, Mac};
use sha2::{Digest, Sha256};

type HmacSha256 = Hmac<Sha256>;
const HASH_LEN: usize = 32; // SHA-256 output length

/// HKDF-Extract as defined in RFC 5869.
/// Combines salt and input keying material into a pseudorandom key.
///
/// PRK = HMAC-Hash(salt, IKM)
fn hkdf_extract(salt: &[u8], ikm: &[u8]) -> [u8; HASH_LEN] {
    let mut mac = HmacSha256::new_from_slice(salt)
        .expect("HMAC accepts any key length");
    mac.update(ikm);
    mac.finalize().into_bytes().into()
}

/// HKDF-Expand as defined in RFC 5869.
/// Expands a pseudorandom key with context info into `length` bytes.
fn hkdf_expand(prk: &[u8], info: &[u8], length: usize) -> Vec<u8> {
    let mut okm = Vec::with_capacity(length);
    let mut t = Vec::new(); // T(0) = ""
    let mut counter: u8 = 1;

    while okm.len() < length {
        // T(i) = HMAC-Hash(PRK, T(i-1) || info || i)
        let mut mac = HmacSha256::new_from_slice(prk)
            .expect("PRK length is valid");
        mac.update(&t);
        mac.update(info);
        mac.update(&[counter]);
        t = mac.finalize().into_bytes().to_vec();
        okm.extend_from_slice(&t);
        counter += 1;
    }
    okm.truncate(length);
    okm
}

/// HKDF-Expand-Label as defined in TLS 1.3 (RFC 8446, Section 7.1).
///
/// HkdfLabel = length (2 bytes big-endian)
///          || "tls13 " (6 bytes)
///          || label
///          || context (with 1-byte length prefix)
///
/// Returns `length` bytes of derived key material.
fn hkdf_expand_label(secret: &[u8], label: &[u8], context: &[u8], length: u16) -> Vec<u8> {
    // Build HkdfLabel structure
    let mut info = Vec::new();
    // Length: 2 bytes big-endian
    info.push((length >> 8) as u8);
    info.push((length & 0xFF) as u8);
    // Label: "tls13 " prefix + label
    let full_label = [b"tls13 ".as_ref(), label].concat();
    info.push(full_label.len() as u8);
    info.extend_from_slice(&full_label);
    // Context: 1-byte length + content
    info.push(context.len() as u8);
    info.extend_from_slice(context);

    hkdf_expand(secret, &info, length as usize)
}

/// Derive-Secret as defined in TLS 1.3 (RFC 8446, Section 7.1).
///
/// Derive-Secret(Secret, Label, Messages) =
///   HKDF-Expand-Label(Secret, Label, Transcript-Hash(Messages), Hash.length)
///
/// `transcript_hash` should be SHA-256(all handshake messages up to this point).
fn derive_secret(secret: &[u8], label: &[u8], transcript_hash: &[u8]) -> Vec<u8> {
    hkdf_expand_label(secret, label, transcript_hash, HASH_LEN as u16)
}

/// SHA-256 of empty string — used as the "empty transcript" hash
/// in early phases of the key schedule.
fn empty_hash() -> Vec<u8> {
    Sha256::digest(b"").to_vec()
}

/// The complete TLS 1.3 key schedule.
///
/// # Arguments
/// * `psk`        - Pre-shared key, or zeroes if no PSK (resumption)
/// * `dhe_secret` - (EC)DHE shared secret from key exchange
/// * `client_hello_hash`  - SHA-256(ClientHello)
/// * `server_hello_hash`  - SHA-256(ClientHello || ServerHello)
/// * `full_handshake_hash`- SHA-256(all handshake messages through server Finished)
/// * `complete_hash`      - SHA-256(all messages including client Finished)
#[derive(Debug)]
pub struct KeySchedule {
    pub early_secret: [u8; HASH_LEN],

    // Handshake secrets
    pub handshake_secret: [u8; HASH_LEN],
    pub client_handshake_traffic_secret: Vec<u8>,
    pub server_handshake_traffic_secret: Vec<u8>,

    // Application secrets
    pub master_secret: [u8; HASH_LEN],
    pub client_application_traffic_secret_0: Vec<u8>,
    pub server_application_traffic_secret_0: Vec<u8>,

    // Exporter and resumption
    pub exporter_master_secret: Vec<u8>,
    pub resumption_master_secret: Vec<u8>,
}

impl KeySchedule {
    pub fn new(
        psk: Option<&[u8]>,
        dhe_secret: &[u8],
        ch_hash: &[u8],       // Hash(ClientHello)
        ch_sh_hash: &[u8],    // Hash(ClientHello..ServerHello)
        server_fin_hash: &[u8],// Hash(ClientHello..server Finished)
        client_fin_hash: &[u8],// Hash(ClientHello..client Finished)
    ) -> Self {
        // Zero PSK if none provided
        let psk_bytes = psk.unwrap_or(&[0u8; HASH_LEN]);

        // ── Step 1: Early Secret ──────────────────────────────────────────
        // HKDF-Extract(0^HashLen, PSK)
        // The salt is all zeros when no external binder is used
        let early_secret: [u8; HASH_LEN] = hkdf_extract(
            &vec![0u8; HASH_LEN], // salt = 0^HashLen
            psk_bytes,
        );

        // Derive binder_key (for PSK binder computation — not shown here)
        let _ext_binder_key = derive_secret(&early_secret, b"ext binder", &empty_hash());
        let _res_binder_key = derive_secret(&early_secret, b"res binder", &empty_hash());

        // client_early_traffic_secret (for 0-RTT, if enabled)
        let _c_early_traffic = derive_secret(&early_secret, b"c e traffic", ch_hash);

        // ── Step 2: Handshake Secret ──────────────────────────────────────
        // The "derived" value acts as salt for the next Extract.
        // HKDF-Extract(Derive-Secret(early_secret, "derived", ""), DHE)
        let derived_from_early = derive_secret(&early_secret, b"derived", &empty_hash());
        let handshake_secret: [u8; HASH_LEN] = hkdf_extract(&derived_from_early, dhe_secret);

        // Handshake traffic secrets — bound to the transcript through ServerHello
        let client_handshake_traffic_secret =
            derive_secret(&handshake_secret, b"c hs traffic", ch_sh_hash);
        let server_handshake_traffic_secret =
            derive_secret(&handshake_secret, b"s hs traffic", ch_sh_hash);

        // ── Step 3: Master Secret ─────────────────────────────────────────
        // HKDF-Extract(Derive-Secret(handshake_secret, "derived", ""), 0^HashLen)
        let derived_from_hs = derive_secret(&handshake_secret, b"derived", &empty_hash());
        let master_secret: [u8; HASH_LEN] = hkdf_extract(
            &derived_from_hs,
            &vec![0u8; HASH_LEN], // IKM = 0^HashLen
        );

        // Application traffic secrets — bound to transcript through server Finished
        let client_application_traffic_secret_0 =
            derive_secret(&master_secret, b"c ap traffic", server_fin_hash);
        let server_application_traffic_secret_0 =
            derive_secret(&master_secret, b"s ap traffic", server_fin_hash);

        // Exporter — for application-level exporters (RFC 8449)
        let exporter_master_secret =
            derive_secret(&master_secret, b"exp master", server_fin_hash);

        // Resumption master secret — bound to full transcript including client Finished
        let resumption_master_secret =
            derive_secret(&master_secret, b"res master", client_fin_hash);

        KeySchedule {
            early_secret,
            handshake_secret,
            client_handshake_traffic_secret,
            server_handshake_traffic_secret,
            master_secret,
            client_application_traffic_secret_0,
            server_application_traffic_secret_0,
            exporter_master_secret,
            resumption_master_secret,
        }
    }

    /// Derive the write key and IV for a given traffic secret.
    /// Used to get the actual AES-GCM / ChaCha20-Poly1305 keys.
    pub fn derive_keys(&self, traffic_secret: &[u8]) -> (Vec<u8>, Vec<u8>) {
        // AES-128-GCM: key = 16 bytes, IV = 12 bytes
        let key = hkdf_expand_label(traffic_secret, b"key", b"", 16);
        let iv  = hkdf_expand_label(traffic_secret, b"iv",  b"", 12);
        (key, iv)
    }

    /// Compute the Finished MAC key and the expected verify_data.
    ///
    /// verify_data = HMAC-SHA256(finished_key, transcript_hash)
    /// finished_key = HKDF-Expand-Label(traffic_secret, "finished", "", HashLen)
    pub fn compute_finished(&self, traffic_secret: &[u8], transcript_hash: &[u8]) -> Vec<u8> {
        let finished_key = hkdf_expand_label(
            traffic_secret,
            b"finished",
            b"",
            HASH_LEN as u16,
        );
        let mut mac = HmacSha256::new_from_slice(&finished_key)
            .expect("valid length");
        mac.update(transcript_hash);
        mac.finalize().into_bytes().to_vec()
    }

    /// Ratchet the application traffic secret for a KeyUpdate.
    ///
    /// application_traffic_secret_N+1 =
    ///   HKDF-Expand-Label(application_traffic_secret_N, "traffic upd", "", HashLen)
    pub fn update_traffic_secret(secret: &[u8]) -> Vec<u8> {
        hkdf_expand_label(secret, b"traffic upd", b"", HASH_LEN as u16)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Test vector from RFC 8448 (TLS 1.3 example session).
    /// This validates our HKDF implementation against a known-good value.
    #[test]
    fn test_hkdf_expand_label() {
        // RFC 8448 Section 3:
        // early_secret from PSK = all zeros, salt = all zeros (no external PSK)
        let psk = [0u8; 32];
        let salt = [0u8; 32];
        let early_secret = hkdf_extract(&salt, &psk);

        // Expected: 33ad0a1c607ec03b09e6cd9893680ce210adf300aa1f2660e1b22e10f170f92a
        let expected = hex::decode(
            "33ad0a1c607ec03b09e6cd9893680ce210adf300aa1f2660e1b22e10f170f92a"
        ).unwrap();
        assert_eq!(early_secret.to_vec(), expected);
    }
}
```

### 19.4 mTLS with rustls

```rust
// mtls_server.rs — Mutual TLS server with custom client certificate verification

use std::{fs::File, io::BufReader, sync::Arc};
use rustls::{
    pki_types::{CertificateDer, TrustAnchor},
    server::WebPkiClientVerifier,
    RootCertStore, ServerConfig,
};
use rustls_pemfile::certs;

fn build_mtls_server_config(
    server_cert: &str,
    server_key: &str,
    client_ca_cert: &str,
) -> Result<Arc<ServerConfig>, Box<dyn std::error::Error>> {
    // Load the CA cert that signed client certificates
    let ca_file = File::open(client_ca_cert)?;
    let mut ca_reader = BufReader::new(ca_file);
    let ca_certs: Vec<CertificateDer<'static>> = certs(&mut ca_reader).collect::<Result<_, _>>()?;

    // Build a RootCertStore containing only our internal CA
    let mut client_cert_roots = RootCertStore::empty();
    for cert in &ca_certs {
        client_cert_roots.add(cert.clone())?;
    }

    // WebPkiClientVerifier verifies client certificates against the root store.
    // It performs full chain validation, expiry checks, and name binding.
    let client_verifier = WebPkiClientVerifier::builder(Arc::new(client_cert_roots))
        // Optionally allow anonymous connections (skip client cert):
        // .allow_unauthenticated()
        .build()?;

    // Load server cert chain and key
    let server_certs: Vec<CertificateDer<'static>> = {
        let f = File::open(server_cert)?;
        let mut r = BufReader::new(f);
        certs(&mut r).collect::<Result<_, _>>()?
    };

    let server_key = {
        let f = File::open(server_key)?;
        let mut r = BufReader::new(f);
        rustls_pemfile::private_key(&mut r)?.unwrap()
    };

    let config = ServerConfig::builder()
        .with_protocol_versions(&[&rustls::version::TLS13, &rustls::version::TLS12])?
        // Use our custom client certificate verifier
        .with_client_cert_verifier(client_verifier)
        .with_single_cert(server_certs, server_key)?;

    Ok(Arc::new(config))
}

// In the connection handler, you can inspect the client's certificate:
fn inspect_client_cert(conn: &rustls::ServerConnection) {
    if let Some(certs) = conn.peer_certificates() {
        if let Some(cert) = certs.first() {
            // Parse with x509-parser or rcgen for full inspection
            println!("Client cert: {} bytes", cert.len());
        }
    }
}
```

---

## 20. Deployment Best Practices

### 20.1 Protocol Version Policy

```
Recommended configuration:
  Minimum: TLS 1.2
  Maximum: TLS 1.3
  
  Disable: SSLv2, SSLv3, TLS 1.0, TLS 1.1
  
  If you must support TLS 1.0/1.1 (legacy devices):
    Document it as a known risk
    Enable SSL_OP_NO_SESSION_RESUMPTION_ON_RENEGOTIATION
    Monitor for exploit attempts
    Set a deadline to disable
```

### 20.2 Cipher Suite Policy

```
TLS 1.3: all three standard suites are acceptable
  TLS_AES_256_GCM_SHA384      (highest security)
  TLS_CHACHA20_POLY1305_SHA256 (faster on mobile/IoT)
  TLS_AES_128_GCM_SHA256      (good performance/security balance)

TLS 1.2: ECDHE + AEAD only
  Require:  ECDHE (forward secrecy)
            GCM or POLY1305 (AEAD — no separate MAC)
            AES-128 or AES-256 or ChaCha20

  Acceptable order (server preference):
    ECDHE-ECDSA-AES256-GCM-SHA384
    ECDHE-RSA-AES256-GCM-SHA384
    ECDHE-ECDSA-AES128-GCM-SHA256
    ECDHE-RSA-AES128-GCM-SHA256
    ECDHE-ECDSA-CHACHA20-POLY1305
    ECDHE-RSA-CHACHA20-POLY1305
    DHE-RSA-AES256-GCM-SHA384    (fallback if ECDHE not available)
    DHE-RSA-AES128-GCM-SHA256

  Disable all others.
```

### 20.3 Certificate Best Practices

```
Key type: ECDSA P-256 (fast, strong, small certs)
          or RSA-2048 minimum (RSA-3072 for new deployments)

Lifetime: 90 days (Let's Encrypt standard)
          Up to 397 days for manually managed certs
          (Browsers may reject longer lifetimes in the future)

Must-have extensions:
  subjectAltName (SANs) — CN alone is insufficient
  keyUsage: digitalSignature (ECDSA) or both (RSA)
  extendedKeyUsage: serverAuth
  authorityInfoAccess: OCSP URL + issuer URL
  cRLDistributionPoints
  certificatePolicies: DV/OV/EV OID

Should-have:
  Signed Certificate Timestamps (CT)
  OCSP Must-Staple (if you can maintain OCSP stapling uptime)

Private key security:
  Store in HSM or encrypted key store (not plaintext on disk)
  Permissions: 600 (owner read-only)
  Never put private key in version control
  Rotate on suspected compromise immediately
```

### 20.4 OCSP Stapling Configuration

```nginx
# nginx OCSP stapling configuration
ssl_stapling on;
ssl_stapling_verify on;
ssl_trusted_certificate /path/to/chain-plus-root.crt;
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;
```

```apache
# Apache OCSP stapling
SSLUseStapling on
SSLStaplingCache "shmcb:logs/ssl_stapling(32768)"
```

### 20.5 HTTP Security Headers (Complementary to TLS)

```
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
  → HSTS: tells browsers to only use HTTPS for 2 years
  → includeSubDomains: applies to all subdomains
  → preload: submit to browser preload list (HTTPS before first connection)

Content-Security-Policy: default-src 'self' https:
  → Prevents loading of mixed content

X-Content-Type-Options: nosniff
X-Frame-Options: DENY (or SAMEORIGIN)
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: ...
```

### 20.6 Testing Your TLS Configuration

```bash
# SSL Labs (online grade report)
# https://www.ssllabs.com/ssltest/

# testssl.sh (local comprehensive test)
testssl.sh --severity HIGH --parallel https://example.com

# OpenSSL quick check
openssl s_client -connect example.com:443 \
    -servername example.com \
    -status \
    2>&1 | grep -E "Protocol|Cipher|Verify"

# Check for weak ciphers
nmap --script ssl-enum-ciphers -p 443 example.com

# Certificate transparency search
curl "https://crt.sh/?q=example.com&output=json" | jq '.[].name_value'
```

### 20.7 TLS Termination Architecture

```
Option 1: TLS at Load Balancer (most common)
  Client ──TLS──> Load Balancer ──HTTP──> App Servers
  
  Pros: Centralized cert management, offloads TLS CPU
  Cons: Traffic from LB to app server is unencrypted
        Requires trusted internal network
        mTLS information must be forwarded as headers

Option 2: End-to-End TLS (most secure)
  Client ──TLS──> Load Balancer ──TLS──> App Servers
  
  Pros: Encrypted throughout, true E2E security
  Cons: More complex cert management, more CPU

Option 3: TLS Passthrough (for mTLS)
  Client ──TLS──> Load Balancer (SNI routing) ──TLS──> App Server
                  (does not terminate TLS, just routes by SNI)
  
  Pros: Load balancer never sees plaintext, app server does mTLS auth
  Cons: Can't inspect or modify HTTP headers at LB level
```

---

## 21. Mental Model Summary

Here is the high-level mental model for thinking about TLS efficiently:

### The Three Security Properties

**Confidentiality** is achieved by symmetric encryption (AES-GCM, ChaCha20-Poly1305) using keys that only the two endpoints know. The keys are established fresh for each session via an asymmetric key exchange (ECDHE), so they are never transmitted and cannot be derived from eavesdropped traffic.

**Integrity** is achieved by AEAD authentication tags (in modern TLS) or HMAC (in older cipher suites). Every byte of application data is covered by a MAC that incorporates a per-message sequence number. Modification of any bit is immediately detected.

**Authentication** is achieved by the server's certificate (signed by a CA) and its CertificateVerify signature (in TLS 1.3) or the key exchange signature (in TLS 1.2). The server proves it controls the private key for the certificate it presents. The certificate proves the public key belongs to the expected hostname.

### The Handshake is a Bootstrapping Protocol

The handshake is not the security mechanism — it is the mechanism that establishes the security mechanism. Its job is to agree on algorithms, exchange keys, prove identity, and create the symmetric keys used for the actual data. Once the handshake is complete, the handshake machinery is irrelevant; only the record layer matters.

### Forward Secrecy is About the Future

Forward secrecy means: compromise of the server's long-term private key today cannot decrypt traffic recorded yesterday. It is achieved by using ephemeral DH keys that are discarded after use. The server's certificate key (long-term) is only used to sign the ephemeral key (proving its authenticity), not to encrypt anything that would reveal the session key.

### TLS 1.3 Made the Right Choices

Every change in TLS 1.3 was driven by a specific known attack or security proof:
- Removing RSA key exchange → prevents future private key compromise from exposing past sessions.
- Encrypting more of the handshake → prevents traffic analysis and extension fingerprinting.
- HKDF key schedule → formally proven secure; old PRF was not.
- Mandatory AEAD → removes the class of MAC-then-Encrypt padding oracle attacks.
- Removing renegotiation → removes complexity that caused injection attacks.
- 1-RTT instead of 2-RTT → not just performance; reduces the attack window during handshake.

### Certificates are the Achilles Heel

The cryptography in TLS is nearly unassailable with modern parameters. The weak point is the certificate authority system: any trusted CA can issue a certificate for any domain. This is why Certificate Transparency, HSTS preloading, and CAA DNS records exist — to constrain what CAs can issue for your domain and detect misissuance.

### Think in Layers

When debugging a TLS issue, think in layers:
1. **TCP layer:** Did the connection establish?
2. **Record layer:** Are records being framed correctly?
3. **Handshake layer:** Is the version/cipher suite being negotiated correctly?
4. **Certificate layer:** Is the chain valid, hostname matching, not expired?
5. **Key derivation layer:** Are both sides computing the same keys?
6. **Application layer:** Is ALPN negotiated? Is SNI correct?

Alerts (Section 9) will tell you exactly which layer is failing if you read them correctly.

---

*End of document. This guide covers SSL/TLS from cryptographic primitives through deployment, including all major protocol versions, attack history, and production-quality C and Rust implementations.*