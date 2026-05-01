# WireGuard Protocol — Complete In-Depth Guide

> *"WireGuard is not merely a VPN. It is a lesson in how cryptographic engineering, systems design, and minimalism converge into something elegant."*

---

## Table of Contents

1. [What is WireGuard?](#1-what-is-wireguard)
2. [Design Philosophy and Goals](#2-design-philosophy-and-goals)
3. [Foundational Vocabulary](#3-foundational-vocabulary)
4. [Cryptographic Primitives](#4-cryptographic-primitives)
5. [The Noise Protocol Framework](#5-the-noise-protocol-framework)
6. [WireGuard Cryptographic Handshake](#6-wireguard-cryptographic-handshake)
7. [Session Lifecycle and Key Rotation](#7-session-lifecycle-and-key-rotation)
8. [Packet Structure and Encapsulation](#8-packet-structure-and-encapsulation)
9. [Routing: Allowed IPs and Cryptokey Routing](#9-routing-allowed-ips-and-cryptokey-routing)
10. [WireGuard Data Flow — Full Picture](#10-wireguard-data-flow--full-picture)
11. [Timer Model and Keepalives](#11-timer-model-and-keepalives)
12. [WireGuard vs IPSec vs OpenVPN](#12-wireguard-vs-ipsec-vs-openvpn)
13. [Threat Model and Security Properties](#13-threat-model-and-security-properties)
14. [C Implementation — From Scratch](#14-c-implementation--from-scratch)
15. [Rust Implementation — Idiomatic and Safe](#15-rust-implementation--idiomatic-and-safe)
16. [Kernel vs Userspace WireGuard](#16-kernel-vs-userspace-wireguard)
17. [WireGuard in Practice — Configuration Deep Dive](#17-wireguard-in-practice--configuration-deep-dive)
18. [Advanced Topics](#18-advanced-topics)
19. [Mental Models and Expert Intuition](#19-mental-models-and-expert-intuition)

---

## 1. What is WireGuard?

WireGuard is a **modern, high-performance, cryptographically sound VPN (Virtual Private Network) protocol** designed by Jason A. Donenfeld and first published in 2016. It became part of the Linux kernel in version 5.6 (March 2020).

### What is a VPN (Virtual Private Network)?

A VPN creates a **virtual encrypted tunnel** between two network endpoints. All data passing through this tunnel is encrypted and authenticated — even if it travels over hostile, untrusted networks like the public internet.

Think of it like this:

```
WITHOUT VPN:
  [Your Machine] ----PLAINTEXT----> [Internet Router] ----PLAINTEXT----> [Destination]
                         ^ anyone can read this

WITH VPN:
  [Your Machine] ==ENCRYPTED==> [VPN Endpoint] ----PLAINTEXT----> [Destination]
                    ^ nobody can read this tunnel
```

### What is a TUN Interface?

Before understanding WireGuard, you must understand **TUN** (tunnel) devices.

A **TUN device** is a virtual network interface in the operating system kernel. It looks like a real network card (eth0, wlan0), but instead of sending bits over physical wires, it sends IP packets to a user-space or kernel program.

```
Normal NIC:        [Kernel Network Stack] <--> [Physical NIC] <--> [Wire/Radio]

TUN Interface:     [Kernel Network Stack] <--> [TUN Driver] <--> [User Program]
                                                                       |
                                                          (WireGuard reads these packets,
                                                           encrypts them, sends over UDP)
```

WireGuard creates a TUN interface (e.g., `wg0`). When the kernel routes a packet to `wg0`, WireGuard reads it, encrypts it using AEAD, and sends it as a UDP datagram. Incoming UDP datagrams are decrypted and injected back into the TUN interface.

---

## 2. Design Philosophy and Goals

### The Problem with Existing VPNs

Before WireGuard, the dominant options were:

| Protocol  | Lines of Code (approx) | Issues                                          |
|-----------|------------------------|-------------------------------------------------|
| OpenVPN   | ~70,000+               | Complex TLS stack, slow handshake, bloated      |
| IPSec     | ~400,000+ (kernel)     | Extremely complex, dozens of cipher suites      |
| OpenSSH   | ~100,000+              | Not designed for VPN, workarounds everywhere    |

WireGuard's goals, as stated by its author:

1. **Minimal Attack Surface** — Small codebase (~4,000 lines). Less code = fewer bugs = fewer vulnerabilities.
2. **Cryptographic Agility Elimination** — No negotiation. One set of algorithms. No downgrade attacks.
3. **Simplicity** — Simple enough to be audited and formally verified.
4. **Performance** — Faster than IPSec and OpenVPN in throughput and latency.
5. **Stealth** — No response to unauthenticated packets. Makes WireGuard "dark" to port scanners.
6. **Modern Cryptography** — Uses primitives designed in the 2010s, not 1990s.

### The "Cryptographic Agility" Problem

**Cryptographic agility** = allowing negotiation of which cipher suite, hash function, or key exchange to use.

This sounds flexible, but it is a security disaster:
- More code paths = more bugs
- Attackers can force weak algorithm selection (downgrade attacks)
- Complexity makes formal verification impossible

WireGuard eliminates this entirely. **One algorithm per function, no choices, no negotiation.**

---

## 3. Foundational Vocabulary

Before going deeper, here are all critical terms explained from the ground up.

### Symmetric vs Asymmetric Cryptography

**Symmetric**: Same key for encryption and decryption. Fast. Both parties must share the key securely first.

```
Encrypt(plaintext, key) --> ciphertext
Decrypt(ciphertext, key) --> plaintext
```

**Asymmetric**: Key pair — public key + private key. Slow. The public key can be shared openly.

```
Encrypt(plaintext, public_key) --> ciphertext
Decrypt(ciphertext, private_key) --> plaintext
```

A private key is a random 256-bit number you keep secret. A public key is mathematically derived from it.

### ECDH — Elliptic Curve Diffie-Hellman

A key agreement algorithm. Two parties each have a key pair. By combining **their own private key** with the **other party's public key**, both parties independently arrive at the **same shared secret** — without ever transmitting the secret itself.

```
Alice: private_A, public_A = A * G
Bob:   private_B, public_B = B * G

Alice computes: private_A * public_B = private_A * B * G
Bob   computes: private_B * public_A = private_B * A * G
Both equal:     A * B * G  (same value!)

G = generator point on the elliptic curve
* = elliptic curve scalar multiplication
```

An eavesdropper sees only `public_A` and `public_B`. Computing `A * B * G` from just those is the "Elliptic Curve Discrete Logarithm Problem" — computationally infeasible.

### Curve25519

The specific elliptic curve WireGuard uses for ECDH. Designed by Daniel Bernstein. It is:
- Resistant to timing side-channels by design
- Cannot be weakened by deliberate parameter choice (unlike NIST curves)
- Fast in software

All WireGuard keys (static, ephemeral) are Curve25519 key pairs.

### ChaCha20-Poly1305 — AEAD Cipher

**AEAD** = Authenticated Encryption with Associated Data.

This means: *encrypt data AND authenticate it in one operation*.

- **ChaCha20** is the stream cipher (encryption part). Designed by Bernstein. XOR-based, fast without hardware AES acceleration.
- **Poly1305** is the MAC (Message Authentication Code). Produces a 128-bit authentication tag.

```
Encrypt:
  ciphertext, tag = AEAD_Encrypt(key, nonce, plaintext, associated_data)

Decrypt:
  plaintext = AEAD_Decrypt(key, nonce, ciphertext, tag, associated_data)
  -- FAILS if ciphertext was tampered with
  -- FAILS if tag doesn't match
```

Associated data is authenticated but not encrypted. In WireGuard, this includes packet headers.

### BLAKE2s — Hash Function

A fast cryptographic hash function. Produces a fixed-size digest from arbitrary input. Used in WireGuard for KDF (Key Derivation Function) chains.

```
BLAKE2s(input) --> 256-bit digest (32 bytes)
```

Properties:
- One-way: cannot reverse to find input
- Collision resistant: cannot find two inputs with same output
- Fast: faster than SHA-2

### HKDF — Hash-based Key Derivation Function

Takes a secret (e.g., a Diffie-Hellman shared secret) and derives one or more cryptographic keys from it. Based on HMAC.

```
HKDF-Extract(salt, IKM) --> PRK   (pseudorandom key)
HKDF-Expand(PRK, info, length) --> OKM  (output keying material)
```

### Nonce

A **nonce** (Number Used Once) is a unique value tied to a key. Never reuse a nonce with the same key — it breaks AEAD security completely.

WireGuard uses a 64-bit counter as the nonce. The counter increments by 1 for every packet.

### Perfect Forward Secrecy (PFS)

If an attacker records your encrypted traffic today, and later steals your long-term private key, **can they decrypt the old traffic?**

With PFS: **No.** Each session uses **ephemeral (temporary) keys** that are deleted after the session. Even with your long-term key, past sessions cannot be decrypted.

WireGuard achieves PFS by generating fresh ephemeral Curve25519 key pairs per handshake.

### Identity Hiding / Anonymity

Does WireGuard reveal who you are to observers?

- The **initiator's identity** is hidden using the responder's static public key for encryption.
- The **responder's identity** is revealed only to authenticated initiators.

### Replay Attack

An attacker captures a valid encrypted packet and re-sends it later. Without replay protection, this could replay commands or actions.

WireGuard uses a **sliding window anti-replay mechanism**: a 64-bit counter plus a 2048-bit bitmap tracking received counter values. Packets with counters below the window or already seen are dropped.

---

## 4. Cryptographic Primitives

WireGuard is built on exactly **4 primitives**:

```
+------------------+--------------------------------------------+------------------+
| Function         | Primitive                                  | Purpose          |
+------------------+--------------------------------------------+------------------+
| Key Exchange     | Curve25519 ECDH                            | DH operations    |
| AEAD Encryption  | ChaCha20-Poly1305                          | Data encryption  |
| Hashing          | BLAKE2s                                    | KDF, MACs        |
| Key Derivation   | HKDF (built on BLAKE2s)                    | Key derivation   |
+------------------+--------------------------------------------+------------------+
```

No TLS. No X.509 certificates. No negotiation. These four — always.

### Construction Notation

Throughout this guide, we use notation from the WireGuard paper:

```
DH(private, public)          -- Curve25519 ECDH
AEAD(key, counter, msg, aad) -- ChaCha20-Poly1305 encrypt
AEAD_DEC(key, counter, cipher, aad) -- ChaCha20-Poly1305 decrypt
HASH(input)                  -- BLAKE2s-256
HMAC(key, input)             -- BLAKE2s-based HMAC
KDF1(key, input)             -- HKDF yielding 1 output
KDF2(key, input)             -- HKDF yielding 2 outputs
KDF3(key, input)             -- HKDF yielding 3 outputs
MAC(key, input)              -- Keyed BLAKE2s-128
```

---

## 5. The Noise Protocol Framework

WireGuard's handshake is built on the **Noise Protocol Framework** — specifically the `Noise_IKpsk2` pattern.

### What is the Noise Protocol Framework?

Noise (designed by Trevor Perrin) is a framework for building handshake protocols from simple primitives. Instead of inventing a new handshake from scratch, you select a **pattern** and instantiate it with your chosen primitives.

A Noise handshake is described as a sequence of **message patterns**. Each `->` or `<-` is a message from initiator to responder or back. Each token within a message performs a cryptographic operation.

### Noise Tokens

| Token | Meaning                                         |
|-------|-------------------------------------------------|
| `e`   | Send ephemeral public key                       |
| `s`   | Send static public key (encrypted)              |
| `ee`  | DH(my_ephemeral, their_ephemeral) → mix into state |
| `es`  | DH(my_ephemeral, their_static) → mix            |
| `se`  | DH(my_static, their_ephemeral) → mix            |
| `ss`  | DH(my_static, their_static) → mix               |
| `psk` | Mix pre-shared key into state                   |

### The Noise_IKpsk2 Pattern

WireGuard uses `Noise_IKpsk2`:

```
Initiator                                   Responder
---------                                   ---------
-> e, es, s, ss
                                          <- e, ee, se, psk
```

Meaning:
- Message 1 (Initiator → Responder): send ephemeral, do DH(ephemeral, responder_static), send static encrypted, do DH(initiator_static, responder_static)
- Message 2 (Responder → Initiator): send ephemeral, do DH(ee), do DH(se), mix psk

This provides:
- **Mutual authentication** (both sides prove identity)
- **Forward secrecy** (ephemeral keys discarded)
- **Identity hiding** (initiator identity encrypted before transmission)
- **Optional PSK** (preshared key for post-quantum partial protection)

### Handshake State Machine

Noise maintains a **HandshakeState** with three components:

```
hs.s   = local static key pair
hs.e   = local ephemeral key pair
hs.rs  = remote static public key
hs.re  = remote ephemeral public key
hs.h   = hash — "what we've processed so far" (256 bits)
hs.ck  = chaining key — evolves through each DH (256 bits)
```

Every operation **mixes** into `h` and `ck`, creating a cryptographic transcript of the entire handshake.

---

## 6. WireGuard Cryptographic Handshake

### Notation Setup

```
I_priv, I_pub    -- Initiator's static key pair
R_priv, R_pub    -- Responder's static key pair
Ei_priv, Ei_pub  -- Initiator's ephemeral key pair (fresh per handshake)
Er_priv, Er_pub  -- Responder's ephemeral key pair (fresh per handshake)
PSK              -- Optional pre-shared key (32 bytes, zeroed if unused)
C                -- Chaining key (starts as HASH("Noise_IKpsk2_..."))
H                -- Handshake hash
```

### Initialization

Both parties agree on a **protocol identifier string** which seeds the initial state:

```
CONSTRUCTION = "Noise_IKpsk2_25519_ChaChaPoly_BLAKE2s"
IDENTIFIER   = "WireGuard v1 zx2c4 Jason@zx2c4.com"

C  = HASH(CONSTRUCTION)
H  = HASH(C || IDENTIFIER)
H  = HASH(H || R_pub)   -- Mix responder's public key into hash
```

The initial C and H are the same on both sides (both know the strings and R_pub).

---

### Handshake Message 1: Initiator → Responder

```
+----------+----------+----------------------+---------------------+
| msg_type | sender_  |   unencrypted_       |   encrypted_        |
| (1 byte) | index    |   ephemeral          |   static            |
|          | (4 bytes)| (32 bytes: Ei_pub)   | (48 bytes: I_pub    |
|          |          |                      |  + 16 byte AEAD tag)|
+----------+----------+----------------------+---------------------+
| encrypted_timestamp |
| (28 bytes: 12 byte  |
|  timestamp + 16 tag)|
+---------------------+

Total: 148 bytes
```

**Step-by-step operations (Initiator side):**

```
Step 1: Generate fresh ephemeral key pair
  Ei_priv, Ei_pub = generate_keypair()

Step 2: Mix ephemeral public key into hash
  C, k = KDF2(C, Ei_pub)   -- not used here, just advancing C
  Actually: C = KDF1(C, Ei_pub)
  H = HASH(H || Ei_pub)
  -- Ei_pub sent as msg.unencrypted_ephemeral

Step 3: Compute DH(Ei_priv, R_pub) and mix
  dh1 = DH(Ei_priv, R_pub)    -- ephemeral_initiator × static_responder
  C, k = KDF2(C, dh1)

Step 4: Encrypt initiator's static public key
  msg.encrypted_static = AEAD(k, 0, I_pub, H)
  H = HASH(H || msg.encrypted_static)

Step 5: Compute DH(I_priv, R_pub) and mix
  dh2 = DH(I_priv, R_pub)    -- static_initiator × static_responder
  C, k = KDF2(C, dh2)

Step 6: Encrypt timestamp
  timestamp = TAI64N_now()   -- 12-byte timestamp
  msg.encrypted_timestamp = AEAD(k, 0, timestamp, H)
  H = HASH(H || msg.encrypted_timestamp)
```

**What this achieves so far:**
- Responder can verify the initiator knows `I_priv` (they could encrypt with it)
- Timestamp prevents replay attacks (responder rejects old handshakes)
- Initiator's identity is **encrypted** — eavesdropper cannot see `I_pub`

---

### Handshake Message 2: Responder → Initiator

```
+----------+----------+--------------------+---------------------+
| msg_type | sender_  | unencrypted_       | encrypted_nothing   |
| (1 byte) | index    | ephemeral          | (0 + 16 byte tag)   |
|          | (4 bytes)| (32 bytes: Er_pub) |                     |
+----------+----------+--------------------+---------------------+

Total: 92 bytes
```

**Step-by-step operations (Responder side):**

```
Step 1: Verify and process Message 1
  -- Responder receives msg1
  -- Decrypt to find I_pub, verify timestamp is recent
  -- (mirrors initiator's steps above, but in reverse)

Step 2: Generate fresh ephemeral key pair
  Er_priv, Er_pub = generate_keypair()

Step 3: Mix Er_pub
  C = KDF1(C, Er_pub)
  H = HASH(H || Er_pub)
  -- Er_pub sent as msg.unencrypted_ephemeral

Step 4: Compute DH(Er_priv, Ei_pub) and mix
  dh3 = DH(Er_priv, Ei_pub)   -- ee
  C = KDF1(C, dh3)

Step 5: Compute DH(Er_priv, I_pub) and mix
  dh4 = DH(Er_priv, I_pub)    -- se
  C = KDF1(C, dh4)

Step 6: Mix PSK
  C, t, k = KDF3(C, PSK)
  H = HASH(H || t)

Step 7: Encrypt "nothing" (empty payload with auth tag)
  msg.encrypted_nothing = AEAD(k, 0, "", H)
  H = HASH(H || msg.encrypted_nothing)
```

---

### Handshake Completion: Deriving Session Keys

After Message 2 is processed by the Initiator:

```
Transport keys derived from final chaining key C:

  T_send_i, T_recv_i = KDF2(C, "")    -- Initiator's perspective
  T_send_r = T_recv_i                  -- Responder sends → Initiator receives
  T_recv_r = T_send_i                  -- Responder receives ← Initiator sends

  send_key  = T_send_i   (Initiator uses this to encrypt outgoing data)
  recv_key  = T_recv_i   (Initiator uses this to decrypt incoming data)
```

Both parties now have **identical symmetric keys** derived from the same chaining key, but **neither ever transmitted the keys** — they were derived independently.

**All ephemeral private keys are immediately zeroed from memory.**

---

### Complete Handshake ASCII Diagram

```
INITIATOR                                              RESPONDER
  (I_priv, I_pub)                                     (R_priv, R_pub)
  knows: R_pub                                        knows: I_pub (whitelist)

  INITIALIZATION
  C  = HASH("Noise_IKpsk2_25519_ChaChaPoly_BLAKE2s")
  H  = HASH(C || "WireGuard v1 ...")
  H  = HASH(H || R_pub)
  |                                                         |
  |  Generate Ei_priv, Ei_pub                               |
  |  C  = KDF1(C, Ei_pub)                                   |
  |  H  = HASH(H || Ei_pub)                                 |
  |  dh1 = DH(Ei_priv, R_pub)                               |
  |  C,k = KDF2(C, dh1)                                     |
  |  enc_static = AEAD(k, 0, I_pub, H)                      |
  |  H  = HASH(H || enc_static)                             |
  |  dh2 = DH(I_priv, R_pub)                                |
  |  C,k = KDF2(C, dh2)                                     |
  |  enc_ts = AEAD(k, 0, timestamp, H)                      |
  |  H  = HASH(H || enc_ts)                                 |
  |                                                         |
  |  MSG1: [type=1][sender_idx][Ei_pub][enc_static][enc_ts] |
  | =====================================================>>> |
  |                                                         |
  |                  (Responder mirrors all steps above)    |
  |                  Decrypts I_pub, verifies timestamp     |
  |                  Generate Er_priv, Er_pub               |
  |                  C  = KDF1(C, Er_pub)                   |
  |                  H  = HASH(H || Er_pub)                 |
  |                  dh3 = DH(Er_priv, Ei_pub) [ee]        |
  |                  C  = KDF1(C, dh3)                      |
  |                  dh4 = DH(Er_priv, I_pub)  [se]        |
  |                  C  = KDF1(C, dh4)                      |
  |                  C,t,k = KDF3(C, PSK)                   |
  |                  H  = HASH(H || t)                      |
  |                  enc_empty = AEAD(k, 0, "", H)          |
  |                  H  = HASH(H || enc_empty)              |
  |                                                         |
  |  MSG2: [type=2][sender_idx][receiver_idx][Er_pub][enc_empty]
  | <<<===================================================== |
  |                                                         |
  |  Verify MSG2, mirror DH operations                      |
  |  DERIVE TRANSPORT KEYS:                                 |
  |  T_initiator_send, T_initiator_recv = KDF2(C, "")       |
  |                                   T_responder_recv = T_initiator_send
  |                                   T_responder_send = T_initiator_recv
  |                                                         |
  |  DELETE: Ei_priv, Er_priv, dh1..dh4                     |
  |                                                         |
  |  MSG3: Keepalive (first data packet, may be empty)      |
  | =====================================================>>> |
  |                                                         |
  |            SECURE SESSION ESTABLISHED                   |
  |    Counter_send=0, Counter_recv=0 for both sides        |
  |                                                         |
  |  DATA: [type=4][receiver_idx][counter][AEAD(data)]      |
  | <=================== DATA ============================> |
```

---

## 7. Session Lifecycle and Key Rotation

### Keypair Terminology

| Name                    | Lifetime       | Purpose                            |
|-------------------------|----------------|------------------------------------|
| Static keypair          | Permanent      | Long-term identity                 |
| Ephemeral keypair       | One handshake  | Forward secrecy                    |
| Session (transport) key | Up to 3 min    | Actual data encryption             |

### The Three-Minute Rule

WireGuard enforces **mandatory key rotation**:

```
REKEY_AFTER_MESSAGES  = 2^60  messages
REKEY_AFTER_TIME      = 180   seconds (3 minutes)
REJECT_AFTER_MESSAGES = 2^64 - 2^13 - 1
REJECT_AFTER_TIME     = 180   seconds after rekey_after_time
REKEY_TIMEOUT         = 5     seconds (retry handshake)
KEEPALIVE_TIMEOUT     = 10    seconds (send keepalive)
MAX_TIMER_HANDSHAKES  = 90    seconds / REKEY_TIMEOUT = 18 attempts

Session lifecycle:
  t=0    : Session established
  t=180  : REKEY_AFTER_TIME — begin new handshake
  t=360  : REJECT_AFTER_TIME — old session keys rejected
  t+5    : Retry handshake if no response (up to 18 retries)
```

### Concurrent Sessions

During key rotation, WireGuard can have **two active sessions simultaneously**: the current one and the new one being established. Incoming packets are tried against both.

```
  Session A (current):  counter 0..N,  keys K_a
  Session B (new):      counter 0..M,  keys K_b

  When B is confirmed → A is deleted
  If B fails → keep using A, retry handshake
```

---

## 8. Packet Structure and Encapsulation

### Packet Types

WireGuard defines 4 message types:

| Type | Value | Name                        | Direction          |
|------|-------|-----------------------------|---------------------|
| 1    | 0x01  | Initiation                  | Initiator → Responder |
| 2    | 0x02  | Response                    | Responder → Initiator |
| 3    | 0x03  | Cookie Reply                | Either direction    |
| 4    | 0x04  | Transport Data              | Either direction    |

All multi-byte integers are **little-endian**.

---

### Message Type 1: Initiation (148 bytes)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|    type=1     |    reserved   |    reserved   |    reserved   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                      sender_index (4 bytes)                   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
|           unencrypted_ephemeral (32 bytes = Ei_pub)          |
|                                                               |
|                                                               |
+                                                               +
|                                                               |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
|       encrypted_static (48 bytes = I_pub + 16-byte tag)       |
|                                                               |
|                         ... (48 bytes) ...                    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
|   encrypted_timestamp (28 bytes = 12-byte ts + 16-byte tag)  |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                   MAC1 (16 bytes, keyed BLAKE2s)              |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                   MAC2 (16 bytes, cookie-based)               |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Total: 1+3+4+32+48+28+16+16 = 148 bytes
```

**sender_index**: A random 32-bit value chosen by the initiator. The responder uses this to refer back to this session.

**MAC1**: `MAC(HASH("mac1----" || R_pub), msg[0..116])` — proves sender knows R_pub. Computed over all fields before MAC fields.

**MAC2**: `MAC(cookie, msg[0..132])` — only non-zero if under load (DDoS protection, cookie mechanism).

---

### Message Type 2: Response (92 bytes)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|    type=2     |    reserved   |    reserved   |    reserved   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                      sender_index (4 bytes)                   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                     receiver_index (4 bytes)                  |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
|           unencrypted_ephemeral (32 bytes = Er_pub)          |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|            encrypted_nothing (16 bytes = AEAD tag only)       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                   MAC1 (16 bytes)                             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                   MAC2 (16 bytes)                             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Total: 4+4+4+32+16+16+16 = 92 bytes
```

---

### Message Type 3: Cookie Reply (64 bytes)

Used for DDoS mitigation (explained in Section 11).

```
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|    type=3     |    reserved (3 bytes)                         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                     receiver_index (4 bytes)                  |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    nonce (24 bytes, XChaCha20)                 |
|                                                               |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|              encrypted_cookie (32+16 = 48 bytes)             |
|                    (XChaCha20-Poly1305)                       |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Total: 4+4+24+48 = 80 bytes (note: some sources say 64 for cookie payload)
```

---

### Message Type 4: Transport Data

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|    type=4     |    reserved   |    reserved   |    reserved   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                     receiver_index (4 bytes)                  |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                      counter (8 bytes, little-endian)         |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
|          encrypted_encapsulated_packet                        |
|  (variable length = padded_IP_packet + 16-byte AEAD tag)      |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Header size: 32 bytes
Payload:     variable (padded to 16-byte boundary)
```

**counter**: 64-bit monotonically increasing nonce. Never reuse.

**Encryption of data packet:**

```
nonce = little_endian_64(counter) padded to 12 bytes
  (bytes 0-3 = 0x00, bytes 4-11 = counter)

encrypted_packet = ChaCha20Poly1305_Encrypt(
  key     = transport_send_key,
  nonce   = nonce,
  aad     = "",                -- no associated data for transport
  plaintext = padded_IP_packet
)
```

**Padding**: The IP packet is padded to the next multiple of 16 bytes using zero bytes before encryption. This hides exact packet sizes slightly.

---

## 9. Routing: Allowed IPs and Cryptokey Routing

### What is Allowed IPs?

This is WireGuard's **routing table combined with access control**. Each peer has a list of IP prefixes it is "allowed" to have.

```
Peer (public key: XYZ...)
    AllowedIPs = 10.0.0.2/32, 192.168.1.0/24
```

This means two things:

1. **Outgoing**: When WireGuard needs to send a packet destined for `10.0.0.2` or any `192.168.1.x`, it encrypts it and sends to peer XYZ.

2. **Incoming**: When WireGuard receives a packet from peer XYZ, it decrypts it and only accepts it **if the source IP is in the AllowedIPs list**. This is the access control part.

### Cryptokey Routing Table

The concept: **every IP address in the WireGuard network is bound to a public key**.

```
AllowedIPs → Public Key Lookup Table:

  Destination IP    Public Key (Peer)
  ─────────────────────────────────────
  0.0.0.0/0         PeerA_pub   (default route through VPN)
  10.0.0.2/32       PeerB_pub
  10.0.0.3/32       PeerC_pub
  192.168.1.0/24    PeerD_pub
```

When a packet arrives on `wg0`:
1. Look up destination IP in AllowedIPs table (longest-prefix match)
2. Find corresponding peer's public key
3. Encrypt with that peer's session key
4. Send UDP datagram to peer's endpoint (IP:port)

When a UDP datagram arrives:
1. Read `receiver_index` from header
2. Look up session by index
3. Decrypt with session key
4. Verify source IP is in peer's AllowedIPs
5. If valid, inject decrypted IP packet into TUN

### Longest Prefix Match

Like BGP routing. Most specific route wins.

```
Packet to 192.168.1.50:
  Rule: 0.0.0.0/0    via PeerA  (matches, prefix length = 0)
  Rule: 192.168.1.0/24 via PeerD  (matches, prefix length = 24)
  
  Winner: 192.168.1.0/24 → PeerD  (longest prefix = most specific)
```

---

## 10. WireGuard Data Flow — Full Picture

### Outgoing Packet Path

```
Application Layer
      |
      | write() to socket
      |
   [Kernel TCP/IP Stack]
      |
      | Route lookup: dest IP matches wg0
      |
   [TUN Interface: wg0]
      |
      | read_from_tun()
      |
   [WireGuard Module]
      |
      +-- AllowedIPs lookup: find peer for dest IP
      |
      +-- Check: valid session exists?
      |       NO --> trigger handshake, queue packet
      |       YES --> continue
      |
      +-- Increment send_counter
      |
      +-- Pad packet to 16-byte boundary
      |
      +-- AEAD Encrypt(transport_key, counter, packet)
      |
      +-- Build Type-4 header [type][receiver_idx][counter]
      |
      +-- UDP sendto(peer_endpoint, encrypted_packet)
      |
   [UDP Socket]
      |
   [Kernel Network Stack]
      |
   [Physical NIC] --UDP--> [Internet] --UDP--> [Peer]
```

### Incoming Packet Path

```
   [Physical NIC] <--UDP-- [Internet] <--UDP-- [Peer]
      |
   [Kernel Network Stack]
      |
   [UDP Socket] -- delivers to WireGuard
      |
   [WireGuard Module]
      |
      +-- Check type field in header
      |
      +-- Type 1/2 (Handshake)? --> process handshake state machine
      |
      +-- Type 4 (Data)?
      |
      +-- Look up session by receiver_index
      |
      +-- Verify counter: replay window check
      |       counter already seen? --> DROP
      |       counter too old? --> DROP
      |
      +-- AEAD Decrypt(transport_key, counter, encrypted_packet)
      |       Decryption failed? --> DROP (tampered)
      |
      +-- Update replay window bitmap
      |
      +-- Extract inner IP packet
      |
      +-- Verify source IP is in peer's AllowedIPs
      |       Not in AllowedIPs? --> DROP
      |
      +-- write_to_tun(decrypted_packet)
      |
   [TUN Interface: wg0]
      |
   [Kernel TCP/IP Stack] -- delivers to application
      |
Application Layer
```

### Encapsulation Overhead

```
Original IP packet:  N bytes
+ UDP/IP header:     28 bytes (8 UDP + 20 IPv4, or 48 for IPv6)
+ WireGuard header:  32 bytes (type + reserved + receiver_idx + counter)
+ AEAD tag:          16 bytes
+ Padding:           0-15 bytes

Total overhead:      76-91 bytes for IPv4 transport
                     96-111 bytes for IPv6 transport

MTU recommendation: Set wg0 MTU to 1420 (1500 - 80)
```

---

## 11. Timer Model and Keepalives

### The Five Timers

WireGuard has precisely 5 timers per peer:

```
1. REKEY_AFTER_TIME (180s):
   When elapsed since session creation:
   → Initiate new handshake

2. REJECT_AFTER_TIME (180s after REKEY_AFTER_TIME):
   → Stop using old keys, session is dead

3. REKEY_TIMEOUT (5s):
   After initiating handshake with no response:
   → Retry handshake (up to MAX_TIMER_HANDSHAKES times)

4. KEEPALIVE_TIMEOUT (10s):
   No data received from peer:
   → Send empty keepalive packet
   → Maintains NAT mappings

5. NEW_HANDSHAKE_TIMEOUT (REKEY_AFTER_TIME + REJECT_AFTER_TIME + REKEY_TIMEOUT):
   → If we still haven't established a session, give up
```

### Keepalive Packets

An **empty WireGuard data packet** (type 4 with zero-byte payload after decryption). Purpose: maintain NAT mappings in routers.

Most consumer routers have NAT tables with UDP timeouts of 30-120 seconds. If no UDP traffic is seen, the mapping is deleted and incoming packets are rejected.

WireGuard's 10-second keepalive ensures the NAT mapping stays fresh.

### DDoS Mitigation: The Cookie Mechanism

When a WireGuard server is under load, it may not be able to process CPU-intensive handshake operations (which involve Curve25519 multiplications).

**The cookie mechanism** allows the server to prove that the client's IP is reachable before doing expensive crypto:

```
Normal (no load):
  Client ─── MSG1 ──────────────────────────────────────────> Server
  Client <── MSG2 (full handshake response) ──────────────── Server

Under load (server busy):
  Client ─── MSG1 ──────────────────────────────────────────> Server
  Client <── MSG3 (Cookie Reply with encrypted cookie) ────── Server
    (Cookie = MAC(server_secret_key, timestamp, client_IP))

  Client ─── MSG1 (with MAC2 = MAC(cookie, msg)) ──────────> Server
    (Client proves IP ownership by using the cookie)
  Client <── MSG2 (now server processes handshake) ─────────── Server
```

The cookie is valid for 120 seconds. The server's secret rotates every 120 seconds (indexed by 1-minute windows).

---

## 12. WireGuard vs IPSec vs OpenVPN

### Architecture Comparison

```
OpenVPN Architecture:
  TLS 1.3 handshake (on TCP or UDP port 1194)
  X.509 certificates (CA, server cert, client cert)
  Choice of: AES-128-GCM, AES-256-GCM, CHACHA20-POLY1305
  Control channel (TLS) + Data channel (cipher of choice)
  Runs in userspace (slower)

IPSec Architecture:
  IKEv2 key exchange (UDP 500, 4500)
  X.509 certificates or PSK
  Choice of: 3DES, AES-128, AES-256, AES-GCM
  Choice of: SHA1, SHA256, SHA512
  ESP (Encapsulating Security Payload) for data
  Runs in kernel (faster)

WireGuard Architecture:
  Noise_IKpsk2 handshake (UDP, any port)
  Public key pairs (no PKI, no certificates)
  Only: ChaCha20-Poly1305
  Only: Curve25519 ECDH
  Only: BLAKE2s
  Transport data uses same AEAD
  Runs in kernel or userspace
```

### Performance Comparison

```
Test: 1 Gbps throughput, 1400-byte packets, 4-core Intel Xeon

                  Throughput    CPU Usage    Latency
  WireGuard:      ~950 Mbps     25%          0.3ms
  IPSec (AES-NI): ~830 Mbps     40%          0.6ms
  OpenVPN:        ~250 Mbps     90%          1.2ms

(Figures vary by hardware; WireGuard is consistently fastest)
```

### Code Size Comparison

```
  WireGuard:  ~4,000 lines (kernel module + userspace tools)
  OpenVPN:    ~70,000 lines
  strongSwan: ~300,000 lines (IPSec implementation)

Fewer lines = smaller attack surface = easier to audit
WireGuard's kernel module was formally verified using Tamarin Prover
```

### Security Properties Comparison

```
Property               WireGuard   OpenVPN   IPSec
─────────────────────────────────────────────────────
Forward Secrecy        YES         YES       YES (IKEv2)
Identity Hiding        YES (init)  NO        Partial
Crypto Agility         NO (good!)  YES       YES
Post-Quantum PSK       YES         NO        Partial
Replay Protection      YES         YES       YES
DoS Resistance         YES (cookie) Partial  Partial
Formal Verification    YES         NO        Partial
No PKI Required        YES         NO        Partial (PSK)
```

---

## 13. Threat Model and Security Properties

### What WireGuard Protects Against

1. **Passive eavesdropping**: All data is encrypted with ChaCha20-Poly1305.
2. **Active tampering**: AEAD authentication tag detects any modification.
3. **Replay attacks**: 64-bit counter + sliding window bitmap.
4. **Man-in-the-middle**: Public key pinning (you configure peer's public key explicitly).
5. **Identity disclosure to eavesdropper**: Initiator's identity encrypted.
6. **Future compromise of static keys**: Ephemeral keys provide forward secrecy.
7. **DoS amplification**: Cookie mechanism requires IP reachability proof.
8. **Port scanning**: WireGuard does not respond to unauthenticated packets.

### What WireGuard Does NOT Protect Against

1. **Compromise of the running system**: If an attacker has kernel access, all is lost.
2. **Traffic analysis**: Packet timing and sizes can reveal communication patterns (only partially mitigated by padding).
3. **Quantum computers (long-term)**: Curve25519 is vulnerable to Shor's algorithm. The PSK provides **partial** post-quantum security (must also compromise PSK).
4. **Endpoint identity beyond public keys**: No certificate revocation, no OCSP.
5. **DNS leaks**: WireGuard is a layer-3 VPN; DNS queries may bypass the tunnel if misconfigured.

### The "Silent" Property

WireGuard is **completely silent** to anyone who doesn't know your public key.

If you receive a UDP packet on WireGuard's port that doesn't pass MAC1 validation:
→ **Drop silently. No response. No ICMP error. Nothing.**

To a port scanner, WireGuard looks like a closed port.

```
Port scanner:
  send UDP to port 51820
  [WireGuard: MAC1 invalid, DROP silently]
  port scanner receives: nothing
  conclusion: port closed or filtered

Legitimate peer:
  send MSG1 with valid MAC1
  [WireGuard: MAC1 valid, process handshake]
  receive MSG2
  conclusion: port open, WireGuard running
```

---

## 14. C Implementation — From Scratch

This is a **pedagogical, simplified** implementation showing the core concepts. Production use requires the full `wireguard-tools` and kernel module.

### Project Structure

```
wireguard_demo/
├── main.c
├── crypto/
│   ├── curve25519.c     -- Curve25519 ECDH
│   ├── curve25519.h
│   ├── chacha20poly1305.c -- AEAD cipher
│   ├── chacha20poly1305.h
│   ├── blake2s.c        -- Hash function
│   ├── blake2s.h
│   └── noise.c          -- Noise protocol state machine
│   └── noise.h
├── wireguard/
│   ├── handshake.c      -- Message 1 and 2 processing
│   ├── handshake.h
│   ├── session.c        -- Session management
│   ├── session.h
│   ├── allowedips.c     -- Routing table
│   ├── allowedips.h
│   └── replay.c         -- Anti-replay window
│   └── replay.h
└── Makefile
```

### Core Types and Constants (noise.h)

```c
/* wireguard_demo/crypto/noise.h */
#ifndef NOISE_H
#define NOISE_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

/* ─── Sizes ───────────────────────────────────────────────── */
#define NOISE_KEY_LEN           32   /* Curve25519 key length (bytes) */
#define NOISE_HASH_LEN          32   /* BLAKE2s-256 output (bytes)    */
#define NOISE_SYMMETRIC_KEY_LEN 32   /* ChaCha20 key (bytes)          */
#define NOISE_AEAD_TAG_LEN      16   /* Poly1305 tag (bytes)          */
#define NOISE_TIMESTAMP_LEN     12   /* TAI64N timestamp (bytes)      */
#define NOISE_NONCE_LEN         12   /* AEAD nonce (bytes)            */

/* ─── WireGuard Message Types ─────────────────────────────── */
#define WG_MSG_INITIATION       1
#define WG_MSG_RESPONSE         2
#define WG_MSG_COOKIE_REPLY     3
#define WG_MSG_TRANSPORT        4

/* ─── WireGuard Timers (seconds) ─────────────────────────── */
#define REKEY_AFTER_TIME        180
#define REJECT_AFTER_TIME       180
#define REKEY_TIMEOUT           5
#define KEEPALIVE_TIMEOUT       10
#define REKEY_AFTER_MESSAGES    (1ULL << 60)
#define REJECT_AFTER_MESSAGES   ((1ULL << 64) - (1ULL << 13) - 1)

/* ─── Keypair ─────────────────────────────────────────────── */
typedef struct {
    uint8_t private_key[NOISE_KEY_LEN];
    uint8_t public_key[NOISE_KEY_LEN];
    bool    has_private;
} noise_keypair_t;

/* ─── Handshake State ─────────────────────────────────────── */
/*
 * This is the Noise HandshakeState object.
 * 'h'  = handshake hash  (running transcript hash)
 * 'ck' = chaining key    (evolves through each DH operation)
 *
 * Both accumulate cryptographic proof of everything seen so far.
 * At the end, transport keys are derived from 'ck'.
 */
typedef struct {
    /* Local keys */
    noise_keypair_t s;          /* Static key pair */
    noise_keypair_t e;          /* Ephemeral key pair (fresh each handshake) */

    /* Remote keys (known before handshake for static, received during for ephemeral) */
    uint8_t rs[NOISE_KEY_LEN];  /* Remote static public key */
    uint8_t re[NOISE_KEY_LEN];  /* Remote ephemeral public key */

    /* Noise state */
    uint8_t h[NOISE_HASH_LEN];  /* Handshake hash (transcript) */
    uint8_t ck[NOISE_HASH_LEN]; /* Chaining key */

    /* Optional pre-shared key */
    uint8_t psk[NOISE_KEY_LEN];
    bool    has_psk;

    /* Derived transport keys (set after handshake completes) */
    uint8_t tx_key[NOISE_SYMMETRIC_KEY_LEN]; /* Send key  */
    uint8_t rx_key[NOISE_SYMMETRIC_KEY_LEN]; /* Recv key  */
    bool    keys_ready;
} noise_handshake_t;

/* ─── Session (Transport State) ──────────────────────────── */
/*
 * After handshake: we have symmetric keys and counters.
 * Every data packet uses and increments these counters.
 */
typedef struct {
    uint8_t  tx_key[NOISE_SYMMETRIC_KEY_LEN];
    uint8_t  rx_key[NOISE_SYMMETRIC_KEY_LEN];
    uint64_t tx_counter;    /* Nonce for sending  */
    uint64_t rx_counter;    /* Latest received nonce */

    /*
     * Anti-replay bitmap:
     * A sliding window of 2048 bits (256 bytes).
     * Each bit represents whether a packet with that counter has been received.
     * Prevents replay of captured packets.
     */
    uint64_t replay_window[32];  /* 32 * 64 = 2048 bits */
    uint64_t replay_base;        /* Counter value at window start */

    uint32_t local_index;   /* Our index for this session */
    uint32_t remote_index;  /* Remote's index for this session */

    bool     is_valid;
} wg_session_t;

/* ─── Function Declarations ──────────────────────────────── */
int  noise_handshake_init(noise_handshake_t *hs,
                          const noise_keypair_t *local_static,
                          const uint8_t *remote_static_pub);

int  noise_create_initiation(noise_handshake_t *hs,
                              uint8_t *msg_out, size_t *msg_len);

int  noise_consume_initiation(noise_handshake_t *hs,
                               const uint8_t *msg, size_t msg_len);

int  noise_create_response(noise_handshake_t *hs,
                            uint8_t *msg_out, size_t *msg_len);

int  noise_consume_response(noise_handshake_t *hs,
                             const uint8_t *msg, size_t msg_len);

void noise_handshake_zero(noise_handshake_t *hs); /* Zero sensitive memory */

#endif /* NOISE_H */
```

### BLAKE2s Hash (blake2s.h)

```c
/* wireguard_demo/crypto/blake2s.h */
#ifndef BLAKE2S_H
#define BLAKE2S_H

#include <stdint.h>
#include <stddef.h>

#define BLAKE2S_BLOCK_SIZE  64
#define BLAKE2S_HASH_SIZE   32

typedef struct {
    uint32_t h[8];           /* Hash state (8 x 32-bit words) */
    uint32_t t[2];           /* Counter (bytes processed)     */
    uint32_t f[2];           /* Finalization flags            */
    uint8_t  buf[64];        /* Input buffer                  */
    size_t   buflen;         /* Bytes in buffer               */
    uint8_t  outlen;         /* Desired output length         */
} blake2s_state_t;

/*
 * blake2s(): One-shot hash of 'input' (ilen bytes) into 'out' (outlen bytes).
 * blake2s_keyed(): Keyed hash (acts like HMAC but faster).
 * blake2s_hmac(): HMAC-BLAKE2s for KDF operations.
 */
void blake2s(uint8_t *out, size_t outlen,
             const uint8_t *input, size_t ilen);

void blake2s_keyed(uint8_t *out, size_t outlen,
                   const uint8_t *key, size_t keylen,
                   const uint8_t *input, size_t ilen);

/*
 * HKDF using BLAKE2s:
 *   prk = HMAC-BLAKE2s(salt, ikm)
 *   okm[0] = HMAC-BLAKE2s(prk, "" || 0x01)
 *   okm[1] = HMAC-BLAKE2s(prk, okm[0] || 0x02)
 *   okm[2] = HMAC-BLAKE2s(prk, okm[1] || 0x03)
 */
void blake2s_hkdf(const uint8_t *ck, size_t ck_len,
                  const uint8_t *ikm, size_t ikm_len,
                  uint8_t *out1,      /* First 32-byte output  */
                  uint8_t *out2,      /* Second 32-byte output (or NULL) */
                  uint8_t *out3);     /* Third 32-byte output  (or NULL) */

#endif /* BLAKE2S_H */
```

### BLAKE2s Implementation (blake2s.c)

```c
/* wireguard_demo/crypto/blake2s.c */
#include "blake2s.h"
#include <string.h>
#include <stdint.h>

/* ─── BLAKE2s Constants ──────────────────────────────────── */
/*
 * Initialization values (IV):
 * First 8 fractional bits of square roots of first 8 primes.
 * Same as SHA-256 IV — this is NOT a backdoor, it's a standard
 * "nothing-up-my-sleeve" constant.
 */
static const uint32_t BLAKE2S_IV[8] = {
    0x6A09E667UL, 0xBB67AE85UL, 0x3C6EF372UL, 0xA54FF53AUL,
    0x510E527FUL, 0x9B05688CUL, 0x1F83D9ABUL, 0x5BE0CD19UL
};

/*
 * Sigma permutations: define the message schedule.
 * Each row tells which message word goes to which position in each round.
 */
static const uint8_t SIGMA[10][16] = {
    { 0, 1, 2, 3, 4, 5, 6, 7, 8, 9,10,11,12,13,14,15 },
    {14,10, 4, 8, 9,15,13, 6, 1,12, 0, 2,11, 7, 5, 3 },
    {11, 8,12, 0, 5, 2,15,13,10,14, 3, 6, 7, 1, 9, 4 },
    { 7, 9, 3, 1,13,12,11,14, 2, 6, 5,10, 4, 0,15, 8 },
    { 9, 0, 5, 7, 2, 4,10,15,14, 1,11,12, 6, 8, 3,13 },
    { 2,12, 6,10, 0,11, 8, 3, 4,13, 7, 5,15,14, 1, 9 },
    {12, 5, 1,15,14,13, 4,10, 0, 7, 6, 3, 9, 2, 8,11 },
    {13,11, 7,14,12, 1, 3, 9, 5, 0,15, 4, 8, 6, 2,10 },
    { 6,15,14, 9,11, 3, 0, 8,12, 2,13, 7, 1, 4,10, 5 },
    {10, 2, 8, 4, 7, 6, 1, 5,15,11, 9,14, 3,12,13, 0 },
};

/* ─── Utility: rotate right ─────────────────────────────── */
static inline uint32_t rotr32(uint32_t x, int n) {
    return (x >> n) | (x << (32 - n));
}

/* ─── G mixing function ──────────────────────────────────── */
/*
 * The core mixing step of BLAKE2s.
 * v[a], v[b], v[c], v[d] are 4 of 16 working variables.
 * x, y are two message words.
 *
 * This diffuses bits through the state — each G application
 * ensures all 4 variables depend on all inputs.
 */
#define G(r, i, a, b, c, d)                          \
    do {                                              \
        a += b + m[SIGMA[r][2*i+0]];                 \
        d ^= a; d = rotr32(d, 16);                   \
        c += d;                                       \
        b ^= c; b = rotr32(b, 12);                   \
        a += b + m[SIGMA[r][2*i+1]];                 \
        d ^= a; d = rotr32(d, 8);                    \
        c += d;                                       \
        b ^= c; b = rotr32(b, 7);                    \
    } while (0)

/* ─── Compression Function ───────────────────────────────── */
/*
 * The compression function processes one 64-byte block.
 * State 'h' (8 words) is mixed with block 'm' (16 words)
 * through 10 rounds of the G mixing function.
 */
static void blake2s_compress(blake2s_state_t *state, const uint8_t *block) {
    uint32_t m[16];
    uint32_t v[16];
    int i;

    /* Load message block as little-endian 32-bit words */
    for (i = 0; i < 16; i++) {
        m[i] = ((uint32_t)block[4*i+0])       |
               ((uint32_t)block[4*i+1] <<  8) |
               ((uint32_t)block[4*i+2] << 16) |
               ((uint32_t)block[4*i+3] << 24);
    }

    /* Initialize working variables v[0..15] */
    for (i = 0; i < 8; i++) {
        v[i]   = state->h[i];
        v[i+8] = BLAKE2S_IV[i];
    }

    /* Mix in counter and flags */
    v[12] ^= state->t[0];   /* low word of byte counter */
    v[13] ^= state->t[1];   /* high word of byte counter */
    v[14] ^= state->f[0];   /* finalization flag */
    v[15] ^= state->f[1];

    /* 10 rounds of mixing */
    for (int r = 0; r < 10; r++) {
        /* Column step: mix columns */
        G(r, 0, v[ 0], v[ 4], v[ 8], v[12]);
        G(r, 1, v[ 1], v[ 5], v[ 9], v[13]);
        G(r, 2, v[ 2], v[ 6], v[10], v[14]);
        G(r, 3, v[ 3], v[ 7], v[11], v[15]);
        /* Diagonal step: mix diagonals */
        G(r, 4, v[ 0], v[ 5], v[10], v[15]);
        G(r, 5, v[ 1], v[ 6], v[11], v[12]);
        G(r, 6, v[ 2], v[ 7], v[ 8], v[13]);
        G(r, 7, v[ 3], v[ 4], v[ 9], v[14]);
    }

    /* XOR working variables back into state */
    for (i = 0; i < 8; i++) {
        state->h[i] ^= v[i] ^ v[i+8];
    }
}

/* ─── Public API ─────────────────────────────────────────── */
static void blake2s_init_internal(blake2s_state_t *s,
                                  const uint8_t *key, size_t keylen,
                                  size_t outlen) {
    int i;
    memset(s, 0, sizeof(*s));

    /* Copy IV into state */
    for (i = 0; i < 8; i++) s->h[i] = BLAKE2S_IV[i];

    /* Parameter block: XOR with IV
     * Byte 0: digest length
     * Byte 1: key length
     * Byte 2: fanout = 1 (sequential mode)
     * Byte 3: depth = 1 (sequential mode)
     */
    s->h[0] ^= 0x01010000U | ((uint32_t)keylen << 8) | (uint32_t)outlen;
    s->outlen = (uint8_t)outlen;

    if (keylen > 0) {
        /* Key is padded to a full 64-byte block */
        uint8_t block[64] = {0};
        memcpy(block, key, keylen);
        s->buflen = 64;
        memcpy(s->buf, block, 64);
    }
}

void blake2s(uint8_t *out, size_t outlen,
             const uint8_t *input, size_t ilen) {
    blake2s_state_t s;
    blake2s_init_internal(&s, NULL, 0, outlen);

    /* Process full blocks */
    size_t offset = 0;

    /* If there's leftover in buf from key, process it first */
    if (s.buflen > 0) {
        /* Key block handling - simplified: buffer the key block */
        /* In full impl, we'd compress the key block here */
    }

    while (ilen > 0) {
        size_t take = ilen > 64 ? 64 : ilen;
        if (s.buflen + take > 64) {
            /* Compress current buffer */
            s.t[0] += 64;
            if (s.t[0] < 64) s.t[1]++;
            blake2s_compress(&s, s.buf);
            s.buflen = 0;
        }
        memcpy(s.buf + s.buflen, input + offset, take);
        s.buflen += take;
        offset   += take;
        ilen     -= take;
    }

    /* Final block with finalization flag set */
    s.t[0] += (uint32_t)s.buflen;
    if (s.t[0] < s.buflen) s.t[1]++;
    s.f[0] = 0xFFFFFFFFUL;
    memset(s.buf + s.buflen, 0, 64 - s.buflen);
    blake2s_compress(&s, s.buf);

    /* Output little-endian words */
    for (size_t i = 0; i < outlen; i++) {
        out[i] = (uint8_t)(s.h[i/4] >> (8 * (i % 4)));
    }

    /* Zero sensitive state */
    memset(&s, 0, sizeof(s));
}

void blake2s_keyed(uint8_t *out, size_t outlen,
                   const uint8_t *key, size_t keylen,
                   const uint8_t *input, size_t ilen) {
    blake2s_state_t s;
    blake2s_init_internal(&s, key, keylen, outlen);
    /* Process input same as blake2s() above */
    /* Simplified: calling blake2s with key mixed in */
    (void)input; (void)ilen; /* Full impl omitted for clarity */

    /*
     * NOTE: A production implementation would fully implement
     * the keyed variant. See libsodium or the reference implementation.
     * This structure shows the API and intent.
     */
}

/*
 * HKDF-BLAKE2s:
 * WireGuard uses HKDF with BLAKE2s-HMAC as the PRF.
 *
 * KDF1(ck, input) -> (ck', key)
 * KDF2(ck, input) -> (ck', key1, key2)
 * KDF3(ck, input) -> (ck', key1, key2, key3)
 */
void blake2s_hkdf(const uint8_t *ck, size_t ck_len,
                  const uint8_t *ikm, size_t ikm_len,
                  uint8_t *out1, uint8_t *out2, uint8_t *out3) {
    uint8_t prk[32];
    uint8_t tmp[32];
    uint8_t counter;

    /*
     * Extract phase:
     * prk = HMAC-BLAKE2s(ck, ikm)
     *
     * HMAC(key, msg):
     *   inner = BLAKE2s_keyed(key, msg)
     *   outer = BLAKE2s_keyed(key, inner)   <- simplified; real HMAC has ipad/opad
     */
    blake2s_keyed(prk, 32, ck, ck_len, ikm, ikm_len);

    /*
     * Expand phase:
     * T(1) = HMAC(prk, 0x01)
     * T(2) = HMAC(prk, T(1) || 0x02)
     * T(3) = HMAC(prk, T(2) || 0x03)
     */
    if (out1) {
        counter = 0x01;
        blake2s_keyed(out1, 32, prk, 32, &counter, 1);
    }
    if (out2) {
        uint8_t in2[33];
        memcpy(in2, out1, 32);
        in2[32] = 0x02;
        blake2s_keyed(out2, 32, prk, 32, in2, 33);
    }
    if (out3) {
        uint8_t in3[33];
        memcpy(in3, out2, 32);
        in3[32] = 0x03;
        blake2s_keyed(out3, 32, prk, 32, in3, 33);
    }

    /* Zero intermediate state */
    memset(prk, 0, 32);
    memset(tmp, 0, 32);
}
```

### ChaCha20-Poly1305 AEAD (chacha20poly1305.h + .c)

```c
/* wireguard_demo/crypto/chacha20poly1305.h */
#ifndef CHACHA20POLY1305_H
#define CHACHA20POLY1305_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

/*
 * Encrypt plaintext using ChaCha20-Poly1305 AEAD.
 *
 * Parameters:
 *   key     : 32-byte symmetric key
 *   nonce   : 12-byte nonce (MUST be unique per key)
 *   aad     : Additional Authenticated Data (not encrypted, but authenticated)
 *   aad_len : Length of AAD
 *   plain   : Plaintext to encrypt
 *   plain_len: Plaintext length
 *   cipher  : Output buffer (at least plain_len + 16 bytes)
 *             Format: [ciphertext][16-byte Poly1305 tag]
 *
 * Returns: 0 on success
 */
int chacha20poly1305_encrypt(
    const uint8_t key[32],
    const uint8_t nonce[12],
    const uint8_t *aad, size_t aad_len,
    const uint8_t *plain, size_t plain_len,
    uint8_t *cipher  /* out: plain_len + 16 bytes */
);

/*
 * Decrypt and authenticate a ChaCha20-Poly1305 ciphertext.
 *
 * Parameters:
 *   cipher_len includes the 16-byte tag: cipher_len = plaintext_len + 16
 *
 * Returns: 0 on success, -1 if authentication failed (tampered data)
 *
 * SECURITY: If this returns -1, the output buffer contains garbage.
 *           NEVER use the output if this returns -1.
 */
int chacha20poly1305_decrypt(
    const uint8_t key[32],
    const uint8_t nonce[12],
    const uint8_t *aad, size_t aad_len,
    const uint8_t *cipher, size_t cipher_len,
    uint8_t *plain  /* out: cipher_len - 16 bytes */
);

#endif /* CHACHA20POLY1305_H */
```

```c
/* wireguard_demo/crypto/chacha20poly1305.c */
#include "chacha20poly1305.h"
#include <string.h>
#include <stdint.h>

/*
 * ═══════════════════════════════════════════════════════════════
 *  ChaCha20 Stream Cipher
 * ═══════════════════════════════════════════════════════════════
 *
 * ChaCha20 is a stream cipher. It generates a pseudorandom keystream
 * from a 256-bit key and a 96-bit nonce, then XORs the keystream
 * with the plaintext.
 *
 * Internal state: 16 x 32-bit words (512 bits total)
 *   - 4 words: constant "expa nd 3 2-by te k"
 *   - 8 words: 256-bit key
 *   - 1 word:  32-bit block counter
 *   - 3 words: 96-bit nonce
 *
 * State layout:
 *   [c0][c1][c2][c3]    <- "expa nd 3 2-by te k" (constants)
 *   [k0][k1][k2][k3]    <- key bytes 0-15
 *   [k4][k5][k6][k7]    <- key bytes 16-31
 *   [ct][n0][n1][n2]    <- counter + nonce
 */

/* Load 32-bit little-endian */
static inline uint32_t load32_le(const uint8_t *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

/* Store 32-bit little-endian */
static inline void store32_le(uint8_t *p, uint32_t v) {
    p[0] = v & 0xFF; p[1] = (v >> 8) & 0xFF;
    p[2] = (v >> 16) & 0xFF; p[3] = (v >> 24) & 0xFF;
}

static inline uint32_t rotl32(uint32_t x, int n) {
    return (x << n) | (x >> (32 - n));
}

/*
 * The Quarter Round: core of ChaCha20.
 * Mixes 4 words a, b, c, d using ADD, XOR, ROTATE (ARX design).
 * ARX = Addition, Rotation, XOR — no S-boxes, constant time.
 */
#define QUARTERROUND(a, b, c, d)   \
    a += b; d ^= a; d = rotl32(d, 16); \
    c += d; b ^= c; b = rotl32(b, 12); \
    a += b; d ^= a; d = rotl32(d,  8); \
    c += d; b ^= c; b = rotl32(b,  7);

/* Generate one 64-byte ChaCha20 block */
static void chacha20_block(uint32_t state[16], uint8_t out[64]) {
    uint32_t x[16];
    int i;

    memcpy(x, state, 64);

    /*
     * 20 rounds = 10 "double rounds"
     * Each double round: 4 column rounds + 4 diagonal rounds
     * Column rounds mix state columns,
     * Diagonal rounds mix diagonals.
     * Together: full avalanche in 20 rounds.
     */
    for (i = 0; i < 10; i++) {
        /* Column rounds */
        QUARTERROUND(x[ 0], x[ 4], x[ 8], x[12]);
        QUARTERROUND(x[ 1], x[ 5], x[ 9], x[13]);
        QUARTERROUND(x[ 2], x[ 6], x[10], x[14]);
        QUARTERROUND(x[ 3], x[ 7], x[11], x[15]);
        /* Diagonal rounds */
        QUARTERROUND(x[ 0], x[ 5], x[10], x[15]);
        QUARTERROUND(x[ 1], x[ 6], x[11], x[12]);
        QUARTERROUND(x[ 2], x[ 7], x[ 8], x[13]);
        QUARTERROUND(x[ 3], x[ 4], x[ 9], x[14]);
    }

    /* Add original state to scrambled state */
    for (i = 0; i < 16; i++) {
        x[i] += state[i];
    }

    /* Store as little-endian bytes */
    for (i = 0; i < 16; i++) {
        store32_le(out + 4*i, x[i]);
    }

    /* Increment block counter */
    state[12]++;
}

/*
 * ═══════════════════════════════════════════════════════════════
 *  Poly1305 MAC
 * ═══════════════════════════════════════════════════════════════
 *
 * Poly1305 is a MAC (Message Authentication Code).
 * It computes a 128-bit authentication tag over any message.
 *
 * Mathematical basis: polynomial evaluation over GF(2^130 - 5)
 *   tag = (r * m + s) mod (2^130 - 5)
 *
 * r: 16-byte key, clamped (certain bits zeroed for security)
 * s: 16-byte key, used as final addition
 * m: message split into 17-byte blocks (with a high bit set)
 *
 * The "clamp" operation on r prevents certain attacks.
 */
typedef struct {
    uint32_t r[5];   /* r key, 130-bit representation (5 x 26 bits) */
    uint32_t h[5];   /* accumulator                                  */
    uint32_t pad[4]; /* s key                                        */
} poly1305_state_t;

static void poly1305_init(poly1305_state_t *st,
                           const uint8_t key[32]) {
    /*
     * Clamp r:
     * Zero out certain bits of r to ensure r is in a "safe" subgroup.
     * Bits zeroed: r[3], r[7], r[11], r[15] upper nibbles + specific bits.
     * This is a fixed requirement of the Poly1305 specification.
     */
    st->r[0] = (load32_le(key +  0))       & 0x3FFFFFF;
    st->r[1] = (load32_le(key +  3) >>  2) & 0x3FFFF03;
    st->r[2] = (load32_le(key +  6) >>  4) & 0x3FFC0FF;
    st->r[3] = (load32_le(key +  9) >>  6) & 0x3F03FFF;
    st->r[4] = (load32_le(key + 12) >>  8) & 0x00FFFFF;

    /* Zero accumulator */
    st->h[0] = st->h[1] = st->h[2] = st->h[3] = st->h[4] = 0;

    /* s key (pad) */
    st->pad[0] = load32_le(key + 16);
    st->pad[1] = load32_le(key + 20);
    st->pad[2] = load32_le(key + 24);
    st->pad[3] = load32_le(key + 28);
}

static void poly1305_blocks(poly1305_state_t *st,
                              const uint8_t *m, size_t bytes,
                              uint32_t hibit) {
    /*
     * Process message in 16-byte blocks.
     * hibit = 1<<24 for regular blocks (sets the "high bit" of the 130-bit message)
     * hibit = 0 for the final partial block
     */
    uint32_t r0 = st->r[0], r1 = st->r[1], r2 = st->r[2];
    uint32_t r3 = st->r[3], r4 = st->r[4];
    uint32_t h0 = st->h[0], h1 = st->h[1], h2 = st->h[2];
    uint32_t h3 = st->h[3], h4 = st->h[4];
    uint32_t s1, s2, s3, s4;
    uint64_t d0, d1, d2, d3, d4;

    s1 = r1 * 5; s2 = r2 * 5; s3 = r3 * 5; s4 = r4 * 5;

    while (bytes >= 16) {
        /* Load 16-byte chunk as 130-bit number */
        uint32_t t0 = load32_le(m +  0);
        uint32_t t1 = load32_le(m +  4);
        uint32_t t2 = load32_le(m +  8);
        uint32_t t3 = load32_le(m + 12);

        /* h += m with high bit */
        h0 += (t0)                      & 0x3FFFFFF;
        h1 += (t0 >> 26 | t1 <<  6)    & 0x3FFFFFF;
        h2 += (t1 >> 20 | t2 << 12)    & 0x3FFFFFF;
        h3 += (t2 >> 14 | t3 << 18)    & 0x3FFFFFF;
        h4 += (t3 >>  8)               | hibit;

        /* h = (h * r) mod (2^130 - 5) */
        d0 = (uint64_t)h0*r0 + (uint64_t)h1*s4 + (uint64_t)h2*s3 +
             (uint64_t)h3*s2 + (uint64_t)h4*s1;
        d1 = (uint64_t)h0*r1 + (uint64_t)h1*r0 + (uint64_t)h2*s4 +
             (uint64_t)h3*s3 + (uint64_t)h4*s2;
        d2 = (uint64_t)h0*r2 + (uint64_t)h1*r1 + (uint64_t)h2*r0 +
             (uint64_t)h3*s4 + (uint64_t)h4*s3;
        d3 = (uint64_t)h0*r3 + (uint64_t)h1*r2 + (uint64_t)h2*r1 +
             (uint64_t)h3*r0 + (uint64_t)h4*s4;
        d4 = (uint64_t)h0*r4 + (uint64_t)h1*r3 + (uint64_t)h2*r2 +
             (uint64_t)h3*r1 + (uint64_t)h4*r0;

        /* Carry propagation: reduce mod 2^130-5 */
        h0 = (uint32_t)d0 & 0x3FFFFFF; d1 += d0 >> 26;
        h1 = (uint32_t)d1 & 0x3FFFFFF; d2 += d1 >> 26;
        h2 = (uint32_t)d2 & 0x3FFFFFF; d3 += d2 >> 26;
        h3 = (uint32_t)d3 & 0x3FFFFFF; d4 += d3 >> 26;
        h4 = (uint32_t)d4 & 0x3FFFFFF;
        h0 += (uint32_t)(d4 >> 26) * 5;  /* mod 2^130-5 */
        h1 += h0 >> 26; h0 &= 0x3FFFFFF;

        m     += 16;
        bytes -= 16;
    }

    st->h[0] = h0; st->h[1] = h1; st->h[2] = h2;
    st->h[3] = h3; st->h[4] = h4;
}

static void poly1305_finish(poly1305_state_t *st, uint8_t mac[16]) {
    uint32_t h0 = st->h[0], h1 = st->h[1], h2 = st->h[2];
    uint32_t h3 = st->h[3], h4 = st->h[4];
    uint32_t c, mask;
    uint64_t f;

    /* Fully reduce h mod 2^130 - 5 */
    c = h1 >> 26; h1 &= 0x3FFFFFF;
    h2 += c; c = h2 >> 26; h2 &= 0x3FFFFFF;
    h3 += c; c = h3 >> 26; h3 &= 0x3FFFFFF;
    h4 += c; c = h4 >> 26; h4 &= 0x3FFFFFF;
    h0 += c * 5; c = h0 >> 26; h0 &= 0x3FFFFFF;
    h1 += c;

    /* Compute h + -p where p = 2^130 - 5 */
    uint32_t g0 = h0 + 5;
    c  = g0 >> 26; g0 &= 0x3FFFFFF;
    uint32_t g1 = h1 + c; c = g1 >> 26; g1 &= 0x3FFFFFF;
    uint32_t g2 = h2 + c; c = g2 >> 26; g2 &= 0x3FFFFFF;
    uint32_t g3 = h3 + c; c = g3 >> 26; g3 &= 0x3FFFFFF;
    uint32_t g4 = h4 + c - (1 << 26);

    /* Select h if h < p, else h + (-p) */
    mask = (g4 >> 31) - 1;  /* 0xFFFFFFFF if g4 positive (h >= p), else 0 */
    g0 &= mask; g1 &= mask; g2 &= mask; g3 &= mask; g4 &= mask;
    mask = ~mask;
    h0 = (h0 & mask) | g0;
    h1 = (h1 & mask) | g1;
    h2 = (h2 & mask) | g2;
    h3 = (h3 & mask) | g3;
    h4 = (h4 & mask) | g4;

    /* Convert from 5 x 26-bit to 4 x 32-bit, add s (pad) */
    h0 = (h0 | (h1 << 26));
    h1 = (h1 >> 6) | (h2 << 20);
    h2 = (h2 >> 12) | (h3 << 14);
    h3 = (h3 >> 18) | (h4 <<  8);

    f = (uint64_t)h0 + st->pad[0]; h0 = (uint32_t)f;
    f = (uint64_t)h1 + st->pad[1] + (f >> 32); h1 = (uint32_t)f;
    f = (uint64_t)h2 + st->pad[2] + (f >> 32); h2 = (uint32_t)f;
    f = (uint64_t)h3 + st->pad[3] + (f >> 32); h3 = (uint32_t)f;

    store32_le(mac +  0, h0);
    store32_le(mac +  4, h1);
    store32_le(mac +  8, h2);
    store32_le(mac + 12, h3);

    /* Zero state */
    memset(st, 0, sizeof(*st));
}

/*
 * ═══════════════════════════════════════════════════════════════
 *  ChaCha20-Poly1305 AEAD Construction
 * ═══════════════════════════════════════════════════════════════
 *
 * Combining ChaCha20 (encryption) with Poly1305 (authentication):
 *
 * Key derivation:
 *   poly_key = ChaCha20(key, nonce, counter=0)[0..31]  <- first 32 bytes of keystream
 *   ciphertext = ChaCha20(key, nonce, counter=1) XOR plaintext
 *
 * Authentication:
 *   mac_data = aad || pad(aad) || ciphertext || pad(ciphertext) ||
 *              len(aad) as 8 bytes LE || len(ciphertext) as 8 bytes LE
 *   tag = Poly1305(poly_key, mac_data)
 *
 * The padding aligns to 16-byte boundaries (pad = zeros to next multiple of 16)
 */

static void poly1305_pad_and_len(poly1305_state_t *st,
                                  const uint8_t *data, size_t len) {
    poly1305_blocks(st, data, len, (1 << 24));
    if (len % 16) {
        uint8_t pad[16] = {0};
        poly1305_blocks(st, pad, 16 - (len % 16), (1 << 24));
    }
}

int chacha20poly1305_encrypt(
    const uint8_t key[32],
    const uint8_t nonce[12],
    const uint8_t *aad, size_t aad_len,
    const uint8_t *plain, size_t plain_len,
    uint8_t *cipher)
{
    uint32_t state[16];
    uint8_t  block[64];
    uint8_t  poly_key[32];
    size_t   i;

    /* ── Initialize ChaCha20 state ────────────────────────── */
    /* Constants: "expa nd 3 2-by te k" as four 32-bit LE words */
    state[0] = 0x61707865UL;  /* "expa" */
    state[1] = 0x3320646EUL;  /* "nd 3" */
    state[2] = 0x79622D32UL;  /* "2-by" */
    state[3] = 0x6B206574UL;  /* "te k" */

    /* Key */
    for (i = 0; i < 8; i++) state[4+i] = load32_le(key + 4*i);

    /* Counter = 0 (to generate Poly1305 key) */
    state[12] = 0;

    /* Nonce */
    state[13] = load32_le(nonce + 0);
    state[14] = load32_le(nonce + 4);
    state[15] = load32_le(nonce + 8);

    /* ── Generate Poly1305 key (first keystream block) ────── */
    chacha20_block(state, block);
    memcpy(poly_key, block, 32);  /* First 32 bytes of block 0 */

    /* ── Encrypt plaintext (counter starts at 1) ──────────── */
    /* state[12] was incremented to 1 by chacha20_block */
    size_t offset = 0;
    while (offset < plain_len) {
        size_t take = plain_len - offset;
        chacha20_block(state, block);
        if (take > 64) take = 64;
        for (i = 0; i < take; i++) {
            cipher[offset + i] = plain[offset + i] ^ block[i];
        }
        offset += take;
    }

    /* ── Compute Poly1305 tag ────────────────────────────── */
    poly1305_state_t poly;
    poly1305_init(&poly, poly_key);

    /* MAC covers: aad (padded) || ciphertext (padded) || lengths */
    poly1305_pad_and_len(&poly, aad, aad_len);
    poly1305_pad_and_len(&poly, cipher, plain_len);

    /* Append lengths as 8-byte LE */
    uint8_t lengths[16];
    store32_le(lengths + 0, (uint32_t)aad_len);       lengths[4]=0;
    lengths[5]=0; lengths[6]=0; lengths[7]=0;
    store32_le(lengths + 8, (uint32_t)plain_len);      lengths[12]=0;
    lengths[13]=0; lengths[14]=0; lengths[15]=0;
    poly1305_blocks(&poly, lengths, 16, (1 << 24));

    /* Finalize: write tag after ciphertext */
    poly1305_finish(&poly, cipher + plain_len);

    /* Zero sensitive intermediates */
    memset(block, 0, 64);
    memset(poly_key, 0, 32);
    return 0;
}

int chacha20poly1305_decrypt(
    const uint8_t key[32],
    const uint8_t nonce[12],
    const uint8_t *aad, size_t aad_len,
    const uint8_t *cipher, size_t cipher_len,
    uint8_t *plain)
{
    if (cipher_len < 16) return -1;  /* Too short to have tag */

    size_t   ct_len = cipher_len - 16;
    uint32_t state[16];
    uint8_t  block[64];
    uint8_t  poly_key[32];
    uint8_t  expected_tag[16];
    size_t   i;

    /* Same state init as encrypt */
    state[0] = 0x61707865UL; state[1] = 0x3320646EUL;
    state[2] = 0x79622D32UL; state[3] = 0x6B206574UL;
    for (i = 0; i < 8; i++) state[4+i] = load32_le(key + 4*i);
    state[12] = 0;
    state[13] = load32_le(nonce + 0);
    state[14] = load32_le(nonce + 4);
    state[15] = load32_le(nonce + 8);

    /* Generate Poly1305 key */
    chacha20_block(state, block);
    memcpy(poly_key, block, 32);

    /* Compute expected tag over ciphertext */
    poly1305_state_t poly;
    poly1305_init(&poly, poly_key);
    poly1305_pad_and_len(&poly, aad, aad_len);
    poly1305_pad_and_len(&poly, cipher, ct_len);
    uint8_t lengths[16];
    store32_le(lengths + 0, (uint32_t)aad_len);
    memset(lengths + 4, 0, 4);
    store32_le(lengths + 8, (uint32_t)ct_len);
    memset(lengths + 12, 0, 4);
    poly1305_blocks(&poly, lengths, 16, (1 << 24));
    poly1305_finish(&poly, expected_tag);

    /*
     * Constant-time tag comparison.
     * CRITICAL: Never use memcmp() for MAC comparison.
     * memcmp() may short-circuit on first mismatch, leaking timing info.
     * An attacker can use this timing to forge MACs byte by byte.
     */
    uint8_t diff = 0;
    for (i = 0; i < 16; i++) {
        diff |= expected_tag[i] ^ cipher[ct_len + i];
    }
    if (diff != 0) {
        memset(block, 0, 64);
        memset(poly_key, 0, 32);
        return -1;  /* Authentication failed: tampered data */
    }

    /* Decrypt (counter starts at 1 after poly key gen) */
    size_t offset = 0;
    while (offset < ct_len) {
        size_t take = ct_len - offset;
        chacha20_block(state, block);
        if (take > 64) take = 64;
        for (i = 0; i < take; i++) {
            plain[offset + i] = cipher[offset + i] ^ block[i];
        }
        offset += take;
    }

    memset(block, 0, 64);
    memset(poly_key, 0, 32);
    return 0;
}
```

### Handshake Implementation (handshake.c)

```c
/* wireguard_demo/wireguard/handshake.c */
#include "handshake.h"
#include "../crypto/blake2s.h"
#include "../crypto/chacha20poly1305.h"
#include <string.h>
#include <time.h>
#include <stdio.h>

/*
 * WireGuard protocol constants
 */
static const char CONSTRUCTION[] = "Noise_IKpsk2_25519_ChaChaPoly_BLAKE2s";
static const char IDENTIFIER[]   = "WireGuard v1 zx2c4 Jason@zx2c4.com";
static const char LABEL_MAC1[]   = "mac1----";
static const char LABEL_COOKIE[] = "cookie--";

/* ── Helper: MixHash ─────────────────────────────────────────
 * h = BLAKE2s(h || data)
 * This extends the handshake transcript with new data.
 */
static void mix_hash(uint8_t h[32], const uint8_t *data, size_t len) {
    uint8_t combined[32 + len];  /* VLA — avoid in production; use heap */
    memcpy(combined,      h,    32);
    memcpy(combined + 32, data, len);
    blake2s(h, 32, combined, 32 + len);
}

/* ── Helper: MixKey ──────────────────────────────────────────
 * Advances the chaining key ck using HKDF with new DH output.
 * ck' = HKDF_extract(ck, input)
 */
static void mix_key(uint8_t ck[32], const uint8_t *input, size_t len) {
    uint8_t new_ck[32];
    blake2s_hkdf(ck, 32, input, len, new_ck, NULL, NULL);
    memcpy(ck, new_ck, 32);
    memset(new_ck, 0, 32);
}

/* ── Helper: TAI64N timestamp ────────────────────────────────
 * WireGuard uses TAI64N: 64-bit seconds + 32-bit nanoseconds
 * Both big-endian (network byte order).
 */
static void tai64n_now(uint8_t ts[12]) {
    struct timespec t;
    clock_gettime(CLOCK_REALTIME, &t);

    /* TAI64 epoch: seconds since 1970-01-01 + 10 seconds (TAI-UTC offset approx) */
    uint64_t sec = (uint64_t)t.tv_sec + 0x400000000000000aULL;
    uint32_t nsec = (uint32_t)t.tv_nsec;

    /* Big-endian encoding */
    ts[0]  = (sec >> 56) & 0xFF; ts[1]  = (sec >> 48) & 0xFF;
    ts[2]  = (sec >> 40) & 0xFF; ts[3]  = (sec >> 32) & 0xFF;
    ts[4]  = (sec >> 24) & 0xFF; ts[5]  = (sec >> 16) & 0xFF;
    ts[6]  = (sec >>  8) & 0xFF; ts[7]  = (sec >>  0) & 0xFF;
    ts[8]  = (nsec >> 24) & 0xFF; ts[9]  = (nsec >> 16) & 0xFF;
    ts[10] = (nsec >>  8) & 0xFF; ts[11] = (nsec >>  0) & 0xFF;
}

/* ─────────────────────────────────────────────────────────────
 * noise_handshake_init()
 *
 * Initialize the handshake state machine.
 * Call this once per handshake attempt, with the remote's static
 * public key.
 *
 * This sets up ck and h as described in the WireGuard paper:
 *   ck = BLAKE2s("Noise_IKpsk2_25519_ChaChaPoly_BLAKE2s")
 *   h  = BLAKE2s(ck || "WireGuard v1 ...")
 *   h  = BLAKE2s(h || responder_static_pub)
 * ─────────────────────────────────────────────────────────────
 */
int noise_handshake_init(noise_handshake_t *hs,
                          const noise_keypair_t *local_static,
                          const uint8_t *remote_static_pub) {
    if (!hs || !local_static || !remote_static_pub) return -1;

    memset(hs, 0, sizeof(*hs));

    /* Copy local static keys */
    memcpy(hs->s.private_key, local_static->private_key, 32);
    memcpy(hs->s.public_key,  local_static->public_key,  32);
    hs->s.has_private = true;

    /* Copy remote static public key */
    memcpy(hs->rs, remote_static_pub, 32);

    /* ── Initialize chaining key ck ──────────────────────── */
    /* ck = HASH("Noise_IKpsk2_25519_ChaChaPoly_BLAKE2s") */
    blake2s(hs->ck, 32,
            (const uint8_t *)CONSTRUCTION, strlen(CONSTRUCTION));

    /* ── Initialize handshake hash h ─────────────────────── */
    /* h = HASH(ck || "WireGuard v1 zx2c4 Jason@zx2c4.com") */
    {
        uint8_t tmp[32 + sizeof(IDENTIFIER) - 1];
        memcpy(tmp,      hs->ck,     32);
        memcpy(tmp + 32, IDENTIFIER, strlen(IDENTIFIER));
        blake2s(hs->h, 32, tmp, 32 + strlen(IDENTIFIER));
    }

    /* h = HASH(h || R_pub) -- bind responder identity into hash */
    mix_hash(hs->h, remote_static_pub, 32);

    return 0;
}

/* ─────────────────────────────────────────────────────────────
 * noise_create_initiation()
 *
 * Constructs Message 1 (Initiator → Responder).
 * This is the Noise IK pattern:
 *   -> e, es, s, ss
 *
 * Output buffer must be at least 148 bytes.
 * ─────────────────────────────────────────────────────────────
 */
int noise_create_initiation(noise_handshake_t *hs,
                              uint8_t *msg_out, size_t *msg_len_out) {
    uint8_t dh_result[32];
    uint8_t key[32];
    uint8_t ck2[32];

    *msg_len_out = 148;
    memset(msg_out, 0, 148);

    /* Message type */
    msg_out[0] = WG_MSG_INITIATION;
    /* reserved[1..3] = 0 */

    /* sender_index: 4 bytes at offset 4 */
    /* (Should be a random 32-bit value in production) */
    uint32_t sender_idx = 0x12345678;  /* Placeholder */
    memcpy(msg_out + 4, &sender_idx, 4);

    /* ── Step 1: Ephemeral public key ─────────────────────── */
    /*
     * Generate fresh ephemeral key pair.
     * In production: use crypto_random_bytes() or getrandom().
     * Here we use a deterministic placeholder for illustration.
     */
    memset(hs->e.private_key, 0xAA, 32);  /* PLACEHOLDER: use random! */
    /* hs->e.public_key = Curve25519(hs->e.private_key) */
    /* curve25519_generate_public(hs->e.public_key, hs->e.private_key); */
    hs->e.has_private = true;

    /* -> e: send ephemeral public key */
    memcpy(msg_out + 8, hs->e.public_key, 32);  /* offset 8, 32 bytes */

    /* Mix e into hash: h = HASH(h || e.public_key) */
    mix_hash(hs->h, hs->e.public_key, 32);
    /* Mix e into ck: ck = KDF1(ck, e.public_key) */
    mix_key(hs->ck, hs->e.public_key, 32);

    /* ── Step 2: DH(e_priv, rs) — es ─────────────────────── */
    /*
     * Compute ephemeral_initiator × static_responder.
     * This is the "es" Noise token: ephemeral-static DH.
     * Purpose: encrypt our static key under a key only the responder can compute.
     */
    /* curve25519(dh_result, hs->e.private_key, hs->rs); */
    memset(dh_result, 0x55, 32);  /* PLACEHOLDER */

    /* ck, key = KDF2(ck, DH(e, rs)) */
    blake2s_hkdf(hs->ck, 32, dh_result, 32, hs->ck, key, NULL);

    /* ── Step 3: Encrypt static public key ───────────────── */
    /*
     * enc_static = AEAD_Encrypt(key, 0, I_pub, h)
     * 32 bytes of I_pub → 48 bytes (32 + 16-byte tag)
     */
    {
        uint8_t nonce[12] = {0};  /* Counter = 0 */
        chacha20poly1305_encrypt(key, nonce,
                                  hs->h, 32,           /* AAD = h */
                                  hs->s.public_key, 32, /* plaintext */
                                  msg_out + 40);         /* output at offset 40 */
    }

    /* h = HASH(h || encrypted_static) */
    mix_hash(hs->h, msg_out + 40, 48);

    /* ── Step 4: DH(s_priv, rs) — ss ─────────────────────── */
    /* Compute static_initiator × static_responder */
    /* curve25519(dh_result, hs->s.private_key, hs->rs); */
    memset(dh_result, 0x77, 32);  /* PLACEHOLDER */

    /* ck, key = KDF2(ck, DH(s, rs)) */
    blake2s_hkdf(hs->ck, 32, dh_result, 32, hs->ck, key, NULL);

    /* ── Step 5: Encrypt timestamp ───────────────────────── */
    {
        uint8_t ts[12];
        uint8_t nonce[12] = {0};
        tai64n_now(ts);

        chacha20poly1305_encrypt(key, nonce,
                                  hs->h, 32,  /* AAD = h */
                                  ts, 12,      /* plaintext: timestamp */
                                  msg_out + 88); /* output at offset 88 */
    }

    /* h = HASH(h || encrypted_timestamp) */
    mix_hash(hs->h, msg_out + 88, 28);

    /* ── Step 6: Compute MAC1 ─────────────────────────────── */
    /*
     * MAC1 = MAC(HASH("mac1----" || R_pub), msg[0..115])
     * This proves knowledge of the responder's public key.
     * Without R_pub, MAC1 cannot be computed, so random UDP
     * packets cannot pass MAC1 verification.
     */
    {
        uint8_t mac_key[32];
        uint8_t label_and_pub[8 + 32];
        memcpy(label_and_pub,     LABEL_MAC1, 8);
        memcpy(label_and_pub + 8, hs->rs,     32);
        blake2s(mac_key, 32, label_and_pub, 40);

        /* MAC1 = BLAKE2s-128(mac_key, msg[0..115]) */
        blake2s_keyed(msg_out + 116, 16,  /* 16-byte output at offset 116 */
                       mac_key, 32,
                       msg_out, 116);
    }

    /* MAC2 = 0 (no cookie, not under load) */
    memset(msg_out + 132, 0, 16);

    /* Zero sensitive intermediates */
    memset(dh_result, 0, 32);
    memset(key, 0, 32);

    return 0;
}

/* ─────────────────────────────────────────────────────────────
 * noise_handshake_zero()
 * Zero all sensitive material from memory.
 * ─────────────────────────────────────────────────────────────
 */
void noise_handshake_zero(noise_handshake_t *hs) {
    /*
     * Use volatile memset or platform secure_zero (platform-specific)
     * to prevent compiler from optimizing away the zeroing.
     *
     * In production: use explicit_bzero() (Linux) or SecureZeroMemory() (Windows)
     */
    volatile uint8_t *p = (volatile uint8_t *)hs;
    for (size_t i = 0; i < sizeof(*hs); i++) p[i] = 0;
}
```

### Anti-Replay Window (replay.c)

```c
/* wireguard_demo/wireguard/replay.c */
#include "replay.h"
#include <string.h>
#include <stdbool.h>

/*
 * ═══════════════════════════════════════════════════════════════
 *  Anti-Replay Sliding Window
 * ═══════════════════════════════════════════════════════════════
 *
 * Problem: An attacker captures valid encrypted packets and replays them.
 * Without replay protection, the same packet could be processed twice.
 *
 * Solution: Track which packet counters we've already seen.
 *
 * We use a bitmap of WINDOW_SIZE bits.
 * The window tracks the last WINDOW_SIZE packet counters.
 * The "right edge" of the window is the highest counter seen so far.
 *
 * Visual:
 *
 *   ... [bit 2047][bit 2046]...[bit 1][bit 0] = window
 *                                               ^
 *                              window_base (highest seen counter)
 *
 *   If new counter N:
 *     N > window_base + WINDOW_SIZE:
 *       → N is far ahead: slide window, accept
 *     window_base < N <= window_base + WINDOW_SIZE:
 *       → N within window: check bit, accept if not set
 *     N <= window_base:
 *       → N is at or behind right edge:
 *         If N >= (window_base - WINDOW_SIZE): check bit
 *         Else: too old, reject
 */

#define WINDOW_SIZE    2048  /* bits (256 bytes) */
#define WINDOW_WORDS   (WINDOW_SIZE / 64)  /* 32 uint64_t words */

typedef struct {
    uint64_t bitmap[WINDOW_WORDS];
    uint64_t base;        /* Highest counter value seen (right edge) */
    bool     initialized;
} replay_window_t;

/* Check if a counter bit is set in the window */
static bool window_get(replay_window_t *w, uint64_t counter) {
    uint64_t index = counter % WINDOW_SIZE;
    return (w->bitmap[index / 64] >> (index % 64)) & 1;
}

/* Set a counter bit in the window */
static void window_set(replay_window_t *w, uint64_t counter) {
    uint64_t index = counter % WINDOW_SIZE;
    w->bitmap[index / 64] |= (1ULL << (index % 64));
}

/* Clear a range of bits (for sliding window) */
static void window_clear(replay_window_t *w, uint64_t from, uint64_t to) {
    for (uint64_t c = from; c <= to; c++) {
        uint64_t index = c % WINDOW_SIZE;
        w->bitmap[index / 64] &= ~(1ULL << (index % 64));
    }
}

/*
 * replay_check_and_update():
 *
 * Returns: REPLAY_OK      — new packet, counter accepted
 *          REPLAY_REPLAY  — counter already seen (replay!)
 *          REPLAY_OLD     — counter too old (outside window)
 */
replay_result_t replay_check_and_update(replay_window_t *w, uint64_t counter) {
    if (!w->initialized) {
        /* First packet ever: initialize window */
        memset(w->bitmap, 0, sizeof(w->bitmap));
        w->base = counter;
        w->initialized = true;
        window_set(w, counter);
        return REPLAY_OK;
    }

    if (counter > w->base) {
        /* New highest counter: slide window forward */
        uint64_t advance = counter - w->base;
        if (advance >= WINDOW_SIZE) {
            /* Window slid entirely: clear everything */
            memset(w->bitmap, 0, sizeof(w->bitmap));
        } else {
            /* Clear the newly opened positions */
            window_clear(w, w->base + 1, counter);
        }
        w->base = counter;
        window_set(w, counter);
        return REPLAY_OK;

    } else if (counter == w->base) {
        /* Exact duplicate of highest seen */
        return REPLAY_REPLAY;

    } else {
        /* counter < w->base */
        uint64_t behind = w->base - counter;

        if (behind >= WINDOW_SIZE) {
            /* Too old: outside window */
            return REPLAY_OLD;
        }

        /* Within window: check if already seen */
        if (window_get(w, counter)) {
            return REPLAY_REPLAY;
        }

        /* New packet, within window */
        window_set(w, counter);
        return REPLAY_OK;
    }
}
```

### Main Entry Point (main.c)

```c
/* wireguard_demo/main.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include "crypto/noise.h"
#include "crypto/blake2s.h"
#include "crypto/chacha20poly1305.h"

/*
 * Demo: Simulate a WireGuard handshake between Alice (initiator)
 * and Bob (responder).
 *
 * In real WireGuard:
 *  - Keys are loaded from /etc/wireguard/wg0.conf
 *  - UDP socket binds to port 51820
 *  - TUN device created with ip tuntap add mode tun wg0
 *
 * Here we simulate both sides in the same process.
 */

static void print_hex(const char *label, const uint8_t *data, size_t len) {
    printf("  %-30s: ", label);
    for (size_t i = 0; i < len; i++) {
        printf("%02x", data[i]);
        if (i % 32 == 31 && i != len-1) printf("\n%34s", "");
    }
    printf("\n");
}

int main(void) {
    printf("╔══════════════════════════════════════════════════╗\n");
    printf("║     WireGuard Protocol Demo (C Implementation)   ║\n");
    printf("╚══════════════════════════════════════════════════╝\n\n");

    /* ── Key Setup ──────────────────────────────────────────── */
    /*
     * In real use:
     *   wg genkey | tee privatekey | wg pubkey > publickey
     *
     * Here we use placeholder keys for demo purposes.
     * In production: use libsodium's crypto_box_keypair() or
     * the Curve25519 key generation.
     */
    noise_keypair_t alice_static = {
        .private_key = {
            0xa0,0xa1,0xa2,0xa3,0xa4,0xa5,0xa6,0xa7,
            0xa8,0xa9,0xaa,0xab,0xac,0xad,0xae,0xaf,
            0xb0,0xb1,0xb2,0xb3,0xb4,0xb5,0xb6,0xb7,
            0xb8,0xb9,0xba,0xbb,0xbc,0xbd,0xbe,0xbf,
        },
        .has_private = true,
    };

    noise_keypair_t bob_static = {
        .private_key = {
            0xc0,0xc1,0xc2,0xc3,0xc4,0xc5,0xc6,0xc7,
            0xc8,0xc9,0xca,0xcb,0xcc,0xcd,0xce,0xcf,
            0xd0,0xd1,0xd2,0xd3,0xd4,0xd5,0xd6,0xd7,
            0xd8,0xd9,0xda,0xdb,0xdc,0xdd,0xde,0xdf,
        },
        .has_private = true,
    };

    /* Derive public keys (simplified: in real Curve25519, multiply private by base point G) */
    /* Placeholder: copy lower bytes of private for demo */
    memcpy(alice_static.public_key, alice_static.private_key, 32);
    alice_static.public_key[0] ^= 0x80; /* differentiate */
    memcpy(bob_static.public_key, bob_static.private_key, 32);
    bob_static.public_key[0] ^= 0x80;

    printf("Alice (Initiator):\n");
    print_hex("Private Key", alice_static.private_key, 32);
    print_hex("Public Key",  alice_static.public_key,  32);

    printf("\nBob (Responder):\n");
    print_hex("Private Key", bob_static.private_key, 32);
    print_hex("Public Key",  bob_static.public_key,  32);

    /* ── Initiator: Create Message 1 ────────────────────────── */
    printf("\n─── Phase 1: Initiator sends MSG1 ──────────────────\n");

    noise_handshake_t alice_hs;
    noise_handshake_init(&alice_hs, &alice_static, bob_static.public_key);

    uint8_t msg1[148];
    size_t  msg1_len;
    noise_create_initiation(&alice_hs, msg1, &msg1_len);

    printf("MSG1 constructed (%zu bytes):\n", msg1_len);
    printf("  Type:          0x%02x\n", msg1[0]);
    printf("  Sender Index:  0x%08x\n",
           msg1[4] | (msg1[5]<<8) | (msg1[6]<<16) | (msg1[7]<<24));
    print_hex("Ephemeral Pub",  msg1 + 8,   32);
    print_hex("Enc Static",     msg1 + 40,  48);
    print_hex("Enc Timestamp",  msg1 + 88,  28);
    print_hex("MAC1",           msg1 + 116, 16);

    /* ── Demo: Encrypt/Decrypt a data packet ─────────────────── */
    printf("\n─── Demo: Transport Data Encryption ─────────────────\n");

    /* Simulated session keys (in real WireGuard: derived from handshake) */
    uint8_t session_key[32];
    memset(session_key, 0x42, 32);  /* Placeholder session key */

    /* IP packet payload: a simple ICMP echo request */
    uint8_t ip_packet[] = {
        0x45, 0x00, 0x00, 0x1C,  /* IPv4, IHL=5, TOS=0, Length=28 */
        0x00, 0x01, 0x00, 0x00,  /* ID=1, Flags=0, FragOff=0 */
        0x40, 0x01, 0x00, 0x00,  /* TTL=64, Protocol=ICMP, Checksum=0 */
        0x0A, 0x00, 0x00, 0x01,  /* Src: 10.0.0.1 */
        0x0A, 0x00, 0x00, 0x02,  /* Dst: 10.0.0.2 */
        0x08, 0x00, 0x00, 0x00,  /* ICMP type=8 (echo), code=0 */
        0x00, 0x01, 0x00, 0x00,  /* ID=1, Seq=0 */
    };
    size_t ip_len = sizeof(ip_packet);

    /* Build Type-4 WireGuard header */
    uint8_t wg_packet[32 + ip_len + 16];  /* Header + payload + AEAD tag */
    memset(wg_packet, 0, sizeof(wg_packet));

    wg_packet[0] = WG_MSG_TRANSPORT;  /* type = 4 */
    /* receiver_index (bytes 4-7): which session this belongs to */
    uint32_t receiver_idx = 0xDEADBEEF;
    memcpy(wg_packet + 4, &receiver_idx, 4);

    /* Counter (bytes 8-15): 64-bit little-endian nonce */
    uint64_t counter = 0;
    memcpy(wg_packet + 8, &counter, 8);

    /* Build AEAD nonce from counter */
    uint8_t nonce[12] = {0};
    memcpy(nonce + 4, &counter, 8);  /* bytes 0-3 = 0, bytes 4-11 = counter LE */

    /* Encrypt IP packet → encrypted_encapsulated_packet */
    chacha20poly1305_encrypt(session_key, nonce,
                              NULL, 0,           /* no AAD for transport */
                              ip_packet, ip_len,
                              wg_packet + 32);   /* encrypted output at offset 32 */

    printf("Original IP packet (%zu bytes):\n", ip_len);
    print_hex("IP Packet", ip_packet, ip_len);

    printf("\nWireGuard Type-4 Packet (%zu bytes):\n", sizeof(wg_packet));
    printf("  Type:            0x%02x\n", wg_packet[0]);
    printf("  Receiver Index:  0x%08x\n", receiver_idx);
    printf("  Counter:         %llu\n",   (unsigned long long)counter);
    print_hex("Encrypted Payload", wg_packet + 32, ip_len);
    print_hex("AEAD Tag",          wg_packet + 32 + ip_len, 16);

    /* Decrypt and verify */
    uint8_t decrypted[ip_len];
    int result = chacha20poly1305_decrypt(session_key, nonce,
                                           NULL, 0,
                                           wg_packet + 32, ip_len + 16,
                                           decrypted);

    printf("\nDecryption result: %s\n", result == 0 ? "SUCCESS ✓" : "FAILED ✗");
    if (result == 0) {
        printf("Decrypted matches original: %s\n",
               memcmp(decrypted, ip_packet, ip_len) == 0 ? "YES ✓" : "NO ✗");
    }

    /* Tamper test */
    printf("\n─── Tamper Detection Test ───────────────────────────\n");
    uint8_t tampered[ip_len + 16];
    memcpy(tampered, wg_packet + 32, ip_len + 16);
    tampered[5] ^= 0xFF;  /* Flip a bit in the ciphertext */

    result = chacha20poly1305_decrypt(session_key, nonce,
                                       NULL, 0,
                                       tampered, ip_len + 16,
                                       decrypted);
    printf("Tampered packet decryption: %s\n",
           result == -1 ? "CORRECTLY REJECTED ✓" : "WRONGLY ACCEPTED ✗");

    /* ── Cleanup ─────────────────────────────────────────────── */
    noise_handshake_zero(&alice_hs);
    memset(session_key, 0, 32);
    memset(msg1, 0, 148);

    printf("\n╔══════════════════════════════════════════════════╗\n");
    printf("║            Demo Complete                          ║\n");
    printf("╚══════════════════════════════════════════════════╝\n");
    return 0;
}
```

### Makefile

```makefile
# wireguard_demo/Makefile
CC      = gcc
CFLAGS  = -Wall -Wextra -O2 -std=c11 -g \
          -fsanitize=address,undefined \
          -Icrypto -Iwireguard

SRCS    = main.c \
          crypto/blake2s.c \
          crypto/chacha20poly1305.c \
          wireguard/handshake.c \
          wireguard/replay.c

TARGET  = wireguard_demo

$(TARGET): $(SRCS)
	$(CC) $(CFLAGS) -o $@ $^

clean:
	rm -f $(TARGET) *.o

.PHONY: clean
```

---

## 15. Rust Implementation — Idiomatic and Safe

### Cargo.toml

```toml
[package]
name    = "wireguard-demo"
version = "0.1.0"
edition = "2021"

[dependencies]
# Production-grade, formally verified crypto
chacha20poly1305 = "0.10"      # AEAD cipher
x25519-dalek     = "2.0"       # Curve25519 ECDH
blake2           = "0.10"      # BLAKE2s hash
hkdf             = "0.12"      # HKDF key derivation
hmac             = "0.12"      # HMAC
rand             = "0.8"       # Cryptographic RNG
zeroize          = "1.6"       # Secure memory zeroing
zeroize_derive   = "1.4"

[dev-dependencies]
hex = "0.4"
```

### Core Types (src/types.rs)

```rust
// src/types.rs
//
// Core data types for the WireGuard protocol.
// We use Rust's type system to enforce correctness at compile time.

use zeroize::{Zeroize, ZeroizeOnDrop};

/// Message type constants from the WireGuard spec
#[repr(u8)]
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum MessageType {
    Initiation  = 1,
    Response    = 2,
    CookieReply = 3,
    Transport   = 4,
}

/// A 256-bit (32-byte) symmetric key.
/// ZeroizeOnDrop: memory is automatically zeroed when this value is dropped.
/// This prevents key material from lingering in memory.
#[derive(Clone, Zeroize, ZeroizeOnDrop)]
pub struct SymmetricKey(pub [u8; 32]);

impl SymmetricKey {
    pub fn new(bytes: [u8; 32]) -> Self {
        SymmetricKey(bytes)
    }
    pub fn as_bytes(&self) -> &[u8; 32] {
        &self.0
    }
}

impl std::fmt::Debug for SymmetricKey {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "SymmetricKey([REDACTED])")  // Never log key material
    }
}

/// A 128-bit (16-byte) AEAD authentication tag.
#[derive(Debug, Clone, PartialEq)]
pub struct AeadTag(pub [u8; 16]);

/// A 64-bit packet counter used as AEAD nonce.
/// Wraps a u64 and builds the 12-byte nonce on demand.
#[derive(Debug, Clone, Copy)]
pub struct Counter(pub u64);

impl Counter {
    /// Build the 12-byte AEAD nonce from the counter.
    ///
    /// WireGuard nonce layout:
    ///   bytes 0-3:   0x00000000 (zero)
    ///   bytes 4-11:  counter as little-endian u64
    pub fn to_nonce(self) -> [u8; 12] {
        let mut nonce = [0u8; 12];
        nonce[4..12].copy_from_slice(&self.0.to_le_bytes());
        nonce
    }

    /// Increment counter, returning error on overflow.
    /// Never reuse a counter with the same key!
    pub fn increment(&mut self) -> Result<Counter, WireGuardError> {
        let prev = *self;
        self.0 = self.0.checked_add(1)
            .ok_or(WireGuardError::CounterOverflow)?;
        Ok(prev)
    }
}

/// Errors that can occur in WireGuard operations.
#[derive(Debug)]
pub enum WireGuardError {
    /// AEAD decryption failed: packet was tampered with or key is wrong.
    AuthenticationFailure,
    /// Replay detection: this counter was already seen.
    ReplayDetected,
    /// Counter value too old to be in the replay window.
    CounterTooOld,
    /// Counter wrapped around (should never happen in practice).
    CounterOverflow,
    /// Handshake message was malformed.
    MalformedMessage,
    /// Session has expired and must be renegotiated.
    SessionExpired,
    /// AllowedIPs check failed: source IP not in allowed list.
    NotAllowed,
}

impl std::fmt::Display for WireGuardError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            WireGuardError::AuthenticationFailure =>
                write!(f, "AEAD authentication failed"),
            WireGuardError::ReplayDetected =>
                write!(f, "Replay detected: counter already seen"),
            WireGuardError::CounterTooOld =>
                write!(f, "Counter too old: outside replay window"),
            WireGuardError::CounterOverflow =>
                write!(f, "Counter overflow"),
            WireGuardError::MalformedMessage =>
                write!(f, "Malformed WireGuard message"),
            WireGuardError::SessionExpired =>
                write!(f, "Session expired: needs renegotiation"),
            WireGuardError::NotAllowed =>
                write!(f, "Source IP not in AllowedIPs"),
        }
    }
}
```

### Noise Handshake State (src/noise.rs)

```rust
// src/noise.rs
//
// Implementation of the Noise_IKpsk2 handshake pattern.
//
// Mental Model: Think of the HandshakeState as a "cryptographic accumulator".
// Every operation feeds data into it, and the final state produces keys.
// The hash 'h' proves the transcript hasn't been tampered with.
// The chaining key 'ck' evolves to eventually become the session keys.

use blake2::{Blake2s256, Digest};
use blake2::digest::Mac;
use hkdf::Hkdf;
use hmac::Hmac;
use x25519_dalek::{EphemeralSecret, PublicKey, StaticSecret};
use zeroize::{Zeroize, ZeroizeOnDrop};
use crate::types::{SymmetricKey, WireGuardError};

// ── Protocol Constants ──────────────────────────────────────────────────────

/// The Noise protocol identifier string.
/// Seeds the initial chaining key.
const CONSTRUCTION: &str = "Noise_IKpsk2_25519_ChaChaPoly_BLAKE2s";

/// The WireGuard-specific identifier.
/// Mixed into the hash after initialization.
const IDENTIFIER: &str = "WireGuard v1 zx2c4 Jason@zx2c4.com";

// ── Helper Functions ────────────────────────────────────────────────────────

/// Compute BLAKE2s-256 hash of data.
fn hash(data: &[u8]) -> [u8; 32] {
    let mut h = Blake2s256::new();
    h.update(data);
    h.finalize().into()
}

/// Compute BLAKE2s-256 hash of two concatenated inputs.
/// Avoids allocation by using the Blake2s update API.
fn hash2(a: &[u8], b: &[u8]) -> [u8; 32] {
    let mut h = Blake2s256::new();
    h.update(a);
    h.update(b);
    h.finalize().into()
}

/// HKDF-Extract + single Expand: derive one 32-byte output.
/// KDF1(key, input) -> (new_ck)
fn kdf1(ck: &[u8; 32], input: &[u8]) -> [u8; 32] {
    let hk = Hkdf::<blake2::Blake2s256>::new(Some(ck), input);
    let mut out = [0u8; 32];
    hk.expand(&[], &mut out).expect("HKDF expand failed");
    out
}

/// KDF2(ck, input) -> (new_ck, key)
/// Returns a pair: (new chaining key, derived key)
fn kdf2(ck: &[u8; 32], input: &[u8]) -> ([u8; 32], [u8; 32]) {
    let hk = Hkdf::<blake2::Blake2s256>::new(Some(ck), input);
    let mut ck_new = [0u8; 32];
    let mut key    = [0u8; 32];
    let mut both   = [0u8; 64];
    hk.expand(&[], &mut both).expect("HKDF expand failed");
    ck_new.copy_from_slice(&both[..32]);
    key.copy_from_slice(&both[32..]);
    both.zeroize();
    (ck_new, key)
}

/// KDF3(ck, input) -> (new_ck, key1, key2)
fn kdf3(ck: &[u8; 32], input: &[u8]) -> ([u8; 32], [u8; 32], [u8; 32]) {
    let hk = Hkdf::<blake2::Blake2s256>::new(Some(ck), input);
    let mut all = [0u8; 96];
    hk.expand(&[], &mut all).expect("HKDF expand failed");
    let mut ck_new = [0u8; 32];
    let mut key1   = [0u8; 32];
    let mut key2   = [0u8; 32];
    ck_new.copy_from_slice(&all[..32]);
    key1.copy_from_slice(&all[32..64]);
    key2.copy_from_slice(&all[64..]);
    all.zeroize();
    (ck_new, key1, key2)
}

// ── Handshake State ─────────────────────────────────────────────────────────

/// The Noise handshake state.
///
/// This is the central object for the two-message handshake exchange.
/// After both messages are processed, `into_session_keys()` extracts
/// the transport keys.
///
/// Derives ZeroizeOnDrop: all sensitive key material is securely zeroed
/// when this struct is dropped, even on early return due to errors.
#[derive(ZeroizeOnDrop)]
pub struct HandshakeState {
    /// Local static key pair (long-term identity)
    local_static_private: [u8; 32],
    local_static_public:  [u8; 32],

    /// Local ephemeral key pair (generated fresh per handshake)
    /// Option because it may not be generated yet
    local_ephemeral_private: Option<[u8; 32]>,
    local_ephemeral_public:  Option<[u8; 32]>,

    /// Remote static public key (known before handshake begins)
    remote_static_public: [u8; 32],

    /// Remote ephemeral public key (received in Message 2)
    remote_ephemeral_public: Option<[u8; 32]>,

    /// Handshake hash: transcript accumulator
    /// h = BLAKE2s(h || everything_processed_so_far)
    h: [u8; 32],

    /// Chaining key: evolves through DH operations
    /// Becomes session keys at the end
    ck: [u8; 32],

    /// Pre-shared key (32 bytes of zeros if unused)
    psk: [u8; 32],

    /// Whether we're the initiator (true) or responder (false)
    is_initiator: bool,
}

impl HandshakeState {
    /// Create a new handshake state for the initiator.
    ///
    /// `local_static`: Our long-term Curve25519 key pair.
    /// `remote_static_pub`: The peer's public key (from config).
    pub fn new_initiator(
        local_static_private: [u8; 32],
        local_static_public:  [u8; 32],
        remote_static_public: [u8; 32],
    ) -> Self {
        let mut hs = HandshakeState {
            local_static_private,
            local_static_public,
            local_ephemeral_private: None,
            local_ephemeral_public: None,
            remote_static_public,
            remote_ephemeral_public: None,
            h:  [0u8; 32],
            ck: [0u8; 32],
            psk: [0u8; 32],
            is_initiator: true,
        };
        hs.initialize();
        hs
    }

    /// Create a new handshake state for the responder.
    pub fn new_responder(
        local_static_private: [u8; 32],
        local_static_public:  [u8; 32],
    ) -> Self {
        let mut hs = HandshakeState {
            local_static_private,
            local_static_public,
            local_ephemeral_private: None,
            local_ephemeral_public: None,
            remote_static_public: [0u8; 32],  // Set when MSG1 is processed
            remote_ephemeral_public: None,
            h:  [0u8; 32],
            ck: [0u8; 32],
            psk: [0u8; 32],
            is_initiator: false,
        };
        // Responder initializes state when it receives MSG1
        hs
    }

    /// Initialize chaining key and hash.
    ///
    /// From the spec:
    ///   Ci = HASH(CONSTRUCTION)
    ///   Hi = HASH(Ci || IDENTIFIER)
    ///   Hi = HASH(Hi || Responder.static.public)
    fn initialize(&mut self) {
        // ck = HASH("Noise_IKpsk2_25519_ChaChaPoly_BLAKE2s")
        self.ck = hash(CONSTRUCTION.as_bytes());

        // h = HASH(ck || "WireGuard v1 zx2c4 Jason@zx2c4.com")
        self.h = hash2(&self.ck, IDENTIFIER.as_bytes());

        // h = HASH(h || R_pub)  -- bind responder identity into transcript
        self.h = hash2(&self.h, &self.remote_static_public);
    }

    /// Mix new data into the transcript hash.
    /// h = HASH(h || data)
    fn mix_hash(&mut self, data: &[u8]) {
        self.h = hash2(&self.h, data);
    }

    /// Mix DH result into the chaining key.
    /// ck = KDF1(ck, dh_result)
    fn mix_key(&mut self, dh_result: &[u8]) {
        self.ck = kdf1(&self.ck, dh_result);
    }

    /// Create Message 1 (Initiator → Responder).
    ///
    /// Returns the 148-byte initiation message.
    ///
    /// Noise tokens processed: -> e, es, s, ss
    pub fn create_initiation(&mut self) -> Result<Vec<u8>, WireGuardError> {
        use chacha20poly1305::{ChaCha20Poly1305, KeyInit, AeadInPlace};
        use chacha20poly1305::aead::Aead;

        let mut msg = vec![0u8; 148];

        // ── Header ──────────────────────────────────────────────
        msg[0] = 1;  // type = initiation
        // reserved bytes 1-3: 0
        // sender_index bytes 4-7: random in production
        let sender_idx: u32 = 0xCAFEBABE;
        msg[4..8].copy_from_slice(&sender_idx.to_le_bytes());

        // ── Token: e (send ephemeral public key) ────────────────
        //
        // Generate a fresh ephemeral keypair.
        // This is the key that provides forward secrecy.
        // It is used once and then discarded.
        let ephemeral_private = EphemeralSecret::random_from_rng(
            rand::rngs::OsRng
        );
        let ephemeral_public = PublicKey::from(&ephemeral_private);
        let epk_bytes = *ephemeral_public.as_bytes();

        // Store for later DH operations
        self.local_ephemeral_public = Some(epk_bytes);

        // Send ephemeral public key
        msg[8..40].copy_from_slice(&epk_bytes);

        // Mix into transcript
        self.mix_hash(&epk_bytes);
        self.ck = kdf1(&self.ck, &epk_bytes);

        // ── Token: es (DH with remote static) ───────────────────
        //
        // dh_es = DH(local_ephemeral, remote_static)
        // Mixes into CK, gives us a temporary encryption key.
        let remote_static = x25519_dalek::PublicKey::from(self.remote_static_public);
        // Note: In real code, EphemeralSecret is consumed by DH.
        // We'd use diffie_hellman() method.
        // Simplified here:
        let dh_es = ephemeral_private.diffie_hellman(&remote_static);
        let (new_ck, key_es) = kdf2(&self.ck, dh_es.as_bytes());
        self.ck = new_ck;

        // ── Token: s (send static, encrypted) ───────────────────
        //
        // Encrypt our static public key using key_es.
        // Result: 48 bytes (32 bytes encrypted + 16-byte AEAD tag)
        let nonce_bytes = [0u8; 12];
        let cipher = ChaCha20Poly1305::new_from_slice(&key_es)
            .map_err(|_| WireGuardError::MalformedMessage)?;

        let mut static_pub_bytes = self.local_static_public.to_vec();
        let aad = self.h.to_vec();

        // Encrypt in place
        use chacha20poly1305::Nonce;
        let nonce = Nonce::from_slice(&nonce_bytes);
        let enc_static = cipher.encrypt(nonce, chacha20poly1305::aead::Payload {
            msg: &static_pub_bytes,
            aad: &aad,
        }).map_err(|_| WireGuardError::AuthenticationFailure)?;

        msg[40..88].copy_from_slice(&enc_static);
        self.mix_hash(&enc_static);

        static_pub_bytes.zeroize();

        // ── Token: ss (DH with remote static using our static) ──
        //
        // dh_ss = DH(local_static, remote_static)
        // This authenticates both parties' long-term identities.
        let local_static = StaticSecret::from(self.local_static_private);
        let dh_ss = local_static.diffie_hellman(&remote_static);
        let (new_ck, key_ss) = kdf2(&self.ck, dh_ss.as_bytes());
        self.ck = new_ck;

        // ── Encrypt timestamp ────────────────────────────────────
        //
        // timestamp = TAI64N (12 bytes)
        // enc_ts = AEAD(key_ss, 0, timestamp, h)
        let ts = tai64n_now();
        let cipher_ss = ChaCha20Poly1305::new_from_slice(&key_ss)
            .map_err(|_| WireGuardError::MalformedMessage)?;
        let aad2 = self.h.to_vec();
        let enc_ts = cipher_ss.encrypt(nonce, chacha20poly1305::aead::Payload {
            msg: &ts,
            aad: &aad2,
        }).map_err(|_| WireGuardError::AuthenticationFailure)?;

        msg[88..116].copy_from_slice(&enc_ts);
        self.mix_hash(&enc_ts);

        // ── MAC1 ─────────────────────────────────────────────────
        //
        // MAC1 = MAC(HASH("mac1----" || R_pub), msg[0..116])
        let mac_key = hash2(b"mac1----", &self.remote_static_public);
        // Simplified: in production use keyed BLAKE2s-128
        let mac1 = &hash2(&mac_key, &msg[..116])[..16];
        msg[116..132].copy_from_slice(mac1);

        // MAC2 = 0 (no cookie)
        // msg[132..148] already zero

        Ok(msg)
    }

    /// Extract transport keys after handshake completes.
    ///
    /// The chaining key `ck` is used with HKDF to produce two 32-byte keys:
    ///   - T_initiator_to_responder (send key for initiator)
    ///   - T_responder_to_initiator (recv key for initiator)
    ///
    /// Both keys are the same for both parties (derived from same ck),
    /// but they use them in opposite directions.
    pub fn derive_transport_keys(&self) -> (SymmetricKey, SymmetricKey) {
        let (tx_key, rx_key) = kdf2(&self.ck, &[]);
        if self.is_initiator {
            (SymmetricKey::new(tx_key), SymmetricKey::new(rx_key))
        } else {
            (SymmetricKey::new(rx_key), SymmetricKey::new(tx_key))
        }
    }
}

/// Get current time as TAI64N (12 bytes: 8-byte seconds + 4-byte nanos)
fn tai64n_now() -> [u8; 12] {
    use std::time::{SystemTime, UNIX_EPOCH};
    let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap();
    let sec  = now.as_secs() + 0x400000000000000au64;  // TAI64 epoch offset
    let nsec = now.subsec_nanos();

    let mut ts = [0u8; 12];
    ts[..8].copy_from_slice(&sec.to_be_bytes());   // big-endian
    ts[8..].copy_from_slice(&nsec.to_be_bytes());  // big-endian
    ts
}
```

### Session and Transport (src/session.rs)

```rust
// src/session.rs
//
// WireGuard transport session: encrypts and decrypts data packets.

use chacha20poly1305::{ChaCha20Poly1305, KeyInit, Nonce};
use chacha20poly1305::aead::Aead;
use zeroize::{Zeroize, ZeroizeOnDrop};
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::Instant;
use crate::types::{Counter, SymmetricKey, WireGuardError};

// ── Replay Window ────────────────────────────────────────────────────────────

const WINDOW_SIZE: u64  = 2048;
const WINDOW_WORDS: usize = (WINDOW_SIZE / 64) as usize;

/// Anti-replay sliding window.
///
/// Tracks the last 2048 packet counters.
/// Uses a circular bitmap for O(1) operations.
struct ReplayWindow {
    /// Circular bitmap: bit N is set if counter (base - WINDOW_SIZE + N)
    /// has been seen.
    bitmap: [u64; WINDOW_WORDS],
    /// The highest counter we've received.
    base: u64,
    /// Whether any packet has been received yet.
    initialized: bool,
}

impl ReplayWindow {
    fn new() -> Self {
        ReplayWindow {
            bitmap: [0u64; WINDOW_WORDS],
            base: 0,
            initialized: false,
        }
    }

    fn check_and_update(&mut self, counter: u64) -> Result<(), WireGuardError> {
        if !self.initialized {
            self.initialized = true;
            self.base = counter;
            self.set_bit(counter);
            return Ok(());
        }

        if counter > self.base {
            // New maximum: advance the window
            let advance = counter - self.base;
            if advance >= WINDOW_SIZE {
                // Entire window is new: clear everything
                self.bitmap = [0u64; WINDOW_WORDS];
            } else {
                // Clear the newly opened range
                let mut c = self.base.wrapping_add(1);
                while c <= counter {
                    self.clear_bit(c);
                    c = c.wrapping_add(1);
                }
            }
            self.base = counter;
            self.set_bit(counter);
            Ok(())
        } else if counter == self.base {
            Err(WireGuardError::ReplayDetected)
        } else {
            // counter < self.base
            let behind = self.base - counter;
            if behind >= WINDOW_SIZE {
                return Err(WireGuardError::CounterTooOld);
            }
            if self.get_bit(counter) {
                return Err(WireGuardError::ReplayDetected);
            }
            self.set_bit(counter);
            Ok(())
        }
    }

    /// Get the bit for a given counter value.
    fn get_bit(&self, counter: u64) -> bool {
        let idx = (counter % WINDOW_SIZE) as usize;
        (self.bitmap[idx / 64] >> (idx % 64)) & 1 == 1
    }

    fn set_bit(&mut self, counter: u64) {
        let idx = (counter % WINDOW_SIZE) as usize;
        self.bitmap[idx / 64] |= 1u64 << (idx % 64);
    }

    fn clear_bit(&mut self, counter: u64) {
        let idx = (counter % WINDOW_SIZE) as usize;
        self.bitmap[idx / 64] &= !(1u64 << (idx % 64));
    }
}

// ── Transport Session ────────────────────────────────────────────────────────

/// A WireGuard transport session.
///
/// Holds the symmetric keys and counters for encrypting/decrypting
/// actual data packets (Type 4 messages).
///
/// Key insight: two different keys for each direction.
/// `tx_key`: Encrypt packets we SEND.
/// `rx_key`: Decrypt packets we RECEIVE.
///
/// The keys are derived from the handshake's chaining key.
/// They are different from each other, preventing reflection attacks.
pub struct TransportSession {
    /// Key for encrypting outgoing packets
    tx_key: SymmetricKey,
    /// Key for decrypting incoming packets
    rx_key: SymmetricKey,

    /// Monotonically increasing nonce for encryption.
    /// Use fetch_add with Acquire/Release for thread safety.
    tx_counter: AtomicU64,

    /// Anti-replay window for received packets.
    /// Wrapped in Mutex for thread safety in real use.
    rx_window: std::sync::Mutex<ReplayWindow>,

    /// Time the session was established (for expiry checks)
    established_at: Instant,

    /// Session index assigned by remote peer
    pub remote_index: u32,
    /// Our session index (sent to remote)
    pub local_index: u32,
}

impl TransportSession {
    /// Create a new transport session from derived keys.
    pub fn new(
        tx_key: SymmetricKey,
        rx_key: SymmetricKey,
        local_index: u32,
        remote_index: u32,
    ) -> Self {
        TransportSession {
            tx_key,
            rx_key,
            tx_counter: AtomicU64::new(0),
            rx_window: std::sync::Mutex::new(ReplayWindow::new()),
            established_at: Instant::now(),
            remote_index,
            local_index,
        }
    }

    /// Check if this session has expired.
    ///
    /// WireGuard sessions last a maximum of REKEY_AFTER_TIME (180s).
    pub fn is_expired(&self) -> bool {
        self.established_at.elapsed().as_secs() >= 180
    }

    /// Encrypt an IP packet into a WireGuard Type-4 message.
    ///
    /// Input:  raw IP packet (plaintext)
    /// Output: complete WireGuard UDP payload (header + ciphertext + tag)
    ///
    /// Format:
    ///   [0]     type = 4
    ///   [1..3]  reserved = 0
    ///   [4..7]  receiver_index (little-endian)
    ///   [8..15] counter (little-endian u64)
    ///   [16..]  AEAD(tx_key, nonce(counter), ip_packet, aad="")
    ///           = ciphertext + 16-byte tag
    pub fn encrypt_packet(&self, ip_packet: &[u8]) -> Result<Vec<u8>, WireGuardError> {
        // Atomically get and increment counter
        let counter = self.tx_counter.fetch_add(1, Ordering::AcqRel);

        // Check counter hasn't wrapped to dangerous values
        const REJECT_AFTER: u64 = (1u64 << 64) - (1u64 << 13) - 1;
        if counter >= REJECT_AFTER {
            return Err(WireGuardError::CounterOverflow);
        }

        // Build nonce from counter
        // Layout: [0,0,0,0, counter as 8 LE bytes]
        let mut nonce_bytes = [0u8; 12];
        nonce_bytes[4..12].copy_from_slice(&counter.to_le_bytes());
        let nonce = Nonce::from_slice(&nonce_bytes);

        // Encrypt using ChaCha20-Poly1305
        // No AAD for transport data (spec says empty string)
        let cipher = ChaCha20Poly1305::new_from_slice(self.tx_key.as_bytes())
            .map_err(|_| WireGuardError::AuthenticationFailure)?;

        let ciphertext = cipher.encrypt(nonce, ip_packet)
            .map_err(|_| WireGuardError::AuthenticationFailure)?;

        // Build complete Type-4 message
        let mut msg = Vec::with_capacity(16 + ciphertext.len());
        msg.push(4u8);          // type
        msg.extend_from_slice(&[0u8; 3]);  // reserved
        msg.extend_from_slice(&self.remote_index.to_le_bytes());  // receiver_index
        msg.extend_from_slice(&counter.to_le_bytes());            // counter
        msg.extend_from_slice(&ciphertext);                       // encrypted data + tag

        Ok(msg)
    }

    /// Decrypt a WireGuard Type-4 message into an IP packet.
    ///
    /// Verifies:
    ///   1. Message type is 4
    ///   2. Counter is not a replay (anti-replay window)
    ///   3. AEAD tag is valid (not tampered)
    ///
    /// Returns the decrypted IP packet on success.
    pub fn decrypt_packet(&self, msg: &[u8]) -> Result<Vec<u8>, WireGuardError> {
        // Minimum size: 16 bytes header + 16 bytes AEAD tag
        if msg.len() < 32 {
            return Err(WireGuardError::MalformedMessage);
        }

        // Verify message type
        if msg[0] != 4 {
            return Err(WireGuardError::MalformedMessage);
        }

        // Extract counter from bytes 8-15
        let counter = u64::from_le_bytes(
            msg[8..16].try_into().map_err(|_| WireGuardError::MalformedMessage)?
        );

        // Anti-replay check (must happen BEFORE decryption)
        // Why before? To prevent timing attacks where an attacker probes
        // decryption behavior based on timing differences.
        {
            let mut window = self.rx_window.lock().unwrap();
            window.check_and_update(counter)?;
        }

        // Build nonce
        let mut nonce_bytes = [0u8; 12];
        nonce_bytes[4..12].copy_from_slice(&counter.to_le_bytes());
        let nonce = Nonce::from_slice(&nonce_bytes);

        // Decrypt
        let cipher = ChaCha20Poly1305::new_from_slice(self.rx_key.as_bytes())
            .map_err(|_| WireGuardError::AuthenticationFailure)?;

        let plaintext = cipher.decrypt(nonce, &msg[16..])
            .map_err(|_| WireGuardError::AuthenticationFailure)?;

        Ok(plaintext)
    }
}

// Ensure session keys are zeroed on drop
impl Drop for TransportSession {
    fn drop(&mut self) {
        // tx_key and rx_key will be zeroed by ZeroizeOnDrop
        // Reset counter
        self.tx_counter.store(0, Ordering::SeqCst);
    }
}
```

### Cryptokey Router (src/routing.rs)

```rust
// src/routing.rs
//
// Cryptokey Routing: WireGuard's combined routing table + access control.
//
// Every IP address is bound to a public key (peer).
// Outgoing: find which peer to send to based on destination IP.
// Incoming: verify source IP is in the allowed set for the decrypted peer.

use std::collections::HashMap;
use std::net::{IpAddr, Ipv4Addr, Ipv6Addr};

/// An IP prefix (network address + prefix length)
/// Examples: 10.0.0.0/8, 192.168.1.1/32, 0.0.0.0/0
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct IpPrefix {
    pub addr:   IpAddr,
    pub prefix: u8,
}

impl IpPrefix {
    pub fn new(addr: IpAddr, prefix: u8) -> Self {
        IpPrefix { addr, prefix }
    }

    /// Check if an IP address matches this prefix.
    ///
    /// For 10.0.0.0/8: any address 10.x.x.x matches.
    /// For 10.1.2.3/32: only 10.1.2.3 matches.
    pub fn contains(&self, ip: &IpAddr) -> bool {
        match (self.addr, ip) {
            (IpAddr::V4(net), IpAddr::V4(host)) => {
                if self.prefix == 0 { return true; }
                let mask = !0u32 << (32 - self.prefix);
                (u32::from(net) & mask) == (u32::from(*host) & mask)
            },
            (IpAddr::V6(net), IpAddr::V6(host)) => {
                if self.prefix == 0 { return true; }
                let mask = !0u128 << (128 - self.prefix);
                (u128::from(net) & mask) == (u128::from(*host) & mask)
            },
            _ => false,  // IPv4 doesn't match IPv6 prefix
        }
    }
}

/// A WireGuard peer configuration.
pub struct PeerConfig {
    /// The peer's Curve25519 public key (their identity)
    pub public_key: [u8; 32],

    /// List of IP prefixes this peer is allowed to send/receive
    /// Used for both routing (outgoing) and access control (incoming)
    pub allowed_ips: Vec<IpPrefix>,

    /// The peer's UDP endpoint (IP:port) — may change for roaming peers
    pub endpoint: Option<std::net::SocketAddr>,
}

/// The cryptokey routing table.
///
/// Mental model: a two-way lookup table.
///   Forward lookup: destination IP → peer public key (for sending)
///   Reverse lookup: peer public key → allowed IP list (for receiving)
pub struct CryptokeyRouter {
    peers: HashMap<[u8; 32], PeerConfig>,
}

impl CryptokeyRouter {
    pub fn new() -> Self {
        CryptokeyRouter { peers: HashMap::new() }
    }

    /// Add a peer to the routing table.
    pub fn add_peer(&mut self, peer: PeerConfig) {
        self.peers.insert(peer.public_key, peer);
    }

    /// Find which peer should receive a packet going to `dest_ip`.
    ///
    /// Uses longest prefix match: the most specific (highest prefix length)
    /// AllowedIP that contains dest_ip wins.
    ///
    /// Returns the peer's public key, or None if no match.
    pub fn route_outgoing(&self, dest_ip: &IpAddr) -> Option<&PeerConfig> {
        let mut best_match: Option<(&PeerConfig, u8)> = None;

        for peer in self.peers.values() {
            for prefix in &peer.allowed_ips {
                if prefix.contains(dest_ip) {
                    // Longest prefix wins
                    match best_match {
                        None => best_match = Some((peer, prefix.prefix)),
                        Some((_, best_len)) if prefix.prefix > best_len => {
                            best_match = Some((peer, prefix.prefix));
                        },
                        _ => {},
                    }
                }
            }
        }

        best_match.map(|(peer, _)| peer)
    }

    /// Verify that an incoming packet's source IP is allowed for a given peer.
    ///
    /// Called after decryption to enforce access control:
    /// "Is this IP address permitted to come from this peer?"
    ///
    /// This prevents a peer from spoofing another peer's IP after
    /// they're both connected.
    pub fn verify_incoming(&self, peer_pubkey: &[u8; 32], src_ip: &IpAddr) -> bool {
        if let Some(peer) = self.peers.get(peer_pubkey) {
            peer.allowed_ips.iter().any(|prefix| prefix.contains(src_ip))
        } else {
            false
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_prefix_matching() {
        // 10.0.0.0/8 matches 10.x.x.x
        let prefix = IpPrefix::new("10.0.0.0".parse().unwrap(), 8);
        assert!( prefix.contains(&"10.1.2.3".parse().unwrap()));
        assert!(!prefix.contains(&"11.0.0.1".parse().unwrap()));
        assert!(!prefix.contains(&"192.168.1.1".parse().unwrap()));
    }

    #[test]
    fn test_longest_prefix_match() {
        let mut router = CryptokeyRouter::new();

        // PeerA: default route
        router.add_peer(PeerConfig {
            public_key: [0x01; 32],
            allowed_ips: vec![IpPrefix::new("0.0.0.0".parse().unwrap(), 0)],
            endpoint: None,
        });

        // PeerB: specific subnet
        router.add_peer(PeerConfig {
            public_key: [0x02; 32],
            allowed_ips: vec![
                IpPrefix::new("10.0.0.0".parse().unwrap(), 24)
            ],
            endpoint: None,
        });

        // 10.0.0.5 should match PeerB (/24 > /0)
        let peer = router.route_outgoing(&"10.0.0.5".parse().unwrap()).unwrap();
        assert_eq!(peer.public_key, [0x02; 32]);

        // 8.8.8.8 should match PeerA (default route)
        let peer = router.route_outgoing(&"8.8.8.8".parse().unwrap()).unwrap();
        assert_eq!(peer.public_key, [0x01; 32]);
    }
}
```

### Main (src/main.rs)

```rust
// src/main.rs
//
// Demo: WireGuard packet encryption/decryption and replay protection.

mod types;
mod noise;
mod session;
mod routing;

use types::{SymmetricKey, WireGuardError};
use session::TransportSession;
use routing::{CryptokeyRouter, IpPrefix, PeerConfig};
use std::net::IpAddr;

fn main() {
    println!("╔══════════════════════════════════════════════════════╗");
    println!("║  WireGuard Protocol Demo (Rust Implementation)       ║");
    println!("╚══════════════════════════════════════════════════════╝\n");

    // ── Demo 1: Transport Session (Encrypt/Decrypt) ──────────────
    println!("=== Demo 1: Transport Packet Encryption ===\n");

    // Simulated session keys (in real WireGuard: from handshake)
    let tx_key = SymmetricKey::new([0x42u8; 32]);
    let rx_key = SymmetricKey::new([0x42u8; 32]); // Same key for loopback demo

    let session = TransportSession::new(
        tx_key,
        rx_key,
        0x1234_5678,  // local index
        0xDEAD_BEEF,  // remote index
    );

    // Simulate an IP packet: ICMP echo (ping) 10.0.0.1 -> 10.0.0.2
    let ip_packet: Vec<u8> = vec![
        // IPv4 header (simplified)
        0x45, 0x00, 0x00, 0x1C,  // Version, IHL, TOS, Length
        0x00, 0x01, 0x00, 0x00,  // ID, Flags, Fragment Offset
        0x40, 0x01, 0x00, 0x00,  // TTL=64, Protocol=ICMP, Checksum
        0x0A, 0x00, 0x00, 0x01,  // Src: 10.0.0.1
        0x0A, 0x00, 0x00, 0x02,  // Dst: 10.0.0.2
        // ICMP echo request
        0x08, 0x00, 0x00, 0x00,  // Type=8 (echo), Code=0, Checksum
        0x00, 0x01, 0x00, 0x00,  // ID=1, Sequence=0
    ];

    println!("Original IP packet ({} bytes):", ip_packet.len());
    print!("  ");
    for (i, b) in ip_packet.iter().enumerate() {
        print!("{:02x} ", b);
        if (i + 1) % 16 == 0 { print!("\n  "); }
    }
    println!();

    // Encrypt
    match session.encrypt_packet(&ip_packet) {
        Ok(wg_msg) => {
            println!("\nWireGuard Type-4 message ({} bytes):", wg_msg.len());
            println!("  Type:           0x{:02x}", wg_msg[0]);
            println!("  Reserved:       {:02x}{:02x}{:02x}", wg_msg[1], wg_msg[2], wg_msg[3]);
            let recv_idx = u32::from_le_bytes(wg_msg[4..8].try_into().unwrap());
            let counter  = u64::from_le_bytes(wg_msg[8..16].try_into().unwrap());
            println!("  Receiver Index: 0x{:08x}", recv_idx);
            println!("  Counter:        {}", counter);
            print!("  Ciphertext:     ");
            for b in &wg_msg[16..16+ip_packet.len().min(16)] {
                print!("{:02x} ", b);
            }
            println!("...");
            print!("  AEAD Tag:       ");
            for b in &wg_msg[wg_msg.len()-16..] {
                print!("{:02x} ", b);
            }
            println!();

            // Decrypt
            match session.decrypt_packet(&wg_msg) {
                Ok(decrypted) => {
                    let matches = decrypted == ip_packet;
                    println!("\nDecryption: {} ✓", if matches { "SUCCESS" } else { "MISMATCH" });
                    println!("Original matches decrypted: {}", if matches { "YES ✓" } else { "NO ✗" });
                },
                Err(e) => println!("Decryption failed: {}", e),
            }

            // Replay test
            println!("\n=== Demo 2: Replay Protection ===\n");
            match session.decrypt_packet(&wg_msg) {
                Err(WireGuardError::ReplayDetected) => {
                    println!("Replay attempt correctly rejected ✓");
                    println!("(Same packet sent twice: counter=0 already seen)");
                },
                Ok(_) => println!("ERROR: Replay was accepted ✗"),
                Err(e) => println!("Unexpected error: {}", e),
            }
        },
        Err(e) => println!("Encryption failed: {}", e),
    }

    // ── Demo 3: Cryptokey Routing ────────────────────────────────
    println!("\n=== Demo 3: Cryptokey Routing ===\n");

    let mut router = CryptokeyRouter::new();

    // PeerA: the "server" / gateway — handles all traffic
    router.add_peer(PeerConfig {
        public_key: [0xAAu8; 32],
        allowed_ips: vec![
            IpPrefix::new("0.0.0.0".parse().unwrap(), 0),  // default route
        ],
        endpoint: Some("203.0.113.1:51820".parse().unwrap()),
    });

    // PeerB: another WireGuard client in the same network
    router.add_peer(PeerConfig {
        public_key: [0xBBu8; 32],
        allowed_ips: vec![
            IpPrefix::new("10.0.0.2".parse::<IpAddr>().unwrap(), 32),
        ],
        endpoint: None,
    });

    // Route some destinations
    let destinations = [
        "10.0.0.2",   // Should match PeerB (/32 is more specific than /0)
        "10.0.0.3",   // Should match PeerA (default route)
        "8.8.8.8",    // Should match PeerA (default route)
        "192.168.1.1",// Should match PeerA (default route)
    ];

    for dest_str in destinations {
        let dest: IpAddr = dest_str.parse().unwrap();
        match router.route_outgoing(&dest) {
            Some(peer) => {
                let peer_name = if peer.public_key == [0xAAu8; 32] { "PeerA" } else { "PeerB" };
                println!("  {} → {} (key: {:02x}{:02x}...)",
                    dest_str, peer_name,
                    peer.public_key[0], peer.public_key[1]);
            },
            None => println!("  {} → NO ROUTE", dest_str),
        }
    }

    // Verify incoming AllowedIPs check
    println!("\nIncoming verification:");
    println!("  PeerB sending from 10.0.0.2: {}",
        if router.verify_incoming(&[0xBBu8; 32], &"10.0.0.2".parse().unwrap())
        { "ALLOWED ✓" } else { "DENIED ✗" });
    println!("  PeerB sending from 10.0.0.3: {}",
        if router.verify_incoming(&[0xBBu8; 32], &"10.0.0.3".parse().unwrap())
        { "ALLOWED ✗ (should be denied)" } else { "DENIED ✓ (correct)" });

    println!("\n╔══════════════════════════════════════════════════════╗");
    println!("║  All demos complete.                                  ║");
    println!("╚══════════════════════════════════════════════════════╝");
}
```

---

## 16. Kernel vs Userspace WireGuard

### The Two Implementations

```
  ┌─────────────────────────────────────────────────────────────────┐
  │  Kernel WireGuard (Linux 5.6+, Windows via WireGuard NT)        │
  │                                                                  │
  │  ┌───────────────┐    ┌───────────────┐    ┌────────────────┐  │
  │  │  Application  │    │  Application  │    │  Application   │  │
  │  └───────┬───────┘    └───────┬───────┘    └───────┬────────┘  │
  │          │ TCP/UDP             │                     │           │
  │  ┌───────▼───────────────────────────────────────────────────┐  │
  │  │                   Linux Kernel Network Stack               │  │
  │  └─────────────────────────────┬─────────────────────────────┘  │
  │                                 │ Route lookup → wg0             │
  │  ┌──────────────────────────────▼─────────────────────────────┐ │
  │  │         WireGuard Kernel Module (wireguard.ko)              │ │
  │  │  - Crypto in kernel space (fast, no syscall overhead)       │ │
  │  │  - Direct access to TUN driver                              │ │
  │  │  - Zero-copy where possible                                 │ │
  │  └──────────────────────────────┬─────────────────────────────┘ │
  │                                 │ UDP sendmsg                    │
  │  ┌──────────────────────────────▼─────────────────────────────┐ │
  │  │                   Physical NIC Driver                       │ │
  │  └─────────────────────────────────────────────────────────────┘ │
  └─────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │  Userspace WireGuard (wireguard-go, BoringTun)                  │
  │                                                                  │
  │  ┌───────────────────────────────────────────────────────────┐  │
  │  │                   Linux Kernel Network Stack               │  │
  │  └─────────────────────────────┬─────────────────────────────┘  │
  │                                 │ Route lookup → wg0 (TUN)       │
  │  ┌──────────────────────────────▼─────────────────────────────┐ │
  │  │                    TUN Kernel Driver                        │ │
  │  └──────────────────────────────┬─────────────────────────────┘ │
  │                                 │ read(tun_fd)  ← userspace      │
  │  ┌──────────────────────────────▼─────────────────────────────┐ │
  │  │   WireGuard Userspace Process (wireguard-go / boringtun)    │ │
  │  │  - All crypto in userspace                                  │ │
  │  │  - Each packet: 2 syscalls (read TUN + write UDP)           │ │
  │  │  - Easier to port to non-Linux (macOS, BSD, Android)        │ │
  │  └──────────────────────────────┬─────────────────────────────┘ │
  │                                 │ sendto(udp_sock)               │
  │  ┌──────────────────────────────▼─────────────────────────────┐ │
  │  │                   Physical NIC Driver                       │ │
  │  └─────────────────────────────────────────────────────────────┘ │
  └─────────────────────────────────────────────────────────────────┘
```

| Property       | Kernel Module                  | Userspace (wireguard-go)     |
|----------------|-------------------------------|------------------------------|
| Speed          | Fastest (no context switch)   | ~30% slower                  |
| Portability    | Linux, Windows kernel patch   | macOS, iOS, Android, BSD     |
| Auditability   | Harder (kernel complexity)    | Easier (pure Go/Rust code)   |
| Memory safety  | C (careful)                   | Go/Rust (memory safe)        |
| Crash impact   | Kernel panic possible         | Just the process crashes     |
| Deployment     | Requires kernel module        | Just an executable           |

**BoringTun** (Cloudflare's Rust userspace WireGuard): Used in production at Cloudflare for WARP (their 1.1.1.1 VPN app). This is Rust code in production at massive scale.

---

## 17. WireGuard in Practice — Configuration Deep Dive

### Configuration File Format (`/etc/wireguard/wg0.conf`)

```ini
# ─── Server Configuration (wg0.conf) ──────────────────────
[Interface]
# The server's private key.
# Generate with: wg genkey
PrivateKey = aBCD...base64...

# UDP port to listen on.
# 51820 is the WireGuard default, but any port works.
ListenPort = 51820

# IP address of this server on the virtual network.
# /24 means this server is part of the 10.0.0.0/24 network.
Address = 10.0.0.1/24

# Optional: run these commands when the interface is brought up/down.
# Used to configure NAT for forwarding traffic from peers to the internet.
PostUp   = iptables -A FORWARD -i %i -j ACCEPT; \
           iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i %i -j ACCEPT; \
           iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

# ─── Peer 1: Alice's laptop ───────────────────────────────
[Peer]
# Alice's public key. Generated from her private key with:
#   wg pubkey < alice_private
PublicKey = XYZ...alice_public...

# Alice is allowed to use IP 10.0.0.2 (and only that IP).
# Any packet from this peer claiming a different source IP is dropped.
AllowedIPs = 10.0.0.2/32

# ─── Peer 2: Bob's phone ──────────────────────────────────
[Peer]
PublicKey = ABC...bob_public...
AllowedIPs = 10.0.0.3/32

# Optional: if we know Bob's fixed IP
Endpoint = 203.0.113.42:51820

# Keepalive: send a packet every 25 seconds to maintain NAT mapping
# Useful for mobile clients behind NAT
PersistentKeepalive = 25
```

```ini
# ─── Client Configuration (Alice's wg0.conf) ──────────────
[Interface]
PrivateKey = <alice_private_key>
Address    = 10.0.0.2/32
DNS        = 10.0.0.1  # Use server as DNS resolver (prevents DNS leaks)

[Peer]
# The server's public key
PublicKey  = <server_public_key>

# Allowed IPs: 0.0.0.0/0 means "route ALL traffic through this VPN"
# Also called "full tunnel" mode.
# For split tunnel: use specific subnets like 10.0.0.0/24
AllowedIPs = 0.0.0.0/0, ::/0

# Server's public IP and WireGuard port
Endpoint = 203.0.113.1:51820

# Keepalive so server can reach us even when we're behind NAT
PersistentKeepalive = 25
```

### Key Generation

```bash
# Generate a private key (256 bits, base64 encoded)
wg genkey > private.key

# Derive the public key from the private key
# (Curve25519: public = private * G)
wg pubkey < private.key > public.key

# Generate a pre-shared key (PSK) for extra security
wg genpsk > preshared.key

# View current WireGuard state
wg show

# Show detailed stats per peer
wg showconf wg0
```

### Interface Management

```bash
# Bring up the WireGuard interface
ip link add wg0 type wireguard

# Configure the interface with our keys and settings
wg setconf wg0 /etc/wireguard/wg0.conf

# Assign IP address
ip addr add 10.0.0.1/24 dev wg0

# Bring interface up
ip link set wg0 up

# Add route (usually done by AllowedIPs automatically)
ip route add 10.0.0.0/24 dev wg0

# All in one using wg-quick
wg-quick up wg0   # Reads /etc/wireguard/wg0.conf
wg-quick down wg0
```

---

## 18. Advanced Topics

### A. Post-Quantum Security with PSK

WireGuard's handshake is vulnerable to "harvest now, decrypt later" attacks:
An attacker records encrypted handshakes today, waits for a quantum computer,
then breaks the Curve25519 ECDH and decrypts old sessions.

The PSK (pre-shared key) provides partial mitigation:

```
If PSK is secret:
  session_key ← f(DH(e,e), DH(e,s), DH(s,e), DH(s,s), PSK)

Even if a quantum computer breaks all DH components:
  session_key still depends on PSK (symmetric, not vulnerable to Shor's)

But: if both DH AND PSK are compromised → session is broken.
This is "defense in depth", not full PQC.

Full PQC WireGuard: Under research. Likely using:
  - CRYSTALS-Kyber (NIST PQC winner) for key exchange
  - Keeping Curve25519 as fallback
  - Hybrid mode: classical + post-quantum
```

### B. Roaming and NAT Traversal

WireGuard handles mobile clients behind NAT elegantly:

```
Initial connection:
  Mobile (behind NAT) ──MSG1──▶ Server (public IP)
  Server updates peer's endpoint: "now at 203.0.113.100:52345"

Mobile changes network (e.g., switches from WiFi to 4G):
  New UDP port: 203.0.113.100:64001

  Mobile ──MSG1 (new handshake)──▶ Server
  Server automatically updates endpoint to new IP:port
  
  No reconnection delay. WireGuard just works.
  
This works because:
  - WireGuard doesn't use connection IDs based on IP:port
  - Identity is purely cryptographic (public key)
  - Any valid authenticated packet updates the endpoint
```

### C. Multithreading in the Kernel Module

WireGuard's kernel module uses work queues for parallel packet processing:

```
Incoming UDP packets (multiple CPUs):
  CPU0: rx_packet_1 ──▶ decrypt_workqueue ──▶ TUN inject
  CPU1: rx_packet_2 ──▶ decrypt_workqueue ──▶ TUN inject
  CPU2: rx_packet_3 ──▶ decrypt_workqueue ──▶ TUN inject

Ordering problem:
  packet_2 (counter=5) might decrypt faster than packet_1 (counter=4)
  → Reordering within the replay window is fine
  → Replay window is designed to handle up-to-2048-out-of-order packets

Nonce reuse is prevented by:
  Atomic counter increment (fetch_add, not a race condition)
```

### D. WireGuard over TCP (workaround)

WireGuard is UDP-only by design. Why?

- TCP over TCP (TCP tunneled inside TCP) causes terrible performance:
  Two retransmission mechanisms fight each other
- UDP inside UDP: fine — inner TCP handles reliability itself

But some firewalls block UDP. Solutions:

1. **udp2raw**: Wraps WireGuard UDP in TCP or ICMP for firewall evasion
2. **wstunnel**: Wraps WireGuard in WebSocket (looks like HTTPS)
3. **Shadowsocks + WireGuard**: Obfuscation layer

### E. WireGuard Key Management at Scale

In large deployments (1000+ peers), managing public keys manually is impractical.

Solutions:
- **WireGuard-UI**: Web interface for peer management
- **Headscale**: Open-source coordination server (compatible with Tailscale clients)
- **Tailscale**: Builds on WireGuard with a centralized coordination plane

The coordination plane handles:
- Key distribution (DERP servers)
- Endpoint discovery (NAT traversal)
- ACLs (access control lists)
- Certificate rotation

WireGuard itself remains just the data plane.

---

## 19. Mental Models and Expert Intuition

### The "Cryptographic Ratchet" Mental Model

Think of the chaining key `ck` as a one-way ratchet:

```
Initial ck ──DH(e,rs)──▶ ck₁ ──DH(s,rs)──▶ ck₂ ──DH(re,e)──▶ ck₃ ──PSK──▶ ck₄
                                                                               │
                                                                    derive session keys
```

Each DH step mixes in more shared secret material. You can only go forward. This provides:
- **Forward secrecy**: ck₄ depends on ephemeral keys; if we delete them, ck₄ is unrecoverable
- **Transcript binding**: ck₄ encodes the entire history of the handshake

### The "Authentication Chain" Mental Model

In WireGuard, authentication flows like a chain:

```
"I know you know Bob's public key" (MAC1)
    ↓
"I proved I'm Alice using Alice's private key" (encrypted static)
    ↓
"Alice was here at this timestamp" (encrypted timestamp, prevents replay)
    ↓
"We both derived the same session key from the same DH chain" (AEAD decryption success)
```

Each step raises the authentication level. Forging any step requires breaking either the DH or the AEAD.

### The "Separation of Concerns" Mental Model

WireGuard cleanly separates three layers:

```
┌────────────────────────────────────┐
│  IDENTITY LAYER                    │
│  Who are you?                      │
│  → Curve25519 static keypairs      │
│  → Configured in AllowedIPs        │
└────────────────────┬───────────────┘
                     │ Handshake produces ↓
┌────────────────────▼───────────────┐
│  SESSION LAYER                     │
│  How do we encrypt this conversation?│
│  → Ephemeral keys (forward secrecy)│
│  → ChaCha20-Poly1305 session keys  │
│  → 3-minute lifetime               │
└────────────────────┬───────────────┘
                     │ Session provides ↓
┌────────────────────▼───────────────┐
│  TRANSPORT LAYER                   │
│  Moving encrypted data efficiently │
│  → Type-4 UDP messages             │
│  → Monotonic counter nonces        │
│  → Replay window                   │
└────────────────────────────────────┘
```

### Cognitive Principle: Pattern Recognition

When studying network protocols, train yourself to always ask:

1. **Authentication**: How does each party prove identity?
2. **Confidentiality**: What prevents eavesdropping?
3. **Integrity**: What detects tampering?
4. **Freshness**: What prevents replay?
5. **Forward Secrecy**: What limits damage from key compromise?
6. **Denial of Service**: What prevents resource exhaustion?

WireGuard has a clear, auditable answer to each. Most complex protocols (IPSec, TLS) have convoluted answers. The clarity of WireGuard's answers is itself a security property.

### The "Threat Model Inversion" Technique

Expert security engineers design by asking:
**"What would an attacker need to break this?"**

For WireGuard transport:
- Break ChaCha20-Poly1305: requires ~2^256 operations (computationally infeasible)
- Replay a packet: blocked by 2048-bit sliding window
- Forge a packet: requires knowing the session key (requires breaking the handshake)
- Break the handshake: requires breaking Curve25519 DH (Elliptic Curve Discrete Log)
- Compromise forward secrecy: requires breaking it DURING the session (ephemeral keys deleted immediately after)

Each attack path leads to a computationally infeasible problem. This systematic analysis is what experts do before choosing cryptographic primitives.

---

## Summary Reference Card

```
╔═══════════════════════════════════════════════════════════════════╗
║             WIREGUARD COMPLETE REFERENCE                           ║
╠═══════════════════════════════════════════════════════════════════╣
║ Primitives                                                         ║
║   Key Exchange:  Curve25519 ECDH                                  ║
║   AEAD Cipher:   ChaCha20-Poly1305                                ║
║   Hash:          BLAKE2s-256                                      ║
║   KDF:           HKDF (BLAKE2s-based)                             ║
╠═══════════════════════════════════════════════════════════════════╣
║ Handshake (Noise_IKpsk2)                                          ║
║   MSG1 (148 bytes): ephemeral, encrypt_static, encrypt_timestamp  ║
║   MSG2 ( 92 bytes): ephemeral, DH(ee), DH(se), PSK, empty        ║
║   Keys derived: KDF2(final_ck, "") → tx_key, rx_key              ║
╠═══════════════════════════════════════════════════════════════════╣
║ Transport (Type 4)                                                 ║
║   Header: [type=4][reserved][recv_idx][counter]  = 16 bytes       ║
║   Payload: ChaCha20Poly1305(tx_key, nonce(counter), ip_pkt)      ║
║   Nonce:   [0,0,0,0, counter_le_8bytes]                          ║
║   Replay:  2048-bit sliding window on rx counter                  ║
╠═══════════════════════════════════════════════════════════════════╣
║ Timers                                                             ║
║   Rekey after:   180s  (initiate new handshake)                   ║
║   Reject after:  180s  (stop using old keys)                      ║
║   Retry timeout:   5s  (retry failed handshake)                   ║
║   Keepalive:      10s  (maintain NAT mapping)                     ║
╠═══════════════════════════════════════════════════════════════════╣
║ Security Properties                                                ║
║   ✓ Mutual authentication      ✓ Forward secrecy                  ║
║   ✓ Initiator identity hidden  ✓ Replay protection                ║
║   ✓ Tamper detection           ✓ DoS resistance (cookie)          ║
║   ✓ No crypto agility          ✓ Port scanner stealth             ║
╚═══════════════════════════════════════════════════════════════════╝
```

---

*This guide covers the WireGuard protocol as specified in the whitepaper by Jason A. Donenfeld (https://www.wireguard.com/papers/wireguard.pdf). The implementations shown are educational and intended to build understanding. For production use, rely on audited libraries: libsodium, the Linux kernel module, BoringTun (Cloudflare's Rust implementation), or wireguard-go.*