# TACACS+ — Complete In-Depth Technical Reference Guide

---

## Table of Contents

1. [Introduction & Background](#1-introduction--background)
2. [Historical Evolution: TACACS → XTACACS → TACACS+](#2-historical-evolution)
3. [The AAA Security Framework](#3-the-aaa-security-framework)
4. [TACACS+ Architecture & Components](#4-tacacs-architecture--components)
5. [Protocol Fundamentals](#5-protocol-fundamentals)
6. [Packet Structure & Encoding](#6-packet-structure--encoding)
7. [Encryption Mechanism](#7-encryption-mechanism)
8. [Authentication — Deep Dive](#8-authentication--deep-dive)
9. [Authorization — Deep Dive](#9-authorization--deep-dive)
10. [Accounting — Deep Dive](#10-accounting--deep-dive)
11. [Session Management & State Machine](#11-session-management--state-machine)
12. [TACACS+ vs RADIUS — Full Comparison](#12-tacacs-vs-radius--full-comparison)
13. [Network Device Access Control Flows](#13-network-device-access-control-flows)
14. [Server Implementations](#14-server-implementations)
15. [Client-Side Configuration (Cisco IOS / NX-OS / IOS-XE / IOS-XR)](#15-client-side-configuration)
16. [High Availability, Redundancy & Load Balancing](#16-high-availability-redundancy--load-balancing)
17. [Security Hardening & Best Practices](#17-security-hardening--best-practices)
18. [Privilege Levels & Command Authorization](#18-privilege-levels--command-authorization)
19. [TACACS+ in Modern Environments](#19-tacacs-in-modern-environments)
20. [Troubleshooting & Debugging](#20-troubleshooting--debugging)
21. [Common Deployment Scenarios & Architectures](#21-common-deployment-scenarios--architectures)
22. [Mental Model Summary](#22-mental-model-summary)

---

## 1. Introduction & Background

**TACACS+** (Terminal Access Controller Access-Control System Plus) is a network security protocol that provides centralized **Authentication**, **Authorization**, and **Accounting** (AAA) services for network devices. It was developed by Cisco Systems and is defined primarily in **RFC 8907** (published September 2020, which finally formalized what was previously only a Cisco draft standard).

### Why TACACS+ Exists

In any non-trivial network infrastructure, you face a fundamental operational security problem:

- You have **dozens to thousands of network devices** (routers, switches, firewalls, load balancers, wireless controllers).
- Each device has its own local user database.
- Managing credentials across all these devices individually is operationally impossible and a major security risk.
- You need to know **who logged in**, **what they did**, and **whether they were allowed to do it**.

TACACS+ solves this by centralizing all three concerns into a dedicated server that all network devices query.

### Core Design Philosophy

TACACS+ was designed around a key architectural insight: **separate the three functions of AAA into independent, independently negotiable exchanges**. This is fundamentally different from RADIUS, which bundles them together. This separation gives TACACS+ enormous flexibility in complex enterprise deployments.

---

## 2. Historical Evolution

Understanding the history gives you a mental model for *why* certain design decisions were made.

### 2.1 Original TACACS (1984)

- Described in **RFC 927** (1984) and **RFC 1492** (1993).
- Originally designed for MILNET (Military Network) — the precursor to the Internet.
- Used **UDP** on port 49.
- Very simple: a client sends credentials, the server responds with ACCEPT or REJECT.
- **No encryption** — credentials sent in cleartext.
- **No separation** of AAA — authentication and authorization were bundled.
- No accounting whatsoever.

```
Original TACACS Flow (UDP):
+--------+   Username/Password (UDP/49, CLEARTEXT)   +--------+
| Client |  ----------------------------------------> | Server |
|        |  <---------------------------------------- |        |
+--------+           ACCEPT / REJECT                  +--------+
```

### 2.2 XTACACS (Extended TACACS) — 1990

- Cisco's proprietary extension to original TACACS.
- Still UDP-based.
- Added **separate authorization** and **accounting** packet types.
- Still no encryption.
- Cisco-proprietary, never standardized.

### 2.3 TACACS+ (1993 onward)

- A **completely new protocol** — NOT backward-compatible with TACACS or XTACACS despite the name.
- Developed by Cisco, released as a draft RFC, **finally standardized as RFC 8907 in 2020**.
- Switched from UDP to **TCP** (reliability, ordered delivery).
- **Full payload encryption** using MD5-based obfuscation.
- Complete separation of Authentication, Authorization, and Accounting.
- Support for **multiple authentication methods** (PAP, CHAP, MS-CHAP, ASCII, etc.).
- Extensible attribute-value (AV) pair system for authorization.

```
Timeline:
1984 -------- 1990 -------- 1993 -------- 2020
  |              |              |             |
TACACS         XTACACS       TACACS+       RFC 8907
(RFC 927)    (Cisco prop.)  (Cisco draft) (Formalized)
UDP/49        UDP/49         TCP/49         TCP/49
No encrypt    No encrypt     Encrypted      Encrypted
Bundle AAA    Partial sep.   Full sep.      Full sep.
```

---

## 3. The AAA Security Framework

AAA is the conceptual backbone. Every TACACS+ exchange maps directly to one of these three pillars.

### 3.1 Authentication — "Who Are You?"

Authentication verifies **identity**. It answers: "Is this person/device who they claim to be?"

TACACS+ supports multiple authentication mechanisms:

| Method | Description | Security Level |
|---|---|---|
| ASCII | Interactive — server prompts, client responds with typed text | Low |
| PAP | Password Authentication Protocol — plaintext password | Low |
| CHAP | Challenge Handshake Authentication Protocol — MD5 hash challenge | Medium |
| MS-CHAP | Microsoft's variant of CHAP | Medium |
| MS-CHAPv2 | Improved MS-CHAP with mutual authentication | Medium-High |
| EAP | Extensible Authentication Protocol passthrough | High |

### 3.2 Authorization — "What Are You Allowed to Do?"

Authorization happens **after** successful authentication. It determines what the authenticated identity is **permitted** to do.

In network device management, this translates to:
- What **privilege level** can you access? (exec vs enable vs config mode)
- What **commands** can you execute?
- What **services** can you access?
- What **network resources** can you reach?

Authorization in TACACS+ works through **attribute-value (AV) pairs** — a key=value system where the server sends back a list of permissions, restrictions, and settings.

### 3.3 Accounting — "What Did You Do?"

Accounting records **what happened** — it is the audit trail. Accounting records are sent from the network device (NAS) to the TACACS+ server and typically log:

- Session start/stop times
- Commands executed (with arguments)
- Bytes/packets transferred
- User identity, source IP, privilege level used

Accounting serves **compliance**, **forensics**, **billing**, and **security monitoring** purposes.

### 3.4 The AAA Independence Principle

One of TACACS+'s greatest architectural strengths: **each AAA function is an independent exchange**. You can:

- Authenticate against TACACS+ but authorize locally.
- Authenticate and authorize via TACACS+ but do accounting via RADIUS.
- Use different TACACS+ servers for authentication vs. accounting.
- Skip authorization entirely and rely on authentication-granted privilege levels.

```
AAA Independence Model:

  +------------------+     +------------------+     +------------------+
  |  Authentication  |     |  Authorization   |     |   Accounting     |
  |                  |     |                  |     |                  |
  |  "Who are you?"  |     | "What can you do"|     | "What did you do"|
  |                  |     |                  |     |                  |
  | - Independent    |     | - Independent    |     | - Independent    |
  | - Own packets    |     | - Own packets    |     | - Own packets    |
  | - Own server     |     | - Own server     |     | - Own server     |
  +------------------+     +------------------+     +------------------+
          |                        |                        |
          +------------------------+------------------------+
                                   |
                        Can all point to same
                        TACACS+ server OR
                        different servers per function
```

---

## 4. TACACS+ Architecture & Components

### 4.1 Core Components

```
TACACS+ Deployment Architecture:

                        CORPORATE NETWORK
  +=======================================================================+
  |                                                                       |
  |   +------------------+         +------------------+                  |
  |   |  TACACS+ Server  |         |  TACACS+ Server  |                  |
  |   |   (Primary)      |         |   (Secondary)    |                  |
  |   |                  |         |                  |                  |
  |   | - User database  |         | - Replica/Backup |                  |
  |   | - Policy engine  |         | - Failover only  |                  |
  |   | - AV-pair rules  |         |                  |                  |
  |   | - Audit logs     |         |                  |                  |
  |   | IP: 10.0.0.10    |         | IP: 10.0.0.11    |                  |
  |   +--------+---------+         +--------+---------+                  |
  |            |   TCP/49                   |   TCP/49                   |
  |            |                            |                            |
  |   +--------+----------------------------+--------+                   |
  |   |              Management Network              |                   |
  |   |              (Out-of-Band preferred)         |                   |
  |   +---+--------+--------+--------+--------+------+                   |
  |       |        |        |        |        |                          |
  |    +--+--+  +--+--+  +--+--+  +--+--+  +--+--+                      |
  |    | RTR |  | SWT |  | FW  |  | LB  |  | WLC |                      |
  |    | NAS |  | NAS |  | NAS |  | NAS |  | NAS |                      |
  |    +--+--+  +--+--+  +--+--+  +--+--+  +--+--+                      |
  |       |        |        |        |        |                          |
  +=======|========|========|========|========|=========================+
          |        |        |        |        |
       Console  SSH/     Console  Console  Console
       SSH      Telnet

 NAS = Network Access Server (any device acting as TACACS+ client)
```

### 4.2 Component Roles Explained

#### TACACS+ Server (Daemon)
The server is the **policy decision point**. It:
- Maintains the user/group database (locally or via LDAP/AD backend).
- Evaluates authentication attempts.
- Makes authorization decisions based on configured policies.
- Receives and stores accounting records.
- Manages the **shared secret** for each client.

#### Network Access Server (NAS) / TACACS+ Client
The NAS is the **policy enforcement point**. It:
- Is the network device being managed (router, switch, firewall, etc.).
- Intercepts login attempts.
- Forwards credentials to the TACACS+ server.
- Enforces the authorization decisions received.
- Sends accounting data after actions occur.
- Has the **shared secret** configured to encrypt/decrypt traffic.

#### Shared Secret
The shared secret is the **foundation of TACACS+ security**. It is:
- A pre-configured symmetric secret known to both client and server.
- Used in the MD5-based encryption of packet payloads.
- Different secrets can (and should) be configured per client device.
- **Never transmitted over the network** — it is used locally at each end.

### 4.3 The Client-Server Relationship in Detail

```
Single NAS ↔ TACACS+ Server Relationship:

+==============================================================+
|                    NAS (e.g., Cisco Router)                  |
|                                                              |
|  +---------------------------+   +------------------------+  |
|  |   AAA Configuration       |   |   Active Sessions      |  |
|  |                           |   |                        |  |
|  | tacacs-server host        |   | User: alice            |  |
|  |   10.0.0.10               |   | Priv: 15               |  |
|  | key: MySecret123          |   | Time: 14:32:01         |  |
|  | timeout: 5                |   |                        |  |
|  | port: 49                  |   | User: bob              |  |
|  +---------------------------+   | Priv: 1                |  |
|                                  +------------------------+  |
+==========================+===================================+
                           |
                           | TCP/49
                           | Encrypted payload
                           | (shared secret: MySecret123)
                           |
+==========================+===================================+
|                    TACACS+ Server                            |
|                                                              |
|  +---------------------------+   +------------------------+  |
|  |   Client Registry         |   |   Policy Engine        |  |
|  |                           |   |                        |  |
|  | 10.0.0.1 (router1)       |   | Group: netadmin        |  |
|  |   secret: MySecret123     |   |   priv-lvl = 15        |  |
|  |                           |   |   cmd = show *         |  |
|  | 10.0.0.2 (switch1)       |   |   cmd = conf t         |  |
|  |   secret: SwitchSec456    |   |                        |  |
|  +---------------------------+   | Group: readonly        |  |
|                                  |   priv-lvl = 1         |  |
|  +---------------------------+   |   cmd = show *         |  |
|  |   User Database           |   |   cmd-deny = conf *    |  |
|  |                           |   +------------------------+  |
|  | alice: group=netadmin     |                              |
|  | bob: group=readonly       |   +------------------------+  |
|  | charlie: group=netadmin   |   |   Accounting Log       |  |
|  +---------------------------+   |                        |  |
|                                  | [2026-05-04 14:32:01]  |  |
|                                  | alice@10.0.0.1 START   |  |
|                                  | cmd: show run          |  |
|                                  +------------------------+  |
+==============================================================+
```

---

## 5. Protocol Fundamentals

### 5.1 Transport Layer — TCP Port 49

TACACS+ operates over **TCP port 49**. This is a critical design decision with significant implications:

**Why TCP (not UDP)?**

| Concern | TCP Benefit |
|---|---|
| Reliability | TCP guarantees delivery — lost auth packets don't silently fail |
| Ordering | Packets arrive in order — multi-packet auth dialogs remain coherent |
| Flow Control | TCP handles congestion — server not overwhelmed |
| Connection State | Stateful — both sides know if the other disappears |
| Error Detection | TCP checksum + retransmission |

**The TCP Connection Model:**

TACACS+ has two connection models:

1. **Single-connection mode** (preferred): One persistent TCP connection is established per session and reused for multiple AAA exchanges. Reduces TCP handshake overhead.

2. **Per-session mode**: A new TCP connection is opened for every AAA transaction and closed after. More overhead but simpler state management.

```
Single-Connection Mode (Preferred):
                                                              
  NAS                                    TACACS+ Server
   |                                           |
   |--- TCP SYN -------------------------------->|
   |<-- TCP SYN-ACK -----------------------------|
   |--- TCP ACK -------------------------------->|
   |          (TCP connection established)       |
   |                                             |
   |--- AUTHEN START (seq=1) ------------------>|  AUTH
   |<-- AUTHEN REPLY (seq=2) -------------------|  exchange
   |--- AUTHEN CONTINUE (seq=3) -------------->|  1
   |<-- AUTHEN REPLY (seq=4, PASS) -------------|
   |                                             |
   |--- AUTHOR REQUEST (seq=1, new session) --->|  AUTHZ
   |<-- AUTHOR RESPONSE (seq=2, PASS_ADD) ------|  exchange
   |                                             |
   |--- ACCT REQUEST (seq=1) ------------------>|  ACCT
   |<-- ACCT REPLY (seq=2, SUCCESS) ------------|  exchange
   |                                             |
   | [connection kept alive for next session]    |
   |                                             |
   |--- TCP FIN -------------------------------->|  (when done)
   |<-- TCP FIN-ACK -----------------------------|
```

### 5.2 Session Concept

A **TACACS+ session** is identified by a **session_id** — a 32-bit random number generated by the client. All packets belonging to one AAA transaction (e.g., one login attempt) share the same session_id. This allows multiplexing over a single TCP connection.

### 5.3 Sequence Numbers

Every packet in a TACACS+ session has a sequence number starting at **1** and incrementing by 1 for each packet. Client-originated packets have **odd** sequence numbers; server-originated replies have **even** sequence numbers.

```
Sequence Number Pattern:

  NAS (Client)                    Server
     |                               |
     |-- seq=1 (client sends) ------>|
     |<- seq=2 (server replies) ------|
     |-- seq=3 (client continues) -->|
     |<- seq=4 (server replies) ------|
     |                               |
  [Max sequence = 255. New session needed after that]
```

### 5.4 Packet Types Overview

TACACS+ defines three major packet type families:

```
Packet Type Families:

  TAC_PLUS_AUTHEN  (0x01) — Authentication packets
  TAC_PLUS_AUTHOR  (0x02) — Authorization packets
  TAC_PLUS_ACCT    (0x03) — Accounting packets

Within Authentication (TAC_PLUS_AUTHEN = 0x01):

  Subtypes by direction:
    Client → Server:
      TAC_PLUS_AUTHEN_START     (seq=1, initial request)
      TAC_PLUS_AUTHEN_CONTINUE  (seq=3+, continuation)

    Server → Client:
      TAC_PLUS_AUTHEN_REPLY     (seq=2, 4, 6..., server response)

Within Authorization (TAC_PLUS_AUTHOR = 0x02):

  Client → Server:
    TAC_PLUS_AUTHOR_REQUEST     (single request)

  Server → Client:
    TAC_PLUS_AUTHOR_RESPONSE    (single response)

Within Accounting (TAC_PLUS_ACCT = 0x03):

  Client → Server:
    TAC_PLUS_ACCT_REQUEST       (single request)

  Server → Client:
    TAC_PLUS_ACCT_REPLY         (single response)
```

---

## 6. Packet Structure & Encoding

### 6.1 The Common Header

Every TACACS+ packet begins with a **12-byte fixed header**:

```
TACACS+ Common Header (12 bytes):

 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|    major_version (4 bits)    |  minor_version (4 bits)        |  Byte 0
|    type (8 bits)                                              |  Byte 1
|    seq_no (8 bits)                                            |  Byte 2
|    flags (8 bits)                                             |  Byte 3
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                     session_id (32 bits)                      |  Bytes 4-7
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                     length (32 bits)                          |  Bytes 8-11
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

**Field Breakdown:**

| Field | Size | Description |
|---|---|---|
| major_version | 4 bits | Always 0xC (decimal 12) for TACACS+ |
| minor_version | 4 bits | 0x0 (default) or 0x1 (for some auth types) |
| type | 8 bits | 0x01=AUTHEN, 0x02=AUTHOR, 0x03=ACCT |
| seq_no | 8 bits | Sequence number (1 to 255) |
| flags | 8 bits | Control flags (see below) |
| session_id | 32 bits | Random session identifier |
| length | 32 bits | Length of the body (payload) only |

**Header Flags:**

| Flag Bit | Name | Meaning |
|---|---|---|
| 0x01 | TAC_PLUS_UNENCRYPTED_FLAG | Payload is NOT encrypted (testing only, never in prod) |
| 0x04 | TAC_PLUS_SINGLE_CONNECT_FLAG | Use single-connection mode for this session |

**CRITICAL**: The header is **always sent in the clear** (unencrypted). Only the **body** is encrypted. This means an attacker on the wire can see packet types, sequence numbers, and session IDs — but not the actual content (usernames, passwords, commands).

### 6.2 Authentication START Packet Body

Sent by NAS to initiate an authentication session:

```
Authentication START Body:

+------------------+
| action (1 byte)  |   TAC_PLUS_AUTHEN_LOGIN=0x01
|                  |   TAC_PLUS_AUTHEN_CHPASS=0x02
|                  |   TAC_PLUS_AUTHEN_SENDAUTH=0x04
+------------------+
| priv_lvl (1byte) |   Requested privilege level (0-15)
+------------------+
| authen_type      |   PAP=0x02, CHAP=0x03, ASCII=0x01, etc.
| (1 byte)         |
+------------------+
| authen_service   |   LOGIN=0x01, ENABLE=0x02, PPP=0x03, etc.
| (1 byte)         |
+------------------+
| user_len (1byte) |   Length of username field
+------------------+
| port_len (1byte) |   Length of port name (e.g., "tty0")
+------------------+
| rem_addr_len     |   Length of remote address (e.g., "192.168.1.5")
| (1 byte)         |
+------------------+
| data_len (1byte) |   Length of additional data field
+------------------+
| user (variable)  |   Username string
+------------------+
| port (variable)  |   Port/interface name
+------------------+
| rem_addr(variable|   Remote client address
+------------------+
| data (variable)  |   Additional auth data (PAP password, CHAP challenge, etc.)
+------------------+
```

### 6.3 Authentication REPLY Packet Body

Sent by server in response to START or CONTINUE:

```
Authentication REPLY Body:

+----------------------+
| status (1 byte)      |   PASS=0x01, FAIL=0x02, GETDATA=0x03,
|                      |   GETUSER=0x04, GETPASS=0x05, RESTART=0x06,
|                      |   ERROR=0x07, FOLLOW=0x21
+----------------------+
| flags (1 byte)       |   TAC_PLUS_REPLY_FLAG_NOECHO=0x01
|                      |   (suppress echo for password prompt)
+----------------------+
| server_msg_len       |   Length of message to display to user
| (2 bytes)            |
+----------------------+
| data_len (2 bytes)   |   Length of data field
+----------------------+
| server_msg(variable) |   Human-readable prompt or message
+----------------------+
| data (variable)      |   Additional protocol data
+----------------------+
```

### 6.4 Authorization REQUEST Packet Body

```
Authorization REQUEST Body:

+----------------------+
| authen_method (1byte)|   How user was authenticated (e.g., TACACSPLUS=0x06)
+----------------------+
| priv_lvl (1 byte)    |   Current privilege level of the session
+----------------------+
| authen_type (1 byte) |   Authentication type used
+----------------------+
| authen_svc (1 byte)  |   Authentication service used
+----------------------+
| user_len (1 byte)    |
+----------------------+
| port_len (1 byte)    |
+----------------------+
| rem_addr_len (1 byte)|
+----------------------+
| arg_cnt (1 byte)     |   Number of AV-pair arguments
+----------------------+
| arg_1_len (1 byte)   |   Length of first argument
| arg_2_len (1 byte)   |   Length of second argument
| ... (variable)       |
+----------------------+
| user (variable)      |   Username
+----------------------+
| port (variable)      |   Port name
+----------------------+
| rem_addr (variable)  |   Remote address
+----------------------+
| arg_1 (variable)     |   First AV-pair (e.g., "service=shell")
| arg_2 (variable)     |   Second AV-pair (e.g., "cmd=show")
| ... (variable)       |
+----------------------+
```

### 6.5 Attribute-Value (AV) Pairs

AV pairs are the flexible data-carrying mechanism of TACACS+ authorization and accounting. They use the format:

```
Mandatory AV pair:    attribute=value     (equals sign, server MUST act on it)
Optional AV pair:     attribute*value     (asterisk, server MAY ignore it)
```

**Common AV Pairs:**

| Attribute | Direction | Meaning |
|---|---|---|
| `service` | Request/Response | Service type: shell, ppp, raccess, x25, etc. |
| `cmd` | Request/Response | Command being authorized |
| `cmd-arg` | Request/Response | Arguments to the command |
| `priv-lvl` | Response | Privilege level (0-15) |
| `acl` | Response | ACL number/name to apply |
| `timeout` | Response | Idle timeout in minutes |
| `idletime` | Response | Idle time limit |
| `autocmd` | Response | Auto-execute command on login |
| `noescape` | Response | Prevent escape to exec mode |
| `nohangup` | Response | Don't hangup after autocmd |
| `start_time` | Accounting | Session start timestamp |
| `stop_time` | Accounting | Session stop timestamp |
| `elapsed_time` | Accounting | Duration in seconds |
| `bytes_in` | Accounting | Inbound bytes |
| `bytes_out` | Accounting | Outbound bytes |
| `task_id` | Accounting | Unique task/accounting record ID |
| `timezone` | Accounting | Timezone of the NAS |

---

## 7. Encryption Mechanism

### 7.1 The MD5-Based Obfuscation Scheme

TACACS+ uses a **pseudo-one-time-pad** encryption scheme based on MD5 hashing. It is important to understand this is **not AES** — it is stream cipher-like XOR obfuscation using repeated MD5 hashing.

**Terminology note**: RFC 8907 calls this "obfuscation" rather than encryption, acknowledging that it relies on MD5 which is considered cryptographically weak by modern standards.

### 7.2 Encryption Algorithm — Step by Step

```
Encryption Process:

Given:
  K   = Shared secret key
  H   = Header (12 bytes, sent unencrypted)
  S   = session_id (from header, 4 bytes)
  V   = version byte (from header, 1 byte)
  seq = sequence number (from header, 1 byte)
  P   = Plaintext body to encrypt

Step 1: Generate the first MD5 hash:
  MD5_1 = MD5(K + S + V + seq)
           \_____________________/
            Concatenated together

Step 2: Generate subsequent hashes (for bodies > 16 bytes):
  MD5_2 = MD5(K + S + V + seq + MD5_1)
  MD5_3 = MD5(K + S + V + seq + MD5_2)
  ...continuing until enough keystream is generated

Step 3: Create keystream by concatenating MD5 hashes:
  Keystream = MD5_1 || MD5_2 || MD5_3 || ...
  (truncated to the length of the plaintext body)

Step 4: XOR plaintext with keystream:
  Ciphertext[i] = Plaintext[i] XOR Keystream[i]

Step 5: Send:
  Header (12 bytes, UNENCRYPTED) + Ciphertext (encrypted body)
```

**Visual representation:**

```
Encryption Key Generation Chain:

 [Shared Secret + session_id + version + seq_no]
                        |
                        v
                  MD5 Hash #1 (16 bytes)
                  /           \
            XOR with         Used as input for
          plaintext[0-15]    next hash
                              |
                              v
          [Secret + S + V + seq + MD5#1]
                              |
                              v
                      MD5 Hash #2 (16 bytes)
                      /           \
                XOR with         Used for
              plaintext[16-31]   next hash
                                  |
                                  v
                          MD5 Hash #3 (16 bytes)
                          ...and so on...
```

### 7.3 Security Implications of MD5-Based Encryption

**Known weaknesses:**

1. **MD5 is cryptographically broken**: Collision attacks are practical. MD5 should not be used for security-sensitive operations.
2. **No forward secrecy**: If the shared secret is compromised, all historical sessions can be decrypted.
3. **No integrity protection beyond MD5**: The scheme does not provide strong HMAC-based message authentication.
4. **Susceptible to offline dictionary attacks**: If an attacker captures traffic, they can brute-force the shared secret using the known plaintext of protocol headers.

**Mitigations and modern guidance:**

- Use **strong, long, random shared secrets** (minimum 32 characters, ideally 64+).
- Run TACACS+ traffic on a **dedicated out-of-band management network** not accessible from regular data paths.
- Use **RFC 8907's recommended** approach: tunnel TACACS+ within TLS (TACACS+ over TLS, defined in RFC 9105).
- Treat the shared secret as a **high-value cryptographic credential** and rotate it regularly.

### 7.4 TACACS+ over TLS (RFC 9105)

RFC 9105 (2021) defines **TACACS+ over TLS** as the modern secure transport:

- Uses **TLS 1.2 or 1.3** for the transport layer encryption.
- The inner TACACS+ packets use the **TAC_PLUS_UNENCRYPTED_FLAG** (since TLS handles encryption).
- Default port: **TCP 49** (same, or optionally a different port).
- Provides strong confidentiality, integrity, and authentication of the server itself.
- Protects against the MD5 weaknesses.

```
TACACS+ over TLS (RFC 9105) Stack:

  +--------------------------------+
  |   TACACS+ Application Layer    |  (Unencrypted flag set)
  +--------------------------------+
  |   TLS 1.2 / 1.3               |  (Strong encryption)
  +--------------------------------+
  |   TCP / Port 49                |  (Reliable transport)
  +--------------------------------+
  |   IP                           |
  +--------------------------------+
```

---

## 8. Authentication — Deep Dive

### 8.1 Authentication Methods and Their Flows

#### 8.1.1 ASCII Authentication (Interactive Login)

This is the most common method for interactive CLI access. The server drives the conversation, sending prompts; the NAS relays them to the user.

```
ASCII Authentication Flow (Interactive Login):

  User Terminal        NAS (Router)              TACACS+ Server
       |                    |                          |
       |  [connects SSH]    |                          |
       |<---[TCP session]-->|                          |
       |                    |                          |
       |                    |--- AUTHEN START -------->|
       |                    |  type=ASCII              |
       |                    |  action=LOGIN            |
       |                    |  user="" (empty)         |
       |                    |                          |
       |                    |<-- AUTHEN REPLY ---------|
       |                    |  status=GETUSER          |
       |                    |  server_msg="Username: " |
       |                    |                          |
       |<-- "Username: " ---|                          |
       |--- "alice\n" ----->|                          |
       |                    |                          |
       |                    |--- AUTHEN CONTINUE ----->|
       |                    |  user_msg="alice"        |
       |                    |                          |
       |                    |<-- AUTHEN REPLY ---------|
       |                    |  status=GETPASS          |
       |                    |  flags=NOECHO            |
       |                    |  server_msg="Password: " |
       |                    |                          |
       |<-- "Password: " ---|  (no echo to terminal)   |
       |--- "s3cr3t\n" ---->|                          |
       |                    |                          |
       |                    |--- AUTHEN CONTINUE ----->|
       |                    |  user_msg="s3cr3t"       |
       |                    |                          |
       |                    |<-- AUTHEN REPLY ---------|
       |                    |  status=PASS             |
       |                    |                          |
       |<-- Shell prompt ---|  [authorization follows]  |
```

#### 8.1.2 PAP Authentication

PAP (Password Authentication Protocol) sends the password directly in the AUTHEN START packet. The NAS collects the password locally (via the login prompt it controls) and includes it in the START packet.

```
PAP Authentication Flow:

  User Terminal        NAS                       TACACS+ Server
       |                |                              |
       |<--"Username: "--| (NAS prompts locally)        |
       |---"alice"------>|                              |
       |<--"Password: "--|                              |
       |---"s3cr3t"----->|                              |
       |                 |                              |
       |                 |--- AUTHEN START ------------>|
       |                 |  type=PAP                    |
       |                 |  user="alice"                |
       |                 |  data="s3cr3t" (encrypted)   |
       |                 |                              |
       |                 |<-- AUTHEN REPLY -------------|
       |                 |  status=PASS or FAIL         |
       |                 |                              |
```

Note: In PAP, the password is included in the START packet. The NAS handles the user interface itself — only one round trip to the server.

#### 8.1.3 CHAP Authentication

CHAP uses a challenge-response mechanism. The NAS generates a random challenge and sends it along with the username. The user's device (or the NAS for CLI access) computes: MD5(id + password + challenge) and sends the hash.

```
CHAP Authentication Flow:

  User/NAS             NAS                       TACACS+ Server
       |                |                              |
       |                |  (NAS generates challenge:   |
       |                |   random 16-byte value)       |
       |<--CHAP Chall---|                              |
       |  (id + chall)  |                              |
       |                |                              |
       |  MD5(id+pass   |                              |
       |      +chall)   |                              |
       |---CHAP Resp--->|                              |
       |  (hash value)  |                              |
       |                |                              |
       |                |--- AUTHEN START ------------>|
       |                |  type=CHAP                   |
       |                |  user="alice"                |
       |                |  data= id + challenge + response
       |                |  (CHAP data bundle)          |
       |                |                              |
       |                | [Server knows password,      |
       |                |  recomputes MD5, compares]   |
       |                |                              |
       |                |<-- AUTHEN REPLY -------------|
       |                |  status=PASS or FAIL         |
```

### 8.2 ENABLE Authentication (Privilege Escalation)

A critical but often overlooked authentication flow is **enable authentication** — when a user at privilege level 1 attempts to escalate to level 15 (or any higher level) using the `enable` command.

```
Enable (Privilege Escalation) Authentication Flow:

  User (at priv 1)     NAS                       TACACS+ Server
       |                |                              |
       |---"enable"----->|                              |
       |                |                              |
       |                |--- AUTHEN START ------------>|
       |                |  action=LOGIN                |
       |                |  service=ENABLE              |
       |                |  user="alice" (current user) |
       |                |  priv_lvl=15 (requested)     |
       |                |                              |
       |                |<-- AUTHEN REPLY -------------|
       |                |  status=GETPASS              |
       |                |  msg="Password:"             |
       |                |                              |
       |<--"Password: "--|                              |
       |---[enable pw]-->|                              |
       |                |                              |
       |                |--- AUTHEN CONTINUE --------->|
       |                |                              |
       |                |<-- AUTHEN REPLY -------------|
       |                |  status=PASS                 |
       |                |                              |
       |<-- priv lvl 15-|                              |
```

### 8.3 Authentication Status Codes — Complete Reference

| Code | Value | Meaning |
|---|---|---|
| TAC_PLUS_AUTHEN_STATUS_PASS | 0x01 | Authentication succeeded |
| TAC_PLUS_AUTHEN_STATUS_FAIL | 0x02 | Authentication failed |
| TAC_PLUS_AUTHEN_STATUS_GETDATA | 0x03 | Server needs more data (custom prompt) |
| TAC_PLUS_AUTHEN_STATUS_GETUSER | 0x04 | Server requests username |
| TAC_PLUS_AUTHEN_STATUS_GETPASS | 0x05 | Server requests password |
| TAC_PLUS_AUTHEN_STATUS_RESTART | 0x06 | Restart authentication |
| TAC_PLUS_AUTHEN_STATUS_ERROR | 0x07 | Server error |
| TAC_PLUS_AUTHEN_STATUS_FOLLOW | 0x21 | Follow redirect to another server |

### 8.4 Authentication Methods (authen_type field)

| Type | Value | Description |
|---|---|---|
| TAC_PLUS_AUTHEN_TYPE_ASCII | 0x01 | Interactive ASCII |
| TAC_PLUS_AUTHEN_TYPE_PAP | 0x02 | PAP |
| TAC_PLUS_AUTHEN_TYPE_CHAP | 0x03 | CHAP |
| TAC_PLUS_AUTHEN_TYPE_ARAP | 0x04 | AppleTalk Remote Access |
| TAC_PLUS_AUTHEN_TYPE_MSCHAP | 0x05 | MS-CHAP |
| TAC_PLUS_AUTHEN_TYPE_MSCHAPV2 | 0x06 | MS-CHAPv2 |

### 8.5 Authentication Services (authen_service field)

| Service | Value | Used For |
|---|---|---|
| TAC_PLUS_AUTHEN_SVC_NONE | 0x00 | None |
| TAC_PLUS_AUTHEN_SVC_LOGIN | 0x01 | CLI login |
| TAC_PLUS_AUTHEN_SVC_ENABLE | 0x02 | Enable escalation |
| TAC_PLUS_AUTHEN_SVC_PPP | 0x03 | PPP sessions |
| TAC_PLUS_AUTHEN_SVC_ARAP | 0x04 | AppleTalk |
| TAC_PLUS_AUTHEN_SVC_PT | 0x05 | Pass-through |
| TAC_PLUS_AUTHEN_SVC_RCMD | 0x06 | Remote commands (rsh, rcp) |
| TAC_PLUS_AUTHEN_SVC_X25 | 0x07 | X.25 PAD |
| TAC_PLUS_AUTHEN_SVC_NASI | 0x08 | NASI |
| TAC_PLUS_AUTHEN_SVC_FWPROXY | 0x09 | Firewall proxy |

---

## 9. Authorization — Deep Dive

### 9.1 The Authorization Decision Process

Authorization in TACACS+ is a **policy-based decision** made by the server. The NAS sends a REQUEST describing what the user wants to do; the server evaluates it against its policy and responds.

```
Authorization Decision Flow:

  NAS                                           TACACS+ Server
   |                                                   |
   |-- AUTHOR REQUEST ----------------------------->    |
   |   user="alice"                              |     |
   |   authen_method=TACACSPLUS                  |     |
   |   priv_lvl=15                               |     |
   |   service=shell                             |     |
   |   cmd=configure                             |     |
   |   cmd-arg=terminal                          |     |
   |                                             |     |
   |                  [Policy Evaluation]        |     |
   |                  1. Find user "alice"       |     |
   |                  2. Find group "netadmin"   |     |
   |                  3. Check cmd="configure"   |     |
   |                  4. Policy: PERMIT          |     |
   |                                             |     |
   |<-- AUTHOR RESPONSE -------------------------+     |
   |   status=PASS_ADD                                 |
   |   (AV-pairs added to session)                     |
```

### 9.2 Authorization Response Status Codes

| Status | Value | Meaning |
|---|---|---|
| TAC_PLUS_AUTHOR_STATUS_PASS_ADD | 0x01 | Authorized; AV pairs added to session |
| TAC_PLUS_AUTHOR_STATUS_PASS_REPL | 0x02 | Authorized; replace client AV pairs with server's |
| TAC_PLUS_AUTHOR_STATUS_FAIL | 0x10 | Denied |
| TAC_PLUS_AUTHOR_STATUS_ERROR | 0x11 | Server error — fall back to local |
| TAC_PLUS_AUTHOR_STATUS_FOLLOW | 0x21 | Follow redirect |

**PASS_ADD vs PASS_REPL:**
- **PASS_ADD**: The server adds its AV pairs to whatever the client sent. The final effective set = client AV pairs + server additions.
- **PASS_REPL**: The server's AV pairs **replace** the client's entirely. Used when the server wants complete control.

### 9.3 Command Authorization — The Core Use Case

Command authorization is what makes TACACS+ indispensable in enterprise networks. Every command typed on a managed device can be sent to the TACACS+ server for approval before execution.

```
Command Authorization Flow:

  Network Admin       Router (NAS)                  TACACS+ Server
       |                   |                              |
       |--"show run"------->|                             |
       |                   |                              |
       |                   |--- AUTHOR REQUEST ---------->|
       |                   |  user="alice"                |
       |                   |  service=shell               |
       |                   |  cmd=show                    |
       |                   |  cmd-arg=run                 |
       |                   |                              |
       |                   |  [Policy check:              |
       |                   |   alice in group=netops      |
       |                   |   netops policy:             |
       |                   |   permit cmd=show *]         |
       |                   |                              |
       |                   |<-- AUTHOR RESPONSE ----------|
       |                   |  status=PASS_ADD             |
       |                   |                              |
       |<-- [running config]|  [command executes]         |
       |                   |                              |
       |--"reload"--------->|                             |
       |                   |                              |
       |                   |--- AUTHOR REQUEST ---------->|
       |                   |  cmd=reload                  |
       |                   |                              |
       |                   |  [Policy check:              |
       |                   |   netops policy:             |
       |                   |   deny cmd=reload]           |
       |                   |                              |
       |                   |<-- AUTHOR RESPONSE ----------|
       |                   |  status=FAIL                 |
       |                   |                              |
       |<-- "Command authorization failed"                |
```

### 9.4 EXEC Authorization (Session-Level)

Before command authorization, there is **EXEC authorization** — determining whether the user can get a shell (exec) at all, and what parameters govern their session.

```
EXEC Authorization (Shell Service):

  NAS sends:
    service=shell
    cmd=""  (empty — session-level, not command-level)

  Server responds with session parameters:
    priv-lvl=15        → grant privilege level 15
    timeout=30         → 30-minute idle timeout
    acl=101            → apply ACL 101 to this session
    autocmd=show users → auto-run "show users" on login
    noescape=true      → prevent escape to exec mode
```

### 9.5 Authorization for Network Access (PPP/SLIP/ARA)

TACACS+ isn't just for CLI management — it also authorizes **network access sessions** (dial-up era, VPN, etc.):

```
PPP Authorization AV Pairs:
  service=ppp
  protocol=ip
  addr=172.16.1.50         → Assign this IP to the user
  addr-pool=dialin-pool    → Or: assign from this pool
  inacl=100                → Inbound ACL
  outacl=101               → Outbound ACL
  route=10.0.0.0/8         → Push static route to client
  timeout=3600             → Maximum session time (seconds)
  idletime=600             → Idle timeout
```

### 9.6 Policy Models — Permit/Deny Logic

TACACS+ servers implement policies using either:

**1. First-match (Ordered) Model:**
Rules are evaluated top-to-bottom; first match wins.

```
Group: junior-admin
  permit cmd=show *
  permit cmd=ping *
  deny cmd=*            ← Explicit deny-all at bottom
```

**2. Permit-all with explicit denies:**
```
Group: senior-admin
  deny cmd=reload *
  deny cmd=write erase *
  permit cmd=*          ← Permit everything else
```

**3. Deny-all with explicit permits:**
```
Group: read-only
  permit cmd=show *
  deny cmd=*            ← Default deny
```

---

## 10. Accounting — Deep Dive

### 10.1 Accounting Record Types

Accounting records come in three types:

| Type | Value | Meaning |
|---|---|---|
| TAC_PLUS_ACCT_FLAG_START | 0x02 | Session/task has started |
| TAC_PLUS_ACCT_FLAG_STOP | 0x04 | Session/task has stopped |
| TAC_PLUS_ACCT_FLAG_WATCHDOG | 0x08 | Interim update (session still active) |

### 10.2 Accounting Flow — Session Accounting

```
Session Accounting Flow (Start/Stop):

  User                 NAS                       TACACS+ Server
   |                    |                              |
   | [auth+authz done] |                              |
   |                    |                              |
   |                    |--- ACCT REQUEST (START) ---->|
   |                    |  flags=START                 |
   |                    |  user="alice"                |
   |                    |  task_id="12345"             |
   |                    |  start_time=1746350000       |
   |                    |  service=shell               |
   |                    |  port=tty0                   |
   |                    |  rem_addr=192.168.1.50       |
   |                    |                              |
   |                    |<-- ACCT REPLY ---------------|
   |                    |  status=SUCCESS              |
   |                    |                              |
   | [user works...]    |  [session active]            |
   |                    |                              |
   | [user logs out]    |                              |
   |                    |                              |
   |                    |--- ACCT REQUEST (STOP) ----->|
   |                    |  flags=STOP                  |
   |                    |  user="alice"                |
   |                    |  task_id="12345"             |
   |                    |  stop_time=1746353600        |
   |                    |  elapsed_time=3600           |
   |                    |  bytes_in=45231              |
   |                    |  bytes_out=12847             |
   |                    |  disc-cause=User Request     |
   |                    |                              |
   |                    |<-- ACCT REPLY ---------------|
   |                    |  status=SUCCESS              |
```

### 10.3 Command Accounting

One of TACACS+'s most powerful features: **recording every command a user executes**, with timestamp.

```
Command Accounting Flow:

  Admin types:           NAS                       TACACS+ Server
  "show running-config"   |                              |
       |                  |--- ACCT REQUEST (STOP) ----->|
       |                  |  flags=STOP                  |
       |                  |  user="alice"                |
       |                  |  task_id="99887"             |
       |                  |  service=shell               |
       |                  |  cmd=show                    |
       |                  |  cmd-arg=running-config       |
       |                  |  stop_time=<timestamp>       |
       |                  |  elapsed_time=0              |
       |                  |                              |
       |                  |<-- ACCT REPLY ---------------|
       |                  |  status=SUCCESS              |

Note: Command accounting uses STOP records (no START, since commands
are instantaneous). The WATCHDOG type is for long-running tasks.
```

### 10.4 Accounting Attribute-Value Pairs (Complete Set)

```
Core Accounting AV Pairs:

  task_id          = Unique ID per accounting record
  start_time       = Unix timestamp of start
  stop_time        = Unix timestamp of stop
  elapsed_time     = Duration in seconds
  timezone         = Timezone string (e.g., "UTC+5:30")
  event            = Description of event
  reason           = Reason string
  bytes_in         = Received bytes
  bytes_out        = Transmitted bytes
  paks_in          = Received packets
  paks_out         = Transmitted packets
  status           = Final status of task
  err_msg          = Error message if any

  service          = Service type used
  protocol         = Protocol (e.g., ip, ipx)
  addr             = Address assigned/used
  cmd              = Command executed
  cmd-arg          = Command arguments
  port             = NAS port
  rem_addr         = Remote address
  priv-lvl         = Privilege level during session
  disc-cause       = Disconnect cause code
  disc-cause-ext   = Extended disconnect cause
  connect-progress = Connection progress code
  nas-rx-speed     = NAS receive speed (bps)
  nas-tx-speed     = NAS transmit speed (bps)
```

### 10.5 Accounting Reply Status Codes

| Status | Value | Meaning |
|---|---|---|
| TAC_PLUS_ACCT_STATUS_SUCCESS | 0x01 | Record accepted |
| TAC_PLUS_ACCT_STATUS_ERROR | 0x02 | Server error |
| TAC_PLUS_ACCT_STATUS_FOLLOW | 0x21 | Follow redirect |

### 10.6 What To Do When Accounting Fails

Accounting failure is a policy decision:

- **stop-only**: If accounting fails, session continues. Common in many deployments but reduces auditability.
- **stop-on-fail** (most secure): If accounting START fails, deny the session entirely. Ensures every session is recorded.

```
Cisco IOS Configuration for Accounting on Failure:
  aaa accounting send stop-record authentication failure
  aaa accounting system default start-stop group tacacs+
```

---

## 11. Session Management & State Machine

### 11.1 Complete TACACS+ Session State Machine

```
TACACS+ Full Session State Machine (CLI Login):

  +------------------+
  |   IDLE / Initial  |
  +------------------+
           |
           | User connects (SSH/Telnet/Console)
           v
  +------------------+
  |  TCP CONNECT to  |
  |  TACACS+ Server  |
  +------------------+
           |
           | TCP established
           v
  +------------------+
  |  AUTHEN START    |  ← NAS sends type, user, port info
  |  (seq=1)         |
  +------------------+
           |
           v
  +------------------+
  |  AUTHEN REPLY    |  ← Server sends GETUSER / GETPASS /
  |  (seq=2)         |    GETDATA / PASS / FAIL
  +------------------+
           |
    +------+------+
    |             |
  PASS          Need more data
    |           (GETUSER/GETPASS/GETDATA)
    |             |
    |             v
    |      +------------------+
    |      |  AUTHEN CONTINUE |  ← NAS sends user's response
    |      |  (seq=3)         |
    |      +------------------+
    |             |
    |             v
    |      +------------------+
    |      |  AUTHEN REPLY    |  ← Server evaluates again
    |      |  (seq=4)         |  → loop until PASS/FAIL
    |      +------------------+
    |             |
    |          PASS |  FAIL
    |             |      |
    |      +------+      +---> DENY ACCESS
    |      |
    +------+
           |
           v
  +------------------+
  |  AUTHOR REQUEST  |  ← NAS requests exec authorization
  |  (new session)   |    service=shell, cmd="" (EXEC)
  +------------------+
           |
           v
  +------------------+
  |  AUTHOR RESPONSE |  ← Server: PASS_ADD + priv-lvl, timeout
  +------------------+
           |
    PASS_ADD/REPL | FAIL
           |          |
           v          +---> DENY EXEC
  +------------------+
  |  ACCT REQUEST    |  ← NAS sends START record
  |  (START)         |
  +------------------+
           |
           v
  +------------------+
  |  Session ACTIVE  |  ← User is in CLI
  +------------------+
           |
           | User types command
           v
  +------------------+
  |  AUTHOR REQUEST  |  ← Per-command authorization
  |  cmd=<command>   |
  +------------------+
           |
   PASS | FAIL
     |       |
     v       +---> "Command authorization failed"
  Execute
  command
     |
     v
  +------------------+
  |  ACCT REQUEST    |  ← Command accounting STOP record
  |  (cmd, STOP)     |
  +------------------+
           |
           | [repeat for each command]
           |
           | User logs out
           v
  +------------------+
  |  ACCT REQUEST    |  ← Session accounting STOP record
  |  (session, STOP) |
  +------------------+
           |
           v
  +------------------+
  |  TCP CLOSE       |  (or reuse for next session)
  +------------------+
           |
           v
        DONE
```

### 11.2 Failure Handling in the State Machine

```
Failure Scenarios and Handling:

  Scenario 1: TACACS+ Server Unreachable
  ----------------------------------------
  NAS tries primary server → TCP timeout
  NAS tries secondary server → TCP timeout
  NAS falls back to:
    - Local authentication (if configured: "aaa authentication login default group tacacs+ local")
    - Or denies access entirely (if no fallback configured)

  Scenario 2: Authentication FAIL response
  -----------------------------------------
  Server responds FAIL → NAS denies login
  Depending on config: may try next method in method list

  Scenario 3: Authorization FAIL for EXEC
  ----------------------------------------
  After successful auth, server denies exec authorization
  NAS closes the session — user sees "Authorization failed"

  Scenario 4: Authorization FAIL for Command
  -------------------------------------------
  User is already logged in
  Specific command is denied
  NAS prints: "Command authorization failed."
  Session continues — user can try other commands

  Scenario 5: Accounting Server Error
  -------------------------------------
  Depends on config:
  - If accounting is non-blocking: session continues
  - If stop-on-fail: session may be terminated
```

---

## 12. TACACS+ vs RADIUS — Full Comparison

Understanding this comparison is critical for designing AAA infrastructure and for interviews/certifications.

### 12.1 Fundamental Differences

| Dimension | TACACS+ | RADIUS |
|---|---|---|
| **Transport** | TCP/49 | UDP/1812 (auth), UDP/1813 (acct) |
| **Reliability** | TCP guarantees delivery | UDP — no reliability, NAS must retry |
| **Encryption** | Full body encrypted | Only password encrypted (in auth); rest cleartext |
| **AAA Separation** | Complete (independent exchanges) | Bundled (auth+authz in same exchange) |
| **Multiprotocol** | Yes (IP, IPX, AppleTalk, X.25, etc.) | Primarily IP |
| **Command Authorization** | Native, granular, per-command | Not natively supported |
| **Accounting Detail** | Very detailed, per-command | Session-level, less granular |
| **Standard** | RFC 8907 (2020) | RFC 2865/2866 (2000) |
| **Vendor** | Originally Cisco; now open | Originally Livingston/Merit; now open |
| **Scalability** | Excellent (TCP, single-connect) | Good (UDP, stateless) |
| **Router/Switch mgmt** | Primary choice | Not ideal |
| **Network access (WiFi/VPN)** | Can be used | Primary choice |
| **802.1X support** | No native support | Yes (via EAP) |

### 12.2 Encryption Scope Comparison

```
RADIUS Encryption Scope:
+-------------------------------------------------+
| RADIUS Packet                                   |
|                                                 |
| Code | ID | Length | Authenticator |            |
|      (CLEARTEXT header)                         |
|                                                 |
| Attributes:                                     |
|   NAS-IP-Address: 10.0.0.1      [CLEARTEXT]    |
|   User-Name: alice               [CLEARTEXT]    |  <-- username visible!
|   User-Password: ******          [ENCRYPTED]    |  <-- only this encrypted
|   NAS-Port: 5                    [CLEARTEXT]    |
|   Called-Station-Id: ...         [CLEARTEXT]    |
+-------------------------------------------------+

TACACS+ Encryption Scope:
+-------------------------------------------------+
| TACACS+ Packet                                  |
|                                                 |
| Header (12 bytes):              [CLEARTEXT]     |
|   version | type | seq | flags                  |
|   session_id | length                           |
|                                                 |
| Body (everything below):        [ENCRYPTED]     |
|   ==========================================    |
|   | username | password | AV pairs | commands | |
|   | remote address | port | all data          | |
|   ==========================================    |
+-------------------------------------------------+
```

### 12.3 AAA Separation Comparison

```
RADIUS — Auth+Authz Bundled:

  NAS                              RADIUS Server
   |                                    |
   |-- Access-Request (auth) ---------->|
   |   Username + Password              |
   |                                    |
   |<-- Access-Accept (auth+authz) -----|
   |   + Attributes (authz embedded)    |
   |                                    |
   [Auth and Authz happen in one step]

TACACS+ — Auth and Authz Separate:

  NAS                              TACACS+ Server
   |                                    |
   |-- AUTHEN START ------------------->|  Step 1: Auth only
   |<-- AUTHEN REPLY (PASS) ------------|
   |                                    |
   |-- AUTHOR REQUEST ----------------->|  Step 2: Authz only
   |<-- AUTHOR RESPONSE (PASS_ADD) -----|
   |                                    |
   [Auth and Authz are independent — can use different servers]
```

### 12.4 When to Choose Each

**Choose TACACS+ when:**
- Managing **network infrastructure devices** (routers, switches, firewalls).
- You need **per-command authorization and accounting**.
- Your environment is **Cisco-heavy**.
- You need **detailed audit trails** for compliance (SOX, PCI-DSS, HIPAA).
- Security policy requires knowing exactly what commands each admin ran.

**Choose RADIUS when:**
- Authenticating **end-user network access** (WiFi, VPN, dial-up).
- Implementing **802.1X port-based authentication**.
- Working with **non-Cisco** vendors with strong RADIUS support.
- Integrating with **cloud** or **SaaS** AAA platforms.
- You need **EAP** (e.g., EAP-TLS, PEAP) for certificate-based auth.

**Use both when:**
- TACACS+ for network device management.
- RADIUS for endpoint/user network access.
- This is the most common enterprise pattern.

---

## 13. Network Device Access Control Flows

### 13.1 Console Access Flow

```
Console Access (Out-of-Band Physical Access):

  Engineer           Console Port         NAS (Device)          TACACS+ Server
     |                    |                    |                       |
     |---[physical cable]-->|                  |                       |
     |                    |---[login trigger]-->|                       |
     |                    |                    |-- AUTHEN START ------->|
     |                    |                    |   port=con0            |
     |                    |                    |   rem_addr=           |
     |<-- "Username: " ---|                    |<-- AUTHEN REPLY GETUSER|
     |---"admin"---------->|                   |-- AUTHEN CONTINUE ---->|
     |<-- "Password: " ---|                    |<-- AUTHEN REPLY GETPASS|
     |---"password"------->|                   |-- AUTHEN CONTINUE ---->|
     |                    |                    |<-- AUTHEN REPLY PASS --|
     |                    |                    |                        |
     |                    |                    |-- AUTHOR REQUEST ------>|
     |                    |                    |   service=shell, cmd="" |
     |                    |                    |<-- AUTHOR RESPONSE -----|
     |                    |                    |   PASS_ADD, priv-lvl=15|
     |                    |                    |                        |
     |                    |                    |-- ACCT START ---------->|
     |<-- Router prompt ---|                   |<-- ACCT SUCCESS --------|
```

### 13.2 SSH Remote Access Flow

```
SSH Remote Management Access:

  Remote Admin      SSH Client          NAS (Switch)          TACACS+ Server
       |                |                    |                       |
       |--SSH request-->|                    |                       |
       |                |---[TCP/22 SYN]---->|                       |
       |                |<--[TCP/22 SYN-ACK]-|                       |
       |                |---[SSH Handshake]->|                       |
       |                |<--[SSH Keys]--------|                      |
       |                |   [SSH session established]                |
       |                |                    |                       |
       |                |                    |--[TCP/49 to TACACS+]->|
       |                |                    |-- AUTHEN START ------->|
       |                |                    |   type=ASCII           |
       |                |                    |   port=vty0            |
       |                |                    |   rem_addr=203.0.113.5 |
       |                |<-- "Username:" ----|<-- AUTHEN GETUSER -----|
       |<-- "Username:" -|                   |                        |
       |--"netadmin"--->|                    |                        |
       |                |---"netadmin"------->|-- AUTHEN CONTINUE ---->|
       |                |                    |<-- AUTHEN GETPASS -----|
       |<-- "Password:" -|                   |                        |
       |--"pass"-------->|                   |                        |
       |                |---"pass"----------->|-- AUTHEN CONTINUE ---->|
       |                |                    |<-- AUTHEN PASS ---------|
       |                |                    |                        |
       |                |                    |-- AUTHOR REQUEST ------>|
       |                |                    |   service=shell        |
       |                |                    |<-- AUTHOR PASS_ADD ----|
       |                |                    |   priv-lvl=15          |
       |                |                    |                        |
       |                |                    |-- ACCT START ---------->|
       |<-- CLI prompt --|                   |                        |
       |                |                    |                        |
       | "show ip bgp"  |                    |                        |
       |--------------->|                    |                        |
       |                |---"show ip bgp"--->|                        |
       |                |                    |-- AUTHOR REQUEST ------>|
       |                |                    |   cmd=show             |
       |                |                    |   cmd-arg=ip           |
       |                |                    |   cmd-arg=bgp          |
       |                |                    |<-- AUTHOR PASS_ADD ----|
       |                |                    |                        |
       |                |                    |-- ACCT STOP (cmd) ----->|
       |<-- BGP output --|                   |                        |
```

### 13.3 Privilege Escalation (Enable) Flow

```
Privilege Escalation Flow (1 → 15):

  Admin (at priv 1)    NAS                         TACACS+ Server
       |                |                                |
       |--"enable 15"-->|                                |
       |                |                                |
       |                |--- AUTHEN START -------------->|
       |                |   action=LOGIN                 |
       |                |   service=ENABLE               |
       |                |   user="netadmin"              |
       |                |   priv_lvl=15                  |
       |                |                                |
       |                |<-- AUTHEN REPLY (GETPASS) -----|
       |                |   msg="Password:"              |
       |                |                                |
       |<-- "Password:" -|                               |
       |--[enable pass]->|                               |
       |                |                                |
       |                |--- AUTHEN CONTINUE ----------->|
       |                |   user_msg="<enable password>" |
       |                |                                |
       |                |<-- AUTHEN REPLY (PASS) --------|
       |                |                                |
       |                |--- AUTHOR REQUEST ------------>|
       |                |   service=shell                |
       |                |   priv_lvl=15                  |
       |                |                                |
       |                |<-- AUTHOR RESPONSE (PASS_ADD) -|
       |                |   priv-lvl=15                  |
       |                |                                |
       |<-- "#" prompt --|                               |
       |  (enabled mode) |                               |
```

---

## 14. Server Implementations

### 14.1 Cisco ISE (Identity Services Engine)

The enterprise-grade Cisco AAA solution. ISE is the most feature-rich TACACS+ server available but also the most complex:

- Full TACACS+ support including command authorization.
- Integration with **Active Directory**, **LDAP**, **RSA SecurID**.
- **RBAC** (Role-Based Access Control) with granular command sets.
- **Device Administration** license specifically for TACACS+ features.
- REST API for programmability.
- Built-in reporting and dashboards.
- Supports both RADIUS and TACACS+ simultaneously.
- **Note**: TACACS+ in ISE requires the **Device Administration** license (separate from Network Access licenses).

### 14.2 Cisco ACS (Access Control Server) — Legacy

Cisco's original TACACS+ server, now **End-of-Life (EoL)**. ISE replaced it. If you see ACS 5.x in production, migration to ISE should be planned.

### 14.3 FreeRADIUS with TACACS+ Plugin

FreeRADIUS is primarily a RADIUS server, but community plugins exist for TACACS+ support. Not recommended for enterprise production use.

### 14.4 tac_plus (Shrubbery Networks)

The original open-source TACACS+ daemon. Still widely used:
- Simple flat-file configuration.
- Available on Linux/Unix.
- No native GUI — config file based.
- Excellent for small/medium deployments.
- Source: http://www.shrubbery.net/tac_plus/

**Basic tac_plus configuration:**
```
key = MySharedSecret123!@#

group = netadmin {
    default service = permit
    service = exec {
        priv-lvl = 15
    }
}

group = readonly {
    cmd = show { permit .* }
    cmd = exit { permit .* }
    cmd = logout { permit .* }
    cmd = quit { permit .* }
    default cmd = deny
    service = exec {
        priv-lvl = 1
    }
}

user = alice {
    member = netadmin
    login = cleartext "AlicePassword123"
}

user = bob {
    member = readonly
    login = cleartext "BobPassword456"
}
```

### 14.5 TACACS.net / PacketFence

PacketFence is an open-source NAC solution that includes TACACS+ server functionality:
- Web-based management interface.
- LDAP/AD integration.
- Suitable for small to medium enterprises.

### 14.6 Aruba ClearPass

Aruba's AAA platform supports both RADIUS and TACACS+:
- Common in Aruba/HPE networks.
- Full command authorization support.
- Policy-based access control.

### 14.7 FortiAuthenticator

Fortinet's AAA server supporting TACACS+:
- Integrates with FortiGate firewalls natively.
- LDAP/AD integration.
- MFA support.

### 14.8 Open-Source Alternatives

| Solution | Type | Notes |
|---|---|---|
| tac_plus (Shrubbery) | Standalone daemon | Classic, simple, reliable |
| tac_plus-ng | Modernized tac_plus | Actively maintained fork |
| RANCID + tac_plus | Config management + AAA | Common open-source stack |
| TACACS+ on Ubuntu | DIY | tac_plus packaged in apt |

---

## 15. Client-Side Configuration

### 15.1 Cisco IOS — Complete Configuration

This is the most common TACACS+ client platform. Understanding IOS TACACS+ config is essential.

#### Step 1: Enable AAA

```
! ALWAYS enable AAA globally first
aaa new-model
```

#### Step 2: Define TACACS+ Server(s)

**Legacy syntax (still works):**
```
tacacs-server host 10.0.0.10 key 7 <encrypted-key>
tacacs-server host 10.0.0.11 key 7 <encrypted-key>  ! secondary
tacacs-server timeout 5
tacacs-server directed-request
```

**Modern syntax (IOS 12.4(2)T+, preferred):**
```
! Define a named server group
aaa group server tacacs+ TACACS-SERVERS
 server-private 10.0.0.10 key MySharedSecret123
 server-private 10.0.0.11 key MySharedSecret123
 ip tacacs source-interface Loopback0
```

#### Step 3: Configure Authentication

```
! Login authentication: try TACACS+, fall back to local
aaa authentication login default group TACACS-SERVERS local

! For console — optionally different policy
aaa authentication login CONSOLE-AUTH local

! For enable authentication
aaa authentication enable default group TACACS-SERVERS enable

! Apply CONSOLE-AUTH to console line
line con 0
 login authentication CONSOLE-AUTH

! VTY lines use default (TACACS+)
line vty 0 15
 login authentication default
 transport input ssh
```

#### Step 4: Configure Authorization

```
! EXEC (shell) authorization
aaa authorization exec default group TACACS-SERVERS local

! Command authorization for all privilege levels
aaa authorization commands 0 default group TACACS-SERVERS local
aaa authorization commands 1 default group TACACS-SERVERS local
aaa authorization commands 15 default group TACACS-SERVERS local

! Network (PPP, etc.) authorization
aaa authorization network default group TACACS-SERVERS

! Configuration mode authorization
aaa authorization config-commands
```

#### Step 5: Configure Accounting

```
! EXEC session accounting
aaa accounting exec default start-stop group TACACS-SERVERS

! Command accounting for all privilege levels
aaa accounting commands 0 default start-stop group TACACS-SERVERS
aaa accounting commands 1 default start-stop group TACACS-SERVERS
aaa accounting commands 15 default start-stop group TACACS-SERVERS

! Network accounting
aaa accounting network default start-stop group TACACS-SERVERS

! System accounting (reloads, config changes to AAA)
aaa accounting system default start-stop group TACACS-SERVERS

! Send accounting records even on auth failure
aaa accounting send stop-record authentication failure
```

#### Full IOS Configuration — Production Template

```
! ==========================================
! TACACS+ AAA Full Production Configuration
! ==========================================

! Enable AAA
aaa new-model

! TACACS+ server group
aaa group server tacacs+ CORP-TACACS
 server-private 10.0.0.10 port 49 key 0 V3ryStr0ngSh4r3dS3cr3t!
 server-private 10.0.0.11 port 49 key 0 V3ryStr0ngSh4r3dS3cr3t!
 ip tacacs source-interface Loopback0

! Authentication policies
aaa authentication login default group CORP-TACACS local
aaa authentication login CONSOLE local
aaa authentication enable default group CORP-TACACS enable

! Authorization policies
aaa authorization exec default group CORP-TACACS local if-authenticated
aaa authorization commands 0 default group CORP-TACACS local if-authenticated
aaa authorization commands 1 default group CORP-TACACS local if-authenticated
aaa authorization commands 15 default group CORP-TACACS local if-authenticated
aaa authorization config-commands

! Accounting policies
aaa accounting exec default start-stop group CORP-TACACS
aaa accounting commands 0 default start-stop group CORP-TACACS
aaa accounting commands 1 default start-stop group CORP-TACACS
aaa accounting commands 15 default start-stop group CORP-TACACS
aaa accounting system default start-stop group CORP-TACACS
aaa accounting send stop-record authentication failure

! Line configurations
line con 0
 login authentication CONSOLE
 exec-timeout 10 0
 privilege level 15       ! Console gets full access locally

line vty 0 4
 login authentication default
 authorization exec default
 accounting exec default
 exec-timeout 15 0
 transport input ssh
 access-class 10 in       ! ACL restricting SSH source IPs

line vty 5 15
 login authentication default
 exec-timeout 15 0
 transport input ssh

! Local fallback user (in case TACACS+ is unreachable)
username admin privilege 15 secret 5 $1$abcd$...

! Source interface for TACACS+ connections
ip tacacs source-interface Loopback0

! Disable telnet (use SSH only)
ip ssh version 2
```

### 15.2 Cisco IOS-XE

IOS-XE uses the same AAA commands as IOS but with some additions:

```
! IOS-XE specific: TACACS+ with named server config
tacacs server TACACS-PRIMARY
 address ipv4 10.0.0.10
 port 49
 key 7 <encrypted-key>
 timeout 5
 single-connection           ! Use persistent TCP connection

tacacs server TACACS-SECONDARY
 address ipv4 10.0.0.11
 port 49
 key 7 <encrypted-key>
 timeout 5
 single-connection

aaa group server tacacs+ CORP-TACACS
 server name TACACS-PRIMARY
 server name TACACS-SECONDARY
 ip tacacs source-interface Loopback0
```

### 15.3 Cisco NX-OS (Nexus)

```
! NX-OS TACACS+ Configuration

feature tacacs+

tacacs-server key 7 <encrypted>

tacacs-server host 10.0.0.10
  key 7 <encrypted>
  port 49
  timeout 5

tacacs-server host 10.0.0.11
  key 7 <encrypted>

aaa group server tacacs+ CORP-TACACS
  server 10.0.0.10
  server 10.0.0.11
  source-interface mgmt0
  use-vrf management

aaa authentication login default group CORP-TACACS local
aaa authentication login console local
aaa authorization exec default group CORP-TACACS local
aaa authorization commands default group CORP-TACACS local
aaa accounting default group CORP-TACACS
```

### 15.4 Cisco IOS-XR

```
! IOS-XR TACACS+ Configuration (different syntax!)

tacacs-server host 10.0.0.10 port 49
 key MySharedSecret
 timeout 10
 single-connect

tacacs-server host 10.0.0.11 port 49
 key MySharedSecret

aaa group server tacacs CORP-TACACS
 server 10.0.0.10
 server 10.0.0.11
 source-interface MgmtEth0/0/CPU0/0
 vrf Mgmt-intf

aaa authentication login default group CORP-TACACS local
aaa authorization exec default group CORP-TACACS local
aaa authorization commands default group CORP-TACACS local
aaa accounting exec default start-stop group CORP-TACACS
aaa accounting commands default start-stop group CORP-TACACS
```

### 15.5 Juniper JunOS

```
# JunOS TACACS+ Configuration
set system authentication-order [tacplus password]

set system tacplus-server 10.0.0.10 secret MySharedSecret
set system tacplus-server 10.0.0.10 port 49
set system tacplus-server 10.0.0.10 timeout 5
set system tacplus-server 10.0.0.10 source-address 10.0.0.1

set system tacplus-server 10.0.0.11 secret MySharedSecret

set system login user remote full-name "Remote TACACS Users"
set system login user remote class super-user
```

### 15.6 Arista EOS

```
# Arista EOS TACACS+ Configuration
tacacs-server host 10.0.0.10 key MySharedSecret
tacacs-server host 10.0.0.11 key MySharedSecret
tacacs-server timeout 5

aaa group server tacacs+ CORP-TACACS
   server 10.0.0.10
   server 10.0.0.11

aaa authentication login default group CORP-TACACS local
aaa authorization exec default group CORP-TACACS local
aaa authorization commands all default group CORP-TACACS local
aaa accounting exec default start-stop group CORP-TACACS
aaa accounting commands all default start-stop group CORP-TACACS
```

### 15.7 Method Lists — Advanced Configuration

Method lists allow different authentication policies for different use cases:

```
! Method list syntax:
! aaa authentication login <list-name> <method1> [method2] [method3]

! Methods:
!   group <server-group>  — TACACS+ server group
!   local                 — Local user database
!   enable                — Enable password
!   line                  — Line password
!   none                  — No authentication (NEVER use in production)
!   if-authenticated      — Pass if already authenticated

! Examples:

! VTY: TACACS+, then local
aaa authentication login VTY-AUTH group CORP-TACACS local

! Console: local only (in case of network failure)
aaa authentication login CON-AUTH local

! Enable: TACACS+ enable password, then local enable
aaa authentication enable ENABLE-AUTH group CORP-TACACS enable

! Apply named lists to lines
line con 0
 login authentication CON-AUTH

line vty 0 15
 login authentication VTY-AUTH
```

---

## 16. High Availability, Redundancy & Load Balancing

### 16.1 Server Redundancy Models

```
TACACS+ High Availability Architectures:

Model 1: Active/Standby (Most Common)
======================================

  Network Devices
        |
        | Primary (always first)
        v
  +------------------+
  |  TACACS+ Primary |  <-- All requests go here normally
  |  (10.0.0.10)     |
  +------------------+
        |
        | If primary fails (TCP timeout after 'timeout' seconds)
        v
  +------------------+
  |  TACACS+ Standby |  <-- Fallback, only used on primary failure
  |  (10.0.0.11)     |
  +------------------+

  Pros: Simple, predictable
  Cons: Standby is unused resource; failover has latency

Model 2: Geographic Redundancy
================================

  Site A Devices --------> Primary TACACS (DC-A)
                   ------> Secondary TACACS (DC-B)  [WAN failover]

  Site B Devices --------> Primary TACACS (DC-B)
                   ------> Secondary TACACS (DC-A)  [WAN failover]

  "Home" server is geographically closest.
  Remote is failover across WAN.

Model 3: Load Balancing (Less Common for TACACS+)
===================================================

  Network Devices
        |
        v
  +------------------+
  |   Load Balancer  |   Layer 4 TCP load balancing
  |   (VIP: 10.0.0.9)|
  +------------------+
       / | \
      /  |  \
     v   v   v
  TAC1 TAC2 TAC3     All three handle requests

  Issue: Session state — LB must use persistence per session_id
  TACACS+ TCP sessions must be kept to same server for duration

Model 4: DNS-Based Redundancy
================================

  NAS configured with hostname, not IP
  DNS returns multiple A records
  NAS tries first, fails over to next

  Pros: Easy server swaps
  Cons: DNS caching, TTL issues, complexity
```

### 16.2 Failover Timing

```
Failover Timeline:

NAS tries primary TACACS+ server:
  |
  |-- TCP SYN sent to 10.0.0.10
  |
  | [Wait for TCP response]
  |
  | If no response in <timeout> seconds (default: 5):
  |
  |-- TCP SYN sent to 10.0.0.11 (secondary)
  |
  | If secondary responds:
  |-- AAA transaction continues on secondary
  |
  | If secondary also fails:
  |-- Next method in AAA method list (e.g., local)
```

**Tuning timeout values:**

```
! Lower timeout = faster failover, but more false failures on slow networks
tacacs-server timeout 3      ! 3 seconds (aggressive)

! Higher timeout = more tolerant of latency, slower failover
tacacs-server timeout 10     ! 10 seconds (conservative)

! Per-server timeout override:
aaa group server tacacs+ CORP-TACACS
 server-private 10.0.0.10 timeout 3
 server-private 10.0.0.11 timeout 5
```

### 16.3 Single-Connection Mode and Its Impact on HA

```
! Single-connection mode keeps one persistent TCP connection
! This is important for HA behavior:

Without single-connection:
  Each AAA transaction = new TCP connection = faster detection of failure
  But: higher overhead, more TCP handshakes

With single-connection:
  Persistent TCP connection
  If connection breaks, must detect TCP keepalive failure first
  Then reconnect to primary or failover to secondary

! Enable single-connection:
tacacs server PRIMARY
 single-connection

! Or in legacy syntax:
tacacs-server single-connection
```

### 16.4 TACACS+ Server Clustering

Enterprise deployments use clustered TACACS+ servers with shared database backend:

```
TACACS+ Server Cluster Architecture:

  +==================================================================+
  |                     TACACS+ Server Farm                          |
  |                                                                  |
  |  +---------------+   +---------------+   +---------------+      |
  |  | TACACS Node 1 |   | TACACS Node 2 |   | TACACS Node 3 |      |
  |  | 10.0.0.10     |   | 10.0.0.11     |   | 10.0.0.12     |      |
  |  +-------+-------+   +-------+-------+   +-------+-------+      |
  |          |                   |                   |               |
  |          +-------------------+-------------------+               |
  |                              |                                   |
  |                     +--------+--------+                          |
  |                     |  Shared Backend |                          |
  |                     |  - User DB      |                          |
  |                     |  - Policy DB    |                          |
  |                     |  - Acct DB      |                          |
  |                     | (LDAP/AD/SQL)   |                          |
  |                     +-----------------+                          |
  +==================================================================+
```

---

## 17. Security Hardening & Best Practices

### 17.1 Shared Secret Management

The shared secret is the single most critical security element in TACACS+. Treat it like a private key.

```
Good shared secret:
  Length: 32+ characters
  Character set: Uppercase, lowercase, digits, symbols
  Randomness: Cryptographically random (not dictionary words)
  Example: "kR9#mPqL@2vF$nXw7hJ&tCsY4bGe!dA"

Bad shared secret:
  "cisco"         ← vendor default
  "cisco123"      ← trivial extension of default
  "tacacs"        ← obvious
  "company2024"   ← guessable pattern
  "1234567890"    ← trivially weak
```

**Secret rotation process:**
1. Update TACACS+ server with new secret for client X.
2. Update client X's configuration.
3. Test connectivity.
4. Move to next client.
5. Never do all clients at once — staggered rotation.

### 17.2 Network Segmentation

```
Management Network Architecture (Best Practice):

  +==============================================+
  |       Out-of-Band Management Network         |
  |       (10.0.0.0/24 — MGT VLAN)              |
  |                                              |
  |   TACACS+ Server (10.0.0.10)                |
  |   SYSLOG Server (10.0.0.20)                 |
  |   NTP Server (10.0.0.30)                    |
  |   Jump Host (10.0.0.50)                     |
  |                                              |
  |   All network devices: Mgmt interface only  |
  |   connects to this network.                  |
  |                                              |
  |   TACACS+ traffic NEVER crosses the         |
  |   production data network.                   |
  +==============================================+
           |
           | ACL: Only allow TCP/49 FROM device mgmt IPs
           |      TO TACACS+ server IP
           | ACL: Block all other traffic into mgmt network
           |
  +==============================================+
  |              Production Network              |
  |         (No TACACS+ traffic here)            |
  +==============================================+
```

### 17.3 ACL Protection on Network Devices

```
! Restrict who can access TACACS+ port on NAS
! (Redundant since TACACS+ is server-initiated from NAS perspective)

! More importantly: restrict management access to NAS
ip access-list standard MGMT-ACCESS
 permit 10.0.0.50    ! Jump host
 permit 10.0.0.0 0.0.0.255  ! Management subnet
 deny any log

line vty 0 15
 access-class MGMT-ACCESS in

! Also protect source IP of TACACS+ packets
ip access-list extended TACACS-SERVER
 permit tcp 10.0.0.10 host 10.0.0.10 eq 49 host 10.0.0.1
 deny tcp any any eq 49 log
 permit ip any any
```

### 17.4 TACACS+ Server Hardening

```
Server-Side Security Checklist:
================================
[ ] OS hardened (minimal packages, all patches applied)
[ ] TACACS+ daemon runs as non-root user
[ ] TACACS+ server itself behind firewall
[ ] Firewall: only allow TCP/49 FROM authorized NAS IPs
[ ] Separate shared secret per NAS client device
[ ] All secrets minimum 32 characters
[ ] TACACS+ logs to separate SIEM/syslog server
[ ] Regular backup of user/policy database
[ ] MFA for access to TACACS+ server management console
[ ] SNMP/monitoring for TACACS+ server availability
[ ] Regular rotation of shared secrets (quarterly minimum)
[ ] Audit log review process defined
```

### 17.5 Local Fallback User — Critical Design Decision

A common debate: should there be a local fallback user?

```
Scenario: TACACS+ servers are unreachable (network failure, maintenance)
Without local fallback: NO ONE can log into network devices
With local fallback: Emergency access preserved

Best Practice — Emergency Local User:
=======================================

! Configure a local break-glass user
username emergency-admin privilege 15 secret 0 <very-strong-password>

! Store this password in a physical safe / password vault
! Change it on every use
! Audit every use of this account

! AAA method list with local fallback ONLY on console:
aaa authentication login CONSOLE local          ! Console: local only
aaa authentication login VTY-ACCESS group CORP-TACACS  ! VTY: TACACS only (no fallback)

! This means: only physical console access is possible if TACACS+ is down
! Remote access remains protected

! Common mistake: "local" as fallback on VTY lines
! This creates a backdoor if TACACS+ fails but network is still up
! Someone could exploit the timing to use weaker local credentials
```

### 17.6 Transport Security — TACACS+ over TLS

```
! TACACS+ over TLS (RFC 9105) — Modern Secure Transport

! On the server side (ISE example):
! Configure TLS certificate on ISE TACACS+ listener
! Enable TLS in device administration settings

! On the client (IOS-XE, if supported):
tacacs server SECURE-TACACS
 address ipv4 10.0.0.10
 port 49
 key 0 MySecret
 tls                    ! Enable TLS transport
 tls-trustpoint CORP-CA ! CA certificate for server verification
```

### 17.7 Privilege Level Security Model

```
Cisco Privilege Level Reference:
==================================

Privilege Level 0:  Extremely limited (disable, enable, exit, help, logout only)
Privilege Level 1:  User EXEC — basic show commands (show version, show ip int brief, etc.)
Privilege Levels 2-14: Custom — assignable to specific commands
Privilege Level 15: Privileged EXEC — full access (equivalent to root)

Best Practice Privilege Architecture:

  Level 1  (Helpdesk/Monitoring):
    permit: show interface, show ip route, show log, show version, ping

  Level 7  (NOC Operators):
    permit: all Level 1 commands
    permit: debug (limited), clear counters, interface shutdown/no shutdown

  Level 15 (Network Engineers/Admins):
    permit: all commands
    deny: reload (only change-control approved)
    deny: write erase (only with manager approval)

! Assign commands to privilege levels on the NAS:
privilege exec level 7 debug ip ospf
privilege exec level 7 clear counters
privilege exec level 7 show running-config  ! Move from 15 to 7 if desired
```

---

## 18. Privilege Levels & Command Authorization

### 18.1 The Two Models of Privilege Control

There are two distinct approaches to privilege/command control in TACACS+ environments:

**Model 1: NAS-side Privilege Levels + TACACS+ Priv Assignment**
The NAS controls what commands are available at each privilege level. TACACS+ server just assigns which privilege level a user gets.

```
Server sends:  priv-lvl=15   → User gets full access
Server sends:  priv-lvl=7    → User gets custom limited access
Server sends:  priv-lvl=1    → User gets basic access

Pros: Simple, performant (no per-command AAA transactions)
Cons: Coarse-grained, same for all devices
```

**Model 2: TACACS+ Command Authorization (Granular)**
Every command is authorized by the TACACS+ server. The server has full visibility and control.

```
User types command → NAS asks server → Server permits/denies

Pros: Very fine-grained, centralized policy, full audit
Cons: Higher load on TACACS+ server, adds latency per command
```

**Best Practice**: Use both — assign priv-level 15 (or appropriate) via EXEC authorization, AND enable command authorization to control specific high-risk commands.

### 18.2 Command Authorization Policy Design

```
Policy Design Framework:
=========================

Identify command categories:

  SAFE (Read-Only):
    show *, ping *, traceroute *, exit, logout, terminal *

  MEDIUM RISK (Operational):
    interface * shutdown, no shutdown
    clear counters
    clear interface
    debug * (with care)
    ip route (static routes)

  HIGH RISK (Configuration):
    configure terminal
    router * (routing protocols)
    no router *
    ip access-list
    crypto *
    ntp server *
    tacacs-server * ← THIS ONE ESPECIALLY

  CRITICAL (Destructive):
    reload
    write erase
    no aaa *
    no ip ssh *
    erase nvram

Policy by role:

  Read-Only:    SAFE commands only
  Operations:   SAFE + MEDIUM RISK
  Engineering:  SAFE + MEDIUM + HIGH (except CRITICAL)
  Admin:        ALL including CRITICAL (with approval process)
```

### 18.3 tac_plus Command Authorization Config Example

```
# Complete tac_plus policy example

key = S3cur3SharedK3y!@#$

# ===========================
# Group Definitions
# ===========================

group = read-only {
    default service = deny
    
    cmd = show { permit .* }
    cmd = ping { permit .* }
    cmd = traceroute { permit .* }
    cmd = exit { permit .* }
    cmd = logout { permit .* }
    cmd = quit { permit .* }
    cmd = terminal { permit length.* }
    
    service = exec {
        priv-lvl = 1
    }
}

group = noc-operator {
    default service = deny
    
    # Inherit read-only commands
    cmd = show { permit .* }
    cmd = ping { permit .* }
    cmd = traceroute { permit .* }
    cmd = exit { permit .* }
    cmd = logout { permit .* }
    
    # Operational commands
    cmd = clear { permit counters.* }
    cmd = clear { permit interface.* }
    cmd = debug { permit ip ospf.* }
    cmd = debug { permit ip bgp.* }
    cmd = undebug { permit .* }
    cmd = interface {
        permit .*
    }
    
    service = exec {
        priv-lvl = 7
    }
}

group = net-engineer {
    default service = permit     # Permit-all, then deny dangerous
    
    cmd = reload { deny .* }
    cmd = write  { deny erase.* }
    cmd = erase  { deny nvram.* }
    
    service = exec {
        priv-lvl = 15
        timeout = 60
    }
}

group = net-admin {
    default service = permit     # Full access, no restrictions
    
    service = exec {
        priv-lvl = 15
    }
}

# ===========================
# User Definitions
# ===========================

user = alice {
    member = net-admin
    login = cleartext "Alice$Strong!Pass"
    enable = cleartext "Alice$Enable!Pass"
}

user = bob {
    member = net-engineer
    login = des "$1$xyz$encryptedpassword"
}

user = charlie {
    member = noc-operator
    login = cleartext "CharlieNOCpass!"
}

user = diana {
    member = read-only
    login = cleartext "DianaROpass!"
}

# Device-specific overrides:
user = alice {
    member = net-admin
    # Alice gets different priv on firewall-01
    host = fw-01 {
        member = read-only    # Even Alice is read-only on firewall
    }
}
```

### 18.4 ISE Command Authorization Sets

In Cisco ISE, command authorization is configured through **Command Sets**:

```
ISE Command Set: NOC-Operators
  +-- Permit: show .*
  +-- Permit: ping .*
  +-- Permit: clear counters .*
  +-- Deny:   configure .*
  +-- Deny:   reload .*
  +-- Default: Deny

ISE Command Set: Network-Engineers
  +-- Deny: reload .*
  +-- Deny: write erase .*
  +-- Default: Permit

ISE Shell Profile: exec-priv15
  +-- Default Privilege: 15
  +-- Maximum Privilege: 15
  +-- Idle Time: 30 minutes

ISE Policy:
  IF device-type = Router AND user-group = NOC-Operators
  THEN Shell-Profile=exec-priv15, Command-Set=NOC-Operators

  IF device-type = Any AND user-group = Network-Engineers
  THEN Shell-Profile=exec-priv15, Command-Set=Network-Engineers
```

---

## 19. TACACS+ in Modern Environments

### 19.1 Integration with Active Directory / LDAP

Most enterprises don't store network admin credentials directly in the TACACS+ server. Instead:

```
AD/LDAP Integration Architecture:

  NAS                TACACS+ Server              Active Directory
   |                       |                           |
   |--- AUTHEN START ------>|                           |
   |                       |                           |
   |                       |--- LDAP Bind ------------>|
   |                       |   (service account)       |
   |                       |                           |
   |                       |--- LDAP Search ----------->|
   |                       |   (&(sAMAccountName=alice) |
   |                       |    (memberOf=NetAdmins))   |
   |                       |                           |
   |                       |<-- LDAP Response ----------|
   |                       |   DN: cn=alice,...         |
   |                       |   memberOf: cn=NetAdmins   |
   |                       |                           |
   |                       |--- LDAP Auth ------------>|
   |                       |   Bind as alice,           |
   |                       |   password=user's password |
   |                       |                           |
   |                       |<-- LDAP Bind Success ------|
   |                       |                           |
   |                       | [Map AD group to TACACS    |
   |                       |  policy: NetAdmins →       |
   |                       |  net-engineer group]       |
   |                       |                           |
   |<-- AUTHEN REPLY PASS---|                           |
   |   priv-lvl=15          |                           |
```

**Benefits of AD integration:**
- Single identity source — same password for Windows and network devices.
- User disable in AD instantly removes network device access.
- Group membership in AD drives TACACS+ authorization policy.
- Password complexity/expiration policies enforced by AD.

### 19.2 Multi-Factor Authentication (MFA) Integration

TACACS+ can integrate with MFA through several mechanisms:

**1. Token Code Appended to Password (simplest):**
```
User enters: <password><OTP-token>
TACACS+ server splits: password + OTP
Validates password against LDAP
Validates OTP against token server (RSA, TOTP, etc.)

Example: Password="MyPass" + OTP="123456" = "MyPass123456"
```

**2. Challenge-Response (GETDATA status):**
```
Server replies GETDATA with msg="Enter OTP: "
User enters their TOTP or RSA token code
Server validates OTP

This is cleaner UX but requires server support for async OTP validation.
```

**3. Cisco DUO Integration:**
```
ISE + DUO:
  1. Auth to ISE with AD credentials (TACACS+ AUTHEN)
  2. ISE calls DUO API to trigger push notification
  3. Server returns GETDATA: "Check DUO app and enter passcode:"
  4. User approves on phone → receives passcode
  5. User enters passcode → ISE validates with DUO
  6. AUTHEN PASS returned to NAS
```

### 19.3 Role-Based Access Control (RBAC) Design

```
Enterprise RBAC Matrix for Network Devices:

Role              | Routers | Core SWT | Edge SWT | Firewalls | WLC
------------------+---------+----------+----------+-----------+----
Help Desk         | RO      | RO       | RO       | --        | RO
NOC Level 1       | RO+OPS  | RO+OPS   | RO+OPS   | RO        | RO
NOC Level 2       | RO+OPS  | RO+OPS   | FULL     | RO        | OPS
Network Engineer  | FULL    | FULL     | FULL     | RO        | FULL
Security Engineer | RO      | RO       | RO       | FULL      | RO
Senior Admin      | FULL    | FULL     | FULL     | FULL      | FULL

RO    = Read-Only (show commands)
OPS   = Operational (show + clear + debug + some interface ops)
FULL  = Full access (all commands minus destructive)
FULL* = Full access including destructive (reload, erase)
--    = No access
```

### 19.4 Network Automation and TACACS+

When automating network devices (Ansible, Netmiko, NAPALM, etc.), TACACS+ considerations:

```
Automation TACACS+ Best Practices:
=====================================

1. Dedicated automation service account
   user = automation-svc
   member = automation-group

2. Automation-specific command set
   automation-group allows:
     - All needed configuration commands
     - BUT NOT interactive commands like "more", "terminal pager 0"
     - Use "terminal length 0" equivalent in your tool

3. Source IP restriction (if possible at TACACS+ server)
   Only allow automation account login from automation server IPs
   automation-svc may only authenticate from 10.0.0.100

4. Separate accounting stream
   Tag automation sessions for separation in audit logs
   service = shell
   task_id = AUTOMATION-<job-id>

5. Credential management
   Store automation credentials in:
     - HashiCorp Vault
     - CyberArk
     - AWS Secrets Manager
   Never in plaintext files or version control

6. Test TACACS+ availability before automation runs
   If TACACS+ is down and you use local fallback:
   Automation may auth locally but with different permissions!
   This can cause unexpected authorization failures mid-run
```

### 19.5 TACACS+ in SDN and Controller-Based Networks

In modern SDN environments (Cisco DNA Center, SD-WAN, etc.):

```
SDN/Controller-Based TACACS+ Architecture:

  Engineers
     |
     | SSH/HTTPS
     v
  +------------------+
  |   DNA Center /   |
  |   SD-WAN Manager |  ← Central management plane
  |   (Controller)   |
  +--------+---------+
           |
           | TACACS+ auth for controller login
           v
  +------------------+
  |  TACACS+ Server  |
  +------------------+
           |
           | [Engineers may also have direct
           |  device access for emergencies]
           |
           v
  Network Devices (managed by controller)

Key points:
- TACACS+ now protects the CONTROLLER, not individual devices
- Controller accesses devices via its own credentials (NETCONF/RESTCONF)
- TACACS+ accounting on controller captures what changes were pushed
- But individual device command authorization is less applicable
- Traditional TACACS+ + direct device access still needed for break-glass
```

---

## 20. Troubleshooting & Debugging

### 20.1 IOS Debug Commands

```
! ===========================
! TACACS+ Debugging Commands
! ===========================

! WARNING: Debug commands generate significant output
! Always use terminal monitor and logging buffered in production
! Turn off debug immediately after capturing needed info

! Enable terminal output for SSH/Telnet sessions:
terminal monitor

! Core TACACS+ debug:
debug tacacs             ! Basic TACACS+ events and status
debug tacacs events      ! Detailed event tracing
debug tacacs packets     ! Full packet content (most verbose)

! AAA-level debug:
debug aaa authentication  ! Authentication events
debug aaa authorization   ! Authorization events
debug aaa accounting      ! Accounting events

! Combination for full picture:
debug tacacs packets
debug aaa authentication
debug aaa authorization

! ALWAYS turn off when done:
undebug all
no debug all
```

### 20.2 Interpreting Debug Output

```
Sample debug tacacs output:

Router# debug tacacs
TACACS+: Opening TCP/IP to 10.0.0.10/49 timeout=5      ← Connecting to server
TACACS+: Opened TCP/IP handle 0x6 to 10.0.0.10/49      ← Connection successful
TACACS+: Authenticate/Author/Acct (0x3/0x2): session_id=1234 service=1 ← Session started
TACACS+: send AUTHEN/START packet ver=193 id=1234       ← Sending auth start
TACACS+: received AUTHEN/REPLY ver=193 id=1234          ← Got reply from server
TACACS+:   status = 5 (GETPASS)                         ← Server asking for password
TACACS+: send AUTHEN/CONTINUE packet ver=193 id=1234    ← Sending password
TACACS+: received AUTHEN/REPLY ver=193 id=1234
TACACS+:   status = 1 (PASS)                            ← Authentication passed!
TACACS+: send AUTHOR/REQUEST ver=193 id=5678            ← Sending auth request
TACACS+: received AUTHOR/RESPONSE ver=193 id=5678
TACACS+:   status = 1 (PASS_ADD)                        ← Authorization passed!
TACACS+: send ACCT/START ver=193 id=9999                ← Sending accounting start
TACACS+: received ACCT/REPLY ver=193 id=9999
TACACS+:   status = 1 (SUCCESS)                         ← Accounting acknowledged

---
Error scenario:
TACACS+: Opening TCP/IP to 10.0.0.10/49 timeout=5
TACACS+: TCP open to 10.0.0.10/49 FAILED                ← Cannot reach server!
TACACS+: Opening TCP/IP to 10.0.0.11/49 timeout=5       ← Trying secondary
TACACS+: Opened TCP/IP handle 0x7 to 10.0.0.11/49
... (continues on secondary)

---
Authorization failure:
TACACS+: received AUTHOR/RESPONSE ver=193 id=5678
TACACS+:   status = 16 (FAIL)                           ← Command denied!
%AAA-3-AUTHORIZE: Command authorization failed for user 'bob' trying cmd 'configure terminal'
```

### 20.3 Common Problems and Solutions

#### Problem 1: "% Authentication failed"

```
Symptom: User sees "% Authentication failed" immediately
         Or: Login prompt appears then fails

Debugging Steps:
1. Verify TACACS+ server is reachable from NAS:
   test aaa group CORP-TACACS username testuser password testpass new-code
   (This tests AAA without logging in)

2. Check server connectivity:
   telnet 10.0.0.10 49     ! Should connect (even though it's not Telnet protocol)
   ping 10.0.0.10

3. Verify shared secret matches:
   On NAS: show running-config | include tacacs
   On server: check client config

4. Check if user exists on TACACS+ server

5. Check if server IP is in TACACS+ client list on server

Common Causes:
- Shared secret mismatch (MOST COMMON)
- User not in TACACS+ database
- NAS IP not in TACACS+ server client list
- Wrong port number
- Firewall blocking TCP/49
```

#### Problem 2: "% Authorization failed"

```
Symptom: User logs in successfully but gets:
         "% Authorization failed" at exec prompt
         Or: "Command authorization failed" for specific commands

Debugging Steps:
1. debug aaa authorization
2. Look for AUTHOR/RESPONSE with status=16 (FAIL)

3. On TACACS+ server: check the user's group membership
4. Check group's service=shell entry
5. Check if cmd is in permitted commands

For exec authorization failure:
- User group may be missing "service = exec { priv-lvl = X }"
- TACACS+ server may have no matching policy for this service

For command authorization failure:
- Command not in permitted cmd list
- Default service = deny blocks it
- Regex in permit statement doesn't match command arguments
```

#### Problem 3: "% Connection to TACACS+ server timeout"

```
Symptom: Long pause before login prompt
         Then either local fallback or failure

Debugging Steps:
1. Check network path: ping, traceroute to TACACS+ server
2. Check firewall rules (TCP/49 allowed?)
3. Check TACACS+ daemon running on server: systemctl status tac_plus
4. Check if server IP is correct in NAS config
5. Check source interface configured correctly:
   show ip tacacs

Common Causes:
- TACACS+ daemon not running
- Firewall blocking TCP/49
- Wrong server IP configured
- Source interface IP not reachable from server
- Routing issue in management network

Fix:
- Reduce timeout to fail-fast: tacacs-server timeout 2
- Ensure secondary server is configured and reachable
- Fix underlying network/firewall issue
```

#### Problem 4: Accounting Records Not Appearing

```
Symptom: Auth and authz work but no accounting logs appear

Check:
1. Is accounting configured?
   show running-config | include aaa accounting

2. Is the accounting server reachable? (Same checks as auth)

3. Check if TACACS+ server log directory has write permissions

4. debug tacacs
   Look for ACCT/START and ACCT/REPLY packets
   Check REPLY status

5. For command accounting: ensure aaa accounting commands X is configured
   for the right privilege levels

6. Check: aaa accounting exec vs aaa accounting commands
   Both may be needed
```

#### Problem 5: Single-Connection Mode Lockout

```
Symptom: After changing TACACS+ config, some sessions work,
         others fail in unpredictable ways

Cause: Single-connection mode with cached TCP connections
       Old connections use old config, new ones use new

Fix:
  clear tcp tcb <handle>   ! Clear specific TCP handle
  clear tcp statistics
  
Or restart the relevant service/process on the NAS
After config changes, test immediately to verify
```

### 20.4 show Commands for TACACS+ Status

```
! Useful show commands:

show tacacs               ! Server list, hits, failures, last used
show aaa servers          ! All AAA servers and statistics
show aaa sessions         ! Active AAA sessions
show aaa local user lockout  ! Locked out local users
show aaa user all         ! All AAA user info
show aaa attributes       ! Defined AAA attributes
show running-config | section aaa        ! All AAA config
show running-config | section tacacs     ! TACACS+ config
show users                ! Currently logged-in users
show line                 ! Line status and users

! Test without logging in:
test aaa group CORP-TACACS username admin password admin123 new-code

! Example output of 'show tacacs':
Router# show tacacs

Tacacs+ Server : 10.0.0.10/49    opens=15 closes=15 aborts=0 errors=0
                                   packets in=45 packets out=45
                                   failed to connect=0

Tacacs+ Server : 10.0.0.11/49    opens=0  closes=0  aborts=0 errors=0
                                   packets in=0  packets out=0
                                   failed to connect=0
```

### 20.5 Server-Side Log Analysis

On a tac_plus server:

```
# tac_plus log format:
# timestamp  host  NAS  user  service  status  cmd

Example logs:

Mon May  4 14:32:01 2026 [12345]: alice cli/ssh 10.0.0.1 start  task_id=1 service=shell
Mon May  4 14:32:05 2026 [12345]: alice cli/ssh 10.0.0.1 cmd    task_id=2 service=shell cmd=show ver
Mon May  4 14:32:10 2026 [12345]: alice cli/ssh 10.0.0.1 cmd    task_id=3 service=shell cmd=conf t
Mon May  4 14:32:15 2026 [12345]: alice cli/ssh 10.0.0.1 cmd    task_id=4 service=shell cmd=router ospf 1
Mon May  4 14:45:00 2026 [12345]: alice cli/ssh 10.0.0.1 stop   task_id=1 service=shell elapsed=780

Failed auth:
Mon May  4 14:30:00 2026 [12346]: bob cli/ssh 10.0.0.2 authen failed

Unauthorized command:
Mon May  4 14:33:01 2026 [12347]: charlie cli/ssh 10.0.0.1 author denied cmd=reload
```

### 20.6 Packet Capture Analysis

```
TACACS+ Traffic Analysis with Wireshark/tcpdump:

# Capture TACACS+ traffic:
tcpdump -i eth0 -w tacacs.pcap 'tcp port 49'

# In Wireshark:
Filter: tcp.port == 49
Protocol: TACACS+

What you can see (cleartext):
  - Source/Destination IP
  - TCP SYN/ACK/FIN sequence
  - TACACS+ header: type, sequence, session_id, length
  - Packet type (AUTHEN/AUTHOR/ACCT)

What you CANNOT see (encrypted):
  - Usernames
  - Passwords
  - Commands
  - AV pairs

If TAC_PLUS_UNENCRYPTED_FLAG is set (testing mode):
  ALL content visible — never leave this in production
```

---

## 21. Common Deployment Scenarios & Architectures

### 21.1 Small Enterprise (< 50 Devices)

```
Small Enterprise TACACS+ Deployment:

  +============================================================+
  |                    Company Network                         |
  |                                                           |
  |   +-----------------+        +-----------------+          |
  |   |  Linux Server   |        |  Linux Server   |          |
  |   |  tac_plus       |        |  tac_plus       |          |
  |   |  Primary        |        |  Secondary      |          |
  |   |  10.1.0.10      |        |  10.1.0.11      |          |
  |   +--------+--------+        +--------+--------+          |
  |            |                          |                   |
  |            +----------+---------------+                   |
  |                       |                                   |
  |              Management VLAN (10.1.0.0/24)               |
  |                       |                                   |
  |          +------------+-----------+                       |
  |          |            |           |                       |
  |      +---+---+    +---+---+   +---+---+                   |
  |      |  RTR  |    | CORE  |   |  FW   |                   |
  |      | (2x)  |    | SW    |   |       |                   |
  |      +-------+    +---+---+   +-------+                   |
  |                       |                                   |
  |            +----------+----------+                        |
  |            |          |          |                        |
  |        +---+---+  +---+---+  +---+---+                    |
  |        |ACCESS |  |ACCESS |  |ACCESS |                    |
  |        |  SW   |  |  SW   |  |  SW   |                    |
  |        +-------+  +-------+  +-------+                    |
  |                                                           |
  |   Users: 3-5 network admins                              |
  |   Config: tac_plus flat file                              |
  |   Auth: TACACS+ → local fallback                          |
  |   No AD integration (or simple LDAP)                      |
  +============================================================+
```

### 21.2 Medium Enterprise (50-500 Devices)

```
Medium Enterprise TACACS+ Deployment:

  +================================================================+
  |                      Enterprise Network                         |
  |                                                                |
  |  +------------------+    Replicated    +------------------+    |
  |  |   ISE / ACS      |<================>|   ISE / ACS      |    |
  |  |   Primary        |    User/Policy   |   Secondary      |    |
  |  |   10.1.0.10      |    Database      |   10.1.0.11      |    |
  |  +--------+---------+                  +--------+---------+    |
  |           |                                     |              |
  |           +------------------+------------------+              |
  |                              |                                 |
  |                     LDAP/AD Query                              |
  |                              |                                 |
  |                    +--------------------+                      |
  |                    |  Active Directory  |                      |
  |                    |  (Domain Ctrl)     |                      |
  |                    +--------------------+                      |
  |                              |                                 |
  |             Management Network (10.1.0.0/24)                  |
  |                              |                                 |
  |      +-------+-------+-------+-------+-------+                |
  |      |       |       |       |       |       |                |
  |   ROUTERS  CORE  DISTRIBUTION  EDGE  FIREWALL  WLC           |
  |   (10)     SWT(4)  SWT(20)   SWT(50) (4)     (2)            |
  |                                                                |
  |   Users: 15-30 network admins                                  |
  |   Config: ISE with AD integration                              |
  |   Auth: TACACS+ (no local fallback on VTY)                     |
  |   Console: local fallback only                                  |
  |   MFA: DUO integration for engineers                            |
  +================================================================+
```

### 21.3 Large Enterprise / Service Provider (500+ Devices)

```
Large Enterprise / SP TACACS+ Deployment:

  HEADQUARTERS (Data Center A)           DATA CENTER B
  +---------------------------------+    +---------------------------+
  |                                 |    |                           |
  | +----------+  +----------+      |    | +----------+             |
  | | TACACS+  |  | TACACS+  |      |    | | TACACS+  |             |
  | | Primary  |  | Secondary|      |    | | Regional |             |
  | | ISE-1    |  | ISE-2    |      |    | | ISE-3    |             |
  | | (active) |  | (standby)|      |    | | (active) |             |
  | +----+-----+  +----+-----+      |    | +----+-----+             |
  |      |             |            |    |      |                   |
  |      +------+------+            |    |      |                   |
  |             |                   |    |      |                   |
  |   +---------+----------+        |    | +----+------+            |
  |   | Management Network  |       |    | | Mgmt Net   |           |
  |   | DC-A (10.1.0.0/24) |       |    | | DC-B       |           |
  |   +--+---+---+---+---+-+       |    | +--+-+-+--+--+           |
  |      |   |   |   |   |         |    |    | | |  |              |
  |   CORE DIST EDGE FW WLC        |    |  RTR SW FW WLC           |
  |   (50) (200)(100)(20)(10)      |    | (100)(200)(10)(5)         |
  +---------------------------------+    +---------------------------+
                  |                              |
                  +------ WAN Interconnect -------+
                  |
          BRANCH OFFICES (x20)
          +----------------------------+
          |  Branch router/switch       |
          |  → Primary: Regional ISE   |
          |  → Secondary: HQ ISE       |
          |  (over WAN, timeout=10s)   |
          +----------------------------+

Policy Hierarchy:
  Global policies (all devices): ISE Policy Sets
  Device-specific: ISE Device Groups
    DC-Core-Switches → Policy: DC-Admins
    Branch-Devices   → Policy: Branch-Ops
    Firewalls        → Policy: Security-Team

Accounting:
  All accounting → SIEM (Splunk/QRadar)
  Real-time alerting on:
    - reload commands
    - write erase commands
    - Failed auth (brute force detection)
    - Off-hours admin access
```

### 21.4 Multi-Vendor Environment

```
Multi-Vendor TACACS+ Environment:

  +=========================================================+
  |                  Mixed Vendor Network                   |
  |                                                         |
  |   TACACS+ Server (tac_plus or ISE)                     |
  |        |                                               |
  |        +----------+----------+----------+             |
  |        |          |          |          |             |
  |   +----+----+ +---+----+ +---+----+ +---+----+       |
  |   | Cisco   | | Juniper| | Arista | | Palo   |       |
  |   | IOS-XE  | | JunOS  | | EOS    | | Alto   |       |
  |   |         | |        | |        | |        |       |
  |   | Full    | | Full   | | Full   | | Partial|       |
  |   | TACACS+ | | TACACS+| | TACACS+| | TACACS+|       |
  |   | support | | support| | support| | support|       |
  |   +---------+ +--------+ +--------+ +--------+       |
  |                                                       |
  |   Vendor-Specific Considerations:                     |
  |   - Cisco: priv-lvl maps to IOS privilege levels      |
  |   - Juniper: class attribute maps to login classes     |
  |   - Arista: maps to EOS privilege levels              |
  |   - Palo Alto: Uses TACACS+ but admin role            |
  |     determined by "admin-role" AV pair                |
  +=========================================================+
```

---

## 22. Mental Model Summary

This section crystallizes the most important conceptual models for thinking about TACACS+.

### 22.1 The Doorman Analogy

Think of TACACS+ like a **high-security building's entrance system**:

```
Building = Network Device (Router, Switch, Firewall)
Doorman = NAS (enforces policy)
Security Office = TACACS+ Server (makes decisions)
ID Badge = Credentials (username/password)
Access List = Authorization Policy
Sign-In Log = Accounting Records

When you arrive:
1. AUTHENTICATION: Doorman checks your badge with Security Office.
   "Is this person who they claim to be?"

2. AUTHORIZATION: Security Office tells doorman what you're allowed to access.
   "This person can enter floors 1-5 but NOT the server room."

3. ACCOUNTING: Every door you open is logged.
   "Alice entered floor 3 at 14:32, accessed room 301 at 14:35..."
```

### 22.2 The Three Pillars Mental Model

```
         +---TACACS+---+
         |             |
    +----+    WHAT    +----+
    |    |   YOU DO   |    |
    |    +------------+    |
    |                     |
    v                     v
+-------+           +----------+
|  WHO  |           |  RECORD  |
|  ARE  |           |  WHAT    |
|  YOU  |           | HAPPENED |
+-------+           +----------+
AUTHEN              ACCOUNTING
(Verify             (Audit
 identity)          trail)
         ^
         |
    +----+----+
    | WHAT CAN|
    |  YOU DO |
    +---------+
    AUTHORIZATION
    (Policy
     enforcement)
```

### 22.3 The Protocol Flow Mental Model

```
Every TACACS+ interaction follows this pattern:

  CLIENT says: "I want to do X"    (REQUEST)
  SERVER says: "Yes/No/Tell me more" (REPLY)
  [Repeat if more info needed]

  Authentication: "Can I log in?" → "Give me password" → "Yes/No"
  Authorization:  "Can I run show?" → "Yes/No + conditions"
  Accounting:     "I just did X"    → "Acknowledged"
```

### 22.4 The Security Onion Model

```
TACACS+ Security Layers (from outside in):

  +==================================================+
  |  NETWORK LAYER: Out-of-band management network   |
  |  TACACS+ traffic isolated from data plane        |
  |  +============================================+  |
  |  |  TRANSPORT LAYER: TCP/49 (reliable)        |  |
  |  |  Optional: TLS wrapper (RFC 9105)          |  |
  |  |  +======================================+  |  |
  |  |  |  ENCRYPTION LAYER: MD5 obfuscation   |  |  |
  |  |  |  Full body encrypted, header clear   |  |  |
  |  |  |  +================================+  |  |  |
  |  |  |  |  SECRET LAYER: Shared key      |  |  |  |
  |  |  |  |  Never transmitted, used for   |  |  |  |
  |  |  |  |  encryption only               |  |  |  |
  |  |  |  |  +==========================+  |  |  |  |
  |  |  |  |  |  DATA: Credentials,      |  |  |  |  |
  |  |  |  |  |  commands, AV pairs,     |  |  |  |  |
  |  |  |  |  |  accounting records      |  |  |  |  |
  |  |  |  |  +==========================+  |  |  |  |
  |  |  |  +================================+  |  |  |
  |  |  +======================================+  |  |
  |  +============================================+  |
  +==================================================+
```

### 22.5 Decision Framework

**When designing TACACS+ policy, ask in this order:**

```
1. WHO is authenticating?
   └── What identity source? (Local DB / LDAP / AD)
   └── What MFA requirement? (None / OTP / Push)

2. WHERE are they connecting FROM?
   └── Source IP restrictions
   └── Time-of-day restrictions

3. WHAT device are they accessing?
   └── Device type (router vs switch vs firewall)
   └── Device criticality (core vs edge vs branch)

4. WHAT can they DO on that device?
   └── Privilege level (read-only, ops, full)
   └── Specific command whitelist/blacklist
   └── Service (shell vs ppp vs enable)

5. WHAT should be RECORDED?
   └── Session start/stop
   └── All commands (especially for compliance)
   └── Failed attempts
   └── Where accounting records go (SIEM, local file)
```

### 22.6 Key Numbers to Remember

| Item | Value |
|---|---|
| TCP Port | 49 |
| Header size | 12 bytes |
| Max sequence number | 255 (then new session) |
| Encryption | MD5-based XOR obfuscation |
| Major version | 0xC (12) |
| Privilege levels | 0-15 (15 = full access) |
| Default timeout | 5 seconds |
| AUTHEN status PASS | 0x01 |
| AUTHEN status FAIL | 0x02 |
| AUTHOR status PASS_ADD | 0x01 |
| AUTHOR status FAIL | 0x10 |
| ACCT status SUCCESS | 0x01 |
| Mandatory AV pair separator | = (equals sign) |
| Optional AV pair separator | * (asterisk) |

### 22.7 RFC Reference Map

```
Core TACACS+ Standards:
========================

RFC 8907 (Sept 2020) — The TACACS+ Protocol
  The definitive specification of TACACS+
  Formalizes what Cisco's draft described for 27 years
  Covers: packet format, encryption, all three AAA services
  Status: INFORMATIONAL (not STANDARDS TRACK, but authoritative)

RFC 9105 (Aug 2021) — An YANG Data Model for TACACS+
  Defines YANG model for TACACS+ client configuration
  Also covers TACACS+ over TLS

Related Standards:
==================
RFC 2865 — RADIUS (for comparison)
RFC 2866 — RADIUS Accounting (for comparison)
RFC 3579 — RADIUS and EAP (for comparison)
RFC 5176 — Dynamic RADIUS Authorization Extensions

Authentication Method Standards:
=================================
RFC 1994 — PPP CHAP
RFC 2433 — Microsoft PPP CHAP Extensions (MS-CHAP v1)
RFC 2759 — Microsoft PPP CHAP Extensions v2
RFC 3748 — EAP (Extensible Authentication Protocol)
```

---

## Appendix A: Quick Reference Card

```
TACACS+ Quick Reference
========================

Protocol:   TCP/49
RFC:        8907 (2020)
Encryption: MD5 XOR (body only, header cleartext)
AAA:        Fully separated (independent exchanges)

Packet Types:
  0x01 = AUTHEN (Authentication)
  0x02 = AUTHOR (Authorization)
  0x03 = ACCT   (Accounting)

Auth Status Codes:
  0x01 = PASS     0x04 = GETUSER
  0x02 = FAIL     0x05 = GETPASS
  0x03 = GETDATA  0x07 = ERROR

Author Status Codes:
  0x01 = PASS_ADD   0x10 = FAIL
  0x02 = PASS_REPL  0x11 = ERROR

Acct Status Codes:
  0x01 = SUCCESS    0x02 = ERROR

AV Pair Separators:
  = (mandatory)   * (optional)

Key IOS Commands:
  aaa new-model                   — Enable AAA
  debug tacacs                    — Basic debug
  debug tacacs packets            — Packet-level debug
  show tacacs                     — Server stats
  test aaa group <grp> user pass new-code — Test auth
  undebug all                     — Stop all debugs

Common AV Pairs:
  priv-lvl=15    service=shell
  cmd=show       cmd-arg=run
  timeout=30     idletime=15
```

## Appendix B: Wireshark TACACS+ Filter Reference

```
Wireshark Filters for TACACS+ Analysis:
=========================================

# All TACACS+ traffic
tcp.port == 49

# Only TACACS+ protocol packets (if Wireshark dissects them)
tacacs+

# TACACS+ authentication packets
tacacs+.type == 1

# TACACS+ authorization packets
tacacs+.type == 2

# TACACS+ accounting packets
tacacs+.type == 3

# Traffic to/from specific server
ip.addr == 10.0.0.10 && tcp.port == 49

# TCP connection issues
tcp.port == 49 && (tcp.flags.syn == 1 || tcp.flags.rst == 1)
```

## Appendix C: TACACS+ Compliance Mapping

```
Compliance Requirement ←→ TACACS+ Feature Mapping:

PCI-DSS Requirement 8 (User ID and Authentication):
  8.2 — Unique user IDs: TACACS+ per-user accounts
  8.3 — MFA: TACACS+ + DUO/RSA integration
  8.5 — No group/shared accounts: Per-user policy
  8.6 — No vendor defaults: Custom shared secrets

PCI-DSS Requirement 10 (Audit Logging):
  10.1 — Audit trail: TACACS+ accounting
  10.2 — Individual actions: Per-command accounting
  10.3 — Timestamps: Accounting includes timestamps
  10.5 — Log protection: Accounting sent to SIEM

SOX IT Controls:
  Access Control: Command authorization (who can do what)
  Change Management: Accounting shows what was changed
  Segregation of Duties: Role-based command sets

HIPAA Security Rule:
  164.312(a)(1) — Access Control: Auth + Authorization
  164.312(b) — Audit Controls: Command accounting
  164.312(d) — Person Authentication: TACACS+ auth

NIST SP 800-53:
  AC-2 — Account Management: TACACS+ user lifecycle
  AC-3 — Access Enforcement: Command authorization
  AU-2 — Audit Events: Session + command accounting
  AU-12 — Audit Record Generation: Accounting records
  IA-2 — Identification and Authentication: Auth module
  IA-5 — Authenticator Management: Shared secret mgmt
```

---

*This document covers TACACS+ comprehensively from protocol fundamentals through enterprise deployment. RFC 8907 is the authoritative specification. For the most current implementation guidance on specific platforms, always consult vendor documentation alongside this reference.*