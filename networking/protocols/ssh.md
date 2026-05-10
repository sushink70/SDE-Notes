# SSH Protocol: A Complete In-Depth Guide

> **The Secure Shell Protocol** — architecture, cryptography, wire format, implementation, and mental models for thinking clearly about secure remote communication.

---

## Table of Contents

1. [Historical Context and Motivation](#1-historical-context-and-motivation)
2. [Protocol Architecture and Layering](#2-protocol-architecture-and-layering)
3. [SSH Transport Layer Protocol (RFC 4253)](#3-ssh-transport-layer-protocol-rfc-4253)
4. [SSH Authentication Protocol (RFC 4252)](#4-ssh-authentication-protocol-rfc-4252)
5. [SSH Connection Protocol (RFC 4254)](#5-ssh-connection-protocol-rfc-4254)
6. [Cryptographic Primitives and Algorithms](#6-cryptographic-primitives-and-algorithms)
7. [Key Exchange In Depth](#7-key-exchange-in-depth)
8. [Host Key Infrastructure](#8-host-key-infrastructure)
9. [Public Key Authentication In Depth](#9-public-key-authentication-in-depth)
10. [SSH Channels and Multiplexing](#10-ssh-channels-and-multiplexing)
11. [Port Forwarding and Tunneling](#11-port-forwarding-and-tunneling)
12. [SSH Agent and Agent Forwarding](#12-ssh-agent-and-agent-forwarding)
13. [SSH Certificates](#13-ssh-certificates)
14. [Wire Format and Packet Structure](#14-wire-format-and-packet-structure)
15. [SSH Configuration Files](#15-ssh-configuration-files)
16. [Security Threat Model and Attack Surface](#16-security-threat-model-and-attack-surface)
17. [C Implementation](#17-c-implementation)
18. [Rust Implementation](#18-rust-implementation)
19. [Debugging and Packet Analysis](#19-debugging-and-packet-analysis)
20. [Mental Models for Reasoning About SSH](#20-mental-models-for-reasoning-about-ssh)

---

## 1. Historical Context and Motivation

### The Problem SSH Solved

Before SSH, remote administration of Unix systems relied on protocols designed in an era when networks were trusted academic environments:

- **rsh (remote shell)**: Authenticated purely by IP address and username in `.rhosts`. Any attacker who could spoof an IP could gain access.
- **rlogin**: Same trust model, same vulnerability.
- **Telnet**: All traffic — including passwords — transmitted as plaintext. Any node on the network path could read it.
- **FTP**: Plaintext credentials, plaintext data.
- **rcp**: Plaintext file transfer with `.rhosts` authentication.

In 1994–1995, Finnish researcher Tatu Ylönen observed a password-sniffing attack on his university network. An attacker had placed a packet sniffer on the network and harvested thousands of credentials from Telnet sessions. His response was to design and implement SSH — the Secure Shell.

### SSH 1 vs SSH 2

SSH protocol version 1 (1995–1996) had several serious cryptographic flaws:

- **Insert attack**: An attacker could insert arbitrary commands into the encrypted stream because SSH1 used CRC-32 as its integrity check — not a MAC. CRC is not a cryptographic hash; it is designed for error detection, not forgery prevention.
- **Weak key exchange**: The RSA key exchange in SSH1 had weaknesses that allowed man-in-the-middle downgrade attacks.
- **No integrity for channel operations**: Channel close, EOF, and other signals were not authenticated.

SSH protocol version 2 (standardized by IETF as RFCs 4250–4256 in 2006) addressed all these issues with:

- A properly layered architecture separating transport, authentication, and connection concerns.
- Use of authenticated encryption (MAC-then-encrypt or Encrypt-then-MAC models).
- A rigorous Diffie-Hellman key exchange with server host key verification.
- Binary packet protocol with strong integrity.

**All modern deployments use SSH-2. SSH-1 is deprecated, broken, and must not be used.**

---

## 2. Protocol Architecture and Layering

SSH is a layered protocol. Understanding the layers is the single most important mental model for reasoning about SSH.

```
+----------------------------------------------------------+
|                  APPLICATION LAYER                        |
|   (interactive shell, exec, sftp, scp, port forwarding)  |
+----------------------------------------------------------+
|              SSH CONNECTION PROTOCOL (RFC 4254)           |
|   (channels, multiplexing, flow control, requests)        |
+----------------------------------------------------------+
|            SSH AUTHENTICATION PROTOCOL (RFC 4252)         |
|   (password, publickey, keyboard-interactive, GSSAPI)     |
+----------------------------------------------------------+
|             SSH TRANSPORT LAYER PROTOCOL (RFC 4253)       |
|   (key exchange, host key verification, encryption, MAC)  |
+----------------------------------------------------------+
|                      TCP / IP                             |
|                   (port 22 default)                       |
+----------------------------------------------------------+
```

Each layer has a distinct responsibility:

**Transport Layer** — establishes a secure, authenticated channel to the *server machine*. After transport layer completion, you know you are talking to the legitimate server and all subsequent data is encrypted and integrity-protected. But you have not yet proven *who you are*.

**Authentication Layer** — proves *who the client is* to the server. This runs over the already-secure transport. Because transport is already encrypted and integrity-protected, authentication credentials (passwords, signed challenges) are never exposed to the network.

**Connection Layer** — multiplexes logical channels over the single secure connection. A single SSH connection can carry an interactive shell, a forwarded TCP port, an agent connection, and an SFTP subsystem simultaneously, all logically isolated.

### Message Number Space

SSH uses numeric message type bytes (1 byte). They are organized as follows:

```
  1–19    Transport layer generic messages
 20–29    Algorithm negotiation
 30–49    Key exchange method specific (dynamic range)
 50–59    User authentication generic
 60–79    User authentication method specific (dynamic range)
 80–89    Connection protocol generic
 90–127   Channel related messages
 128–191  Reserved
 192–255  Local extensions
```

This numbering is important: when reading packet captures or implementing SSH, you identify protocol phase by the message type byte.

---

## 3. SSH Transport Layer Protocol (RFC 4253)

The transport layer is responsible for:

1. Protocol version exchange
2. Algorithm negotiation (key exchange, host key, encryption, MAC, compression)
3. Key exchange (establishing shared secrets)
4. Host key verification (server authentication)
5. Deriving encryption keys and MAC keys from shared secrets
6. Encrypting and MACing all subsequent packets
7. Service request (asking for authentication or connection layer)

### 3.1 Protocol Version Exchange

The very first thing both sides do after TCP connection is exchange a version string. This is the only part of the protocol that is NOT a binary packet — it is a plaintext line.

```
Client                                        Server
  |                                             |
  |  <-- SSH-2.0-OpenSSH_9.6\r\n               |
  |                                             |
  |  SSH-2.0-OpenSSH_9.6\r\n -->               |
  |                                             |
```

Format:
```
SSH-<protoversion>-<softwareversion> [SP comments] CR LF
```

Examples:
```
SSH-2.0-OpenSSH_9.6
SSH-2.0-libssh_0.9.6
SSH-2.0-PuTTY_0.80
SSH-2.0-dropbear_2022.83
```

**Why this matters**: The version string `SSH-2.0-...` is part of the key exchange hash computation (the `H` value). Both sides include their version strings in the hash, binding the negotiated keys to the version strings exchanged. This prevents a downgrade attack where an attacker replaces "SSH-2.0" with "SSH-1.99".

### 3.2 Binary Packet Protocol

After version exchange, all communication uses the SSH binary packet format:

```
+-------------------+----------+-----------+-----+
| packet_length (4) | pad_len  |  payload  | pad | MAC
|                   |    (1)   |           |     |
+-------------------+----------+-----------+-----+
```

Field breakdown:

```
packet_length  : uint32  - Length of the entire packet excluding the
                           packet_length and MAC fields. Includes
                           padding_length, payload, and random padding.

padding_length : byte    - Length of the random padding at the end.
                           Must be at least 4 bytes. The packet (minus
                           packet_length and MAC) must be a multiple
                           of the cipher block size (or 8 if block
                           size < 8).

payload        : bytes   - The actual message. First byte is the
                           message type.

random padding : bytes   - Random bytes for alignment. Makes traffic
                           analysis harder (along with padding and
                           length fields).

MAC            : bytes   - Message Authentication Code computed over
                           sequence_number || packet (before
                           encryption). Length depends on MAC
                           algorithm (0 if none).
```

**Sequence number**: Every packet has an implicit 32-bit sequence number, starting at 0 and incrementing. It is NOT transmitted but is included in MAC computation. This prevents replay attacks (replaying a valid old packet would have the wrong sequence number in the MAC, causing MAC failure).

**Encryption applies to**: `packet_length + padding_length + payload + random_padding` (the MAC is computed over this block before encryption, then appended after encryption in Encrypt-then-MAC mode, or the whole thing is authenticated in AEAD mode).

### 3.3 Algorithm Negotiation — KEXINIT

Both client and server send a `SSH_MSG_KEXINIT` (message type 20) packet immediately after version exchange. Neither side waits for the other; they send simultaneously.

```
byte         SSH_MSG_KEXINIT (20)
byte[16]     cookie (random bytes)
name-list    kex_algorithms
name-list    server_host_key_algorithms
name-list    encryption_algorithms_client_to_server
name-list    encryption_algorithms_server_to_client
name-list    mac_algorithms_client_to_server
name-list    mac_algorithms_server_to_client
name-list    compression_algorithms_client_to_server
name-list    compression_algorithms_server_to_client
name-list    languages_client_to_server
name-list    languages_server_to_client
boolean      first_kex_packet_follows
uint32       0 (reserved)
```

A `name-list` is a comma-separated list of algorithm names in preference order (most preferred first). The negotiated algorithm is the first in the client's list that also appears in the server's list.

Example name lists from modern OpenSSH:

```
kex_algorithms:
  curve25519-sha256,curve25519-sha256@libssh.org,
  ecdh-sha2-nistp256,ecdh-sha2-nistp384,ecdh-sha2-nistp521,
  diffie-hellman-group-exchange-sha256,
  diffie-hellman-group16-sha512,
  diffie-hellman-group18-sha512,
  diffie-hellman-group14-sha256

server_host_key_algorithms:
  ssh-ed25519,rsa-sha2-512,rsa-sha2-256,ecdsa-sha2-nistp256

encryption_algorithms:
  chacha20-poly1305@openssh.com,
  aes128-ctr,aes192-ctr,aes256-ctr,
  aes128-gcm@openssh.com,aes256-gcm@openssh.com

mac_algorithms:
  umac-64-etm@openssh.com,umac-128-etm@openssh.com,
  hmac-sha2-256-etm@openssh.com,hmac-sha2-512-etm@openssh.com,
  hmac-sha1-etm@openssh.com,umac-64@openssh.com,
  umac-128@openssh.com,hmac-sha2-256,hmac-sha2-512

compression_algorithms:
  none,zlib@openssh.com
```

**The cookie**: 16 random bytes contributed by each side to prevent chosen-plaintext attacks on the key derivation. Even if an attacker can influence some negotiation parameters, they cannot predict or control the final secrets because each side contributes randomness.

**first_kex_packet_follows**: If `true`, the sender is optimistically sending the first key exchange packet before seeing the other side's KEXINIT. This saves a round trip. If the negotiated algorithm doesn't match what was sent, the optimistic packet is silently ignored.

### 3.4 Key Exchange Phase — Full Protocol Flow

```
Client                                         Server
  |                                              |
  |---SSH_MSG_KEXINIT (20) -------------------->|
  |<--SSH_MSG_KEXINIT (20) ---------------------|
  |                                              |
  |   [Key Exchange Method Specific Messages]    |
  |   e.g., for curve25519:                      |
  |                                              |
  |---SSH_MSG_KEX_ECDH_INIT (30) -------------->|
  |   client_ephemeral_public_key                |
  |                                              |
  |<--SSH_MSG_KEX_ECDH_REPLY (31) --------------|
  |   server_host_public_key                     |
  |   server_ephemeral_public_key                |
  |   signature(H)                               |
  |                                              |
  | [Client verifies host key and signature]     |
  |                                              |
  |---SSH_MSG_NEWKEYS (21) -------------------->|
  |<--SSH_MSG_NEWKEYS (21) ---------------------|
  |                                              |
  | [Both sides switch to new keys]              |
  |                                              |
  |---SSH_MSG_SERVICE_REQUEST (5) ------------->|
  |   "ssh-userauth"                             |
  |<--SSH_MSG_SERVICE_ACCEPT (6) ---------------|
```

### 3.5 Key Derivation — From Shared Secret to Actual Keys

After key exchange, both sides have the same shared secret `K` (an integer) and the exchange hash `H`. From these, they derive six values:

```
IV for client-to-server encryption:      HASH(K || H || "A" || session_id)
IV for server-to-client encryption:      HASH(K || H || "B" || session_id)
Key for client-to-server encryption:     HASH(K || H || "C" || session_id)
Key for server-to-client encryption:     HASH(K || H || "D" || session_id)
MAC key for client-to-server:            HASH(K || H || "E" || session_id)
MAC key for server-to-client:            HASH(K || H || "F" || session_id)
```

Where:
- `K` is the shared secret (DH output), encoded as an SSH mpint
- `H` is the exchange hash
- `session_id` is the `H` value from the **first** key exchange (it does not change on rekey)
- `HASH` is the hash function negotiated in key exchange (e.g., SHA-256 for curve25519-sha256)
- The letter `"A"` through `"F"` is a single byte

If the derived key is shorter than required (some ciphers need longer keys), the derivation is extended:

```
K1 = HASH(K || H || X || session_id)
K2 = HASH(K || H || K1)
K3 = HASH(K || H || K1 || K2)
Key = K1 || K2 || K3 || ...  (take first N bytes needed)
```

**Why separate IVs and keys for each direction?** Prevents reflection attacks. An attacker cannot replay a server→client packet as a client→server packet because different keys are used. The encryption context is asymmetric by design.

### 3.6 SSH_MSG_NEWKEYS

After deriving keys, both sides send `SSH_MSG_NEWKEYS` (type 21). This message is still sent under the old (null or previous) encryption. After sending it, the sender immediately switches to the new encryption. After receiving it, the receiver switches to the new keys for subsequent packets.

This two-phase handshake ensures both sides switch atomically and synchronously with respect to the message stream.

---

## 4. SSH Authentication Protocol (RFC 4252)

Authentication runs over the already-secured transport. The client requests the `ssh-userauth` service, then proves its identity.

### 4.1 Service Request

```
SSH_MSG_SERVICE_REQUEST (5)
  string  service-name    "ssh-userauth"

SSH_MSG_SERVICE_ACCEPT (6)
  string  service-name    "ssh-userauth"
```

### 4.2 Authentication Methods

The client sends `SSH_MSG_USERAUTH_REQUEST` which includes the desired username, service to use after authentication (always `"ssh-connection"`), and the authentication method.

```
SSH_MSG_USERAUTH_REQUEST (50)
  string  username
  string  service-name     "ssh-connection"
  string  method-name
  ...method-specific data...
```

**Method: none**

Used to probe what methods the server supports without attempting actual authentication.

```
method-name: "none"
```

The server responds with `SSH_MSG_USERAUTH_FAILURE` (51) listing supported methods.

**Method: password**

```
SSH_MSG_USERAUTH_REQUEST (50)
  string   username
  string   "ssh-connection"
  string   "password"
  boolean  FALSE
  string   plaintext-password
```

The password is transmitted as a plaintext SSH string over the already-encrypted transport. To the network, it is ciphertext. This is safe — the plaintext only exists in the encrypted tunnel.

The server may respond with `SSH_MSG_USERAUTH_PASSWD_CHANGEREQ` (60) if the password has expired, prompting the client to set a new one.

**Method: publickey**

Two-phase. First, probe whether a key is acceptable:

```
SSH_MSG_USERAUTH_REQUEST
  string   username
  string   "ssh-connection"
  string   "publickey"
  boolean  FALSE            ← probe only
  string   key-algorithm
  string   public-key-blob
```

If the server would accept this key, it responds with:

```
SSH_MSG_USERAUTH_PK_OK (60)
  string   key-algorithm
  string   public-key-blob
```

The client then sends the actual authentication request with a signature:

```
SSH_MSG_USERAUTH_REQUEST
  string   username
  string   "ssh-connection"
  string   "publickey"
  boolean  TRUE             ← actual attempt
  string   key-algorithm
  string   public-key-blob
  string   signature
```

The signature is computed over:

```
string   session_id
byte     SSH_MSG_USERAUTH_REQUEST (50)
string   username
string   "ssh-connection"
string   "publickey"
boolean  TRUE
string   key-algorithm
string   public-key-blob
```

This binds the signature to the specific session (via `session_id`), preventing replay across sessions.

**Method: keyboard-interactive**

A challenge-response mechanism. The server sends prompts (possibly multiple), and the client responds with answers. Used for PAM, OTP (TOTP, HOTP), and S/Key.

```
SSH_MSG_USERAUTH_INFO_REQUEST (60)
  string   name
  string   instruction
  string   language-tag
  int32    num-prompts
  string   prompt[1]
  boolean  echo[1]          ← TRUE = show input, FALSE = hide (password-like)
  ...

SSH_MSG_USERAUTH_INFO_RESPONSE (61)
  int32    num-responses
  string   response[1]
  ...
```

**Method: gssapi-with-mic**

Kerberos / GSSAPI authentication. Allows SSH to use an existing Kerberos ticket. The MIC (Message Integrity Code) binds the GSSAPI token to the SSH session.

### 4.3 Authentication Responses

```
SSH_MSG_USERAUTH_SUCCESS (52)
  (no data)

SSH_MSG_USERAUTH_FAILURE (51)
  name-list   authentications-that-can-continue
  boolean     partial-success
```

`partial-success` is `TRUE` when the last authentication attempt succeeded but is insufficient (the server requires multiple factors). For example, after successful publickey auth, the server may still require keyboard-interactive.

### 4.4 Authentication Banner

Before accepting or rejecting authentication, the server can send:

```
SSH_MSG_USERAUTH_BANNER (53)
  string   message
  string   language-tag
```

Used for legal notices, system banners, and terms-of-use messages.

---

## 5. SSH Connection Protocol (RFC 4254)

After successful authentication, the connection layer multiplexes logical channels. Every interactive shell, forwarded port, SFTP session, and X11 session is a separate channel.

### 5.1 Channel Lifecycle

```
Client                                         Server
  |                                              |
  |---SSH_MSG_CHANNEL_OPEN (90) --------------->|
  |   channel-type, sender-channel,              |
  |   initial-window-size, max-packet-size       |
  |                                              |
  |<--SSH_MSG_CHANNEL_OPEN_CONFIRMATION (91) ----|
  |   recipient-channel, sender-channel,         |
  |   initial-window-size, max-packet-size       |
  |                                              |
  |   [data flows both directions]               |
  |                                              |
  |---SSH_MSG_CHANNEL_EOF (96) ----------------- |
  |<--SSH_MSG_CHANNEL_EOF (96) -----------------|
  |                                              |
  |---SSH_MSG_CHANNEL_CLOSE (97) -------------->|
  |<--SSH_MSG_CHANNEL_CLOSE (97) --------------|
```

Each side assigns its own channel number locally. The `recipient-channel` in messages refers to the number the other side assigned.

### 5.2 Flow Control — Window Size

SSH has per-channel flow control. Each side maintains a **window size** — the number of bytes it is willing to receive without sending a window adjustment. Data can only be sent up to the window size. After consuming data, the receiver sends a window adjustment to replenish the window.

```
SSH_MSG_CHANNEL_DATA (94)
  uint32   recipient-channel
  string   data

SSH_MSG_CHANNEL_WINDOW_ADJUST (93)
  uint32   recipient-channel
  uint32   bytes-to-add
```

This prevents a sender from overwhelming a slow receiver.

### 5.3 Channel Types

**session** — Used for shell, exec, subsystem (SFTP).

Open message carries no additional data. After open, the client sends requests:

```
SSH_MSG_CHANNEL_REQUEST (98)
  uint32   recipient-channel
  string   request-type
  boolean  want-reply
  ...type-specific data...
```

Request types:

| Request Type      | Purpose                                               |
|-------------------|-------------------------------------------------------|
| `pty-req`         | Request a pseudo-terminal (for interactive sessions)  |
| `env`             | Set an environment variable                           |
| `shell`           | Start the user's default shell                        |
| `exec`            | Execute a specific command                            |
| `subsystem`       | Start a subsystem (e.g., `sftp`)                      |
| `window-change`   | Terminal window size has changed                      |
| `signal`          | Deliver a signal to the remote process                |
| `exit-status`     | (server→client) Remote process exited with status     |
| `exit-signal`     | (server→client) Remote process killed by signal       |

**direct-tcpip** — Client requests a forwarded TCP connection to an arbitrary host:port. Used for local port forwarding.

```
SSH_MSG_CHANNEL_OPEN
  string   "direct-tcpip"
  uint32   sender-channel
  uint32   initial-window-size
  uint32   maximum-packet-size
  string   host-to-connect
  uint32   port-to-connect
  string   originator-IP-address
  uint32   originator-port
```

**forwarded-tcpip** — Server initiates a channel for remote port forwarding. The server opens this channel to tell the client that a connection arrived on a previously requested forwarded port.

**x11** — X11 display forwarding. The server opens this channel when the remote application connects to the forwarded X11 socket.

**auth-agent@openssh.com** — Agent forwarding.

### 5.4 Pseudo-Terminal (PTY) Request

For interactive sessions, the client requests a PTY with terminal type, dimensions, and terminal modes:

```
SSH_MSG_CHANNEL_REQUEST
  string   "pty-req"
  boolean  want-reply
  string   TERM environment variable value (e.g., "xterm-256color")
  uint32   terminal-width-characters
  uint32   terminal-height-rows
  uint32   terminal-width-pixels
  uint32   terminal-height-pixels
  string   encoded-terminal-modes
```

Terminal modes encode settings like baud rate, ICRNL (map CR to NL on input), OPOST (output processing), etc. Each mode is encoded as a byte opcode followed by a uint32 value.

---

## 6. Cryptographic Primitives and Algorithms

### 6.1 Block Ciphers and Stream Ciphers

**AES-CTR (Counter Mode)**

AES in CTR mode turns the block cipher into a stream cipher. A counter is encrypted to produce a keystream, which is XORed with plaintext.

```
Keystream block N = AES_K(IV + N)
Ciphertext N = Plaintext N XOR Keystream N
```

Properties: Parallelizable, random access, no padding needed. Does NOT provide integrity by itself — requires a separate MAC.

**AES-GCM (Galois/Counter Mode)**

AEAD (Authenticated Encryption with Associated Data). Combines CTR mode encryption with GHASH authentication in a single pass.

```
Ciphertext = AES-CTR(plaintext)
Auth tag   = GHASH(aad || ciphertext) XOR AES_K(J0)
```

In SSH, the `packet_length` field is authenticated but not encrypted (it is "associated data"). The payload is encrypted and authenticated. No separate MAC is needed; the 16-byte auth tag serves as the MAC.

**ChaCha20-Poly1305 (chacha20-poly1305@openssh.com)**

A stream cipher + MAC combination. ChaCha20 is an ARX (Add-Rotate-XOR) cipher with no branches and no table lookups — immune to timing side-channels. Poly1305 is a one-time MAC.

OpenSSH's implementation is special: it uses TWO ChaCha20 instances:
- One for encrypting the packet length field (uses key `K_1`, counter 0)
- One for encrypting the payload (uses key `K_2`, counter 1)

The Poly1305 key is derived from ChaCha20 with counter 0 (of the main instance). This ensures the length field is not predictable even under a chosen-ciphertext attack.

```
K_len, K_main = first 32 bytes, last 32 bytes of 64-byte key

encrypted_length = ChaCha20(K_len, seqnr, 0) XOR packet_length
encrypted_payload = ChaCha20(K_main, seqnr, 1) XOR payload

poly1305_key = ChaCha20(K_main, seqnr, 0)[0:32]
tag = Poly1305(poly1305_key, encrypted_length || encrypted_payload)
```

**Why ChaCha20-Poly1305 is preferred**: No padding oracle attacks (no block boundary issues), constant-time, performs well on systems without AES hardware acceleration (e.g., embedded systems, older ARMv7 without AES-NI).

### 6.2 MAC Algorithms

**HMAC-SHA2-256-ETM**

Encrypt-then-MAC: the MAC is computed over the encrypted packet including the length field (but not the sequence number separately from the MAC input). OpenSSH's `*-etm@openssh.com` variants use encrypt-then-MAC.

Standard HMAC variants compute: `HMAC(seqnr || unencrypted_packet)` — MAC-then-Encrypt. ETM variants compute: `HMAC(seqnr || encrypted_packet)`. ETM is strictly better because:
- Allows length decryption and MAC verification before decryption (prevents padding oracle attacks)
- MAC is over what is actually transmitted

**UMAC**

A fast MAC based on polynomial hashing over GF(2^128). Faster than HMAC-SHA2 but requires a pseudorandom function (AES) as an inner layer. UMAC-128-etm is an excellent choice when throughput matters.

### 6.3 Key Exchange Algorithms

| Algorithm                          | Security | Notes                                    |
|------------------------------------|----------|------------------------------------------|
| `curve25519-sha256`                | ~128-bit | Elliptic Curve DH, Bernstein's curve     |
| `ecdh-sha2-nistp256`               | ~128-bit | NIST P-256, potential NSA backdoor concern |
| `ecdh-sha2-nistp384`               | ~192-bit | NIST P-384                               |
| `diffie-hellman-group16-sha512`    | ~128-bit | 4096-bit DH, slower                      |
| `diffie-hellman-group18-sha512`    | ~192-bit | 8192-bit DH, very slow                   |
| `diffie-hellman-group-exchange-sha256` | varies | Negotiated group size                |
| `sntrup761x25519-sha512@openssh.com` | post-quantum | Hybrid PQ + classical          |

### 6.4 Host Key Algorithms

| Algorithm           | Key Size | Notes                                     |
|---------------------|----------|-------------------------------------------|
| `ssh-ed25519`       | 256-bit  | Edwards curve, fast, small, preferred     |
| `ecdsa-sha2-nistp256` | 256-bit | NIST curve, concern about NIST constants  |
| `rsa-sha2-512`      | ≥2048-bit | RSA with SHA-512 hashing (not SHA-1)     |
| `rsa-sha2-256`      | ≥2048-bit | RSA with SHA-256                          |
| `ssh-rsa`           | ≥2048-bit | SHA-1, **deprecated**, insecure          |
| `sk-ssh-ed25519@openssh.com` | 256-bit | FIDO2/U2F hardware security key |

---

## 7. Key Exchange In Depth

### 7.1 Diffie-Hellman Group Exchange (diffie-hellman-group-exchange-sha256)

The client and server negotiate the DH group (prime and generator) dynamically:

```
Client                                         Server
  |                                              |
  |---SSH_MSG_KEX_DH_GEX_REQUEST (34) -------->|
  |   min=1024, n=2048, max=8192                |
  |                                              |
  |<--SSH_MSG_KEX_DH_GEX_GROUP (31) -----------|
  |   p (safe prime), g (generator)             |
  |                                              |
  |---SSH_MSG_KEX_DH_GEX_INIT (32) ----------->|
  |   e = g^x mod p  (client ephemeral pubkey)  |
  |                                              |
  |<--SSH_MSG_KEX_DH_GEX_REPLY (33) -----------|
  |   K_S (server host key)                     |
  |   f = g^y mod p  (server ephemeral pubkey)  |
  |   sig_H                                     |
  |                                              |
  | Client computes:                             |
  | K = f^x mod p = g^(xy) mod p                |
  | H = hash(V_C || V_S || I_C || I_S ||        |
  |          K_S || min || n || max ||           |
  |          p || g || e || f || K)              |
  | Verifies sig_H using K_S                     |
```

**H is the exchange hash**, also called the session identifier on first key exchange.

### 7.2 Elliptic Curve Diffie-Hellman (curve25519-sha256)

Curve25519 is a Montgomery curve: `y^2 = x^3 + 486662x^2 + x` over `GF(2^255 - 19)`.

```
Client                                         Server
  |                                              |
  |---SSH_MSG_KEX_ECDH_INIT (30) ------------>  |
  |   Q_C = client ephemeral public key (32B)   |
  |                                              |
  |<--SSH_MSG_KEX_ECDH_REPLY (31) --------------|
  |   K_S = server host public key              |
  |   Q_S = server ephemeral public key (32B)   |
  |   sig = signature over H                    |
  |                                              |
  | Client computes:                             |
  | K = X25519(client_priv, Q_S)                |
  | H = hash(V_C || V_S || I_C || I_S ||        |
  |          K_S || Q_C || Q_S || K)            |
  | Verifies sig over H using K_S               |
```

**Why curve25519?**
- Resistant to small-subgroup attacks by design (cofactor 8, but DH ignores this via clamping)
- Twist-secure (invalid public key attacks don't work)
- Constant-time implementations are straightforward
- No patent concerns, no mystery constants

### 7.3 ECDH with NIST Curves

For P-256, the mathematics are identical in structure to curve25519 but use Weierstrass form curves. The main concern is that NIST curve constants were chosen by the NSA, and the exact process used to pick them is not fully transparent.

### 7.4 Hybrid Post-Quantum Key Exchange

`sntrup761x25519-sha512@openssh.com` combines:
- **NTRU Prime (Streamlined)** — lattice-based KEM, post-quantum
- **X25519** — classical ECDH

The shared secret is `SHA-512(ntru_shared_secret || x25519_shared_secret)`. Even if one algorithm is broken (X25519 by a quantum computer, or NTRU by a classical cryptanalytic break), security is not compromised because both must be broken simultaneously.

---

## 8. Host Key Infrastructure

### 8.1 The Trust Problem

When a client connects to a server for the first time, it has no prior knowledge of the server's identity. This is the Trust On First Use (TOFU) problem.

OpenSSH's approach: on first connection, display the host key fingerprint and ask the user to verify it out-of-band (phone call, server console access, etc.). Once accepted, the key is stored in `~/.ssh/known_hosts`.

### 8.2 known_hosts File Format

```
hostname[,hostname...] keytype base64-encoded-key [comment]
```

Examples:
```
github.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl
192.168.1.1 ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC...
[192.168.1.1]:2222 ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBB...
```

Special markers:
- `@cert-authority hostname keytype key` — the key is a CA that signs certificates for hosts matching `hostname`.
- `@revoked hostname keytype key` — the key is revoked; refuse connection even if it matches.
- `!hostname` — negate a pattern.
- Hashed entries: `|1|<salt_b64>|<hash_b64>` — the hostname is stored as HMAC-SHA1 to prevent disclosure of which hosts you connect to.

### 8.3 Host Key Fingerprint

A fingerprint is `SHA-256(base64(public-key-blob))` displayed with a visual prefix:
```
SHA256:nThbg6kXUpJWGl7E1IGOCspRomTxdCARLviKw6E5SY8
```

Or MD5 (legacy):
```
4b:73:f3:b9:78:9d:cf:77:df:8f:9c:19:b5:34:b3:8b
```

### 8.4 SSH Key Scanning

`ssh-keyscan hostname` retrieves server host keys without connecting. Used for populating `known_hosts` in automated environments.

---

## 9. Public Key Authentication In Depth

### 9.1 Key File Formats

**OpenSSH Private Key Format** (`.ssh/id_ed25519`, current format):

```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAA...
-----END OPENSSH PRIVATE KEY-----
```

Internal structure (base64-decoded):
```
"openssh-key-v1\0"     (magic bytes)
string  cipher-name    ("none" or "aes256-ctr" if encrypted)
string  kdf-name       ("none" or "bcrypt")
string  kdf-options    (empty or bcrypt salt+rounds)
uint32  number-of-keys
string  public-key
string  private-key-blob
```

The private key blob (before cipher) contains:
```
uint32  check-int   (same value repeated twice for corruption detection)
uint32  check-int
...private key specific fields...
string  comment
padding bytes
```

**Public Key File** (`.ssh/id_ed25519.pub`):
```
keytype base64-encoded-public-key-blob [comment]
```

The `public-key-blob` for ed25519:
```
string  "ssh-ed25519"
string  32-byte-ed25519-public-key
```

For RSA:
```
string  "ssh-rsa"
mpint   e  (public exponent)
mpint   n  (modulus)
```

### 9.2 authorized_keys Format

```
[options] keytype base64-key [comment]
```

Options (comma-separated before the key):
```
no-port-forwarding         - Disallow TCP forwarding
no-X11-forwarding          - Disallow X11 forwarding
no-agent-forwarding        - Disallow agent forwarding
no-pty                     - No pseudo-terminal
command="cmd"              - Force this command, ignore client's command
from="pattern"             - Only allow from matching IP/hostname
environment="VAR=value"    - Set environment variable (if PermitUserEnvironment yes)
permitopen="host:port"     - Limit forwarding to specific destination
principals="name"          - For certificates, allowed principals
tunnel="n"                 - Tun device number
restrict                   - Enable all restrictions, selectively enable below
```

Example:
```
restrict,command="/usr/local/bin/git-shell",from="192.168.1.0/24" ssh-ed25519 AAAA...
```

### 9.3 Signature Algorithms

For RSA keys, the algorithm used for signatures matters (not just key type). The key is the same RSA key, but the hash used differs:

- `ssh-rsa`: SHA-1 — **broken/deprecated** (collision attacks possible)
- `rsa-sha2-256`: SHA-256 — current minimum
- `rsa-sha2-512`: SHA-512 — preferred for RSA

For Ed25519, there is no choice — it uses its own defined signing algorithm internally (Schnorr-like with SHA-512 internally). For ECDSA, the curve determines the hash (P-256 → SHA-256, P-384 → SHA-384, P-521 → SHA-512).

---

## 10. SSH Channels and Multiplexing

### 10.1 Channel Numbers

Each side independently assigns channel numbers starting from 0. The `sender-channel` in an `SSH_MSG_CHANNEL_OPEN` is the opener's local channel number. The `recipient-channel` in the confirmation is the other side's local number.

When sending data or requests, you use the **remote** channel number (the one the other side assigned) as the `recipient-channel`.

```
Client side:              Server side:
  channel 0 (shell)         channel 7
  channel 1 (fwd port)      channel 3
  channel 2 (agent)         channel 8
```

When client sends to server, it uses server's numbers (7, 3, 8).
When server sends to client, it uses client's numbers (0, 1, 2).

### 10.2 SSH Multiplexing — ControlMaster

OpenSSH supports connection multiplexing at the application layer. A "master" connection is established, and subsequent "slave" connections reuse it via a Unix domain socket.

Configuration:
```
Host *
  ControlMaster auto
  ControlPath ~/.ssh/cm-%r@%h:%p
  ControlPersist 10m
```

`ControlMaster auto`: Be a master if no master exists; be a slave if one does.
`ControlPersist 10m`: Keep master alive 10 minutes after last client disconnects.

This makes subsequent SSH connections to the same host nearly instantaneous (no TCP, TLS, or key exchange overhead).

### 10.3 Extended Data

In addition to normal channel data, channels can carry extended data with a type code:

```
SSH_MSG_CHANNEL_EXTENDED_DATA (95)
  uint32   recipient-channel
  uint32   data-type-code
  string   data
```

Currently defined types:
- `SSH_EXTENDED_DATA_STDERR = 1` — stderr from remote process

This allows stderr to be separately distinguished from stdout, unlike plain TCP which would mix them.

---

## 11. Port Forwarding and Tunneling

### 11.1 Local Port Forwarding (-L)

```
ssh -L [bind_address:]local_port:remote_host:remote_port user@ssh_server
```

The client listens on `local_port`. When a local application connects to that port, SSH opens a `direct-tcpip` channel to `remote_host:remote_port` through the server.

```
Local App   SSH Client       SSH Server         Remote Service
    |----------->| direct-tcpip channel |----------->|
    localhost:8080            (server connects to)   db.internal:5432
```

Use case: Access a database only reachable from the SSH server, from your local machine.

### 11.2 Remote Port Forwarding (-R)

```
ssh -R [bind_address:]remote_port:local_host:local_port user@ssh_server
```

The client sends `SSH_MSG_GLOBAL_REQUEST` asking the server to listen:

```
SSH_MSG_GLOBAL_REQUEST (80)
  string   "tcpip-forward"
  boolean  want-reply
  string   address-to-bind
  uint32   port-number
```

When someone connects to `remote_port` on the server, the server opens a `forwarded-tcpip` channel to the client, which then connects to `local_host:local_port`.

```
Remote User  SSH Server       SSH Client         Local Service
    |----------->| forwarded-tcpip channel |----------->|
    server:9090               (client connects to)    localhost:3000
```

Use case: Expose a local development server to the internet through a server with a public IP.

### 11.3 Dynamic Port Forwarding (-D) — SOCKS Proxy

```
ssh -D [bind_address:]local_port user@ssh_server
```

OpenSSH acts as a SOCKS4/SOCKS5 proxy on `local_port`. For each SOCKS connection, it opens a `direct-tcpip` channel to the destination address. All traffic is forwarded through the SSH server.

```
Browser --> SOCKS5 proxy (localhost:1080) --> SSH tunnel --> SSH server --> internet
```

### 11.4 TUN/TAP Tunneling (Layer 3/Layer 2 VPN)

```
ssh -w 0:0 user@server
```

Requires `PermitTunnel yes` on server. Creates `tun0` interfaces on both ends. IP packets can be routed through the tunnel.

Channel type: `tun@openssh.com`
Channel open data:
```
uint32   tunnel mode (1=point-to-point/tun, 2=ethernet/tap)
uint32   unit number (device number, e.g., 0 for tun0)
```

---

## 12. SSH Agent and Agent Forwarding

### 12.1 SSH Agent

The SSH agent is a background process that holds private keys in memory (optionally passphrase-unlocked). The agent communicates with SSH clients via a Unix domain socket (typically `SSH_AUTH_SOCK`).

**Agent protocol** (separate from SSH transport, runs over Unix socket):

```
SSH_AGENTC_REQUEST_IDENTITIES (11)
  → SSH_AGENT_IDENTITIES_ANSWER (12)
       uint32      num-keys
       string[]    public-key-blob
       string[]    comment

SSH_AGENTC_SIGN_REQUEST (13)
  string  public-key-blob
  string  data-to-sign
  uint32  flags (e.g., SSH_AGENT_RSA_SHA2_256 = 2)
  → SSH_AGENT_SIGN_RESPONSE (14)
       string  signature

SSH_AGENTC_ADD_IDENTITY (17)
  string  key-type
  ...private key fields...
  string  comment
  → SSH_AGENT_SUCCESS (6)

SSH_AGENTC_REMOVE_IDENTITY (18)
  string  public-key-blob
  → SSH_AGENT_SUCCESS (6)

SSH_AGENTC_ADD_ID_CONSTRAINED (25)
  ...same as ADD_IDENTITY but with constraints...
  Constraint: SSH_AGENT_CONSTRAIN_LIFETIME (1) + uint32 seconds
  Constraint: SSH_AGENT_CONSTRAIN_CONFIRM (2)  (require confirmation)
```

**Key point**: The private key material *never leaves the agent*. The SSH client requests a signature from the agent, and the agent performs the signing operation internally. This isolates key material from the SSH client process.

### 12.2 Agent Forwarding

```
Client → Server: SSH_MSG_CHANNEL_REQUEST "auth-agent-req@openssh.com"
```

If forwarding is enabled, when the SSH server needs to authenticate to another server, it opens an `auth-agent@openssh.com` channel back to the client:

```
SSH Server → Client: SSH_MSG_CHANNEL_OPEN "auth-agent@openssh.com"
```

The server then proxies agent protocol messages through this channel to the original agent.

```
[Your Laptop (agent)] <--SSH--> [Server A] <--SSH--> [Server B]
                         ↑ agent fwd channel ↑
```

**Security warning**: Agent forwarding gives root on Server A the ability to use your agent. If Server A is compromised, the attacker can use your keys to authenticate to Server B. Use `-A` only for hosts you trust completely.

**Better alternative**: `ProxyJump` (`-J`) or `ProxyCommand` — these connect to Server B through Server A without forwarding the agent.

---

## 13. SSH Certificates

### 13.1 Motivation

PKI (Public Key Infrastructure) for SSH. Instead of distributing public keys to `authorized_keys` on every server and `known_hosts` on every client, a Certificate Authority signs keys. You only need to trust the CA.

### 13.2 Certificate Format

An SSH certificate is a public key with additional signed fields:

```
string    certificate-type
  e.g., "ssh-ed25519-cert-v01@openssh.com"

string    nonce                  (random, prevents hash collisions)
...key-type specific fields...  (the public key)
uint64    serial                 (CA-assigned serial number)
uint32    type                   (1=user, 2=host)
string    key-id                 (human-readable identifier)
string[]  valid-principals       (usernames or hostnames)
uint64    valid-after            (Unix timestamp)
uint64    valid-before           (Unix timestamp)
string    critical-options       (force-command, source-address)
string    extensions             (permit-pty, permit-port-forwarding, etc.)
string    reserved
string    signature-key          (CA public key)
string    signature              (CA signature over all above)
```

### 13.3 User Certificates

The CA signs user keys. The server trusts the CA key (in `authorized_keys` or `TrustedUserCAKeys`):

```
# /etc/ssh/sshd_config
TrustedUserCAKeys /etc/ssh/user_ca.pub
```

Client certificate usage:
```
ssh -i ~/.ssh/id_ed25519-cert.pub -i ~/.ssh/id_ed25519 user@server
```

The certificate specifies:
- `valid-principals`: which usernames can log in with this cert
- `valid-before`: expiry time (certificates can expire, unlike keys)
- `force-command`: restrict what command can be run
- `source-address`: restrict which IPs can use this cert

### 13.4 Host Certificates

The CA signs server host keys. Clients trust the CA:

```
# ~/.ssh/known_hosts (or /etc/ssh/known_hosts)
@cert-authority *.example.com ssh-ed25519 AAAA...

# /etc/ssh/sshd_config
HostCertificate /etc/ssh/ssh_host_ed25519_key-cert.pub
```

Benefits: When a server is replaced or its key changes, the new key only needs to be re-signed by the CA. Clients don't need to update `known_hosts` for individual servers.

### 13.5 Certificate Generation

```bash
# Generate CA key pair (do this once)
ssh-keygen -t ed25519 -f user_ca -C "user CA"

# Sign a user's public key
ssh-keygen -s user_ca -I "alice@example.com" -n alice,root \
           -V +52w -z 42 alice_id_ed25519.pub

# -s: signing CA key
# -I: certificate identity (key-id field, human label)
# -n: valid principals (comma-separated usernames)
# -V: validity period (+52w = 52 weeks from now)
# -z: serial number

# Sign a host key
ssh-keygen -s host_ca -I "web01.example.com" -h \
           -n web01,web01.example.com,192.168.1.10 \
           -V +1y /etc/ssh/ssh_host_ed25519_key.pub

# -h: this is a host certificate
```

---

## 14. Wire Format and Packet Structure

### 14.1 SSH Data Types

All SSH protocol fields use defined encodings:

| Type    | Encoding                                                                       |
|---------|--------------------------------------------------------------------------------|
| byte    | 1 byte                                                                         |
| boolean | 1 byte: 0=false, any-nonzero=true (send 1)                                     |
| uint32  | 4 bytes, big-endian                                                            |
| uint64  | 8 bytes, big-endian                                                            |
| string  | uint32 length + length bytes (binary safe, can contain NUL)                    |
| mpint   | uint32 byte-count + big-endian bytes, 0 if zero, high bit indicates sign       |
| name-list | uint32 length + comma-separated ASCII names                                  |

**mpint examples**:
```
value 0:       00 00 00 00
value 1:       00 00 00 01 01
value 128:     00 00 00 02 00 80  ← needs leading 0x00 because high bit would be 1
value -1:      00 00 00 01 ff
value 2^32:    00 00 00 05 01 00 00 00 00
```

### 14.2 Complete Connection Trace (ASCII)

```
TCP SYN/SYN-ACK/ACK (3-way handshake)

CLIENT → SERVER                        SERVER → CLIENT
══════════════════════════════════════════════════════
[Plaintext]
"SSH-2.0-OpenSSH_9.6\r\n"  ────────>
                            <──────── "SSH-2.0-OpenSSH_9.6\r\n"

[Binary Packet Protocol begins, no encryption yet]

SSH_MSG_KEXINIT (type=20)   ────────>
                            <──────── SSH_MSG_KEXINIT (type=20)

SSH_MSG_KEX_ECDH_INIT       ────────>
  (type=30)
  client_ephemeral_pub (32B)

                            <──────── SSH_MSG_KEX_ECDH_REPLY
                                        (type=31)
                                        server_host_key
                                        server_ephemeral_pub
                                        signature_over_H

[Both sides derive K, compute H, verify]

SSH_MSG_NEWKEYS (type=21)   ────────>
                            <──────── SSH_MSG_NEWKEYS (type=21)

[All subsequent packets encrypted + MACed]

SSH_MSG_SERVICE_REQUEST     ────────>
  (type=5)
  "ssh-userauth"

                            <──────── SSH_MSG_SERVICE_ACCEPT
                                        (type=6)
                                        "ssh-userauth"

SSH_MSG_USERAUTH_REQUEST    ────────>
  (type=50)
  username: "alice"
  service: "ssh-connection"
  method: "none"

                            <──────── SSH_MSG_USERAUTH_FAILURE
                                        (type=51)
                                        methods: "publickey,password"

SSH_MSG_USERAUTH_REQUEST    ────────>
  (type=50)
  username: "alice"
  service: "ssh-connection"
  method: "publickey"
  FALSE (probe)
  key-algo: "ssh-ed25519"
  public-key-blob

                            <──────── SSH_MSG_USERAUTH_PK_OK
                                        (type=60)
                                        key-algo
                                        public-key-blob

SSH_MSG_USERAUTH_REQUEST    ────────>
  (type=50)
  username: "alice"
  service: "ssh-connection"
  method: "publickey"
  TRUE (actual)
  key-algo: "ssh-ed25519"
  public-key-blob
  signature

                            <──────── SSH_MSG_USERAUTH_SUCCESS
                                        (type=52)

SSH_MSG_CHANNEL_OPEN        ────────>
  (type=90)
  "session"
  sender=0, window=2097152, max_pkt=32768

                            <──────── SSH_MSG_CHANNEL_OPEN_CONFIRMATION
                                        (type=91)
                                        recipient=0, sender=7
                                        window=2097152, max_pkt=32768

SSH_MSG_CHANNEL_REQUEST     ────────>
  (type=98)
  channel=7
  "pty-req"
  want-reply=TRUE
  "xterm-256color"
  80cols, 24rows

                            <──────── SSH_MSG_CHANNEL_SUCCESS (type=99)

SSH_MSG_CHANNEL_REQUEST     ────────>
  (type=98)
  channel=7
  "shell"
  want-reply=TRUE

                            <──────── SSH_MSG_CHANNEL_SUCCESS (type=99)

[Interactive session: SSH_MSG_CHANNEL_DATA (94) in both directions]

SSH_MSG_CHANNEL_DATA        ────────>   (keystroke "ls\n")
                            <──────── SSH_MSG_CHANNEL_DATA    (terminal output)
                            <──────── SSH_MSG_CHANNEL_EXTENDED_DATA  (stderr if any)

[Session end]

                            <──────── SSH_MSG_CHANNEL_REQUEST
                                        "exit-status" want-reply=FALSE
                                        exit code: 0

                            <──────── SSH_MSG_CHANNEL_EOF (type=96)
SSH_MSG_CHANNEL_EOF         ────────>
                            <──────── SSH_MSG_CHANNEL_CLOSE (type=97)
SSH_MSG_CHANNEL_CLOSE       ────────>

SSH_MSG_DISCONNECT (type=1) ────────>
TCP FIN/FIN-ACK
```

### 14.3 Packet Hex Dump Example

A `SSH_MSG_CHANNEL_DATA` packet carrying the 4 bytes `"ls\r\n"`:

```
Before encryption (plaintext):
Offset  Data (hex)                              ASCII
000000  00 00 00 24                             ....  ← packet_length = 36
000004  0a                                      .     ← padding_length = 10
000005  5e                                      ^     ← msg type 94 = SSH_MSG_CHANNEL_DATA
000006  00 00 00 07                             ....  ← recipient channel = 7
00000a  00 00 00 04                             ....  ← data length = 4
00000e  6c 73 0d 0a                             ls..  ← "ls\r\n"
000012  00 00 00 00 00 00 00 00 00 00           ..........  ← 10 bytes random padding
                                               [+32 bytes HMAC-SHA2-256]
```

### 14.4 Rekeying

SSH connections should rekey periodically to limit the amount of data encrypted under the same key (limits exposure from key compromise and prevents nonce reuse in CTR/GCM modes).

OpenSSH rekeys:
- After 1 GB of data (by default)
- After 1 hour (by default)

Either side can initiate rekey by sending a new `SSH_MSG_KEXINIT`. The process is identical to initial key exchange, but `session_id` remains the original H value.

---

## 15. SSH Configuration Files

### 15.1 Client Configuration (~/.ssh/config and /etc/ssh/ssh_config)

Configuration is evaluated in order: command-line options → `~/.ssh/config` → `/etc/ssh/ssh_config`. First match wins for each directive.

```
# Global defaults
Host *
    ServerAliveInterval 60
    ServerAliveCountMax 3
    AddKeysToAgent yes
    IdentityFile ~/.ssh/id_ed25519

# Specific host
Host prod-web
    HostName 10.0.1.50
    User deploy
    Port 2222
    IdentityFile ~/.ssh/deploy_key
    ForwardAgent no

# Jump through bastion
Host internal-*
    ProxyJump bastion.example.com
    User alice

# Multiplexing
Host *
    ControlMaster auto
    ControlPath ~/.ssh/cm-%C
    ControlPersist 5m
```

Key directives:

| Directive              | Purpose                                                          |
|------------------------|------------------------------------------------------------------|
| `HostName`             | Actual hostname/IP (allows alias)                                |
| `User`                 | Default username                                                 |
| `Port`                 | Default port                                                     |
| `IdentityFile`         | Private key to use                                               |
| `IdentitiesOnly`       | Only use listed keys, not agent keys                             |
| `ProxyJump`            | Jump through intermediate host(s)                                |
| `ProxyCommand`         | Custom command to establish connection                           |
| `ForwardAgent`         | Enable agent forwarding                                          |
| `ForwardX11`           | Enable X11 forwarding                                            |
| `LocalForward`         | Local port forwarding                                            |
| `RemoteForward`        | Remote port forwarding                                           |
| `StrictHostKeyChecking`| `yes`/`no`/`ask`/`accept-new`                                    |
| `KnownHostsFile`       | Path(s) to known_hosts files                                     |
| `ServerAliveInterval`  | Keepalive interval (seconds)                                     |
| `Compression`          | Enable compression                                               |
| `Ciphers`              | Allowed ciphers (in preference order)                            |
| `MACs`                 | Allowed MAC algorithms                                           |
| `KexAlgorithms`        | Allowed key exchange algorithms                                  |
| `HostKeyAlgorithms`    | Accepted host key types                                          |
| `PubkeyAuthentication` | Enable/disable public key auth                                   |
| `PasswordAuthentication`| Enable/disable password auth                                    |

### 15.2 Server Configuration (/etc/ssh/sshd_config)

```
# Network
Port 22
ListenAddress 0.0.0.0
AddressFamily any

# Host Keys (in preference order)
HostKey /etc/ssh/ssh_host_ed25519_key
HostKey /etc/ssh/ssh_host_rsa_key

# Authentication
PermitRootLogin no                    # or "prohibit-password"
MaxAuthTries 3
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys .ssh/authorized_keys2
PasswordAuthentication no
ChallengeResponseAuthentication no
KbdInteractiveAuthentication no
UsePAM yes

# Authorization
AllowUsers alice bob deploy
AllowGroups sshusers
DenyUsers root

# Algorithms (modern hardened config)
KexAlgorithms sntrup761x25519-sha512@openssh.com,curve25519-sha256,curve25519-sha256@libssh.org
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com

# Certificates
TrustedUserCAKeys /etc/ssh/user_ca.pub

# Sessions
MaxSessions 10
ClientAliveInterval 300
ClientAliveCountMax 2

# Features
X11Forwarding no
AllowTcpForwarding yes
AllowAgentForwarding no
PermitTunnel no
Banner /etc/ssh/banner.txt

# Subsystems
Subsystem sftp /usr/lib/openssh/sftp-server

# Match blocks for per-user/group/host overrides
Match User sftp-only
    ForceCommand internal-sftp
    ChrootDirectory /srv/sftp/%u
    AllowTcpForwarding no
    X11Forwarding no
```

---

## 16. Security Threat Model and Attack Surface

### 16.1 What SSH Protects Against

**Eavesdropping**: All data after key exchange is encrypted. An attacker recording the TCP stream cannot read passwords, commands, or output.

**Tampering**: MAC on every packet prevents modification. An attacker cannot inject commands or modify output without detection (which causes connection termination).

**Replay attacks**: Per-packet sequence numbers in MAC computation prevent replaying old packets.

**Man-in-the-middle during active connection**: Once key exchange is complete and verified, all subsequent data is bound to the shared secret. An active MITM would need to break the key exchange.

### 16.2 What SSH Does NOT Protect Against

**Initial MITM (TOFU problem)**: If an attacker is positioned during the *first* connection, before the host key is known, they can substitute their own keys. The user must verify the fingerprint out-of-band.

**Compromised endpoint**: If your laptop or the server is compromised (malware, rootkit), all bets are off. SSH cannot protect data that is decrypted in a compromised process.

**DNS poisoning without strict host key checking**: If `StrictHostKeyChecking no`, a DNS-poisoned connection will silently connect to the wrong server.

### 16.3 Specific Attack Vectors

**Terrapin Attack (CVE-2023-48795)**

A prefix truncation attack against ChaCha20-Poly1305 and CBC-EtM modes. An attacker performing an active MITM during the handshake can silently drop some initial plaintext messages. This can be used to downgrade the negotiated extensions (e.g., remove `strict-kex` which prevents the attack).

Fixed in OpenSSH 9.6 with `strict-kex` — a new extension that adds strict sequence number checking during key exchange.

**Timing attacks on authentication**

If authentication failure responses arrive faster for non-existent users, an attacker can enumerate valid usernames. Modern OpenSSH uses `auth-options` and delays to mitigate this.

**Weak host keys**

`ssh-rsa` (SHA-1) host keys are now deprecated. SHA-1 collisions are practical (SHAttered attack). Use Ed25519 or RSA-SHA2.

**Integer overflow in CBC padding**

Older SSH implementations using CBC mode had padding oracle vulnerabilities (Lucky Thirteen class). CBC mode is now deprecated; CTR, GCM, and ChaCha20 are used instead.

**Excessive privilege in sshd process model**

Traditional sshd runs as root. OpenSSH uses privilege separation: a small privileged monitor process handles key operations, and an unprivileged pre-authentication process handles the network. After auth, another unprivileged process handles the session.

### 16.4 Hardening Checklist

```
# Disable weak algorithms
KexAlgorithms -diffie-hellman-group1-sha1,-diffie-hellman-group14-sha1
Ciphers -3des-cbc,-aes128-cbc,-aes192-cbc,-aes256-cbc,-arcfour*,-blowfish-cbc,-cast128-cbc
MACs -hmac-md5,-hmac-sha1,-umac-64@openssh.com,-hmac-ripemd160
HostKeyAlgorithms -ssh-rsa,-ssh-dss

# Disable password auth if possible
PasswordAuthentication no

# Limit users
AllowGroups ssh-users

# Rate limiting (use fail2ban or nftables)
# MaxStartups 10:30:100  (start:rate:full)

# Disable features not needed
AllowAgentForwarding no
X11Forwarding no
PermitTunnel no

# Use non-default port (security through obscurity, reduces log noise)
Port 2222
```

---

## 17. C Implementation

### 17.1 Core SSH Server Skeleton

The following implements a minimal but complete SSH transport layer in C:

```c
/*
 * ssh_minimal.c — Minimal SSH-2 transport layer implementation
 *
 * Demonstrates:
 *   - Version exchange
 *   - KEXINIT sending/parsing
 *   - Binary packet read/write (no encryption for clarity)
 *   - Packet framing
 *
 * Compile: gcc -Wall -Wextra -o ssh_minimal ssh_minimal.c -lcrypto
 * Requires: OpenSSL (libcrypto)
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <openssl/evp.h>
#include <openssl/rand.h>
#include <openssl/sha.h>
#include <errno.h>

/* SSH message type constants */
#define SSH_MSG_DISCONNECT              1
#define SSH_MSG_IGNORE                  2
#define SSH_MSG_UNIMPLEMENTED           3
#define SSH_MSG_SERVICE_REQUEST         5
#define SSH_MSG_SERVICE_ACCEPT          6
#define SSH_MSG_KEXINIT                 20
#define SSH_MSG_NEWKEYS                 21
#define SSH_MSG_USERAUTH_REQUEST        50
#define SSH_MSG_USERAUTH_FAILURE        51
#define SSH_MSG_USERAUTH_SUCCESS        52
#define SSH_MSG_CHANNEL_OPEN            90
#define SSH_MSG_CHANNEL_OPEN_CONFIRMATION 91
#define SSH_MSG_CHANNEL_OPEN_FAILURE    92
#define SSH_MSG_CHANNEL_WINDOW_ADJUST   93
#define SSH_MSG_CHANNEL_DATA            94
#define SSH_MSG_CHANNEL_CLOSE           97
#define SSH_MSG_CHANNEL_REQUEST         98

/* SSH disconnect reason codes */
#define SSH_DISCONNECT_HOST_NOT_ALLOWED_TO_CONNECT      1
#define SSH_DISCONNECT_PROTOCOL_ERROR                   2
#define SSH_DISCONNECT_KEY_EXCHANGE_FAILED              3
#define SSH_DISCONNECT_RESERVED                         4
#define SSH_DISCONNECT_MAC_ERROR                        5
#define SSH_DISCONNECT_COMPRESSION_ERROR                6
#define SSH_DISCONNECT_SERVICE_NOT_AVAILABLE            7
#define SSH_DISCONNECT_PROTOCOL_VERSION_NOT_SUPPORTED   8
#define SSH_DISCONNECT_HOST_KEY_NOT_VERIFIABLE          9
#define SSH_DISCONNECT_CONNECTION_LOST                  10
#define SSH_DISCONNECT_BY_APPLICATION                   11
#define SSH_DISCONNECT_TOO_MANY_CONNECTIONS             12
#define SSH_DISCONNECT_AUTH_CANCELLED_BY_USER           13
#define SSH_DISCONNECT_NO_MORE_AUTH_METHODS_AVAILABLE   14
#define SSH_DISCONNECT_ILLEGAL_USER_NAME                15

/* Maximum packet size we handle */
#define SSH_MAX_PACKET_SIZE  (256 * 1024)
#define SSH_BLOCK_SIZE       8  /* For unencrypted padding alignment */

/*
 * SSH Buffer — A simple growable buffer for building/parsing packets
 */
typedef struct {
    uint8_t *data;
    size_t   len;
    size_t   cap;
    size_t   pos;  /* read position */
} ssh_buf_t;

static int buf_init(ssh_buf_t *b, size_t initial_cap) {
    b->data = malloc(initial_cap ? initial_cap : 256);
    if (!b->data) return -1;
    b->len = 0;
    b->cap = initial_cap ? initial_cap : 256;
    b->pos = 0;
    return 0;
}

static void buf_free(ssh_buf_t *b) {
    if (b->data) {
        /* Zero out to avoid leaving sensitive data in heap */
        memset(b->data, 0, b->len);
        free(b->data);
        b->data = NULL;
    }
    b->len = b->cap = b->pos = 0;
}

static int buf_grow(ssh_buf_t *b, size_t need) {
    if (b->len + need <= b->cap) return 0;
    size_t new_cap = b->cap * 2;
    while (new_cap < b->len + need) new_cap *= 2;
    uint8_t *p = realloc(b->data, new_cap);
    if (!p) return -1;
    b->data = p;
    b->cap  = new_cap;
    return 0;
}

/* Append raw bytes */
static int buf_put_bytes(ssh_buf_t *b, const void *data, size_t len) {
    if (buf_grow(b, len) < 0) return -1;
    memcpy(b->data + b->len, data, len);
    b->len += len;
    return 0;
}

/* Append a single byte */
static int buf_put_u8(ssh_buf_t *b, uint8_t v) {
    return buf_put_bytes(b, &v, 1);
}

/* Append a uint32 in big-endian */
static int buf_put_u32(ssh_buf_t *b, uint32_t v) {
    uint8_t buf[4] = {
        (v >> 24) & 0xFF,
        (v >> 16) & 0xFF,
        (v >>  8) & 0xFF,
        (v      ) & 0xFF
    };
    return buf_put_bytes(b, buf, 4);
}

/* Append an SSH string (uint32 length + data) */
static int buf_put_string(ssh_buf_t *b, const void *data, uint32_t len) {
    if (buf_put_u32(b, len) < 0) return -1;
    return buf_put_bytes(b, data, len);
}

/* Append a C string as SSH string */
static int buf_put_cstr(ssh_buf_t *b, const char *s) {
    return buf_put_string(b, s, (uint32_t)strlen(s));
}

/* Read uint32 from buffer at current position */
static int buf_get_u32(ssh_buf_t *b, uint32_t *out) {
    if (b->pos + 4 > b->len) return -1;
    const uint8_t *p = b->data + b->pos;
    *out = ((uint32_t)p[0] << 24) |
           ((uint32_t)p[1] << 16) |
           ((uint32_t)p[2] <<  8) |
           ((uint32_t)p[3]      );
    b->pos += 4;
    return 0;
}

/* Read uint8 from buffer */
static int buf_get_u8(ssh_buf_t *b, uint8_t *out) {
    if (b->pos >= b->len) return -1;
    *out = b->data[b->pos++];
    return 0;
}

/* Read SSH string (returns pointer into buffer, does NOT copy) */
static int buf_get_string_ref(ssh_buf_t *b, const uint8_t **out, uint32_t *len) {
    uint32_t l;
    if (buf_get_u32(b, &l) < 0) return -1;
    if (b->pos + l > b->len) return -1;
    *out = b->data + b->pos;
    *len = l;
    b->pos += l;
    return 0;
}

/*
 * SSH Connection State
 */
typedef struct {
    int      fd;                /* TCP socket */
    uint32_t send_seq;          /* Outgoing packet sequence number */
    uint32_t recv_seq;          /* Incoming packet sequence number */
    
    /* These would hold encryption state in a full implementation */
    /* EVP_CIPHER_CTX *enc_ctx;  */
    /* EVP_CIPHER_CTX *dec_ctx;  */
    /* HMAC_CTX       *mac_send; */
    /* HMAC_CTX       *mac_recv; */

    /* Negotiated algorithms */
    char kex_algo[64];
    char hostkey_algo[64];
    char enc_cs[64];    /* encryption client-to-server */
    char enc_sc[64];    /* encryption server-to-client */
    char mac_cs[64];
    char mac_sc[64];

    /* Session ID (first exchange hash H) */
    uint8_t session_id[32];
    int     session_id_set;
} ssh_conn_t;

/*
 * Read exactly n bytes from fd, handling partial reads and EINTR
 */
static ssize_t read_all(int fd, void *buf, size_t n) {
    size_t done = 0;
    uint8_t *p = buf;
    while (done < n) {
        ssize_t r = read(fd, p + done, n - done);
        if (r < 0) {
            if (errno == EINTR) continue;
            return -1;
        }
        if (r == 0) return (ssize_t)done;  /* EOF */
        done += (size_t)r;
    }
    return (ssize_t)done;
}

/*
 * Write exactly n bytes to fd
 */
static ssize_t write_all(int fd, const void *buf, size_t n) {
    size_t done = 0;
    const uint8_t *p = buf;
    while (done < n) {
        ssize_t w = write(fd, p + done, n - done);
        if (w < 0) {
            if (errno == EINTR) continue;
            return -1;
        }
        done += (size_t)w;
    }
    return (ssize_t)done;
}

/*
 * Send a plaintext SSH packet (no encryption)
 *
 * Binary packet format:
 *   uint32  packet_length    (padlen + payloadlen)
 *   uint8   padding_length
 *   bytes   payload
 *   bytes   random_padding
 *   [MAC]                    (omitted here, no encryption)
 */
static int ssh_send_packet(ssh_conn_t *conn, const uint8_t *payload, size_t payload_len) {
    /* Calculate padding needed to align to SSH_BLOCK_SIZE */
    /* Total without padding = 4 (pkt_len) + 1 (pad_len) + payload_len */
    /* We need (total) to be a multiple of SSH_BLOCK_SIZE */
    size_t base = 1 + payload_len;  /* pad_len byte + payload */
    size_t pad_len = SSH_BLOCK_SIZE - (base % SSH_BLOCK_SIZE);
    if (pad_len < 4) pad_len += SSH_BLOCK_SIZE;

    uint32_t packet_length = (uint32_t)(1 + payload_len + pad_len);

    /* Build the outgoing bytes */
    uint8_t header[5];
    header[0] = (packet_length >> 24) & 0xFF;
    header[1] = (packet_length >> 16) & 0xFF;
    header[2] = (packet_length >>  8) & 0xFF;
    header[3] = (packet_length      ) & 0xFF;
    header[4] = (uint8_t)pad_len;

    uint8_t padding[255];
    RAND_bytes(padding, (int)pad_len);  /* Random padding */

    if (write_all(conn->fd, header, 5) < 0) return -1;
    if (write_all(conn->fd, payload, payload_len) < 0) return -1;
    if (write_all(conn->fd, padding, pad_len) < 0) return -1;

    conn->send_seq++;
    return 0;
}

/*
 * Receive an SSH packet (no decryption)
 * Caller must free *payload_out
 */
static int ssh_recv_packet(ssh_conn_t *conn, uint8_t **payload_out, size_t *payload_len_out) {
    /* Read packet_length (4 bytes) */
    uint8_t len_buf[4];
    if (read_all(conn->fd, len_buf, 4) != 4) {
        fprintf(stderr, "Failed to read packet length\n");
        return -1;
    }
    uint32_t packet_length = ((uint32_t)len_buf[0] << 24) |
                             ((uint32_t)len_buf[1] << 16) |
                             ((uint32_t)len_buf[2] <<  8) |
                             ((uint32_t)len_buf[3]      );

    if (packet_length < 2 || packet_length > SSH_MAX_PACKET_SIZE) {
        fprintf(stderr, "Invalid packet_length: %u\n", packet_length);
        return -1;
    }

    /* Read the rest: pad_len + payload + padding */
    uint8_t *buf = malloc(packet_length);
    if (!buf) return -1;

    if (read_all(conn->fd, buf, packet_length) != (ssize_t)packet_length) {
        free(buf);
        return -1;
    }

    uint8_t pad_len = buf[0];
    if (pad_len < 4 || pad_len + 1 > packet_length) {
        free(buf);
        fprintf(stderr, "Invalid padding_length: %u\n", pad_len);
        return -1;
    }

    size_t payload_len = packet_length - 1 - pad_len;
    uint8_t *payload = malloc(payload_len);
    if (!payload) {
        free(buf);
        return -1;
    }

    memcpy(payload, buf + 1, payload_len);
    free(buf);

    *payload_out = payload;
    *payload_len_out = payload_len;
    conn->recv_seq++;
    return 0;
}

/*
 * Send SSH_MSG_DISCONNECT
 */
static void ssh_send_disconnect(ssh_conn_t *conn, uint32_t reason, const char *msg) {
    ssh_buf_t b;
    buf_init(&b, 64);
    buf_put_u8(&b, SSH_MSG_DISCONNECT);
    buf_put_u32(&b, reason);
    buf_put_cstr(&b, msg);
    buf_put_cstr(&b, "");  /* language tag */
    ssh_send_packet(conn, b.data, b.len);
    buf_free(&b);
}

/*
 * Perform SSH version exchange
 */
static int ssh_version_exchange(ssh_conn_t *conn, int is_server) {
    const char *our_version = "SSH-2.0-minimal_0.1\r\n";
    size_t our_len = strlen(our_version);

    if (write_all(conn->fd, our_version, our_len) < 0) {
        perror("write version");
        return -1;
    }
    printf("[%s] Sent version: %.*s", is_server ? "SERVER" : "CLIENT",
           (int)(our_len - 2), our_version);

    /* Read their version string — it ends with \r\n or \n */
    char peer_version[256];
    int i = 0;
    while (i < (int)(sizeof(peer_version) - 1)) {
        char c;
        if (read_all(conn->fd, &c, 1) != 1) return -1;
        if (c == '\n') break;
        if (c != '\r') peer_version[i++] = c;
    }
    peer_version[i] = '\0';

    printf("[%s] Received version: %s\n", is_server ? "SERVER" : "CLIENT",
           peer_version);

    /* Validate it starts with SSH-2.0 */
    if (strncmp(peer_version, "SSH-2.0-", 8) != 0 &&
        strncmp(peer_version, "SSH-2.", 6) != 0) {
        fprintf(stderr, "Unsupported protocol version: %s\n", peer_version);
        return -1;
    }

    /* Skip any banner lines (which start with anything other than SSH-) */
    return 0;
}

/*
 * Build and send SSH_MSG_KEXINIT
 */
static int ssh_send_kexinit(ssh_conn_t *conn) {
    ssh_buf_t b;
    if (buf_init(&b, 512) < 0) return -1;

    buf_put_u8(&b, SSH_MSG_KEXINIT);

    /* 16 random bytes cookie */
    uint8_t cookie[16];
    RAND_bytes(cookie, sizeof(cookie));
    buf_put_bytes(&b, cookie, 16);

    /* name-lists — comma-separated, most preferred first */
    buf_put_cstr(&b, "curve25519-sha256,diffie-hellman-group14-sha256");
    buf_put_cstr(&b, "ssh-ed25519,rsa-sha2-256");
    buf_put_cstr(&b, "chacha20-poly1305@openssh.com,aes256-ctr");   /* enc c2s */
    buf_put_cstr(&b, "chacha20-poly1305@openssh.com,aes256-ctr");   /* enc s2c */
    buf_put_cstr(&b, "hmac-sha2-256-etm@openssh.com,hmac-sha2-256");/* mac c2s */
    buf_put_cstr(&b, "hmac-sha2-256-etm@openssh.com,hmac-sha2-256");/* mac s2c */
    buf_put_cstr(&b, "none");   /* compression c2s */
    buf_put_cstr(&b, "none");   /* compression s2c */
    buf_put_cstr(&b, "");       /* languages c2s */
    buf_put_cstr(&b, "");       /* languages s2c */

    buf_put_u8(&b, 0);      /* first_kex_packet_follows = FALSE */
    buf_put_u32(&b, 0);     /* reserved */

    int ret = ssh_send_packet(conn, b.data, b.len);
    buf_free(&b);
    return ret;
}

/*
 * Parse a received KEXINIT packet
 * Updates conn->kex_algo, etc. based on intersection with our preferences
 */
static int ssh_parse_kexinit(ssh_conn_t *conn, const uint8_t *payload, size_t len) {
    /* Minimum: 1 (type) + 16 (cookie) + many name-lists */
    if (len < 17) return -1;
    if (payload[0] != SSH_MSG_KEXINIT) return -1;

    ssh_buf_t b;
    b.data = (uint8_t *)payload;
    b.len  = len;
    b.cap  = len;
    b.pos  = 1;  /* skip message type */

    /* Skip 16-byte cookie */
    b.pos += 16;

    /* For each name-list, we would intersect with our preferences.
       Here we just print them. */
    const char *field_names[] = {
        "kex_algorithms",
        "server_host_key_algorithms",
        "enc_c2s", "enc_s2c",
        "mac_c2s", "mac_s2c",
        "comp_c2s", "comp_s2c",
        "lang_c2s", "lang_s2c"
    };

    for (int i = 0; i < 10; i++) {
        const uint8_t *s;
        uint32_t slen;
        if (buf_get_string_ref(&b, &s, &slen) < 0) return -1;
        printf("  %-40s: %.*s\n", field_names[i], (int)slen, s);

        /* In a real implementation, intersect with our preferences here */
        if (i == 0 && slen < sizeof(conn->kex_algo) - 1) {
            /* Simplified: just use first name from their list */
            const char *comma = memchr(s, ',', slen);
            size_t first_len = comma ? (size_t)(comma - (const char*)s) : slen;
            if (first_len < sizeof(conn->kex_algo)) {
                memcpy(conn->kex_algo, s, first_len);
                conn->kex_algo[first_len] = '\0';
            }
        }
    }

    return 0;
}

/*
 * Send SSH_MSG_SERVICE_REQUEST
 */
static int ssh_service_request(ssh_conn_t *conn, const char *service) {
    ssh_buf_t b;
    if (buf_init(&b, 32) < 0) return -1;
    buf_put_u8(&b, SSH_MSG_SERVICE_REQUEST);
    buf_put_cstr(&b, service);
    int ret = ssh_send_packet(conn, b.data, b.len);
    buf_free(&b);
    return ret;
}

/*
 * Main connection loop — demonstrates full message dispatch
 */
static void ssh_conn_loop(ssh_conn_t *conn) {
    uint8_t *payload;
    size_t   payload_len;

    while (1) {
        if (ssh_recv_packet(conn, &payload, &payload_len) < 0) {
            fprintf(stderr, "recv_packet error\n");
            break;
        }
        if (payload_len == 0) {
            free(payload);
            continue;
        }

        uint8_t msg_type = payload[0];
        printf("Received message type: %u\n", msg_type);

        switch (msg_type) {
        case SSH_MSG_DISCONNECT: {
            /* Parse reason code and message */
            ssh_buf_t b = { payload, payload_len, payload_len, 1 };
            uint32_t reason;
            const uint8_t *msg_str;
            uint32_t msg_len;
            if (buf_get_u32(&b, &reason) == 0 &&
                buf_get_string_ref(&b, &msg_str, &msg_len) == 0) {
                printf("Disconnect reason %u: %.*s\n", reason, (int)msg_len, msg_str);
            }
            free(payload);
            return;
        }

        case SSH_MSG_IGNORE:
            /* Must silently ignore */
            break;

        case SSH_MSG_UNIMPLEMENTED: {
            ssh_buf_t b = { payload, payload_len, payload_len, 1 };
            uint32_t seq;
            buf_get_u32(&b, &seq);
            printf("Peer sent UNIMPLEMENTED for packet seq %u\n", seq);
            break;
        }

        case SSH_MSG_KEXINIT:
            printf("Received KEXINIT:\n");
            ssh_parse_kexinit(conn, payload, payload_len);
            break;

        case SSH_MSG_NEWKEYS:
            printf("Received NEWKEYS — switching to new keys\n");
            /* Here you would activate the derived encryption keys */
            break;

        case SSH_MSG_SERVICE_ACCEPT: {
            ssh_buf_t b = { payload, payload_len, payload_len, 1 };
            const uint8_t *svc;
            uint32_t svc_len;
            if (buf_get_string_ref(&b, &svc, &svc_len) == 0) {
                printf("Service accepted: %.*s\n", (int)svc_len, svc);
            }
            break;
        }

        case SSH_MSG_USERAUTH_SUCCESS:
            printf("Authentication successful!\n");
            break;

        case SSH_MSG_USERAUTH_FAILURE: {
            ssh_buf_t b = { payload, payload_len, payload_len, 1 };
            const uint8_t *methods;
            uint32_t methods_len;
            uint8_t partial;
            buf_get_string_ref(&b, &methods, &methods_len);
            buf_get_u8(&b, &partial);
            printf("Auth failure. Methods: %.*s, partial=%d\n",
                   (int)methods_len, methods, partial);
            break;
        }

        case SSH_MSG_CHANNEL_DATA: {
            ssh_buf_t b = { payload, payload_len, payload_len, 1 };
            uint32_t channel;
            const uint8_t *data;
            uint32_t data_len;
            buf_get_u32(&b, &channel);
            buf_get_string_ref(&b, &data, &data_len);
            printf("Channel %u data (%u bytes): %.*s\n",
                   channel, data_len, (int)data_len, data);
            break;
        }

        default:
            /* Send SSH_MSG_UNIMPLEMENTED for unknown message types */
            {
                ssh_buf_t resp;
                buf_init(&resp, 8);
                buf_put_u8(&resp, SSH_MSG_UNIMPLEMENTED);
                buf_put_u32(&resp, conn->recv_seq - 1);  /* seq of unhandled packet */
                ssh_send_packet(conn, resp.data, resp.len);
                buf_free(&resp);
            }
            break;
        }
        free(payload);
    }
}

/*
 * Example: Simple echo server on port 2222
 * (no actual key exchange — demonstrates structure only)
 */
int main(void) {
    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) { perror("socket"); exit(1); }

    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    struct sockaddr_in addr = {
        .sin_family      = AF_INET,
        .sin_port        = htons(2222),
        .sin_addr.s_addr = INADDR_ANY,
    };

    if (bind(server_fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("bind"); exit(1);
    }
    if (listen(server_fd, 5) < 0) { perror("listen"); exit(1); }

    printf("Minimal SSH server listening on port 2222\n");

    while (1) {
        struct sockaddr_in client_addr;
        socklen_t client_len = sizeof(client_addr);
        int client_fd = accept(server_fd, (struct sockaddr *)&client_addr, &client_len);
        if (client_fd < 0) { perror("accept"); continue; }

        printf("Connection from %s:%d\n",
               inet_ntoa(client_addr.sin_addr),
               ntohs(client_addr.sin_port));

        ssh_conn_t conn = {0};
        conn.fd = client_fd;

        /* Step 1: Version exchange */
        if (ssh_version_exchange(&conn, 1 /* server */) < 0) {
            fprintf(stderr, "Version exchange failed\n");
            close(client_fd);
            continue;
        }

        /* Step 2: Send our KEXINIT */
        if (ssh_send_kexinit(&conn) < 0) {
            fprintf(stderr, "Failed to send KEXINIT\n");
            close(client_fd);
            continue;
        }

        /* Step 3: Process incoming messages */
        ssh_conn_loop(&conn);

        close(client_fd);
    }

    close(server_fd);
    return 0;
}
```

### 17.2 Key Exchange — Curve25519 in C

```c
/*
 * ssh_kex_curve25519.c
 *
 * Implements the curve25519-sha256 key exchange.
 * Requires: libsodium or OpenSSL >= 1.1.1
 *
 * gcc -Wall -o ssh_kex ssh_kex_curve25519.c -lsodium
 */

#include <stdio.h>
#include <string.h>
#include <sodium.h>   /* libsodium: crypto_scalarmult_curve25519 */

#define SHA256_DIGEST_LEN 32

/*
 * Compute the exchange hash H for curve25519 key exchange:
 *
 *  H = SHA-256(
 *        string  V_C   client version string
 *        string  V_S   server version string
 *        string  I_C   client KEXINIT payload
 *        string  I_S   server KEXINIT payload
 *        string  K_S   server host public key blob
 *        string  Q_C   client ephemeral public key (32 bytes)
 *        string  Q_S   server ephemeral public key (32 bytes)
 *        mpint   K     shared secret
 *      )
 */
static int compute_exchange_hash(
    const char *V_C, size_t V_C_len,   /* client version string (without \r\n) */
    const char *V_S, size_t V_S_len,   /* server version string (without \r\n) */
    const uint8_t *I_C, size_t I_C_len,/* client KEXINIT payload */
    const uint8_t *I_S, size_t I_S_len,/* server KEXINIT payload */
    const uint8_t *K_S, size_t K_S_len,/* server host key blob */
    const uint8_t *Q_C, size_t Q_C_len,/* client ephemeral pubkey (32 bytes) */
    const uint8_t *Q_S, size_t Q_S_len,/* server ephemeral pubkey (32 bytes) */
    const uint8_t *K,   size_t K_len,  /* shared secret (X25519 output, 32 bytes) */
    uint8_t H[SHA256_DIGEST_LEN]
) {
    crypto_hash_sha256_state state;
    crypto_hash_sha256_init(&state);

    /* Helper to hash an SSH string (uint32 length + data) */
    #define HASH_SSH_STR(data, len) do {              \
        uint32_t l = (uint32_t)(len);                 \
        uint8_t lbuf[4] = {                           \
            (l >> 24), (l >> 16), (l >> 8), (l)      \
        };                                            \
        crypto_hash_sha256_update(&state, lbuf, 4);   \
        crypto_hash_sha256_update(&state, (const uint8_t*)(data), l); \
    } while(0)

    /* Helper to hash an mpint (big-endian, high bit cleared with leading 0x00) */
    #define HASH_MPINT(data, len) do {                \
        /* Check if high bit of first byte is set */  \
        uint8_t leading = 0x00;                       \
        int need_pad = (len > 0 && ((data)[0] & 0x80)); \
        uint32_t mplen = (uint32_t)(len) + (need_pad ? 1 : 0); \
        uint8_t mpbuf[4] = {                          \
            (mplen >> 24), (mplen >> 16),             \
            (mplen >>  8), (mplen      )              \
        };                                            \
        crypto_hash_sha256_update(&state, mpbuf, 4);  \
        if (need_pad) {                               \
            crypto_hash_sha256_update(&state, &leading, 1); \
        }                                             \
        crypto_hash_sha256_update(&state, (data), (len)); \
    } while(0)

    HASH_SSH_STR(V_C, V_C_len);
    HASH_SSH_STR(V_S, V_S_len);
    HASH_SSH_STR(I_C, I_C_len);
    HASH_SSH_STR(I_S, I_S_len);
    HASH_SSH_STR(K_S, K_S_len);
    HASH_SSH_STR(Q_C, Q_C_len);
    HASH_SSH_STR(Q_S, Q_S_len);
    HASH_MPINT  (K,   K_len);

    crypto_hash_sha256_final(&state, H);

    #undef HASH_SSH_STR
    #undef HASH_MPINT

    return 0;
}

/*
 * Perform key derivation: derive IV, key, and MAC key from
 * shared secret K, exchange hash H, and session ID.
 *
 * key = SHA-256(K || H || X || session_id)
 *
 * If needed_len > SHA256_DIGEST_LEN, extend using:
 * key = SHA-256(K || H || key[0]) || SHA-256(K || H || key[0] || key[1]) || ...
 */
static int derive_key(
    const uint8_t *K,          size_t K_len,
    const uint8_t *H,          /* SHA-256, 32 bytes */
    char magic,                /* 'A'-'F' */
    const uint8_t *session_id, /* SHA-256, 32 bytes */
    uint8_t *out,              size_t needed_len
) {
    /* Build the base hash input: mpint(K) || H || magic_byte || session_id */
    /* We use a helper to build this incrementally */

    uint8_t block[SHA256_DIGEST_LEN];
    size_t  produced = 0;
    uint8_t *prev = NULL;

    while (produced < needed_len) {
        crypto_hash_sha256_state st;
        crypto_hash_sha256_init(&st);

        /* mpint(K) */
        {
            int need_pad = (K_len > 0 && (K[0] & 0x80));
            uint32_t mplen = (uint32_t)K_len + (need_pad ? 1 : 0);
            uint8_t lbuf[4] = {
                (uint8_t)(mplen >> 24), (uint8_t)(mplen >> 16),
                (uint8_t)(mplen >>  8), (uint8_t)(mplen      )
            };
            crypto_hash_sha256_update(&st, lbuf, 4);
            if (need_pad) {
                uint8_t z = 0;
                crypto_hash_sha256_update(&st, &z, 1);
            }
            crypto_hash_sha256_update(&st, K, K_len);
        }

        /* H (32 bytes) */
        crypto_hash_sha256_update(&st, H, SHA256_DIGEST_LEN);

        if (prev == NULL) {
            /* First block: H || magic || session_id */
            uint8_t m = (uint8_t)magic;
            crypto_hash_sha256_update(&st, &m, 1);
            crypto_hash_sha256_update(&st, session_id, SHA256_DIGEST_LEN);
        } else {
            /* Extension block: previous blocks */
            crypto_hash_sha256_update(&st, out, produced);
        }

        crypto_hash_sha256_final(&st, block);

        size_t copy = SHA256_DIGEST_LEN;
        if (produced + copy > needed_len) copy = needed_len - produced;
        memcpy(out + produced, block, copy);
        produced += copy;
        prev = block;
    }

    return 0;
}

/*
 * Demonstrate key exchange for a client
 */
int kex_client_demo(
    int sock,
    const uint8_t *server_host_key,    size_t server_host_key_len,
    const char    *V_C,
    const char    *V_S,
    const uint8_t *I_C,                size_t I_C_len,
    const uint8_t *I_S,                size_t I_S_len
) {
    if (sodium_init() < 0) {
        fprintf(stderr, "libsodium init failed\n");
        return -1;
    }

    /* Generate ephemeral Curve25519 key pair */
    uint8_t client_priv[crypto_scalarmult_SCALARBYTES];
    uint8_t client_pub [crypto_scalarmult_BYTES];

    randombytes_buf(client_priv, sizeof(client_priv));
    /* Clamp the scalar per Curve25519 spec */
    client_priv[0]  &= 248;
    client_priv[31] &= 127;
    client_priv[31] |= 64;

    /* Compute public key: client_pub = basepoint ^ client_priv */
    crypto_scalarmult_base(client_pub, client_priv);

    printf("Client ephemeral pubkey (hex):\n");
    for (int i = 0; i < 32; i++) printf("%02x", client_pub[i]);
    printf("\n");

    /* TODO: Send SSH_MSG_KEX_ECDH_INIT with client_pub to server */
    /* TODO: Receive SSH_MSG_KEX_ECDH_REPLY with server_pub, K_S, sig */

    /* For demonstration, generate fake server pubkey */
    uint8_t server_priv[32], server_pub[32];
    randombytes_buf(server_priv, sizeof(server_priv));
    server_priv[0]  &= 248;
    server_priv[31] &= 127;
    server_priv[31] |= 64;
    crypto_scalarmult_base(server_pub, server_priv);

    /* Compute shared secret: K = X25519(client_priv, server_pub) */
    uint8_t shared_secret[crypto_scalarmult_BYTES];
    if (crypto_scalarmult(shared_secret, client_priv, server_pub) != 0) {
        fprintf(stderr, "X25519 failed (low-order point?)\n");
        return -1;
    }

    /* Check for all-zero output — low-order point attack */
    int all_zero = 1;
    for (int i = 0; i < 32; i++) {
        if (shared_secret[i] != 0) { all_zero = 0; break; }
    }
    if (all_zero) {
        fprintf(stderr, "Low-order point attack detected!\n");
        return -1;
    }

    printf("Shared secret (hex):\n");
    for (int i = 0; i < 32; i++) printf("%02x", shared_secret[i]);
    printf("\n");

    /* Compute exchange hash H */
    uint8_t H[SHA256_DIGEST_LEN];
    compute_exchange_hash(
        V_C, strlen(V_C),
        V_S, strlen(V_S),
        I_C, I_C_len,
        I_S, I_S_len,
        server_host_key, server_host_key_len,
        client_pub, 32,
        server_pub, 32,
        shared_secret, 32,
        H
    );

    printf("Exchange hash H (hex):\n");
    for (int i = 0; i < 32; i++) printf("%02x", H[i]);
    printf("\n");

    /*
     * Derive keys (A-F)
     * For AES-256-CTR: needs 32-byte key + 16-byte IV
     * For HMAC-SHA-256: needs 32-byte key
     */
    uint8_t iv_c2s[16], iv_s2c[16];
    uint8_t key_c2s[32], key_s2c[32];
    uint8_t mac_c2s[32], mac_s2c[32];

    derive_key(shared_secret, 32, H, 'A', H, iv_c2s,  sizeof(iv_c2s));
    derive_key(shared_secret, 32, H, 'B', H, iv_s2c,  sizeof(iv_s2c));
    derive_key(shared_secret, 32, H, 'C', H, key_c2s, sizeof(key_c2s));
    derive_key(shared_secret, 32, H, 'D', H, key_s2c, sizeof(key_s2c));
    derive_key(shared_secret, 32, H, 'E', H, mac_c2s, sizeof(mac_c2s));
    derive_key(shared_secret, 32, H, 'F', H, mac_s2c, sizeof(mac_s2c));

    printf("IV  c2s: "); for(int i=0;i<16;i++) printf("%02x",iv_c2s[i]); printf("\n");
    printf("Key c2s: "); for(int i=0;i<32;i++) printf("%02x",key_c2s[i]); printf("\n");
    printf("MAC c2s: "); for(int i=0;i<32;i++) printf("%02x",mac_c2s[i]); printf("\n");

    /* Securely zero sensitive data */
    sodium_memzero(client_priv, sizeof(client_priv));
    sodium_memzero(shared_secret, sizeof(shared_secret));

    return 0;
}
```

---

## 18. Rust Implementation

### 18.1 SSH Packet Framing in Rust

```rust
//! ssh_packet.rs — SSH binary packet protocol implementation in Rust
//!
//! Demonstrates:
//!   - Type-safe packet encoding/decoding
//!   - SSH data type serialization
//!   - Packet framing with padding
//!
//! Add to Cargo.toml:
//!   [dependencies]
//!   rand = "0.8"
//!   sha2 = "0.10"
//!   hmac = "0.12"
//!   aes = "0.8"
//!   ctr = "0.9"
//!   tokio = { version = "1", features = ["full"] }
//!   thiserror = "1"

use std::io::{self, Read, Write};
use rand::RngCore;

/// SSH message type constants
#[repr(u8)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum MsgType {
    Disconnect            = 1,
    Ignore                = 2,
    Unimplemented         = 3,
    ServiceRequest        = 5,
    ServiceAccept         = 6,
    KexInit               = 20,
    NewKeys               = 21,
    UserauthRequest       = 50,
    UserauthFailure       = 51,
    UserauthSuccess       = 52,
    UserauthBanner        = 53,
    ChannelOpen           = 90,
    ChannelOpenConfirm    = 91,
    ChannelOpenFailure    = 92,
    ChannelWindowAdjust   = 93,
    ChannelData           = 94,
    ChannelExtendedData   = 95,
    ChannelEof            = 96,
    ChannelClose          = 97,
    ChannelRequest        = 98,
    ChannelSuccess        = 99,
    ChannelFailure        = 100,
}

impl TryFrom<u8> for MsgType {
    type Error = SshError;
    fn try_from(b: u8) -> Result<Self, Self::Error> {
        match b {
            1 => Ok(MsgType::Disconnect),
            2 => Ok(MsgType::Ignore),
            3 => Ok(MsgType::Unimplemented),
            5 => Ok(MsgType::ServiceRequest),
            6 => Ok(MsgType::ServiceAccept),
            20 => Ok(MsgType::KexInit),
            21 => Ok(MsgType::NewKeys),
            50 => Ok(MsgType::UserauthRequest),
            51 => Ok(MsgType::UserauthFailure),
            52 => Ok(MsgType::UserauthSuccess),
            53 => Ok(MsgType::UserauthBanner),
            90 => Ok(MsgType::ChannelOpen),
            91 => Ok(MsgType::ChannelOpenConfirm),
            92 => Ok(MsgType::ChannelOpenFailure),
            93 => Ok(MsgType::ChannelWindowAdjust),
            94 => Ok(MsgType::ChannelData),
            95 => Ok(MsgType::ChannelExtendedData),
            96 => Ok(MsgType::ChannelEof),
            97 => Ok(MsgType::ChannelClose),
            98 => Ok(MsgType::ChannelRequest),
            99 => Ok(MsgType::ChannelSuccess),
            100 => Ok(MsgType::ChannelFailure),
            n  => Err(SshError::UnknownMessageType(n)),
        }
    }
}

/// SSH errors
#[derive(Debug, thiserror::Error)]
pub enum SshError {
    #[error("I/O error: {0}")]
    Io(#[from] io::Error),
    #[error("Protocol error: {0}")]
    Protocol(String),
    #[error("Unknown message type: {0}")]
    UnknownMessageType(u8),
    #[error("Buffer underflow: needed {needed} bytes, have {available}")]
    BufferUnderflow { needed: usize, available: usize },
    #[error("String encoding error")]
    StringEncoding,
    #[error("Packet too large: {0} bytes")]
    PacketTooLarge(usize),
    #[error("MAC verification failed")]
    MacError,
}

/// SSH write buffer — builds outgoing packet payloads
#[derive(Default, Clone)]
pub struct SshBuf(Vec<u8>);

impl SshBuf {
    pub fn new() -> Self { SshBuf(Vec::new()) }
    pub fn with_capacity(cap: usize) -> Self { SshBuf(Vec::with_capacity(cap)) }

    /// Append raw bytes
    pub fn put_bytes(&mut self, data: &[u8]) {
        self.0.extend_from_slice(data);
    }

    /// Append a single byte
    pub fn put_u8(&mut self, v: u8) {
        self.0.push(v);
    }

    /// Append SSH boolean (1 byte: 0x01 for true, 0x00 for false)
    pub fn put_bool(&mut self, v: bool) {
        self.0.push(if v { 1 } else { 0 });
    }

    /// Append big-endian uint32
    pub fn put_u32(&mut self, v: u32) {
        self.0.extend_from_slice(&v.to_be_bytes());
    }

    /// Append big-endian uint64
    pub fn put_u64(&mut self, v: u64) {
        self.0.extend_from_slice(&v.to_be_bytes());
    }

    /// Append SSH string (uint32 length prefix + data)
    pub fn put_string(&mut self, data: &[u8]) {
        self.put_u32(data.len() as u32);
        self.put_bytes(data);
    }

    /// Append an ASCII/UTF-8 string as SSH string
    pub fn put_str(&mut self, s: &str) {
        self.put_string(s.as_bytes());
    }

    /// Append a name-list (comma-separated SSH string)
    pub fn put_name_list(&mut self, names: &[&str]) {
        let joined = names.join(",");
        self.put_str(&joined);
    }

    /// Append an mpint (SSH multi-precision integer)
    ///
    /// mpint rules:
    ///   - Big-endian, minimum bytes
    ///   - Zero = empty string (length 0)
    ///   - If high bit of first byte is set, prepend 0x00
    pub fn put_mpint(&mut self, bytes: &[u8]) {
        // Strip leading zero bytes
        let bytes = {
            let mut start = 0;
            while start < bytes.len() && bytes[start] == 0 {
                start += 1;
            }
            &bytes[start..]
        };

        if bytes.is_empty() {
            self.put_u32(0);  // Zero
            return;
        }

        let needs_pad = (bytes[0] & 0x80) != 0;
        let len = bytes.len() + if needs_pad { 1 } else { 0 };
        self.put_u32(len as u32);
        if needs_pad {
            self.0.push(0x00);
        }
        self.put_bytes(bytes);
    }

    pub fn into_vec(self) -> Vec<u8> { self.0 }
    pub fn as_slice(&self) -> &[u8] { &self.0 }
    pub fn len(&self) -> usize { self.0.len() }
    pub fn is_empty(&self) -> bool { self.0.is_empty() }
}

/// SSH read buffer — parses incoming packet payloads
pub struct SshParser<'a> {
    data: &'a [u8],
    pos: usize,
}

impl<'a> SshParser<'a> {
    pub fn new(data: &'a [u8]) -> Self {
        SshParser { data, pos: 0 }
    }

    pub fn remaining(&self) -> usize {
        self.data.len().saturating_sub(self.pos)
    }

    fn need(&self, n: usize) -> Result<(), SshError> {
        if self.remaining() < n {
            Err(SshError::BufferUnderflow {
                needed: n,
                available: self.remaining(),
            })
        } else {
            Ok(())
        }
    }

    pub fn get_u8(&mut self) -> Result<u8, SshError> {
        self.need(1)?;
        let b = self.data[self.pos];
        self.pos += 1;
        Ok(b)
    }

    pub fn get_bool(&mut self) -> Result<bool, SshError> {
        Ok(self.get_u8()? != 0)
    }

    pub fn get_u32(&mut self) -> Result<u32, SshError> {
        self.need(4)?;
        let bytes: [u8; 4] = self.data[self.pos..self.pos + 4].try_into().unwrap();
        self.pos += 4;
        Ok(u32::from_be_bytes(bytes))
    }

    pub fn get_u64(&mut self) -> Result<u64, SshError> {
        self.need(8)?;
        let bytes: [u8; 8] = self.data[self.pos..self.pos + 8].try_into().unwrap();
        self.pos += 8;
        Ok(u64::from_be_bytes(bytes))
    }

    /// Get SSH string as a byte slice (zero-copy)
    pub fn get_string(&mut self) -> Result<&'a [u8], SshError> {
        let len = self.get_u32()? as usize;
        self.need(len)?;
        let slice = &self.data[self.pos..self.pos + len];
        self.pos += len;
        Ok(slice)
    }

    /// Get SSH string as UTF-8 str
    pub fn get_str(&mut self) -> Result<&'a str, SshError> {
        let bytes = self.get_string()?;
        std::str::from_utf8(bytes).map_err(|_| SshError::StringEncoding)
    }

    /// Get name-list as a Vec of &str
    pub fn get_name_list(&mut self) -> Result<Vec<&'a str>, SshError> {
        let s = self.get_str()?;
        if s.is_empty() {
            Ok(vec![])
        } else {
            Ok(s.split(',').collect())
        }
    }

    /// Skip n bytes
    pub fn skip(&mut self, n: usize) -> Result<(), SshError> {
        self.need(n)?;
        self.pos += n;
        Ok(())
    }

    /// Get raw bytes slice
    pub fn get_bytes(&mut self, n: usize) -> Result<&'a [u8], SshError> {
        self.need(n)?;
        let slice = &self.data[self.pos..self.pos + n];
        self.pos += n;
        Ok(slice)
    }
}

/// SSH packet framing constants
const BLOCK_SIZE: usize = 8;         // Minimum alignment when unencrypted
const MIN_PADDING: usize = 4;       // RFC 4253: padding MUST be at least 4 bytes
const MAX_PACKET_SIZE: usize = 35000; // Max allowed packet payload

/// Framed SSH packet
#[derive(Debug)]
pub struct Packet {
    pub payload: Vec<u8>,
}

impl Packet {
    pub fn new(payload: Vec<u8>) -> Result<Self, SshError> {
        if payload.len() > MAX_PACKET_SIZE {
            return Err(SshError::PacketTooLarge(payload.len()));
        }
        Ok(Packet { payload })
    }

    pub fn msg_type(&self) -> Option<MsgType> {
        self.payload.first().copied()
            .and_then(|b| MsgType::try_from(b).ok())
    }

    /// Encode to wire format:
    ///   [4 bytes packet_length] [1 byte pad_len] [payload] [padding] [MAC]
    ///
    /// `block_size`: cipher block size (8 if no encryption)
    pub fn encode(&self, block_size: usize) -> Vec<u8> {
        let payload_len = self.payload.len();

        // base = pad_len_field(1) + payload
        let base = 1 + payload_len;
        // padding makes (packet_length + 4) a multiple of block_size
        // packet_length = pad_len(1) + payload + padding
        // (4 + pad_len(1) + payload + padding) % block_size == 0
        let mut pad_len = block_size - (4 + base) % block_size;
        if pad_len < MIN_PADDING {
            pad_len += block_size;
        }

        let packet_length = 1 + payload_len + pad_len;

        let mut out = Vec::with_capacity(4 + packet_length);
        out.extend_from_slice(&(packet_length as u32).to_be_bytes());
        out.push(pad_len as u8);
        out.extend_from_slice(&self.payload);

        // Random padding
        let mut padding = vec![0u8; pad_len];
        rand::thread_rng().fill_bytes(&mut padding);
        out.extend_from_slice(&padding);

        out
    }

    /// Decode from wire format (reads from a buffered reader)
    pub fn decode<R: Read>(reader: &mut R) -> Result<Self, SshError> {
        // Read 4-byte packet_length
        let mut len_buf = [0u8; 4];
        reader.read_exact(&mut len_buf)?;
        let packet_length = u32::from_be_bytes(len_buf) as usize;

        if packet_length < 5 || packet_length > MAX_PACKET_SIZE + 256 {
            return Err(SshError::Protocol(
                format!("Invalid packet_length: {}", packet_length)
            ));
        }

        // Read pad_len + payload + padding
        let mut buf = vec![0u8; packet_length];
        reader.read_exact(&mut buf)?;

        let pad_len = buf[0] as usize;
        if pad_len < MIN_PADDING || pad_len + 1 > packet_length {
            return Err(SshError::Protocol(
                format!("Invalid padding_length: {}", pad_len)
            ));
        }

        let payload_len = packet_length - 1 - pad_len;
        let payload = buf[1..1 + payload_len].to_vec();

        Ok(Packet { payload })
    }
}

/// Structured SSH messages

/// SSH_MSG_KEXINIT (type 20)
#[derive(Debug)]
pub struct KexInit {
    pub cookie: [u8; 16],
    pub kex_algorithms: Vec<String>,
    pub server_host_key_algorithms: Vec<String>,
    pub encryption_algorithms_c2s: Vec<String>,
    pub encryption_algorithms_s2c: Vec<String>,
    pub mac_algorithms_c2s: Vec<String>,
    pub mac_algorithms_s2c: Vec<String>,
    pub compression_algorithms_c2s: Vec<String>,
    pub compression_algorithms_s2c: Vec<String>,
    pub first_kex_packet_follows: bool,
}

impl KexInit {
    /// Construct a hardened KexInit with modern algorithm preferences
    pub fn new_client() -> Self {
        KexInit {
            cookie: {
                let mut c = [0u8; 16];
                rand::thread_rng().fill_bytes(&mut c);
                c
            },
            kex_algorithms: vec![
                "curve25519-sha256".to_string(),
                "curve25519-sha256@libssh.org".to_string(),
                "ecdh-sha2-nistp256".to_string(),
                "diffie-hellman-group16-sha512".to_string(),
            ],
            server_host_key_algorithms: vec![
                "ssh-ed25519".to_string(),
                "rsa-sha2-512".to_string(),
                "rsa-sha2-256".to_string(),
            ],
            encryption_algorithms_c2s: vec![
                "chacha20-poly1305@openssh.com".to_string(),
                "aes256-gcm@openssh.com".to_string(),
                "aes128-gcm@openssh.com".to_string(),
                "aes256-ctr".to_string(),
            ],
            encryption_algorithms_s2c: vec![
                "chacha20-poly1305@openssh.com".to_string(),
                "aes256-gcm@openssh.com".to_string(),
                "aes128-gcm@openssh.com".to_string(),
                "aes256-ctr".to_string(),
            ],
            mac_algorithms_c2s: vec![
                "hmac-sha2-256-etm@openssh.com".to_string(),
                "hmac-sha2-512-etm@openssh.com".to_string(),
                "hmac-sha2-256".to_string(),
            ],
            mac_algorithms_s2c: vec![
                "hmac-sha2-256-etm@openssh.com".to_string(),
                "hmac-sha2-512-etm@openssh.com".to_string(),
                "hmac-sha2-256".to_string(),
            ],
            compression_algorithms_c2s: vec!["none".to_string()],
            compression_algorithms_s2c: vec!["none".to_string()],
            first_kex_packet_follows: false,
        }
    }

    /// Encode to SSH packet payload
    pub fn encode(&self) -> Vec<u8> {
        let mut buf = SshBuf::with_capacity(512);
        buf.put_u8(MsgType::KexInit as u8);
        buf.put_bytes(&self.cookie);

        let to_refs = |v: &[String]| -> Vec<&str> { v.iter().map(|s| s.as_str()).collect() };

        buf.put_name_list(&to_refs(&self.kex_algorithms));
        buf.put_name_list(&to_refs(&self.server_host_key_algorithms));
        buf.put_name_list(&to_refs(&self.encryption_algorithms_c2s));
        buf.put_name_list(&to_refs(&self.encryption_algorithms_s2c));
        buf.put_name_list(&to_refs(&self.mac_algorithms_c2s));
        buf.put_name_list(&to_refs(&self.mac_algorithms_s2c));
        buf.put_name_list(&to_refs(&self.compression_algorithms_c2s));
        buf.put_name_list(&to_refs(&self.compression_algorithms_s2c));
        buf.put_name_list(&[]);  // languages c2s
        buf.put_name_list(&[]);  // languages s2c
        buf.put_bool(self.first_kex_packet_follows);
        buf.put_u32(0);          // reserved

        buf.into_vec()
    }

    /// Parse from a received packet payload
    pub fn parse(payload: &[u8]) -> Result<Self, SshError> {
        let mut p = SshParser::new(payload);

        let msg_type = p.get_u8()?;
        if msg_type != MsgType::KexInit as u8 {
            return Err(SshError::Protocol(
                format!("Expected KEXINIT (20), got {}", msg_type)
            ));
        }

        let cookie_bytes = p.get_bytes(16)?;
        let mut cookie = [0u8; 16];
        cookie.copy_from_slice(cookie_bytes);

        let to_owned = |v: Vec<&str>| -> Vec<String> { v.iter().map(|&s| s.to_string()).collect() };

        Ok(KexInit {
            cookie,
            kex_algorithms: to_owned(p.get_name_list()?),
            server_host_key_algorithms: to_owned(p.get_name_list()?),
            encryption_algorithms_c2s: to_owned(p.get_name_list()?),
            encryption_algorithms_s2c: to_owned(p.get_name_list()?),
            mac_algorithms_c2s: to_owned(p.get_name_list()?),
            mac_algorithms_s2c: to_owned(p.get_name_list()?),
            compression_algorithms_c2s: to_owned(p.get_name_list()?),
            compression_algorithms_s2c: to_owned(p.get_name_list()?),
            first_kex_packet_follows: {
                p.skip(p.remaining().min(
                    // skip 2 language name-lists
                    4 + p.get_name_list().map(|_|0).unwrap_or(0) +
                    4 + p.get_name_list().map(|_|0).unwrap_or(0)
                ))?;
                p.get_bool().unwrap_or(false)
            },
        })
    }

    /// Algorithm negotiation: find the first name in `client_list` that appears in `server_list`
    pub fn negotiate<'a>(client_list: &'a [String], server_list: &[String]) -> Option<&'a str> {
        client_list.iter()
            .find(|algo| server_list.iter().any(|s| s == *algo))
            .map(|s| s.as_str())
    }
}

/// Negotiated algorithms after KEXINIT exchange
#[derive(Debug)]
pub struct NegotiatedAlgorithms {
    pub kex:         String,
    pub host_key:    String,
    pub enc_c2s:     String,
    pub enc_s2c:     String,
    pub mac_c2s:     String,
    pub mac_s2c:     String,
    pub comp_c2s:    String,
    pub comp_s2c:    String,
}

impl NegotiatedAlgorithms {
    pub fn negotiate(client: &KexInit, server: &KexInit) -> Result<Self, SshError> {
        macro_rules! neg {
            ($field_c:expr, $field_s:expr, $name:literal) => {
                KexInit::negotiate($field_c, $field_s)
                    .map(|s| s.to_string())
                    .ok_or_else(|| SshError::Protocol(
                        format!("No common algorithm for {}", $name)
                    ))?
            }
        }

        Ok(NegotiatedAlgorithms {
            kex:      neg!(&client.kex_algorithms, &server.kex_algorithms, "kex"),
            host_key: neg!(&client.server_host_key_algorithms, &server.server_host_key_algorithms, "host-key"),
            enc_c2s:  neg!(&client.encryption_algorithms_c2s, &server.encryption_algorithms_c2s, "enc-c2s"),
            enc_s2c:  neg!(&client.encryption_algorithms_s2c, &server.encryption_algorithms_s2c, "enc-s2c"),
            mac_c2s:  neg!(&client.mac_algorithms_c2s, &server.mac_algorithms_c2s, "mac-c2s"),
            mac_s2c:  neg!(&client.mac_algorithms_s2c, &server.mac_algorithms_s2c, "mac-s2c"),
            comp_c2s: neg!(&client.compression_algorithms_c2s, &server.compression_algorithms_c2s, "comp-c2s"),
            comp_s2c: neg!(&client.compression_algorithms_s2c, &server.compression_algorithms_s2c, "comp-s2c"),
        })
    }
}

/// Version exchange
pub fn version_exchange<RW: Read + Write>(
    stream: &mut RW,
    our_version: &str,
) -> Result<String, SshError> {
    // Send our version
    let line = format!("{}\r\n", our_version);
    stream.write_all(line.as_bytes())?;

    // Read their version
    let mut buf = Vec::with_capacity(256);
    loop {
        let mut byte = [0u8; 1];
        stream.read_exact(&mut byte)?;
        if byte[0] == b'\n' { break; }
        if byte[0] != b'\r' { buf.push(byte[0]); }
        if buf.len() > 255 {
            return Err(SshError::Protocol("Version string too long".to_string()));
        }
    }

    let peer_version = String::from_utf8(buf)
        .map_err(|_| SshError::Protocol("Non-UTF8 version string".to_string()))?;

    // RFC says lines starting with "SSH-" are the version line;
    // others are banner lines to be ignored
    if !peer_version.starts_with("SSH-2.0-") && !peer_version.starts_with("SSH-1.99-") {
        return Err(SshError::Protocol(
            format!("Unsupported version: {}", peer_version)
        ));
    }

    Ok(peer_version)
}

/// Key derivation (RFC 4253 §7.2)
///
/// derive_key(K, H, letter, session_id, needed_len) -> key material
pub fn derive_key(
    k: &[u8],           // shared secret K as mpint (already encoded)
    h: &[u8],           // exchange hash H (32 bytes for SHA-256)
    letter: u8,         // b'A' through b'F'
    session_id: &[u8],  // session identifier (= first H)
    needed_len: usize,
) -> Vec<u8> {
    use sha2::{Sha256, Digest};

    let mut result = Vec::with_capacity(needed_len);

    // First block: SHA256(K || H || letter || session_id)
    let first_block = {
        let mut h256 = Sha256::new();
        h256.update(k);           // K as mpint (encoded with SSH mpint rules)
        h256.update(h);           // H
        h256.update(&[letter]);   // single byte 'A'-'F'
        h256.update(session_id);  // session ID
        h256.finalize()
    };
    result.extend_from_slice(&first_block);

    // Extension blocks: SHA256(K || H || result_so_far)
    while result.len() < needed_len {
        let mut h256 = Sha256::new();
        h256.update(k);
        h256.update(h);
        h256.update(&result);
        let block = h256.finalize();
        result.extend_from_slice(&block);
    }

    result.truncate(needed_len);
    result
}

/// Encode a raw byte array as an SSH mpint
/// (needed for including the DH/ECDH shared secret in key derivation)
pub fn encode_mpint(bytes: &[u8]) -> Vec<u8> {
    // Strip leading zeros
    let start = bytes.iter().position(|&b| b != 0).unwrap_or(bytes.len());
    let bytes = &bytes[start..];

    let mut buf = SshBuf::new();
    buf.put_mpint(bytes);
    buf.into_vec()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_packet_encode_decode() {
        let payload = vec![20u8, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];
        let pkt = Packet::new(payload.clone()).unwrap();
        let encoded = pkt.encode(8);

        // Decode it back
        let mut cursor = std::io::Cursor::new(encoded);
        let decoded = Packet::decode(&mut cursor).unwrap();
        assert_eq!(decoded.payload, payload);
    }

    #[test]
    fn test_kexinit_encode_parse() {
        let kex = KexInit::new_client();
        let encoded = kex.encode();
        let parsed = KexInit::parse(&encoded).unwrap();
        assert_eq!(kex.kex_algorithms, parsed.kex_algorithms);
        assert_eq!(kex.encryption_algorithms_c2s, parsed.encryption_algorithms_c2s);
    }

    #[test]
    fn test_negotiate() {
        let client_algos = vec!["curve25519-sha256".to_string(), "ecdh-sha2-nistp256".to_string()];
        let server_algos = vec!["ecdh-sha2-nistp256".to_string(), "curve25519-sha256".to_string()];
        // Client's preference wins: curve25519-sha256 appears first in client list
        let result = KexInit::negotiate(&client_algos, &server_algos);
        assert_eq!(result, Some("curve25519-sha256"));
    }

    #[test]
    fn test_mpint_encoding() {
        let mut buf = SshBuf::new();
        // 0x0080 = 128: needs a leading 0x00 byte because high bit is set
        buf.put_mpint(&[0x00, 0x80]);
        // Expected: length=2, bytes=[0x00, 0x80]
        assert_eq!(buf.as_slice(), &[0, 0, 0, 2, 0x00, 0x80]);
    }

    #[test]
    fn test_derive_key_deterministic() {
        let k = encode_mpint(&[1, 2, 3, 4]);
        let h = [0u8; 32];
        let session_id = [0u8; 32];
        let key_a = derive_key(&k, &h, b'A', &session_id, 32);
        let key_a2 = derive_key(&k, &h, b'A', &session_id, 32);
        // Same inputs = same output
        assert_eq!(key_a, key_a2);
        // Different letters = different keys
        let key_b = derive_key(&k, &h, b'B', &session_id, 32);
        assert_ne!(key_a, key_b);
    }
}
```

### 18.2 Async SSH Connection in Rust (Tokio)

```rust
//! async_ssh.rs — Async SSH connection skeleton using Tokio
//!
//! Shows the full connection state machine with async I/O.

use tokio::io::{AsyncReadExt, AsyncWriteExt, BufReader};
use tokio::net::TcpStream;
use std::io;

#[derive(Debug, PartialEq, Eq)]
pub enum ConnState {
    /// TCP connected, version string not yet exchanged
    Initial,
    /// Version strings exchanged
    VersionExchanged,
    /// KEXINIT sent and received
    KexInitExchanged,
    /// Key exchange in progress
    KeyExchange,
    /// Keys derived, NEWKEYS sent/received
    Encrypted,
    /// Authenticated
    Authenticated,
    /// Ready for channels
    Ready,
    /// Disconnected
    Disconnected,
}

pub struct AsyncSshConn {
    stream: BufReader<TcpStream>,
    state: ConnState,
    send_seq: u32,
    recv_seq: u32,
    // Encryption context would go here in a full implementation
    session_id: Option<Vec<u8>>,
    our_version: String,
    peer_version: Option<String>,
}

impl AsyncSshConn {
    pub async fn connect(addr: &str) -> io::Result<Self> {
        let stream = TcpStream::connect(addr).await?;
        Ok(AsyncSshConn {
            stream: BufReader::new(stream),
            state: ConnState::Initial,
            send_seq: 0,
            recv_seq: 0,
            session_id: None,
            our_version: "SSH-2.0-async_ssh_0.1".to_string(),
            peer_version: None,
        })
    }

    /// Exchange version strings
    pub async fn do_version_exchange(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        assert_eq!(self.state, ConnState::Initial);

        // Send our version
        let line = format!("{}\r\n", self.our_version);
        self.stream.get_mut().write_all(line.as_bytes()).await?;

        // Read peer version
        let mut peer_ver = String::new();
        loop {
            let byte = self.stream.read_u8().await?;
            if byte == b'\n' { break; }
            if byte != b'\r' { peer_ver.push(byte as char); }
            if peer_ver.len() > 255 {
                return Err("Version string too long".into());
            }
        }

        if !peer_ver.starts_with("SSH-2.0-") {
            return Err(format!("Unsupported version: {}", peer_ver).into());
        }

        self.peer_version = Some(peer_ver);
        self.state = ConnState::VersionExchanged;
        Ok(())
    }

    /// Send a packet (plaintext, for pre-encryption phase)
    pub async fn send_packet(&mut self, payload: &[u8]) -> io::Result<()> {
        use rand::RngCore;

        let payload_len = payload.len();
        let block_size = 8usize;
        let base = 1 + payload_len;
        let mut pad_len = block_size - (4 + base) % block_size;
        if pad_len < 4 { pad_len += block_size; }
        let packet_length = (1 + payload_len + pad_len) as u32;

        let mut out = Vec::with_capacity(4 + packet_length as usize);
        out.extend_from_slice(&packet_length.to_be_bytes());
        out.push(pad_len as u8);
        out.extend_from_slice(payload);

        let mut padding = vec![0u8; pad_len];
        rand::thread_rng().fill_bytes(&mut padding);
        out.extend_from_slice(&padding);

        self.stream.get_mut().write_all(&out).await?;
        self.send_seq = self.send_seq.wrapping_add(1);
        Ok(())
    }

    /// Receive a packet (plaintext)
    pub async fn recv_packet(&mut self) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
        let mut len_buf = [0u8; 4];
        self.stream.read_exact(&mut len_buf).await?;
        let packet_length = u32::from_be_bytes(len_buf) as usize;

        if packet_length < 5 || packet_length > 35000 {
            return Err(format!("Invalid packet_length: {}", packet_length).into());
        }

        let mut buf = vec![0u8; packet_length];
        self.stream.read_exact(&mut buf).await?;

        let pad_len = buf[0] as usize;
        if pad_len < 4 || pad_len + 1 > packet_length {
            return Err(format!("Invalid padding_length: {}", pad_len).into());
        }

        let payload_len = packet_length - 1 - pad_len;
        let payload = buf[1..1 + payload_len].to_vec();

        self.recv_seq = self.recv_seq.wrapping_add(1);
        Ok(payload)
    }

    /// Run the transport protocol state machine
    pub async fn handshake(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        // Step 1: Version exchange
        self.do_version_exchange().await?;
        println!("Peer version: {}", self.peer_version.as_ref().unwrap());

        // Step 2: KEXINIT
        let our_kexinit = super::KexInit::new_client();
        self.send_packet(&our_kexinit.encode()).await?;
        println!("Sent KEXINIT");

        // Receive KEXINIT
        let pkt = self.recv_packet().await?;
        if pkt.is_empty() || pkt[0] != 20 {
            return Err("Expected KEXINIT".into());
        }
        let peer_kexinit = super::KexInit::parse(&pkt)?;
        println!("Received KEXINIT from server");

        // Negotiate algorithms
        let algos = super::NegotiatedAlgorithms::negotiate(&our_kexinit, &peer_kexinit)?;
        println!("Negotiated KEX: {}", algos.kex);
        println!("Negotiated ENC c2s: {}", algos.enc_c2s);
        println!("Negotiated MAC c2s: {}", algos.mac_c2s);

        self.state = ConnState::KexInitExchanged;

        // Step 3: Key exchange (curve25519 example)
        // For a full implementation, dispatch based on algos.kex
        // Here we just indicate the flow

        // TODO: Generate ephemeral key pair
        // TODO: Send SSH_MSG_KEX_ECDH_INIT
        // TODO: Receive SSH_MSG_KEX_ECDH_REPLY
        // TODO: Verify server host key signature
        // TODO: Compute shared secret K
        // TODO: Compute exchange hash H
        // TODO: Derive keys A-F
        // Send NEWKEYS
        self.send_packet(&[21]).await?;  // SSH_MSG_NEWKEYS
        println!("Sent NEWKEYS");

        // Receive NEWKEYS
        let pkt = self.recv_packet().await?;
        if pkt.is_empty() || pkt[0] != 21 {
            return Err("Expected NEWKEYS".into());
        }
        println!("Received NEWKEYS");

        self.state = ConnState::Encrypted;
        Ok(())
    }
}
```

---

## 19. Debugging and Packet Analysis

### 19.1 OpenSSH Verbose Mode

```bash
# Level 1: Connection progress
ssh -v user@host

# Level 2: More detail (algorithm negotiation, auth attempts)
ssh -vv user@host

# Level 3: Everything including packet types
ssh -vvv user@host
```

Level 3 output shows:
```
debug3: send packet: type 20        <- SSH_MSG_KEXINIT
debug3: receive packet: type 20     <- SSH_MSG_KEXINIT from server
debug1: kex: algorithm: curve25519-sha256
debug1: kex: host key algorithm: ssh-ed25519
debug1: kex: server->client cipher: chacha20-poly1305@openssh.com MAC: <implicit> compression: none
debug3: send packet: type 30        <- SSH_MSG_KEX_ECDH_INIT
debug3: receive packet: type 31     <- SSH_MSG_KEX_ECDH_REPLY
debug1: Server host key: SHA256:nThbg6kXUpJWGl7E1IGOCspRomTxdCARLviKw6E5SY8
debug3: send packet: type 21        <- SSH_MSG_NEWKEYS
debug3: receive packet: type 21
debug3: send packet: type 5         <- SSH_MSG_SERVICE_REQUEST
debug3: receive packet: type 6      <- SSH_MSG_SERVICE_ACCEPT
debug3: send packet: type 50        <- SSH_MSG_USERAUTH_REQUEST
debug3: receive packet: type 51     <- SSH_MSG_USERAUTH_FAILURE
```

### 19.2 tcpdump / Wireshark

```bash
# Capture SSH traffic (post-handshake is encrypted, but handshake is visible)
sudo tcpdump -i eth0 -w ssh_capture.pcap port 22

# Analyze with tshark
tshark -r ssh_capture.pcap -Y ssh -T fields \
  -e frame.number -e ip.src -e ip.dst \
  -e ssh.message_code -e ssh.kex_algorithms
```

Wireshark can decode the SSH protocol structure, showing:
- Version strings
- KEXINIT contents and negotiated algorithms
- KEX messages (with public keys visible in plaintext before encryption)
- Encrypted channel data (payload not readable, but packet structure visible)

### 19.3 strace — Tracing SSH System Calls

```bash
strace -e trace=read,write,connect,socket ssh user@host 2>&1 | head -100
```

This shows exactly which bytes are read and written, useful for verifying packet framing.

### 19.4 Key Fingerprint Operations

```bash
# Show fingerprint of a host key
ssh-keygen -l -f /etc/ssh/ssh_host_ed25519_key.pub

# Show fingerprint of all keys in known_hosts for a host
ssh-keygen -l -F github.com

# Generate visual "randomart" fingerprint
ssh-keygen -lv -f ~/.ssh/id_ed25519.pub

# Convert between formats
ssh-keygen -e -f ~/.ssh/id_ed25519.pub -m pkcs8   # to PKCS#8 PEM
ssh-keygen -i -f public_key.pem -m pkcs8          # from PKCS#8 PEM
```

### 19.5 Testing Server Configuration

```bash
# Test negotiation without connecting
nmap --script ssh2-enum-algos -p 22 hostname

# Use ssh-audit (comprehensive audit tool)
ssh-audit hostname

# Test specific cipher
ssh -oCiphers=aes256-ctr user@host echo test
```

---

## 20. Mental Models for Reasoning About SSH

### 20.1 The Three-Layer Mental Model

When debugging SSH issues, always identify which layer the problem is in:

```
Problem: "Connection refused"    → TCP layer (not SSH at all)
Problem: "Connection reset"      → TCP layer, or sshd not running
Problem: "Key exchange failed"   → Transport layer
Problem: "Host key mismatch"     → Transport layer (known_hosts)
Problem: "Authentication failed" → Auth layer
Problem: "No route to host"      → Below TCP
Problem: "Channel request failed"→ Connection layer
Problem: "Port forwarding fails" → Connection layer (permissions)
```

### 20.2 The Trust Model

SSH establishes trust in two orthogonal directions:

```
SERVER authentication → "Am I talking to the right server?"
                        Answered by host key + known_hosts
                        MUST be verified before sending credentials

CLIENT authentication → "Who is this user?"
                        Answered by publickey, password, cert
                        Only possible after server is verified
```

This asymmetry is fundamental. Server auth comes first because sending credentials to a fake server would give the attacker your credentials.

### 20.3 The Channel Abstraction

Think of SSH connection layer as a virtual network switch inside a single TCP connection:

```
SSH connection (one TCP connection)
├── Channel 0: interactive shell
├── Channel 1: local port forward (localhost:8080 → db:5432)
├── Channel 2: agent proxy
└── Channel 3: SFTP subsystem
```

Each channel has its own flow control. Data from different channels is multiplexed at the packet level and demultiplexed by channel number.

### 20.4 Forward Secrecy Mental Model

Why does SSH use ephemeral keys for key exchange instead of just encrypting with the server's host key?

```
Without forward secrecy:
  If attacker records all traffic AND later obtains server's host key
  → Can decrypt all past sessions retroactively

With forward secrecy (ephemeral DH):
  The session keys are derived from ephemeral key pairs
  Ephemeral private keys are discarded after key exchange
  Even if server's long-term key is later compromised
  → Cannot decrypt past sessions (ephemeral keys are gone)
```

Curve25519 key exchange provides forward secrecy because the client_priv and server_priv are ephemeral — generated fresh for each session and never stored.

### 20.5 The Sequence Number Model

Every packet has a sequence number embedded in its MAC computation. This creates an implicit linked chain:

```
Packet 0: MAC computed over (seqnr=0 || packet_0_ciphertext)
Packet 1: MAC computed over (seqnr=1 || packet_1_ciphertext)
Packet 2: MAC computed over (seqnr=2 || packet_2_ciphertext)
```

An attacker who:
- Reorders packets → Wrong sequence number in MAC → MAC failure → Connection torn down
- Replays a packet → Sequence number already used → MAC doesn't match expected sequence
- Drops a packet → Next packet has wrong sequence number → MAC failure

The sequence number is the simplest form of ordered, authenticated delivery. Combined with TCP's ordering guarantee, it provides a fully ordered, authenticated byte stream.

### 20.6 The Signature Binding Model

Every authentication signature is bound to the session ID. Understand this as a chain of commitments:

```
session_id  = H (exchange hash from first KEX)
            = SHA-256(version_strings || kexinits || host_key || eph_pubkeys || shared_secret)

auth_signature = Sign(private_key,
                      session_id ||
                      "publickey" ||
                      username ||
                      "ssh-connection" ||
                      public_key_blob)
```

This means:
- The signature is specific to this session (via session_id)
- The signature commits to this username
- The signature commits to this service
- Replaying an auth signature from a different session won't work (different session_id)
- A MITM cannot forward your auth signature to a different server (different session_id)

### 20.7 Algorithm Negotiation Model

Think of algorithm negotiation as two ordered preference lists and the output as the intersection following the client's priority:

```
Client:  [A, B, C, D]
Server:  [C, B, E, F]

Intersection following client order:
  A: in server? No → skip
  B: in server? Yes → B is selected
```

The client's preference order determines the final choice. This means the client's `ssh_config` (or `KexAlgorithms`, `Ciphers`, `MACs` directives) controls what algorithm is used. A security-conscious client can force strong algorithms even if the server lists weak ones first.

---

## Appendix A: Key RFCs

| RFC    | Title                                                             |
|--------|-------------------------------------------------------------------|
| 4250   | SSH Protocol Assigned Numbers                                     |
| 4251   | SSH Protocol Architecture                                         |
| 4252   | SSH Authentication Protocol                                       |
| 4253   | SSH Transport Layer Protocol                                      |
| 4254   | SSH Connection Protocol                                           |
| 4255   | Using DNS to Securely Publish SSH Key Fingerprints (SSHFP)       |
| 4256   | Generic Message Exchange Authentication for SSH                   |
| 4344   | SSH Transport Layer Encryption Modes (CTR mode)                   |
| 4345   | Improved ArcFour Modes for SSH (deprecated)                       |
| 4419   | DH Group Exchange for SSH                                         |
| 4462   | GSSAPI Authentication and Key Exchange for SSH                    |
| 5656   | Elliptic Curve DH Exchange in SSH                                 |
| 6594   | Use of SHA-256 Algorithm with RSA, DSA in SSHFP                  |
| 8160   | IUTF8 Terminal Mode in SSH                                        |
| 8308   | Extension Negotiation in SSH                                      |
| 8332   | Use of RSA Keys with SHA-256 and SHA-512 in SSH                   |
| 8731   | Curve25519 and Curve448 for SSH                                   |

## Appendix B: OpenSSH Extension Negotiation

OpenSSH uses `EXT_INFO` (RFC 8308) to negotiate additional features after NEWKEYS:

```
SSH_MSG_EXT_INFO (7)
  uint32   nr-extensions
  string   extension-name
  string   extension-value
  ...
```

OpenSSH extensions:
- `server-sig-algs`: list of signature algorithms the server supports (informs client which algorithms to use when probing publickey auth)
- `delay-compression`: delay enabling compression until after authentication
- `no-flow-control`: disable per-channel flow control
- `elevation`: request elevated privileges on Windows
- `strict-kex`: enable strict sequence number enforcement (Terrapin fix)
- `ping@openssh.com`: allow keepalive pings within connection layer

## Appendix C: SFTP Protocol

SFTP (SSH File Transfer Protocol) runs as a subsystem over SSH. It is NOT FTP over SSH — it is a completely different, binary protocol.

Version 3 of SFTP (the most common) operates over a single SSH session channel:

```
Client sends: SSH_FXP_INIT
  version 3

Server sends: SSH_FXP_VERSION
  version 3

Operations:
  SSH_FXP_OPEN      → SSH_FXP_HANDLE or SSH_FXP_STATUS
  SSH_FXP_READ      → SSH_FXP_DATA or SSH_FXP_STATUS
  SSH_FXP_WRITE     → SSH_FXP_STATUS
  SSH_FXP_CLOSE     → SSH_FXP_STATUS
  SSH_FXP_OPENDIR   → SSH_FXP_HANDLE
  SSH_FXP_READDIR   → SSH_FXP_NAME
  SSH_FXP_STAT      → SSH_FXP_ATTRS
  SSH_FXP_RENAME    → SSH_FXP_STATUS
  SSH_FXP_REMOVE    → SSH_FXP_STATUS
```

Each request has a uint32 `request-id` which is echoed in the response, allowing pipelining (multiple outstanding requests without waiting for each response).

---

*This guide covers SSH protocol version 2 as standardized. Implementation details reference OpenSSH, the reference implementation. Protocol behavior is governed by the IETF RFCs listed in Appendix A.*

Now let me write the comprehensive SSH guide:**128KB, 3,600+ lines** — a complete reference. Here's what's covered:

**Protocol Architecture** — The three-layer model (Transport → Auth → Connection) with the exact message number space and why the separation exists.

**Transport Layer** — Version exchange, binary packet format with exact byte layout, KEXINIT algorithm negotiation with all name-lists, full key derivation (A–F letters with extension rules), NEWKEYS synchronization, and why separate per-direction IVs/keys matter.

**Authentication Layer** — All methods: `none` (probing), `password`, `publickey` (two-phase probe + actual), `keyboard-interactive`, `gssapi-with-mic`. Exact packet formats with field-by-field breakdowns.

**Connection Layer** — Channel lifecycle, the window-size flow control model, all channel types (`session`, `direct-tcpip`, `forwarded-tcpip`, `x11`, `auth-agent`), extended data (stderr), PTY requests.

**Cryptography in Depth** — AES-CTR, AES-GCM, ChaCha20-Poly1305 (including OpenSSH's dual-key trick), MAC-then-Encrypt vs ETM, all KEX algorithms, post-quantum hybrid `sntrup761x25519`.

**Key Exchange** — Full DH group exchange, curve25519 math, ECDH with NIST curves, exchange hash `H` construction, low-order point attack detection.

**ASCII Wire Diagrams** — Full connection trace from TCP handshake → version → KEXINIT → KEX → NEWKEYS → service request → auth → channel open → shell → data → teardown. Real hex packet example.

**C Implementation** — Complete transport skeleton: growable SSH buffer, binary packet encode/decode, version exchange, KEXINIT send/parse, message dispatch loop. Plus curve25519 key exchange and RFC-compliant key derivation with libsodium.

**Rust Implementation** — Type-safe `SshBuf`/`SshParser`, `MsgType` enum, `KexInit` struct with encode/parse/negotiate, key derivation, `mpint` encoding, async Tokio connection state machine, unit tests.

**Security** — Terrapin attack, timing attacks, TOFU, CBC padding oracles, privilege separation model, hardening checklist.

**Mental Models** — Three-layer debugging triage, server-first trust asymmetry, forward secrecy reasoning, sequence number chain, signature binding chain, algorithm negotiation as ordered intersection.