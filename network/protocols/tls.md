# TLS Protocol: Elite Analyst's Complete Technical Reference
### For Malware Reverse Engineers, APT Defenders, and Threat Intelligence Specialists

---

> **North Star:** TLS is not just a protocol — it is the primary cloak worn by modern APT infrastructure.
> Understanding it at the cryptographic, byte, OS, and network layer is mandatory for anyone operating
> at the FLARE/GReAT tier. Every C2 beacon, every exfiltration stream, every malware update channel
> hides behind TLS. To hunt it, you must understand it completely.

---

## Table of Contents

1. [Historical Context & Version Timeline](#1-historical-context--version-timeline)
2. [Cryptographic Foundations](#2-cryptographic-foundations)
3. [PKI and X.509 Certificate Infrastructure](#3-pki-and-x509-certificate-infrastructure)
4. [TLS Record Layer — The Transport Substrate](#4-tls-record-layer--the-transport-substrate)
5. [TLS 1.2 — Full Protocol Walkthrough](#5-tls-12--full-protocol-walkthrough)
6. [TLS 1.3 — Complete Redesign](#6-tls-13--complete-redesign)
7. [Cipher Suites — Anatomy and Selection](#7-cipher-suites--anatomy-and-selection)
8. [Key Derivation — PRF (TLS 1.2) and HKDF (TLS 1.3)](#8-key-derivation--prf-tls-12-and-hkdf-tls-13)
9. [TLS Extensions — Complete Catalog](#9-tls-extensions--complete-catalog)
10. [Mutual TLS (mTLS)](#10-mutual-tls-mtls)
11. [Session Resumption — Tickets and Session IDs](#11-session-resumption--tickets-and-session-ids)
12. [TLS Fingerprinting — JA3, JA3S, JA4, JARM](#12-tls-fingerprinting--ja3-ja3s-ja4-jarm)
13. [APT Abuse of TLS — C2, Exfiltration, Tunneling](#13-apt-abuse-of-tls--c2-exfiltration-tunneling)
14. [Historic TLS Vulnerabilities (BEAST, CRIME, POODLE, DROWN, Heartbleed)](#14-historic-tls-vulnerabilities)
15. [Certificate Transparency and Passive DNS Pivoting](#15-certificate-transparency-and-passive-dns-pivoting)
16. [TLS in Malware — Implementation Patterns and Detection](#16-tls-in-malware--implementation-patterns-and-detection)
17. [C Implementation — Raw TLS Client/Server](#17-c-implementation--raw-tls-clientserver)
18. [Rust Implementation — TLS from First Principles](#18-rust-implementation--tls-from-first-principles)
19. [Memory Forensics of TLS Sessions](#19-memory-forensics-of-tls-sessions)
20. [YARA Rules for TLS-Related Malware Detection](#20-yara-rules-for-tls-related-malware-detection)
21. [Sigma Rules for TLS Anomaly Detection](#21-sigma-rules-for-tls-anomaly-detection)
22. [Zeek Scripting for TLS Intelligence](#22-zeek-scripting-for-tls-intelligence)
23. [The Expert Mental Model](#23-the-expert-mental-model)

---

## 1. Historical Context & Version Timeline

### Why TLS History Matters for Analysts

Every malware sample carries implicit version history. A C2 communicating over SSLv3 in 2024 is either legacy-constrained or deliberately choosing a broken protocol. The TLS version negotiated is a behavioral fingerprint as significant as the cipher suite chosen.

```
TIMELINE OF TLS / SSL EVOLUTION
================================

1994 ─── SSL 2.0 ── Netscape (broken: padding oracle, no MAC-then-encrypt)
1996 ─── SSL 3.0 ── Netscape (broken: POODLE - CBC padding oracle)
1999 ─── TLS 1.0 ── RFC 2246 (still vulnerable: BEAST, RC4, weak PRF)
2006 ─── TLS 1.1 ── RFC 4346 (fixed IV, still weak cipher suites)
2008 ─── TLS 1.2 ── RFC 5246 (SHA-256 PRF, AEAD, current baseline)
2018 ─── TLS 1.3 ── RFC 8446 (complete redesign, 1-RTT, PFS mandatory)

CURRENT STATUS (2024):
  SSL 2.0 / 3.0  → DEPRECATED, broken, disabled by default everywhere
  TLS 1.0 / 1.1  → DEPRECATED by RFC 8996 (2021), most browsers removed
  TLS 1.2        → CURRENT, still dominant (~60% of HTTPS traffic)
  TLS 1.3        → CURRENT, growing (~40% of HTTPS traffic)
```

### RFC Reference Map

| Protocol | RFC | Key Improvements |
|---|---|---|
| TLS 1.0 | RFC 2246 | HMAC (replaces MAC), explicit IV |
| TLS 1.1 | RFC 4346 | Protection against CBC attacks |
| TLS 1.2 | RFC 5246 | SHA-256 PRF, AEAD support, negotiable PRF |
| TLS 1.3 | RFC 8446 | 0-RTT, mandatory PFS, removed legacy, encrypted handshake |
| DTLS 1.2 | RFC 6347 | TLS over UDP (used by WebRTC, QUIC precursors) |
| DTLS 1.3 | RFC 9147 | DTLS aligned with TLS 1.3 |

**APT relevance:** Lazarus Group's HOPLIGHT backdoor and several FIN7 tools have been observed negotiating TLS 1.0 specifically — indicative of embedded OpenSSL 1.0.x linked statically. This is a detection signal.

---

## 2. Cryptographic Foundations

### 2.1 Symmetric Encryption in TLS

TLS uses symmetric encryption for bulk data after handshake. The key exchange only establishes shared secret; actual data is protected by symmetric cipher.

#### Block Ciphers (TLS 1.2 and below)

```
AES-CBC (Cipher Block Chaining) — PROBLEMATIC
==============================================

Plaintext blocks:  P1    P2    P3    P4
                   |     |     |     |
                   XOR   XOR   XOR   XOR
                   |     |     |     |
IV ────────────► [AES] [AES] [AES] [AES]
                   |     |     |     |
Ciphertext:        C1    C2    C3    C4

ISSUE: Padding oracle attacks (POODLE, BEAST)
     : Each block depends on previous — no parallelism
     : Requires explicit IV per record (added in TLS 1.1)
```

#### Stream Ciphers

```
RC4 — BROKEN (removed TLS 1.3, RFC 7465 prohibits)
ChaCha20 — MODERN (TLS 1.3, XOR-based, no padding issues)

ChaCha20 operation:
  keystream = ChaCha20(key, nonce, counter)
  ciphertext = plaintext XOR keystream

  AEAD version: ChaCha20-Poly1305
  Poly1305 = MAC authenticates ciphertext
  nonce = 12 bytes, unique per record
```

#### AEAD — The Modern Standard

**Authenticated Encryption with Associated Data** — provides confidentiality AND integrity in one primitive. Mandatory in TLS 1.3.

```
AES-GCM (Galois/Counter Mode)
==============================

Input:  plaintext, key (16/32 bytes), nonce (12 bytes), AAD (optional)

Step 1: CTR mode encryption
  counter = nonce || 0x00000001
  for each block:
    keystream = AES(key, counter++)
    cipherblock = plaintext_block XOR keystream

Step 2: GHASH authentication
  auth_tag = GHASH(H, AAD, ciphertext)
  H = AES(key, 0^128)  // hash subkey

Output: ciphertext || auth_tag (16 bytes)

DECRYPTION:
  1. Verify auth_tag FIRST (before decryption)
  2. If tag invalid → reject record (no plaintext returned)
  3. If valid → decrypt
```

**Why AEAD matters for analysts:** When you see `auth_tag` verification failures in memory or logs, it indicates either corruption, tampering, or a C2 server sending malformed records — potential exfil channel probe or test.

### 2.2 Asymmetric Cryptography in TLS

Used exclusively during handshake for authentication and key exchange.

#### RSA (TLS 1.2 key exchange — now deprecated in 1.3)

```
RSA Key Exchange (VULNERABLE — no PFS):
========================================

Client generates:  PreMasterSecret (48 bytes)
                   = TLS_version (2) || random (46)

Client encrypts:   EncryptedPMS = RSA_encrypt(server_pubkey, PMS)
Client sends:      ClientKeyExchange { EncryptedPMS }

Server decrypts:   PMS = RSA_decrypt(server_privkey, EncryptedPMS)

PROBLEM: If attacker records traffic and later obtains server private key
         → can decrypt ALL past sessions (no forward secrecy)
         → Equation Group / NSA collected TLS traffic for this
```

#### Diffie-Hellman (Key Agreement — Ephemeral)

```
ECDHE — Elliptic Curve Diffie-Hellman Ephemeral
================================================

Curve: P-256 (secp256r1) or X25519

Server generates: server_private (s), server_public = s * G
Client generates: client_private (c), client_public = c * G

Exchange:
  Server → Client: ServerKeyExchange { server_public }
  Client → Server: ClientKeyExchange { client_public }

Shared Secret:
  Both compute: S = c * (s*G) = s * (c*G) = c*s*G

  Client: shared = client_private * server_public
  Server: shared = server_private * client_public

WHY FORWARD SECRECY:
  s and c are ephemeral — generated fresh per session
  Even if server's long-term key compromised,
  past sessions cannot be decrypted

X25519 math:
  Field: GF(2^255 - 19)
  Base point: 9 (encoded as 32-byte little-endian)
  scalar multiplication: Montgomery ladder (constant-time)
```

#### ECDSA and RSA-PSS (Signatures for Authentication)

```
Certificate signature verification chain:

  Root CA private key ──signs──► Root CA cert (self-signed)
       │
       └──signs──► Intermediate CA cert
                        │
                        └──signs──► Server leaf cert
                                         │
                                         └── Server proves identity by
                                             signing handshake with
                                             corresponding private key
```

### 2.3 Hash Functions and MAC

```
HMAC-SHA256 (used in TLS 1.2 PRF, finished messages):
======================================================

HMAC(K, m) = H((K XOR opad) || H((K XOR ipad) || m))

  ipad = 0x36 repeated (block size)
  opad = 0x5C repeated (block size)
  H    = SHA-256

TLS Finished message verification:
  verify_data = PRF(master_secret,
                    label,          // "client finished" or "server finished"
                    Hash(handshake_messages))
  
  If either side computes different verify_data → handshake tampered
  Length = 12 bytes (TLS 1.2)
```

### 2.4 Random Number Generation — Critical for TLS Security

```
TLS Random fields (critical for session uniqueness):
=====================================================

ClientHello.random = 32 bytes
  Historically: Unix timestamp (4 bytes) || random (28 bytes)
  TLS 1.3: MUST be fully random (timestamp deprecated)

ServerHello.random = 32 bytes
  TLS 1.3 downgrade protection:
    If server supports TLS 1.3 but negotiating TLS 1.2:
    Last 8 bytes of random MUST be: 44 4F 57 4E 47 52 44 01
    ("DOWNGRD\x01") to signal intentional downgrade

MALWARE IMPLICATION: Poorly implemented malware TLS stacks
often use weak PRNG for ClientHello.random. This creates
detectable patterns in JA3/packet captures.
```

---

## 3. PKI and X.509 Certificate Infrastructure

### 3.1 X.509 Certificate Structure

```
X.509v3 Certificate (DER/PEM encoded)
======================================

Certificate ::= SEQUENCE {
  tbsCertificate   TBSCertificate,
  signatureAlgorithm AlgorithmIdentifier,
  signature        BIT STRING
}

TBSCertificate ::= SEQUENCE {
  version         [0] INTEGER (v3 = 2),
  serialNumber    INTEGER,
  signature       AlgorithmIdentifier,  // must match outer
  issuer          Name,
  validity        Validity {
    notBefore     Time,
    notAfter      Time
  },
  subject         Name,
  subjectPublicKeyInfo SubjectPublicKeyInfo {
    algorithm     AlgorithmIdentifier,
    subjectPublicKey BIT STRING
  },
  extensions      [3] SEQUENCE OF Extension
}
```

### 3.2 X.509 Extensions — Forensically Significant

| Extension | OID | Purpose | Malware Relevance |
|---|---|---|---|
| Subject Alternative Name | 2.5.29.17 | Additional hostnames/IPs | C2 domains listed here |
| Basic Constraints | 2.5.29.19 | Is CA cert? | Self-signed C2 certs often set CA=TRUE |
| Key Usage | 2.5.29.15 | Digital Signature, Key Encipherment | |
| Extended Key Usage | 2.5.29.37 | Server Auth, Client Auth | mTLS client certs |
| Subject Key Identifier | 2.5.29.14 | Hash of public key | Pivot: same key → same operator |
| Authority Key Identifier | 2.5.29.35 | Identifies signing CA | |
| CRL Distribution Points | 2.5.29.31 | Revocation check URL | Rarely checked by malware |
| Certificate Transparency | 1.3.6.1.4.1.11129.2.4.2 | SCT list | Absence is suspicious |

### 3.3 Certificate Encoding Formats

```
PEM (Privacy Enhanced Mail):
-----BEGIN CERTIFICATE-----
MIIBpDCCAQ2gAwIBAgIJAK...
-----END CERTIFICATE-----

(Base64-encoded DER inside PEM header/footer)

DER (Distinguished Encoding Rules):
Raw binary ASN.1 encoding
First bytes: 30 82 XX XX (SEQUENCE, length)

PKCS#12 (.pfx / .p12):
Combined certificate + private key (password protected)
Used by malware that bundles client certs for mTLS C2

PKCS#7 (.p7b):
Certificate chain only, no private key
```

### 3.4 Certificate Validation — How Browsers vs. Malware Differ

```
FULL VALIDATION (proper TLS client):
  1. Certificate chain builds to trusted root
  2. Each cert signed by issuer
  3. Validity period not expired
  4. Revocation checked (CRL or OCSP)
  5. Subject/SAN matches hostname (hostname verification)
  6. Key usage permits TLS

MALWARE SHORTCUTS:
  Most malware disables validation entirely:
  ┌─────────────────────────────────────────────────┐
  │ SSL_CTX_set_verify(ctx, SSL_VERIFY_NONE, NULL);  │  <- common in C malware
  └─────────────────────────────────────────────────┘

  Or in Go:
  tls.Config{ InsecureSkipVerify: true }

  Or in Python:
  requests.get(url, verify=False)

DETECTION IMPLICATION: The string "InsecureSkipVerify",
"SSL_VERIFY_NONE", or "verify=False" in a binary is a
RED FLAG — legitimate software rarely disables cert validation.
```

### 3.5 Certificate Pinning

```
Certificate Pinning variants:
==============================

1. LEAF PINNING: Pin specific server certificate
   - Breaks on cert rotation
   - Rarely used except mobile apps

2. PUBLIC KEY PINNING (HPKP / manual):
   expected_pin = SHA256(SubjectPublicKeyInfo)
   Pin public key — survives cert rotation if key unchanged

3. CA PINNING: Pin intermediate or root CA
   - More flexible
   - APT malware often pins custom CA for mTLS

APT41 / DoubleAgent: Hardcoded certificate fingerprints
in custom C2 clients to prevent MITM interception by defenders.

BYPASS: Memory patching the comparison routine at runtime.
Find the memcmp/strncmp call that checks the pin.
Patch to always return 0 (equal).
```

---

## 4. TLS Record Layer — The Transport Substrate

The Record Layer is the lowest TLS sublayer — it fragments, compresses (disabled in TLS 1.3), and encapsulates all higher-layer messages.

### 4.1 Record Header Format

```
TLS Record Format (on wire)
============================

Byte Offset  Field              Size   Description
───────────  ─────────────────  ─────  ──────────────────────────────────
0            ContentType        1      22=Handshake, 23=AppData,
                                       20=ChangeCipherSpec, 21=Alert,
                                       24=Heartbeat
1-2          ProtocolVersion    2      0x0303 = TLS 1.2
                                       0x0301 = TLS 1.0 (compat)
                                       TLS 1.3 still shows 0x0303 here!
3-4          Length             2      Length of payload (max 16384 bytes)
5-N          Payload            var    Content (plaintext or encrypted)

EXAMPLE (unencrypted ClientHello):
16 03 01 00 f1
│  │──┘ └──┘
│  │        └── Length: 0x00f1 = 241 bytes
│  └────────── Version: 0x0301 = TLS 1.0 (compatibility mode)
└────────────── ContentType: 0x16 = Handshake

NOTE: TLS 1.3 uses 0x0303 in record layer but negotiates
1.3 through the supported_versions extension. This is a
backward-compatibility design choice.
```

### 4.2 Record Layer State Machine

```
TLS Record Layer States
========================

          INITIAL
            │
            ▼
   ┌─────────────────┐
   │  Unprotected    │  ← ClientHello, ServerHello sent here
   │  (plaintext)    │
   └────────┬────────┘
            │ ChangeCipherSpec (TLS 1.2)
            │ or derived traffic keys (TLS 1.3)
            ▼
   ┌─────────────────┐
   │   Protected     │  ← All application data
   │   (encrypted)   │
   └────────┬────────┘
            │ Alert (close_notify)
            ▼
          CLOSED

TLS 1.3 difference: No ChangeCipherSpec message
Keys derived immediately after ServerHello
Server begins sending encrypted records before
client even sends its Finished message!
```

### 4.3 Record Layer Encryption in Detail

```
Encrypted Record (TLS 1.2 with AES-GCM)
=========================================

Plaintext record → encrypt → Encrypted record

Nonce construction (AES-GCM):
  explicit_nonce = 8 bytes sent in plaintext before ciphertext
  actual_nonce   = write_IV (4 bytes) || explicit_nonce (8 bytes)
                 = 12 bytes total

Wire format of encrypted record:
  [Header: 5 bytes][Explicit Nonce: 8 bytes][Ciphertext][Auth Tag: 16 bytes]

Encrypted Record (TLS 1.3 with AES-128-GCM)
=============================================

Nonce construction (TLS 1.3):
  sequence_number = 8-byte big-endian counter (per direction)
  nonce = write_iv XOR (0^4 || sequence_number)
  
  No explicit nonce sent — it's derived from sequence number!
  
Wire format:
  [Header: 5 bytes][Ciphertext || ContentType][Auth Tag: 16 bytes]

  ContentType is ENCRYPTED (moved inside payload in TLS 1.3)!
  This hides whether record is handshake or application data.

AAD for AEAD (TLS 1.3):
  additional_data = record_header (5 bytes with type=23, length=len)
  
  The outer ContentType is always 0x17 (ApplicationData) in TLS 1.3
  to obscure actual content type from network observers.
```

---

## 5. TLS 1.2 — Full Protocol Walkthrough

### 5.1 State Machine Overview

```
TLS 1.2 Full Handshake (2-RTT)
================================

Client                                    Server
  │                                          │
  │──── ClientHello ──────────────────────►  │
  │     version, random, session_id,         │
  │     cipher_suites, extensions            │
  │                                          │
  │ ◄─── ServerHello ─────────────────────  │
  │      version, random, session_id,        │
  │      cipher_suite, extensions            │
  │                                          │
  │ ◄─── Certificate ─────────────────────  │
  │      cert chain (leaf to root)           │
  │                                          │
  │ ◄─── ServerKeyExchange ───────────────  │
  │      ECDHE params (if DHE/ECDHE suite)   │
  │      signed with server's private key    │
  │                                          │
  │ ◄─── ServerHelloDone ─────────────────  │
  │                                          │
  │──── ClientKeyExchange ────────────────►  │
  │     ECDHE client public key              │
  │     (or RSA-encrypted PMS)               │
  │                                          │
  │──── ChangeCipherSpec ─────────────────►  │
  │     (signal: switching to encryption)    │
  │                                          │
  │──── Finished ─────────────────────────►  │
  │     HMAC of all handshake messages       │
  │                                          │
  │ ◄─── ChangeCipherSpec ─────────────────  │
  │                                          │
  │ ◄─── Finished ─────────────────────────  │
  │                                          │
  │ ◄══════ Application Data ═════════════►  │  (encrypted)
  │                                          │
  │──── Alert (close_notify) ─────────────►  │
  │ ◄─── Alert (close_notify) ─────────────  │
  │                                          │
 [CLOSED]                                 [CLOSED]

Total: 2 full round trips before application data
```

### 5.2 ClientHello — Wire-Level Analysis

```
ClientHello Message Structure
================================

Handshake header:
  01              HandshakeType.ClientHello
  00 00 f4        Length (3 bytes) = 244 bytes

ClientHello body:
  03 03           client_version = TLS 1.2 (0x0303)
  
  [32 bytes]      client_random
  │  Bytes 0-3:   UNIX timestamp (deprecated in TLS 1.3)
  │  Bytes 4-31:  28 random bytes
  
  00              session_id_length = 0 (new session)
  [session_id]    (empty for new session, 32 bytes for resumption)
  
  00 1e           cipher_suites_length = 30 bytes (15 suites)
  [cipher_suites] list of 2-byte cipher suite codes:
    c0 2b  TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
    c0 2f  TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
    c0 2c  TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
    c0 30  TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
    cc a9  TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256
    cc a8  TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256
    00 ff  TLS_EMPTY_RENEGOTIATION_INFO_SCSV
  
  01              compression_methods_length = 1
  00              compression_method = null (0)
                  (zlib removed due to CRIME attack)
  
  [extensions]    variable length extension block
```

### 5.3 ServerKeyExchange — The Critical Authentication Step

```
ServerKeyExchange (ECDHE example)
===================================

Handshake header:
  0c              HandshakeType.ServerKeyExchange
  00 00 XX        Length

Body:
  03              curve_type = named_curve
  00 1d           named_curve = x25519 (0x001d)
  
  20              pubkey_length = 32 bytes
  [32 bytes]      server_ephemeral_public_key
  
  04 01           signature_algorithm = RSA with SHA-256
  [2 bytes]       signature_length
  [N bytes]       signature
  
  WHAT IS SIGNED:
  signature = Sign(server_private_key,
                   client_random ||
                   server_random ||
                   curve_type    ||
                   named_curve   ||
                   pubkey_length ||
                   server_pubkey)
  
  WHY THIS MATTERS:
  This signature proves the server knows the private key
  corresponding to the certificate's public key.
  This authenticates the ECDHE parameters.
  Without this signature, ECDHE would be unauthenticated
  (anonymous DH — vulnerable to MITM).
```

### 5.4 Key Material Derivation in TLS 1.2

```
TLS 1.2 Key Hierarchy
======================

STEP 1: PreMasterSecret
  For ECDHE: PMS = ECDH(client_ephemeral_private, server_ephemeral_public)
  For RSA:   PMS = random 48 bytes encrypted with server pubkey

STEP 2: MasterSecret (48 bytes)
  MS = PRF(PreMasterSecret,
           "master secret",
           ClientHello.random || ServerHello.random)
  PRF = HMAC-SHA256-based P_hash function

STEP 3: Key Material (key block)
  key_block = PRF(MasterSecret,
                  "key expansion",
                  ServerHello.random || ClientHello.random)
              NOTE: Random order is REVERSED here!

STEP 4: Extract keying material from key_block
  client_write_MAC_key = key_block[0..mac_key_len]
  server_write_MAC_key = key_block[mac_key_len..2*mac_key_len]
  client_write_key     = key_block[..+enc_key_len]
  server_write_key     = key_block[..+enc_key_len]
  client_write_IV      = key_block[..+iv_len]  (for AEAD)
  server_write_IV      = key_block[..+iv_len]

EXAMPLE VALUES (AES-128-GCM-SHA256):
  mac_key_len = 0 (AEAD does its own auth, no separate MAC)
  enc_key_len = 16 (AES-128)
  iv_len      = 4  (implicit IV, 8 bytes explicit per record)

PRF definition:
  PRF(secret, label, seed) = P_SHA256(secret, label || seed)
  P_SHA256(S, A_0) = HMAC-SHA256(S, A(1)||seed) ||
                     HMAC-SHA256(S, A(2)||seed) || ...
  where A(0) = seed, A(i) = HMAC-SHA256(S, A(i-1))
```

### 5.5 Finished Message — Handshake Integrity Verification

```
Finished Message
=================

verify_data = PRF(master_secret,
                  label,
                  Hash(handshake_messages))

  label = "client finished" (client's Finished)
  label = "server finished" (server's Finished)
  
  handshake_messages = ALL handshake messages from
                       ClientHello through this Finished
                       (excluding record headers)

verify_data length = 12 bytes (TLS 1.2 default)

IF MISMATCH: fatal alert (handshake_failure or decrypt_error)

ANALYST NOTE: In a MITM attack, modifying any handshake
message will cause Finished verification to fail.
This is why MITM requires a valid certificate — the attacker
must run TWO complete TLS handshakes (one with client, one with server).
```

### 5.6 Alert Protocol

```
Alert Message Structure
========================

Level:    1 byte
  1 = warning  (session can continue)
  2 = fatal    (session terminates immediately)

Description: 1 byte
  0  = close_notify          (normal termination)
  10 = unexpected_message
  20 = bad_record_mac        (auth tag failure / wrong key)
  21 = decryption_failed     (historical, now bad_record_mac)
  22 = record_overflow
  40 = handshake_failure     (no common cipher suite)
  42 = bad_certificate
  44 = certificate_revoked
  45 = certificate_expired
  46 = certificate_unknown
  47 = illegal_parameter
  48 = unknown_ca            (cert chain didn't validate)
  50 = decode_error
  51 = decrypt_error         (Finished failed to verify)
  70 = protocol_version      (unsupported version)
  71 = insufficient_security (cipher too weak)
  80 = internal_error
  90 = user_cancelled
  100= no_renegotiation
  110= unsupported_extension

FORENSIC VALUE: Alert codes in PCAP tell you WHY a TLS
session failed. bad_record_mac on first application data
record = wrong key material = botched malware implementation.
unknown_ca = malware using self-signed cert, client not configured
to accept it.
```

---

## 6. TLS 1.3 — Complete Redesign

### 6.1 What Changed and Why

TLS 1.3 is a fundamental redesign motivated by years of attacks:

| Removed from TLS 1.3 | Reason |
|---|---|
| RSA key exchange | No forward secrecy |
| DH with static keys | No forward secrecy |
| CBC mode ciphers | Padding oracle attacks (POODLE, BEAST) |
| RC4 | Broken statistically |
| MD5, SHA-1 | Weak collision resistance |
| Compression | CRIME attack |
| Renegotiation | Triple Handshake attack |
| Session tickets (unencrypted) | Traffic analysis |
| ServerHelloDone | Unnecessary round-trip |
| ChangeCipherSpec | Redundant (still sent for compatibility) |
| Exportable cipher suites | Historical US export regulations |

### 6.2 TLS 1.3 Handshake — 1-RTT

```
TLS 1.3 Full Handshake (1-RTT)
================================

Client                                        Server
  │                                              │
  │──── ClientHello ────────────────────────►   │
  │     legacy_version: 0x0303                  │
  │     random: 32 bytes                        │
  │     legacy_session_id: 32 bytes (compat)    │
  │     cipher_suites: TLS 1.3 only             │
  │     extensions:                             │
  │       supported_versions: [TLS 1.3]         │
  │       key_share: x25519 public key          │
  │       signature_algorithms                  │
  │       supported_groups                      │
  │                                              │
  │  ◄── ServerHello ─────────────────────────  │
  │      legacy_version: 0x0303                 │
  │      random: 32 bytes                       │
  │      extensions:                            │
  │        supported_versions: TLS 1.3          │
  │        key_share: server x25519 public key  │
  │                                             │
  │  [Both sides derive handshake keys NOW]     │
  │  handshake_secret = HKDF-Extract(...)       │
  │                                             │
  │  ◄── {EncryptedExtensions} ──────────────  │ ← ENCRYPTED
  │  ◄── {Certificate} ───────────────────────  │ ← ENCRYPTED
  │  ◄── {CertificateVerify} ─────────────────  │ ← ENCRYPTED
  │  ◄── {Finished} ───────────────────────────  │ ← ENCRYPTED
  │                                              │
  │  [Client derives application keys]          │
  │                                              │
  │──── {Finished} ──────────────────────────►  │ ← ENCRYPTED
  │                                              │
  │ ◄════ {Application Data} ════════════════►  │ ← ENCRYPTED
  │                                             │

CRITICAL: Server sends EncryptedExtensions, Certificate,
CertificateVerify, and Finished ALL ENCRYPTED with
handshake traffic keys. Certificate is never in plaintext!
```

### 6.3 TLS 1.3 0-RTT (Early Data)

```
TLS 1.3 0-RTT Handshake
=========================

PRE-CONDITION: Previous session with same server
               Server issued a session ticket

Client                                        Server
  │──── ClientHello ────────────────────────►  │
  │       pre_shared_key extension             │
  │       early_data extension                 │
  │                                            │
  │──── {Early Data (0-RTT)} ────────────────►  │ ← encrypted with PSK
  │                                            │
  │  ◄── ServerHello ─────────────────────────  │
  │  ◄── {EncryptedExtensions} ───────────────  │
  │       (contains early_data extension)      │
  │  ◄── {Finished} ───────────────────────────  │
  │                                            │
  │──── {EndOfEarlyData} ─────────────────────►  │
  │──── {Finished} ───────────────────────────►  │
  │                                            │
  │ ◄════ {Application Data} ════════════════►  │

SECURITY RISKS OF 0-RTT:
  1. REPLAY ATTACKS: 0-RTT data can be replayed by attacker.
     Server must implement anti-replay (e.g., session ticket nonce cache).
  2. Forward secrecy broken for 0-RTT: uses PSK, not ephemeral key.
  3. Not suitable for non-idempotent requests (e.g., POST transactions).

APT RELEVANCE: 0-RTT enables sub-RTT C2 beacons.
Implants using 0-RTT can send commands with zero added latency.
Detection: look for early_data extension in ClientHello.
```

### 6.4 TLS 1.3 Key Schedule — HKDF-Based

```
TLS 1.3 Key Schedule (complete)
================================

Early Secret:
  early_secret = HKDF-Extract(0, PSK or 0)
                   │
                   ├──► client_early_traffic_secret
                   │    = Derive-Secret(early_secret, "c e traffic", CH)
                   │
                   └──► early_exporter_master_secret
                        = Derive-Secret(early_secret, "e exp master", CH)

Handshake Secret:
  derived_secret = Derive-Secret(early_secret, "derived", "")
  handshake_secret = HKDF-Extract(derived_secret, DHE)
                       │
                       ├──► client_handshake_traffic_secret
                       │    = Derive-Secret(HS, "c hs traffic", CH..SH)
                       │
                       └──► server_handshake_traffic_secret
                            = Derive-Secret(HS, "s hs traffic", CH..SH)

Master Secret:
  derived_secret = Derive-Secret(handshake_secret, "derived", "")
  master_secret = HKDF-Extract(derived_secret, 0)
                    │
                    ├──► client_application_traffic_secret_0
                    │    = Derive-Secret(MS, "c ap traffic", CH..SF)
                    │
                    ├──► server_application_traffic_secret_0
                    │    = Derive-Secret(MS, "s ap traffic", CH..SF)
                    │
                    ├──► exporter_master_secret
                    │    = Derive-Secret(MS, "exp master", CH..CF)
                    │
                    └──► resumption_master_secret
                         = Derive-Secret(MS, "res master", CH..CF)

Traffic Keys from each traffic secret:
  [key, iv] = HKDF-Expand-Label(traffic_secret, "key"/"iv", "", key_len/iv_len)

HKDF-Expand-Label(Secret, Label, Context, Length):
  HkdfLabel = Length || ("tls13 " + Label) || Context
  return HKDF-Expand(Secret, HkdfLabel, Length)

Derive-Secret(Secret, Label, Messages):
  return HKDF-Expand-Label(Secret, Label, Transcript-Hash(Messages), Hash.length)
```

### 6.5 CertificateVerify in TLS 1.3

```
CertificateVerify Message
==========================

Input to signature:
  64 bytes of 0x20 (space)  ← prevents cross-protocol attacks
  context string: "TLS 1.3, server CertificateVerify"
  0x00 byte separator
  transcript hash (SHA-256 of all handshake messages so far)

Signature algorithm used: ed25519, ECDSA P-256, RSA-PSS
(RSA PKCS#1 v1.5 PROHIBITED in TLS 1.3)

WHY: The transcript hash binds the certificate to this
specific handshake. An attacker cannot replay a captured
CertificateVerify from another session.
```

---

## 7. Cipher Suites — Anatomy and Selection

### 7.1 Cipher Suite Naming Convention

```
TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
│    │     │    │    │   │   │
│    │     │    │    │   │   └─ MAC/PRF hash algorithm
│    │     │    │    │   └───── Mode (GCM = Galois/Counter)
│    │     │    │    └───────── Key size (256 bits)
│    │     │    └────────────── Symmetric cipher (AES)
│    │     └─────────────────── Authentication algorithm (RSA sign)
│    └───────────────────────── Key exchange (ECDHE = ephemeral)
└────────────────────────────── Protocol prefix
```

### 7.2 TLS 1.3 Cipher Suites (Only 5)

| Suite | IANA Code | Cipher | Mode | Hash |
|---|---|---|---|---|
| TLS_AES_128_GCM_SHA256 | 0x1301 | AES-128 | GCM | SHA-256 |
| TLS_AES_256_GCM_SHA384 | 0x1302 | AES-256 | GCM | SHA-384 |
| TLS_CHACHA20_POLY1305_SHA256 | 0x1303 | ChaCha20 | Poly1305 | SHA-256 |
| TLS_AES_128_CCM_SHA256 | 0x1304 | AES-128 | CCM | SHA-256 |
| TLS_AES_128_CCM_8_SHA256 | 0x1305 | AES-128 | CCM-8 | SHA-256 |

**Note:** TLS 1.3 cipher suites do NOT specify key exchange or auth — those are separate extensions. This is a critical architectural improvement.

### 7.3 TLS 1.2 Cipher Suites — Dangerous vs. Safe

```
DANGEROUS (NEVER USE):
  0x0035  TLS_RSA_WITH_AES_256_CBC_SHA       ← no PFS, CBC
  0x002F  TLS_RSA_WITH_AES_128_CBC_SHA       ← no PFS, CBC
  0x0005  TLS_RSA_WITH_RC4_128_SHA           ← RC4 broken
  0x0004  TLS_RSA_WITH_RC4_128_MD5           ← RC4 + MD5 = catastrophic
  0x0000  TLS_NULL_WITH_NULL_NULL            ← no encryption at all!
  0xFF    SCSV (Signaling Cipher Suite Value) ← pseudo-value
  
SAFE (RECOMMENDED):
  0xC02B  TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256  ← best
  0xC02F  TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256    ← common
  0xCCA9  TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305   ← mobile-friendly
  0xCCA8  TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305     ← mobile-friendly

MALWARE FINGERPRINT: Unusual cipher suite ordering or
selection of deprecated suites identifies specific TLS
implementations. Golang standard library, Python urllib3,
OpenSSL, WinHTTP, and NSS all have distinct fingerprints.
```

### 7.4 GREASE (Generate Random Extensions And Sustain Extensibility)

```
GREASE Values (RFC 8701)
=========================

Chrome and modern TLS clients insert GREASE values to prevent
ossification (servers that reject unknown values).

GREASE cipher suite values:
  0x0A0A, 0x1A1A, 0x2A2A, 0x3A3A, 0x4A4A, 0x5A5A,
  0x6A6A, 0x7A7A, 0x8A8A, 0x9A9A, 0xAAAA, 0xBABA,
  0xCACA, 0xDADA, 0xEAEA, 0xFAFA

GREASE in extensions: same values used for extension types
GREASE in supported_groups: same values

FINGERPRINTING IMPLICATION:
  Chrome inserts GREASE → identifiable in JA3 string
  Most malware does NOT insert GREASE
  Presence/absence of GREASE is a browser-vs-malware signal
```

---

## 8. Key Derivation — PRF (TLS 1.2) and HKDF (TLS 1.3)

### 8.1 TLS 1.2 PRF (P_hash)

```
PRF Implementation (TLS 1.2)
==============================

// Pseudocode
function P_hash(secret, seed, length):
    A = [seed]  // A(0) = seed
    output = []
    while len(output) < length:
        A.append(HMAC_SHA256(secret, A[-1]))  // A(i) = HMAC(secret, A(i-1))
        output += HMAC_SHA256(secret, A[-1] + seed)
    return output[:length]

function PRF(secret, label, seed, length):
    return P_hash(secret, label + seed, length)

// MasterSecret derivation
master_secret = PRF(
    pre_master_secret,
    "master secret",
    client_random + server_random,
    48  // bytes
)

// Key block derivation
key_block = PRF(
    master_secret,
    "key expansion",
    server_random + client_random,  // NOTE: reversed order!
    key_material_length
)
```

### 8.2 HKDF (TLS 1.3)

HKDF = HMAC-based Key Derivation Function (RFC 5869).

```
HKDF Construction
==================

Two stages:
  1. Extract: compress random input into uniform key material
  2. Expand:  expand uniform key material into application keys

HKDF-Extract(salt, IKM):
  return HMAC-Hash(salt, IKM)
  // salt = previous stage output or zeros
  // IKM  = input key material (DHE secret, PSK, or zeros)
  // output = pseudorandom key (PRK)

HKDF-Expand(PRK, info, length):
  T(0) = ""
  T(1) = HMAC-Hash(PRK, T(0) || info || 0x01)
  T(2) = HMAC-Hash(PRK, T(1) || info || 0x02)
  ...
  return first `length` bytes of T(1) || T(2) || ...

HKDF-Expand-Label(Secret, Label, Context, Length):
  HkdfLabel = uint16(Length) || uint8(len("tls13 "+Label)) ||
              "tls13 " || Label || uint8(len(Context)) || Context
  return HKDF-Expand(Secret, HkdfLabel, Length)
```

### 8.3 Memory Artifacts of Key Material

```
WHERE TO FIND TLS KEY MATERIAL IN MEMORY
==========================================

OpenSSL (libssl.so / libssl.dll):
  SSL_SESSION structure contains master_secret
  SSL structure contains read/write BIO and cipher state

  Relevant fields (OpenSSL 1.1.x):
    ssl_st->s3->client_random    ← 32 bytes at fixed offset
    ssl_st->s3->server_random    ← 32 bytes
    ssl_st->session->master_key  ← 48 bytes master secret

WinSCHANNEL (Windows TLS):
  Located in lsass.exe process memory
  NCRYPT key blobs contain private key material
  
  Key material scan:
    Look for sequences of 32/48 bytes following random bytes
    Pattern: two 32-byte random values adjacent in memory

SSLKEYLOGFILE:
  Many TLS implementations support this env var
  Format: CLIENT_RANDOM <hex_random> <hex_master_secret>
  Malware hunters: grep implant processes for this env var
  
  Wireshark can use this file to decrypt TLS in PCAP:
    Edit → Preferences → Protocols → TLS → (Pre)-Master-Secret log
```

---

## 9. TLS Extensions — Complete Catalog

Extensions are how TLS negotiates capabilities. Every extension in ClientHello is a fingerprinting opportunity.

### 9.1 Extension Format

```
Extension Wire Format
======================

extension_type:   2 bytes (extension ID)
extension_data:   variable, preceded by 2-byte length

Extensions block in ClientHello:
  [2 bytes total extensions length]
  [extension_type: 2][extension_length: 2][extension_data: var]
  [extension_type: 2][extension_length: 2][extension_data: var]
  ...
```

### 9.2 Critical Extensions — Technical Deep Dive

#### SNI — Server Name Indication (Extension Type 0x0000)

```
SNI Extension
=============

Solves the problem: Multiple HTTPS sites on same IP.
Without SNI, server doesn't know which cert to present.

Wire format:
  00 00              extension_type = SNI (0)
  00 12              extension_length = 18
  00 10              server_name_list_length = 16
  00                 server_name_type = host_name (0)
  00 0d              hostname_length = 13
  65 78 61 6d ...    "example.com"

SECURITY IMPLICATIONS:
  SNI is PLAINTEXT in ClientHello (TLS 1.2 and 1.3!)
  Network observer can see target hostname for EVERY connection.
  
  ESNI (Encrypted SNI) → now ECH (Encrypted Client Hello, RFC 9258)
  ECH encrypts the entire inner ClientHello using server's public key
  obtained from DNS HTTPS record.

MALWARE USAGE:
  APT operators often configure C2 with:
  - Domain fronting: SNI = legitimate CDN domain (e.g., ajax.googleapis.com)
    Host header = actual C2 subdomain
    CDN routes based on Host header, TLS terminates on CDN
  - This defeats SNI-based blocking

DETECTION:
  Mismatch between SNI and HTTP Host header = domain fronting indicator
  SNI targeting cloud CDN domains from non-browser processes
```

#### Supported Groups (Extension Type 0x000A)

```
Supported Groups (formerly: Elliptic Curves)
=============================================

Specifies which EC curves/groups client supports:
  0x001d  x25519      ← modern, fast, preferred
  0x0017  secp256r1   ← NIST P-256, widely supported
  0x0018  secp384r1   ← NIST P-384
  0x0019  secp521r1   ← NIST P-521
  0x001e  x448
  0x0100  ffdhe2048   ← Finite-field DH (TLS 1.3)
  0x0101  ffdhe3072
  
FINGERPRINTING: The ORDER of groups is implementation-specific.
Firefox, Chrome, OpenSSL, Go's crypto/tls each have distinct orderings.
```

#### Key Share (Extension Type 0x0033) — TLS 1.3 Only

```
Key Share Extension
===================

Client sends one or more ECDHE public keys speculatively.
Server picks one, sends its share. If client didn't send
the server's preferred group, server sends HelloRetryRequest.

Client Key Share (for x25519):
  00 33              extension_type = key_share
  00 26              extension_length = 38
  00 24              client_shares_length = 36
  00 1d              group = x25519 (29)
  00 20              key_exchange_length = 32
  [32 bytes]         client public key

Server Key Share:
  00 33              extension_type = key_share
  00 24              extension_length = 36
  00 1d              group = x25519
  00 20              key_exchange_length = 32
  [32 bytes]         server public key

ANALYTICAL NOTE: Both x25519 public keys are transmitted in
plaintext. An attacker with the PRIVATE keys (e.g., obtained
via memory forensics or key export) can derive the shared secret
and decrypt ALL TLS 1.3 sessions retroactively — UNLESS
ephemeral keys are properly discarded after session end.
```

#### ALPN — Application Layer Protocol Negotiation (0x0010)

```
ALPN Extension
==============

Negotiates application protocol WITHIN TLS.
Prevents port ambiguity.

Values:
  "http/1.1"    HTTP/1.1 over TLS
  "h2"          HTTP/2 (mandatory for HTTP/2)
  "h3"          HTTP/3 (QUIC)
  "ftp"         FTP over TLS
  "dot"         DNS over TLS
  "acme-tls/1"  ACME certificate issuance
  "grpc"        gRPC
  
MALWARE RELEVANCE:
  Custom ALPN values = custom C2 protocol.
  Impacket uses non-standard ALPN.
  Cobalt Strike historically used "http/1.1" always.
  
  Novel C2s may use:
  - No ALPN (omitting the extension)
  - Single unexpected ALPN value
  - Custom string not in IANA registry
  
DETECTION:
  Process sends ALPN "h2" but traffic pattern is not HTTP/2.
  Unusual ALPN values from non-browser processes.
```

#### Session Ticket (0x0023) and Pre-Shared Key (0x0029)

```
Session Ticket (TLS 1.2)
=========================

Server generates encrypted blob containing session state:
  ticket = Encrypt(ticket_key, {master_secret, cipher_suite,
                                client_certs, timestamp})
  
  ticket_key = server-side symmetric key (NOT sent to client)
  
Client stores ticket; on reconnect sends it in ClientHello.
Server decrypts, extracts master_secret, resumes session.

SECURITY NOTES:
  - Ticket key rotation determines effective PFS for resumption
  - Stateless: server doesn't store session server-side
  - Ticket contains master_secret → ticket key compromise = mass decryption

Pre-Shared Key (TLS 1.3, 0x0029)
==================================

Used for session resumption (replacing session tickets).
PSK binder proves knowledge of PSK without revealing it.

  psk_identity: opaque ticket from previous session
  obfuscated_ticket_age: timestamp (obfuscated)
  binders: HMAC(early_secret, handshake_transcript)
```

#### Certificate Status Request — OCSP Stapling (0x0005)

```
OCSP Stapling
=============

Without stapling: client must contact OCSP responder to check
revocation status → leaks browsing history to OCSP responder.

With stapling: server attaches OCSP response in Certificate
message → client verifies OCSP response offline.

Extension in ClientHello:
  status_type = ocsp (1)
  responder_id_list (optional)
  request_extensions (optional)

Server response: CertificateStatus handshake message with
signed OCSP response.

MALWARE IMPLICATION: Most malware TLS clients do NOT request
OCSP stapling. Its absence from ClientHello is one fingerprint
distinguishing malware from browsers.
```

### 9.3 Extension Fingerprinting Table

| Extension | Type | Chrome | Firefox | Go stdlib | Curl/OpenSSL | Malware (generic) |
|---|---|---|---|---|---|---|
| SNI | 0x0000 | ✓ | ✓ | ✓ | ✓ | Sometimes missing |
| Extended Master Secret | 0x0017 | ✓ | ✓ | ✓ | ✓ | Often missing |
| Renegotiation Info | 0xFF01 | ✓ | ✓ | ✓ | ✓ | Often missing |
| Supported Groups | 0x000A | ✓ | ✓ | ✓ | ✓ | Minimal list |
| EC Point Formats | 0x000B | ✓ | ✓ | × | ✓ | Varies |
| Session Ticket | 0x0023 | ✓ | ✓ | ✓ | ✓ | Often missing |
| ALPN | 0x0010 | ✓ | ✓ | × | ✓ | Suspicious values |
| Status Request (OCSP) | 0x0005 | ✓ | ✓ | × | Opt | Almost never |
| SCT | 0x0012 | ✓ | × | × | × | Never |
| GREASE | Various | ✓ | × | × | × | Never |
| Compress Certificate | 0x001B | ✓ | ✓ | × | × | Never |

---

## 10. Mutual TLS (mTLS)

### 10.1 mTLS — Full Handshake with Client Authentication

```
mTLS Handshake Flow
====================

Client                                         Server
  │──── ClientHello ──────────────────────►    │
  │                                            │
  │ ◄─── ServerHello ─────────────────────     │
  │ ◄─── Certificate (server cert) ──────     │
  │ ◄─── ServerKeyExchange (if DHE) ──────    │
  │ ◄─── CertificateRequest ──────────────    │ ← requests client cert
  │ ◄─── ServerHelloDone ─────────────────    │
  │                                            │
  │──── Certificate (client cert) ──────────►  │
  │──── ClientKeyExchange ──────────────────►  │
  │──── CertificateVerify ──────────────────►  │ ← proves key ownership
  │──── ChangeCipherSpec ───────────────────►  │
  │──── Finished ───────────────────────────►  │
  │                                            │
  │ ◄─── ChangeCipherSpec ─────────────────    │
  │ ◄─── Finished ─────────────────────────    │
  │                                            │

CertificateVerify (client):
  signature = Sign(client_private_key,
                   Hash(all_handshake_messages_so_far))
  
  Server verifies against client's certificate public key.
```

### 10.2 APT Use of mTLS for C2 Authentication

```
APT mTLS C2 Architecture
==========================

PROBLEM FOR OPERATOR: If C2 server is identified, blocking
its IP/domain stops campaign. Anyone can connect and probe.

SOLUTION: mTLS with operator-issued client certificates.
  - Server accepts ONLY connections with valid client certs
  - Client certs signed by private CA (operator-controlled)
  - CA cert NOT publicly known → analysts cannot mint valid certs

IMPLEMENTATION:
  operator generates:
    ca_key.pem    ← private, never leaves operator control
    ca_cert.pem   ← embedded in C2 server config
    implant_key.pem   ← unique per campaign/implant
    implant_cert.pem  ← signed by ca_key, embedded in implant

  C2 server SSL_CTX:
    SSL_CTX_set_verify(ctx, SSL_VERIFY_PEER | SSL_VERIFY_FAIL_IF_NO_PEER_CERT, verify_cb)
    SSL_CTX_load_verify_locations(ctx, "ca_cert.pem", NULL)

  If analyst connects without valid cert → handshake failure
  If analyst presents wrong cert → verify_cb returns 0 → failure

REAL WORLD:
  - SUNBURST (APT29 SolarWinds): Used HTTPS with specific
    UserAgent/URI patterns as first-stage authentication before
    C2 commands. Not strict mTLS but behavioral equivalent.
  - APT41 malware POISONPLUG: Used custom PKI for C2 auth.
  - Cobalt Strike Team Servers: Can be configured for mTLS.

DETECTION:
  - Extract embedded certificates from malware binary
  - Check certificate issuer — self-signed CA with no CT logs
  - Look for certificate loading code at binary level
  - Reverse engineer the private CA to monitor C2 infrastructure
```

---

## 11. Session Resumption — Tickets and Session IDs

### 11.1 Session ID Resumption (TLS 1.2)

```
Session ID Resumption
======================

INITIAL CONNECTION:
  ClientHello { session_id = 0x0000...0000 (empty) }
  ServerHello { session_id = <32 bytes server-assigned ID> }
  Server stores: {session_id → master_secret, cipher_suite}

RESUMPTION:
  ClientHello { session_id = <previously received ID> }
  
  If server finds session_id in cache:
    ServerHello { session_id = same ID }
    [No Certificate, no ServerKeyExchange!]
    ChangeCipherSpec
    Finished
    
  If not found (session expired):
    ServerHello { session_id = new 32-byte ID }
    [Full handshake]

DRAWBACK:
  - Server must maintain session cache (memory pressure)
  - Session cannot resume across multiple server instances
  - Session ticket solves this (stateless server-side)
```

### 11.2 Session Ticket Resumption (TLS 1.2)

```
Session Ticket Flow
====================

INITIAL:
  Client: extension { session_ticket = empty }
  Server → Client: NewSessionTicket {
    ticket_lifetime_hint: 3600 seconds
    ticket: encrypted_blob
  }
  Client stores ticket for this server.

RESUMPTION:
  ClientHello { session_ticket = <stored blob> }
  Server decrypts ticket → extracts master_secret
  If valid: abbreviated handshake
  If expired/invalid: full handshake

TICKET STRUCTURE (server-side implementation):
  ticket = AES_128_CBC(ticket_key, {
    master_secret:    48 bytes
    client_identity:  variable (certificates)
    cipher_suite:     2 bytes
    creation_time:    8 bytes
    expiry_time:      8 bytes
  }) + HMAC_SHA256(hmac_key, ciphertext)

FORWARD SECRECY WARNING:
  Session tickets break forward secrecy for resumption.
  The master_secret (derived from ephemeral ECDHE) is stored
  in the ticket. If ticket_key is compromised (static key),
  all sessions resumed with that key can be decrypted.
  
  MITIGATION: Rotate ticket_key every 24 hours minimum.
```

---

## 12. TLS Fingerprinting — JA3, JA3S, JA4, JARM

### 12.1 JA3 — Client Fingerprinting

JA3 was developed by John Althouse, Jeff Atkinson, and Josh Atkins at Salesforce in 2017. It fingerprints TLS clients based on ClientHello parameters.

```
JA3 Algorithm
==============

Extract from ClientHello:
  1. TLS Version (from record header, not extensions)
  2. Cipher Suites (list, excluding GREASE)
  3. Extensions (list of type codes, excluding GREASE)
  4. Elliptic Curves (from supported_groups, excluding GREASE)
  5. EC Point Formats (from ec_point_formats)

Concatenate with dashes within fields, commas between:
  string = "Version,CipherSuites,Extensions,EllipticCurves,EllipticCurvePointFormats"

JA3 = MD5(string)

EXAMPLE:
  Version:       771 (TLS 1.2 = 0x0303)
  Ciphers:       49195,49199,52393,52392,49196,49200,49162,49161,49171,49172,51,57
  Extensions:    0,23,65281,10,11,35,16,5,13,18,51,45,43,27,17513,21
  Groups:        29,23,24
  Point Formats: 0

  String: "771,49195-49199-...,0-23-...,29-23-24,0"
  JA3:    "MD5 of above string" = e.g., "769e8f64d86fc4a6e0f19e19c5fa99ed"

Known JA3 hashes:
  51c64c77e60f3980eea90869b68c58a8  ← Metasploit
  de9f13b1e54f3bd40b11c1cd73dab95b  ← Cobalt Strike (default profile)
  a0e9f5d64349fb13191bc781f81f42e1  ← CobaltStrike malleable profile
  72a589da586844d7f0818ce684948eea  ← Mirai botnet
  6734f37431670b3ab4292b8f60f29984  ← TrickBot
  b386946a5a44d1ddcc843bc75336dfce  ← Emotet
```

### 12.2 JA3S — Server Fingerprinting

```
JA3S Algorithm
==============

Extract from ServerHello:
  1. TLS Version
  2. Cipher Suite (single value chosen by server)
  3. Extensions (list of types in ServerHello)

String = "Version,CipherSuite,Extensions"
JA3S = MD5(string)

USAGE:
  JA3 alone: identifies client implementation
  JA3S alone: identifies server implementation
  JA3 + JA3S pair: identifies C2 communication channel

EXAMPLE C2 DETECTION:
  JA3  matches Cobalt Strike malleable profile
  JA3S matches known C2 framework response pattern
  → High confidence C2 traffic despite valid TLS certificate
```

### 12.3 JA4 — Next Generation Fingerprinting

```
JA4 Algorithm (John Althouse, 2023)
=====================================

Improvements over JA3:
  - Sorted cipher suites (order-independent)
  - Sorted extensions (except first and last, per RFC)
  - Handles TLS 1.3 properly
  - More granular fingerprint components

JA4 format: t{tls_version}{SNI}{num_ciphers}{num_extensions}{alpn}_{cipher_hash}_{ext_hash}

Example breakdown:
  t  = TLS (d = DTLS, q = QUIC)
  13 = TLS 1.3
  d  = SNI present (d=domain, i=IP, n=none)
  12 = number of cipher suites
  14 = number of extensions
  h2 = first ALPN value (or "00" if none)
  _ separator
  {12-char cipher hash} = first 12 chars of SHA256 of sorted ciphers (hex)
  _ separator
  {12-char ext hash}    = first 12 chars of SHA256 of sorted extensions (hex)

Full JA4: "t13d1214h2_94c3e27be1_60f7c41be6"
```

### 12.4 JARM — Server-Side Active Fingerprinting

```
JARM (Salesforce, 2020)
========================

Active technique: Send 10 specially crafted ClientHellos
to a server, record its responses.

10 probes use different combinations of:
  - TLS version (TLS 1.0, 1.1, 1.2, 1.3)
  - Cipher suite ordering (forward, reverse)
  - Extension combinations
  - Protocol version in record vs. extensions

Each ServerHello response = 1 character in JARM hash.
Result = 62-character JARM fingerprint.

HOW IT WORKS:
  probe_1: TLS 1.2, cipher list in forward order
  probe_2: TLS 1.2, cipher list in reverse order
  probe_3: TLS 1.2, only forward-secret ciphers
  probe_4: TLS 1.2, MAX_FRAGMENT_LENGTH extension
  probe_5: TLS 1.3, cipher list in forward order
  probe_6: TLS 1.3, cipher list in reverse order
  probe_7: TLS 1.2, only non-forward-secret ciphers
  probe_8: TLS 1.2, TLS_EMPTY_RENEGOTIATION_INFO_SCSV
  probe_9: TLS 1.3, no supported_versions extension
  probe_10: TLS 1.3, all TLS 1.3 ciphers

From each ServerHello: extract cipher + version → 6 chars
JARM = concatenation of 10 x 6-char responses

Known JARM fingerprints:
  Cobalt Strike:    "07d14d16d21d21d07c42d41d00041d24a458a375eef0c576d23a7bab9a9fb1"
  Metasploit:       "05d02d19d00000000000000000000000000000000000000000000000000000"
  Merlin C2:        "29d29d00029d29d29d29d29d29d29d..." (varies by version)
  Apache HTTPD:     "2ad2ad0002ad2ad2ad2ad2ad2ad2ad..."

USAGE: Scan known C2 IPs with JARM to attribute infrastructure.
Shodan indexes JARM fingerprints.
```

---

## 13. APT Abuse of TLS — C2, Exfiltration, Tunneling

### 13.1 Domain Fronting

```
Domain Fronting Architecture
=============================

                    ┌────────────────────────────────┐
                    │       CDN / Cloud Provider      │
                    │   (Cloudflare, AWS CloudFront,  │
                    │    Azure Front Door, Fastly)    │
                    │                                  │
                    │  CDN routes based on HTTP Host   │
                    │  header AFTER TLS termination    │
                    └────────────────────────────────┘
                           ▲                  │
                           │                  │
          TLS with          │                  │ HTTP request forwarded
          SNI =             │                  │ to origin based on Host
          "cdn.legit.com"  │                  │ header value
                           │                  ▼
┌─────────────┐            │        ┌─────────────────────┐
│   Implant   │────────────┘        │   C2 Server         │
│             │                     │   actual C2 IP      │
│ SNI:        │                     │   hosted as CDN     │
│   cdn.legit │                     │   customer          │
│ Host header:│                     └─────────────────────┘
│   c2.evil   │
└─────────────┘

ANALYST VIEW:
  Network logs show: connection to cdn.legit.com
  TLS cert: valid for *.cdn.legit.com
  JA3/TLS: normal-looking
  → INVISIBLE at network level

MITIGATION: Major CDNs now prohibit domain fronting.
  Cloudflare: blocked ~2018
  AWS: blocked 2022 (required after APT29 SUNBURST)
  Google: ended ~2018 (affected Signal, Tor usage)
  Azure: still possible in some configurations

DETECTION:
  SNI vs Host header mismatch (requires TLS inspection)
  Unusual volume to generic CDN with CDN-inconsistent timing
  HTTP Host header containing uncommon/unknown domains via CDN
```

### 13.2 TLS Tunneling Techniques

```
TLS Tunneling Variants
========================

1. HTTPS TUNNEL (most common):
   HTTP CONNECT → establish TCP tunnel → run TLS inside
   Used by: Cobalt Strike, Metasploit, custom RATs
   
   Detection: CONNECT method to non-standard destination,
   long-lived "established" TCP connections through proxy

2. DNS-over-TLS (DoT) ABUSE:
   Port 853, looks like DoT traffic
   Real DNS queries mixed with C2 commands in DNS TXT records
   
   Detection: Volume/timing anomalies on port 853,
   unusual query types (TXT records with base64 content)

3. TLS OVER WebSocket:
   HTTP/1.1 Upgrade to WebSocket
   Binary WebSocket frames carry encrypted C2 payload
   Appears as legitimate WSS traffic
   
   Detection: WebSocket connections from non-browser processes,
   small uniform-size frames at regular intervals

4. HTTP/2 ABUSE:
   Multiplexed streams within single TLS connection
   C2 commands in one stream, legitimate data in another
   Harder to detect than HTTP/1.1 (single connection, mixed)
   
   Detection: Persistent HTTP/2 connections from unlikely processes,
   unusual stream patterns (regular small POSTs + small GETs)

5. gRPC C2:
   Built on HTTP/2 + TLS + Protocol Buffers
   Appears as legitimate microservice traffic
   Hard to distinguish from legitimate gRPC
   
   Real usage: Sliver C2 framework uses gRPC as primary protocol
   Detection: gRPC service names in Protobuf headers that don't match
   organization's known services
```

### 13.3 Beacon Traffic Analysis

```
Cobalt Strike Beacon — TLS Fingerprinting
==========================================

Default Cobalt Strike TLS fingerprint (JA3):
  "72a589da586844d7f0818ce684948eea"  ← WELL KNOWN, will be detected!

Default Malleable C2 profile generates:
  Specific cipher suite ordering
  Specific extension list
  Default JARM fingerprint

BEACON MATH:
  Cobalt Strike beacon interval with jitter:
  sleep_time = base_sleep * (1 ± jitter%)
  
  To detect: calculate inter-beacon intervals
  If intervals form normal distribution around base ± jitter,
  and match known CS configurations → beacon with high confidence.

  cs_intervals = [30±15%, 30±15%, 30±15%, ...] seconds
  → distribution peaks around 25-35 seconds

PCAP DETECTION:
  1. Calculate time delta between outbound TLS connections to same IP/port
  2. Check for normal distribution (histogram)
  3. If coefficient of variation < 0.3 and period matches common CS values
     → likely beacon

KNOWN COBALT STRIKE TEAM SERVER JARM:
  07d14d16d21d21d07c42d41d00041d24a458a375eef0c576d23a7bab9a9fb1

Cobalt Strike Profile Customization (operators use these to evade):
  Malleable C2 allows custom:
  - Cipher suite list and order
  - Extension list
  - HTTP URI patterns
  - HTTP headers
  - Sleep jitter
  → Changes JA3 and JARM. Static signatures fail.
  → Behavioral detection required.
```

### 13.4 APT-Specific TLS Patterns

#### APT29 (Cozy Bear) — SUNBURST

```
SUNBURST TLS Analysis
======================

Sample: SolarWinds.Orion.Core.BusinessLayer.dll
Hash: b91ce2fa41029f6955bff20079468448

TLS characteristics:
  - Used .NET HttpClient (WinHTTP underneath)
  - JA3 fingerprint matches legitimate SolarWinds traffic
    (supply chain: implant in legitimate software = legitimate fingerprint)
  
C2 communication:
  - Domain: avsvmcloud.com (DGA-like subdomains)
  - Protocol: HTTPS with legitimate-looking HTTP headers
  - User-Agent rotated to match installed browsers
  - Initial beacon encoded in DNS CNAME response
  
TLS evasion technique:
  - Cert validation NOT disabled (unusual for implant!)
  - Validates server cert against Windows trust store
  - SNI matches actual C2 domain subdomain
  - Designed to look like telemetry traffic

Detection gap exploited:
  SolarWinds product already in enterprise TLS inspection exclusions.
  Traffic assumed legitimate by security tools.
```

#### Lazarus Group — TLS Patterns

```
Lazarus / HIDDEN COBRA TLS Analysis
=====================================

HOPLIGHT backdoor (2019):
  - Embedded self-signed certificates (RSA 2048)
  - Custom TLS implementation in some variants
  - Certificate subject: common fake company names
  - Validity: often 1-2 year from compilation date

BLINDINGCAN RAT:
  - Uses WinHTTP (Microsoft's implementation)
  - JA3 matches WinHTTP default → hard to distinguish
  - Custom application-layer encryption OVER TLS
    (double encryption: TLS outer, XOR/RC4 inner)
  
AppleJeus (macOS cryptocurrency attacks):
  - Uses libcurl for TLS
  - JA3 matches curl user-agent
  - Certificate pinned to custom CA embedded in binary

FINGERPRINT:
  Self-signed cert with these patterns:
  - Issuer CN often = Subject CN (self-signed)
  - Organization field: generic ("Lazarus Inc" in some early samples)
  - Serial number: often 1 or small integer
  - Key: RSA 2048 (rarely EC)
```

#### Volt Typhoon — LOTL TLS Patterns

```
Volt Typhoon TLS Evasion
=========================

TECHNIQUE: Uses Windows built-in tools for TLS,
no custom TLS stack to fingerprint.

Tools observed:
  - PowerShell Invoke-WebRequest (WinHTTP)
  - certutil (for cert operations)
  - netsh (port forwarding through TLS)
  - WMI for remote queries

TLS characteristics:
  - All traffic uses WinHTTP → identical JA3 to legitimate traffic
  - ProxyShell, ProxyLogon exploitation over HTTPS
  - Tunnel traffic through legitimate HTTPS proxies in target network

DETECTION CHALLENGE:
  No custom TLS fingerprint.
  Detection must be behavioral:
  - certutil.exe making outbound TLS connections
  - netsh.exe establishing TLS tunnels
  - PowerShell making TLS connections to unusual destinations
  - Process parent-child relationships (e.g., lsass → powershell → TLS)
```

---

## 14. Historic TLS Vulnerabilities

### 14.1 BEAST (Browser Exploit Against SSL/TLS) — CVE-2011-3389

```
BEAST Attack
=============

AFFECTED: TLS 1.0 (and SSL 3.0) with CBC mode ciphers

ROOT CAUSE: In TLS 1.0, IV for CBC encryption = last ciphertext
block of PREVIOUS record. This makes IV predictable.

ATTACK:
  Attacker can inject chosen plaintext before target plaintext.
  Predictable IV allows block-by-block decryption.

  If attacker knows: P[i-1] (previous block)
                     C[i-1] (previous ciphertext block)
                     IV[i] = C[i-1] (TLS 1.0 explicit predictability)
  
  Then: to test guess G for P[i]:
    inject X = G XOR P[i-1] XOR IV[i]
    observe if E(IV[i] XOR X) = C[i]
    if yes: G is correct plaintext byte

IMPACT: Decrypt session cookies → account hijacking

FIX:
  TLS 1.1: Explicit random IV per record (breaks predictability)
  Mitigations: 1/n-1 record splitting, prioritize RC4 (then RC4 was broken)
  Real fix: Use TLS 1.2+ with AEAD (AES-GCM has no padding)

ANALYST NOTE: BEAST requires MITM + injected JavaScript.
Not a direct TLS wire attack — requires browser + active MITM.
```

### 14.2 CRIME (Compression Ratio Info-leak Made Easy) — CVE-2012-4929

```
CRIME Attack
=============

AFFECTED: TLS/SPDY with compression enabled

ROOT CAUSE: TLS compression (deflate/zlib) reduces data size.
If request contains known prefix (e.g., "Cookie: session="),
attacker can determine cookie value by observing compressed size.

MECHANISM:
  Compression exploits: repeated strings become shorter.
  
  Attacker controls part of HTTP request (injected JavaScript).
  Attacker guesses cookie byte-by-byte.
  
  For guess G:
    Inject "Cookie: session=G" into request
    Observe length of compressed+encrypted data
    
  If G is correct → compression finds "Cookie: session=G"
  repeated in actual cookie header → shorter output.
  If G is wrong → no repetition → no compression → longer.

FIX:
  TLS 1.3: compression REMOVED entirely.
  TLS 1.2: disable TLS compression (now default in all major implementations).
  HTTP: CRIME requires control over request content; prevent cross-origin requests.

VARIANT: BREACH (Browser Reconnaissance and Exfiltration via Adaptive Compression of Hypertext)
  Same principle, HTTP-level compression (gzip) instead of TLS compression.
  Not fixed by TLS 1.3 — requires HTTP-level mitigations.
```

### 14.3 POODLE (Padding Oracle On Downgraded Legacy Encryption) — CVE-2014-3566

```
POODLE Attack
=============

AFFECTED: SSL 3.0 (and TLS 1.0-1.2 in "POODLE for TLS" variant)

ROOT CAUSE: SSL 3.0 CBC padding is not properly validated.
Padding bytes can be ANY value (not checked by MAC).

PADDING STRUCTURE (SSL 3.0):
  [Plaintext | MAC | padding | padding_length]
  padding bytes: any value (ignored after MAC verification)

ATTACK:
  Attacker forces TLS downgrade to SSL 3.0.
  Craft specially padded record that moves target byte to
  position where its value can be deduced from successful/failed MAC.
  
  This is a padding oracle: whether decryption succeeds reveals plaintext.

FIX:
  Disable SSL 3.0 entirely (RFC 7568 - 2015).
  TLS_FALLBACK_SCSV: prevents deliberate version downgrade.
  
  TLS_FALLBACK_SCSV (0x5600):
    Client includes this pseudo-cipher-suite if it's offering
    a lower version than it supports.
    Server receiving this with version < its max → abort.
    Prevents active downgrade attacks.
```

### 14.4 Heartbleed — CVE-2014-0160

```
Heartbleed
==========

AFFECTED: OpenSSL 1.0.1 - 1.0.1f (April 2012 - April 2014)

COMPONENT: TLS Heartbeat extension (RFC 6520)

PURPOSE OF HEARTBEAT:
  Client → Server: HeartbeatRequest { payload_length, payload }
  Server → Client: HeartbeatResponse { payload_length, payload }
  Used for keepalive without renegotiation.

THE BUG (in dtls1_process_heartbeat / tls1_process_heartbeat):

```c
/* Actual vulnerable OpenSSL code (simplified): */
unsigned int payload;
unsigned char *p = &s->s3->rrec.data[0];

/* payload_length from attacker: */
n2s(p, payload);  /* read 2 bytes, no bounds check! */

/* Allocate response: */
unsigned char *bp = OPENSSL_malloc(1 + 2 + payload + padding);
/* Copy "payload" bytes starting from p: */
memcpy(bp, p, payload);  /* READS BEYOND RECEIVED DATA! */
```

IMPACT:
  Attacker sends: HeartbeatRequest { payload_length: 0xFFFF, payload: "A" }
  Server responds with 65535 bytes of memory from heap.
  That memory contains: private keys, session keys, passwords,
  plaintext from other users' sessions.

  Can extract server's TLS private key by repeated requests.
  No authentication required.
  No log entry generated.

EXPLOITATION:
  Cloudflare issued challenge: can you get private key?
  Researchers got private key in ~2.5 million requests.
  
  Basic exploit (Python pseudocode):
    send: 18 03 02 00 03 01 40 00  (heartbeat, 1 byte payload, claim 16384)
    receive: 65535 bytes of server heap memory

FIX: Bounds check added: if (1 + 2 + payload + 16 > s->s3->rrec.length) return 0;

ANALYST NOTE: Two years of OpenSSL exposure. Nation-state actors
almost certainly exploited this before disclosure. All TLS sessions
during 2012-2014 period should be considered potentially compromised
for servers that ran vulnerable OpenSSL.
```

### 14.5 DROWN — CVE-2016-0800

```
DROWN (Decrypting RSA with Obsolete and Weakened eNcryption)
=============================================================

AFFECTED: Any TLS server sharing a key with SSLv2-enabled server

ROOT CAUSE: SSLv2's export-grade RSA cipher (512-bit keys)
            + Bleichenbacher RSA padding oracle

MECHANISM:
  1. Attacker captures modern TLS (RSA key exchange) ciphertext.
  2. Attacker targets ANY server sharing same RSA key that supports SSLv2.
  3. Uses SSLv2 server as oracle to break captured TLS session.
  
  Requires: ~40,000 oracle queries + cloud compute time.
  Actual cost: ~$440 USD on Amazon EC2 in 2016.

SCOPE OF IMPACT:
  33% of HTTPS servers vulnerable at disclosure time.
  Even if YOUR server has SSLv2 disabled,
  if your cert's private key is used by ANY other server
  that has SSLv2 enabled → you're vulnerable.

FIX:
  Disable SSLv2 on ALL servers sharing any certificate/key.
  OpenSSL: SSL_OP_NO_SSLv2
  
LESSONS:
  Certificate/key reuse across services is dangerous.
  Protocol weakness in ONE implementation can compromise ALL
  implementations sharing the same key.
```

### 14.6 ROBOT — Return Of Bleichenbacher's Oracle Threat (2017)

```
ROBOT Attack
=============

AFFECTED: 27 HTTPS servers including Facebook, PayPal, and others

ROOT CAUSE: Incomplete fix for Bleichenbacher (1998) RSA PKCS#1 v1.5
            padding oracle vulnerability.

BLEICHENBACHER ORACLE (1998):
  RSA encryption: C = M^e mod n
  PKCS#1 v1.5 padding for M: 0x00 0x02 [random padding] 0x00 [data]
  
  If decryption reveals "is padding valid?" → oracle exists.
  Oracle allows recovering M bit-by-bit using adaptive chosen ciphertext.

WHY ROBOT (2017):
  Vendors applied fixes that were incomplete.
  Timing differences, behavior differences leaked oracle.
  
  Vulnerable: F5, Citrix, Radware, Cisco ACE load balancers, 
              Bouncy Castle, many other implementations.

FIX:
  Use constant-time operations for RSA PKCS#1 processing.
  Better: switch to ECDHE (no RSA key exchange) → immune.
  TLS 1.3: RSA key exchange removed → immune by design.
```

---

## 15. Certificate Transparency and Passive DNS Pivoting

### 15.1 Certificate Transparency (CT) — RFC 6962

```
Certificate Transparency Architecture
======================================

PROBLEM: CA can issue cert for any domain without domain owner knowing.
SOLUTION: All certs must be logged in public CT logs before browsers trust them.

FLOW:
  CA signs certificate
  CA submits to 2+ CT logs
  Log returns Signed Certificate Timestamp (SCT)
  CA embeds SCT in cert (or delivers via OCSP/TLS extension)
  Browser verifies SCT signature from trusted log
  Browser may require 2+ SCTs from different operators

CT LOG STRUCTURE:
  Merkle hash tree of all submitted certificates
  Log server signs tree root periodically (STH = Signed Tree Head)
  Anyone can audit: verify consistency, inclusion proofs
  
  Public logs: Let's Encrypt, DigiCert, Google Argon, Cloudflare Nimbus

ANALYST TOOLS:
  crt.sh:          search all CT logs by domain/organization/key
  Censys:          indexes CT logs with additional metadata
  Facebook CT:     ct.facebook.com (monitors for your domains)
  certstream:      real-time feed of new CT log entries

PIVOTING TECHNIQUE:
  1. Identify C2 domain (e.g., from PCAP or malware config)
  2. Query CT logs for same certificate key fingerprint
     → find other domains using same private key
  3. Query CT logs for same organization name
     → find certificates issued to same entity
  4. Query CT logs for wildcard on base domain
     → find all subdomains ever used as C2

EXAMPLE PIVOT (crt.sh API):
  https://crt.sh/?q=%.example.com&output=json
  → returns all certificates for *.example.com
  → includes subject, SAN, issuer, dates
```

### 15.2 Passive DNS for Infrastructure Mapping

```
Passive DNS Analysis Workflow
==============================

TOOLS:
  Farsight DNSDB:    historical DNS resolutions
  VirusTotal:        passive DNS + domain reputation
  RiskIQ/PassiveTotal: IP-to-domain historical mapping
  SecurityTrails:    DNS history, subdomains, WHOIS
  Shodan:           TLS cert + open ports + JARM
  Censys:           TLS cert metadata + IP scan data

WORKFLOW FOR APT C2 DISCOVERY:

Step 1: Seed IOC
  Known C2: bad.example.com → 1.2.3.4

Step 2: Pivot on IP (passive DNS)
  1.2.3.4 historically resolved: bad.example.com, evil2.example.com, cmd.another.com
  → expand IOC list

Step 3: Pivot on certificate
  Cert on 1.2.3.4: SHA256 fingerprint = abc123...
  → search crt.sh: same key used on other domains?
  → search Censys: same cert fingerprint on other IPs?

Step 4: Pivot on registration data
  bad.example.com WHOIS: registrant email = admin@throwaway.com
  → search all domains registered by admin@throwaway.com
  → find registration clusters (same email, same dates, similar naming)

Step 5: Pivot on hosting pattern
  1.2.3.4 → ASN 12345 (VPS provider), City: Amsterdam
  → find other IPs in same ASN subnet with similar TLS fingerprints
  → JARM scan subnet → cluster matching C2 JARM

Step 6: Validate and attribute
  Correlate IP/domain/cert clusters with ATT&CK TTPs
  Match tool signatures (JA3, JARM, malware family hashes)
  → attribution hypothesis
```

---

## 16. TLS in Malware — Implementation Patterns and Detection

### 16.1 How Malware Implements TLS

```
TLS Implementation Options for Malware Authors
================================================

1. EMBEDDED OPENSSL (most common, C malware):
   - Statically linked libssl + libcrypto
   - Binary size: +1-4 MB
   - Detection: OpenSSL strings ("OpenSSL 1.0.2", certificate parsing functions)
   - Import scan: no SSL DLL imports (static)
   - DIE/pestudio entropy analysis: large .text section

2. WINHTTPS / WININET (Windows, LOTL):
   - Uses Windows built-in TLS (SChannel)
   - API calls: WinHttpOpen, WinHttpConnect, WinHttpSendRequest
   - JA3 matches WinHTTP → hard to distinguish from legitimate
   - Disadvantage: detectable in API monitoring

3. .NET HTTPCLIENT / SSLSTREAM (C# malware):
   - WinHTTP underneath, managed API
   - ILSpy/dnSpy decompile to near-source
   - JA3 matches .NET default fingerprint

4. GO CRYPTO/TLS (Go malware):
   - Built-in, compiled into binary
   - JA3 fingerprint: identifiable Go pattern
   - Key identifier: pclntab in binary (Go runtime tables)
   - goroutine scheduler visible in analysis

5. RUST RUSTLS or NATIVE-TLS:
   - Rustls: pure Rust, no OpenSSL dependency
   - native-tls: wraps platform TLS (SChannel/SecureTransport/OpenSSL)
   - Smaller binary, harder to fingerprint
   - Growing use in modern ransomware (BlackCat/ALPHV)

6. PYTHON REQUESTS + SSL (script-based):
   - Imports ssl, requests, urllib3
   - Obvious in strings analysis
   - JA3 matches Python/urllib3 fingerprint

7. CUSTOM IMPLEMENTATION (nation-state level):
   - Equation Group: custom symmetric crypto hand-coded
   - Rare: TLS is complex; custom implementation likely has bugs
   - But: allows unique JA3 + removes OpenSSL IOCs
```

### 16.2 TLS in Ghidra — What to Look For

```
Ghidra Analysis of TLS Malware
================================

FINDING OPENSSL:
  Search strings:
    "OpenSSL", "TLSv1.", "sslv2_base_method", "SSL_write", "SSL_read"
    "BEGIN CERTIFICATE", "BEGIN RSA PRIVATE KEY"
    "SSL_CTX_new", "SSL_new", "SSL_connect", "SSL_accept"
  
  Import analysis (dynamic linking):
    libssl.so.* or ssleay32.dll imports
    Relevant exports: SSL_CTX_new, SSL_connect, SSL_read, SSL_write
  
  Static linking (harder):
    Look for large data sections with certificate/key patterns
    Search for AES S-Box: 63 7c 77 7b f2 6b 6f c5 30 01 67 2b fe d7 ab 76
    SHA-256 constants: 6a 09 e6 67 bb 67 ae 85 3c 6e f3 72 a5 4f f5 3a

FINDING CERTIFICATE VALIDATION BYPASS:
  Look for:
    SSL_CTX_set_verify(ctx, SSL_VERIFY_NONE, ...)
    X509_VERIFY_PARAM_set_flags with X509_V_FLAG_NO_CHECK_TIME
    Custom verify callback that always returns 1
  
  In assembly, after call to SSL_CTX_set_verify:
    Push 0x0 (SSL_VERIFY_NONE) as second argument
    
  Ghidra: search for cross-references to SSL_CTX_set_verify
          examine argument pushed before call

FINDING HARDCODED C2 CONFIGURATION:
  Look for:
    Hardcoded IP strings near SSL_connect calls
    Hardcoded port numbers (443, 8443, 4443, 3389, 8080)
    Hardcoded certificate bytes (DER encoded = starts with 30 82)
    Base64-encoded certificate in .data section

FINDING CERTIFICATE DATA:
  Pattern: 30 82 [2 bytes length]  → X.509 DER certificate
  Pattern: 30 82 [2 bytes] 02 01   → PKCS#8 private key
  Entropy: compressed/encrypted data ≥ 7.0 bits/byte
  
  openssl asn1parse -inform DER -in extracted_bytes.bin
```

### 16.3 Dynamic Analysis of TLS Malware

```
Dynamic Analysis Workflow
==========================

GOAL: Decrypt TLS traffic without server private key.

METHOD 1: SSLKEYLOGFILE
  Set environment variable before launching malware:
    SSLKEYLOGFILE=C:\keys.log
  
  Works for: OpenSSL-based malware, NSS (Firefox), Go (patched)
  
  Result file format:
    CLIENT_RANDOM <hex_random> <hex_master_secret>
  
  Wireshark: Edit→Preferences→TLS→Pre-Master-Secret Log

METHOD 2: FRIDA HOOKING
  Hook SSL_write / SSL_read (before encryption, after decryption):
  
  frida -p <pid> -l ssl_hook.js
  
  ssl_hook.js:
    Interceptor.attach(Module.findExportByName("libssl.so", "SSL_write"), {
      onEnter: function(args) {
        var buf = args[1];
        var len = args[2].toInt32();
        console.log(hexdump(buf, {length: len}));
      }
    });
  
  Advantages: Works even with custom TLS or without SSLKEYLOGFILE
  Disadvantages: Detected by anti-Frida checks in some malware

METHOD 3: MAN-IN-THE-MIDDLE (certificate validation disabled)
  If malware doesn't validate certs:
    Run mitmproxy or Burp Suite in transparent mode
    Route malware traffic through proxy
    Proxy intercepts TLS, presents new cert
    Malware accepts any cert → traffic visible
  
  Test: Check for SSL_VERIFY_NONE in binary first

METHOD 4: MEMORY DUMP + KEY EXTRACTION
  After TLS handshake completes:
    Dump malware process memory
    Search for SSL_SESSION structure
    Extract master_secret field (48 bytes)
    Import into Wireshark as SSLKEYLOGFILE entry

METHOD 5: API MONITOR / DETOURS
  Hook at OS level:
    Process Monitor: monitor WinInet.dll / WinHTTP.dll calls
    API Monitor: trace SSL_write / SSL_read arguments
    Detours: DLL injection to wrap SSL functions

TOOL: ssl_logger (Google) — frida-based, logs SSL keys and data
      https://github.com/google/ssl_logger
```

---

## 17. C Implementation — Raw TLS Client/Server

### 17.1 TLS Client (OpenSSL, C)

```c
/* ============================================================
 * TLS 1.3 Client Implementation in C (OpenSSL 3.x)
 * Elite Analyst Reference — Understanding TLS Internals
 * ============================================================ */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <openssl/ssl.h>
#include <openssl/err.h>
#include <openssl/x509v3.h>
#include <openssl/bio.h>

/* TLS version constants */
#define TLS_VERSION_13  TLS1_3_VERSION
#define TLS_VERSION_12  TLS1_2_VERSION

/* ─────────────────────────────────────────────────────────────
 * UTILITY: Dump SSL error stack (critical for debugging TLS)
 * ──────────────────────────────────────────────────────────── */
static void dump_ssl_errors(const char *context) {
    unsigned long err;
    char buf[256];
    fprintf(stderr, "[TLS ERROR] Context: %s\n", context);
    while ((err = ERR_get_error()) != 0) {
        ERR_error_string_n(err, buf, sizeof(buf));
        fprintf(stderr, "  %s\n", buf);
    }
}

/* ─────────────────────────────────────────────────────────────
 * CREATE SSL CONTEXT
 * Configures TLS parameters before any connection
 * ──────────────────────────────────────────────────────────── */
static SSL_CTX *create_client_context(void) {
    const SSL_METHOD *method;
    SSL_CTX *ctx;

    /* TLS_client_method(): auto-negotiates best protocol version
     * Alternative: TLS_method() works for both client and server */
    method = TLS_client_method();
    
    ctx = SSL_CTX_new(method);
    if (!ctx) {
        dump_ssl_errors("SSL_CTX_new");
        exit(EXIT_FAILURE);
    }

    /* ── VERSION CONSTRAINTS ────────────────────────────────── */
    /* Force minimum TLS 1.2 — NEVER accept SSLv3, TLSv1.0, TLSv1.1 */
    if (SSL_CTX_set_min_proto_version(ctx, TLS1_2_VERSION) != 1) {
        dump_ssl_errors("set_min_proto_version");
        SSL_CTX_free(ctx);
        exit(EXIT_FAILURE);
    }
    /* Prefer TLS 1.3 but allow 1.2 fallback */
    SSL_CTX_set_max_proto_version(ctx, TLS1_3_VERSION);

    /* ── CIPHER SUITES ──────────────────────────────────────── */
    /* TLS 1.2 cipher suite string (TLS 1.3 ciphers set separately) */
    if (SSL_CTX_set_cipher_list(ctx,
        "ECDHE-ECDSA-AES256-GCM-SHA384:"
        "ECDHE-RSA-AES256-GCM-SHA384:"
        "ECDHE-ECDSA-CHACHA20-POLY1305:"
        "ECDHE-RSA-CHACHA20-POLY1305:"
        "!aNULL:!MD5:!DSS:!RC4") != 1) {
        dump_ssl_errors("set_cipher_list");
        SSL_CTX_free(ctx);
        exit(EXIT_FAILURE);
    }

    /* TLS 1.3 cipher suite selection (separate API in OpenSSL) */
    if (SSL_CTX_set_ciphersuites(ctx,
        "TLS_AES_256_GCM_SHA384:"
        "TLS_CHACHA20_POLY1305_SHA256:"
        "TLS_AES_128_GCM_SHA256") != 1) {
        dump_ssl_errors("set_ciphersuites");
        SSL_CTX_free(ctx);
        exit(EXIT_FAILURE);
    }

    /* ── CERTIFICATE VERIFICATION ───────────────────────────── */
    /* CRITICAL: Always verify certificate in production.
     * Malware often uses SSL_VERIFY_NONE here — a major IOC. */
    SSL_CTX_set_verify(ctx, SSL_VERIFY_PEER, NULL);
    SSL_CTX_set_verify_depth(ctx, 4);  /* max chain depth */

    /* Load system trust store */
    if (SSL_CTX_set_default_verify_paths(ctx) != 1) {
        dump_ssl_errors("set_default_verify_paths");
        SSL_CTX_free(ctx);
        exit(EXIT_FAILURE);
    }

    /* Alternative: load specific CA bundle */
    /* SSL_CTX_load_verify_locations(ctx, "/etc/ssl/certs/ca-certificates.crt", NULL) */

    /* ── OPTIONS AND FLAGS ──────────────────────────────────── */
    /* Disable compression (CRIME mitigation) */
    SSL_CTX_set_options(ctx, SSL_OP_NO_COMPRESSION);
    
    /* Prevent downgrade attacks */
    SSL_CTX_set_options(ctx, SSL_OP_NO_SSLv2 | SSL_OP_NO_SSLv3 |
                              SSL_OP_NO_TLSv1 | SSL_OP_NO_TLSv1_1);

    /* Enable TLS_FALLBACK_SCSV automatically (done by OpenSSL) */
    SSL_CTX_set_options(ctx, SSL_OP_NO_SESSION_RESUMPTION_ON_RENEGOTIATION);

    return ctx;
}

/* ─────────────────────────────────────────────────────────────
 * CERTIFICATE INSPECTION
 * Extract and display server certificate fields
 * ──────────────────────────────────────────────────────────── */
static void inspect_server_certificate(SSL *ssl, const char *hostname) {
    X509 *cert;
    char subject[256], issuer[256];
    ASN1_TIME *not_before, *not_after;
    EVP_PKEY *pubkey;
    int key_type, key_bits;

    /* Get the peer certificate (NULL if no cert) */
    cert = SSL_get_peer_certificate(ssl);
    if (!cert) {
        fprintf(stderr, "[WARN] Server presented no certificate!\n");
        return;
    }

    /* ── SUBJECT AND ISSUER ─────────────────────────────────── */
    X509_NAME_oneline(X509_get_subject_name(cert), subject, sizeof(subject));
    X509_NAME_oneline(X509_get_issuer_name(cert), issuer, sizeof(issuer));
    printf("[CERT] Subject:  %s\n", subject);
    printf("[CERT] Issuer:   %s\n", issuer);
    
    /* Self-signed detection (subject == issuer) */
    if (strcmp(subject, issuer) == 0) {
        printf("[WARN] Certificate is SELF-SIGNED!\n");
    }

    /* ── VALIDITY PERIOD ─────────────────────────────────────── */
    not_before = X509_get_notBefore(cert);
    not_after  = X509_get_notAfter(cert);
    printf("[CERT] Valid from: ");
    ASN1_TIME_print(BIO_new_fp(stdout, BIO_NOCLOSE), not_before);
    printf("\n[CERT] Valid to:   ");
    ASN1_TIME_print(BIO_new_fp(stdout, BIO_NOCLOSE), not_after);
    printf("\n");

    /* Check if cert is expired */
    if (X509_cmp_current_time(not_after) < 0) {
        printf("[WARN] Certificate is EXPIRED!\n");
    }

    /* ── PUBLIC KEY INFO ─────────────────────────────────────── */
    pubkey   = X509_get_pubkey(cert);
    key_type = EVP_PKEY_base_id(pubkey);
    key_bits = EVP_PKEY_bits(pubkey);
    printf("[CERT] Key type: %s, bits: %d\n",
           key_type == EVP_PKEY_RSA  ? "RSA"   :
           key_type == EVP_PKEY_EC   ? "EC"    :
           key_type == EVP_PKEY_ED25519 ? "Ed25519" : "Unknown",
           key_bits);
    
    if (key_type == EVP_PKEY_RSA && key_bits < 2048) {
        printf("[WARN] RSA key too small (%d bits)!\n", key_bits);
    }
    EVP_PKEY_free(pubkey);

    /* ── SUBJECT ALTERNATIVE NAMES ──────────────────────────── */
    GENERAL_NAMES *sans = X509_get_ext_d2i(cert, NID_subject_alt_name, NULL, NULL);
    if (sans) {
        printf("[CERT] SANs:\n");
        for (int i = 0; i < sk_GENERAL_NAME_num(sans); i++) {
            GENERAL_NAME *san = sk_GENERAL_NAME_value(sans, i);
            if (san->type == GEN_DNS) {
                printf("         DNS: %s\n",
                       ASN1_STRING_get0_data(san->d.dNSName));
            } else if (san->type == GEN_IPADD) {
                unsigned char *ip = ASN1_STRING_data(san->d.iPAddress);
                printf("         IP:  %d.%d.%d.%d\n", ip[0],ip[1],ip[2],ip[3]);
            }
        }
        sk_GENERAL_NAME_pop_free(sans, GENERAL_NAME_free);
    }

    /* ── SERIAL NUMBER ──────────────────────────────────────── */
    BIGNUM *serial_bn = ASN1_INTEGER_to_BN(X509_get_serialNumber(cert), NULL);
    char *serial_hex  = BN_bn2hex(serial_bn);
    printf("[CERT] Serial:   %s\n", serial_hex);
    /* Very small serial (e.g., 0x01) is suspicious (self-signed/test) */
    if (BN_num_bits(serial_bn) < 64) {
        printf("[WARN] Unusually small serial number — possible test cert\n");
    }
    OPENSSL_free(serial_hex);
    BN_free(serial_bn);

    /* ── FINGERPRINT ─────────────────────────────────────────── */
    unsigned char fingerprint[EVP_MAX_MD_SIZE];
    unsigned int  fp_len;
    X509_digest(cert, EVP_sha256(), fingerprint, &fp_len);
    printf("[CERT] SHA256 fingerprint: ");
    for (unsigned int i = 0; i < fp_len; i++) {
        printf("%02X%s", fingerprint[i], i < fp_len-1 ? ":" : "\n");
    }

    /* ── HOSTNAME VERIFICATION ──────────────────────────────── */
    /* This is done automatically by OpenSSL if we set the hostname
     * in the SSL object. Shown here for clarity. */
    X509_VERIFY_PARAM *param = SSL_get0_param(ssl);
    X509_VERIFY_PARAM_set_hostflags(param, X509_CHECK_FLAG_NO_PARTIAL_WILDCARDS);
    X509_VERIFY_PARAM_set1_host(param, hostname, strlen(hostname));

    X509_free(cert);
}

/* ─────────────────────────────────────────────────────────────
 * TLS SESSION INFORMATION
 * Extract negotiated parameters after handshake
 * ──────────────────────────────────────────────────────────── */
static void print_tls_session_info(SSL *ssl) {
    const SSL_CIPHER *cipher;
    const char *version;
    
    version = SSL_get_version(ssl);
    cipher  = SSL_get_current_cipher(ssl);
    
    printf("[TLS] Version:      %s\n", version);
    printf("[TLS] Cipher:       %s\n", SSL_CIPHER_get_name(cipher));
    printf("[TLS] Cipher bits:  %d\n", SSL_CIPHER_get_bits(cipher, NULL));
    
    /* Check if session was resumed */
    if (SSL_session_reused(ssl)) {
        printf("[TLS] Session: RESUMED (from cache/ticket)\n");
    } else {
        printf("[TLS] Session: NEW (full handshake)\n");
    }
    
    /* ALPN negotiated */
    const unsigned char *alpn;
    unsigned int alpn_len;
    SSL_get0_alpn_selected(ssl, &alpn, &alpn_len);
    if (alpn_len > 0) {
        printf("[TLS] ALPN:         %.*s\n", alpn_len, alpn);
    }
    
    /* Export keying material (for debugging — DANGEROUS IN PRODUCTION) */
    /*
    unsigned char keying_material[32];
    SSL_export_keying_material(ssl, keying_material, sizeof(keying_material),
                               "EXPORTER-Channel-Binding", 24, NULL, 0, 0);
    printf("[TLS] Keying material: ");
    for (int i = 0; i < 32; i++) printf("%02x", keying_material[i]);
    printf("\n");
    */
}

/* ─────────────────────────────────────────────────────────────
 * TCP CONNECT
 * Raw socket connection before TLS handshake
 * ──────────────────────────────────────────────────────────── */
static int tcp_connect(const char *hostname, const char *port) {
    struct addrinfo hints = {0}, *res, *rp;
    int sockfd = -1;

    hints.ai_family   = AF_UNSPEC;   /* IPv4 or IPv6 */
    hints.ai_socktype = SOCK_STREAM;

    if (getaddrinfo(hostname, port, &hints, &res) != 0) {
        perror("getaddrinfo");
        return -1;
    }

    for (rp = res; rp != NULL; rp = rp->ai_next) {
        sockfd = socket(rp->ai_family, rp->ai_socktype, rp->ai_protocol);
        if (sockfd == -1) continue;
        if (connect(sockfd, rp->ai_addr, rp->ai_addrlen) == 0) break;
        close(sockfd);
        sockfd = -1;
    }

    freeaddrinfo(res);
    return sockfd;
}

/* ─────────────────────────────────────────────────────────────
 * MAIN TLS CLIENT
 * ──────────────────────────────────────────────────────────── */
int main(int argc, char *argv[]) {
    const char *hostname = argc > 1 ? argv[1] : "example.com";
    const char *port     = argc > 2 ? argv[2] : "443";
    SSL_CTX *ctx;
    SSL *ssl;
    int sockfd;
    int ret;
    char buf[4096];
    int  nread;

    /* Initialize OpenSSL (not needed in OpenSSL 1.1+, but harmless) */
    SSL_library_init();
    SSL_load_error_strings();
    OpenSSL_add_ssl_algorithms();

    /* Create context with security settings */
    ctx = create_client_context();

    /* TCP connection */
    sockfd = tcp_connect(hostname, port);
    if (sockfd < 0) {
        fprintf(stderr, "TCP connection failed\n");
        SSL_CTX_free(ctx);
        return EXIT_FAILURE;
    }
    printf("[TCP] Connected to %s:%s\n", hostname, port);

    /* Create SSL object and bind to socket */
    ssl = SSL_new(ctx);
    SSL_set_fd(ssl, sockfd);

    /* ── SNI EXTENSION ──────────────────────────────────────── */
    /* Set Server Name Indication — REQUIRED for virtual hosting */
    if (SSL_set_tlsext_host_name(ssl, hostname) != 1) {
        dump_ssl_errors("SSL_set_tlsext_host_name");
        goto cleanup;
    }

    /* ── HOSTNAME VERIFICATION ──────────────────────────────── */
    /* Tell OpenSSL which hostname to verify against cert */
    SSL_set_hostflags(ssl, X509_CHECK_FLAG_NO_PARTIAL_WILDCARDS);
    if (!SSL_set1_host(ssl, hostname)) {
        dump_ssl_errors("SSL_set1_host");
        goto cleanup;
    }

    /* ── TLS HANDSHAKE ──────────────────────────────────────── */
    printf("[TLS] Starting handshake...\n");
    ret = SSL_connect(ssl);
    if (ret != 1) {
        int err = SSL_get_error(ssl, ret);
        fprintf(stderr, "[TLS] Handshake failed: SSL error %d\n", err);
        dump_ssl_errors("SSL_connect");
        goto cleanup;
    }
    printf("[TLS] Handshake complete!\n");

    /* Print session information */
    print_tls_session_info(ssl);
    inspect_server_certificate(ssl, hostname);

    /* Verify certificate was actually validated */
    long verify_result = SSL_get_verify_result(ssl);
    if (verify_result != X509_V_OK) {
        fprintf(stderr, "[SECURITY] Certificate verification FAILED: %s\n",
                X509_verify_cert_error_string(verify_result));
        goto cleanup;
    }
    printf("[TLS] Certificate verified OK\n");

    /* ── SEND HTTP REQUEST ──────────────────────────────────── */
    const char *request_fmt = 
        "GET / HTTP/1.1\r\n"
        "Host: %s\r\n"
        "Connection: close\r\n"
        "User-Agent: TLSAnalysisClient/1.0\r\n"
        "\r\n";
    
    char request[512];
    snprintf(request, sizeof(request), request_fmt, hostname);
    
    if (SSL_write(ssl, request, strlen(request)) <= 0) {
        dump_ssl_errors("SSL_write");
        goto cleanup;
    }

    /* ── READ RESPONSE ──────────────────────────────────────── */
    printf("\n[RESPONSE]\n");
    while ((nread = SSL_read(ssl, buf, sizeof(buf) - 1)) > 0) {
        buf[nread] = '\0';
        printf("%s", buf);
    }
    
    /* Check for clean shutdown */
    if (nread == 0) {
        printf("\n[TLS] Connection closed cleanly\n");
    } else {
        int err = SSL_get_error(ssl, nread);
        if (err != SSL_ERROR_ZERO_RETURN) {
            dump_ssl_errors("SSL_read");
        }
    }

    /* ── TLS SHUTDOWN ───────────────────────────────────────── */
    /* Send close_notify alert */
    SSL_shutdown(ssl);
    /* Receive peer's close_notify (may timeout) */
    SSL_shutdown(ssl);

cleanup:
    SSL_free(ssl);
    close(sockfd);
    SSL_CTX_free(ctx);
    EVP_cleanup();
    return EXIT_SUCCESS;
}

/*
 * BUILD:
 *   gcc -o tls_client tls_client.c -lssl -lcrypto -Wall -Wextra
 *
 * USAGE:
 *   ./tls_client example.com 443
 *   ./tls_client api.github.com 443
 */
```

### 17.2 mTLS Server (C, OpenSSL)

```c
/* ============================================================
 * mTLS Server — Requires Client Certificate
 * Pattern used by APT C2 servers for implant authentication
 * ============================================================ */

#include <openssl/ssl.h>
#include <openssl/err.h>
#include <openssl/x509.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>

#define PORT 8443
#define BACKLOG 10

/* Custom certificate verification callback */
static int verify_client_certificate(int preverify_ok, X509_STORE_CTX *ctx) {
    X509 *cert = X509_STORE_CTX_get_current_cert(ctx);
    int  depth  = X509_STORE_CTX_get_error_depth(ctx);
    int  err    = X509_STORE_CTX_get_error(ctx);
    char subject[256];

    X509_NAME_oneline(X509_get_subject_name(cert), subject, sizeof(subject));
    printf("[mTLS] Verifying client cert (depth=%d): %s\n", depth, subject);

    if (!preverify_ok) {
        printf("[mTLS] Verification failed: %s\n",
               X509_verify_cert_error_string(err));
        return 0;  /* Reject connection */
    }

    /* Additional custom checks could go here:
     * - Check specific OID extensions
     * - Verify implant ID in cert subject
     * - Check revocation against internal list */

    return 1;  /* Accept */
}

static SSL_CTX *create_server_context(
    const char *cert_file,    /* Server certificate */
    const char *key_file,     /* Server private key */
    const char *ca_file       /* CA cert that signed client certs */
) {
    SSL_CTX *ctx = SSL_CTX_new(TLS_server_method());
    if (!ctx) { ERR_print_errors_fp(stderr); exit(1); }

    /* ── REQUIRE CLIENT CERTIFICATE ─────────────────────────── */
    /* This is the mTLS-defining line: */
    SSL_CTX_set_verify(ctx,
        SSL_VERIFY_PEER |                   /* Request client cert */
        SSL_VERIFY_FAIL_IF_NO_PEER_CERT,   /* Reject if not provided */
        verify_client_certificate);         /* Custom callback */

    /* ── LOAD CA FOR CLIENT CERT VERIFICATION ───────────────── */
    /* Only client certs signed by this CA will be accepted */
    if (!SSL_CTX_load_verify_locations(ctx, ca_file, NULL)) {
        ERR_print_errors_fp(stderr);
        exit(1);
    }

    /* ── LOAD SERVER CERTIFICATE AND KEY ────────────────────── */
    if (SSL_CTX_use_certificate_file(ctx, cert_file, SSL_FILETYPE_PEM) <= 0) {
        ERR_print_errors_fp(stderr);
        exit(1);
    }
    if (SSL_CTX_use_PrivateKey_file(ctx, key_file, SSL_FILETYPE_PEM) <= 0) {
        ERR_print_errors_fp(stderr);
        exit(1);
    }
    /* Verify key matches certificate */
    if (!SSL_CTX_check_private_key(ctx)) {
        fprintf(stderr, "Certificate and private key do not match\n");
        exit(1);
    }

    /* ── SECURITY OPTIONS ───────────────────────────────────── */
    SSL_CTX_set_min_proto_version(ctx, TLS1_2_VERSION);
    SSL_CTX_set_options(ctx, SSL_OP_NO_COMPRESSION | SSL_OP_NO_SSLv3);
    
    /* Prefer server cipher order over client */
    SSL_CTX_set_options(ctx, SSL_OP_CIPHER_SERVER_PREFERENCE);

    /* ── SESSION TICKETS ─────────────────────────────────────── */
    /* Disable for high-security C2 (each session must authenticate) */
    SSL_CTX_set_options(ctx, SSL_OP_NO_TICKET);

    return ctx;
}

/* Accept loop for mTLS server */
static void run_server(SSL_CTX *ctx) {
    struct sockaddr_in addr = {
        .sin_family = AF_INET,
        .sin_port   = htons(PORT),
        .sin_addr.s_addr = INADDR_ANY
    };
    
    int listenfd = socket(AF_INET, SOCK_STREAM, 0);
    setsockopt(listenfd, SOL_SOCKET, SO_REUSEADDR, &(int){1}, sizeof(int));
    bind(listenfd, (struct sockaddr*)&addr, sizeof(addr));
    listen(listenfd, BACKLOG);
    
    printf("[mTLS Server] Listening on port %d\n", PORT);

    while (1) {
        struct sockaddr_in client_addr;
        socklen_t client_len = sizeof(client_addr);
        int connfd = accept(listenfd, (struct sockaddr*)&client_addr, &client_len);
        
        printf("[mTLS] New connection from %s\n", inet_ntoa(client_addr.sin_addr));

        SSL *ssl = SSL_new(ctx);
        SSL_set_fd(ssl, connfd);

        int ret = SSL_accept(ssl);
        if (ret <= 0) {
            printf("[mTLS] Handshake failed (no valid client cert?)\n");
            ERR_print_errors_fp(stderr);
        } else {
            printf("[mTLS] Handshake SUCCESS — client authenticated!\n");
            
            /* Read implant command */
            char buf[1024];
            int n = SSL_read(ssl, buf, sizeof(buf)-1);
            if (n > 0) {
                buf[n] = '\0';
                printf("[mTLS] Received: %s\n", buf);
                /* Send command back */
                const char *cmd = "exec:whoami\n";
                SSL_write(ssl, cmd, strlen(cmd));
            }
        }

        SSL_shutdown(ssl);
        SSL_free(ssl);
        close(connfd);
    }
}

int main(void) {
    SSL_CTX *ctx = create_server_context(
        "server.crt",   /* Server cert */
        "server.key",   /* Server private key */
        "client_ca.crt" /* CA that signs implant certs */
    );
    run_server(ctx);
    SSL_CTX_free(ctx);
    return 0;
}

/*
 * GENERATE TEST CERTIFICATES:
 *   # CA key and cert
 *   openssl genrsa -out ca.key 4096
 *   openssl req -new -x509 -days 3650 -key ca.key -out ca.crt -subj "/CN=Operator CA"
 *
 *   # Server cert
 *   openssl genrsa -out server.key 4096
 *   openssl req -new -key server.key -out server.csr -subj "/CN=c2.internal"
 *   openssl x509 -req -days 365 -in server.csr -CA ca.crt -CAkey ca.key \
 *           -CAcreateserial -out server.crt
 *
 *   # Client (implant) cert
 *   openssl genrsa -out client.key 4096
 *   openssl req -new -key client.key -out client.csr -subj "/CN=implant-001"
 *   openssl x509 -req -days 365 -in client.csr -CA ca.crt -CAkey ca.key \
 *           -CAcreateserial -out client.crt
 *
 * BUILD:
 *   gcc -o mtls_server mtls_server.c -lssl -lcrypto
 */
```

### 17.3 TLS Handshake Parser (C — Raw Bytes)

```c
/* ============================================================
 * TLS Record and Handshake Parser
 * Parse TLS wire bytes from PCAP or network capture
 * ============================================================ */

#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <arpa/inet.h>

/* TLS ContentType values */
typedef enum {
    TLS_CHANGE_CIPHER_SPEC = 20,
    TLS_ALERT              = 21,
    TLS_HANDSHAKE          = 22,
    TLS_APPLICATION_DATA   = 23,
    TLS_HEARTBEAT          = 24
} tls_content_type_t;

/* TLS HandshakeType values */
typedef enum {
    TLS_HELLO_REQUEST        = 0,
    TLS_CLIENT_HELLO         = 1,
    TLS_SERVER_HELLO         = 2,
    TLS_NEW_SESSION_TICKET   = 4,
    TLS_END_OF_EARLY_DATA    = 5,
    TLS_ENCRYPTED_EXTENSIONS = 8,
    TLS_CERTIFICATE          = 11,
    TLS_SERVER_KEY_EXCHANGE  = 12,
    TLS_CERTIFICATE_REQUEST  = 13,
    TLS_SERVER_HELLO_DONE    = 14,
    TLS_CERTIFICATE_VERIFY   = 15,
    TLS_CLIENT_KEY_EXCHANGE  = 16,
    TLS_FINISHED             = 20,
    TLS_KEY_UPDATE           = 24,
    TLS_MESSAGE_HASH         = 254
} tls_handshake_type_t;

/* TLS Record header (5 bytes) */
typedef struct __attribute__((packed)) {
    uint8_t  content_type;      /* ContentType */
    uint16_t version;           /* Protocol version (big-endian) */
    uint16_t length;            /* Payload length (big-endian) */
} tls_record_header_t;

/* TLS Handshake header (4 bytes) */
typedef struct __attribute__((packed)) {
    uint8_t  type;              /* HandshakeType */
    uint8_t  length[3];         /* 3-byte big-endian length */
} tls_handshake_header_t;

/* Read 3-byte big-endian integer */
static uint32_t read_uint24_be(const uint8_t *p) {
    return ((uint32_t)p[0] << 16) | ((uint32_t)p[1] << 8) | p[2];
}

/* Parse TLS extension */
static int parse_extension(const uint8_t *data, size_t len) {
    if (len < 4) return -1;
    
    uint16_t ext_type   = ntohs(*(uint16_t*)data);
    uint16_t ext_len    = ntohs(*(uint16_t*)(data + 2));
    const uint8_t *ext_data = data + 4;
    
    printf("    Extension 0x%04x", ext_type);
    
    switch (ext_type) {
        case 0x0000: /* SNI */
            printf(" (SNI)");
            if (ext_len > 5) {
                uint16_t list_len = ntohs(*(uint16_t*)ext_data);
                uint8_t  name_type = ext_data[2];
                uint16_t name_len  = ntohs(*(uint16_t*)(ext_data + 3));
                if (name_type == 0 && name_len < ext_len) {
                    printf(" → hostname: %.*s", name_len, ext_data + 5);
                }
            }
            break;
        case 0x000A: printf(" (Supported Groups)"); break;
        case 0x000B: printf(" (EC Point Formats)"); break;
        case 0x000D: printf(" (Signature Algorithms)"); break;
        case 0x0010: /* ALPN */
            printf(" (ALPN)");
            if (ext_len > 3) {
                uint8_t proto_len = ext_data[2];
                printf(" → %.*s", proto_len, ext_data + 3);
            }
            break;
        case 0x0017: printf(" (Extended Master Secret)"); break;
        case 0x001B: printf(" (Compress Certificate)"); break;
        case 0x0023: printf(" (Session Ticket)"); break;
        case 0x0029: printf(" (Pre-Shared Key)"); break;
        case 0x002B: printf(" (Supported Versions)"); break;
        case 0x002D: printf(" (PSK Key Exchange Modes)"); break;
        case 0x0033: printf(" (Key Share)"); break;
        case 0x4469: printf(" (Token Binding)"); break;
        case 0xFF01: printf(" (Renegotiation Info)"); break;
        default:
            if ((ext_type & 0x0F0F) == 0x0A0A) {
                printf(" *** GREASE VALUE ***");
            }
            break;
    }
    printf(" [%u bytes]\n", ext_len);
    return 4 + ext_len;
}

/* Parse ClientHello message */
static void parse_client_hello(const uint8_t *data, size_t len) {
    if (len < 34) return;
    
    printf("  [ClientHello]\n");
    
    /* Client version */
    uint16_t client_version = ntohs(*(uint16_t*)data);
    printf("  Client Version: 0x%04x (%s)\n", client_version,
           client_version == 0x0303 ? "TLS 1.2/1.3" :
           client_version == 0x0302 ? "TLS 1.1" :
           client_version == 0x0301 ? "TLS 1.0" : "Unknown");
    
    /* Random (32 bytes) */
    printf("  Random: ");
    for (int i = 2; i < 34; i++) printf("%02x", data[i]);
    printf("\n");
    
    /* Session ID */
    uint8_t session_id_len = data[34];
    printf("  Session ID length: %u\n", session_id_len);
    size_t offset = 35 + session_id_len;
    
    /* Cipher suites */
    if (offset + 2 > len) return;
    uint16_t cs_len = ntohs(*(uint16_t*)(data + offset));
    printf("  Cipher Suites (%u bytes, %u suites):\n", cs_len, cs_len/2);
    offset += 2;
    for (uint16_t i = 0; i < cs_len; i += 2) {
        uint16_t cs = ntohs(*(uint16_t*)(data + offset + i));
        printf("    0x%04x", cs);
        if ((cs & 0x0F0F) == 0x0A0A) printf(" [GREASE]");
        else switch(cs) {
            case 0xC02B: printf(" TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256"); break;
            case 0xC02F: printf(" TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256");   break;
            case 0xC02C: printf(" TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384"); break;
            case 0xC030: printf(" TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384");   break;
            case 0xCCA9: printf(" TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305");  break;
            case 0xCCA8: printf(" TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305");    break;
            case 0x1301: printf(" TLS_AES_128_GCM_SHA256 [TLS1.3]");         break;
            case 0x1302: printf(" TLS_AES_256_GCM_SHA384 [TLS1.3]");         break;
            case 0x1303: printf(" TLS_CHACHA20_POLY1305_SHA256 [TLS1.3]");   break;
            case 0x0035: printf(" TLS_RSA_WITH_AES_256_CBC_SHA [WEAK]");     break;
            case 0x00FF: printf(" TLS_EMPTY_RENEGOTIATION_INFO_SCSV");       break;
        }
        printf("\n");
    }
    offset += cs_len;
    
    /* Compression methods */
    if (offset >= len) return;
    uint8_t comp_len = data[offset++];
    printf("  Compression methods: %u (", comp_len);
    for (uint8_t i = 0; i < comp_len; i++) {
        printf("%s%02x", i?",":"", data[offset+i]);
    }
    printf(")\n");
    offset += comp_len;
    
    /* Extensions */
    if (offset + 2 > len) return;
    uint16_t ext_total = ntohs(*(uint16_t*)(data + offset));
    offset += 2;
    printf("  Extensions (%u bytes):\n", ext_total);
    size_t ext_end = offset + ext_total;
    while (offset < ext_end && offset < len) {
        int consumed = parse_extension(data + offset, ext_end - offset);
        if (consumed <= 0) break;
        offset += consumed;
    }
}

/* Parse TLS Record */
void parse_tls_record(const uint8_t *data, size_t len) {
    if (len < 5) {
        printf("[!] Buffer too small for TLS record\n");
        return;
    }

    const tls_record_header_t *hdr = (const tls_record_header_t*)data;
    uint16_t rec_version = ntohs(hdr->version);
    uint16_t rec_length  = ntohs(hdr->length);

    printf("[TLS Record]\n");
    printf("  Content-Type: %u (%s)\n", hdr->content_type,
           hdr->content_type == TLS_HANDSHAKE         ? "Handshake"         :
           hdr->content_type == TLS_ALERT              ? "Alert"             :
           hdr->content_type == TLS_CHANGE_CIPHER_SPEC ? "ChangeCipherSpec"  :
           hdr->content_type == TLS_APPLICATION_DATA   ? "ApplicationData"   :
           hdr->content_type == TLS_HEARTBEAT          ? "Heartbeat"         : "Unknown");
    printf("  Version:      0x%04x\n", rec_version);
    printf("  Length:       %u bytes\n", rec_length);

    if (len < 5 + rec_length) {
        printf("[!] Truncated record\n");
        return;
    }

    if (hdr->content_type == TLS_HANDSHAKE) {
        const uint8_t *hs = data + 5;
        tls_handshake_type_t hs_type = (tls_handshake_type_t)hs[0];
        uint32_t hs_len = read_uint24_be(hs + 1);
        
        printf("  Handshake Type: %u (%s)\n", hs_type,
               hs_type == TLS_CLIENT_HELLO         ? "ClientHello"        :
               hs_type == TLS_SERVER_HELLO         ? "ServerHello"        :
               hs_type == TLS_CERTIFICATE          ? "Certificate"        :
               hs_type == TLS_SERVER_KEY_EXCHANGE  ? "ServerKeyExchange"  :
               hs_type == TLS_CLIENT_KEY_EXCHANGE  ? "ClientKeyExchange"  :
               hs_type == TLS_SERVER_HELLO_DONE    ? "ServerHelloDone"    :
               hs_type == TLS_FINISHED             ? "Finished"           :
               hs_type == TLS_NEW_SESSION_TICKET   ? "NewSessionTicket"   :
               hs_type == TLS_ENCRYPTED_EXTENSIONS ? "EncryptedExtensions": "Unknown");
        printf("  Handshake Len:  %u bytes\n", hs_len);

        if (hs_type == TLS_CLIENT_HELLO) {
            parse_client_hello(hs + 4, hs_len);
        }
    }
}

/* Example usage with raw bytes */
int main(void) {
    /* Example: TLS ClientHello bytes (abbreviated) */
    uint8_t sample[] = {
        /* TLS Record Header */
        0x16,           /* ContentType: Handshake */
        0x03, 0x01,     /* Version: TLS 1.0 (compat) */
        0x00, 0x30,     /* Length: 48 bytes */
        
        /* Handshake Header */
        0x01,           /* ClientHello */
        0x00, 0x00, 0x2c, /* Length: 44 bytes */
        
        /* ClientHello body */
        0x03, 0x03,     /* Client version: TLS 1.2 */
        /* 32 bytes random (truncated example) */
        0x11,0x22,0x33,0x44,0x55,0x66,0x77,0x88,
        0x11,0x22,0x33,0x44,0x55,0x66,0x77,0x88,
        0x11,0x22,0x33,0x44,0x55,0x66,0x77,0x88,
        0x11,0x22,0x33,0x44,0x55,0x66,0x77,0x88,
        /* Session ID length: 0 */
        0x00,
        /* Cipher suites length: 4, two suites */
        0x00, 0x04,
        0xC0, 0x2B,     /* TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256 */
        0x13, 0x01,     /* TLS_AES_128_GCM_SHA256 */
        /* Compression: 1 method, null */
        0x01, 0x00,
        /* No extensions (truncated) */
    };

    parse_tls_record(sample, sizeof(sample));
    return 0;
}
```

---

## 18. Rust Implementation — TLS from First Principles

### 18.1 TLS Client Using Rustls

```rust
//! ============================================================
//! TLS Client in Rust (rustls — pure Rust, no OpenSSL)
//! Elite RE Reference: understand the implementation model
//! ============================================================

use std::io::{Read, Write, BufReader};
use std::net::TcpStream;
use std::sync::Arc;
use std::fs::File;

// Rustls: pure Rust TLS implementation
// No OpenSSL dependency → different JA3 fingerprint
use rustls::{
    ClientConfig, ClientConnection, StreamOwned,
    RootCertStore, ServerName, OwnedTrustAnchor,
};
use rustls::client::{ServerCertVerifier, ServerCertVerified, WebPkiVerifier};
use rustls::Certificate as RustlsCert;

/// Custom certificate verifier (for analysis/research purposes)
/// In production: ALWAYS use proper verification!
struct InsecureVerifier;

impl ServerCertVerifier for InsecureVerifier {
    fn verify_server_cert(
        &self,
        end_entity: &RustlsCert,
        intermediates: &[RustlsCert],
        server_name: &ServerName,
        _scts: &mut dyn Iterator<Item = &[u8]>,
        _ocsp_response: &[u8],
        _now: std::time::SystemTime,
    ) -> Result<ServerCertVerified, rustls::Error> {
        // DANGEROUS: accepts any certificate
        // Used here to illustrate the verification bypass pattern
        // that malware implements
        eprintln!("[WARN] SKIPPING CERTIFICATE VERIFICATION");
        eprintln!("[WARN] Server: {:?}", server_name);
        eprintln!("[WARN] Cert len: {} bytes", end_entity.0.len());
        Ok(ServerCertVerified::assertion())
    }
}

/// Parse X.509 DER certificate and extract fields
/// Minimal ASN.1 parser — illustrates what OpenSSL does under the hood
fn parse_cert_der(der: &[u8]) {
    // ASN.1 DER structure for X.509:
    // SEQUENCE {          <- Certificate
    //   SEQUENCE {        <- TBSCertificate
    //     [0] INTEGER     <- version
    //     INTEGER         <- serialNumber
    //     SEQUENCE        <- signature AlgorithmIdentifier
    //     SEQUENCE        <- issuer Name
    //     SEQUENCE        <- validity
    //     ...
    //   }
    //   SEQUENCE          <- signatureAlgorithm
    //   BIT STRING        <- signature
    // }
    
    if der.len() < 4 {
        return;
    }
    
    // Verify DER starts with SEQUENCE tag (0x30)
    if der[0] != 0x30 {
        eprintln!("[CERT] Not a DER certificate (expected 0x30, got 0x{:02x})", der[0]);
        return;
    }
    
    // Parse length (could be short or long form)
    let (total_len, header_len) = if der[1] < 0x80 {
        (der[1] as usize, 2)
    } else {
        let num_bytes = (der[1] & 0x7F) as usize;
        let mut len = 0usize;
        for i in 0..num_bytes {
            len = (len << 8) | der[2 + i] as usize;
        }
        (len, 2 + num_bytes)
    };
    
    println!("[CERT] DER Certificate: {} bytes", total_len + header_len);
    
    // In a full parser, we'd walk the ASN.1 tree recursively
    // For now, search for known patterns:
    
    // RSA OID: 2a 86 48 86 f7 0d 01 01 01 (rsaEncryption)
    let rsa_oid = [0x2a, 0x86, 0x48, 0x86, 0xf7, 0x0d, 0x01, 0x01, 0x01];
    // ECDSA OID: 2a 86 48 ce 3d 02 01 (id-ecPublicKey)
    let ec_oid  = [0x2a, 0x86, 0x48, 0xce, 0x3d, 0x02, 0x01];
    
    let key_type = if der.windows(rsa_oid.len()).any(|w| w == rsa_oid) {
        "RSA"
    } else if der.windows(ec_oid.len()).any(|w| w == ec_oid) {
        "EC"
    } else {
        "Unknown"
    };
    
    println!("[CERT] Public key type: {}", key_type);
}

/// Compute JA3 fingerprint from ClientHello parameters
/// This is what network monitoring tools compute from PCAP
fn compute_ja3(
    tls_version: u16,
    cipher_suites: &[u16],
    extensions: &[u16],
    elliptic_curves: &[u16],
    ec_point_formats: &[u8],
) -> String {
    // Filter GREASE values
    let is_grease = |v: u16| (v & 0x0F0F) == 0x0A0A;
    
    let ciphers: Vec<String> = cipher_suites.iter()
        .filter(|&&c| !is_grease(c))
        .map(|c| c.to_string())
        .collect();
    
    let exts: Vec<String> = extensions.iter()
        .filter(|&&e| !is_grease(e))
        .map(|e| e.to_string())
        .collect();
    
    let curves: Vec<String> = elliptic_curves.iter()
        .filter(|&&g| !is_grease(g))
        .map(|g| g.to_string())
        .collect();
    
    let formats: Vec<String> = ec_point_formats.iter()
        .map(|f| f.to_string())
        .collect();
    
    let ja3_str = format!("{},{},{},{},{}",
        tls_version,
        ciphers.join("-"),
        exts.join("-"),
        curves.join("-"),
        formats.join("-"),
    );
    
    println!("[JA3] Input string: {}", ja3_str);
    
    // MD5 hash
    let digest = md5::compute(ja3_str.as_bytes());
    format!("{:x}", digest)
}

/// Create TLS configuration with full verification (production-safe)
fn create_secure_config() -> Arc<ClientConfig> {
    // Build root certificate store from system trust anchors
    let mut root_store = RootCertStore::empty();
    
    // Add system trust anchors (webpki-roots crate)
    root_store.add_trust_anchors(
        webpki_roots::TLS_SERVER_ROOTS
            .iter()
            .map(|ta| OwnedTrustAnchor::from_subject_spki_name_constraints(
                ta.subject,
                ta.spki,
                ta.name_constraints,
            ))
    );
    
    // Configure cipher suites (TLS 1.3 by default in rustls)
    // rustls supports only safe suites — no RC4, no CBC, no export
    let config = ClientConfig::builder()
        .with_safe_defaults()          // TLS 1.2+, AEAD only
        .with_root_certificates(root_store)
        .with_no_client_auth();        // No mTLS (client-side)
    
    Arc::new(config)
}

/// Create insecure TLS config (for research/analysis of malware behavior)
fn create_insecure_config() -> Arc<ClientConfig> {
    let config = ClientConfig::builder()
        .with_safe_defaults()
        .with_custom_certificate_verifier(Arc::new(InsecureVerifier))
        .with_no_client_auth();
    
    Arc::new(config)
}

/// TLS connection wrapper with analysis output
struct TlsConnection {
    stream: StreamOwned<ClientConnection, TcpStream>,
    hostname: String,
}

impl TlsConnection {
    fn connect(hostname: &str, port: u16, config: Arc<ClientConfig>) 
        -> Result<Self, Box<dyn std::error::Error>> 
    {
        // TCP connection
        let addr = format!("{}:{}", hostname, port);
        println!("[TCP] Connecting to {}", addr);
        let tcp = TcpStream::connect(&addr)?;
        tcp.set_nodelay(true)?;
        println!("[TCP] Connected");
        
        // Parse server name for SNI
        let server_name = ServerName::try_from(hostname)
            .map_err(|_| "Invalid hostname")?
            .to_owned();
        
        // Create TLS connection (handshake not started yet)
        let conn = ClientConnection::new(config, server_name)?;
        
        // Wrap TCP stream with TLS — handshake happens on first read/write
        let mut tls_stream = StreamOwned::new(conn, tcp);
        
        // Force handshake by flushing (no-op write triggers it)
        tls_stream.flush()?;
        println!("[TLS] Handshake complete");
        
        // Print negotiated parameters
        let handshake_data = tls_stream.conn.peer_certificates();
        if let Some(certs) = handshake_data {
            println!("[TLS] Peer presented {} certificates", certs.len());
            for (i, cert) in certs.iter().enumerate() {
                println!("[TLS] Certificate {}: {} bytes (DER)", i, cert.0.len());
                parse_cert_der(&cert.0);
            }
        }
        
        // Negotiated protocol version
        if let Some(proto_version) = tls_stream.conn.protocol_version() {
            println!("[TLS] Negotiated version: {:?}", proto_version);
        }
        
        // ALPN
        if let Some(alpn) = tls_stream.conn.alpn_protocol() {
            println!("[TLS] ALPN: {:?}", String::from_utf8_lossy(alpn));
        }
        
        Ok(TlsConnection {
            stream: tls_stream,
            hostname: hostname.to_string(),
        })
    }
    
    fn send_http_request(&mut self) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
        let request = format!(
            "GET / HTTP/1.1\r\nHost: {}\r\nConnection: close\r\nUser-Agent: RustTLSClient/1.0\r\n\r\n",
            self.hostname
        );
        
        self.stream.write_all(request.as_bytes())?;
        self.stream.flush()?;
        println!("[HTTP] Sent request ({} bytes)", request.len());
        
        let mut response = Vec::new();
        self.stream.read_to_end(&mut response)?;
        println!("[HTTP] Received {} bytes", response.len());
        
        Ok(response)
    }
}

/// HKDF implementation (TLS 1.3 key derivation)
/// Understanding this is critical for analyzing TLS 1.3 key material
mod hkdf_demo {
    use hmac::{Hmac, Mac};
    use sha2::Sha256;
    
    type HmacSha256 = Hmac<Sha256>;
    
    /// HKDF-Extract: HMAC(salt, IKM)
    pub fn hkdf_extract(salt: &[u8], ikm: &[u8]) -> Vec<u8> {
        let mut mac = HmacSha256::new_from_slice(salt)
            .expect("HMAC accepts any key length");
        mac.update(ikm);
        mac.finalize().into_bytes().to_vec()
    }
    
    /// HKDF-Expand: expand PRK to `length` bytes
    pub fn hkdf_expand(prk: &[u8], info: &[u8], length: usize) -> Vec<u8> {
        let mut output = Vec::with_capacity(length);
        let mut t = Vec::new();
        let mut counter = 1u8;
        
        while output.len() < length {
            let mut mac = HmacSha256::new_from_slice(prk)
                .expect("HMAC accepts any key length");
            mac.update(&t);
            mac.update(info);
            mac.update(&[counter]);
            t = mac.finalize().into_bytes().to_vec();
            output.extend_from_slice(&t);
            counter += 1;
        }
        
        output.truncate(length);
        output
    }
    
    /// HKDF-Expand-Label (TLS 1.3 specific)
    pub fn hkdf_expand_label(
        secret: &[u8],
        label: &str,
        context: &[u8],
        length: usize,
    ) -> Vec<u8> {
        // HkdfLabel = uint16(length) || uint8(len("tls13 " + label))
        //             || "tls13 " || label || uint8(len(context)) || context
        let full_label = format!("tls13 {}", label);
        let mut hkdf_label = Vec::new();
        
        // uint16 length (big-endian)
        hkdf_label.push((length >> 8) as u8);
        hkdf_label.push(length as u8);
        
        // uint8 label length
        hkdf_label.push(full_label.len() as u8);
        
        // label bytes
        hkdf_label.extend_from_slice(full_label.as_bytes());
        
        // uint8 context length
        hkdf_label.push(context.len() as u8);
        
        // context bytes
        hkdf_label.extend_from_slice(context);
        
        hkdf_expand(secret, &hkdf_label, length)
    }
    
    /// Derive-Secret (TLS 1.3 key schedule step)
    pub fn derive_secret(secret: &[u8], label: &str, transcript_hash: &[u8]) -> Vec<u8> {
        hkdf_expand_label(secret, label, transcript_hash, 32) // SHA-256 output = 32 bytes
    }
    
    /// Demonstrate TLS 1.3 early key schedule (simplified, no real DHE)
    pub fn demo_key_schedule() {
        println!("\n[TLS 1.3 Key Schedule Demo]");
        
        let zeros = [0u8; 32];
        let fake_psk = zeros; // No PSK → zeros
        let fake_dhe = [0xAB; 32]; // Fake DHE shared secret
        let fake_transcript_hash = [0xCD; 32]; // Fake hash of ClientHello..ServerHello
        
        // Early Secret = HKDF-Extract(0, PSK)
        let early_secret = hkdf_extract(&zeros, &fake_psk);
        println!("Early Secret: {}", hex_encode(&early_secret));
        
        // Derive Salt for Handshake Secret
        let derived_secret = derive_secret(&early_secret, "derived", &zeros);
        
        // Handshake Secret = HKDF-Extract(derived, DHE)
        let handshake_secret = hkdf_extract(&derived_secret, &fake_dhe);
        println!("Handshake Secret: {}", hex_encode(&handshake_secret));
        
        // Client handshake traffic secret
        let client_hs_traffic = derive_secret(
            &handshake_secret, "c hs traffic", &fake_transcript_hash
        );
        println!("Client HS Traffic: {}", hex_encode(&client_hs_traffic));
        
        // Derive actual encryption key from traffic secret
        let client_write_key = hkdf_expand_label(
            &client_hs_traffic, "key", &[], 16 // AES-128 = 16 bytes
        );
        let client_write_iv = hkdf_expand_label(
            &client_hs_traffic, "iv", &[], 12  // GCM IV = 12 bytes
        );
        
        println!("Client Write Key: {}", hex_encode(&client_write_key));
        println!("Client Write IV:  {}", hex_encode(&client_write_iv));
    }
    
    fn hex_encode(bytes: &[u8]) -> String {
        bytes.iter().map(|b| format!("{:02x}", b)).collect()
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("=== Rust TLS Analysis Client ===\n");
    
    // Demonstrate key schedule
    hkdf_demo::demo_key_schedule();
    
    println!("\n=== TLS Connection ===\n");
    
    // Connect with secure config
    let config = create_secure_config();
    let mut conn = TlsConnection::connect("example.com", 443, config)?;
    
    // Send HTTP request
    let response = conn.send_http_request()?;
    println!("\n[Response preview]\n{}",
             String::from_utf8_lossy(&response[..std::cmp::min(500, response.len())]));
    
    // Demonstrate JA3 computation
    println!("\n=== JA3 Fingerprint Demo ===\n");
    // These would be extracted from actual ClientHello in real usage
    let ja3 = compute_ja3(
        769,  // TLS 1.0 version field (backward compat)
        &[0xC02B, 0xC02F, 0xCCA9, 0xCCA8, 0x1301, 0x1302, 0x1303],
        &[0x0000, 0x0017, 0xFF01, 0x000A, 0x000B, 0x0023, 0x0010, 0x0005, 0x002B, 0x0033],
        &[0x001d, 0x0017, 0x0018],
        &[0x00],
    );
    println!("[JA3] Fingerprint: {}", ja3);
    
    Ok(())
}

// Cargo.toml dependencies needed:
// [dependencies]
// rustls = { version = "0.21", features = ["dangerous_configuration"] }
// rustls-pemfile = "1.0"
// webpki-roots = "0.25"
// hmac = "0.12"
// sha2 = "0.10"
// md5 = "0.7"
```

### 18.2 Rust mTLS Client (Implant Pattern)

```rust
//! ============================================================
//! mTLS Client in Rust — Pattern used by modern implants
//! e.g., BlackCat/ALPHV Rust ransomware, Sliver framework
//! ============================================================

use std::sync::Arc;
use std::io::{Read, Write};
use std::net::TcpStream;
use rustls::{
    ClientConfig, ClientConnection, StreamOwned,
    Certificate, PrivateKey,
};
use rustls::client::ServerCertVerifier;

/// Load PEM certificate from bytes (embedded in binary)
fn load_cert_from_bytes(pem_bytes: &[u8]) -> Vec<Certificate> {
    let mut reader = std::io::BufReader::new(pem_bytes);
    rustls_pemfile::certs(&mut reader)
        .expect("Failed to parse certificate")
        .into_iter()
        .map(Certificate)
        .collect()
}

/// Load PEM private key from bytes (embedded in binary)  
fn load_key_from_bytes(pem_bytes: &[u8]) -> PrivateKey {
    let mut reader = std::io::BufReader::new(pem_bytes);
    
    // Try PKCS#8 first, then RSA format
    let keys = rustls_pemfile::pkcs8_private_keys(&mut reader)
        .expect("Failed to parse private key");
    
    if let Some(key) = keys.into_iter().next() {
        return PrivateKey(key);
    }
    
    // Reset and try RSA PKCS#1
    let mut reader = std::io::BufReader::new(pem_bytes);
    let rsa_keys = rustls_pemfile::rsa_private_keys(&mut reader)
        .expect("Failed to parse RSA key");
    
    PrivateKey(rsa_keys.into_iter().next().expect("No private key found"))
}

/// Custom verifier: only accept certs signed by our embedded CA
/// This is how APT implants authenticate their C2 server
struct PinnedCaVerifier {
    /// SHA-256 fingerprint of acceptable server certs (or CA cert)
    expected_fingerprint: [u8; 32],
}

impl ServerCertVerifier for PinnedCaVerifier {
    fn verify_server_cert(
        &self,
        end_entity: &Certificate,
        _intermediates: &[Certificate],
        _server_name: &rustls::ServerName,
        _scts: &mut dyn Iterator<Item = &[u8]>,
        _ocsp_response: &[u8],
        _now: std::time::SystemTime,
    ) -> Result<rustls::client::ServerCertVerified, rustls::Error> {
        // Compute SHA-256 fingerprint of server certificate DER
        use sha2::{Sha256, Digest};
        let mut hasher = Sha256::new();
        hasher.update(&end_entity.0);
        let fingerprint: [u8; 32] = hasher.finalize().into();
        
        if fingerprint == self.expected_fingerprint {
            Ok(rustls::client::ServerCertVerified::assertion())
        } else {
            // Certificate doesn't match our pin — reject
            Err(rustls::Error::General("Certificate pinning failed".into()))
        }
    }
}

/// APT-style implant TLS config: mTLS + certificate pinning
fn create_implant_config(
    // Client certificate (implant identity, signed by operator CA)
    client_cert_pem: &[u8],
    // Client private key (embedded in implant)
    client_key_pem: &[u8],
    // Expected server certificate fingerprint (hardcoded in implant)
    server_fingerprint: [u8; 32],
) -> Arc<ClientConfig> {
    let client_certs = load_cert_from_bytes(client_cert_pem);
    let client_key   = load_key_from_bytes(client_key_pem);
    
    // NOTE: In a real implant, these bytes would be:
    // 1. Embedded as static bytes (detectable by string/binary analysis)
    // 2. XOR-encrypted in binary (deobfuscate at runtime)
    // 3. Derived from hardware fingerprint (anti-analysis)
    
    let config = ClientConfig::builder()
        .with_safe_defaults()
        .with_custom_certificate_verifier(
            Arc::new(PinnedCaVerifier { expected_fingerprint: server_fingerprint })
        )
        .with_client_auth_cert(client_certs, client_key)
        .expect("Invalid client certificate or key");
    
    Arc::new(config)
}

/// Beacon loop — connects to C2 and awaits commands
fn run_beacon(c2_host: &str, c2_port: u16, config: Arc<ClientConfig>) {
    use std::time::Duration;
    
    let beacon_interval = Duration::from_secs(30);
    let jitter_max = 15u64; // ±15 seconds jitter
    
    loop {
        // Jitter calculation: sleep_time = base ± rand(jitter)
        let jitter = {
            use std::time::{SystemTime, UNIX_EPOCH};
            let t = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().subsec_nanos();
            (t as u64 % (2 * jitter_max)) as i64 - jitter_max as i64
        };
        let sleep_secs = (30i64 + jitter).max(5) as u64;
        
        eprintln!("[BEACON] Sleeping {}s (jitter {}s)", sleep_secs, jitter);
        std::thread::sleep(Duration::from_secs(sleep_secs));
        
        // Attempt C2 connection
        match attempt_c2_connection(c2_host, c2_port, Arc::clone(&config)) {
            Ok(command) => {
                eprintln!("[BEACON] Received command: {:?}", command);
                // Execute command... (omitted for obvious reasons)
            }
            Err(e) => {
                eprintln!("[BEACON] Connection failed: {}", e);
                // Exponential backoff or domain failover would go here
            }
        }
    }
}

fn attempt_c2_connection(
    host: &str, port: u16, config: Arc<ClientConfig>
) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    let tcp = TcpStream::connect(format!("{}:{}", host, port))?;
    tcp.set_read_timeout(Some(std::time::Duration::from_secs(30)))?;
    
    let server_name = rustls::ServerName::try_from(host)?.to_owned();
    let conn = ClientConnection::new(config, server_name)?;
    let mut tls = StreamOwned::new(conn, tcp);
    
    // Send beacon (implant ID + basic system info)
    let beacon_data = b"BEACON\x00\x01\x00\x00";  // Simplified
    tls.write_all(beacon_data)?;
    tls.flush()?;
    
    // Read command
    let mut response = vec![0u8; 4096];
    let n = tls.read(&mut response)?;
    response.truncate(n);
    
    Ok(response)
}
```

---

## 19. Memory Forensics of TLS Sessions

### 19.1 Finding TLS Key Material in Memory Dumps

```
Memory Forensics: TLS Key Extraction
======================================

SCENARIO: You have a memory dump from a running malware process.
GOAL: Extract TLS session keys to decrypt captured traffic.

TOOL CHAIN: Volatility3 + Wireshark

STEP 1: Identify TLS process
  vol.py -f malware.vmem windows.pslist | grep -E "malware|chrome|firefox"
  vol.py -f malware.vmem windows.dlllist --pid <PID> | grep ssl

STEP 2: Dump process memory
  vol.py -f malware.vmem windows.memmap --pid <PID> --dump
  # Output: pid.<PID>.dmp

STEP 3: Search for TLS master secret pattern
  # Master secret is always 48 bytes
  # Preceded by "CLIENT_RANDOM" label in SSLKEYLOGFILE format
  # Or found in SSL_SESSION structure

  OpenSSL SSL_SESSION structure offsets (OpenSSL 1.1.x, 64-bit):
    +0x00: type (int)
    +0x08: ssl_version (int)
    +0x10: master_key_length (size_t) = 48
    +0x18: master_key[48]             ← 48 bytes of key material
    +0x48: session_id_length
    +0x4C: session_id[32]
    ...

STEP 4: Pattern scan for master secrets
  # Python script to search for SSL_SESSION-like structures:
  
  import struct
  with open("pid.dump", "rb") as f:
      data = f.read()
  
  # Search for ssl_version = 0x0303 (TLS 1.2) or 0x0304 (TLS 1.3)
  # followed by master_key_length = 0x30 (48)
  for i in range(0, len(data)-60, 4):
      if data[i:i+4] in (b'\x03\x03\x00\x00', b'\x03\x04\x00\x00'):
          if data[i+8:i+16] == b'\x30' + b'\x00'*7:  # length = 48
              master_key = data[i+16:i+64]
              print(f"Potential master_key at offset {hex(i+16)}:")
              print(f"  {master_key.hex()}")

STEP 5: Extract ClientHello random from PCAP
  tshark -r capture.pcap -Y "tls.handshake.type == 1" \
         -T fields -e tls.handshake.random
  
  # Output: 32-byte random per ClientHello

STEP 6: Build SSLKEYLOGFILE
  # Format: CLIENT_RANDOM <client_random_hex> <master_secret_hex>
  echo "CLIENT_RANDOM <32-byte-hex> <48-byte-hex>" > keylogfile.txt

STEP 7: Decrypt in Wireshark
  Edit → Preferences → Protocols → TLS
  (Pre)-Master-Secret log filename: keylogfile.txt
  → Wireshark decrypts TLS sessions in capture!
```

### 19.2 Volatility3 TLS Analysis Plugins

```python
# ============================================================
# Custom Volatility3 Plugin: Find OpenSSL SSL_SESSION Structures
# ============================================================

import struct
from volatility3.framework import interfaces, renderers
from volatility3.framework.configuration import requirements
from volatility3.plugins.windows import pslist, memmap

class FindSSLSessions(interfaces.plugins.PluginInterface):
    """Find OpenSSL SSL_SESSION structures in process memory"""
    
    _required_framework_version = (2, 0, 0)
    
    @classmethod
    def get_requirements(cls):
        return [
            requirements.TranslationLayerRequirement(name='primary'),
            requirements.SymbolTableRequirement(name='nt_symbols'),
            requirements.IntRequirement(name='pid', optional=True),
        ]
    
    def run(self):
        kernel = self.context.modules[self.config['nt_symbols']]
        filter_pid = self.config.get('pid', None)
        
        sessions_found = []
        
        # Iterate processes
        for proc in pslist.PsList.list_processes(
            context=self.context,
            layer_name=self.config['primary'],
            symbol_table=self.config['nt_symbols']
        ):
            pid = proc.UniqueProcessId
            if filter_pid and pid != filter_pid:
                continue
            
            proc_name = proc.ImageFileName.cast('string',
                max_length=15, errors='replace')
            
            # Scan process memory for SSL_SESSION signatures
            try:
                proc_layer_name = proc.add_process_layer()
                proc_layer = self.context.layers[proc_layer_name]
                
                # Scan for TLS version markers + master_key_length = 48
                # This is a heuristic — needs tuning per OpenSSL version
                for offset, data in proc_layer.read_chunks(0, proc_layer.maximum_address):
                    if len(data) < 100:
                        continue
                    
                    for i in range(0, len(data) - 80, 8):
                        # Check ssl_version field
                        version = struct.unpack_from('<I', data, i)[0]
                        if version not in (0x0303, 0x0302, 0x0301, 0x0304):
                            continue
                        
                        # Check master_key_length = 48 at +8
                        mklen = struct.unpack_from('<Q', data, i+8)[0]
                        if mklen != 48:
                            continue
                        
                        # Extract master_key at +16
                        master_key = data[i+16:i+64]
                        
                        # Entropy check: key material should be high entropy
                        entropy = calculate_entropy(master_key)
                        if entropy < 6.5:  # Random data ≈ 8.0 bits/byte
                            continue
                        
                        sessions_found.append({
                            'pid': pid,
                            'process': proc_name,
                            'offset': offset + i,
                            'ssl_version': f'0x{version:04x}',
                            'master_key': master_key.hex(),
                            'entropy': f'{entropy:.2f}',
                        })
            except Exception as e:
                pass
        
        return renderers.TreeGrid(
            [('PID', int), ('Process', str), ('Offset', str),
             ('Version', str), ('MasterKey', str), ('Entropy', str)],
            self._generator(sessions_found)
        )
    
    def _generator(self, sessions):
        for s in sessions:
            yield (0, [s['pid'], s['process'], hex(s['offset']),
                       s['ssl_version'], s['master_key'], s['entropy']])

def calculate_entropy(data: bytes) -> float:
    """Shannon entropy calculation"""
    from collections import Counter
    import math
    if not data:
        return 0.0
    counts = Counter(data)
    total = len(data)
    return -sum((c/total) * math.log2(c/total) for c in counts.values())
```

---

## 20. YARA Rules for TLS-Related Malware Detection

```yara
// ============================================================
// YARA Rules: TLS Malware Detection
// ============================================================

// ─────────────────────────────────────────────────────────────
// RULE 1: Certificate Validation Disabled (OpenSSL)
// Detects malware that explicitly bypasses cert verification
// ─────────────────────────────────────────────────────────────
rule TLS_OpenSSL_Verify_None {
    meta:
        description     = "Detects SSL_VERIFY_NONE usage in malware"
        author          = "Threat Intel Team"
        mitre_att       = "T1071.001"
        confidence      = "HIGH"
        last_modified   = "2024-01-01"
    
    strings:
        // "SSL_VERIFY_NONE" string (argument to SSL_CTX_set_verify)
        $ssl_verify_none = "SSL_VERIFY_NONE" ascii wide
        
        // OpenSSL API calls that configure verification
        $set_verify      = "SSL_CTX_set_verify" ascii
        $ssl_connect     = "SSL_connect" ascii
        
        // Common in Python malware
        $insecure_py1    = "verify=False" ascii
        $insecure_py2    = "CERT_NONE" ascii
        
        // Go malware pattern
        $insecure_go     = "InsecureSkipVerify" ascii
        
        // .NET/C# pattern
        $insecure_cs     = "ServerCertificateValidationCallback" ascii
        $insecure_cs2    = "RemoteCertificateValidationCallback" ascii
        
        // Rust pattern
        $insecure_rust   = "danger_accept_invalid_certs" ascii
    
    condition:
        uint16(0) == 0x5A4D  // PE file
        and filesize < 50MB
        and (
            ($ssl_verify_none and $ssl_connect) or
            $insecure_py1 or $insecure_py2 or
            $insecure_go or
            ($insecure_cs and $ssl_connect) or
            $insecure_rust
        )
}

// ─────────────────────────────────────────────────────────────
// RULE 2: Embedded X.509 Certificate (DER format)
// Malware with hardcoded C2 certificate for mTLS
// ─────────────────────────────────────────────────────────────
rule TLS_Embedded_DER_Certificate {
    meta:
        description  = "Binary contains embedded DER X.509 certificate"
        author       = "Threat Intel Team"
        mitre_att    = "T1587.003"
        confidence   = "MEDIUM"
    
    strings:
        // X.509 Certificate DER magic: SEQUENCE of SEQUENCE
        // 30 82 = SEQUENCE, long form, 2-byte length
        // Followed by SEQUENCE of Version/SerialNumber
        $der_cert_start = { 30 82 ?? ?? 30 82 ?? ?? }
        
        // PEM-encoded certificate in binary
        $pem_begin   = "-----BEGIN CERTIFICATE-----" ascii
        $pem_end     = "-----END CERTIFICATE-----" ascii
        
        // PEM private key (VERY suspicious in most contexts)
        $pem_key     = "-----BEGIN RSA PRIVATE KEY-----" ascii
        $pem_key2    = "-----BEGIN PRIVATE KEY-----" ascii
        $pem_key3    = "-----BEGIN EC PRIVATE KEY-----" ascii
        
        // PKCS#12 magic (bundled cert + key)
        $p12_magic   = { 30 82 ?? ?? 02 01 03 }
    
    condition:
        (
            $der_cert_start or
            ($pem_begin and $pem_end) or
            $pem_key or $pem_key2 or $pem_key3 or
            $p12_magic
        )
        and uint16(0) == 0x5A4D  // PE file
        // Exclude legitimate certificate stores and crypto libraries
        and not pe.imports("crypt32.dll", "CertOpenStore")
}

// ─────────────────────────────────────────────────────────────
// RULE 3: OpenSSL Statically Linked (stripped binary)
// Detects malware that statically links OpenSSL
// ─────────────────────────────────────────────────────────────
rule TLS_StaticOpenSSL_Linked {
    meta:
        description = "Binary with statically linked OpenSSL"
        author      = "Threat Intel Team"
        confidence  = "MEDIUM"
    
    strings:
        // OpenSSL internal strings (present even in stripped binaries)
        $ossl_ver1   = "OpenSSL 1.0" ascii
        $ossl_ver2   = "OpenSSL 1.1" ascii
        $ossl_ver3   = "OpenSSL 3.0" ascii
        $ossl_ver4   = "OpenSSL 3.1" ascii
        
        // Error strings from OpenSSL
        $ossl_err1   = "ssl/ssl_lib.c" ascii
        $ossl_err2   = "ssl/record/ssl3_record.c" ascii
        $ossl_err3   = "ssl/statem/statem.c" ascii
        
        // OpenSSL internal function names (often present in debug builds)
        $ossl_fn1    = "SSL_CTX_new" ascii
        $ossl_fn2    = "TLS_client_method" ascii
        $ossl_fn3    = "OPENSSL_init_ssl" ascii
        
        // AES S-Box (present in any AES implementation)
        $aes_sbox    = { 63 7C 77 7B F2 6B 6F C5 30 01 67 2B FE D7 AB 76 }
        
        // SHA-256 initial hash values (H0-H3)
        $sha256_h    = { 67 E6 09 6A 85 AE 67 BB 72 F3 6E 3C 3A F5 4F A5 }
    
    condition:
        uint16(0) == 0x5A4D
        and filesize > 500KB  // Static linking adds size
        and (
            ($ossl_ver1 or $ossl_ver2 or $ossl_ver3 or $ossl_ver4) or
            (2 of ($ossl_err*)) or
            ($aes_sbox and $sha256_h and 1 of ($ossl_fn*))
        )
        // Not importing SSL DLLs (static = no DLL imports)
        and not pe.imports("ssleay32.dll")
        and not pe.imports("libssl-1_1.dll")
}

// ─────────────────────────────────────────────────────────────
// RULE 4: Cobalt Strike Beacon TLS Configuration
// ─────────────────────────────────────────────────────────────
rule CobaltStrike_Beacon_TLS_Config {
    meta:
        description = "Cobalt Strike Beacon with TLS C2 configuration"
        author      = "Threat Intel Team"
        mitre_att   = "T1071.001, T1219"
        confidence  = "HIGH"
        reference   = "https://www.cobaltstrike.com/help-malleable-c2"
    
    strings:
        // CS Beacon configuration magic bytes
        $cs_config_magic = { 00 00 BE EF }
        
        // CS Beacon null/XOR key patterns
        $cs_xor_key      = { 69 68 69 68 69 68 }  // Common XOR pattern
        
        // Typical CS configuration settings (often XOR'd with key)
        // "https://" XOR'd with 0x69: { 01 08 09 01 08 58 58 }
        $cs_https_xor    = { 01 08 09 01 08 58 58 }
        
        // CS MZ header (beacon shellcode)
        $cs_shellcode    = { FC 48 83 E4 F0 E8 }  // Common CS shellcode start
        
        // CS stager URL patterns
        $cs_stager       = "/jquery-3." ascii
        $cs_stager2      = "/updates.rss" ascii
        $cs_stager3      = "/load" ascii
        
        // CS default TLS port indicators (in beacon config)
        $cs_port_443     = { 00 BB 01 }  // Port 443 big-endian
        $cs_port_8443    = { 20 FB 01 }  // Port 8443 big-endian
        
        // CS WaterMark (trial version)
        $cs_watermark    = { 00 00 00 01 }
    
    condition:
        uint16(0) == 0x5A4D
        and (
            ($cs_config_magic and 2 of ($cs_port_443, $cs_port_8443, $cs_stager, $cs_stager2, $cs_stager3)) or
            ($cs_shellcode and 1 of ($cs_stager, $cs_stager2)) or
            ($cs_https_xor and $cs_config_magic)
        )
}

// ─────────────────────────────────────────────────────────────
// RULE 5: Rust Ransomware with TLS C2 (BlackCat/ALPHV pattern)
// ─────────────────────────────────────────────────────────────
rule Rust_Ransomware_TLS_C2 {
    meta:
        description = "Rust-compiled ransomware with TLS C2 (BlackCat/ALPHV pattern)"
        author      = "Threat Intel Team"
        mitre_att   = "T1486, T1071.001"
        confidence  = "MEDIUM"
        family      = "ALPHV/BlackCat"
    
    strings:
        // Rust runtime strings (always present in Rust binaries)
        $rust_panic      = "panicked at" ascii
        $rust_runtime    = "rust_begin_unwind" ascii
        $rust_alloc      = "__rust_alloc" ascii
        
        // Rustls library strings
        $rustls1         = "rustls" ascii
        $rustls2         = "TLS 1.3 not supported" ascii
        $rustls3         = "handshake failed" ascii  // rustls error msg
        
        // Tor/onion addresses for C2 (ransomware pattern)
        $onion_addr      = /[a-z2-7]{56}\.onion/ ascii
        $onion_addr2     = /[a-z2-7]{16}\.onion/ ascii
        
        // Encryption-related strings
        $chacha20        = "chacha20" ascii nocase
        $aes_gcm         = "aes-256-gcm" ascii nocase
        
        // File enumeration patterns
        $walkdir         = "walkdir" ascii  // Rust crate
        $ignore_dir      = ".recycle" ascii
    
    condition:
        uint16(0) == 0x5A4D
        and filesize > 1MB   // Rust binaries are large
        and $rust_panic
        and (
            ($rustls1 or $rustls2 or $rustls3) and
            ($onion_addr or $onion_addr2) and
            ($chacha20 or $aes_gcm)
        )
}

// ─────────────────────────────────────────────────────────────
// RULE 6: Go Malware with TLS (Lazarus/APT patterns)
// ─────────────────────────────────────────────────────────────
rule Go_Malware_TLS_InsecureSkipVerify {
    meta:
        description = "Go malware with TLS certificate verification disabled"
        author      = "Threat Intel Team"
        mitre_att   = "T1071.001"
        confidence  = "HIGH"
    
    strings:
        // Go runtime/binary markers
        $go_buildid      = "Go build ID" ascii
        $go_pclntab      = { FF FF FF FB 00 00 }  // pclntab magic
        $go_version      = /go1\.[0-9]{1,2}\.[0-9]+/ ascii
        
        // InsecureSkipVerify pattern
        $insecure        = "InsecureSkipVerify" ascii
        
        // Common Go HTTP client with TLS bypass
        $go_http         = "net/http" ascii
        $go_tls          = "crypto/tls" ascii
        
        // Go binary markers
        $go_main         = "main.main" ascii
        $go_goroutine    = "goroutine" ascii
    
    condition:
        uint16(0) == 0x5A4D
        and $insecure
        and (
            $go_buildid or $go_pclntab or
            ($go_version and $go_main)
        )
}
```

---

## 21. Sigma Rules for TLS Anomaly Detection

```yaml
# ============================================================
# Sigma Rules: TLS Network Anomaly Detection
# ============================================================

# ─────────────────────────────────────────────────────────────
# RULE 1: Self-Signed Certificate from Non-Browser Process
# ─────────────────────────────────────────────────────────────
title: TLS Self-Signed Certificate from Suspicious Process
id: 8f3c2a1b-4d5e-6f7a-8b9c-0d1e2f3a4b5c
status: production
description: |
    Detects TLS connections using self-signed certificates from
    processes that are not browsers or known legitimate software.
    Self-signed certs are a common APT C2 indicator.
author: Threat Intel Team
date: 2024/01/01
mitre_att_ck:
    - attack.command_and_control
    - attack.t1071.001
    - attack.t1587.003
logsource:
    category: network
    product: zeek
    definition: Requires Zeek SSL log with subject/issuer fields
detection:
    selection:
        # Self-signed: subject == issuer
        log_type: ssl
        # Zeek ssl.log fields
    filter_legitimate:
        # Legitimate browsers
        resp_hostname|contains:
            - 'localhost'
            - '127.0.0.'
            - '192.168.'
    filter_browsers:
        # Exclude known browser processes (if process info available)
        initiated_by|contains:
            - 'chrome.exe'
            - 'firefox.exe'
            - 'msedge.exe'
            - 'safari'
    condition: selection and not (filter_legitimate or filter_browsers)
fields:
    - ts
    - uid
    - id.orig_h
    - id.resp_h
    - id.resp_p
    - server_name
    - subject
    - issuer
    - validation_status
level: medium
falsepositives:
    - Development environments
    - Internal tools with self-signed certificates
    - IoT devices (document these)

---
# ─────────────────────────────────────────────────────────────
# RULE 2: JA3 Hash Matching Known Malware Fingerprints
# ─────────────────────────────────────────────────────────────
title: Known Malware JA3 Fingerprint Detected
id: 1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d
status: production
description: |
    Detects TLS connections matching known malware JA3 fingerprints.
    JA3 is computed from ClientHello parameters and identifies TLS clients.
author: Threat Intel Team
date: 2024/01/01
mitre_att_ck:
    - attack.command_and_control
    - attack.t1071.001
logsource:
    category: network
    product: zeek
    definition: Requires Zeek ssl.log with ja3 field (zeek-package: ja3)
detection:
    malware_ja3:
        log_type: ssl
        ja3|contains:
            # Cobalt Strike default
            - 'de9f13b1e54f3bd40b11c1cd73dab95b'
            # Metasploit
            - '51c64c77e60f3980eea90869b68c58a8'
            # TrickBot
            - '6734f37431670b3ab4292b8f60f29984'
            # Emotet
            - 'b386946a5a44d1ddcc843bc75336dfce'
            # Mirai
            - '72a589da586844d7f0818ce684948eea'
            # Lazarus HOPLIGHT
            - 'a0e9f5d64349fb13191bc781f81f42e1'
    condition: malware_ja3
fields:
    - ts
    - uid
    - id.orig_h
    - id.orig_p
    - id.resp_h
    - id.resp_p
    - ja3
    - server_name
level: high
falsepositives:
    - Very rare — JA3 collision possible but unlikely for listed hashes
    - Same JA3 used by multiple tools (e.g., Go stdlib JA3 used by both malware and legitimate Go apps)

---
# ─────────────────────────────────────────────────────────────
# RULE 3: TLS on Non-Standard Port (C2 Evasion)
# ─────────────────────────────────────────────────────────────
title: TLS Communication on Non-Standard Port
id: 2b3c4d5e-6f7a-8b9c-0d1e-2f3a4b5c6d7e
status: production
description: |
    Detects TLS (HTTPS/SSL) connections on ports other than
    standard HTTPS ports. Common APT technique to avoid port-based
    detection and blend with expected traffic.
author: Threat Intel Team
date: 2024/01/01
mitre_att_ck:
    - attack.command_and_control
    - attack.t1071.001
    - attack.t1571
logsource:
    category: network
    product: zeek
detection:
    tls_connection:
        log_type: ssl
        version|contains:
            - 'TLSv1'
            - 'TLSv1.2'
            - 'TLSv1.3'
    non_standard_port:
        id.resp_p|not_contains:
            - '443'
            - '8443'
            - '4443'
            - '993'   # IMAPS
            - '995'   # POP3S
            - '465'   # SMTPS
            - '636'   # LDAPS
            - '853'   # DoT
            - '8083'  # Common HTTPS alt
            - '4433'  # Common HTTPS alt
    condition: tls_connection and non_standard_port
level: low
falsepositives:
    - Internal applications on non-standard TLS ports
    - Developer environments
    - Some legitimate services (define baselines first)

---
# ─────────────────────────────────────────────────────────────
# RULE 4: JARM Hash Matching Known C2 Frameworks
# ─────────────────────────────────────────────────────────────
title: Known C2 Framework JARM Fingerprint
id: 3c4d5e6f-7a8b-9c0d-1e2f-3a4b5c6d7e8f
status: experimental
description: |
    Detects servers with JARM fingerprints matching known C2 frameworks.
    JARM is an active fingerprint of TLS server configuration.
author: Threat Intel Team
date: 2024/01/01
mitre_att_ck:
    - attack.command_and_control
    - attack.t1071.001
logsource:
    category: network
    product: custom
    definition: Requires JARM scanning output integrated with SIEM
detection:
    c2_jarm:
        jarm|contains:
            # Cobalt Strike Team Server
            - '07d14d16d21d21d07c42d41d00041d24a458a375eef0c576d23a7bab9a9fb1'
            # Metasploit
            - '05d02d19d00000000000000000000000000000000000000000000000000000'
            # Sliver C2
            - '00000000000000000041d00000041d9535d5979f591ae8e547c5e5743e5b64'
    condition: c2_jarm
level: high
falsepositives:
    - C2 framework operators frequently change JARM by modifying TLS config
    - Build internal JARM database of legitimate internal servers

---
# ─────────────────────────────────────────────────────────────
# RULE 5: Beaconing Behavior Detection (TLS)
# ─────────────────────────────────────────────────────────────
title: Periodic TLS Beaconing Behavior
id: 4d5e6f7a-8b9c-0d1e-2f3a-4b5c6d7e8f9a
status: production
description: |
    Detects regular periodic TLS connections from a single source
    to a single destination — characteristic of C2 beacon behavior.
    Uses statistical analysis of connection timing.
author: Threat Intel Team
date: 2024/01/01
mitre_att_ck:
    - attack.command_and_control
    - attack.t1071.001
    - attack.t1573.001
logsource:
    category: network
    product: zeek
detection:
    # This rule requires enrichment/aggregation in SIEM
    # Implementation varies by SIEM product
    # Pseudologic:
    #   Count TLS connections per (src_ip, dst_ip, dst_port) per hour
    #   If count >= 3 AND stddev(interval) / mean(interval) < 0.3
    #   → beaconing detected
    selection:
        log_type: ssl
        # Threshold: 3+ connections, low coefficient of variation
        _comment: "Implemented as SIEM aggregation rule"
    condition: selection
level: medium
falsepositives:
    - Legitimate applications with periodic sync (antivirus, update clients)
    - Time synchronization services
    - Document all known beaconing legitimate software
```

---

## 22. Zeek Scripting for TLS Intelligence

```zeek
##########################################################################
# Zeek TLS Intelligence Scripts
# For threat hunting and APT C2 detection
##########################################################################

@load base/protocols/ssl
@load base/frameworks/notice

module TLSIntel;

export {
    redef enum Notice::Type += {
        SelfSignedCert,
        LowEntropyRandom,
        SuspiciousALPN,
        CertExpiredButActive,
        PossibleDomainFronting,
        UnusualCipherSuite,
    };
}

##########################################################################
# HOOK: SSL certificate analysis on each new connection
##########################################################################
event ssl_established(c: connection) {
    
    # ─── 1. SELF-SIGNED CERTIFICATE DETECTION ──────────────────────
    if (c$ssl?$subject && c$ssl?$issuer) {
        if (c$ssl$subject == c$ssl$issuer) {
            NOTICE([$note=SelfSignedCert,
                    $conn=c,
                    $msg=fmt("Self-signed TLS cert: subject=%s", c$ssl$subject),
                    $identifier=cat(c$id$resp_h, c$ssl$subject),
                    $suppress_for=1hr]);
        }
    }
    
    # ─── 2. SUSPICIOUS CIPHER SUITE ────────────────────────────────
    if (c$ssl?$cipher) {
        local weak_ciphers = set(
            "TLS_RSA_WITH_RC4_128_MD5",
            "TLS_RSA_WITH_RC4_128_SHA",
            "TLS_RSA_WITH_3DES_EDE_CBC_SHA",
            "TLS_NULL_WITH_NULL_NULL",
            "SSL_CK_DES_192_EDE3_CBC_WITH_MD5"
        );
        
        if (c$ssl$cipher in weak_ciphers) {
            NOTICE([$note=UnusualCipherSuite,
                    $conn=c,
                    $msg=fmt("Weak/unusual cipher negotiated: %s", c$ssl$cipher),
                    $identifier=cat(c$id$resp_h, c$ssl$cipher),
                    $suppress_for=6hr]);
        }
    }
    
    # ─── 3. EXPIRED CERTIFICATE STILL BEING USED ───────────────────
    if (c$ssl?$not_valid_after) {
        if (c$ssl$not_valid_after < network_time()) {
            NOTICE([$note=CertExpiredButActive,
                    $conn=c,
                    $msg=fmt("Expired cert from %s (expired: %s)",
                             c$id$resp_h, strftime("%Y-%m-%d", c$ssl$not_valid_after)),
                    $identifier=cat(c$id$resp_h, c$ssl$subject)]);
        }
    }
    
    # ─── 4. SUSPICIOUS ALPN VALUES ─────────────────────────────────
    local suspicious_alpn = set("acme-tls/1", "dot", "irc");
    
    if (c$ssl?$next_protocol && c$ssl$next_protocol in suspicious_alpn) {
        NOTICE([$note=SuspiciousALPN,
                $conn=c,
                $msg=fmt("Unusual ALPN protocol: %s to %s",
                         c$ssl$next_protocol, c$id$resp_h),
                $suppress_for=1hr]);
    }
}

##########################################################################
# LOG: Custom TLS intelligence log
##########################################################################
export {
    type Info: record {
        ts:              time     &log;
        uid:             string   &log;
        id:              conn_id  &log;
        version:         string   &log &optional;
        cipher:          string   &log &optional;
        ja3:             string   &log &optional;
        ja3s:            string   &log &optional;
        server_name:     string   &log &optional;
        subject:         string   &log &optional;
        issuer:          string   &log &optional;
        self_signed:     bool     &log &default=F;
        not_valid_before: time   &log &optional;
        not_valid_after:  time   &log &optional;
        cert_age_days:   int      &log &optional;
        validation:      string   &log &optional;
    };
    
    global log_tls_intel: event(rec: Info);
}

redef record connection += {
    tls_intel: Info &optional;
};

event zeek_init() {
    Log::create_stream(TLSIntel::LOG,
        [$columns=Info, $ev=log_tls_intel, $path="tls_intel"]);
}

event ssl_established(c: connection) {
    if (!c?$ssl) return;
    
    local rec: TLSIntel::Info = [$ts=network_time(), $uid=c$uid, $id=c$id];
    
    if (c$ssl?$version)     rec$version     = c$ssl$version;
    if (c$ssl?$cipher)      rec$cipher      = c$ssl$cipher;
    if (c$ssl?$ja3)         rec$ja3         = c$ssl$ja3;
    if (c$ssl?$ja3s)        rec$ja3s        = c$ssl$ja3s;
    if (c$ssl?$server_name) rec$server_name = c$ssl$server_name;
    if (c$ssl?$subject)     rec$subject     = c$ssl$subject;
    if (c$ssl?$issuer)      rec$issuer      = c$ssl$issuer;
    if (c$ssl?$validation_status) rec$validation = c$ssl$validation_status;
    
    if (c$ssl?$subject && c$ssl?$issuer)
        rec$self_signed = (c$ssl$subject == c$ssl$issuer);
    
    if (c$ssl?$not_valid_before) {
        rec$not_valid_before = c$ssl$not_valid_before;
    }
    if (c$ssl?$not_valid_after) {
        rec$not_valid_after = c$ssl$not_valid_after;
        if (c$ssl?$not_valid_before) {
            rec$cert_age_days = (int_to_count(
                double_to_int((c$ssl$not_valid_after - c$ssl$not_valid_before) / 86400.0)
            )) as int;
        }
    }
    
    Log::write(TLSIntel::LOG, rec);
}

##########################################################################
# DOMAIN FRONTING DETECTION
# Detects SNI ≠ HTTP Host header mismatch
##########################################################################
module DomainFronting;

export {
    global check_fronting: event(c: connection, host_header: string);
}

event http_header(c: connection, is_orig: bool, name: string, value: string) {
    if (!is_orig) return;
    if (name != "HOST") return;
    
    # Only check HTTPS connections (port 443)
    if (c$id$resp_p != 443/tcp) return;
    
    # If connection has SSL info with SNI
    if (!c?$ssl || !c$ssl?$server_name) return;
    
    local sni = c$ssl$server_name;
    local host = sub(value, /:[0-9]+$/, "");  # Remove port if present
    
    # Normalize: remove www. prefix for comparison
    local sni_base  = sub(sni, /^www\./, "");
    local host_base = sub(host, /^www\./, "");
    
    if (sni_base != host_base) {
        NOTICE([$note=TLSIntel::PossibleDomainFronting,
                $conn=c,
                $msg=fmt("Domain fronting: SNI=%s but Host=%s", sni, host),
                $identifier=cat(c$id$resp_h, sni, host)]);
    }
}
```

---

## 23. The Expert Mental Model

**TLS is fundamentally a protocol for establishing shared cryptographic context between two parties who initially share nothing but infrastructure.**

The elite analyst internalizes TLS not as a black box that "encrypts traffic" but as a precisely specified state machine with a clear threat model and known attack surface at each layer. When you see TLS in a malware sample, you immediately decompose it into five analytical dimensions:

**Implementation fingerprint:** What library was used? OpenSSL, WinHTTP, Go's crypto/tls, Rustls, or something custom? Each has a unique JA3 fingerprint, binary artifact set, and characteristic failure modes. The library choice reveals the attacker's operational constraints and preferences.

**Authentication policy:** Does the malware validate the server's certificate? Almost always no — `SSL_VERIFY_NONE` is the lazy path. If it DOES validate (pinning, mTLS), you're looking at a sophisticated operator who has invested in counter-intelligence infrastructure. The presence of certificate pinning means the operator is actively defending against your interception attempts.

**Key exchange and forward secrecy:** Does the session use ephemeral ECDHE? If so, capturing traffic is useless without real-time key extraction from memory. If it uses RSA key exchange, capturing the private key (from the C2 server) decrypts all historical sessions — a critical collection opportunity.

**Network behavioral signature:** Beacon timing, connection duration, data volume patterns — these survive even perfect TLS implementation because they manifest at the TCP/timing layer. A perfectly-configured TLS connection still leaves timing artifacts. A C2 beacon sleeping 30 seconds with 15% jitter creates a statistical signature visible in NetFlow even with no decryption.

**Infrastructure correlation:** Every TLS connection generates a certificate. That certificate, even if self-signed, contains attributes — key size, subject fields, validity period, serial number — that cluster across an operator's infrastructure. CT logs expose every certificate ever issued for legitimate domains. The combination of JA3/JARM fingerprints, certificate attributes, passive DNS, and WHOIS data creates a rich attribution surface that the operator cannot fully sanitize.

The apex skill is understanding that **TLS does not hide the existence of communication, only its content.** The timing, volume, destination, and cryptographic artifacts of TLS remain observable and attributable. Your job is to extract maximum intelligence from what remains visible, and to intercept or decrypt what can be accessed through legal means, memory forensics, or behavioral inference.

> **MITRE ATT&CK Coverage:**
> - T1071.001 — Application Layer Protocol: Web Protocols (HTTPS C2)
> - T1573.001 — Encrypted Channel: Symmetric Cryptography
> - T1573.002 — Encrypted Channel: Asymmetric Cryptography
> - T1587.003 — Develop Capabilities: Digital Certificates
> - T1588.004 — Obtain Capabilities: Digital Certificates
> - T1608.003 — Stage Capabilities: Install Digital Certificate
> - T1584.001 — Compromise Infrastructure: Domains
> - T1090.002 — Proxy: External Proxy (domain fronting)
> - T1659.001 — Content Injection: TLS-based data hiding

---

*End of TLS Protocol Elite Analyst Guide*
*Version: 1.0 | Classification: INTERNAL RESEARCH USE*
*References: RFC 8446, RFC 5246, RFC 6347, RFC 9147, RFC 5869, RFC 6962, RFC 8701*

