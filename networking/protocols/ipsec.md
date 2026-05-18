# IPSec Protocol — The Complete In-Depth Guide
> "Security is not a product, but a process." — Bruce Schneier

---

## Table of Contents

1. [What Is IPSec? — The Foundation](#1-what-is-ipsec--the-foundation)
2. [Why IPSec? — Threat Model & Problems It Solves](#2-why-ipsec--threat-model--problems-it-solves)
3. [IPSec Architecture — The Big Picture](#3-ipsec-architecture--the-big-picture)
4. [Core Concepts — Vocabulary You Must Know](#4-core-concepts--vocabulary-you-must-know)
5. [Security Associations (SA)](#5-security-associations-sa)
6. [Security Databases: SPD and SAD](#6-security-databases-spd-and-sad)
7. [IPSec Protocols: AH and ESP](#7-ipsec-protocols-ah-and-esp)
8. [IPSec Modes: Transport vs Tunnel](#8-ipsec-modes-transport-vs-tunnel)
9. [Internet Key Exchange (IKE)](#9-internet-key-exchange-ike)
10. [IKEv1 — Phase 1 and Phase 2 Deep Dive](#10-ikev1--phase-1-and-phase-2-deep-dive)
11. [IKEv2 — Modern Key Exchange](#11-ikev2--modern-key-exchange)
12. [Cryptographic Algorithms in IPSec](#12-cryptographic-algorithms-in-ipsec)
13. [Packet Processing — Step by Step](#13-packet-processing--step-by-step)
14. [Real Protocol Packet Diagrams (ASCII)](#14-real-protocol-packet-diagrams-ascii)
15. [Anti-Replay Protection](#15-anti-replay-protection)
16. [Dead Peer Detection (DPD)](#16-dead-peer-detection-dpd)
17. [NAT Traversal (NAT-T)](#17-nat-traversal-nat-t)
18. [Perfect Forward Secrecy (PFS)](#18-perfect-forward-secrecy-pfs)
19. [IPSec in Practice — VPN Use Cases](#19-ipsec-in-practice--vpn-use-cases)
20. [C Implementation](#20-c-implementation)
21. [Rust Implementation](#21-rust-implementation)
22. [Security Considerations & Common Attacks](#22-security-considerations--common-attacks)
23. [Mental Models & Thinking Frameworks](#23-mental-models--thinking-frameworks)

---

## 1. What Is IPSec? — The Foundation

### Definition

**IPSec** stands for **Internet Protocol Security**. It is a **suite of protocols** (not a single protocol) that operates at the **Network Layer (Layer 3)** of the OSI model to provide security services for IP communications.

The key phrase is "suite of protocols" — IPSec is like a toolbox containing multiple specialized tools that work together.

### OSI Layer Context

```
+-------------------------------------------+
|  Layer 7: Application  (HTTP, FTP, DNS)   |
+-------------------------------------------+
|  Layer 6: Presentation (TLS/SSL)          |
+-------------------------------------------+
|  Layer 5: Session                         |
+-------------------------------------------+
|  Layer 4: Transport    (TCP, UDP)         |
+-------------------------------------------+
|  Layer 3: Network  <<< IPSec lives here >>>
+-------------------------------------------+
|  Layer 2: Data Link    (Ethernet, WiFi)   |
+-------------------------------------------+
|  Layer 1: Physical     (Cables, Signals)  |
+-------------------------------------------+
```

**Why Layer 3?** Because IPSec works directly with IP packets. It intercepts, processes, and forwards packets at the network layer — below TCP/UDP, invisible to applications. This means any application using IP gets the benefit of IPSec without modification.

### What IPSec Provides (The CIA Triad + More)

```
| Property | Meaning | IPSec Mechanism |
|---|---|---|
| **Confidentiality** | Data is encrypted; only intended parties can read it | ESP Encryption |
| **Integrity** | Data is not modified in transit | HMAC / AH / ESP Auth |
| **Authentication** | You are who you say you are | IKE + Digital Certs / PSK |
| **Anti-Replay** | Old/duplicate packets are rejected | Sequence Numbers |
| **Key Management** | Keys are securely negotiated and refreshed | IKE Protocol |
```

### What IPSec Is NOT

- IPSec is **not** TLS/SSL — TLS operates at Layer 4-7, IPSec at Layer 3
- IPSec is **not** a single algorithm — it is a framework that uses pluggable algorithms
- IPSec is **not** only for VPNs — though VPNs are the most common use case

---

## 2. Why IPSec? — Threat Model & Problems It Solves

### The Problem: IP Was Designed Without Security

The original IP protocol (RFC 791, 1981) was designed for **reliability and routing**, not security. Raw IP packets have:

- No authentication — anyone can forge the source IP (IP spoofing)
- No encryption — packet payload is visible to any router in path
- No integrity — packets can be modified mid-transit (man-in-the-middle)
- No replay protection — captured packets can be re-sent

### The Threat Model — What Attackers Can Do

```
     [Alice]                  [Attacker]                [Bob]
        |                         |                       |
        |--- IP Packet ---------->|--- IP Packet -------->|
        |                         |                       |
        |   EAVESDROPPING:        |                       |
        |   Attacker reads all    |                       |
        |   packet contents       |                       |
        |                         |                       |
        |   TAMPERING:            |                       |
        |   Attacker modifies     |                       |
        |   packet data           |                       |
        |                         |                       |
        |   REPLAY:               |                       |
        |   Attacker captures     |                       |
        |   and re-sends old      |                       |
        |   packets               |                       |
        |                         |                       |
        |   SPOOFING:             |                       |
        |   Attacker pretends     |                       |
        |   to be Alice           |                       |
```

IPSec was standardized to solve all four attack vectors simultaneously.

---

## 3. IPSec Architecture — The Big Picture

### The IPSec Framework

```
+=========================================================+
|                    IPSec Framework                      |
|                                                         |
|  +------------------+    +------------------+           |
|  |  Key Management  |    |  Data Protection |           |
|  |  (IKE Protocol)  |    |  (AH + ESP)      |           |
|  +------------------+    +------------------+           |
|           |                       |                     |
|           v                       v                     |
|  +------------------+    +------------------+           |
|  | Security Assoc.  |    | Security Policy  |           |
|  | Database (SAD)   |    | Database (SPD)   |           |
|  +------------------+    +------------------+           |
|           |                       |                     |
|           +----------+------------+                     |
|                      |                                  |
|                      v                                  |
|           +---------------------+                       |
|           |    IP Packet        |                       |
|           |    Processing       |                       |
|           |    (Send / Recv)    |                       |
|           +---------------------+                       |
+=========================================================+
```

### The Three Pillars of IPSec

```
         IPSec
           |
    +------+------+
    |      |      |
   AH     ESP    IKE
    |      |      |
  Auth  Encr+   Key
  Only  Auth   Mgmt
```

**1. AH (Authentication Header)** — Provides integrity and authentication, NO encryption  
**2. ESP (Encapsulating Security Payload)** — Provides encryption, and optionally integrity/authentication  
**3. IKE (Internet Key Exchange)** — Negotiates and manages keys for AH and ESP  

---

## 4. Core Concepts — Vocabulary You Must Know

Before diving deep, you must understand these terms precisely:

### 4.1 Peer

A **peer** is any device (router, firewall, computer) that participates in IPSec communication. Two peers communicate to establish security.

### 4.2 Security Association (SA)

An SA is a **one-way agreement** between two peers that defines:
- Which algorithm to use (AES, SHA256, etc.)
- What keys to use
- How long the SA is valid
- The protocol (AH or ESP)

**One-way** is critical: For bidirectional communication, you need TWO SAs — one for each direction.

### 4.3 SPI (Security Parameter Index)

An **SPI** is a 32-bit number that uniquely identifies a Security Association at the receiver. When a packet arrives, the receiver looks at the SPI to find the correct SA and thus the correct keys and algorithms.

Think of SPI like a **file handle** or **session ID** — it's just a lookup key into the SAD database.

### 4.4 Selector

A **selector** is a set of fields used to match traffic to a security policy. Like a firewall rule: "if source IP is X and destination IP is Y and protocol is TCP and destination port is 443, then apply IPSec."

Selectors can match on:
- Source/Destination IP addresses (or ranges/subnets)
- Source/Destination ports
- Protocol (TCP, UDP, ICMP)
- Interface

### 4.5 Tunnel vs Transport

- **Transport mode**: Only the payload (data) is protected; IP headers remain intact
- **Tunnel mode**: The entire original IP packet is protected and encapsulated in a new IP packet

### 4.6 Key Material / Keying Material

The actual cryptographic bytes used for encryption and authentication. IKE negotiates and derives this material.

### 4.7 ISAKMP

**Internet Security Association and Key Management Protocol** — the framework within which IKE operates. ISAKMP defines the message formats and procedures for SA establishment.

### 4.8 Nonce

A **nonce** (Number Used Once) is a random value generated fresh for each session. Prevents replay attacks in key exchange and ensures freshness of derived keys.

### 4.9 PRF (Pseudo-Random Function)

A mathematical function that takes inputs and produces deterministic but unpredictable output — used to derive keys from other keys or shared secrets.

### 4.10 Diffie-Hellman Group

A mathematical structure used for key exchange where two parties can derive the same shared secret without transmitting the secret. Defined by large prime numbers and a generator.

---

## 5. Security Associations (SA)

### Conceptual Model

Think of an SA as a **contract between two peers**:

```
+-----------+                              +-----------+
|  Peer A   |                              |  Peer B   |
|           |                              |           |
| SA #1001|<----Direction A→B------->    | SA #1001|
|  SPI=101  |                              |  SPI=101  |
|  AES-256  |                              |  AES-256  |
|  Key=0xAB |                              |  Key=0xAB |
|           |                              |           |
| SA #1002|<------ Direction B→A   ------| SA #1002|
|  SPI=202  |                              |  SPI=202  |
|  AES-256  |                              |  AES-256  |
|  Key=0xCD |                              |  Key=0xCD |
+-----------+                              +-----------+
```

### SA Parameters

Each SA contains:

```
Security Association {
    SPI          : 32-bit identifier
    Protocol     : AH | ESP
    Mode         : Transport | Tunnel
    Algorithms   : {
        Encryption   : AES-128-CBC | AES-256-GCM | 3DES | NULL
        Integrity    : HMAC-SHA1 | HMAC-SHA256 | AES-XCBC
        PRF          : PRF-HMAC-SHA256
        DH Group     : Group 2 | 14 | 19 | 20
    }
    Keys         : {
        Encryption_Key  : <bytes>
        Auth_Key        : <bytes>
    }
    Lifetime     : {
        Seconds    : e.g., 3600
        Bytes      : e.g., 4GB
    }
    Tunnel_Endpoints : {
        Local  : IP address
        Remote : IP address
    }
    Anti-Replay  : sliding_window_size
    Sequence_Num : counter
}
```

### SA Lifecycle

```
         [NEGOTIATE]         [USE]           [EXPIRE]
              |                |                 |
  IKE starts  |   SA created   |  Data flows    |  SA deleted
  ----------->|--------------->|--------------->|--------->
              |                |                |
              |<-- Lifetime -->|                |
              |          New SA negotiated      |
              |          before expiry          |
```

### SA Bundle

In practice, multiple SAs are used together as a **bundle**. For example, an ESP SA might be used alongside a separate AH SA for different properties. The bundle is applied in sequence.

---

## 6. Security Databases: SPD and SAD

IPSec uses two critical databases at each endpoint:

### 6.1 Security Policy Database (SPD)

The **SPD** is like a **firewall rulebook**. It defines what should happen to every IP packet:
- **BYPASS** — Let the packet through without IPSec
- **DISCARD** — Drop the packet
- **PROTECT** — Apply IPSec (which SA to use?)

#### SPD Entry Structure

```
SPD Entry {
    Selector  : {
        src_ip   : 192.168.1.0/24
        dst_ip   : 10.0.0.0/8
        protocol : TCP
        src_port : any
        dst_port : 443
    }
    Action    : PROTECT
    SA_Template : {
        Protocol : ESP
        Mode     : Tunnel
        Algorithms : AES-256-GCM + SHA-256
    }
    Pointer_to_SA : <SPI in SAD>
}
```

#### SPD Decision Flow

```
Outbound Packet Arrives
         |
         v
   +------------+
   | Match SPD  |
   | Entry?     |
   +------------+
    /    |    \
   /     |     \
  v      v      v
DISCARD  BYPASS  PROTECT
(drop)  (send   (apply
         as-is) IPSec)
                  |
                  v
           +------------+
           | SA exists  |
           | in SAD?    |
           +------------+
              |      |
             YES     NO
              |      |
              v      v
          Use SA   Trigger
                   IKE to
                   create SA
```

### 6.2 Security Association Database (SAD)

The **SAD** stores all active Security Associations. It is indexed by **SPI + destination IP + protocol**.

```
SAD Lookup Key:  (SPI, Destination_IP, Protocol)

SAD {
    Entry[SPI=1001, dst=10.0.0.1, ESP] = {
        encryption_key : 0xDEADBEEF...
        auth_key       : 0xCAFEBABE...
        algorithm      : AES-256-GCM
        seq_num        : 10042
        replay_window  : [bitmap]
        lifetime_bytes : remaining_bytes
        lifetime_secs  : remaining_seconds
    }
    Entry[SPI=2002, dst=192.168.1.1, ESP] = {
        ...
    }
}
```

### 6.3 How SPD and SAD Work Together

```
OUTBOUND PACKET:
   1. Check SPD: "Should this packet be protected?"
   2. If PROTECT: Look up SAD for matching SA
   3. If SA exists: Use it to encrypt/authenticate packet
   4. If no SA: Trigger IKE, then use new SA

INBOUND PACKET:
   1. Extract SPI from AH/ESP header
   2. Look up SAD using (SPI, src_IP, protocol)
   3. Verify authentication / decrypt
   4. Check SPD: "Is this packet authorized to come in?"
   5. If matches policy: pass to upper layers
```

---

## 7. IPSec Protocols: AH and ESP

### 7.1 Authentication Header (AH) — RFC 4302

**AH provides:**
- Data origin authentication
- Integrity verification
- Anti-replay protection
- **NO encryption** (data is visible in plaintext)

**AH does NOT provide:**
- Confidentiality (no encryption)

**AH covers:** The entire IP packet including immutable IP header fields, making it incompatible with NAT (NAT changes IP addresses which breaks AH integrity check).

#### AH Header Format (RFC 4302)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| Next Header   |  Payload Len  |          RESERVED             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                 Security Parameters Index (SPI)               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Sequence Number Field                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                Integrity Check Value (ICV)                    +
|              (variable length, 96 or 128 bits)                |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

**Fields Explained:**
- **Next Header** (8 bits): Protocol of the protected data (6=TCP, 17=UDP, 4=IP for tunnel)
- **Payload Len** (8 bits): Length of the AH header in 32-bit words, minus 2
- **Reserved** (16 bits): Must be zero
- **SPI** (32 bits): Identifies the SA at the receiver
- **Sequence Number** (32 bits): Monotonically increasing counter for anti-replay
- **ICV** (Integrity Check Value): HMAC output, verifies authenticity of packet

#### What AH Covers (Integrity Protection Scope)

```
+-------------------+------------+----------------+
|   IP Header       |  AH Header |    Payload     |
| (some fields are  |            |   (TCP/UDP/    |
|  zero'd for calc) |            |    data)       |
+-------------------+------------+----------------+
|<========== ICV covers this entire range =======>|

Mutable IP fields (TTL, ToS, etc.) are zeroed before ICV calc.
```

### 7.2 Encapsulating Security Payload (ESP) — RFC 4303

**ESP provides:**
- Confidentiality (encryption)
- Data origin authentication (optional)
- Integrity (optional, via authentication)
- Anti-replay protection

ESP is far more commonly used than AH because it provides encryption. In modern deployments, ESP with authentication is the standard choice.

#### ESP Packet Format (RFC 4303)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ ----
|               Security Parameters Index (SPI)                 |  ^
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+  |
|                      Sequence Number                          |  |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+  | Authenticated
|                    Payload Data  (variable)                   |  |
~                                                               ~  |
|                                                               |  |
+               +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+  |
|               |             Padding (0-255 bytes)             |  |
+-+-+-+-+-+-+-+-+               +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+  |
|                               |  Pad Length   | Next Header   |  |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ ----
|         Integrity Check Value-ICV   (variable)                |
~                                                               ~
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

**Fields Explained:**
- **SPI** (32 bits): Identifies SA at receiver
- **Sequence Number** (32 bits): Anti-replay counter
- **Payload Data**: The encrypted data (original packet payload in transport mode, or entire original IP packet in tunnel mode)
- **Padding**: Block cipher alignment; can also obscure traffic lengths
- **Pad Length** (8 bits): Number of padding bytes
- **Next Header** (8 bits): Protocol identifier of encrypted data
- **ICV**: Authentication tag (HMAC or AEAD tag)

#### ESP Encryption and Authentication Scope

```
+-------------------+--------------------------------------------------+
|   IP Header       |  SPI | SeqNum | [IV] | Encrypted Payload | Pad | Pad Len | Next Hdr | ICV |
+-------------------+--------------------------------------------------+
                             |<--- Encrypted (Confidentiality) -------->|
                    |<------------ Authenticated (Integrity) ------------->|
```

**AEAD (Authenticated Encryption with Associated Data)** like AES-GCM combines encryption and authentication in one step — more efficient and secure than separate operations.

### 7.3 AH vs ESP Comparison

```
Feature                    |  AH          |  ESP
---------------------------|--------------|---------------------
Encryption                 |  NO          |  YES
Integrity/Authentication   |  YES         |  YES (optional)
Anti-Replay                |  YES         |  YES
IP Header Protection       |  YES         |  Partial (not outer)
NAT Compatible             |  NO          |  YES (with NAT-T)
Protocol Number            |  51          |  50
Commonly Used Today        |  Rarely      |  YES (standard)
```

---

## 8. IPSec Modes: Transport vs Tunnel

### 8.1 Transport Mode

In **transport mode**, IPSec **only protects the payload** of the IP packet. The original IP header remains intact and is used for routing.

**Use case:** Host-to-host communication where both endpoints run IPSec.

#### Transport Mode — Original Packet

```
+----------------+------------------+------------------+
|   IP Header    |   TCP Header     |   TCP Payload    |
|  (src=A,dst=B) |                  |   (Data)         |
+----------------+------------------+------------------+
```

#### Transport Mode with ESP

```
+----------------+-----------+---+------------------+--------+
|   IP Header    | ESP Hdr   |   |   TCP Hdr+Data   |  ESP   |
|  (src=A,dst=B) | (SPI|Seq) |IV | [ENCRYPTED       | Trailer|
|                |           |   |  TCP+Data]       | + ICV  |
+----------------+-----------+---+------------------+--------+
                 |<------- Authenticated ----------->|
                             |<-- Encrypted -------->|
```

#### Transport Mode with AH

```
+----------------+-----------+------------------+------------------+
|   IP Header    |  AH Header|   TCP Header     |   TCP Payload    |
|  (src=A,dst=B) | (SPI|Seq) |                  |   (Data)         |
+----------------+-----------+------------------+------------------+
|<============ Authenticated (entire packet) ======================>|
```

### 8.2 Tunnel Mode

In **tunnel mode**, the **entire original IP packet** (header + payload) is encapsulated into a new IP packet. A new outer IP header is added.

**Use case:** VPN gateways — a gateway encrypts traffic from many hosts and sends it through the tunnel. The inner IP addresses identify the actual hosts; the outer IP addresses identify the VPN gateways.

#### Tunnel Mode — How It Works

```
+----------------+------------------+------------------+
|   IP Header    |   TCP Header     |   TCP Payload    |   <-- Original Packet
|  (src=A,dst=B) |                  |   (Data)         |
+----------------+------------------+------------------+
                         |
               [ IPSec Tunnel Mode Applied ]
                         |
                         v
+------------------+-----------+----------------------------------+--------+
|  NEW IP Header   | ESP Hdr   |   IV + Encrypted [            ] | ESP    |
| (src=GW1,dst=GW2)| (SPI|Seq) |       [Original IP Packet     ] | Trailer|
|                  |           |       [IP Hdr | TCP Hdr | Data] | + ICV  |
+------------------+-----------+----------------------------------+--------+
<== Outer Header ==>|<========= Authenticated ==================>|
                                |<====== Encrypted ============>|
```

**Notice:**
- Outer IP: `src=Gateway1, dst=Gateway2` (VPN gateway addresses)
- Inner IP: `src=HostA, dst=HostB` (actual host addresses, encrypted)
- External routers see only gateway addresses
- Inner addresses are completely hidden

### 8.3 Transport vs Tunnel — Decision Flow

```
Do both endpoints (src and dst)
run IPSec themselves?
         |
       YES|           NO|
         |              |
    +----v----+    +----v----+
    |Transport|    | Tunnel  |
    |  Mode   |    |  Mode   |
    +---------+    +---------+
    (host to         (gateway
     host)           to gateway,
                    or host to
                     gateway)
```

### 8.4 Visual Comparison of Both Modes

```
TRANSPORT MODE:
Host A ---[AH/ESP protects TCP+Data only]--- Host B
  |                                              |
192.168.1.1                                192.168.1.2
(IP header visible to routers)

TUNNEL MODE (VPN):
Host A -- GW1 ---[ESP protects entire pkt]--- GW2 -- Host B
  |         |                                   |        |
192.168.1.1 10.0.0.1                       10.0.0.2  192.168.2.1
             |<====== Encrypted Tunnel ========>|
     (Routers see only 10.0.0.1 → 10.0.0.2, 
      cannot see inner 192.168.x.x addresses)
```

---

## 9. Internet Key Exchange (IKE)

### What Is IKE?

**IKE** (Internet Key Exchange) is the protocol that negotiates, establishes, and manages Security Associations for IPSec. Without IKE, you would have to manually configure keys on every device — impractical for large networks.

IKE runs on **UDP port 500** (and UDP 4500 when NAT-T is needed).

### IKE Versions

```
         IKE History
              |
    +---------+---------+
    |                   |
  IKEv1               IKEv2
(RFC 2409)          (RFC 7296)
  (1998)              (2005, updated)
  Complex,            Simpler,
  more messages       fewer messages,
                      better design
```

### Core IKE Goals

1. **Mutual Authentication** — Prove both sides are who they claim to be
2. **Key Exchange** — Establish a shared secret without transmitting it
3. **SA Negotiation** — Agree on algorithms, lifetimes, modes
4. **Key Derivation** — Derive encryption/authentication keys from shared secret
5. **SA Management** — Delete, renew, and manage SA lifetimes

### IKE Authentication Methods

| Method | How It Works | Security |
|---|---|---|
| **Pre-Shared Key (PSK)** | Both sides have same secret configured manually | Simple but doesn't scale |
| **RSA Signatures** | Each side has public/private key pair, signs data | Strong, scalable |
| **Digital Certificates** | PKI-based, X.509 certificates | Enterprise standard |
| **EAP (IKEv2 only)** | Extensible Authentication Protocol | Supports many auth types |

---

## 10. IKEv1 — Phase 1 and Phase 2 Deep Dive

IKEv1 operates in two distinct phases:

### Phase 1: IKE SA (ISAKMP SA)

**Goal:** Establish a secure, authenticated channel between the two IKE peers. This is the "negotiation tunnel" used to safely set up IPSec.

IKEv1 Phase 1 has two modes:
1. **Main Mode** — More secure, 6 messages, hides identity
2. **Aggressive Mode** — Faster, 3 messages, identity exposed

#### Phase 1 Main Mode — 6 Message Exchange

```
Initiator (A)                                    Responder (B)
     |                                                  |
     |------- Message 1: SA Proposal  --------------->  |
     |   [Proposed algorithms, DH group, lifetime]      |
     |                                                  |
     |<------ Message 2: SA Accept   ----------------   |
     |   [Chosen algorithm suite]                       |
     |                                                  |
     |------- Message 3: DH Public Key + Nonce ------>  |
     |   [KE payload: g^a mod p, Nonce_A]               |
     |                                                  |
     |<------ Message 4: DH Public Key + Nonce -------  |
     |   [KE payload: g^b mod p, Nonce_B]               |
     |   (Now both compute shared secret g^ab mod p)    |
     |                                                  |
     |------- Message 5: Identity + Auth [ENCRYPTED]--> |
     |   [ID_A, AUTH data]  <-- encrypted with SKEYID   |
     |                                                  |
     |<------ Message 6: Identity + Auth [ENCRYPTED]--  |
     |   [ID_B, AUTH data]  <-- encrypted with SKEYID   |
     |                                                  |
     |   === IKE SA (ISAKMP SA) now established ===     |
     |   === Phase 1 complete ===                       |
```

#### Key Derivation in Phase 1

From the Diffie-Hellman shared secret and nonces, IKEv1 derives:

```
Shared_Secret = DH(g^a mod p, g^b mod p) = g^ab mod p

SKEYID = PRF(Pre-Shared-Key, Nonce_A | Nonce_B)         [for PSK auth]
       = PRF(Nonce_A | Nonce_B, g^ab mod p)              [for cert auth]

SKEYID_d  = PRF(SKEYID, g^ab | CKY-I | CKY-R | 0)      [key material for IPSec SAs]
SKEYID_a  = PRF(SKEYID, SKEYID_d | g^ab | CKY-I | CKY-R | 1) [IKE integrity key]
SKEYID_e  = PRF(SKEYID, SKEYID_a | g^ab | CKY-I | CKY-R | 2) [IKE encryption key]

CKY-I = Cookie of Initiator (prevents DoS)
CKY-R = Cookie of Responder
```

**Mental Model:** Think of SKEYID as the "master key" and SKEYID_d, SKEYID_a, SKEYID_e as "derived sub-keys" for different purposes.

#### Phase 1 Aggressive Mode — 3 Message Exchange

```
Initiator (A)                                    Responder (B)
     |                                                  |
     |-- Message 1: SA + DH + Nonce + ID_A ---------->  |
     |   [All crypto params + identity in one msg]      |
     |                                                  |
     |<- Message 2: SA + DH + Nonce + ID_B + AUTH ----  |
     |   [Chosen params + B's DH + auth of B]           |
     |   (Identity of B visible in plaintext!)          |
     |                                                  |
     |-- Message 3: AUTH --------------------------->   |
     |   [Authentication of A]                          |
     |   (Identity of A also visible!)                  |
     |                                                  |
     |   === Phase 1 complete (but identities exposed!) |
```

**Why Aggressive Mode is Risky:** Identities are transmitted before encryption is established, enabling offline dictionary attacks against PSK.

### Phase 2: IPSec SA (Quick Mode)

**Goal:** Using the secure Phase 1 channel, negotiate the actual IPSec SAs for data protection.

```
Initiator (A)                                    Responder (B)
     |          [All messages encrypted with Phase 1 keys]
     |                                                  |
     |-- Message 1: SA Proposal + Nonce + [ID_selectors]|
     |   [Proposed ESP/AH algorithms, PFS DH group]     |
     |                                                  |
     |<- Message 2: SA Accept + Nonce + [ID_selectors]--|
     |   [Chosen algorithms + B's DH (if PFS)]          |
     |                                                  |
     |-- Message 3: Hash for confirmation ------------> |
     |   [Acknowledges receipt]                         |
     |                                                  |
     |   === IPSec SA pair now established ===          |
     |   === Data can now flow protected ===            |
```

#### Key Derivation in Phase 2

```
If PFS enabled (new DH exchange in Phase 2):
  KEYMAT = PRF(SKEYID_d, g^xy | Protocol | SPI | Nonce_I | Nonce_R)

If no PFS:
  KEYMAT = PRF(SKEYID_d, Protocol | SPI | Nonce_I | Nonce_R)

KEYMAT is then split:
  ESP_Enc_Key_inbound   = first N bytes of KEYMAT
  ESP_Auth_Key_inbound  = next M bytes
  ESP_Enc_Key_outbound  = next N bytes
  ESP_Auth_Key_outbound = next M bytes
```

### IKEv1 Complete Flow Summary

```
 PHASE 1 (6 or 3 messages)         PHASE 2 (3 messages)
+---------------------------+    +---------------------------+
|  Establish IKE SA         |    |  Establish IPSec SA pair  |
|  - Authenticate peers     |    |  - Negotiate ESP/AH algo  |
|  - DH key exchange        |    |  - Optional PFS           |
|  - Derive IKE keys        |    |  - Derive data-plane keys |
+---------------------------+    +---------------------------+
         |                                   |
         v                                   v
  Secure channel for               Data flows encrypted
  Phase 2 negotiation              and authenticated
```

---

## 11. IKEv2 — Modern Key Exchange

IKEv2 (RFC 7296) was designed to address IKEv1's complexity, redundancy, and security issues. It uses **4 messages minimum** to establish both IKE SA and first IPSec SA simultaneously.

### IKEv2 — Initial Exchange (4 Messages)

```
Initiator (A)                                    Responder (B)
     |                                                  |
     |== EXCHANGE: IKE_SA_INIT =========================|
     |                                                  |
     |------- Request 1: IKE_SA_INIT --------------->   |
     |   HDR, SAi1, KEi, Ni                             |
     |   [Proposed IKE algorithms, DH pub key, Nonce]   |
     |                                                  |
     |<------ Response 1: IKE_SA_INIT ---------------   |
     |   HDR, SAr1, KEr, Nr, [CERTREQ]                  |
     |   [Chosen algorithms, DH pub key, Nonce, optcert]|
     |                                                  |
     |   Both sides now compute:                        |
     |   SKEYSEED = PRF(Ni | Nr, g^ir)                  |
     |   Derive: SK_d, SK_ai, SK_ar, SK_ei, SK_er, SK_pi, SK_pr|
     |                                                  |
     |== EXCHANGE: IKE_AUTH ============================|
     |                                                  |
     |------- Request 2: IKE_AUTH [ENCRYPTED] ------->  |
     |   HDR, SK { IDi, [CERT,] [CERTREQ,]              |
     |             [IDr,] AUTH, SAi2, TSi, TSr }        |
     |   [Identity, Auth proof, IPSec SA proposal,      |
     |    Traffic selectors]                            |
     |                                                  |
     |<------ Response 2: IKE_AUTH [ENCRYPTED] -------  |
     |   HDR, SK { IDr, [CERT,] AUTH, SAr2, TSi, TSr }  |
     |   [Identity, Auth proof, IPSec SA acceptance,    |
     |    Traffic selectors]                            |
     |                                                  |
     |   === IKE SA + First IPSec SA both established! =|
     |   === Data can flow immediately after 4 messages=|
```

**Key improvement:** IKEv2 completes both IKE SA and first Child SA in just 4 messages vs IKEv1's 9+ messages.

### IKEv2 Key Derivation

```
g^ir = Diffie-Hellman shared secret

SKEYSEED = PRF(Ni | Nr, g^ir)

{SK_d | SK_ai | SK_ar | SK_ei | SK_er | SK_pi | SK_pr}
  = PRF+(SKEYSEED, Ni | Nr | SPIi | SPIr)

SK_d  : Key for deriving child SA keying material
SK_ai : Integrity key for IKE messages (A→B direction)
SK_ar : Integrity key for IKE messages (B→A direction)
SK_ei : Encryption key for IKE messages (A→B)
SK_er : Encryption key for IKE messages (B→A)
SK_pi : Used in AUTH computation of initiator
SK_pr : Used in AUTH computation of responder
```

### IKEv2 Informational Exchange

After the initial exchange, IKEv2 uses **INFORMATIONAL exchanges** for:
- Deleting SAs (DELETE payload)
- Reporting errors (NOTIFY payload)
- Dead Peer Detection
- Keepalives

```
Initiator (A)                           Responder (B)
     |                                        |
     |-- INFORMATIONAL [ENCRYPTED] ------->   |
     |   HDR, SK { N(DELETE) }                |
     |   [Requesting deletion of SA]          |
     |                                        |
     |<-- INFORMATIONAL [ENCRYPTED] --------  |
     |   HDR, SK {}                           |
     |   [Acknowledges deletion]              |
```

### IKEv2 Child SA Creation (CREATE_CHILD_SA)

After initial exchange, additional IPSec SAs (Child SAs) are created with:

```
Initiator (A)                           Responder (B)
     |                                        |
     |-- CREATE_CHILD_SA [ENCRYPTED] ----->   |
     |   HDR, SK { SA, Ni, [KEi], TSi, TSr }  |
     |                                        |
     |<-- CREATE_CHILD_SA [ENCRYPTED] ------  |
     |   HDR, SK { SA, Nr, [KEr], TSi, TSr }  |
     |                                        |
     |   === New Child SA established ===     |
```

### IKEv1 vs IKEv2 Comparison

```
Feature                  | IKEv1          | IKEv2
-------------------------|----------------|------------------
Messages (min)           | 9 (MM + QM)    | 4
Complexity               | High           | Lower
Identity Protection      | Phase 1 MM only| Always
Reliability              | No built-in    | Request/Response
MOBIKE support           | No             | Yes (RFC 4555)
EAP support              | No             | Yes
Multi-homing             | No             | Yes
DDoS resistance          | Basic cookie   | Enhanced cookie
Dead Peer Detection      | Extra RFC      | Built-in
Traffic selector narrowing| No            | Yes
Simultaneous use         | Discouraged    | Supported
```

---

## 12. Cryptographic Algorithms in IPSec

### 12.1 Encryption Algorithms

| Algorithm | Key Size | Mode | Status | Notes |
|---|---|---|---|---|
| 3DES-CBC | 168 bits | Block | Deprecated | Should not use |
| AES-CBC | 128/256 bits | Block | Common | Needs separate HMAC |
| AES-CTR | 128/256 bits | Stream | Less common | Needs separate HMAC |
| **AES-GCM** | 128/256 bits | AEAD | **Recommended** | Encrypt+Auth in one |
| AES-CCM | 128/256 bits | AEAD | Common | AEAD variant |
| ChaCha20-Poly1305 | 256 bits | AEAD | Modern | RFC 8439, software-friendly |

### 12.2 Integrity / Authentication Algorithms

| Algorithm | Output | Status | Notes |
|---|---|---|---|
| HMAC-MD5-96 | 96 bits | Deprecated | MD5 broken |
| HMAC-SHA1-96 | 96 bits | Legacy | SHA1 weakened |
| **HMAC-SHA256-128** | 128 bits | **Recommended** | Current standard |
| HMAC-SHA384-192 | 192 bits | Strong | |
| HMAC-SHA512-256 | 256 bits | Strong | |
| AES-XCBC-MAC-96 | 96 bits | Common | |
| AES-GCM (built-in) | Varies | **Recommended** | AEAD covers auth |

### 12.3 Diffie-Hellman Groups

| Group | Type | Bits | Status |
|---|---|---|---|
| Group 1 | MODP | 768 | **Broken** |
| Group 2 | MODP | 1024 | **Deprecated** |
| Group 5 | MODP | 1536 | Legacy |
| **Group 14** | MODP | 2048 | **Minimum recommended** |
| Group 15 | MODP | 3072 | Good |
| **Group 19** | ECP | 256 | **Recommended** (ECDH) |
| **Group 20** | ECP | 384 | **Recommended** (ECDH) |
| Group 21 | ECP | 521 | Strong |

**MODP** = Modular Exponential (classic DH)  
**ECP** = Elliptic Curve (ECDH, more efficient)

### 12.4 PRF (Pseudo-Random Functions)

| PRF | Status |
|---|---|
| PRF-HMAC-MD5 | Deprecated |
| PRF-HMAC-SHA1 | Legacy |
| **PRF-HMAC-SHA256** | **Recommended** |
| **PRF-HMAC-SHA384** | Strong |
| PRF-AES128-XCBC | Common |

### 12.5 Algorithm Negotiation Flow

```
Initiator proposes a list:
  SA Proposal {
    Transform 1: ENCR_AES_GCM_16 (key=256)
    Transform 2: ENCR_AES_CBC (key=256)
    Transform 3: PRF_HMAC_SHA2_256
    Transform 4: AUTH_HMAC_SHA2_256_128
    Transform 5: DH_GROUP_19
    Transform 6: DH_GROUP_14
  }

Responder picks one from each category:
  SA Accept {
    ENCR_AES_GCM_16 (key=256)
    PRF_HMAC_SHA2_256
    DH_GROUP_19
  }
  (AUTH not needed since AES-GCM is AEAD)
```

---

## 13. Packet Processing — Step by Step

### 13.1 Outbound Processing

```
Application Data
      |
      v
  +-------+
  |  TCP  |  (adds TCP header)
  +-------+
      |
      v
  +-------+
  |  IP   |  (adds IP header: src=A, dst=B)
  +-------+
      |
      v
  +------------+
  | Check SPD  |  (find policy for this packet)
  +------------+
      |
   PROTECT policy found
      |
      v
  +------------+
  | Find SA    |  (look up SAD for matching SA)
  | in SAD     |
  +------------+
      |
   SA found
      |
      v
  +-----------------+
  | Apply ESP/AH    |
  |                 |
  | For ESP Tunnel: |
  |  1. Add padding |
  |  2. Encrypt     |
  |     (payload +  |
  |      inner IP   |
  |      if tunnel) |
  |  3. Add SPI,    |
  |     SeqNum      |
  |  4. Compute ICV |
  |  5. Add outer   |
  |     IP header   |
  +-----------------+
      |
      v
  Transmit Packet
```

### 13.2 Inbound Processing

```
Receive Packet
      |
      v
  +------------------+
  | Is it AH or ESP? |  (Check IP Protocol field: 50=ESP, 51=AH)
  +------------------+
      |
      v
  +------------------+
  | Extract SPI      |  (from AH or ESP header)
  | from packet      |
  +------------------+
      |
      v
  +------------------+
  | Look up SAD      |  (using SPI + dst_IP + protocol)
  +------------------+
      |
   SA found (has keys and algorithms)
      |
      v
  +------------------+
  | Anti-Replay      |  (check sequence number against window)
  | Check            |
  +------------------+
      |
   Not a replay
      |
      v
  +------------------+
  | Verify ICV       |  (check HMAC/AEAD tag; drop if invalid)
  +------------------+
      |
   ICV valid
      |
      v
  +------------------+
  | Decrypt Payload  |  (if ESP with encryption)
  +------------------+
      |
      v
  +------------------+
  | Check SPD        |  (is this packet authorized to arrive?)
  +------------------+
      |
   Policy allows
      |
      v
  Deliver to Upper Layer (TCP/UDP → Application)
```

---

## 14. Real Protocol Packet Diagrams (ASCII)

### 14.1 Complete ESP Tunnel Mode Packet on the Wire

```
Original Packet (from Host A 192.168.1.10 to Host B 10.0.0.20):
+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
|Ver|IHL|TOS|    Total Length   |  Identification  |Flags| Frag |
|IP Header: src=192.168.1.10, dst=10.0.0.20, proto=TCP          |
+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
|TTL|Pro|    Header Checksum    |    Source IP (192.168.1.10)   |
+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
|         Destination IP (10.0.0.20)    |    TCP Src Port       |
+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
|       TCP Dst Port        |          Sequence Number          |
+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
|                 Acknowledgment Number                         |
+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
|   Application Data (HTTP, SSH, etc.)                          |
+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+

After ESP Tunnel Mode (Gateway GW1 → Gateway GW2):
Byte 0         4         8         12        16
|     |     |     |     |     |     |     |     |     |     |
+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
|Ver=4|IHL=5|TOS  |       Total Length      | Identification|
+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
|Flags|FragOff    |TTL  |Proto=50 (ESP)|  Header Checksum   |
+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
|            Source IP: GW1 (203.0.113.1)                   |
+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
|         Destination IP: GW2 (198.51.100.1)                |
+===================== ESP Header ==========================+
|           Security Parameters Index (SPI) e.g. 0x0000C6BA |
+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
|          Sequence Number (e.g., 00 00 27 10 = 10000)      |
+================= ESP IV (for CBC) or Nonce (for GCM) =====+
|    IV/Nonce: 8 or 12 bytes of random data                 |
|   (e.g., A3 F2 9B 1C 7E 44 D8 0F 22 B5 91 3A)             |
+================= ENCRYPTED PAYLOAD =======================+
|         [Original IP Header (192.168.1.10 → 10.0.0.20)]   |
|         [Original TCP Header (src:12345 dst:443)]         |
|         [HTTP Data: GET / HTTP/1.1...]                    |
|         ... all encrypted with AES-256-GCM ...            |
|         (nobody can see inner addresses or content)       |
+================= ESP Trailer =============================+
|                Padding (variable, 0-255 bytes)            |
+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
|  Pad Length   |  Next Header (4 = IPv4, inner packet)     |
+================= ICV (Authentication Tag) ================+
|    GCM Tag: 16 bytes (128 bits) e.g.,                     |
|    8F 3A 91 C2 4B D0 E7 F5 12 6A 88 C4 3D 97 B1 2E        |
+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
```

### 14.2 IKEv2 IKE_SA_INIT Message Format

```
IKEv2 Message: IKE_SA_INIT Request
+========================================================+
|                   IKE HEADER                           |
+-----+-----+-----+-----+-----+-----+-----+-----+-- -----+
| Initiator SPI (8 bytes, random)                        |
| e.g.: A1 B2 C3 D4 E5 F6 07 18                          |
+-----+-----+-----+-----+-----+-----+-----+-----+----- --+
| Responder SPI (8 bytes, zero for initial request)      |
| 00 00 00 00 00 00 00 00                                |
+-----+-----+-----+-----+-----+-----+-----+-----+---- ---+
|Next Payload|Vers|Exch Type|Flags|      Message ID      |
|  SA (33)   | 2.0| 34      | 0x08|      0x00000001      |
+-----+-----+-----+-----+-----+-----+-----+-----+----- --+
|                   Total Length                         |
+========================================================+
|               SA PAYLOAD (Security Associations)       |
+-----+-----+-----+-----+-----+-----+-----+-----+-------+
|Next |Critical|      SA Payload Length                  |
| KE  |   0   |                                          |
+-----+-----+-----+-----+-----+-----+-----+-----+--- ----+
|       PROPOSAL #1                                      |
|  Proposal Num | Protocol ID=IKE | SPI Size=0 | 4 Trans |
+-----+-----+-----+-----+-----+-----+-----+-----+---- ---+
| Transform 1: ENCR_AES_CBC (type=1, id=12) keylen=256   |
| Transform 2: PRF_HMAC_SHA2_256 (type=2, id=5)          |
| Transform 3: AUTH_HMAC_SHA2_256_128 (type=3, id=12)    |
| Transform 4: DH_GROUP_19 (type=4, id=19)               |
+========================================================+
|               KE PAYLOAD (Key Exchange)                |
+-----+-----+-----+-----+-----+-----+-----+-----+--- ----+
|Next |Critical|       KE Payload Length                 |
| Ni  |   0   |                                          |
+-----+-----+-----+-----+-----+-----+-----+-----+-- -----+
| DH Group: 19 |          RESERVED                       |
+-----+-----+-----+-----+-----+-----+-----+-----+---- ---+
| DH Public Key (g^a mod p), 64 bytes for Group 19       |
| 04 7B 2A 9C F1 3D 5E 8B ... (64 bytes of DH public key)|
+========================================================+
|               Ni PAYLOAD (Nonce)                       |
+-----+-----+-----+-----+-----+-----+-----+-----+----  ---+
|Next |Critical|       Nonce Payload Length              |
|  0  |   0   |                                          |
+-----+-----+-----+-----+-----+-----+-----+----- +-------+
| Nonce data (16-32 bytes of random):                    |
| 3F A8 C1 9D 72 B4 E6 01 5C 8A 2F 7E D3 94 B0 61        |
+========================================================+
```

### 14.3 AH Transport Mode Packet

```
Original IPv4 TCP Packet:
+------+----+----------+---------+-------+
|IP Hdr|    |TCP Header|TCP Data |       |
|20 B  |    | 20 B     | N B     |       |
+------+----+----------+---------+-------+

After AH (Transport Mode):
+-------+----------+----------+---------+
|IP Hdr |AH Header |TCP Header|TCP Data |
|(proto |          |          |         |
| =51)  |          |          |         |
+-------+----------+----------+---------+

AH Header Breakdown (24 bytes minimum):
Offset 0:  Next Header = 6 (TCP)   [1 byte]
Offset 1:  Payload Len = 4         [1 byte] (AH len in 32-bit words - 2)
Offset 2:  Reserved    = 0x0000    [2 bytes]
Offset 4:  SPI         = 0xDEAD   [4 bytes]
Offset 8:  Seq Num     = 0x00003A  [4 bytes] (58th packet)
Offset 12: ICV         =           [12 bytes] (HMAC-SHA1-96)
           8F 3D A1 22 C4 B5 9E 01 F7 2A 88 4C

ICV covers: zeroed mutable IP fields + AH header (ICV=0) + TCP Hdr + Data
```

### 14.4 Full IKEv2 Session Timeline

```
Time  Initiator                                        Responder
----  ---------                                        ---------
t=0   [Generate SPIi, Nonce_i, DH key pair (a, g^a)]
      
t=1   ---IKE_SA_INIT Req (msg_id=0)-------------------> 
         HDR(SPIi, 0), SAi1, KEi(g^a), Ni
      
      [Responder: picks algo, generates b,g^b, Nonce_r]
      [Computes: g^ab = shared_secret]
      [Derives: SKEYSEED, SK_ei/er/ai/ar/d/pi/pr]
      
t=2   <---IKE_SA_INIT Resp (msg_id=0)----------------
         HDR(SPIi, SPIr), SAr1, KEr(g^b), Nr
         [Optional: CERTREQ, N(COOKIE)]
      
      [Initiator also computes shared secret and all SKeys]
      
t=3   ---IKE_AUTH Req (msg_id=1) [ENCRYPTED with SK_ei/SK_ai]-->
         HDR(SPIi,SPIr), SK{ IDi, [CERT,] AUTH, 
                              SAi2, TSi, TSr }
         IDi  = identity of initiator
         AUTH = PRF(SK_pi, <signed data>)
         SAi2 = proposed Child SA algorithms
         TSi/r = Traffic Selectors (who talks to whom)
      
      [Responder: verifies AUTH, creates Child SA]
      
t=4   <---IKE_AUTH Resp (msg_id=1) [ENCRYPTED with SK_er/SK_ar]--
         HDR(SPIi,SPIr), SK{ IDr, [CERT,] AUTH,
                              SAr2, TSi, TSr }
      
      [Initiator: verifies AUTH, installs Child SA]
      
      === COMPLETE: IKE SA + First Child SA established ===
      
t=5   ---ESP DATA PACKET------------------------------------>
         [Encrypted application data begins flowing]
      
      <---ESP DATA PACKET------------------------------------
         [Bidirectional encrypted data flow]

      [Later: SA rekeying, deletion, DPD checks...]
      
t=3600 ---INFORMATIONAL (SA expiry approaching) ------------>
          [Trigger CREATE_CHILD_SA to rekey]
```

---

## 15. Anti-Replay Protection

### What Is Anti-Replay?

**Replay attack**: An attacker captures a legitimate IPSec packet and re-sends it later. Without protection, the receiver would process it again (e.g., re-execute a bank transfer command).

### How Anti-Replay Works

IPSec uses a **sliding window** mechanism based on sequence numbers:

```
Sender:
  - Maintains a 32-bit (or 64-bit extended) sequence number
  - Increments by 1 for every packet sent
  - Never reuses a sequence number within an SA lifetime
  - If counter wraps (reaches 2^32), must rekey

Receiver:
  - Maintains a sliding window (typically 64 or 128 bits wide)
  - Window represents "acceptable" sequence numbers
  - Right edge = highest sequence number seen so far
  - Left edge = right_edge - window_size + 1
```

### Sliding Window Visualization

```
Window size = 8 (simplified; real is 32-64 bits)
Right edge (W) = 12 (highest received)

    Left Edge        Right Edge
         |                |
         v                v
 SeqNum: 5  6  7  8  9  10 11 12  13  14
         [  1  0  1  1   0  1  1  1 ]
          ^received  ^received  ^received
          (1=received OK, 0=not yet received)

If new packet arrives with seq=7:  already in window AND bit=0 → ACCEPT (duplicate check)
If new packet arrives with seq=6:  already in window AND bit=1 → REJECT (replay!)
If new packet arrives with seq=4:  left of window → REJECT (too old, replay)
If new packet arrives with seq=13: right of window, advance window → ACCEPT
If new packet arrives with seq=20: advance window → ACCEPT (but check gap)
```

### Extended Sequence Numbers (ESN)

For high-speed links where 32-bit counters could wrap:
- **ESN** uses 64-bit sequence numbers
- Only lower 32 bits are sent in packet (saves 4 bytes)
- Receiver infers upper 32 bits from context
- Supports ~18 exabytes of data per SA without rekey

---

## 16. Dead Peer Detection (DPD)

### The Problem

What happens when a VPN peer crashes or loses connectivity without sending a proper "goodbye" message? The other side keeps the SA alive but traffic goes nowhere — a "zombie" SA.

### DPD Solution (RFC 3706)

**DPD** monitors whether the remote peer is still alive by sending periodic probes.

```
DPD Logic:
                  Has traffic been
                  received recently?
                       |
                    YES|          NO|
                       |            |
              [No DPD needed]   Send R-U-THERE probe
                                     |
                              Wait for response
                                     |
                         Got R-U-THERE-ACK?
                                  |
                              YES |       NO |
                                  |           |
                          [Peer is alive]  [Retry N times]
                                                 |
                                          [Delete SA, reconnect]
```

### DPD in IKEv2

IKEv2 has DPD built in via **empty INFORMATIONAL exchanges**:

```
Initiator:
  If no IKE or ESP traffic received for timeout period:
  Send: HDR, SK {}  [empty INFORMATIONAL request]

Responder:
  Send: HDR, SK {}  [empty INFORMATIONAL response]

If no response after N retries:
  Declare peer dead, delete IKE SA + all Child SAs
```

---

## 17. NAT Traversal (NAT-T)

### The Problem: NAT Breaks IPSec AH

NAT (Network Address Translation) changes IP addresses in packet headers. This breaks AH because AH authenticates the IP header — any change makes authentication fail.

NAT also changes UDP/TCP port numbers, which can cause issues for ESP.

### Solution: NAT-T (RFC 3948)

**NAT-T encapsulates ESP packets inside UDP port 4500**, allowing NAT to work normally on the UDP header while ESP data passes through unchanged.

```
Normal ESP over IP:
+----------+------------+------------------+
| IP Header| ESP Header | Encrypted Data   |
| Proto=50 |            |                  |
+----------+------------+------------------+

ESP with NAT-T (UDP Encapsulation):
+----------+------------+------------+------------------+
| IP Header| UDP Header | ESP Header | Encrypted Data   |
| Proto=17 | Port=4500  |            |                  |
+----------+------------+------------+------------------+
              ^^^^^^^
              NAT can modify this UDP header without
              breaking the authenticated ESP content
```

### NAT Detection in IKEv2

During IKE_SA_INIT, both peers include **NAT_DETECTION_SOURCE_IP** and **NAT_DETECTION_DESTINATION_IP** notifications containing hashes of their IP+port.

```
NAT_DETECTION_SOURCE_IP = HASH(SPIi | SPIr | IP_src | Port_src)

If the hash received by the other side doesn't match what they computed:
  → NAT is present → Enable NAT-T → Switch to UDP 4500
```

### NAT Keepalives

When NAT-T is active, the client must send keepalive packets to prevent NAT mapping expiry:

```
Every 20 seconds (configurable):
  Send a single byte 0xFF to the VPN server on UDP port 4500
  
  This refreshes the NAT binding table entry
  keeping the NAT mapping alive even during idle periods
```

---

## 18. Perfect Forward Secrecy (PFS)

### What Is Forward Secrecy?

**Forward Secrecy** (also called Perfect Forward Secrecy, PFS) means: **if long-term keys are compromised in the future, past sessions cannot be decrypted**.

### The Problem Without PFS

```
Without PFS:
  Session keys = f(long-term PSK or private key)
  
  If attacker records all encrypted traffic today,
  and obtains PSK/private key years later:
  → Can decrypt ALL past recorded sessions!
```

### PFS Solution

```
With PFS:
  For each session: generate fresh DH key pair
  Session key = f(ephemeral DH shared secret, ...)
  After session ends: ephemeral DH keys are deleted
  
  Even if long-term key is later compromised:
  → Ephemeral keys are gone → Past sessions CANNOT be decrypted
```

### How PFS Works in IPSec

**In IKEv1 Phase 2 (Quick Mode):**
- Without PFS: Child SA keys derived from Phase 1 key material
- With PFS: New DH exchange in Phase 2 → fresh key material → keys not derivable from Phase 1

**In IKEv2 CREATE_CHILD_SA:**
- Include `KEi` in request → triggers fresh DH → PFS achieved

```
Without PFS:
  Child SA Key = PRF(SK_d, Ni | Nr)
  (SK_d is derived once in initial exchange)

With PFS:
  Child SA Key = PRF(SK_d, g^ir | Ni | Nr)
  (g^ir is fresh DH from new key exchange)
  (Each Child SA has unique, independent key)
```

---

## 19. IPSec in Practice — VPN Use Cases

### 19.1 Site-to-Site VPN

Connect two office networks through the Internet:

```
                        Internet
  Office A            (Untrusted)           Office B
  --------          /           \           --------
  Host1  \         /             \         / Host3
  Host2  -+----- GW1 =========== GW2 ----+- Host4
  Host3  /         \  ESP Tunnel  /         \ Host5
  --------          \           /           --------
10.0.1.0/24          \         /           10.0.2.0/24
                   203.0.113.1-198.51.100.1
                   (Public IPs, tunnel endpoints)

Traffic: Host1 (10.0.1.10) → Host3 (10.0.2.30)
  1. Host1 sends packet to 10.0.2.30
  2. GW1 intercepts (per SPD policy), creates ESP tunnel packet
  3. Outer IP: 203.0.113.1 → 198.51.100.1
  4. Inner IP (encrypted): 10.0.1.10 → 10.0.2.30
  5. Travels through Internet to GW2
  6. GW2 decrypts, delivers to Host3
```

### 19.2 Remote Access VPN

Remote worker connects to corporate network:

```
                        Internet
Remote Worker           (Untrusted)         Corporate Network
   Laptop             /           \           -----------
   Client ----[4G/WiFi] =========== VPN GW --+-- Servers
   10.10.1.5          \  ESP Tunnel /           +-- DB
                       \           /           10.0.0.0/16
                    VPN assigns virtual IP
                    to laptop: 10.10.1.5
                    (appears as corporate host)
```

### 19.3 Host-to-Host IPSec

Two servers communicate directly with IPSec (Transport Mode):

```
  Server A (192.168.1.10)       Server B (192.168.1.20)
       |                               |
       +---[ESP Transport Mode]--------+
           (Only payload encrypted;
            IP headers visible to LAN)
       
  Use Case: Database server → App server encryption
            within a data center
```

---

## 20. C Implementation

### 20.1 Core Data Structures

```c
/* ipsec_types.h */
#ifndef IPSEC_TYPES_H
#define IPSEC_TYPES_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>
#include <arpa/inet.h>

/* ============================================================
 * CONSTANTS
 * ============================================================ */
#define IPSEC_MAX_KEY_LEN        64    /* 512 bits max key */
#define IPSEC_REPLAY_WINDOW_SIZE 64    /* 64-bit sliding window */
#define IPSEC_MAX_SPI            0xFFFFFFFF
#define IPSEC_AH_PROTOCOL        51
#define IPSEC_ESP_PROTOCOL       50
#define IPSEC_IKE_PORT           500
#define IPSEC_NATT_PORT          4500
#define IPSEC_NONCE_MIN_LEN      16
#define IPSEC_NONCE_MAX_LEN      256

/* ============================================================
 * ENUMERATIONS
 * ============================================================ */

/* IPSec Protocol */
typedef enum {
    IPSEC_PROTO_AH  = 51,  /* Authentication Header */
    IPSEC_PROTO_ESP = 50,  /* Encapsulating Security Payload */
} ipsec_protocol_t;

/* IPSec Mode */
typedef enum {
    IPSEC_MODE_TRANSPORT = 1,  /* Transport mode: protect payload only */
    IPSEC_MODE_TUNNEL    = 2,  /* Tunnel mode: protect entire packet */
} ipsec_mode_t;

/* Encryption algorithms */
typedef enum {
    ENCR_NULL         = 11,  /* No encryption */
    ENCR_3DES_CBC     = 3,   /* Triple DES CBC (deprecated) */
    ENCR_AES_CBC      = 12,  /* AES CBC */
    ENCR_AES_CTR      = 13,  /* AES Counter mode */
    ENCR_AES_GCM_8    = 18,  /* AES GCM with 8-byte ICV */
    ENCR_AES_GCM_12   = 19,  /* AES GCM with 12-byte ICV */
    ENCR_AES_GCM_16   = 20,  /* AES GCM with 16-byte ICV */
    ENCR_CHACHA20_POLY = 28, /* ChaCha20-Poly1305 */
} encr_algo_t;

/* Integrity/Authentication algorithms */
typedef enum {
    AUTH_NONE              = 0,   /* AEAD handles auth */
    AUTH_HMAC_MD5_96       = 1,   /* HMAC-MD5 with 96-bit ICV (deprecated) */
    AUTH_HMAC_SHA1_96      = 2,   /* HMAC-SHA1 with 96-bit ICV */
    AUTH_AES_XCBC_96       = 5,   /* AES-XCBC-MAC-96 */
    AUTH_HMAC_SHA256_128   = 12,  /* HMAC-SHA256 with 128-bit ICV */
    AUTH_HMAC_SHA384_192   = 13,  /* HMAC-SHA384 with 192-bit ICV */
    AUTH_HMAC_SHA512_256   = 14,  /* HMAC-SHA512 with 256-bit ICV */
} auth_algo_t;

/* DH Groups */
typedef enum {
    DH_GROUP_MODP_1024 = 2,   /* 1024-bit MODP (deprecated) */
    DH_GROUP_MODP_2048 = 14,  /* 2048-bit MODP */
    DH_GROUP_ECP_256   = 19,  /* 256-bit ECP (ECDH P-256) */
    DH_GROUP_ECP_384   = 20,  /* 384-bit ECP (ECDH P-384) */
    DH_GROUP_ECP_521   = 21,  /* 521-bit ECP (ECDH P-521) */
} dh_group_t;

/* SA Direction */
typedef enum {
    SA_DIR_INBOUND  = 0,
    SA_DIR_OUTBOUND = 1,
} sa_direction_t;

/* SPD Action */
typedef enum {
    SPD_ACTION_BYPASS  = 1,  /* Pass packet without IPSec */
    SPD_ACTION_DISCARD = 2,  /* Drop packet */
    SPD_ACTION_PROTECT = 3,  /* Apply IPSec */
} spd_action_t;

/* ============================================================
 * IP HEADER STRUCTURES
 * ============================================================ */

/* IPv4 Header (20 bytes, no options) */
typedef struct __attribute__((packed)) {
    uint8_t  ihl_ver;        /* Version (4 bits) + IHL (4 bits) */
    uint8_t  tos;            /* Type of Service */
    uint16_t total_length;   /* Total packet length */
    uint16_t id;             /* Identification */
    uint16_t flags_frag;     /* Flags (3 bits) + Fragment Offset (13 bits) */
    uint8_t  ttl;            /* Time to Live */
    uint8_t  protocol;       /* Protocol (TCP=6, UDP=17, AH=51, ESP=50) */
    uint16_t checksum;       /* Header checksum */
    uint32_t src_ip;         /* Source IP address */
    uint32_t dst_ip;         /* Destination IP address */
} ipv4_hdr_t;

/* AH Header (RFC 4302) */
typedef struct __attribute__((packed)) {
    uint8_t  next_header;    /* Protocol of protected data */
    uint8_t  payload_len;    /* AH length in 32-bit words - 2 */
    uint16_t reserved;       /* Must be zero */
    uint32_t spi;            /* Security Parameters Index */
    uint32_t seq_num;        /* Sequence number (anti-replay) */
    /* Followed by ICV (variable length, 12 or 16 bytes) */
} ah_hdr_t;

/* ESP Header (RFC 4303) */
typedef struct __attribute__((packed)) {
    uint32_t spi;            /* Security Parameters Index */
    uint32_t seq_num;        /* Sequence number (anti-replay) */
    /* Followed by: IV, Encrypted Payload, Padding, Pad Len, Next Hdr, ICV */
} esp_hdr_t;

/* ESP Trailer (after encrypted payload) */
typedef struct __attribute__((packed)) {
    uint8_t pad_len;         /* Number of padding bytes */
    uint8_t next_header;     /* Protocol of original payload */
} esp_trailer_t;

/* ============================================================
 * CRYPTO CONTEXT
 * ============================================================ */

typedef struct {
    encr_algo_t algo;
    uint8_t     key[IPSEC_MAX_KEY_LEN];
    size_t      key_len;       /* Key length in bytes */
    size_t      iv_len;        /* IV/Nonce length */
    size_t      icv_len;       /* ICV/Tag length */
} encr_ctx_t;

typedef struct {
    auth_algo_t algo;
    uint8_t     key[IPSEC_MAX_KEY_LEN];
    size_t      key_len;
    size_t      icv_len;       /* Truncated HMAC output length */
} auth_ctx_t;

/* ============================================================
 * ANTI-REPLAY WINDOW
 * ============================================================ */

typedef struct {
    uint32_t  right_edge;         /* Highest sequence number seen */
    uint64_t  bitmap;             /* 64-bit sliding window bitmap */
    bool      enabled;
} replay_window_t;

/* ============================================================
 * SECURITY ASSOCIATION (SA)
 * ============================================================ */

typedef struct {
    /* Identity */
    uint32_t        spi;          /* Security Parameter Index */
    ipsec_protocol_t protocol;    /* AH or ESP */
    ipsec_mode_t    mode;         /* Transport or Tunnel */
    sa_direction_t  direction;

    /* Tunnel endpoints (for tunnel mode) */
    uint32_t        tunnel_src;   /* Outer IP source */
    uint32_t        tunnel_dst;   /* Outer IP destination */

    /* Crypto contexts */
    encr_ctx_t      encr;         /* Encryption */
    auth_ctx_t      auth;         /* Authentication */

    /* Anti-replay */
    replay_window_t replay;

    /* Sequence number (outbound) */
    uint32_t        seq_num;

    /* Lifetime */
    uint64_t        lifetime_bytes;     /* Bytes remaining */
    uint32_t        lifetime_seconds;   /* Seconds remaining */
    time_t          created_at;

    /* State */
    bool            valid;

    /* Linked list for SAD */
    struct ipsec_sa *next;
} ipsec_sa_t;

/* ============================================================
 * TRAFFIC SELECTOR
 * ============================================================ */

typedef struct {
    uint8_t  type;          /* TS_IPV4_ADDR_RANGE = 7 */
    uint8_t  ip_proto;      /* 0 = any, 6 = TCP, 17 = UDP */
    uint16_t port_start;    /* Start of port range */
    uint16_t port_end;      /* End of port range */
    uint32_t ip_start;      /* Start of IP range */
    uint32_t ip_end;        /* End of IP range */
} traffic_selector_t;

/* ============================================================
 * SECURITY POLICY DATABASE ENTRY (SPD)
 * ============================================================ */

typedef struct {
    /* Traffic selector (what traffic this policy matches) */
    uint32_t src_ip;
    uint32_t src_mask;
    uint32_t dst_ip;
    uint32_t dst_mask;
    uint8_t  protocol;        /* 0=any, 6=TCP, 17=UDP */
    uint16_t src_port;        /* 0=any */
    uint16_t dst_port;        /* 0=any */

    /* Action */
    spd_action_t action;

    /* If PROTECT: SA template */
    ipsec_protocol_t sa_protocol;
    ipsec_mode_t     sa_mode;
    encr_algo_t      sa_encr;
    auth_algo_t      sa_auth;

    /* Pointer to associated SA (NULL if not yet established) */
    ipsec_sa_t *sa;

    /* Next policy (linked list, priority ordered) */
    struct spd_entry *next;
} spd_entry_t;

#endif /* IPSEC_TYPES_H */
```

### 20.2 Anti-Replay Window Implementation

```c
/* anti_replay.c */
#include "ipsec_types.h"
#include <stdio.h>

/*
 * Initialize the anti-replay window.
 * Right edge starts at 0, bitmap is empty.
 */
void replay_window_init(replay_window_t *win) {
    win->right_edge = 0;
    win->bitmap = 0;
    win->enabled = true;
}

/*
 * Check if a received sequence number is valid (not replayed).
 *
 * Returns: true  = packet should be accepted
 *          false = packet is replayed, reject it
 *
 * The sliding window works as follows:
 *   - right_edge: highest valid sequence number seen
 *   - Window covers: [right_edge - 63, right_edge]
 *   - bitmap bit N: whether seq (right_edge - N) was received
 *
 * Cases:
 *   1. seq > right_edge: New highest, advance window
 *   2. seq in window: Check bit (not seen = OK, seen = replay)
 *   3. seq < window_left: Too old, reject
 */
bool replay_check(replay_window_t *win, uint32_t seq) {
    if (!win->enabled) return true;

    /* Case 1: Sequence number is ahead of window right edge */
    if (seq > win->right_edge) {
        uint32_t shift = seq - win->right_edge;
        if (shift >= 64) {
            /* Window slides entirely; reset bitmap */
            win->bitmap = 0;
        } else {
            /* Shift window: old bits move left, new area = 0 */
            win->bitmap <<= shift;
        }
        win->right_edge = seq;
        /* Mark the new highest as received */
        win->bitmap |= 1ULL;  /* bit 0 = right_edge */
        return true;
    }

    /* Case 2: Sequence number is within window */
    uint32_t diff = win->right_edge - seq;
    if (diff < 64) {
        uint64_t bit_mask = (1ULL << diff);
        if (win->bitmap & bit_mask) {
            /* Already received: REPLAY! */
            return false;
        }
        /* Not yet received: mark and accept */
        win->bitmap |= bit_mask;
        return true;
    }

    /* Case 3: Sequence number is too far behind window */
    return false;  /* Reject: too old */
}

/*
 * Convenience test - does NOT update the window.
 * Used for initial check before verifying ICV.
 * Only update window (replay_check) after ICV passes.
 */
bool replay_peek(const replay_window_t *win, uint32_t seq) {
    if (!win->enabled) return true;
    if (seq > win->right_edge) return true;  /* Ahead of window */
    uint32_t diff = win->right_edge - seq;
    if (diff >= 64) return false;           /* Too old */
    return !(win->bitmap & (1ULL << diff)); /* Not yet seen */
}

/* Demo of anti-replay logic */
void replay_demo(void) {
    replay_window_t win;
    replay_window_init(&win);

    uint32_t test_seqs[] = {1, 2, 3, 10, 5, 4, 3, 100, 1};
    int n = sizeof(test_seqs) / sizeof(test_seqs[0]);

    printf("Anti-Replay Window Demo (window_size=64)\n");
    printf("%-12s %-12s\n", "SeqNum", "Result");
    printf("%-12s %-12s\n", "------", "------");

    for (int i = 0; i < n; i++) {
        bool ok = replay_check(&win, test_seqs[i]);
        printf("%-12u %-12s\n",
               test_seqs[i],
               ok ? "ACCEPT" : "REJECT (replay)");
    }
}
```

### 20.3 ESP Packet Construction

```c
/* esp.c - ESP packet construction and parsing */
#include "ipsec_types.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

/* We use OpenSSL for crypto in this example */
/* #include <openssl/evp.h> */

/*
 * Compute amount of padding needed for block alignment.
 *
 * ESP requires the payload to be aligned to the cipher block size.
 * Also, the pad_len and next_header fields (2 bytes) must end on a
 * 4-byte boundary.
 *
 * total_pad = ((payload_len + 2 + block_size - 1) / block_size * block_size)
 *             - payload_len - 2
 */
static size_t compute_padding(size_t payload_len, size_t block_size) {
    if (block_size == 0) block_size = 4;  /* Minimum 4-byte alignment */
    size_t with_trailer = payload_len + 2;  /* +2 for pad_len + next_hdr */
    size_t aligned = ((with_trailer + block_size - 1) / block_size) * block_size;
    return aligned - with_trailer;
}

/*
 * Build ESP packet layout (WITHOUT actual encryption - that requires crypto lib).
 * This shows the structure building logic.
 *
 * Layout of final ESP packet (in tunnel mode):
 * [Outer IPv4 Hdr][ESP Hdr (SPI+Seq)][IV][Encrypted(Inner IP Pkt + Padding + Trailer)][ICV]
 *
 * Parameters:
 *   sa          - Security Association (has keys, algo, SPI)
 *   inner_pkt   - Original IP packet to protect
 *   inner_len   - Length of original IP packet
 *   out_buf     - Output buffer for the ESP packet
 *   out_len     - [in] size of out_buf, [out] actual ESP packet length
 *   outer_src   - Outer source IP (tunnel mode: GW1 IP)
 *   outer_dst   - Outer destination IP (tunnel mode: GW2 IP)
 *
 * Returns: 0 on success, -1 on error
 */
int esp_encrypt_tunnel(
    ipsec_sa_t *sa,
    const uint8_t *inner_pkt,
    size_t inner_len,
    uint8_t *out_buf,
    size_t *out_len,
    uint32_t outer_src,
    uint32_t outer_dst
) {
    if (!sa || !inner_pkt || !out_buf || !out_len) return -1;
    if (sa->protocol != IPSEC_PROTO_ESP) return -1;

    /* --- Determine sizes --- */
    size_t iv_len      = sa->encr.iv_len;   /* e.g., 12 for AES-GCM */
    size_t icv_len     = sa->encr.icv_len;  /* e.g., 16 for AES-GCM-16 */
    size_t block_size  = 16;                /* AES block size */

    /* Plaintext = inner_pkt (for tunnel mode: entire IP packet) */
    size_t plaintext_len = inner_len;

    /* Compute padding */
    size_t pad_len = compute_padding(plaintext_len, block_size);

    /* Total encrypted region length */
    size_t ciphertext_len = plaintext_len + pad_len + 2; /* 2 = pad_len + next_hdr */

    /* Total ESP packet size */
    size_t esp_pkt_len = sizeof(ipv4_hdr_t)   /* Outer IP header */
                       + sizeof(esp_hdr_t)     /* SPI + SeqNum */
                       + iv_len                /* IV/Nonce */
                       + ciphertext_len        /* Encrypted payload */
                       + icv_len;             /* ICV / Auth Tag */

    if (*out_len < esp_pkt_len) {
        fprintf(stderr, "Output buffer too small: need %zu, have %zu\n",
                esp_pkt_len, *out_len);
        return -1;
    }

    /* --- Pointer arithmetic to lay out the packet --- */
    uint8_t *p = out_buf;

    /* 1. Outer IPv4 Header */
    ipv4_hdr_t *outer_ip = (ipv4_hdr_t *)p;
    p += sizeof(ipv4_hdr_t);

    outer_ip->ihl_ver      = 0x45;  /* IPv4, IHL=5 (20 bytes, no options) */
    outer_ip->tos          = 0;
    outer_ip->total_length = htons((uint16_t)esp_pkt_len);
    outer_ip->id           = htons(0);  /* Set by OS normally */
    outer_ip->flags_frag   = 0;
    outer_ip->ttl          = 64;
    outer_ip->protocol     = IPSEC_ESP_PROTOCOL;  /* 50 */
    outer_ip->checksum     = 0;  /* Computed later */
    outer_ip->src_ip       = htonl(outer_src);
    outer_ip->dst_ip       = htonl(outer_dst);

    /* 2. ESP Header: SPI + Sequence Number */
    esp_hdr_t *esp_hdr = (esp_hdr_t *)p;
    p += sizeof(esp_hdr_t);

    sa->seq_num++;  /* Increment sequence number */
    esp_hdr->spi     = htonl(sa->spi);
    esp_hdr->seq_num = htonl(sa->seq_num);

    /* 3. IV (Initialization Vector) — must be random! */
    uint8_t *iv = p;
    p += iv_len;
    /* In production: use OS CSPRNG */
    /* getrandom(iv, iv_len, 0); */
    /* For demo: fill with pattern */
    for (size_t i = 0; i < iv_len; i++) iv[i] = (uint8_t)(0xAA + i);

    /* 4. Build plaintext buffer (for encryption) */
    /* Layout: [inner_pkt | padding bytes | pad_len | next_header] */
    uint8_t *plaintext_buf = malloc(ciphertext_len);
    if (!plaintext_buf) return -1;

    uint8_t *pb = plaintext_buf;

    /* Copy inner (original) IP packet */
    memcpy(pb, inner_pkt, inner_len);
    pb += inner_len;

    /* Add padding: RFC says padding can be 1,2,3,...,pad_len */
    for (size_t i = 0; i < pad_len; i++) {
        *pb++ = (uint8_t)(i + 1);  /* RFC-recommended: 01,02,03,... */
    }

    /* ESP trailer */
    *pb++ = (uint8_t)pad_len;     /* Pad length field */
    *pb++ = 4;                    /* Next Header: 4 = IPv4 (tunnel mode) */
                                  /* 6=TCP for transport mode */

    /* 5. Encrypt plaintext into out_buf (after IV) */
    uint8_t *ciphertext = p;
    p += ciphertext_len;

    /*
     * HERE: call your crypto library
     * Example with AES-GCM (pseudocode):
     *
     * aad = pointer to esp_hdr (SPI + SeqNum) -- authenticated but not encrypted
     * aad_len = sizeof(esp_hdr_t)
     *
     * EVP_EncryptInit(ctx, EVP_aes_256_gcm(), sa->encr.key, iv);
     * EVP_EncryptUpdate(ctx, NULL, &len, aad, aad_len);  // AAD
     * EVP_EncryptUpdate(ctx, ciphertext, &len, plaintext_buf, ciphertext_len);
     * EVP_EncryptFinal(ctx, ...);
     * EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_GET_TAG, 16, icv_out);
     *
     * For now: copy plaintext (no real encryption in this demo)
     */
    memcpy(ciphertext, plaintext_buf, ciphertext_len);
    free(plaintext_buf);

    /* 6. ICV (Authentication Tag) — filled by AEAD or separate HMAC */
    uint8_t *icv = p;
    p += icv_len;
    /* In production: filled by EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_GET_TAG, ...) */
    memset(icv, 0xBB, icv_len);  /* Placeholder */

    *out_len = esp_pkt_len;
    return 0;
}

/*
 * ESP Inbound Processing (Decryption + Verification)
 *
 * Steps:
 *   1. Parse outer IP header
 *   2. Extract SPI from ESP header
 *   3. Look up SA in SAD (not shown, requires SAD lookup)
 *   4. Check anti-replay (peek)
 *   5. Verify ICV (authenticate before decrypt — Encrypt-then-MAC)
 *   6. Decrypt ciphertext
 *   7. Update anti-replay window
 *   8. Strip ESP header/trailer, extract inner packet
 *   9. Verify SPD policy allows this traffic
 */
int esp_decrypt_tunnel(
    ipsec_sa_t *sa,
    const uint8_t *esp_pkt,
    size_t esp_len,
    uint8_t *inner_pkt,
    size_t *inner_len
) {
    if (!sa || !esp_pkt || !inner_pkt || !inner_len) return -1;

    const uint8_t *p = esp_pkt;

    /* 1. Skip outer IP header */
    const ipv4_hdr_t *outer_ip = (const ipv4_hdr_t *)p;
    size_t ip_hdr_len = (outer_ip->ihl_ver & 0x0F) * 4;
    p += ip_hdr_len;

    /* 2. Parse ESP header */
    const esp_hdr_t *esp_hdr = (const esp_hdr_t *)p;
    p += sizeof(esp_hdr_t);

    uint32_t spi     = ntohl(esp_hdr->spi);
    uint32_t seq_num = ntohl(esp_hdr->seq_num);

    (void)spi;  /* Used for SAD lookup in real implementation */

    /* 3. Anti-replay peek (before expensive crypto) */
    if (!replay_peek(&sa->replay, seq_num)) {
        fprintf(stderr, "ESP: Replayed packet (seq=%u), dropping\n", seq_num);
        return -1;
    }

    size_t iv_len  = sa->encr.iv_len;
    size_t icv_len = sa->encr.icv_len;

    /* Compute encrypted region length */
    size_t header_overhead = ip_hdr_len + sizeof(esp_hdr_t) + iv_len;
    if (esp_len <= header_overhead + icv_len) {
        fprintf(stderr, "ESP: Packet too short\n");
        return -1;
    }
    size_t ciphertext_len = esp_len - header_overhead - icv_len;

    /* Parse IV */
    const uint8_t *iv = p;
    p += iv_len;

    /* Ciphertext region */
    const uint8_t *ciphertext = p;
    p += ciphertext_len;

    /* ICV */
    const uint8_t *icv = p;
    (void)icv;  /* Used in crypto verify */

    /*
     * 4. Verify ICV (in AEAD: this happens during decryption)
     * 5. Decrypt
     *
     * EVP_DecryptInit(ctx, EVP_aes_256_gcm(), sa->encr.key, iv);
     * EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_SET_TAG, 16, (void*)icv);
     * EVP_DecryptUpdate(ctx, NULL, &len, esp_hdr, sizeof(esp_hdr_t));  // AAD
     * EVP_DecryptUpdate(ctx, plaintext, &len, ciphertext, ciphertext_len);
     * int verify = EVP_DecryptFinal(ctx, ...);
     * if (verify <= 0) { reject! }
     */

    /* For demo: copy ciphertext as plaintext */
    uint8_t *plaintext = malloc(ciphertext_len);
    if (!plaintext) return -1;
    memcpy(plaintext, ciphertext, ciphertext_len);

    /* 6. Parse ESP trailer from end of plaintext */
    /* Layout: [inner_pkt | padding | pad_len | next_hdr] */
    if (ciphertext_len < 2) { free(plaintext); return -1; }

    uint8_t pad_len     = plaintext[ciphertext_len - 2];
    uint8_t next_header = plaintext[ciphertext_len - 1];
    (void)next_header;

    size_t actual_inner_len = ciphertext_len - pad_len - 2;
    if (actual_inner_len > *inner_len) {
        free(plaintext);
        return -1;
    }

    /* 7. Update anti-replay window (only after successful ICV verification!) */
    replay_check(&sa->replay, seq_num);

    /* 8. Copy inner packet */
    memcpy(inner_pkt, plaintext, actual_inner_len);
    *inner_len = actual_inner_len;
    free(plaintext);

    /* Update lifetime counter */
    if (sa->lifetime_bytes > 0) {
        sa->lifetime_bytes -= esp_len;
    }

    return 0;
}
```

### 20.4 SPD Policy Matching

```c
/* spd.c - Security Policy Database */
#include "ipsec_types.h"
#include <stdio.h>
#include <stdlib.h>

/* Simple linked list SPD (production: use radix tree or hash) */
static spd_entry_t *spd_head = NULL;

/* Add a policy to SPD (at end of list) */
void spd_add_policy(spd_entry_t *entry) {
    entry->next = NULL;
    if (!spd_head) {
        spd_head = entry;
        return;
    }
    spd_entry_t *cur = spd_head;
    while (cur->next) cur = (spd_entry_t *)cur->next;
    cur->next = (struct spd_entry *)entry;
}

/*
 * Match a packet against SPD.
 * Returns the matching policy action, or SPD_ACTION_BYPASS if no match.
 * Also fills *matched_sa with the SA pointer if action is PROTECT.
 *
 * src_ip, dst_ip: network byte order
 */
spd_action_t spd_lookup(
    uint32_t src_ip, uint32_t dst_ip,
    uint8_t protocol,
    uint16_t src_port, uint16_t dst_port,
    ipsec_sa_t **matched_sa
) {
    if (matched_sa) *matched_sa = NULL;

    for (spd_entry_t *e = spd_head; e; e = (spd_entry_t *)e->next) {
        /* Match source IP (network byte order, with mask) */
        if ((ntohl(src_ip) & ntohl(e->src_mask)) !=
            (ntohl(e->src_ip) & ntohl(e->src_mask))) continue;

        /* Match destination IP */
        if ((ntohl(dst_ip) & ntohl(e->dst_mask)) !=
            (ntohl(e->dst_ip) & ntohl(e->dst_mask))) continue;

        /* Match protocol (0 = any) */
        if (e->protocol != 0 && e->protocol != protocol) continue;

        /* Match source port (0 = any) */
        if (e->src_port != 0 && e->src_port != src_port) continue;

        /* Match destination port (0 = any) */
        if (e->dst_port != 0 && e->dst_port != dst_port) continue;

        /* Policy matched */
        if (matched_sa && e->action == SPD_ACTION_PROTECT) {
            *matched_sa = e->sa;
        }
        return e->action;
    }

    return SPD_ACTION_BYPASS;  /* Default: bypass if no policy matches */
}

/* Setup example policies */
void spd_setup_example(void) {
    /* Policy 1: Protect all traffic between 192.168.1.0/24 and 10.0.0.0/8 */
    spd_entry_t *p1 = calloc(1, sizeof(spd_entry_t));
    p1->src_ip    = inet_addr("192.168.1.0");
    p1->src_mask  = inet_addr("255.255.255.0");
    p1->dst_ip    = inet_addr("10.0.0.0");
    p1->dst_mask  = inet_addr("255.0.0.0");
    p1->protocol  = 0;     /* Any protocol */
    p1->src_port  = 0;     /* Any port */
    p1->dst_port  = 0;     /* Any port */
    p1->action    = SPD_ACTION_PROTECT;
    p1->sa_protocol = IPSEC_PROTO_ESP;
    p1->sa_mode   = IPSEC_MODE_TUNNEL;
    p1->sa_encr   = ENCR_AES_GCM_16;
    p1->sa_auth   = AUTH_NONE;  /* AES-GCM provides auth */
    spd_add_policy(p1);

    /* Policy 2: Discard all other traffic to 10.0.0.0/8 */
    spd_entry_t *p2 = calloc(1, sizeof(spd_entry_t));
    p2->src_ip    = 0;
    p2->src_mask  = 0;
    p2->dst_ip    = inet_addr("10.0.0.0");
    p2->dst_mask  = inet_addr("255.0.0.0");
    p2->protocol  = 0;
    p2->src_port  = 0;
    p2->dst_port  = 0;
    p2->action    = SPD_ACTION_DISCARD;
    spd_add_policy(p2);
}
```

### 20.5 IP Checksum

```c
/* ip_checksum.c */
#include <stdint.h>
#include <stddef.h>

/*
 * Compute Internet Checksum (RFC 1071).
 * Used for IP header checksum.
 * Sum 16-bit words, fold carries into 16 bits, take one's complement.
 */
uint16_t ip_checksum(const void *buf, size_t len) {
    const uint16_t *ptr = (const uint16_t *)buf;
    uint32_t sum = 0;

    /* Sum all 16-bit words */
    while (len > 1) {
        sum += *ptr++;
        len -= 2;
    }

    /* If odd number of bytes, pad with zero byte */
    if (len == 1) {
        sum += *(const uint8_t *)ptr;
    }

    /* Fold 32-bit sum to 16 bits */
    while (sum >> 16) {
        sum = (sum & 0xFFFF) + (sum >> 16);
    }

    /* One's complement */
    return (uint16_t)(~sum);
}
```

---

## 21. Rust Implementation

### 21.1 Core Types and Structures

```rust
// ipsec_types.rs

use std::net::Ipv4Addr;
use std::time::{Duration, Instant};

// ============================================================
// ENUMERATIONS
// ============================================================

/// IPSec Protocol: which protocol protects the data
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum IpsecProtocol {
    Ah  = 51,  // Authentication Header
    Esp = 50,  // Encapsulating Security Payload
}

/// IPSec Mode: how the packet is encapsulated
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum IpsecMode {
    Transport, // Protect payload only; IP header unchanged
    Tunnel,    // Protect entire original packet; new IP header added
}

/// Encryption algorithms (IANA transform IDs)
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum EncrAlgo {
    Null          = 11,
    AesCbc128     = 12,
    AesCbc256     = 12,  // distinguished by key length
    AesGcm16      = 20,  // AES-GCM with 16-byte ICV (AEAD)
    ChaCha20Poly  = 28,  // ChaCha20-Poly1305 (AEAD)
}

/// Authentication/Integrity algorithms
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AuthAlgo {
    None          = 0,   // AEAD handles auth
    HmacSha1_96   = 2,
    HmacSha256_128 = 12,
    HmacSha384_192 = 13,
    HmacSha512_256 = 14,
}

/// Diffie-Hellman Groups
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DhGroup {
    Modp2048 = 14,  // 2048-bit MODP (minimum recommended)
    Ecp256   = 19,  // 256-bit ECP (P-256, recommended)
    Ecp384   = 20,  // 384-bit ECP (P-384)
}

/// Security Policy Database action
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SpdAction {
    Bypass,   // Forward without IPSec
    Discard,  // Drop the packet
    Protect,  // Apply IPSec
}

// ============================================================
// PACKET HEADER STRUCTURES
// ============================================================

/// ESP Header (first part of ESP, unencrypted)
#[derive(Debug, Clone)]
#[repr(C, packed)]
pub struct EspHeader {
    pub spi:     u32,   // Security Parameter Index (big-endian)
    pub seq_num: u32,   // Sequence number (big-endian)
}

/// ESP Trailer (appended after plaintext, before ICV)
#[repr(C, packed)]
pub struct EspTrailer {
    pub pad_len:     u8, // Number of padding bytes
    pub next_header: u8, // Protocol of original payload
}

// ============================================================
// ANTI-REPLAY WINDOW
// ============================================================

/// Sliding window for anti-replay protection.
///
/// Invariant: bitmap bit N represents whether sequence number
///            (right_edge - N) has been received.
///            Bit 0 = right_edge (most recent).
#[derive(Debug, Clone)]
pub struct ReplayWindow {
    right_edge: u32,
    bitmap: u64,        // 64-bit window
    enabled: bool,
}

impl ReplayWindow {
    pub fn new(enabled: bool) -> Self {
        Self {
            right_edge: 0,
            bitmap: 0,
            enabled,
        }
    }

    /// Peek: check without updating. Call BEFORE crypto verification.
    pub fn peek(&self, seq: u32) -> bool {
        if !self.enabled { return true; }
        if seq > self.right_edge { return true; }

        let diff = self.right_edge - seq;
        if diff >= 64 { return false; } // Too old

        (self.bitmap & (1u64 << diff)) == 0 // Not yet seen
    }

    /// Check and update: call AFTER successful ICV verification.
    /// Returns true if packet should be accepted.
    pub fn check_and_update(&mut self, seq: u32) -> bool {
        if !self.enabled { return true; }

        if seq > self.right_edge {
            // New highest sequence number: advance window
            let shift = seq - self.right_edge;
            if shift >= 64 {
                self.bitmap = 0; // Reset: window jumped entirely
            } else {
                self.bitmap <<= shift; // Shift window left
            }
            self.right_edge = seq;
            self.bitmap |= 1u64; // Mark bit 0 (right_edge) as received
            true
        } else {
            let diff = self.right_edge - seq;
            if diff >= 64 {
                return false; // Too old
            }
            let mask = 1u64 << diff;
            if self.bitmap & mask != 0 {
                false // Already seen: replay!
            } else {
                self.bitmap |= mask;
                true
            }
        }
    }

    pub fn window_size() -> u32 { 64 }
}

// ============================================================
// CRYPTO CONTEXT
// ============================================================

/// Encryption context for a Security Association
#[derive(Debug, Clone)]
pub struct EncrContext {
    pub algo: EncrAlgo,
    pub key: Vec<u8>,     // Encryption key bytes
    pub iv_len: usize,    // IV/Nonce length (bytes)
    pub icv_len: usize,   // ICV/Auth tag length (bytes)
    pub block_size: usize, // Block size for padding calculation
}

/// Authentication context for a Security Association
#[derive(Debug, Clone)]
pub struct AuthContext {
    pub algo: AuthAlgo,
    pub key: Vec<u8>,   // HMAC key bytes
    pub icv_len: usize, // Truncated ICV length
}

// ============================================================
// SECURITY ASSOCIATION
// ============================================================

/// A Security Association: one-directional security contract.
///
/// An SA specifies EVERYTHING needed to process one direction
/// of protected traffic: protocol, mode, keys, algorithms,
/// lifetimes, and state.
#[derive(Debug)]
pub struct SecurityAssociation {
    /// Unique identifier at receiver
    pub spi: u32,

    /// Protocol: AH or ESP
    pub protocol: IpsecProtocol,

    /// Mode: Transport or Tunnel
    pub mode: IpsecMode,

    /// Tunnel mode endpoints (only for tunnel mode)
    pub tunnel_src: Option<Ipv4Addr>,
    pub tunnel_dst: Option<Ipv4Addr>,

    /// Cryptographic contexts
    pub encr: EncrContext,
    pub auth: Option<AuthContext>, // None for AEAD (auth is inside encr)

    /// Anti-replay sliding window
    pub replay: ReplayWindow,

    /// Outbound sequence number (monotonically increasing)
    pub seq_num: u32,

    /// Lifetime constraints
    pub lifetime_bytes: u64,   // Remaining bytes (0 = unlimited)
    pub lifetime_until: Option<Instant>, // Absolute expiry time

    /// Is this SA still valid?
    pub valid: bool,
}

impl SecurityAssociation {
    /// Create a new outbound ESP tunnel SA
    pub fn new_esp_tunnel_out(
        spi: u32,
        tunnel_src: Ipv4Addr,
        tunnel_dst: Ipv4Addr,
        encr: EncrContext,
        auth: Option<AuthContext>,
        lifetime_secs: u64,
        lifetime_bytes: u64,
    ) -> Self {
        Self {
            spi,
            protocol: IpsecProtocol::Esp,
            mode: IpsecMode::Tunnel,
            tunnel_src: Some(tunnel_src),
            tunnel_dst: Some(tunnel_dst),
            encr,
            auth,
            replay: ReplayWindow::new(true),
            seq_num: 0,
            lifetime_bytes,
            lifetime_until: if lifetime_secs > 0 {
                Some(Instant::now() + Duration::from_secs(lifetime_secs))
            } else {
                None
            },
            valid: true,
        }
    }

    /// Check if this SA has expired
    pub fn is_expired(&self) -> bool {
        if !self.valid { return true; }
        if let Some(expiry) = self.lifetime_until {
            if Instant::now() >= expiry { return true; }
        }
        false
    }

    /// Increment and return next sequence number. Returns None if would wrap.
    pub fn next_seq(&mut self) -> Option<u32> {
        let next = self.seq_num.checked_add(1)?;
        self.seq_num = next;
        Some(next)
    }

    /// Record bytes consumed; mark invalid if lifetime exhausted
    pub fn consume_bytes(&mut self, n: u64) {
        if self.lifetime_bytes > 0 {
            self.lifetime_bytes = self.lifetime_bytes.saturating_sub(n);
            if self.lifetime_bytes == 0 {
                self.valid = false;
            }
        }
    }
}

// ============================================================
// TRAFFIC SELECTOR
// ============================================================

/// A traffic selector: matches a range of IP addresses and ports.
/// Used in SPD policies and IKE negotiation.
#[derive(Debug, Clone)]
pub struct TrafficSelector {
    pub ip_proto: Option<u8>,       // None = any protocol
    pub src_ip_start: Ipv4Addr,
    pub src_ip_end: Ipv4Addr,
    pub dst_ip_start: Ipv4Addr,
    pub dst_ip_end: Ipv4Addr,
    pub src_port_start: u16,
    pub src_port_end: u16,
    pub dst_port_start: u16,
    pub dst_port_end: u16,
}

impl TrafficSelector {
    /// Create a selector matching a specific subnet pair
    pub fn subnet_pair(
        src_net: Ipv4Addr, src_mask: u32,
        dst_net: Ipv4Addr, dst_mask: u32,
    ) -> Self {
        let src_u32 = u32::from(src_net);
        let dst_u32 = u32::from(dst_net);
        let src_mask_inv = !src_mask;
        let dst_mask_inv = !dst_mask;

        Self {
            ip_proto: None,
            src_ip_start: Ipv4Addr::from(src_u32 & src_mask),
            src_ip_end:   Ipv4Addr::from((src_u32 & src_mask) | src_mask_inv),
            dst_ip_start: Ipv4Addr::from(dst_u32 & dst_mask),
            dst_ip_end:   Ipv4Addr::from((dst_u32 & dst_mask) | dst_mask_inv),
            src_port_start: 0,
            src_port_end: 65535,
            dst_port_start: 0,
            dst_port_end: 65535,
        }
    }

    /// Check if given packet parameters match this selector
    pub fn matches(
        &self,
        src_ip: Ipv4Addr,
        dst_ip: Ipv4Addr,
        proto: u8,
        src_port: u16,
        dst_port: u16,
    ) -> bool {
        let src_u = u32::from(src_ip);
        let dst_u = u32::from(dst_ip);

        if src_u < u32::from(self.src_ip_start) || src_u > u32::from(self.src_ip_end) {
            return false;
        }
        if dst_u < u32::from(self.dst_ip_start) || dst_u > u32::from(self.dst_ip_end) {
            return false;
        }
        if let Some(p) = self.ip_proto {
            if p != proto { return false; }
        }
        if src_port < self.src_port_start || src_port > self.src_port_end {
            return false;
        }
        if dst_port < self.dst_port_start || dst_port > self.dst_port_end {
            return false;
        }
        true
    }
}
```

### 21.2 Security Association Database (SAD) in Rust

```rust
// sad.rs - Security Association Database

use std::collections::HashMap;
use std::net::Ipv4Addr;
use crate::ipsec_types::{SecurityAssociation, IpsecProtocol};

/// Lookup key for the SAD: (SPI, Destination IP, Protocol)
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct SadKey {
    pub spi: u32,
    pub dst_ip: std::net::Ipv4Addr,
    pub protocol: u8,
}

/// Security Association Database
///
/// In production: use a lock-free hash map or RCU structure
/// for high-performance packet processing paths.
pub struct SecurityAssociationDatabase {
    /// Inbound SAs: keyed by (SPI, dst_ip, protocol)
    inbound: HashMap<SadKey, SecurityAssociation>,
    /// Outbound SAs: keyed by arbitrary ID (handle from SPD)
    outbound: Vec<SecurityAssociation>,
}

impl SecurityAssociationDatabase {
    pub fn new() -> Self {
        Self {
            inbound: HashMap::new(),
            outbound: Vec::new(),
        }
    }

    /// Add an inbound SA (receiver looks up by SPI+dst+proto)
    pub fn add_inbound(&mut self, sa: SecurityAssociation, dst_ip: Ipv4Addr) {
        let key = SadKey {
            spi: sa.spi,
            dst_ip,
            protocol: sa.protocol as u8,
        };
        self.inbound.insert(key, sa);
    }

    /// Add an outbound SA
    pub fn add_outbound(&mut self, sa: SecurityAssociation) -> usize {
        let idx = self.outbound.len();
        self.outbound.push(sa);
        idx
    }

    /// Look up inbound SA by SPI + destination IP + protocol
    pub fn lookup_inbound(
        &mut self,
        spi: u32,
        dst_ip: Ipv4Addr,
        protocol: IpsecProtocol,
    ) -> Option<&mut SecurityAssociation> {
        let key = SadKey { spi, dst_ip, protocol: protocol as u8 };
        self.inbound.get_mut(&key).filter(|sa| sa.valid && !sa.is_expired())
    }

    /// Look up outbound SA by index
    pub fn lookup_outbound_by_idx(&mut self, idx: usize) -> Option<&mut SecurityAssociation> {
        self.outbound.get_mut(idx).filter(|sa| sa.valid && !sa.is_expired())
    }

    /// Remove expired SAs (call periodically)
    pub fn cleanup_expired(&mut self) {
        self.inbound.retain(|_, sa| !sa.is_expired());
        self.outbound.retain(|sa| !sa.is_expired());
    }

    pub fn inbound_count(&self) -> usize { self.inbound.len() }
    pub fn outbound_count(&self) -> usize { self.outbound.len() }
}
```

### 21.3 ESP Packet Builder in Rust

```rust
// esp.rs - ESP packet construction in Rust

use crate::ipsec_types::{SecurityAssociation, IpsecMode, EspHeader, EspTrailer};
use std::net::Ipv4Addr;

/// Error type for ESP operations
#[derive(Debug)]
pub enum EspError {
    BufferTooSmall { needed: usize, available: usize },
    SequenceWrap,
    ReplayDetected(u32),
    InvalidPacket(&'static str),
    CryptoError(String),
    SaExpired,
}

impl std::fmt::Display for EspError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            EspError::BufferTooSmall { needed, available } =>
                write!(f, "Buffer too small: need {needed}, have {available}"),
            EspError::SequenceWrap =>
                write!(f, "Sequence number wrapped; SA must be rekeyed"),
            EspError::ReplayDetected(seq) =>
                write!(f, "Replayed packet detected (seq={seq})"),
            EspError::InvalidPacket(msg) =>
                write!(f, "Invalid ESP packet: {msg}"),
            EspError::CryptoError(msg) =>
                write!(f, "Crypto error: {msg}"),
            EspError::SaExpired =>
                write!(f, "Security Association has expired"),
        }
    }
}

/// Compute padding needed to align to block_size.
///
/// After the payload, we have [padding | pad_len | next_hdr] (trailer).
/// Total length including trailer must be block-aligned.
///
/// Formula:
///   total_needed = payload_len + 2  (trailer is always 2 bytes)
///   aligned = ceil(total_needed / block_size) * block_size
///   padding = aligned - payload_len - 2
fn compute_esp_padding(payload_len: usize, block_size: usize) -> usize {
    let block = if block_size == 0 { 4 } else { block_size };
    let with_trailer = payload_len + 2;
    let aligned = (with_trailer + block - 1) / block * block;
    aligned - with_trailer
}

/// ESP packet builder.
///
/// Produces the byte layout for an ESP tunnel-mode packet.
/// Does NOT perform actual encryption (pass encrypt_fn for that).
///
/// # Parameters
/// - `sa`: Mutable reference to the Security Association
/// - `inner_pkt`: The original IP packet to encapsulate
/// - `outer_src`: VPN gateway source IP (tunnel mode only)
/// - `outer_dst`: VPN gateway destination IP (tunnel mode only)
/// - `encrypt_fn`: Closure that performs encryption + authentication
///    Signature: `encrypt_fn(key, iv, aad, plaintext) -> (ciphertext, tag)`
///
/// # Returns
/// Assembled ESP packet bytes
pub fn esp_build_tunnel_packet(
    sa: &mut SecurityAssociation,
    inner_pkt: &[u8],
    outer_src: Ipv4Addr,
    outer_dst: Ipv4Addr,
) -> Result<Vec<u8>, EspError> {
    // Check SA validity
    if sa.is_expired() {
        return Err(EspError::SaExpired);
    }

    // Get next sequence number (prevents sequence wrap within one SA)
    let seq = sa.next_seq().ok_or(EspError::SequenceWrap)?;

    let iv_len      = sa.encr.iv_len;
    let icv_len     = sa.encr.icv_len;
    let block_size  = sa.encr.block_size;

    // Compute padding for alignment
    let payload_len = inner_pkt.len();
    let pad_len     = compute_esp_padding(payload_len, block_size);

    // Plaintext layout: [inner_pkt][padding][pad_len][next_hdr]
    let plaintext_len = payload_len + pad_len + 2;

    // Total ESP packet layout:
    // [Outer IPv4 Hdr (20B)][ESP Hdr (8B)][IV (iv_len)][Ciphertext (plaintext_len)][ICV (icv_len)]
    let esp_pkt_len = 20 + 8 + iv_len + plaintext_len + icv_len;
    let mut pkt = vec![0u8; esp_pkt_len];

    // ---- Build Outer IPv4 Header ----
    {
        let h = &mut pkt[0..20];
        h[0]  = 0x45;          // Version=4, IHL=5 (20 bytes, no options)
        h[1]  = 0;             // DSCP/ECN = 0
        h[2]  = (esp_pkt_len >> 8) as u8;  // Total length (big-endian)
        h[3]  = (esp_pkt_len & 0xFF) as u8;
        h[4]  = 0; h[5] = 0;   // Identification
        h[6]  = 0; h[7] = 0;   // Flags + Fragment Offset
        h[8]  = 64;            // TTL
        h[9]  = 50;            // Protocol = 50 (ESP)
        h[10] = 0; h[11] = 0;  // Checksum (filled separately)
        let src = outer_src.octets();
        let dst = outer_dst.octets();
        h[12..16].copy_from_slice(&src);
        h[16..20].copy_from_slice(&dst);
        // Compute checksum
        let csum = internet_checksum(&pkt[0..20]);
        pkt[10] = (csum >> 8) as u8;
        pkt[11] = (csum & 0xFF) as u8;
    }

    // ---- Build ESP Header: SPI + Sequence Number ----
    {
        let h = &mut pkt[20..28];
        h[0..4].copy_from_slice(&sa.spi.to_be_bytes());
        h[4..8].copy_from_slice(&seq.to_be_bytes());
    }

    // ---- Generate IV (in production: use OS CSPRNG) ----
    {
        let iv_start = 28;
        let iv_end   = 28 + iv_len;
        // Placeholder: fill with counter-based value (INSECURE for production!)
        // Production: use getrandom::getrandom(&mut pkt[iv_start..iv_end]);
        for (i, b) in pkt[iv_start..iv_end].iter_mut().enumerate() {
            *b = (seq as u8).wrapping_add(i as u8);
        }
    }

    // ---- Build Plaintext in a temporary buffer ----
    let mut plaintext = Vec::with_capacity(plaintext_len);
    plaintext.extend_from_slice(inner_pkt);  // Original IP packet

    // Padding bytes: RFC recommends 1,2,3,...,pad_len
    for i in 1..=(pad_len as u8) {
        plaintext.push(i);
    }

    // ESP Trailer: pad_len + next_header
    plaintext.push(pad_len as u8);
    plaintext.push(4);  // Next header: 4 = IPv4 (inside tunnel)

    debug_assert_eq!(plaintext.len(), plaintext_len);

    // ---- Encrypt plaintext → ciphertext at offset 28+iv_len ----
    // For AES-GCM, the AAD is the ESP header (SPI + SeqNum = bytes 20..28)
    let ct_start = 28 + iv_len;
    let ct_end   = ct_start + plaintext_len;

    // PLACEHOLDER: Copy plaintext (real implementation calls AES-GCM here)
    // Production example with ring crate:
    //   let key = ring::aead::LessSafeKey::new(
    //       ring::aead::UnboundKey::new(&ring::aead::AES_256_GCM, &sa.encr.key).unwrap()
    //   );
    //   key.seal_in_place_append_tag(nonce, aad, &mut in_out).unwrap();
    pkt[ct_start..ct_end].copy_from_slice(&plaintext);

    // ---- ICV: authentication tag (produced by AEAD) ----
    // Placeholder: zeros (INSECURE — real code fills from AES-GCM tag)
    // The ICV occupies the last icv_len bytes of the packet
    // (already zeroed from vec initialization)

    // Update SA statistics
    sa.consume_bytes(esp_pkt_len as u64);

    Ok(pkt)
}

/// ESP inbound processing (decryption + verification)
pub fn esp_process_inbound(
    sa: &mut SecurityAssociation,
    raw_pkt: &[u8],
) -> Result<Vec<u8>, EspError> {
    if sa.is_expired() {
        return Err(EspError::SaExpired);
    }
    if raw_pkt.len() < 28 {
        return Err(EspError::InvalidPacket("packet too short"));
    }

    // Skip outer IP header (assume 20 bytes; no options)
    let ip_hdr_len = ((raw_pkt[0] & 0x0F) as usize) * 4;
    if raw_pkt.len() < ip_hdr_len + 8 {
        return Err(EspError::InvalidPacket("packet too short for ESP header"));
    }

    let esp_start = ip_hdr_len;

    // Parse ESP header
    let spi     = u32::from_be_bytes(raw_pkt[esp_start..esp_start+4].try_into().unwrap());
    let seq_num = u32::from_be_bytes(raw_pkt[esp_start+4..esp_start+8].try_into().unwrap());

    // Validate SPI matches SA
    if spi != sa.spi {
        return Err(EspError::InvalidPacket("SPI mismatch"));
    }

    // Anti-replay: peek before crypto (avoid expensive operations on replays)
    if !sa.replay.peek(seq_num) {
        return Err(EspError::ReplayDetected(seq_num));
    }

    let iv_len  = sa.encr.iv_len;
    let icv_len = sa.encr.icv_len;

    let data_start = esp_start + 8 + iv_len;  // After ESP header + IV
    let pkt_len = raw_pkt.len();

    if pkt_len < data_start + icv_len + 2 {
        return Err(EspError::InvalidPacket("packet too short for ciphertext"));
    }

    let ct_len     = pkt_len - data_start - icv_len;
    let ct_end     = data_start + ct_len;
    let icv_start  = ct_end;

    let _iv      = &raw_pkt[esp_start+8 .. esp_start+8+iv_len];
    let ciphertext = &raw_pkt[data_start..ct_end];
    let _icv     = &raw_pkt[icv_start..icv_start+icv_len];

    // PLACEHOLDER: Decryption
    // Production: AES-GCM decrypt+verify here. If tag mismatch → CryptoError.
    // ring::aead::LessSafeKey::open_in_place(nonce, aad, &mut in_out).map_err(...)?;
    let mut plaintext = ciphertext.to_vec();

    // Verify ICV (PLACEHOLDER - real code verifies in open_in_place above)
    // If ICV fails: return Err(EspError::CryptoError("ICV mismatch".into()));

    // Parse ESP Trailer: last 2 bytes of plaintext
    if plaintext.len() < 2 {
        return Err(EspError::InvalidPacket("ciphertext too short for trailer"));
    }
    let pad_len     = plaintext[plaintext.len() - 2] as usize;
    let _next_hdr   = plaintext[plaintext.len() - 1];

    let inner_pkt_len = plaintext.len()
        .checked_sub(pad_len + 2)
        .ok_or(EspError::InvalidPacket("pad_len exceeds plaintext"))?;

    // Update anti-replay window (only after successful ICV verification!)
    if !sa.replay.check_and_update(seq_num) {
        return Err(EspError::ReplayDetected(seq_num));
    }

    sa.consume_bytes(raw_pkt.len() as u64);

    plaintext.truncate(inner_pkt_len);
    Ok(plaintext) // This is the inner IP packet
}

/// Internet checksum (RFC 1071) for IPv4 header
fn internet_checksum(data: &[u8]) -> u16 {
    let mut sum: u32 = 0;
    let mut i = 0;
    while i + 1 < data.len() {
        let word = ((data[i] as u32) << 8) | (data[i+1] as u32);
        sum = sum.wrapping_add(word);
        i += 2;
    }
    if i < data.len() {
        sum = sum.wrapping_add((data[i] as u32) << 8);
    }
    while sum >> 16 != 0 {
        sum = (sum & 0xFFFF) + (sum >> 16);
    }
    !(sum as u16)
}
```

### 21.4 SPD in Rust

```rust
// spd.rs - Security Policy Database

use std::net::Ipv4Addr;
use crate::ipsec_types::{SpdAction, IpsecProtocol, IpsecMode, EncrAlgo, AuthAlgo};

/// A single SPD policy entry.
/// The SPD is ordered: first matching policy wins.
pub struct SpdPolicy {
    pub selector: PolicySelector,
    pub action: SpdAction,
    pub sa_template: Option<SaTemplate>, // Only for PROTECT
    pub sa_idx: Option<usize>,            // Index into SAD
}

/// Traffic selector for SPD policy matching
pub struct PolicySelector {
    pub src_net: u32,     // Network address (network byte order)
    pub src_mask: u32,    // Subnet mask
    pub dst_net: u32,
    pub dst_mask: u32,
    pub protocol: Option<u8>,     // None = any
    pub dst_port: Option<u16>,    // None = any
}

impl PolicySelector {
    pub fn matches(
        &self,
        src_ip: Ipv4Addr,
        dst_ip: Ipv4Addr,
        protocol: u8,
        dst_port: u16,
    ) -> bool {
        let src = u32::from(src_ip);
        let dst = u32::from(dst_ip);

        if (src & self.src_mask) != (self.src_net & self.src_mask) {
            return false;
        }
        if (dst & self.dst_mask) != (self.dst_net & self.dst_mask) {
            return false;
        }
        if let Some(p) = self.protocol {
            if p != protocol { return false; }
        }
        if let Some(port) = self.dst_port {
            if port != dst_port { return false; }
        }
        true
    }
}

/// Template for SA creation when no SA exists yet
pub struct SaTemplate {
    pub protocol: IpsecProtocol,
    pub mode: IpsecMode,
    pub encr: EncrAlgo,
    pub auth: AuthAlgo,
}

/// Security Policy Database
pub struct SecurityPolicyDatabase {
    policies: Vec<SpdPolicy>,
}

impl SecurityPolicyDatabase {
    pub fn new() -> Self {
        Self { policies: Vec::new() }
    }

    /// Add policy (appended; first-match order)
    pub fn add(&mut self, policy: SpdPolicy) {
        self.policies.push(policy);
    }

    /// Lookup: find first matching policy for given packet parameters.
    /// Returns (action, optional_sa_idx)
    pub fn lookup(
        &self,
        src_ip: Ipv4Addr,
        dst_ip: Ipv4Addr,
        protocol: u8,
        dst_port: u16,
    ) -> (SpdAction, Option<usize>) {
        for policy in &self.policies {
            if policy.selector.matches(src_ip, dst_ip, protocol, dst_port) {
                return (policy.action, policy.sa_idx);
            }
        }
        (SpdAction::Bypass, None) // Default: bypass
    }

    /// Update SA index for a policy (after IKE establishes SA)
    pub fn set_sa_idx(&mut self, policy_idx: usize, sa_idx: usize) {
        if let Some(p) = self.policies.get_mut(policy_idx) {
            p.sa_idx = Some(sa_idx);
        }
    }
}
```

### 21.5 Main Integration & Test

```rust
// main.rs - Integration test and demonstration

mod ipsec_types;
mod sad;
mod esp;
mod spd;

use std::net::Ipv4Addr;
use ipsec_types::*;
use sad::SecurityAssociationDatabase;
use esp::{esp_build_tunnel_packet, esp_process_inbound};

fn main() {
    println!("=== IPSec Rust Implementation Demo ===\n");

    // ---- 1. Demonstrate Anti-Replay Window ----
    println!("--- Anti-Replay Window Test ---");
    let mut win = ReplayWindow::new(true);

    let test_cases: &[(u32, &str)] = &[
        (1,   "First packet"),
        (2,   "Sequential"),
        (5,   "Jump forward"),
        (3,   "Within window (not seen)"),
        (2,   "Replay! Already seen"),
        (100, "Big jump, advance window"),
        (30,  "Now outside left edge"),
        (99,  "Within new window"),
        (99,  "Replay again"),
    ];

    println!("{:<10} {:<30} {}", "SeqNum", "Description", "Result");
    println!("{:<10} {:<30} {}", "------", "-----------", "------");
    for &(seq, desc) in test_cases {
        let result = win.check_and_update(seq);
        println!("{:<10} {:<30} {}",
                 seq, desc,
                 if result { "ACCEPT ✓" } else { "REJECT (replay) ✗" });
    }

    // ---- 2. Demonstrate ESP Padding Calculation ----
    println!("\n--- ESP Padding for AES-CBC (block_size=16) ---");
    let block = 16;
    for &payload_len in &[0usize, 1, 14, 15, 16, 17, 30, 100, 255] {
        let pad = esp::compute_esp_padding(payload_len, block); // make pub for test
        println!("  payload={:4} → padding={:3} → total_with_trailer={}",
                 payload_len, pad, payload_len + pad + 2);
    }

    // ---- 3. Build an ESP Tunnel Mode Packet ----
    println!("\n--- Building ESP Tunnel Packet ---");

    // Create a fake inner IP packet (minimal IPv4 TCP)
    let mut inner_pkt = vec![0u8; 40]; // 20B IP + 20B TCP
    inner_pkt[0] = 0x45; // IPv4, IHL=5
    inner_pkt[9] = 6;    // TCP

    // Create SA (in real code, IKE would negotiate this)
    let encr_ctx = EncrContext {
        algo: EncrAlgo::AesGcm16,
        key: vec![0u8; 32],  // 256-bit key (all zeros for demo)
        iv_len: 12,
        icv_len: 16,
        block_size: 1,  // GCM is a stream mode: no block alignment needed
    };

    let mut sa = SecurityAssociation::new_esp_tunnel_out(
        0xC6BA_0001,                   // SPI
        Ipv4Addr::new(203, 0, 113, 1), // Tunnel source: GW1
        Ipv4Addr::new(198, 51, 100, 1),// Tunnel dest: GW2
        encr_ctx,
        None,                          // No separate auth (AEAD)
        3600,                          // 1 hour lifetime
        1024 * 1024 * 1024,            // 1 GB lifetime
    );

    match esp_build_tunnel_packet(
        &mut sa,
        &inner_pkt,
        Ipv4Addr::new(203, 0, 113, 1),
        Ipv4Addr::new(198, 51, 100, 1),
    ) {
        Ok(esp_pkt) => {
            println!("  Inner packet size:  {} bytes", inner_pkt.len());
            println!("  ESP packet size:    {} bytes", esp_pkt.len());
            println!("  Overhead:           {} bytes", esp_pkt.len() - inner_pkt.len());
            println!("  Seq number used:    {}", sa.seq_num);
            println!("  First 8 bytes (outer IP): {:02X?}", &esp_pkt[0..8]);
            println!("  SPI (bytes 20-24):  {:02X?}", &esp_pkt[20..24]);
            println!("  SeqNum (24-28):     {:02X?}", &esp_pkt[24..28]);
        }
        Err(e) => println!("  Error: {}", e),
    }

    // ---- 4. SA Lifetime Check ----
    println!("\n--- SA Expiry Logic ---");
    println!("  SA valid:   {}", !sa.is_expired());
    println!("  Bytes left: {}", sa.lifetime_bytes);
    sa.lifetime_bytes = 1; // Simulate near-exhaustion
    sa.consume_bytes(1);
    println!("  After consuming last byte — valid: {}", sa.valid);

    println!("\n=== Demo Complete ===");
}
```

---

## 22. Security Considerations & Common Attacks

### 22.1 Attacks on IPSec

#### 1. IKE Aggressive Mode PSK Offline Attack

**Attack:** Capture Aggressive Mode exchange (identities are plaintext). Use offline dictionary/brute-force to crack the PSK from the captured HASH payload.

**Mitigation:** Never use Aggressive Mode with PSK. Use Main Mode or IKEv2 with strong PSK or certificates.

#### 2. SWEET32 Attack on 3DES

**Attack:** Birthday attack against 64-bit block ciphers (3DES). After ~32GB of data through same key, blocks repeat → information leakage.

**Mitigation:** Never use 3DES. Use AES (128-bit blocks, immune to birthday attacks at practical traffic volumes).

#### 3. Weak DH Groups (Logjam)

**Attack:** Precomputing logarithms for 1024-bit MODP allows passive decryption of connections using Group 1 or Group 2.

**Mitigation:** Use DH Group 14 (2048-bit MODP) minimum. Prefer Group 19 or 20 (ECDH).

#### 4. Replay Attack on Stale SA

**Attack:** If anti-replay is disabled (misconfiguration), replay captured ESP packets.

**Mitigation:** Always enable anti-replay. Never disable it in production.

#### 5. IKE Denial of Service

**Attack:** Flood a VPN gateway with IKE_SA_INIT requests. Each triggers expensive DH computation on the responder.

**Mitigation:** IKEv2 cookies (RFC 7296 §2.6) — responder sends COOKIE notification; initiator must repeat request with cookie before responder commits DH resources.

```
Initiator                              Responder
    |--- IKE_SA_INIT Req ------------>  |
    |                                   |  [Under load: don't compute DH yet]
    |<-- COOKIE notification ---------- |  [Send cheap cookie challenge]
    |                                   |
    |--- IKE_SA_INIT Req + COOKIE ---> |  [Now compute DH for legitimate requester]
    |                                   |
    |<-- IKE_SA_INIT Response --------- |
```

#### 6. Traffic Analysis

**Attack:** Even with ESP encryption, traffic patterns (packet sizes, timing, frequency) reveal information about communication.

**Mitigation:** ESP padding (obscures payload size). Traffic padding (send dummy packets). Protocol design (HTTPS over IPSec still leaks TLS record sizes).

### 22.2 Configuration Best Practices

```
Recommended IKEv2 Configuration (2024+):

IKE SA (Phase 1 / Parent SA):
  Encryption:    AES-256-GCM or AES-256-CBC
  Integrity:     SHA-256 or SHA-384 (not needed for AEAD)
  PRF:           PRF-HMAC-SHA256 or PRF-HMAC-SHA384
  DH Group:      19 (P-256) or 20 (P-384)
  Lifetime:      86400 seconds (24 hours) or less

Child SA (Phase 2 / IPSec SA):
  Encryption:    AES-256-GCM (AEAD, preferred)
  Integrity:     Not needed (AEAD provides it)
  PFS DH Group:  19 or 20
  Lifetime:      3600 seconds (1 hour) or less
  Byte Limit:    1 GB or less

Authentication:
  Prefer:        RSA signatures with SHA-256 or ECDSA
  PSK:           Only if strong random key (>128 bits), use IKEv2
  Avoid:         MD5, SHA1, 3DES, Group 1/2/5, Aggressive Mode
```

---

## 23. Mental Models & Thinking Frameworks

### 23.1 The Three Questions of IPSec

Every time you reason about an IPSec scenario, ask:

```
1. WHO?    Who are the two peers communicating?
           What authenticates them? (PSK? Certificate?)

2. WHAT?   What traffic needs protection?
           (SPD selector: which IPs, ports, protocols?)

3. HOW?    How is it protected?
           (Protocol: AH or ESP? Mode: Transport or Tunnel?
            Algorithms? Lifetime? PFS?)
```

### 23.2 The "Post Office" Mental Model

Think of IPSec like a secure postal system:

- **SPD** = Postal rules: "All mail between these cities goes through secure courier"
- **SAD** = The secure courier's instructions: "Here are the keys for today's route"
- **IKE** = Negotiating with the courier: "What encryption will we use? Here's my ID"
- **ESP** = The sealed envelope: contents private, envelope authenticated
- **AH** = Notarized mail: contents visible, but origin and integrity guaranteed
- **SPI** = The courier's internal tracking number

### 23.3 Layer Abstraction Model

```
THINK OF IPSEC IN THREE LAYERS:

Layer 3 (Policy):    SPD — WHAT do we protect? WHO can talk to WHOM?
Layer 2 (State):     SAD — HOW do we protect? WHAT keys do we use?
Layer 1 (Mechanism): AH/ESP — DO the actual cryptographic work
Layer 0 (Setup):     IKE — Establish the state in SAD automatically
```

### 23.4 Deliberate Practice — IPSec Mastery Path

```
WEEK 1: Fundamentals
  □ Understand why IP needs security (threat model)
  □ Explain AH vs ESP to a colleague
  □ Draw Transport vs Tunnel mode from memory
  □ Read RFC 4303 (ESP) header section

WEEK 2: State Management
  □ Implement anti-replay window from scratch
  □ Model SPD + SAD in code (your language of choice)
  □ Trace a packet through the full inbound pipeline

WEEK 3: Key Exchange
  □ Understand Diffie-Hellman mathematically
  □ Trace IKEv2 4-message exchange manually
  □ Understand key derivation (SKEYSEED → SK_d, SK_ei...)

WEEK 4: Integration
  □ Build a minimal ESP encapsulator
  □ Use Wireshark to capture and analyze real IKE/ESP traffic
  □ Configure IPSec between two Linux VMs using strongSwan/Libreswan
  □ Read a Security Advisory about an IPSec vulnerability
```

### 23.5 Cognitive Chunking for Protocol Mastery

**Chunking principle:** Group related concepts into single mental units.

```
CHUNK 1: "The SA Pair"
  Always think: outbound SA + inbound SA = ONE secure channel
  Never: a single SA is bidirectional

CHUNK 2: "The SPD-SAD Pipeline"  
  SPD → "Should I protect this?" → SAD → "Here's how"
  The SPD is the policy; the SAD is the enforcement

CHUNK 3: "IKE = Authentication + Key Exchange + SA Creation"
  IKE does three things simultaneously.
  Don't confuse the phases.

CHUNK 4: "AEAD = Encrypt + Authenticate in one step"
  AES-GCM, ChaCha20-Poly1305: No separate HMAC needed
  Simpler, faster, preferred
```

### 23.6 Feynman Technique Checkpoints

You truly understand IPSec when you can explain:

1. Why does tunnel mode need two IP headers?
2. Why does AH break NAT but ESP does not?
3. Why must the anti-replay window update AFTER ICV verification (not before)?
4. What is the purpose of the SKEYID_d derivation in IKEv1?
5. Why does IKEv2 need only 4 messages but IKEv1 needs 9+?
6. What happens if the DH shared secret is the same for multiple sessions (no PFS)?
7. Why is Aggressive Mode with PSK insecure but Main Mode with PSK acceptable?

---

## Appendix A: Key RFC References

| RFC | Title | Purpose |
|---|---|---|
| RFC 4301 | Security Architecture for the Internet Protocol | IPSec architecture |
| RFC 4302 | IP Authentication Header | AH specification |
| RFC 4303 | IP Encapsulating Security Payload | ESP specification |
| RFC 7296 | Internet Key Exchange Protocol Version 2 (IKEv2) | IKEv2 |
| RFC 2409 | The Internet Key Exchange (IKE) | IKEv1 (historical) |
| RFC 3706 | A Traffic-Based Method of Detecting Dead IKE Peers | DPD |
| RFC 3948 | UDP Encapsulation of IPsec ESP Packets | NAT-T |
| RFC 4555 | IKEv2 Mobility and Multihoming Protocol (MOBIKE) | Mobile VPN |
| RFC 8221 | Cryptographic Algorithm Implementation Requirements for ESP and AH | Crypto algorithms |
| RFC 8247 | Algorithm Implementation Requirements for IKEv2 | IKE crypto |

## Appendix B: Wireshark Filters for IPSec Analysis

```
# Capture IKE (both v1 and v2) — port 500 and 4500
udp.port == 500 or udp.port == 4500

# Capture only IKEv2
isakmp.version == 2.0

# Capture ESP packets
ip.proto == 50

# Capture AH packets
ip.proto == 51

# Show IKEv2 exchanges
isakmp.exchtype == 34   # IKE_SA_INIT
isakmp.exchtype == 35   # IKE_AUTH
isakmp.exchtype == 36   # CREATE_CHILD_SA
isakmp.exchtype == 37   # INFORMATIONAL
```

## Appendix C: Linux IPSec Configuration (strongSwan)

```
# /etc/ipsec.conf (strongSwan)

config setup
    charondebug="ike 2, knl 2, cfg 2"

conn site-to-site
    type=tunnel
    left=203.0.113.1          # Local gateway IP
    leftsubnet=192.168.1.0/24 # Local network
    right=198.51.100.1         # Remote gateway IP
    rightsubnet=10.0.0.0/8    # Remote network
    ike=aes256gcm16-prfsha256-ecp256!   # IKE SA proposal
    esp=aes256gcm16-ecp256!             # Child SA proposal
    keyexchange=ikev2
    authby=psk
    auto=start

# /etc/ipsec.secrets
203.0.113.1 198.51.100.1 : PSK "V3ryStr0ngRandomP@ssphrase!"
```

---

*This guide covers IPSec from the ground up through expert-level implementation details. Master each section, implement the code, capture real traffic with Wireshark, and configure a real VPN — only then will the concepts crystallize into true expertise.*

*Remember the monk's way: deep focus, one concept at a time, no shortcuts.*

# IPsec Debugging & Troubleshooting — The Complete In-Depth Reference

> "The first step to fixing a broken tunnel is understanding what a working tunnel looks like — at every layer, at every moment."

---

## Table of Contents

1. [Debugger's Mental Model — How to Think About IPsec Failures](#1-debuggers-mental-model)
2. [IPsec Stack Architecture — Linux XFRM Deep Dive](#2-ipsec-stack-architecture)
3. [Debugging Tools Inventory — Every Tool, Every Flag](#3-debugging-tools-inventory)
4. [IKE Message Analysis — What Normal Looks Like](#4-ike-message-analysis)
5. [IKEv1 Debugging — Phase 1 & Phase 2 Failures](#5-ikev1-debugging)
6. [IKEv2 Debugging — Exchange-Level Failures](#6-ikev2-debugging)
7. [ESP & AH Packet-Level Debugging](#7-esp-and-ah-packet-debugging)
8. [Cryptographic Failure Analysis](#8-cryptographic-failure-analysis)
9. [Certificate and PKI Failures](#9-certificate-and-pki-failures)
10. [NAT Traversal Debugging](#10-nat-traversal-debugging)
11. [Anti-Replay Failures](#11-anti-replay-failures)
12. [SA Lifetime and Rekeying Failures](#12-sa-lifetime-and-rekeying-failures)
13. [Routing and Policy (SPD/SAD) Failures](#13-routing-and-policy-failures)
14. [Dead Peer Detection Failures](#14-dead-peer-detection-failures)
15. [strongSwan — Full Debug Walkthrough](#15-strongswan-debugging)
16. [Libreswan / Openswan Debugging](#16-libreswan-debugging)
17. [Cisco IOS / IOS-XE Debugging](#17-cisco-ios-debugging)
18. [Juniper SRX Debugging](#18-juniper-srx-debugging)
19. [Cloud VPN Debugging — AWS, Azure, GCP](#19-cloud-vpn-debugging)
20. [Wireshark — Full IPsec Dissection Guide](#20-wireshark-dissection)
21. [tcpdump — Packet Capture Recipes](#21-tcpdump-recipes)
22. [Common Failure Scenarios — Root Cause Diagnosis](#22-common-failure-scenarios)
23. [Performance Troubleshooting](#23-performance-troubleshooting)
24. [IPsec Security Audit Checklist](#24-security-audit-checklist)
25. [Quick Reference — State Machines and Timers](#25-quick-reference)

---

## 1. Debugger's Mental Model

### 1.1 The Layered Failure Model

Every IPsec failure lives in exactly one of these layers. Your job as a debugger is to **localize the failure to its layer** before trying to fix anything. Jumping to conclusions wastes hours.

```
Layer 6: APPLICATION  — Is traffic actually being generated? Does app see connection?
           |
Layer 5: ROUTING      — Is the kernel routing table sending traffic to the IPsec policy?
           |
Layer 4: POLICY (SPD) — Does the Security Policy Database match this traffic?
           |
Layer 3: SA STATE     — Does the SAD have a valid, current SA for this traffic?
           |
Layer 2: IKE NEGOTIATION — Did IKE complete? Are there mismatched proposals?
           |
Layer 1: CRYPTO/KEYS  — Are algorithms correct? Keys valid? Certs trusted?
           |
Layer 0: NETWORK      — Can UDP/500 and UDP/4500 reach the peer? Firewall blocking?
```

**Debugging Strategy:** Always start at Layer 0 and work up. A firewall blocking UDP 500 looks identical to a crypto mismatch from the application's perspective — both result in "tunnel doesn't work." Only testing each layer in isolation tells you where the real problem is.

### 1.2 The Three Planes of IPsec

IPsec has three distinct operational planes. Failures in one plane have different symptoms and different fixes:

```
+=========================================================+
|  CONTROL PLANE: IKE (UDP 500/4500)                      |
|  What it does: Negotiate SAs, exchange keys             |
|  Fails when: Proposal mismatch, auth failure, network   |
|  Tools: ike logs, tcpdump on UDP 500, ike debuggers     |
+=========================================================+
|  DATA PLANE: ESP/AH (IP Proto 50/51)                    |
|  What it does: Actually encrypt/authenticate packets    |
|  Fails when: SA mismatch, replay, wrong keys, MTU       |
|  Tools: ip xfrm, tcpdump on proto 50, Wireshark         |
+=========================================================+
|  MANAGEMENT PLANE: SPD/SAD (kernel XFRM)                |
|  What it does: Policy lookup, SA selection, routing     |
|  Fails when: Missing policy, wrong selectors, routing   |
|  Tools: ip xfrm policy, ip xfrm state, ip route        |
+=========================================================+
```

### 1.3 The "Four Packet Test" Mental Model

When a tunnel appears broken, trace these four packets mentally:

```
Packet Journey — Site A (10.0.1.10) to Site B (10.0.2.20):

OUTBOUND on A:
  1. App creates packet: src=10.0.1.10, dst=10.0.2.20
  2. Kernel routing: "10.0.2.0/24 via IPsec"
  3. SPD lookup: "PROTECT this traffic with ESP tunnel"
  4. SAD lookup: "Use SA with SPI=0xDEAD, keys=..."
  5. ESP encrypt: wrap in new IP packet GW-A → GW-B
  6. Send to GW-B on network

INBOUND on B:
  7. Receive ESP packet (proto=50) from GW-A
  8. Extract SPI from ESP header
  9. SAD lookup by SPI → find SA with keys
  10. Verify ICV (HMAC or AEAD tag)
  11. Decrypt payload → recover original packet
  12. SPD check: "Is this traffic allowed in?"
  13. Deliver to routing → forward to 10.0.2.20

If any of these 13 steps fails, the packet dies. Your debug task is to find WHICH step.
```

### 1.4 State Machine Overview

Understanding state machines is critical because logs reference state names:

```
IKEv2 SA State Machine:

        [START]
           |
           | send IKE_SA_INIT request
           v
    [IKE_SA_INIT_SENT]
           |
           | receive IKE_SA_INIT response
           v
    [IKE_AUTH_SENT]
           |
           | receive IKE_AUTH response
           v
    [ESTABLISHED] ←──────────────────────┐
           |                              │
           | rekeying timer fires         │ rekey complete
           v                              │
    [REKEYING]  ──────────────────────────┘
           |
           | delete timer fires / DPD failure
           v
    [DELETING]
           |
           v
       [DELETED]

Child SA (IPsec SA) State Machine:

    [CREATING] → [INSTALLED] → [REKEYING] → [DELETING] → [DELETED]
```

---

## 2. IPsec Stack Architecture

### 2.1 Linux Kernel XFRM Architecture

The Linux kernel's IPsec implementation is called **XFRM** (transform). Understanding it is mandatory for effective debugging.

```
User Space                    Kernel Space
============                  =============

strongSwan / libreswan        ┌─────────────────────┐
         │                    │   XFRM Framework     │
         │  PF_KEY socket     │                      │
         │  or Netlink        │  ┌───────────┐       │
         └──────────────────► │  │    SPD    │       │
                              │  │ (policies)│       │
                              │  └─────┬─────┘       │
                              │        │ lookup       │
                              │  ┌─────▼─────┐       │
                              │  │    SAD    │       │
                              │  │  (states) │       │
                              │  └─────┬─────┘       │
                              │        │              │
                              │  ┌─────▼─────────┐   │
                              │  │  XFRM engine  │   │
                              │  │  (transforms) │   │
                              │  │               │   │
                              │  │  ┌──────────┐ │   │
                              │  │  │ ESP/AH   │ │   │
                              │  │  │ handlers │ │   │
                              │  │  └──────────┘ │   │
                              │  └───────────────┘   │
                              │        │              │
                              │  ┌─────▼─────────┐   │
                              │  │  Net device   │   │
                              │  │  (eth0, etc.) │   │
                              │  └───────────────┘   │
                              └─────────────────────┘

Key data structures:
  xfrm_policy  → SPD entry (struct in kernel net/xfrm/xfrm_policy.c)
  xfrm_state   → SA (struct in include/net/xfrm.h)
  xfrm_tmpl    → SA template within a policy
```

### 2.2 How Outbound Packets Flow Through XFRM

```
app sends packet
       │
       ▼
ip_output() / ip6_output()
       │
       ▼
xfrm_output()  ← Policy lookup happens here
       │
       │ For each SA in the bundle (policies can chain multiple SAs):
       ▼
xfrm_output_one()
       │
       ├─► esp_output()  or  ah_output()
       │       │
       │       ├─ Increment sequence number
       │       ├─ Encrypt (if ESP)
       │       ├─ Compute ICV
       │       └─ Build new IP header (if tunnel mode)
       │
       ▼
dev_queue_xmit()  ← Packet leaves the box
```

### 2.3 How Inbound Packets Flow Through XFRM

```
Packet arrives from network
       │
       ▼
ip_rcv()
       │
       ▼
Protocol demux (proto=50 → ESP, proto=51 → AH)
       │
       ▼
xfrm4_rcv() / esp_input() / ah_input()
       │
       ├─ Extract SPI from header
       ├─ SAD lookup: xfrm_state_lookup(spi, daddr, proto)
       ├─ Anti-replay check (peek)
       ├─ Verify ICV → if FAIL: drop + increment stat
       ├─ Decrypt payload
       ├─ Update anti-replay window
       └─ Strip IPsec headers
       │
       ▼
xfrm_policy_check()  ← SPD inbound check
       │
       ▼
ip_rcv_finish() → route → deliver to app
```

### 2.4 Kernel Data Structures — What ip xfrm Shows

```
xfrm_state (one SA):
  struct xfrm_state {
    u32              id.spi          // SPI number
    u32              id.daddr        // Destination IP
    u8               id.proto        // ESP=50, AH=51
    struct xfrm_id   id
    struct xfrm_selector sel         // Traffic selector
    struct xfrm_lifetime_cfg lft     // Configured lifetimes
    struct xfrm_lifetime_cur curlft  // Current (remaining) lifetimes
    struct xfrm_stats stats          // Counters: replay, auth_err, etc.
    struct xfrm_mode *mode           // transport or tunnel
    struct xfrm_algo_auth *aalg      // auth algorithm
    struct xfrm_algo *ealg           // encryption algorithm
    ...
  }

xfrm_policy (one SPD entry):
  struct xfrm_policy {
    struct xfrm_selector selector    // What traffic this matches
    int action                       // ALLOW, BLOCK, or PROTECT
    struct xfrm_tmpl xfrm_vec[]     // SA templates (up to XFRM_MAX_DEPTH)
    int priority                     // Lower = higher priority
    ...
  }
```

### 2.5 Netlink / PF_KEY Socket Interface

IKE daemons communicate with the kernel XFRM via one of two interfaces:

**PF_KEY (older, RFC 2367):**
```
socket(PF_KEY, SOCK_RAW, PF_KEY_V2)
  → Used by older daemons (racoon, pluto)
  → Messages: SADB_ADD, SADB_DELETE, SADB_GET, SADB_ACQUIRE, etc.
  → SADB_ACQUIRE = kernel asking IKE daemon to create SA for this traffic
```

**Netlink XFRM (modern, Linux-specific):**
```
socket(AF_NETLINK, SOCK_RAW, NETLINK_XFRM)
  → Used by strongSwan, libreswan modern versions
  → Messages: XFRM_MSG_NEWSA, XFRM_MSG_DELSA, XFRM_MSG_ACQUIRE, etc.
  → More granular control, better performance
```

---

## 3. Debugging Tools Inventory

### 3.1 Linux — ip xfrm (Primary Tool)

`ip xfrm` is your primary window into the kernel IPsec state. Every SA and policy the kernel is managing is visible here.

#### View All SA States (SAD)

```bash
# Show all installed SAs (Security Associations)
ip xfrm state

# Example output of a working ESP tunnel SA:
# src 203.0.113.1 dst 198.51.100.1
#         proto esp spi 0xc6ba3f21 reqid 1 mode tunnel
#         replay-window 32 seq 0x00000000 flag noecn
#         auth-trunc hmac(sha256) 0xDEADBEEF... 128
#         enc cbc(aes) 0xCAFEBABE...
#         encap type espinudp sport 4500 dport 4500 addr 0.0.0.0   ← NAT-T in use
#         anti-replay context: seq 0x0, oseq 0x64, bitmap 0xffffffff
#         lifetime config:
#           limit: soft (KB) UNSPEC, hard (KB) UNSPEC
#           limit: soft (sec) 3240, hard (sec) 3600
#           limit: soft (pkts) UNSPEC, hard (pkts) UNSPEC
#         lifetime current:
#           600(bytes), 10(packets)
#           added Thu Jan  1 00:10:00 2026 use Thu Jan  1 00:10:05 2026
#         stats:
#           replay-window 0 replay 0 failed 0

# Show specific SA by SPI
ip xfrm state show spi 0xc6ba3f21 proto esp dst 198.51.100.1

# Short: just list SPIs and directions
ip xfrm state list | grep -E "src|spi|mode"
```

#### View All Policies (SPD)

```bash
# Show all SPD policies
ip xfrm policy

# Example output of a working tunnel policy:
# src 192.168.1.0/24 dst 10.0.0.0/8
#         dir out priority 375423 ptype main
#         tmpl src 203.0.113.1 dst 198.51.100.1
#                 proto esp spi 0xc6ba3f21 reqid 1 mode tunnel
# src 10.0.0.0/8 dst 192.168.1.0/24
#         dir fwd priority 375423 ptype main
#         tmpl src 198.51.100.1 dst 203.0.113.1
#                 proto esp reqid 1 mode tunnel
# src 10.0.0.0/8 dst 192.168.1.0/24
#         dir in priority 375423 ptype main
#         tmpl src 198.51.100.1 dst 203.0.113.1
#                 proto esp reqid 1 mode tunnel

# CRITICAL: For each bidirectional tunnel, you need THREE policies:
#   dir out  (outbound from local subnet)
#   dir in   (inbound to local subnet)
#   dir fwd  (forwarding, needed on gateways)

# Count policies — sanity check
ip xfrm policy | grep -c "^src"
```

#### XFRM Statistics — Counters for Diagnosis

```bash
# Per-SA statistics (replay errors, auth failures)
ip -s xfrm state

# Global XFRM counters (kernel-wide)
cat /proc/net/xfrm_stat

# Column meanings in /proc/net/xfrm_stat:
# XfrmInError         — inbound generic errors
# XfrmInBufferError   — packet too large for buffer
# XfrmInHdrError      — IP header error
# XfrmInNoStates      — no SA found for incoming packet
# XfrmInStateProtoError — SA protocol error (AH/ESP mismatch)
# XfrmInStateModeError  — SA mode mismatch (tunnel/transport)
# XfrmInStateSeqError   — sequence number overflow (replay window too small)
# XfrmInStateExpired    — SA expired (lifetime exceeded)
# XfrmInStateMismatch   — SA selector mismatch
# XfrmInStateInvalid    — SA in invalid state
# XfrmInTmplMismatch    — SPD template mismatch
# XfrmInNoPols          — no SPD policy found for inbound packet
# XfrmInPolBlock        — SPD policy blocked packet
# XfrmInPolError        — SPD policy error
# XfrmOutError          — outbound generic errors
# XfrmOutBundleGenError — SA bundle generation error
# XfrmOutBundleCheckError — SA bundle check error
# XfrmOutNoStates       — no SA found (IKE needs to create one)
# XfrmOutStateProtoError — outbound SA protocol error
# XfrmOutStateModeError  — outbound SA mode error
# XfrmOutStateSeqError   — sequence number exhausted (CRITICAL: force rekey!)
# XfrmOutStateExpired    — outbound SA expired
# XfrmOutPolBlock        — outbound policy blocked
# XfrmOutPolDead         — outbound policy references dead SA
# XfrmOutPolError        — outbound policy error
# XfrmFwdHdrError        — forwarding header error

# Watch xfrm stats in real time (watch changes)
watch -n 1 'cat /proc/net/xfrm_stat | grep -v "^$"'

# One-liner: show only non-zero counters
awk '$2 != 0' /proc/net/xfrm_stat
```

#### XFRM Monitor — Real-Time Events

```bash
# Monitor XFRM kernel events in real time
# Shows SA creation, deletion, expiry events, acquire events
ip xfrm monitor

# You will see:
# Policies:
#   Added:   when IKE installs a new SPD policy
#   Deleted: when SA expires and policy is removed
# States (SAs):
#   Added:   when IKE installs a new Child SA (KEYMAT loaded)
#   Deleted: when SA expires or is deleted
# Acquire:
#   ACQUIRE: CRITICAL — kernel telling IKE "I need an SA for this traffic!"
#            If you see ACQUIRE events and IKE doesn't create SAs, IKE is broken.

# In another terminal, try to ping through the tunnel:
# ping 10.0.2.1  ← triggers ACQUIRE if no SA exists
```

### 3.2 tcpdump — Packet Captures

```bash
# Capture IKE negotiations (UDP 500 and 4500)
tcpdump -i eth0 -n 'udp port 500 or udp port 4500' -w ike_capture.pcap

# Capture raw ESP/AH packets (the encrypted data plane)
tcpdump -i eth0 -n 'proto esp or proto ah'

# Capture everything related to a specific peer
tcpdump -i eth0 -n 'host 198.51.100.1' -w peer_traffic.pcap

# Verbose IKE capture with hex output for manual analysis
tcpdump -i eth0 -n -X -vvv 'udp port 500'

# Capture JUST IKE_SA_INIT exchanges (first 2 IKEv2 messages, no encryption yet)
# These are large UDP packets — the DH public key makes them big
tcpdump -i eth0 -n 'udp port 500 and greater 200' -w ike_init.pcap

# Capture NAT-T ESP (ESP wrapped in UDP 4500)
tcpdump -i eth0 -n 'udp port 4500'

# Capture on the DECRYPTED side (inside interface after IPsec processing)
# On Linux, use the xfrm interface
tcpdump -i xfrm0 -n  # if configured

# Useful flags:
#  -n       : no DNS resolution (faster)
#  -X       : hex + ASCII dump
#  -vvv     : maximum verbosity (shows IKE fields if Wireshark-style)
#  -s 0     : capture full packet (default in modern tcpdump is 65535)
#  -w file  : write to pcap for Wireshark analysis
#  -e       : also print link-layer headers (MAC addresses)
#  -c N     : stop after N packets
#  -G N     : rotate file every N seconds
```

### 3.3 ss / netstat — Socket and Connection State

```bash
# Show UDP 500 and 4500 socket state (IKE daemon sockets)
ss -ulnp | grep -E "500|4500"

# Expected for a running IKE daemon:
# UNCONN  0  0  0.0.0.0:500   0.0.0.0:*  users:(("charon",pid=1234,fd=5))
# UNCONN  0  0  0.0.0.0:4500  0.0.0.0:*  users:(("charon",pid=1234,fd=6))

# If no socket on 500: IKE daemon is not running or crashed
# If socket exists but no peer traffic: firewall blocking, network issue
```

### 3.4 ipsec / swanctl — strongSwan CLI

```bash
# List all active IKE SAs (control plane)
swanctl --list-sas

# List all active IPsec SAs (data plane, Child SAs)
swanctl --list-sas --raw  # More detail

# Load configuration without restart
swanctl --load-all

# Initiate a specific connection
swanctl --initiate --child site-b

# Terminate a connection
swanctl --terminate --ike site-b

# Show loaded connections (configured, may or may not be up)
swanctl --list-conns

# Show loaded credentials (certs, keys)
swanctl --list-certs

# Log level control (verbose output)
swanctl --log-level 4  # 0=error, 1=warn, 2=info, 3=debug, 4=very-verbose

# Alternative: ipsec command (older strongSwan interface)
ipsec statusall
ipsec status
ipsec up <connection-name>
ipsec down <connection-name>
ipsec restart
```

### 3.5 ip route — Routing Verification

```bash
# Does traffic for remote subnet go through the right interface?
ip route get 10.0.2.20

# Example output (should route via the VPN gateway interface):
# 10.0.2.20 via 203.0.113.1 dev eth0 src 192.168.1.1

# Show all routes
ip route show table all | grep -v "^fe"

# Check if IPsec tunnel interface exists (VTI or XFRM based VPN)
ip link show type vti
ip link show type xfrm
```

### 3.6 sysctl — Kernel IPsec Parameters

```bash
# Show all IPsec/net-related sysctl values
sysctl -a | grep -E "xfrm|ipsec|esp|ah"

# Key parameters to check:
sysctl net.ipv4.conf.all.send_redirects     # Should be 0 for VPN gateways
sysctl net.ipv4.conf.all.accept_redirects   # Should be 0 for VPN gateways
sysctl net.ipv4.ip_forward                 # Must be 1 for gateway
sysctl net.ipv4.conf.all.rp_filter         # Strict=1 can break asymmetric routing
sysctl net.core.rmem_max                   # UDP receive buffer (impacts IKE)
sysctl net.core.wmem_max                   # UDP send buffer
```

### 3.7 setkey — PF_KEY Interface (Legacy)

```bash
# List all SAs via PF_KEY (works with older daemons)
setkey -D

# List all SPD policies via PF_KEY
setkey -DP

# Flush all SAs (dangerous in production!)
setkey -F

# Flush all policies (dangerous in production!)
setkey -FP

# Run a setkey script
setkey -f /etc/ipsec-manual.conf
```

### 3.8 openssl — Certificate and Crypto Debugging

```bash
# Verify a certificate chain
openssl verify -CAfile /etc/ssl/certs/ca-bundle.crt /etc/ipsec.d/certs/peer.crt

# Show certificate details (check CN, SAN, validity, extensions)
openssl x509 -in /etc/ipsec.d/certs/peer.crt -text -noout

# Check certificate validity dates
openssl x509 -in /etc/ipsec.d/certs/peer.crt -noout -dates

# Verify a private key matches a certificate
# Method: compare public key fingerprints
openssl x509 -in cert.pem -noout -pubkey | openssl md5
openssl pkey -in key.pem -pubout | openssl md5
# If both md5 hashes match → key and cert are paired correctly

# Check CRL (Certificate Revocation List)
openssl crl -in /etc/ipsec.d/crls/ca.crl -text -noout

# Verify cert against CRL
openssl verify -CAfile ca.crt -crl_check -CRLfile ca.crl peer.crt

# Test PKCS#12 file
openssl pkcs12 -in bundle.p12 -info

# Check DH group parameters
openssl dhparam -check -in dh2048.pem

# Generate test certificates for lab environments
openssl req -x509 -newkey rsa:4096 -keyout test_key.pem \
  -out test_cert.pem -days 365 -nodes \
  -subj "/CN=ipsec-test.example.com"
```

### 3.9 strace — Low-Level IKE Daemon Debugging

```bash
# Trace system calls of the charon daemon
# Useful when IKE daemon appears hung or crashing
strace -p $(pgrep charon) -e trace=network,read,write 2>&1 | head -100

# Trace file operations (certificate loading, config reading)
strace -p $(pgrep charon) -e trace=openat,read,close 2>&1

# Trace Netlink messages to kernel XFRM
strace -p $(pgrep charon) -e trace=sendmsg,recvmsg 2>&1 | grep netlink
```

### 3.10 conntrack — Connection Tracking (NAT Interactions)

```bash
# Show connection tracking table (important for NAT-T troubleshooting)
conntrack -L | grep -E "udp.*500|udp.*4500"

# Show UDP 500/4500 tracked connections
conntrack -L -p udp | grep ":500 "

# If NAT-T is being used, you should see UDP 4500 entries, not 500
# IKE moves to 4500 after NAT detection

# Flush connection tracking for a specific peer (when stuck)
conntrack -D -p udp --dport 500 --orig-dst 198.51.100.1

# Show statistics
conntrack -S
```

---

## 4. IKE Message Analysis

### 4.1 IKEv2 Message Header Anatomy

Before you can analyze packet captures, you must know what every byte means.

```
IKEv2 Generic Header (28 bytes):

Byte  0-7:  Initiator's SPI (8 bytes, random, set by initiator)
Byte  8-15: Responder's SPI (8 bytes; zero in first request from initiator)
Byte 16:    Next Payload type (what payload comes after this header)
Byte 17:    Major Version (4 bits, must be 2) | Minor Version (4 bits, must be 0)
Byte 18:    Exchange Type
            34 (0x22) = IKE_SA_INIT
            35 (0x23) = IKE_AUTH
            36 (0x24) = CREATE_CHILD_SA
            37 (0x25) = INFORMATIONAL
Byte 19:    Flags
            Bit 3 (0x08): Initiator flag (1 = this is initiator)
            Bit 4 (0x10): Version flag (1 = higher version available)
            Bit 5 (0x20): Response flag (1 = this is a response)
Byte 20-23: Message ID (u32, big-endian)
            IKE_SA_INIT: 0
            IKE_AUTH: 1
            Subsequent: increment per request
Byte 24-27: Total Length (u32, big-endian, including this header)

Example IKE_SA_INIT Request (hex):
  A1 B2 C3 D4 E5 F6 07 18   ← Initiator SPI
  00 00 00 00 00 00 00 00   ← Responder SPI (zero: first request)
  21                         ← Next Payload = SA (0x21 = 33)
  20                         ← Version: 2.0
  22                         ← Exchange: IKE_SA_INIT (0x22 = 34)
  08                         ← Flags: Initiator (bit 3 set)
  00 00 00 00               ← Message ID: 0
  00 00 01 A8               ← Total Length: 424 bytes
```

### 4.2 IKEv2 Payload Types Reference

```
Payload Code → Name → Purpose
--------------------------------------
0  (0x00) → No Next Payload (last payload)
2  (0x02) → Proposal            (inside SA payload)
3  (0x03) → Transform           (inside Proposal)
33 (0x21) → SA                  (Security Association: algorithm proposals)
34 (0x22) → KE                  (Key Exchange: DH public key)
35 (0x23) → IDi                 (Initiator Identity)
36 (0x24) → IDr                 (Responder Identity)
37 (0x25) → CERT                (Certificate)
38 (0x26) → CERTREQ             (Certificate Request)
39 (0x27) → AUTH                (Authentication Proof)
40 (0x28) → Ni/Nr               (Nonce)
41 (0x29) → N                   (Notify)
42 (0x2A) → D                   (Delete)
43 (0x2B) → V                   (Vendor ID)
44 (0x2C) → TSi                 (Traffic Selector - Initiator)
45 (0x2D) → TSr                 (Traffic Selector - Responder)
46 (0x2E) → SK                  (Encrypted + Authenticated Payload)
47 (0x2F) → CP                  (Configuration: IP assignment)
48 (0x30) → EAP                 (Extensible Authentication)

Critical bit (bit 7): If set, payload is CRITICAL — must understand or reject message.
```

### 4.3 Notify (N) Payload Types — The Most Important for Debugging

Notify payloads carry error codes and status information. Learning these is essential:

```
Error Notifies (cause negotiation failure):
  1     UNSUPPORTED_CRITICAL_PAYLOAD   — Received unknown critical payload
  4     INVALID_IKE_SPI               — Wrong SPIs
  5     INVALID_MAJOR_VERSION         — Wrong IKE version
  7     INVALID_SYNTAX                — Malformed message
  11    INVALID_MESSAGE_ID            — Wrong message ID
  14    INVALID_SPI                   — Invalid SPI in ESP/AH
  17    NO_PROPOSAL_CHOSEN            — Responder rejected all proposals ← VERY COMMON
  24    INVALID_KE_PAYLOAD            — Wrong DH group (mismatch) ← COMMON
  34    AUTHENTICATION_FAILED         — AUTH payload verification failed ← COMMON
  35    SINGLE_PAIR_REQUIRED          — Traffic selector narrowing needed
  36    NO_ADDITIONAL_SAS             — SA limit reached
  37    INTERNAL_ADDRESS_FAILURE      — IP assignment failed
  38    FAILED_CP_REQUIRED            — Config Payload required but missing
  39    TS_UNACCEPTABLE               — Traffic selectors rejected ← COMMON
  40    INVALID_SELECTORS             — Unexpected inner packet selectors
  41    UNACCEPTABLE_ADDRESSES        — Address not acceptable
  42    UNEXPECTED_NAT_DETECTED       — NAT where not expected

Status Notifies (informational, not errors):
  16384 INITIAL_CONTACT               — First contact (delete old SAs)
  16385 SET_WINDOW_SIZE               — Set anti-replay window size
  16386 ADDITIONAL_TS_POSSIBLE        — TS narrowing available
  16387 IPCOMP_SUPPORTED              — IP compression supported
  16388 NAT_DETECTION_SOURCE_IP       — NAT detection hash (source)
  16389 NAT_DETECTION_DESTINATION_IP  — NAT detection hash (dest)
  16390 COOKIE                        — Anti-DoS cookie
  16391 USE_TRANSPORT_MODE            — Request transport mode
  16392 HTTP_CERT_LOOKUP_SUPPORTED    — Can fetch cert via HTTP
  16393 REKEY_SA                      — Identifies SA being rekeyed
  16394 ESP_TFC_PADDING_NOT_SUPPORTED — No traffic flow confidentiality
  16395 NON_FIRST_FRAGMENTS_ALSO      — Handle non-first fragments
  16396 MOBIKE_SUPPORTED              — RFC 4555 MOBIKE supported
  16397 ADDITIONAL_IP4_ADDRESS        — Additional IPv4 address (MOBIKE)
  16430 SIGNATURE_HASH_ALGORITHMS     — Supported hash algorithms for sig
```

### 4.4 IKEv2 Traffic Selector Format

Traffic selectors are critical — mismatches cause `TS_UNACCEPTABLE` errors:

```
Traffic Selector payload:
  Number of TSs: (count)
  For each TS:
    TS Type:   7 = TS_IPV4_ADDR_RANGE
               8 = TS_IPV6_ADDR_RANGE
    IP Protocol ID: 0=any, 6=TCP, 17=UDP, 58=ICMPv6
    Selector Length: length of this TS entry
    Start Port: (inclusive)
    End Port:   (inclusive)
    Start Address: (first IP in range)
    End Address:   (last IP in range)

Example: Match all traffic from 192.168.1.0/24 to 10.0.0.0/8
  TS Type: 7 (IPv4)
  Proto: 0 (any)
  Port: 0 - 65535 (any)
  Start: 192.168.1.0
  End:   192.168.1.255

Example: Match only SSH from any to 10.0.1.5:
  TS Type: 7
  Proto: 6 (TCP)
  Port: 22 - 22
  Start: 0.0.0.0
  End:   255.255.255.255
```

---

## 5. IKEv1 Debugging

### 5.1 IKEv1 Failure Points Map

```
IKEv1 Phase 1 Main Mode (6 messages):

  MSG 1 → MSG 2: SA Proposal/Accept
    FAILURE: "No proposal chosen" / "No acceptable transform"
    ROOT CAUSE: Algorithm mismatch between peers
    
  MSG 3 → MSG 4: DH Key Exchange
    FAILURE: "Invalid key information"
    ROOT CAUSE: DH group mismatch, weak group rejected
    
  MSG 5 → MSG 6: Identity + Auth (encrypted)
    FAILURE: "Authentication failed" / "Invalid hash"
    ROOT CAUSE: PSK mismatch, cert failure, identity mismatch

IKEv1 Phase 2 Quick Mode (3 messages):

  MSG 1 → MSG 2: SA Proposal
    FAILURE: "No proposal chosen"
    ROOT CAUSE: PFS mismatch, algorithm mismatch, selector mismatch
    
  MSG 3: Confirmation
    FAILURE: Hash mismatch
    ROOT CAUSE: Nonce derivation error, proxy ID mismatch
```

### 5.2 IKEv1 racoon / ike-scan Debugging

```bash
# Test IKEv1 connectivity and see what proposals the peer accepts
ike-scan --showbackoff --aggressive 198.51.100.1

# Test specific IKEv1 proposals
ike-scan --trans=5,2,1,2 198.51.100.1
# Format: --trans=encryption,hash,auth,dh
# encryption: 1=DES, 3=3DES, 5=AES-128, 7=AES-192, 8=AES-256
# hash: 1=MD5, 2=SHA1, 4=SHA256, 5=SHA384, 6=SHA512
# auth: 1=PSK, 3=RSA-sig, 64221=XAUTH-PSK
# dh: 1=768, 2=1024, 5=1536, 14=2048

# Test IKEv1 with PSK (aggressive mode, exposes identity)
ike-scan --aggressive --id=vpn-client 198.51.100.1

# Scan for IKEv1 / IKEv2 support
ike-scan --ikev2 198.51.100.1

# racoon debug logging
racoon -F -v -d  # Foreground, verbose, debug
# Log levels in racoon.conf:
# path log "/var/log/racoon.log";
# log debug2;

# racoon: check current SA status
racoonctl show-sa isakmp  # Phase 1 SAs
racoonctl show-sa esp     # Phase 2 SAs
racoonctl show-sa ah      # Phase 2 SAs (AH)
racoonctl delete-sa isakmp 198.51.100.1  # Delete Phase 1 SA
```

### 5.3 IKEv1 Phase 1 Proposal Debugging

The most common Phase 1 failure is algorithm mismatch. The exchange looks like:

```
ASCII Timeline — Phase 1 Proposal Failure:

Initiator (A)                              Responder (B)
     |                                          |
     |──── MSG1: SA Proposal ────────────────>  |
     |  Proposals:                              |
     |    #1: AES-256 + SHA-256 + DH-14         |
     |    #2: AES-128 + SHA-1   + DH-14         |
     |    #3: 3DES   + MD5      + DH-2          |
     |                                          |
     |                          ┌───────────────┤
     |                          │ Check my list │
     |                          │ No match!     │
     |                          │ (Peer only    │
     |                          │  supports     │
     |                          │  AES-256+SHA1 │
     |                          │  +DH-2, not   │
     |                          │  listed)      │
     |                          └───────────────┤
     |                                          │
     |<──── NO-PROPOSAL-CHOSEN ──────────────── |
     |                                          |
Connection fails with "no proposal chosen"

FIX: Add AES-256 + SHA-1 + DH-2 to initiator's proposals
     OR  update responder to accept AES-256 + SHA-256 + DH-14
```

**How to find what the peer supports:**

```bash
# Use ike-scan to fingerprint peer proposals
ike-scan --showbackoff --multiline 198.51.100.1

# Test each combination manually:
for enc in 5 7 8; do          # AES-128, AES-192, AES-256
  for hash in 1 2 4; do       # MD5, SHA1, SHA256
    for dh in 2 5 14; do      # 1024, 1536, 2048
      ike-scan --trans=$enc,$hash,1,$dh 198.51.100.1 2>/dev/null \
        | grep -q "SA=" && echo "MATCH: enc=$enc hash=$hash dh=$dh"
    done
  done
done
```

### 5.4 IKEv1 Phase 1 PSK Debugging

```
PSK Authentication Failure Sequence:

Initiator (A)                              Responder (B)
     |                                          |
     |──── MSG 1-4: DH Exchange ─────────────> |
     |  (Phase 1 proposals + DH keys exchange) |
     |                                          |
     |──── MSG 5: ID + Hash [ENCRYPTED] ─────> |
     |  IDii = "192.168.1.1"  (Identity)       |
     |  HASH_I = prf(SKEYID, ...) using PSK_A  |
     |                                          |
     |                     ┌────────────────────┤
     |                     │ Look up PSK        │
     |                     │ for ID "192.168.1.1"│
     |                     │ Found: PSK_B       │
     |                     │ Compute HASH_I     │
     |                     │  using PSK_B       │
     |                     │ Compare: FAIL!     │
     |                     │ PSK_A ≠ PSK_B      │
     |                     └────────────────────┤
     |                                          │
     |<──── MSG 6: INVALID-ID-INFORMATION ──── |
     |  OR: connection drops (no response)     |
     |                                          |
Log message: "Phase 1 authentication failed"
            "hash mismatch"
            "invalid ID information"

COMMON CAUSES:
1. PSK text mismatch (typo, encoding difference)
2. PSK matched to wrong identity (IP vs FQDN)
3. Identity type mismatch (one side uses IP, other uses FQDN)
4. Whitespace in PSK (trailing space is invisible)
5. PSK encoding (ASCII vs hex) mismatch
```

**Debugging PSK Issues:**

```bash
# Compute the HASH_I that your side generates (Python):
python3 << 'EOF'
import hmac, hashlib

# These values from Wireshark/packet capture:
psk = b"MySecretKey"
skeyid = b"\xDE\xAD\xBE\xEF..."  # from packet capture

# HASH_I = prf(SKEYID, g^xy | CKY-I | CKY-R | SA_I | IDii)
# This requires all the IKEv1 state from the exchange
# For debugging, focus on: are both sides using IDENTICAL PSK bytes?

# Compare byte-by-byte:
psk_a = "MyPSK"       # Your side
psk_b = "MyPSK "      # Remote side (trailing space! invisible!)
print(f"Match: {psk_a == psk_b}")  # False
print(f"Lengths: {len(psk_a)} vs {len(psk_b)}")  # 5 vs 6
EOF

# In strongSwan, check PSK is loaded correctly:
swanctl --list-certs  # Shows loaded credentials

# In libreswan, verify PSK:
ipsec showhostkey --psk   # Display the PSK being used
```

---

## 6. IKEv2 Debugging

### 6.1 IKEv2 IKE_SA_INIT Failures

```
IKE_SA_INIT Exchange — Failure Analysis:

Initiator (A)                              Responder (B)
     |                                          |
     |──── IKE_SA_INIT Request ───────────────> |
     |  HDR, SAi1, KEi(DH-19), Ni              |
     |  NAT_DETECTION_SOURCE_IP                 |
     |  NAT_DETECTION_DESTINATION_IP            |
     |                                          |

FAILURE SCENARIO 1: No Proposal Chosen
     |<──── IKE_SA_INIT Response ────────────── |
     |  HDR, N(NO_PROPOSAL_CHOSEN)             |
     |                                          |
  Root Cause: Initiator proposed DH-19 (ECP-256)
              Responder only accepts DH-14 (MODP-2048)
  Fix: Match DH groups in proposal
     
FAILURE SCENARIO 2: Wrong DH Group
     |<──── IKE_SA_INIT Response ────────────── |
     |  HDR, N(INVALID_KE_PAYLOAD), N(DH-14)  |
     |  (Tells initiator: "use DH group 14")   |
     |                                          |
     |──── IKE_SA_INIT Request (RETRY) ──────> |
     |  HDR, SAi1, KEi(DH-14), Ni              |
     |  (Now using DH-14 as responder requested)|
     |                                          |
  This is NORMAL behavior — not a failure!
  Initiator adjusts DH group and retries automatically.
  
FAILURE SCENARIO 3: DoS Cookie Required
     |<──── IKE_SA_INIT Response ────────────── |
     |  HDR, N(COOKIE, <cookie-data>)          |
     |  (Responder under load, wants cookie)   |
     |                                          |
     |──── IKE_SA_INIT Request (WITH COOKIE) > |
     |  HDR, N(COOKIE, <cookie-data>), SA, KE  |
     |  (Must include cookie in retry)          |
     |                                          |
  This is NORMAL DoS protection, not a failure.
  
FAILURE SCENARIO 4: Firewall Blocking Large UDP
     |  [No response to IKE_SA_INIT]           |
     |  [Timeout after 4 retransmissions]       |
     |                                          |
  Root Cause: IKE_SA_INIT with DH public key is large (500-1000+ bytes)
              Some firewalls or paths block large UDP packets
              UDP fragmentation may be blocked
  Fix: Check MTU, check firewall rules for large UDP
       Use smaller DH group temporarily to test
       Check: ping with DF bit and large payload
```

#### IKE_SA_INIT Debugging Commands:

```bash
# On strongSwan, enable verbose logging for IKE_SA_INIT:
# In /etc/strongswan.d/charon-logging.conf or similar:
# ike = 4
# net = 4
# enc = 4

# Trigger connection and watch logs:
swanctl --initiate --child mychild 2>&1 &
journalctl -fu strongswan | grep -E "IKE_SA_INIT|INVALID_KE|NO_PROPOSAL"

# Check what proposals are being sent/accepted:
journalctl -fu strongswan | grep -E "selected proposal|no acceptable"
```

### 6.2 IKEv2 IKE_AUTH Failures — Authentication

```
IKE_AUTH Exchange — Authentication Failure Analysis:

IKE_AUTH uses SK (encrypted) payloads. After IKE_SA_INIT,
both sides have SK_ei, SK_er, SK_ai, SK_ar.

Initiator (A)                              Responder (B)
     |                                          |
     |──── IKE_AUTH Request [ENCRYPTED] ──────> |
     |  SK { IDi, [CERT,] [CERTREQ,]           |
     |        AUTH, SAi2, TSi, TSr }           |
     |                                          |

AUTH Payload Computation:
  For PSK:
    AUTH = prf(prf(PSK, "Key Pad for IKEv2"), 
               <signed octets>)
    where <signed octets> = IKE_SA_INIT_msg | Ni | prf(SK_pi, IDi)

  For RSA Signature:
    AUTH = Sign(private_key, 
                <signed octets>)

FAILURE SCENARIO 1: PSK Mismatch
     |<──── IKE_AUTH Response [ENCRYPTED] ───── |
     |  SK { N(AUTHENTICATION_FAILED) }        |
     |                                          |
  Root Cause: PSK strings differ between peers
  
FAILURE SCENARIO 2: Certificate Not Trusted
     |<──── IKE_AUTH Response [ENCRYPTED] ───── |
     |  SK { N(AUTHENTICATION_FAILED) }        |
     |                                          |
  Root Cause: Initiator's cert not signed by trusted CA
              CRL check failed
              Certificate expired
              
FAILURE SCENARIO 3: Identity Mismatch
  The IDi payload must match what the cert says (CN or SAN)
  If cert says CN=vpn.example.com but IDi says IP:192.168.1.1
  → AUTH fails because signed data includes IDi

FAILURE SCENARIO 4: Traffic Selector Rejection
     |<──── IKE_AUTH Response [ENCRYPTED] ───── |
     |  SK { IDr, AUTH, SAr2,                  |
     |        TSi(narrowed), TSr(narrowed),     |
     |        N(TS_UNACCEPTABLE) }              |
     |  OR: TSi/TSr narrowed down to empty set |
     |                                          |
  Root Cause: Proposed TS doesn't match any policy on responder
  Fix: Widen or match TS on both sides
```

### 6.3 IKEv2 AUTH Payload — Deep Dive

The AUTH payload is the most commonly misunderstood and misdebugged part of IKEv2:

```
AUTH Payload Construction (for PSK):

Step 1: Compute InitiatorSignedOctets
  InitiatorSignedOctets =
    IKE_SA_INIT_request_message    (raw bytes, exactly as sent)
    | Ni_value                     (nonce, payload data only)
    | prf(SK_pi, IDi_payload_body) (pseudo-random of identity)

  CRITICAL: "IKE_SA_INIT_request_message" means the EXACT bytes
  of the IKE_SA_INIT request, including the header.
  Any retransmission must use the FIRST sent copy.

Step 2: Compute AUTH
  AUTH = prf(prf(PSK, "Key Pad for IKEv2"), InitiatorSignedOctets)
  
  Where:
  - "Key Pad for IKEv2" is a literal 17-byte ASCII string
  - The inner prf derives a pseudo-key from the PSK
  - The outer prf signs the octets with that key
  
  This double-PRF ensures that even if PSK is weak,
  the AUTH value cannot be predicted without knowing the
  specific nonces and session parameters.

Common Bug: Using PSK bytes directly without "Key Pad" derivation
            → AUTH value will be wrong
            → Both sides will see AUTHENTICATION_FAILED
```

### 6.4 IKEv2 CREATE_CHILD_SA Failures

```
CREATE_CHILD_SA — Rekeying Child SA:

Initiator (A)                              Responder (B)
     |                                          |
     |── CREATE_CHILD_SA [ENCRYPTED] ─────────> |
     |  SK { SA, Ni, [KEi], TSi, TSr,          |
     |        N(REKEY_SA, old_SPI) }           |
     |                                          |

FAILURE: SA rekeying fails but old SA still works briefly

Log: "unable to rekey Child SA ... CHILD_SA_NOT_FOUND"
Root Cause: Race condition — remote side deleted old SA before
            rekeying completed. This is a known IKEv2 issue.
Fix: Check "rekey margin" settings — start rekeying earlier
     strongSwan: rekey_time, margintime settings

FAILURE: PFS DH group mismatch during rekey
     |<── CREATE_CHILD_SA Response ─────────── |
     |  SK { N(NO_PROPOSAL_CHOSEN) }          |
     |                                          |
Root Cause: Child SA proposal includes DH group for PFS,
            but peer doesn't support it or has different group
Fix: Ensure both sides have matching PFS/DH settings
     Or disable PFS (dh_group = none)

FAILURE: Simultaneous rekeying
  Both sides initiate rekey at the same time
  → Creates duplicate SAs temporarily
  → Protocol handles with "delete older SA" logic
  → Should self-resolve; if not, indicates a bug in IKE daemon
```

---

## 7. ESP and AH Packet Debugging

### 7.1 ESP Packet Anatomy — Byte-Level Analysis

When you capture raw ESP packets with tcpdump and need to analyze them manually:

```
Raw ESP Tunnel Packet — Byte Map:

Ethernet Frame (14 bytes):
  00-05: Destination MAC
  06-11: Source MAC
  12-13: EtherType (0x0800 = IPv4)

Outer IPv4 Header (20 bytes):
  14:    Version+IHL   = 0x45 (IPv4, 20-byte header)
  15:    DSCP+ECN
  16-17: Total Length
  18-19: Identification
  20-21: Flags+Fragment Offset
  22:    TTL
  23:    Protocol       = 0x32 (50 decimal = ESP)  ← KEY FIELD
  24-25: Header Checksum
  26-29: Source IP     (Gateway 1: 203.0.113.1)
  30-33: Destination IP (Gateway 2: 198.51.100.1)

ESP Header (8 bytes):
  34-37: SPI            (e.g., 0xC6BA3F21)  ← Use to find SA
  38-41: Sequence Number (e.g., 0x00000064 = 100)  ← Anti-replay

  For AES-CBC: 16-byte IV follows here (bytes 42-57)
  For AES-GCM: 8-byte explicit IV (bytes 42-49)
  For ChaCha20: 8-byte explicit IV (bytes 42-49)

Encrypted Payload (variable):
  [bytes after IV]: Everything from here to (packet_end - icv_len)
  is encrypted. You cannot read it without the keys.
  Contains: Original IP header + TCP/UDP/etc + padding + trailer

ESP Trailer (inside encrypted region, 2 bytes before ICV):
  Pad Length:  1 byte
  Next Header: 1 byte (4=IPv4 for tunnel, 6=TCP for transport)

ICV (Authentication Tag):
  Last N bytes of packet (before Ethernet FCS)
  HMAC-SHA1: 12 bytes
  HMAC-SHA256: 16 bytes
  AES-GCM-16: 16 bytes (GCM tag)

To find ICV boundary in tcpdump output:
  packet_len = outer IP total_length (bytes 16-17)
  esp_start  = outer IP header end (usually byte 34)
  icv_start  = esp_start + packet_len - ip_hdr_len - icv_len
  (icv_len = 12 for HMAC-SHA1-96, 16 for AES-GCM-16)
```

### 7.2 Decrypting ESP Packets for Debugging

In a lab environment or with known keys, you can decrypt ESP captures:

```bash
# Method 1: Wireshark ESP decryption (most practical)
# Edit → Preferences → Protocols → ESP
# Add entry:
#   Protocol: ESP
#   SPI: 0xC6BA3F21 (from ip xfrm state)
#   Encryption Algorithm: AES-256-GCM (16 octet ICV)
#   Encryption Key: (from ip xfrm state, hex string)
#   Authentication Algorithm: None (for AEAD)

# Method 2: Command-line ESP decryption (Python)
python3 << 'EOF'
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import struct

# Extract from Wireshark/tcpdump raw hex:
# (This is a toy example with known values)
spi = 0xC6BA3F21
seq_num = 100

# ESP Header (8 bytes) = AAD for AES-GCM
esp_hdr = struct.pack(">II", spi, seq_num)

# IV (8 bytes explicit for GCM, combined with 4-byte implicit from SA)
explicit_iv = bytes.fromhex("A3F29B1C7E44D80F")
implicit_iv = bytes.fromhex("DEADBEEF")  # First 4 bytes from SA keying material
full_nonce = implicit_iv + explicit_iv   # 12 bytes total nonce for GCM

# Ciphertext + 16-byte GCM tag
ciphertext_with_tag = bytes.fromhex("...")  # From packet capture

# Encryption key (from ip xfrm state)
encr_key = bytes.fromhex("DEADBEEF" * 8)  # 32 bytes for AES-256

# Decrypt
aesgcm = AESGCM(encr_key)
try:
    plaintext = aesgcm.decrypt(full_nonce, ciphertext_with_tag, esp_hdr)
    print(f"Decrypted: {plaintext.hex()}")
    # First bytes should be IPv4 header of original packet
    if plaintext[0] == 0x45:
        print("Inner packet is IPv4")
        import ipaddress
        src_ip = ipaddress.IPv4Address(plaintext[12:16])
        dst_ip = ipaddress.IPv4Address(plaintext[16:20])
        print(f"Inner: {src_ip} → {dst_ip}")
except Exception as e:
    print(f"Decryption/authentication failed: {e}")
    print("Possible causes: wrong key, wrong nonce, packet corrupted, wrong AAD")
EOF

# Method 3: ip xfrm state dump — get key material
# (Only in lab! Never log keys in production!)
ip -json xfrm state | python3 -c "
import json, sys
states = json.load(sys.stdin)
for s in states:
    print(f\"SPI: {s['spi']}\")
    if 'aead' in s:
        print(f\"  Algorithm: {s['aead']['alg']}\")
        print(f\"  Key: {s['aead']['key']}\")
"
```

### 7.3 ESP Decryption Failure Debugging

```
ESP Authentication Failure — Dropped Packets:

When kernel drops an ESP packet for auth failure:
  /proc/net/xfrm_stat shows: XfrmInStateProtoError incremented
  ip -s xfrm state shows:    stats: ... failed N  (N increases)

Sequence of events:
  1. ESP packet arrives
  2. SPI lookup in SAD → found
  3. Anti-replay check → passed (sequence number OK)
  4. HMAC verification → FAIL
  5. Packet dropped, no response to sender
  6. Sender keeps retransmitting TCP data
  7. Eventually TCP times out from sender's perspective

Logging this failure on Linux:
  # Enable kernel crypto debugging
  echo 1 > /sys/module/xfrm_algo/parameters/debug

  # Or check kernel logs
  dmesg | grep -i "esp\|xfrm\|bad\|drop"

Common causes of ESP auth failure:
  1. SA keys out of sync (rekeying race condition)
     → Packet encrypted with new key, received by peer with old key
     → Fix: Investigate rekeying logic; increase overlap window

  2. Packet corruption in transit (rare on modern networks)
     → Verify with ping -Q or tracepath

  3. MTU fragmentation causing truncated packet
     → If outer packet is fragmented, reassembly issue drops ESP
     → Fix: Reduce MTU, enable PMTUD

  4. Wrong SA selected for decryption
     → Two SAs with same SPI? (Should not happen)
     → Audit: ip xfrm state list | grep "spi"

  5. Hardware crypto offload error
     → Some NICs implement AES-NI incorrectly
     → Test: disable hardware offload
     → ethtool -K eth0 tx-ipsec-segmentation off rx-checksumming off
```

### 7.4 AH Debugging

AH is rarely used today (ESP+auth is preferred) but important to understand:

```
AH Packet — What AH Protects:

AH computes ICV over:
  - Immutable IPv4 Header fields (zero out mutable fields first)
  - AH Header (with ICV field set to zero during computation)
  - Original payload (TCP/UDP/etc)

Mutable IPv4 fields zeroed for AH ICV computation:
  - TOS (Type of Service, may be changed by QoS)
  - Flags (may change during fragmentation)
  - Fragment Offset
  - TTL (decremented by every router!)  ← CRITICAL
  - Header Checksum (recomputed after TTL change)

Why NAT breaks AH:
  NAT changes source IP address.
  AH authenticates source IP (even though TTL is zeroed).
  After NAT modifies src IP, AH ICV is invalid → DROP.

AH + NAT = BROKEN (no fix; use ESP instead)

Debugging AH issues:
  # Check AH packets arriving
  tcpdump -n -v 'proto 51'

  # AH packet format in tcpdump:
  # 14:03:22.412300 IP 203.0.113.1 > 198.51.100.1: AH(spi=0x00001234,seq=0x1): ...
  #                                                    ^^^SPI       ^^^sequence

  # If AH packets arrive but are dropped:
  cat /proc/net/xfrm_stat | grep -i "auth\|ah"
```

---

## 8. Cryptographic Failure Analysis

### 8.1 Algorithm Negotiation — Complete Failure Tree

```
IKEv2 Algorithm Negotiation Flow:

Initiator sends SA payload with proposals:
  PROPOSAL 1: ENCR_AES_GCM_16/256 + PRF_HMAC_SHA2_256 + DH_19
  PROPOSAL 2: ENCR_AES_CBC/256 + AUTH_HMAC_SHA2_256 + PRF_HMAC_SHA2_256 + DH_14
  PROPOSAL 3: ENCR_AES_CBC/128 + AUTH_HMAC_SHA1 + PRF_HMAC_SHA1 + DH_2

Responder evaluation:
  For each proposal (in order):
    For each transform type:
      Is at least one proposed algorithm supported?
    If ALL transform types match → this proposal is SELECTED
  If NO proposal matches → N(NO_PROPOSAL_CHOSEN)

Key rules:
  1. AEAD algorithms (AES-GCM, ChaCha20-Poly1305) do NOT need
     a separate AUTH transform. If you include AUTH with AEAD,
     the proposal is invalid.
  2. Non-AEAD algorithms (AES-CBC) REQUIRE both ENCR and AUTH.
  3. PRF is required for IKE SA but not for Child SA.
  4. DH is optional for Child SA (unless PFS is wanted).

Debugging "no proposal chosen":
  1. Enable maximum logging on both sides
  2. Compare exact proposal lists in logs
  3. Find the FIRST place they diverge:
     - Different ENCR algorithms?
     - Different key lengths?
     - AEAD on one side, non-AEAD on other (AUTH mismatch)?
     - Different DH groups?
     - PRF mismatch?
```

### 8.2 Key Length Mismatches

```
AES Key Length Handling:

In IKEv2 SA payload, key length is specified as an attribute:
  Transform Type 1 (ENCR): Transform ID=12 (AES-CBC) with:
    Attribute Type=14 (KEY_LENGTH): value=256 (bits)

Common mismatch:
  Side A: AES-CBC with 256-bit key
  Side B: AES-CBC with 128-bit key (different KEY_LENGTH attribute)
  
  These are DIFFERENT transforms — they won't match!
  The algorithm is the same (AES-CBC) but key size differs.

Debugging:
  Look for: "no acceptable ENCR"
  In strongSwan log: "received proposals: ... ESP:AES_CBC_128/..."
                     "configured proposals: ... ESP:AES_CBC_256/..."
  Fix: Align key lengths: ike=aes256-sha256-ecp256
                          esp=aes256gcm16-ecp256

For AES-GCM:
  AES-GCM-8  = 8-byte (64-bit) ICV  → Transform ID=18
  AES-GCM-12 = 12-byte (96-bit) ICV → Transform ID=19
  AES-GCM-16 = 16-byte (128-bit) ICV → Transform ID=20
  These are DIFFERENT transform IDs — must match exactly!
```

### 8.3 DH Group Mismatch — Extended Analysis

```
DH Group Negotiation in Detail:

In IKE_SA_INIT:
  Initiator sends ONE DH public key in KEi payload.
  The KEi payload specifies which DH group it used.
  
  If responder doesn't support that DH group:
    → Responds with N(INVALID_KE_PAYLOAD) + preferred group number
    → Initiator MUST retry with the correct group
    → This adds ONE round trip to IKE_SA_INIT
  
  This is NORMAL and not an error condition.
  Log: "received INVALID_KE_PAYLOAD notify for group X, sending new KE"

If BOTH sides agree on DH group in SA proposal but
the KEi payload uses a different group:
  → This is a protocol implementation bug
  → Should not happen with correct implementations

DH Group Strength Rankings (2026):
  DEPRECATED (do not use):
    Group 1  (MODP-768)  : Broken
    Group 2  (MODP-1024) : Broken  
    Group 5  (MODP-1536) : Borderline
  
  ACCEPTABLE (minimum):
    Group 14 (MODP-2048) : Minimum acceptable
    Group 15 (MODP-3072) : Good
    Group 16 (MODP-4096) : Good
  
  RECOMMENDED:
    Group 19 (ECP-256)   : Excellent (P-256)
    Group 20 (ECP-384)   : Excellent (P-384)
    Group 21 (ECP-521)   : Excellent (P-521)
  
  MODERN:
    Group 31 (Curve25519): RFC 8031, excellent

Checking DH group in use:
  swanctl --list-sas | grep "DH group\|dh"
  ip xfrm state | grep "group"
```

### 8.4 HMAC and ICV Verification

```
HMAC-SHA256-128 ICV Computation:

For ESP with HMAC-SHA256 truncated to 128 bits:
  Input:  ESP Header | IV | Ciphertext | Pad | PadLen | NextHdr
          (SPI + SeqNum + encrypted payload, excluding ICV itself)
  Key:    Auth key from SA (separate from encryption key)
  Output: SHA256 HMAC → truncate to 16 bytes (128 bits)
  
  Verification: Compute expected ICV, compare with received ICV.
  Constant-time comparison (not ==) to prevent timing attacks.

For AES-GCM-16 (AEAD):
  Input:  ESP Header (SPI + SeqNum) as AAD
          Ciphertext
          Full 12-byte nonce (4 implicit + 8 explicit)
  Output: 16-byte authentication tag (appended to ciphertext)
  
  Decryption and authentication are simultaneous.
  If tag verification fails → decryption is aborted, data discarded.

Why ICV failures happen:
  1. Wrong auth key (key derivation bug, or rekeying mismatch)
  2. Wrong algorithm (HMAC-SHA1 expected, HMAC-SHA256 sent)
  3. Truncation mismatch (96-bit vs 128-bit truncation)
  4. Packet modification in transit (legitimate corruption)
  5. Replay: sequence number accepted but packet modified
  6. IV included in ICV computation on one side but not other

Diagnosing in kernel:
  # Watch ICV failure counter increment
  watch -n 1 'awk "/XfrmInStateProtoError/{print}" /proc/net/xfrm_stat'
  
  # Per-SA auth error counter
  ip -s xfrm state show spi 0xC6BA3F21 proto esp dst 198.51.100.1
  # Look for: stats: ... failed N  (N = auth errors for this SA)
```

---

## 9. Certificate and PKI Failures

### 9.1 Certificate Chain Validation — Full Walkthrough

```
Certificate Chain Validation for IPsec:

Configuration:
  Root CA → Intermediate CA → Site Certificate

Validation steps during IKE_AUTH:
  1. Peer sends CERT payload containing its certificate
  2. Local system extracts issuer from cert
  3. Looks for issuer's cert (Intermediate CA)
     - In CERTREQ payload (peer told us which CAs they trust)
     - In local cert store (/etc/ipsec.d/cacerts/)
  4. Verifies Intermediate CA cert's signature using Root CA pubkey
  5. Verifies Site Cert signature using Intermediate CA pubkey
  6. Checks certificate validity dates (notBefore, notAfter)
  7. Checks certificate extensions:
     - Extended Key Usage: must include "IP Security" or be absent
     - Key Usage: must include digitalSignature
  8. Optionally checks CRL / OCSP for revocation
  9. Checks that certificate identity matches expected peer identity
     - IKEv2: ID payload must match cert CN or SAN

Failure points and log messages:
  "no trusted certificate found"
    → Root CA not in cacerts directory
    → Wrong CA cert loaded (different CA signed this cert)
    
  "certificate expired"  
    → Check: openssl x509 -in cert.pem -noout -dates
    → System clock wrong? (NTP!)
    → cert.pem is outdated
    
  "certificate revoked"
    → CRL check failed (cert was revoked)
    → CRL itself expired (need fresh CRL)
    
  "unable to get local issuer certificate"
    → Intermediate CA cert missing from chain/store
    
  "certificate verification failed"
    → Signature verification failed (wrong CA, corrupted cert)
    
  "no serial number"
    → Malformed certificate
    
  "peer certificate ID mismatch"
    → Certificate CN/SAN doesn't match configured rightid
```

### 9.2 Certificate Debugging Commands

```bash
# Complete certificate chain validation script
cat << 'EOF' > verify_ipsec_certs.sh
#!/bin/bash
CERT_DIR="/etc/ipsec.d"
PEER_CERT="$1"

echo "=== Checking Certificate: $PEER_CERT ==="

# Basic info
echo "--- Basic Info ---"
openssl x509 -in "$PEER_CERT" -noout -subject -issuer -dates

# Serial number (needed for CRL checking)
echo "--- Serial Number ---"
openssl x509 -in "$PEER_CERT" -noout -serial

# Check key usage and extended key usage
echo "--- Extensions ---"
openssl x509 -in "$PEER_CERT" -noout -text | grep -A2 "Key Usage"

# Check Subject Alternative Names (must match IKE identity)
echo "--- Subject Alternative Names ---"
openssl x509 -in "$PEER_CERT" -noout -text | grep -A5 "Subject Alternative"

# Verify signature chain
echo "--- Chain Validation ---"
openssl verify -CApath "$CERT_DIR/cacerts" "$PEER_CERT"

# Check CRL if available
if ls "$CERT_DIR/crls"/*.crl 2>/dev/null; then
    echo "--- CRL Check ---"
    for crl in "$CERT_DIR/crls"/*.crl; do
        # Check CRL expiry
        openssl crl -in "$crl" -noout -nextupdate
        # Check if cert is in CRL
        openssl verify -CApath "$CERT_DIR/cacerts" \
            -crl_check -CRLfile "$crl" "$PEER_CERT" 2>&1
    done
fi

# Check if private key matches cert (for own cert)
if [[ "$2" == "--check-key" ]]; then
    KEY="$3"
    echo "--- Key/Cert Match Check ---"
    CERT_MODULUS=$(openssl x509 -in "$PEER_CERT" -noout -modulus | md5sum)
    KEY_MODULUS=$(openssl rsa -in "$KEY" -noout -modulus 2>/dev/null | md5sum)
    if [[ "$CERT_MODULUS" == "$KEY_MODULUS" ]]; then
        echo "PASS: Certificate and private key match"
    else
        echo "FAIL: Certificate and private key DO NOT match!"
    fi
fi
EOF
chmod +x verify_ipsec_certs.sh
./verify_ipsec_certs.sh /etc/ipsec.d/certs/peer.crt

# Check certificate identity matches IKE configuration:
# In strongSwan, rightid = CN of peer cert OR SAN
PEER_CN=$(openssl x509 -in peer.crt -noout -subject | sed 's/.*CN=\([^,/]*\).*/\1/')
PEER_SAN=$(openssl x509 -in peer.crt -noout -text | grep -oP 'DNS:\K[^,]+' | head -1)
echo "Peer CN: $PEER_CN"
echo "Peer SAN: $PEER_SAN"
echo "Configure rightid to match one of these"

# Check OCSP (Online Certificate Status Protocol)
OCSP_URL=$(openssl x509 -in peer.crt -noout -text | grep -oP 'OCSP - URI:\K\S+')
if [[ -n "$OCSP_URL" ]]; then
    echo "Checking OCSP at: $OCSP_URL"
    openssl ocsp -issuer issuer.crt -cert peer.crt -url "$OCSP_URL" -text 2>&1
fi
```

### 9.3 PKCS#12 / PKCS#8 Handling

```bash
# Convert PKCS#12 bundle to separate PEM files (for strongSwan)
openssl pkcs12 -in vpnclient.p12 -out cert.pem -clcerts -nokeys
openssl pkcs12 -in vpnclient.p12 -out key.pem -nocerts -nodes  # -nodes = no passphrase
openssl pkcs12 -in vpnclient.p12 -out ca.pem -cacerts -nokeys

# Install into strongSwan cert store:
cp cert.pem /etc/ipsec.d/certs/
cp key.pem /etc/ipsec.d/private/
cp ca.pem /etc/ipsec.d/cacerts/
chmod 600 /etc/ipsec.d/private/key.pem

# Verify key permissions (private key must not be world-readable)
ls -la /etc/ipsec.d/private/
# Should be: -rw------- (600) or -rw-r----- (640)

# Check that strongSwan found the cert and key
swanctl --list-certs
# Output should show: loaded cert from /etc/ipsec.d/certs/cert.pem

# Verify fingerprint matches expected (use to verify correct cert):
openssl x509 -in cert.pem -noout -fingerprint -sha256
```

---

## 10. NAT Traversal Debugging

### 10.1 NAT Detection Mechanism — Internals

```
IKEv2 NAT Detection Process:

In IKE_SA_INIT exchange, both sides include:
  N(NAT_DETECTION_SOURCE_IP)
  N(NAT_DETECTION_DESTINATION_IP)

These contain hashes:
  NAT_DETECTION_SOURCE_IP = HASH(SPIi | SPIr | IP_src | Port_src)
  NAT_DETECTION_DESTINATION_IP = HASH(SPIi | SPIr | IP_dst | Port_dst)

Detection logic:
  Initiator (A) sends request from IP_A:Port_A
    NAT_DETECT_SRC = HASH(SPIi|0, IP_A, Port_A)
    
  Responder (B) receives packet from IP_A':Port_A' (possibly NATted)
    Computes: HASH(SPIi|0, IP_A', Port_A')
    Compares with received NAT_DETECT_SRC:
    
    If they match: No NAT on path from A → "no NAT between initiator and responder"
    If they differ: NAT is present on A's side!
    
    Similarly for destination direction.

ASCII Diagram:

Initiator (192.168.1.10)          NAT Device          Responder (198.51.100.1)
         |                          |                          |
         | IKE_SA_INIT              |                          |
         | src=192.168.1.10:500     |                          |
         | NAT_SRC=H(192.168.1.10) |                          |
         |────────────────────────>|                          |
         |                          | TRANSLATE               |
         |                          | src=10.0.0.1:12345      |
         |                          |─────────────────────────>|
         |                          |                          |
         |                          |         Responder sees: |
         |                          |         src=10.0.0.1:12345
         |                          |         NAT_SRC expected: H(10.0.0.1:12345)
         |                          |         NAT_SRC received: H(192.168.1.10:500)
         |                          |         → MISMATCH → NAT DETECTED
         |                          |                          |
         |                          |<─────────────────────────|
         |<─────────────────────────|  IKE_SA_INIT Response   |
         |  N(NAT_DETECTION_*)      |  (NAT-T activated)      |
         |  "switch to port 4500"   |                          |
         |                          |                          |
         |──── IKE_AUTH (UDP 4500) ─|─────────────────────────>|
         |  ESP wrapped in UDP 4500 |                          |
```

### 10.2 NAT-T Debugging

```bash
# Check if NAT-T is active for a connection
swanctl --list-sas | grep -i "nat\|4500\|encap"

# Check kernel SA for NAT-T encapsulation
ip xfrm state | grep -A5 "encap"
# You should see:
# encap type espinudp sport 4500 dport 4500 addr 0.0.0.0

# Check if UDP 4500 is reachable (from behind NAT):
nc -zu 198.51.100.1 4500

# Test NAT-T specifically with ike-scan:
ike-scan --ikev2 --sport=4500 --dport=4500 198.51.100.1

# Check NAT keepalives are being sent (should see ~20s interval):
tcpdump -n -v 'udp port 4500' | grep -E "length 1|0xff"
# NAT keepalive = 1-byte UDP packet containing 0xff

# Check conntrack for NAT mappings:
conntrack -L | grep -E "4500"
# You should see entries like:
# udp  17 170 src=192.168.1.10 dst=198.51.100.1 sport=4500 dport=4500 ...

# Debug NAT-T in strongSwan:
# In /etc/strongswan.d/charon-logging.conf:
# esp = 4
# natt = 4
# net = 4
journalctl -fu strongswan | grep -i "nat\|udp encap"

# Check if firewall is blocking UDP 4500 (on server side):
iptables -L INPUT -n -v | grep -E "4500|esp"
# Must have: ACCEPT udp dpt:4500
# Must have: ACCEPT esp (proto 50) — even though encapsulated in UDP,
#            raw ESP must also be allowed if NAT-T is NOT in use

# Force NAT-T even without NAT detection (for testing):
# strongSwan: forceencaps = yes (in ipsec.conf)
# swanctl: encapsulation = yes (in swanctl.conf)
```

### 10.3 NAT Keepalive Timer Issues

```
Problem: VPN drops after ~30-60 seconds of inactivity

Root Cause: NAT mapping expired (NAT device timeout for UDP)
             UDP is stateless — NAT devices have timers (typically 30-300 seconds)
             After timer expires, NAT mapping removed
             New packets from responder cannot reach initiator
             
Solution 1: Reduce NAT keepalive interval
  strongSwan: charon.keep_alive = 20  (default is 20 seconds)
  
Solution 2: Use DPD to keep traffic flowing
  strongSwan: dpddelay = 10  (send DPD every 10 seconds)
  
Solution 3: Configure NAT device for longer UDP timeout
  Cisco ASA: timeout udp 0:30:00 (30 minutes)
  
Solution 4: Use DPD to detect and reconnect after NAT remapping
  strongSwan: dpdaction = restart

Problem: NAT remapping (mobile clients, roaming)
  When client changes IP (DHCP renewal, cell handoff):
    Old NAT mapping is gone
    Responder sends to stale IP
    Connection breaks
    
Solution: MOBIKE (RFC 4555) — IKEv2 extension
  Allows updating IKE/IPsec SA with new client IP
  strongSwan: mobike = yes
  Client detects IP change, sends UPDATE_SA_ADDRESSES
  Server updates its routing for this client
```

---

## 11. Anti-Replay Failures

### 11.1 Sequence Number Exhaustion

```
32-bit Sequence Number Space:
  Maximum value: 2^32 - 1 = 4,294,967,295
  At 10 Gbps with 1500-byte packets: ~833,000 pkts/sec
  Time to exhaust: 4,294,967,295 / 833,000 ≈ 5,155 seconds ≈ 86 minutes!

Extended Sequence Numbers (ESN):
  64-bit space: 2^64 - 1 ≈ 18 quintillion packets
  Same 10 Gbps: would take ~700 million years
  ESN enabled by: negotiate it in SA proposal

Debugging Sequence Number Exhaustion:
  # Check kernel counter
  grep XfrmOutStateSeqError /proc/net/xfrm_stat
  # If non-zero: sequence number wrapped, SA needs immediate rekeying

  # Check SA outbound sequence number
  ip xfrm state | grep "oseq"
  # oseq approaching 0xFFFFFFFF → rekeying is about to be forced

  # Per-SA sequence number
  ip -s xfrm state show | grep -A20 "src ... dst ..."
  # Look for: anti-replay context: seq 0x0, oseq 0xFFFFF000 ← approaching limit!
```

### 11.2 Replay Window Too Small

```
Problem: Out-of-order packets being rejected as replays

Scenario:
  High-throughput link, packets arrive slightly out of order
  Sequence numbers: 100, 102, 101, 103, ...
  Default replay window: 32 or 64
  
  If window is 32, and we're at seq=150:
    Window covers: 119-150
    Packet seq=115 arrives: 150-115=35 > 32 → REJECTED as replay!
    But packet seq=115 is NOT a replay, just delayed!

Diagnosis:
  grep XfrmInStateSeqError /proc/net/xfrm_stat
  # If incrementing: replay window is rejecting legit packets

Solution 1: Increase replay window size
  # In strongSwan, set replay_window:
  # connections.myconn.children.mychild.replay_window = 128
  
  # Directly in kernel (via ip xfrm):
  ip xfrm state add ... replay-window 128
  
  # Or via setkey:
  # spdadd ... esp/tunnel/... -m tunnel -r 128;

Solution 2: Enable ESN (Extended Sequence Numbers)
  Eliminates the problem for high-throughput scenarios
  Required negotiation: add ESN to proposals

Solution 3: Fix network path (QoS reordering is the root cause)
  Check if intermediate network equipment is reordering:
  mtr --report 198.51.100.1
```

### 11.3 Debugging Anti-Replay State

```bash
# Show anti-replay window state for each SA
ip -s xfrm state | grep -A30 "src\|anti-replay"

# Output interpretation:
# anti-replay context: seq 0x0, oseq 0x3E8, bitmap 0xffffffff
#   seq   = highest inbound sequence number received (inbound SA)
#   oseq  = next outbound sequence number (outbound SA)
#   bitmap = 32-bit window showing which sequences received

# Python: decode replay bitmap
python3 << 'EOF'
bitmap = 0xffffffff  # example from ip xfrm state
right_edge = 1000    # example seq value

print("Replay window (right_edge = {})".format(right_edge))
for bit in range(32):
    seq = right_edge - bit
    received = (bitmap >> bit) & 1
    status = "RECEIVED" if received else "NOT YET"
    print(f"  seq {seq}: {status}")
EOF

# Monitor replay stats in real time:
watch -n 0.5 'ip -s xfrm state | grep -E "stats:|replay"'
```

---

## 12. SA Lifetime and Rekeying Failures

### 12.1 Lifetime Types and Their Interactions

```
IPsec SA has two lifetime dimensions:

1. TIME-BASED LIFETIME:
   Hard lifetime: SA is deleted unconditionally at this time
   Soft lifetime: Rekeying begins at this time
   
   Timeline:
   t=0     SA created
   t=3240  Soft lifetime fires → IKE starts rekeying
   t=3600  Hard lifetime fires → SA forcibly deleted
   
   Overlap window (3600-3240=360s) must be enough time
   to complete rekeying before hard expires.
   
   If rekeying fails to complete before hard expiry:
   → SA deleted
   → Traffic drops until new SA established
   → Depending on reconnect policy, tunnel may restart automatically

2. VOLUME-BASED LIFETIME:
   Hard bytes: SA deleted after this many bytes
   Soft bytes: Rekeying begins after this many bytes
   
   For high-throughput tunnels, BYTE-BASED lifetime may
   trigger before time-based. Common mistake: forgetting
   to configure byte lifetime → SA rekeyed only by time,
   but at 10Gbps one SA rekeyes every few minutes anyway.

3. PACKET-BASED LIFETIME (less common):
   Hard packets: SA deleted after N packets
   Soft packets: Rekeying begins after N packets

Checking current lifetimes:
  ip xfrm state | grep -A10 "lifetime"
  # lifetime config:
  #   limit: soft (KB) 4096, hard (KB) 4608
  #   limit: soft (sec) 3240, hard (sec) 3600
  # lifetime current:
  #   1024(bytes), 15(packets)
  #   added Wed Jan 01 12:00:00 2026 use Wed Jan 01 12:00:05 2026
```

### 12.2 Rekeying Race Conditions

```
Simultaneous Rekeying Problem (IKEv2):

Both sides have soft lifetime set to 3240s.
Due to slight timing differences, both attempt rekeying simultaneously:

Side A                                    Side B
  |                                          |
  |── CREATE_CHILD_SA (rekey) ─────────────>|
  |  N(REKEY_SA, SPI=0x1111)                |
  |                                          |
  |<── CREATE_CHILD_SA (rekey) ─────────────|
  |    N(REKEY_SA, SPI=0x1111)              |
  |                                          |
  Both created new SAs simultaneously!      |
  → Duplicate SAs for same traffic          |
  → Protocol: "delete the one with lower    |
    nonce"                                  |
  → Usually self-resolves                   |
  
If self-resolution fails:
  Log: "CHILD_SA_NOT_FOUND" during rekey
  Log: "received Delete for unknown CHILD_SA"
  Fix: Offset rekeying timers by random jitter
       strongSwan: rand_time = 120 (120s of random variation)

Delete-before-rekey Race:
  SA expires on side A at t=3600
  SA rekey starts on A at t=3240
  Rekey completes on A at t=3245
  A deletes old SA (SPI=0x1111)
  
  Meanwhile, B sends packet encrypted with SPI=0x1111 at t=3248
  (B hasn't processed the delete yet)
  → Packet arrives at A with deleted SPI → DROP
  → Brief traffic interruption (usually sub-second)
  
Mitigation: Increase delete delay
  strongSwan: delete_rekeyed_delay = 5 (keep deleted SA for 5s)
```

### 12.3 IKE SA Rekeying vs Child SA Rekeying

```
Two distinct rekeying processes:

1. IKE SA Rekeying (CREATE_CHILD_SA for IKE SA):
   IKEv2 RFC allows rekeying the IKE SA itself.
   New IKE SA with fresh keys, old IKE SA deleted.
   All Child SAs are moved to the new IKE SA.
   
   Less common in practice; many implementations
   just let IKE SA expire and restart everything.
   
   Log: "creating IKE_SA rekey..."

2. Child SA Rekeying (CREATE_CHILD_SA for Child SA):
   More common. Rekeys the ESP/AH SA under the same IKE SA.
   IKE SA remains; only data-plane keys are refreshed.
   
   This is the routine operation for long-running tunnels.
   
   Log: "creating CHILD_SA rekey..."
   
Debugging rekey failures:
  # Check if rekeying is happening:
  journalctl -fu strongswan | grep -i "rekey"
  
  # Expected log during successful rekey:
  # "CHILD_SA mychild{1} established with SPIs c6ba3f21_i 1234abcd_o"
  # "closing CHILD_SA mychild{0} with SPIs oldspii_i oldspir_o"
  # "sending DELETE for ESP CHILD_SA with SPI oldspii"
  
  # Failed rekey log:
  # "CHILD_SA mychild{0} failed to rekey" 
  # → Check proposal compatibility, network availability
```

---

## 13. Routing and Policy Failures

### 13.1 SPD Policy Not Matching Traffic

```
Traffic misses IPsec policy — goes in cleartext:

Check:
  ip xfrm policy  # Are policies installed?
  
Expected for tunnel from 192.168.1.0/24 to 10.0.0.0/8:
  src 192.168.1.0/24 dst 10.0.0.0/8
    dir out priority 375423 ptype main
    tmpl src GW1 dst GW2 proto esp mode tunnel

If policy is missing:
  1. IKE daemon not running
  2. IKE daemon couldn't load the connection config
  3. Policy was manually flushed (setkey -FP)
  4. Connection is "auto=route" but never triggered

Trigger policy installation:
  swanctl --initiate --child mychild  # Force SA establishment
  # OR configure auto=start in ipsec.conf to bring up at daemon start

Policy matching is most-specific-first:
  If you have:
    Policy A: 192.168.1.0/24 → 10.0.0.0/8  (PROTECT)
    Policy B: 0.0.0.0/0 → 10.0.0.0/8       (BYPASS)
  
  Policy A wins (more specific source) for 192.168.1.x traffic
  But what about 172.16.0.0/12 → 10.0.0.0/8?
  Policy B matches → BYPASS (goes cleartext!)
  
  Fix: Add DISCARD policy for traffic that should never go cleartext:
    src 0.0.0.0/0 dst 10.0.0.0/8  dir out: DISCARD
    (More specific policies override this for legitimate IPsec traffic)
```

### 13.2 Missing "fwd" Policy

```
Linux has THREE directions for each policy:
  out: applied to locally-originated outbound traffic
  in:  applied to inbound traffic destined for local host
  fwd: applied to forwarded traffic (when acting as gateway)

CRITICAL: Gateway systems need "fwd" policy!

Symptom: VPN works for traffic to/from the gateway itself,
         but NOT for traffic to/from hosts behind the gateway.

Example:
  GW1 (203.0.113.1) for subnet 192.168.1.0/24
  GW2 (198.51.100.1) for subnet 10.0.0.0/8
  
  Host 192.168.1.10 → 10.0.0.5:
    Packet arrives at GW1 for forwarding
    Kernel checks "fwd" policy for 192.168.1.10 → 10.0.0.5
    If NO fwd policy → packet forwarded WITHOUT IPsec (cleartext!)
    If fwd policy exists → ESP tunnel applied correctly

Check:
  ip xfrm policy | grep "dir fwd"
  # If no fwd entries, they're missing

Fix in strongSwan (auto-handled if configured correctly):
  Make sure "leftsubnet" and "rightsubnet" cover the actual host subnets
  strongSwan generates fwd policies automatically for subnet configs.

Fix manually:
  ip xfrm policy add \
    src 10.0.0.0/8 dst 192.168.1.0/24 dir fwd \
    tmpl src 198.51.100.1 dst 203.0.113.1 proto esp mode tunnel
```

### 13.3 Routing Conflicts

```
Problem: IPsec tunnel established but traffic doesn't go through it

Diagnosis:
  # Where does traffic go?
  ip route get 10.0.0.5
  # Should show: via <IPsec tunnel interface> or use policy routing
  
  # Check if default route overrides specific IPsec route
  ip route show | head -20
  
  # IPsec policy-based routing vs route-based routing:
  
  POLICY-BASED (no explicit route, relies on SPD):
    Traffic matches SPD policy → encrypted
    Routing table doesn't need an entry for remote subnet
    But: Linux also uses routing to determine if packet should
         be sent at all → may need "throw" route or similar
    
  ROUTE-BASED (VTI or XFRM interface):
    Create virtual interface: ip link add vti0 type vti ...
    Add route: ip route add 10.0.0.0/8 dev vti0
    Traffic routed to vti0 → IPsec applied
    More flexible, supports BGP over VPN

VTI Interface Setup (route-based IPsec):
  # Create VTI interface
  ip link add vti0 type vti \
    local 203.0.113.1 \
    remote 198.51.100.1 \
    key 0xC6BA3F21          # Must match SA SPI
  
  ip link set vti0 up
  ip addr add 172.16.0.1/30 dev vti0
  ip route add 10.0.0.0/8 dev vti0
  
  # Disable ICMP redirects for VTI
  sysctl -w net.ipv4.conf.vti0.rp_filter=0
  sysctl -w net.ipv4.conf.vti0.accept_source_route=0

XFRM Interface (modern, preferred over VTI):
  ip link add xfrm0 type xfrm if_id 42 dev eth0
  ip link set xfrm0 up
  ip route add 10.0.0.0/8 dev xfrm0
  # SA must reference if_id 42
```

### 13.4 Asymmetric Routing

```
Problem: Tunnel works in one direction only

Scenario:
  GW1 routes 10.0.0.0/8 traffic through IPsec tunnel (correct)
  GW2 routes replies back through a different path (NOT through tunnel)
  → One side encrypts, other side sees cleartext
  → SPD on receiving side may drop cleartext if policy says PROTECT

Diagnosis:
  # Test bidirectional connectivity:
  ping -c 5 10.0.0.5  # From 192.168.1.10
  # If ping replies come back: symmetric ✓
  # If no replies: check reverse path on remote side
  
  # Traceroute from remote side:
  ssh gw2 "traceroute 192.168.1.10"
  
  # Check rp_filter (Reverse Path Filter):
  # strict mode (1) drops packets that would not be routed back the same way
  cat /proc/sys/net/ipv4/conf/eth0/rp_filter
  # If set to 2 (loose) or 0 (disabled), may allow asymmetric routing

Fix:
  # Ensure both gateways have correct routes for each other's subnets
  # GW1: 
  ip route add 10.0.0.0/8 via 198.51.100.1
  # GW2:
  ip route add 192.168.1.0/24 via 203.0.113.1
  
  # Disable strict rp_filter if needed (for VPN):
  sysctl -w net.ipv4.conf.eth0.rp_filter=2
  sysctl -w net.ipv4.conf.all.rp_filter=2
```

---

## 14. Dead Peer Detection Failures

### 14.1 DPD State Machine and Failure Modes

```
DPD State Machine:

    [ALIVE]
       |
       | No traffic received for dpddelay seconds
       v
    [PROBE_SENT]
       |──── Send INFORMATIONAL request (empty) ─────────────>
       |
       | Wait dpdtimeout seconds for response
       |
       |── Response received ──────────────────────────────────→ [ALIVE]
       |
       | No response → increment retry counter
       |
       | Retries exhausted
       v
    [DEAD] → Execute dpdaction

dpdaction options:
  clear:   Delete IKE SA and Child SAs, do not reconnect
           Use when: Remote is truly gone, tunnel should stay down
  hold:    Delete Child SAs, keep IKE SA, wait for traffic to trigger reconnect
           Use when: Intermittent connectivity, want auto-reconnect
  restart: Delete SA and immediately re-initiate
           Use when: Should always be connected (site-to-site VPN)
  none:    No action (not recommended)
```

### 14.2 DPD False Positives

```
Problem: DPD incorrectly declares peer dead

Scenario 1: One-way traffic
  If traffic flows only from A→B:
    B receives data → B knows A is alive (resets DPD timer)
    A sends data but has no inbound traffic from B
    A's DPD timer fires (no inbound packets from B)
    A sends DPD probe → B responds → A resets timer
    This is NORMAL: DPD will probe and succeed
    
Scenario 2: Network congestion causing DPD timeout
  DPD probe sent but response delayed beyond dpdtimeout
  → False "peer dead" detection
  → SA deleted → reconnect → unnecessary disruption
  Fix: Increase dpdtimeout (e.g., from 30s to 120s)

Scenario 3: Asymmetric connectivity
  Probe from A reaches B, response from B cannot reach A
  (Firewall change, routing change)
  This is a REAL failure — the path is broken
  dpdaction=restart is correct here

DPD settings in strongSwan:
  connections.myconn.dpd_delay = 30    # Probe interval (seconds)
  connections.myconn.dpd_timeout = 120 # Timeout before declaring dead
  # (dpdaction configured per-child-sa)
  connections.myconn.children.mychild.dpd_action = restart

Debugging DPD:
  journalctl -fu strongswan | grep -i "dpd\|dead\|alive"
  # Normal DPD probe:
  # "sending DPD request IKE_SA[X]"
  # "received DPD response for IKE_SA[X]"
  # Failed DPD:
  # "DPD request timed out for IKE_SA[X], sending DELETE"
```

---

## 15. strongSwan Debugging

### 15.1 strongSwan Architecture

```
strongSwan Components:
  charon        - IKEv2 daemon (main daemon)
  starter       - Config parser, starts charon (legacy)
  swanctl       - Modern CLI interface to charon via VICI protocol
  ipsec         - Legacy CLI wrapper

  Internal charon plugins (loaded dynamically):
    kernel-netlink  - Kernel XFRM interface
    openssl         - Crypto via OpenSSL
    socket-default  - UDP socket handling
    natt            - NAT-T implementation  
    resolve         - DNS resolution for IDs
    revocation      - CRL/OCSP checking
    eap-*           - EAP authentication methods
    
  VICI (Versatile IKE Control Interface):
    Unix socket: /var/run/charon.vici
    Used by swanctl to communicate with charon
    Can also be used by custom applications
```

### 15.2 strongSwan Logging Configuration

```bash
# Modern logging config: /etc/strongswan.d/charon-logging.conf
# or inline in /etc/strongswan.conf:

charon {
    filelog {
        /var/log/charon.log {
            time_format = %Y-%m-%d %H:%M:%S
            default = 1       # Default log level for all subsystems
            
            # Per-subsystem log levels (0=quiet, 1=error, 2=warn, 3=info, 4=debug, 5=verbose)
            ike    = 4   # IKE message parsing and processing
            net    = 3   # Network I/O (socket send/recv)
            enc    = 3   # Encoding/decoding of IKE messages
            auth   = 4   # Authentication (certs, PSK, EAP)
            cfg    = 2   # Configuration loading
            knl    = 4   # Kernel interface (XFRM)
            job    = 1   # Job scheduler
            esp    = 3   # ESP processing
            tls    = 2   # TLS (for EAP-TLS)
            lib    = 1   # Library core
        }
    }
    syslog {
        identifier = charon
        daemon {
            default = 1
        }
    }
}

# For maximum debug output during troubleshooting:
charon {
    filelog {
        /var/log/charon-debug.log {
            default = 4
            flush_line = yes  # Flush each line immediately
        }
    }
}
```

### 15.3 swanctl.conf — Full Annotation

```
# /etc/swanctl/swanctl.conf — annotated for debugging understanding

connections {
    site-to-site {
        # IKE SA parameters
        version = 2              # IKEv2 (default)
        reauth_time = 86400s     # IKE SA lifetime (24 hours)
        rekey_time = 43200s      # Rekey IKE SA at 12 hours
        
        # Local endpoint
        local_addrs = 203.0.113.1
        
        # Remote endpoint  
        remote_addrs = 198.51.100.1
        
        # IKE proposal (encryption-integrity-prf-dhgroup)
        proposals = aes256gcm16-prfsha256-ecp256,     # AEAD
                    aes256-sha256-prfsha256-ecp256,   # Non-AEAD
                    aes128gcm16-prfsha256-ecp256       # Fallback
        
        # Local authentication
        local {
            id = 203.0.113.1                # IKE identity (must match cert CN/SAN if using certs)
            auth = psk                       # psk | pubkey | eap-*
            # OR for cert auth:
            # auth = pubkey
            # certs = /etc/swanctl/x509/local.crt
        }
        
        # Remote authentication
        remote {
            id = 198.51.100.1
            auth = psk
            # auth = pubkey
            # certs = /etc/swanctl/x509/peer.crt (optional: pin specific cert)
        }
        
        # Child SAs (data plane)
        children {
            lan-to-lan {
                # Traffic selectors (what traffic to protect)
                local_ts  = 192.168.1.0/24  # Our subnet
                remote_ts = 10.0.0.0/8      # Remote subnet
                
                # ESP proposal
                esp_proposals = aes256gcm16-ecp256,   # AEAD + PFS
                                aes256-sha256-ecp256,  # Non-AEAD + PFS
                                aes256gcm16            # AEAD, no PFS
                
                # SA lifetimes
                life_time = 3600s    # Hard lifetime
                rekey_time = 3240s   # Soft lifetime (rekey at 90% of hard)
                rand_time = 300s     # Random variation (avoid synchronized rekey)
                
                # Mode
                mode = tunnel        # tunnel | transport
                
                # DPD behavior when peer dies
                dpd_action = restart # restart | clear | hold | none
                
                # Auto-trigger
                start_action = start # start | trap | none
                                     # start = initiate immediately
                                     # trap = wait for traffic (install policy only)
                                     # none = manual only
                
                # Anti-replay window size
                replay_window = 64
                
                # Compression (generally not recommended)
                ipcomp = no
            }
        }
        
        # DPD settings
        dpd_delay = 30s
        dpd_timeout = 120s
        
        # MOBIKE (IP mobility)
        mobike = yes
        
        # Fragmentation (for large IKE messages)
        fragmentation = yes
    }
}

# Pre-Shared Keys
secrets {
    ike-site-to-site {
        id-local  = 203.0.113.1
        id-remote = 198.51.100.1
        secret = "ThisIsMyPreSharedKey123!"
    }
}
```

### 15.4 strongSwan Complete Debug Session

```bash
# ============================================================
# FULL DEBUG SESSION — Site-to-Site Tunnel Not Coming Up
# ============================================================

# Step 1: Check daemon status
systemctl status strongswan
journalctl -u strongswan -n 50 --no-pager

# Step 2: Load config explicitly and check for errors
swanctl --load-all 2>&1
# Look for:
# "loaded connection 'site-to-site'"     ← good
# "loading secrets from '/etc/swanctl/conf.d/*.conf'"
# "loaded IKE secret for ... "           ← PSK loaded
# "loaded certificate ..."               ← cert loaded
# "unknown keyword 'reaky_time'"         ← TYPO in config!

# Step 3: Check loaded SAs and connections
swanctl --list-conns
swanctl --list-sas      # Should be empty if nothing connected yet
swanctl --list-certs    # Verify certificates loaded correctly

# Step 4: Enable debug logging  
# Edit /etc/strongswan.d/charon-logging.conf to set levels to 4
# Then reload charon:
systemctl reload strongswan

# Step 5: Initiate connection and watch logs simultaneously
swanctl --initiate --child lan-to-lan &
journalctl -fu strongswan | tee /tmp/ipsec_debug.log

# Step 6: Capture packets in parallel
tcpdump -n -w /tmp/ike.pcap 'udp port 500 or udp port 4500' &

# Step 7: Parse the log output:
# Successful connection should show:
# "initiating IKE_SA site-to-site[1]"
# "generating IKE_SA_INIT request ..."
# "sending packet: from 203.0.113.1[500] to 198.51.100.1[500]"
# "received packet: from 198.51.100.1[500] to 203.0.113.1[500]"
# "selected proposal: IKE:AES_GCM_16_256/PRF_HMAC_SHA2_256/ECP_256"  ← agreed!
# "generating IKE_AUTH request ..."
# "authentication of '203.0.113.1' with pre-shared key"
# "IKE_SA site-to-site[1] established ..."
# "CHILD_SA lan-to-lan{1} established with SPIs ..."
# "installing new policies ... src 192.168.1.0/24 dst 10.0.0.0/8"

# Failed connection shows:
# "received NO_PROPOSAL_CHOSEN notify"
# "received AUTHENTICATION_FAILED notify"
# "peer not responding, trying again"  (× N times, then gives up)

# Step 8: Check kernel state after connection
ip xfrm state
ip xfrm policy
grep "." /proc/net/xfrm_stat | awk '$2 != 0'  # Non-zero counters

# Step 9: Test traffic flow
ping -c 5 -I 192.168.1.10 10.0.0.5
# Check if packets are being encrypted:
tcpdump -n 'proto esp' -c 5
# You should see ESP packets matching each ping
```

---

## 16. Libreswan Debugging

### 16.1 Libreswan Architecture

```
Libreswan Components:
  pluto     - IKE daemon (supports IKEv1 and IKEv2)
  ipsec     - Wrapper script for pluto control
  
Configuration files:
  /etc/ipsec.conf             - Main config
  /etc/ipsec.secrets          - PSKs and private keys
  /etc/ipsec.d/              - Certificates and CRLs
  /etc/ipsec.d/cacerts/      - Trusted CA certificates
  /etc/ipsec.d/certs/        - Local and peer certificates
  /etc/ipsec.d/private/      - Private keys
  /etc/ipsec.d/crls/         - Certificate Revocation Lists
```

### 16.2 Libreswan Debug Commands

```bash
# Check pluto status
ipsec status
ipsec statusall   # More verbose: shows all SAs and policies

# Start with debug logging
ipsec pluto --debug-all --stderrlog --logfile /var/log/pluto-debug.log

# Connection management
ipsec auto --up myconn        # Bring up connection
ipsec auto --down myconn      # Bring down connection
ipsec auto --add myconn       # Load connection config
ipsec auto --delete myconn    # Unload connection
ipsec restart                  # Restart pluto

# Verbose status for specific connection
ipsec status | grep myconn

# Debug log categories in /etc/ipsec.conf:
config setup
    logfile=/var/log/pluto.log
    logappend=yes
    logtime=yes
    plutodebug=all    # Enable all debug categories
    # Or specific categories:
    # plutodebug="base control crypt dns emitting kernel parsing raw record routing state"
    # base:      Basic operations
    # control:   Control path, connection management
    # crypt:     Crypto operations (generates many messages)
    # kernel:    Kernel XFRM interface
    # parsing:   IKE message parsing
    # raw:       Raw packet dumps
    # state:     State machine transitions

# libreswan ipsec.conf connection template:
conn myconn
    type=tunnel
    left=203.0.113.1        # Local gateway IP
    leftsubnet=192.168.1.0/24  # Local subnet
    right=198.51.100.1      # Remote gateway IP
    rightsubnet=10.0.0.0/8  # Remote subnet
    authby=secret           # PSK auth (or rsasig for cert)
    ike=aes256-sha256;modp2048  # IKE SA proposal
    phase2alg=aes_gcm_c_256-null  # ESP proposal (null=AEAD handles auth)
    phase2=esp
    auto=start              # Bring up on daemon start
    dpdaction=restart       # Restart on DPD failure
    dpddelay=30s
    dpdtimeout=120s
    ikelifetime=24h
    salifetime=8h

# ipsec.secrets format:
# 203.0.113.1 198.51.100.1 : PSK "MySecretKey"
# @my-cert-id               : RSA /etc/ipsec.d/private/mykey.pem

# Check loaded secrets
ipsec secrets   # (or ipsec showhostkey for key fingerprints)

# Verify certificate configuration:
ipsec showhostkey --ckaid  # Show certificate key IDs
ipsec listcerts             # List all loaded certs
ipsec listcacerts           # List all CA certs
ipsec listcrls              # List all CRLs
```

---

## 17. Cisco IOS Debugging

### 17.1 Cisco IOS/IOS-XE IPsec Debug Commands

```
IMPORTANT: Cisco "debug" commands generate high CPU load.
           On production routers, use access-lists to limit debug scope
           and always plan to disable them immediately after capture.

# Show overall IPsec status:
show crypto isakmp sa          # IKEv1 Phase 1 SAs
show crypto ipsec sa           # IKEv1 Phase 2 (IPsec) SAs
show crypto ikev2 sa           # IKEv2 SAs
show crypto ikev2 sa detailed  # IKEv2 SAs with counters

# IKEv2 SA output interpretation:
# IPv4 Crypto IKEv2  SA
# Tunnel-id Local                 Remote                Status         Encr  Hash  Auth DH Lifetime Cap.
# 1         203.0.113.1/500       198.51.100.1/500      READY          AES-256 SHA256 PSK  19  23:59:45 NONE
#           ↑ local IP            ↑ remote IP           ↑ STATE       ↑ algorithms negotiated

# States:
# READY    = IKE SA established, data can flow
# ACTIVE   = Negotiating
# NEG_PHASE2 = IKEv1 Phase 2 negotiation in progress
# SKEYID_STATE = IKEv1 Phase 1 DH computation
# DELETE   = Being deleted

# Show IPsec SA counters (CRITICAL for debugging):
show crypto ipsec sa detail
# Key fields:
#   #pkts encaps: N, #pkts encrypt: N  ← packets encrypted outbound
#   #pkts decaps: N, #pkts decrypt: N  ← packets decrypted inbound
#   #pkts verify failed: N             ← auth failures! should be 0
#   #pkts decompress failed: N
#   #send errors N                     ← outbound errors

# If "pkts encaps" goes up but "pkts decaps" stays at 0:
# → Traffic leaving but not arriving / not being decrypted
# → Check far end, check network path, check SPI mismatch

# Debugging IKEv2 (Cisco):
debug crypto ikev2 {packet|detail|error|internal|proposal|terse}
debug crypto ipsec {detail|error}

# Scoped debug (limit to peer IP, much safer in production):
debug crypto condition peer ipv4 198.51.100.1
debug crypto ikev2 packet
debug crypto ipsec detail

# Capture IKE exchange:
debug crypto ikev2 packet detail  # Decode every IKE field

# Disable all crypto debug (CRITICAL: run when done):
undebug all
no debug crypto condition peer ipv4 198.51.100.1

# IKEv2 troubleshoot commands (Cisco IOS-XE 16.x+):
# Automatically runs debug, captures, and presents summary:
# debug crypto ikev2 error

# Example debug output showing proposal mismatch:
# *Jan  1 00:00:01.000: IKEv2:(SA ID = 1):Searching policy based on peer's proposal
# *Jan  1 00:00:01.001: IKEv2: Proposal mismatch
# *Jan  1 00:00:01.001: IKEv2: Peer's proposal:
# *Jan  1 00:00:01.001: IKEv2:    Encryption: AES-CBC-256
# *Jan  1 00:00:01.001: IKEv2:    Integrity:  SHA256
# *Jan  1 00:00:01.001: IKEv2:    PRF:        SHA256
# *Jan  1 00:00:01.001: IKEv2:    DH Group:   19
# *Jan  1 00:00:01.001: IKEv2: Local policy (no match):
# *Jan  1 00:00:01.001: IKEv2:    Encryption: AES-CBC-128
# *Jan  1 00:00:01.001: IKEv2:    DH Group:   14
# Fix: Update crypto ikev2 proposal on Cisco to match peer
```

### 17.2 Cisco IOS Common Configuration Issues

```
# Cisco IKEv2 configuration structure:
! IKEv2 Proposal (algorithm suite)
crypto ikev2 proposal MY_PROPOSAL
 encryption aes-cbc-256 aes-gcm-256
 integrity sha256 sha384
 group 19 14

! IKEv2 Policy (matches proposals to peers)
crypto ikev2 policy MY_POLICY
 proposal MY_PROPOSAL

! IKEv2 Keyring (authentication credentials)
crypto ikev2 keyring MY_KEYRING
 peer REMOTE
  address 198.51.100.1
  pre-shared-key local MyPSK
  pre-shared-key remote MyPSK

! IKEv2 Profile (ties together policy, auth, identity)
crypto ikev2 profile MY_PROFILE
 match identity remote address 198.51.100.1 255.255.255.255
 identity local address 203.0.113.1
 authentication local pre-share
 authentication remote pre-share
 keyring local MY_KEYRING
 dpd 30 5 periodic

! IPsec Transform Set (ESP algorithms)
crypto ipsec transform-set MY_TS esp-gcm 256
 mode tunnel

! IPsec Profile (for template-based VPN)
crypto ipsec profile MY_PROFILE
 set ikev2-profile MY_PROFILE
 set transform-set MY_TS

! Crypto Map (for policy-based VPN)
crypto map MY_MAP 10 ikev2 ipsec-isakmp
 set peer 198.51.100.1
 set transform-set MY_TS
 set ikev2-profile MY_PROFILE
 match address VPN_ACL

! Access list defining interesting traffic
ip access-list extended VPN_ACL
 permit ip 192.168.1.0 0.0.0.255 10.0.0.0 0.255.255.255

! Apply to interface
interface GigabitEthernet0/0
 ip address 203.0.113.1 255.255.255.0
 crypto map MY_MAP

COMMON CISCO MISTAKES:
1. ACL mismatch: Site A ACL permits A→B, but Site B ACL permits B→A
   → They don't match (they should be mirror images)
   → Error: "no valid proxy" or "proxy mismatch"
   FIX: Make ACLs mirror images

2. Transform set mode mismatch:
   Site A: mode tunnel
   Site B: mode transport (for site-to-site: both must be tunnel)

3. Crypto map not applied to interface
   No "crypto map" command under interface
   → IPsec policies exist but never triggered

4. NAT before crypto:
   If NAT translates the packet BEFORE crypto map checks ACL:
   → Packet no longer matches VPN ACL (source IP changed)
   → Fix: NAT exemption (nat 0 or no-nat rule for VPN traffic)
   ip access-list extended NO_NAT
    permit ip 192.168.1.0 0.0.0.255 10.0.0.0 0.255.255.255
   ip nat inside source list NORMAL_NAT interface GigEth0/0 overload
   ip nat inside source list NO_NAT interface GigEth0/0 overload route-map VPN_ONLY
   ! (complex; simpler is to use route-map for NAT)
```

---

## 18. Juniper SRX Debugging

```bash
# Show IKE SA status
show security ike sa
show security ike sa detail

# Show IPsec SA status
show security ipsec sa
show security ipsec sa detail

# Statistics (look for errors)
show security ipsec statistics
# Key: esp-decryption-failures, ah-authentication-failures

# IKEv2 specific:
show security ike sa ike-policy MY_POLICY

# Traceoptions for full debug (equivalent to debug on Cisco):
# Configure in /[edit security ike traceoptions]:
set security ike traceoptions file ike-debug.log
set security ike traceoptions file size 10m
set security ike traceoptions flag all   # Warning: generates large output
# Or specific flags:
set security ike traceoptions flag certificates
set security ike traceoptions flag ike
set security ike traceoptions flag policy-manager
set security ike traceoptions flag routing-socket
set security ike traceoptions flag general

# Apply traceoptions:
commit
# View log:
show log ike-debug.log | last 100

# IPsec traceoptions:
set security ipsec traceoptions file ipsec-debug.log
set security ipsec traceoptions flag all

# Clear SAs and renegotiate:
clear security ike sa all
clear security ipsec sa all
# Manually trigger negotiation:
clear security ike sa index 1  # Specific SA

# Check zone policies (SRX is zone-based firewall):
# Even if IPsec SA is up, zone policy must allow traffic
show security policies from-zone untrust to-zone trust
# Must have "permit" policy for traffic from VPN zone

# SRX VPN monitoring:
show security monitoring ipsec

# Juniper common issues:
# 1. Zone policy blocking: VPN traffic enters trust zone but
#    policy doesn't allow it through.
# 2. ST (Secure Tunnel) interface not bound to zone.
# 3. "bind-interface" missing: IPsec SA up but no st0 interface.
```

---

## 19. Cloud VPN Debugging

### 19.1 AWS VPN Debugging

```bash
# AWS Site-to-Site VPN uses two tunnels (redundancy)
# Each tunnel is an IKEv1 or IKEv2 endpoint

# View tunnel status via AWS CLI:
aws ec2 describe-vpn-connections \
  --vpn-connection-ids vpn-0123456789abcdef0 \
  --query 'VpnConnections[*].VgwTelemetry'

# Output:
# [{"AcceptedRouteCount": 1, "LastStatusChange": "...",
#   "OutsideIpAddress": "3.15.x.x", "Status": "UP", "StatusMessage": ""},
#  {"AcceptedRouteCount": 0, "LastStatusChange": "...",
#   "OutsideIpAddress": "18.188.x.x", "Status": "DOWN", "StatusMessage": "IPSEC IS DOWN"}]

# Download configuration file for your VPN device:
aws ec2 download-vpn-configuration \
  --vpn-connection-id vpn-0123456789abcdef0 \
  --output text

# AWS VPN requires:
# IKEv1 Phase 1: AES-128, SHA-1, DH-2 (minimum; also supports AES-256, SHA-256, DH-14/19/20)
# IKEv2: AES-128/256, SHA-256/384/512, DH-2/5/14/19/20/21/22/23/24
# ESP: AES-128/256-CBC, AES-128/256-GCM
# Lifetime: 28800s (8h) for IKE, 3600s (1h) for IPsec (required by AWS!)
# Dead Peer Detection: REQUIRED (AWS uses DPD to detect and reroute)
# NAT-T: REQUIRED (AWS VPN endpoints use NAT)

# Common AWS VPN issues:
# 1. Lifetime mismatch: Your side 86400s, AWS requires 28800s max
#    Fix: Set ikelifetime=28800s, salifetime=3600s
# 2. Dead peer detection disabled: AWS declares tunnel DOWN
#    Fix: Enable DPD on customer gateway device
# 3. BGP session down (for dynamic routing):
#    Even if IPsec tunnel is UP, BGP may not be established
#    Check BGP: aws ec2 describe-vpn-connections | grep bgp

# CloudWatch metrics for VPN (if enabled):
aws cloudwatch get-metric-data \
  --metric-data-queries '[{"Id":"tunnelState","MetricStat":{"Metric":{"Namespace":"AWS/VPN","MetricName":"TunnelState","Dimensions":[{"Name":"VpnId","Value":"vpn-0123456789abcdef0"}]},"Period":60,"Stat":"Average"}}]' \
  --start-time 2026-01-01T00:00:00Z \
  --end-time 2026-01-01T01:00:00Z

# VPC Flow Logs to see if traffic reaches VPN endpoint:
# (Enables in VPC → Flow Logs → Filter: ALL)
# Look for packets to/from VPN gateway ENI
```

### 19.2 Azure VPN Debugging

```bash
# Check Azure VPN Gateway connection status:
az network vpn-connection show \
  --name MyVpnConnection \
  --resource-group MyRG \
  --query '{Status:connectionStatus, EgressBytes:egressBytesTransferred, IngressBytes:ingressBytesTransferred}'

# View IKE SA status (Azure Portal or CLI):
az network vpn-connection list-ike-sas \
  --name MyVpnConnection \
  --resource-group MyRG

# Common Azure requirements:
# IKE Phase 1 lifetime: 3600-86400 seconds
# IKE Phase 2 lifetime: 300-3600 seconds  ← much shorter than IKEv1 Phase 1!
# DH Group: DHGroup2, DHGroup14, DHGroup24, ECP256, ECP384
# IKE Encryption: AES128, AES192, AES256, DES, DES3, GCMAES128, GCMAES256
# IKE Integrity: MD5, SHA1, SHA256, SHA384, GCMAES128, GCMAES256
# ESP Encryption: AES128, AES192, AES256, GCMAES128, GCMAES256
# ESP Integrity: MD5, SHA1, SHA256, GCMAES128, GCMAES256
# PFS: PFS1, PFS2, PFS14, PFS24, PFSMM, ECP256, ECP384

# Azure diagnostic logs:
az monitor diagnostic-settings create \
  --resource /subscriptions/.../virtualNetworkGateways/MyGateway \
  --logs '[{"category":"IKEDiagnosticLog","enabled":true}]' \
  --workspace /subscriptions/.../workspaces/MyWorkspace \
  --name IKEDiagnostics

# Query logs in Log Analytics:
# AzureDiagnostics
# | where Category == "IKEDiagnosticLog"
# | where ResourceId contains "MyGateway"
# | order by TimeGenerated desc
# | take 100

# Common Azure VPN issues:
# 1. Policy-based vs Route-based mismatch
#    Azure supports both; some legacy Cisco configs use policy-based
#    Route-based (IKEv2) is strongly preferred
# 2. BGP ASN conflict: Azure uses 65515 by default
#    Customer gateway must use different ASN
# 3. "UsePolicyBasedTrafficSelectors" on route-based gateway
#    Required for connecting to Cisco ASA policy-based VPN
```

### 19.3 GCP Cloud VPN Debugging

```bash
# Check GCP VPN tunnel status:
gcloud compute vpn-tunnels describe my-tunnel \
  --region us-east1 \
  --format='value(status,detailedStatus)'

# Possible status values:
# ESTABLISHED  = Tunnel up, traffic flowing
# NEGOTIATING  = IKE in progress
# WAITING_FOR_FULL_CONFIG = Config not complete
# ALLOCATING_RESOURCES    = Setting up
# FIRST_HANDSHAKE         = Very first IKE attempt
# NO_INCOMING_PACKETS     = IKE established but no ESP traffic
# AUTHORIZATION_ERROR     = Auth failure
# NEGOTIATION_FAILURE     = IKE negotiation failed
# DEPROVISIONING          = Being deleted
# FAILED                  = Error state

# View all tunnels and status:
gcloud compute vpn-tunnels list

# GCP VPN requirements (Classic VPN):
# IKE version: 1 or 2
# IKE Cipher: aes128, aes256, 3des
# IKE PRF: md5, sha1, sha256
# IKE DH: 1, 2, 5, 14, 15, 16
# ESP Cipher: aes128, aes256, 3des
# ESP Integrity: md5, sha1, sha256
# IKE lifetime: 36600s (default)
# ESP lifetime: 10800s (default)
# DPD: enabled with 20s timeout

# Get tunnel details for debugging:
gcloud compute vpn-tunnels describe my-tunnel --region us-east1

# Check firewall rules allowing ESP and UDP 500/4500:
gcloud compute firewall-rules list \
  --filter="targetTags:vpn-gateway"

# Essential firewall rules for GCP VPN gateway:
# Allow ESP (proto 50) from peer
# Allow UDP 500 from peer  
# Allow UDP 4500 from peer (NAT-T)

# GCP Cloud Logging — VPN gateway logs:
gcloud logging read \
  'resource.type="vpn_gateway" AND severity>=WARNING' \
  --freshness=1h \
  --format='value(timestamp,textPayload)'
```

---

## 20. Wireshark — Full IPsec Dissection Guide

### 20.1 Essential Wireshark Filters for IPsec

```
# Basic IPsec filters:
isakmp                    # All IKEv1 and IKEv2 IKE traffic (UDP 500)
isakmp.version.major == 2 # Only IKEv2
isakmp.version.major == 1 # Only IKEv1
esp                       # All ESP packets (IP proto 50)
ah                        # All AH packets (IP proto 51)

# Filter by exchange type (IKEv2):
isakmp.exchangetype == 34  # IKE_SA_INIT
isakmp.exchangetype == 35  # IKE_AUTH
isakmp.exchangetype == 36  # CREATE_CHILD_SA
isakmp.exchangetype == 37  # INFORMATIONAL

# Filter IKEv2 by specific notify type:
isakmp.notify.msgtype == 17    # NO_PROPOSAL_CHOSEN
isakmp.notify.msgtype == 24    # INVALID_KE_PAYLOAD
isakmp.notify.msgtype == 34    # AUTHENTICATION_FAILED
isakmp.notify.msgtype == 39    # TS_UNACCEPTABLE
isakmp.notify.msgtype == 16389 # NAT_DETECTION_DESTINATION_IP
isakmp.notify.msgtype == 16390 # COOKIE

# Filter by SPI:
isakmp.ispi == 0xA1B2C3D4E5F60718  # Specific initiator SPI
esp.spi == 0xC6BA3F21              # Specific ESP SPI

# Filter by peer IP:
ip.addr == 198.51.100.1 and (isakmp or esp or ah)

# NAT-T (ESP over UDP 4500):
udp.port == 4500

# IKE retransmissions (same message ID, same SPI):
isakmp.messageid == 0 and isakmp.ispi == 0xA1B2C3D4E5F60718

# Large IKE packets (possible fragmentation):
isakmp and frame.len > 1400

# Filter IKE errors (any error notify):
isakmp.notify.msgtype < 8192  # Error notifies have type < 8192
```

### 20.2 Wireshark ESP Decryption Setup

```
Configure Wireshark to decrypt ESP packets:

1. Get SA keying material:
   Method A — From Linux XFRM (preferred):
     ip xfrm state show | grep -E "spi|enc|auth|aead"
     # Look for:
     # spi 0xc6ba3f21
     # aead rfc4106(gcm(aes)) 0xKEYHEXSTRING... 128

   Method B — From strongSwan debug log:
     grep -i "installed" /var/log/charon.log
     # "CHILD_SA ... INSTALLED, inbound SPI 0xc6ba3f21 ..."
     # Look for key material in very verbose log (level 5)

2. In Wireshark:
   Edit → Preferences → Protocols → ESP
   
3. Add decryption entry:
   Click "ESP SAs" → Add
   
   Fields:
   - Protocol:        IPv4 (or IPv6)
   - Src IP:          (leave blank for any)
   - Dest IP:         (leave blank for any)
   - SPI:             0xC6BA3F21  (your ESP SPI, 0x prefix)
   
   For AES-256-GCM with 16-byte ICV:
   - Encryption algorithm: AES-GCM-256 [16-byte ICV]
   - Encryption key:       0x (followed by 36 bytes = 32 key + 4 salt)
     Format: [32-byte key][4-byte implicit IV / salt]
     Example: 0xDEADBEEF...(32 bytes)...CAFEBABE (4 bytes)
   
   For AES-256-CBC with HMAC-SHA256:
   - Encryption algorithm: AES-CBC-256
   - Encryption key:       0x (32 bytes)
   - Authentication algorithm: HMAC-SHA-256-128
   - Authentication key:   0x (32 bytes for HMAC-SHA256)

4. Apply and reload capture.
   ESP packets will now show decrypted content.
   You can see inner IP headers and TCP/UDP data.
   
5. After decryption, apply inner packet filters:
   esp.decrypted   (show only successfully decrypted ESP)
   ip.inner.src == 192.168.1.10  (inner source IP after decryption)
```

### 20.3 Wireshark: Analyzing a Complete IKEv2 Session

```
Reading a Full IKEv2 Session in Wireshark:

Packet 1: IKE_SA_INIT Request (Initiator → Responder)
  Protocol: ISAKMP
  Info: "IKE_SA_INIT MID=00 Request"
  Key fields to check:
    Initiator SPI: A1B2C3D4E5F60718  (random, generated now)
    Responder SPI: 0000000000000000  (must be zero for first request)
    Exchange Type: IKE_SA_INIT (34)
    Flags: 0x08 (Initiator bit set)
    Message ID: 0
    
    Payloads:
    ├─ SA: "Supported Proposals"
    │   ├─ Proposal 1: IKE
    │   │   ├─ Transform: ENCR_AES_GCM_16 (256-bit)
    │   │   ├─ Transform: PRF_HMAC_SHA2_256
    │   │   └─ Transform: DH_1024_MODP (group 2)  ← BAD: weak DH!
    ├─ KE: "Key Exchange Data" (DH public key, 128 bytes for group 2)
    ├─ Ni: "Nonce" (16-32 random bytes)
    ├─ N(NAT_DETECTION_SOURCE_IP): HASH(SPIs|IP|Port)
    └─ N(NAT_DETECTION_DESTINATION_IP): HASH(SPIs|IP|Port)

Packet 2: IKE_SA_INIT Response (Responder → Initiator)  
  CASE A — Successful proposal:
    SA: Selected proposal (one from initiator's list)
    KE: Responder's DH public key (same group as initiator chose)
    Nr: Responder's nonce
    N(NAT_DETECTION_SOURCE_IP): Responder's hash
    N(NAT_DETECTION_DESTINATION_IP): Responder's hash
    [CERTREQ: (optional) asking initiator to provide cert]
    
  CASE B — Wrong DH group:
    N(INVALID_KE_PAYLOAD): "Use DH group 14"
    → Initiator will retry with DH group 14
    
  CASE C — No proposal match:
    N(NO_PROPOSAL_CHOSEN)
    → Negotiation ends here; investigate proposals

Packet 3: IKE_AUTH Request (Initiator → Responder) [ENCRYPTED]
  All subsequent messages encrypted with SK_e/SK_a
  Wireshark shows: "Encrypted payload"
  After ESP key entry in preferences: shows decrypted content
  
  Decrypted content:
  ├─ IDi: Initiator identity (e.g., "203.0.113.1" or "vpn.example.com")
  ├─ [CERT: Certificate chain (if using certs)]
  ├─ [CERTREQ: Certificate request]
  ├─ AUTH: Authentication payload (PSK HMAC or RSA signature)
  ├─ SA: Child SA proposals (ESP algorithms)
  ├─ TSi: Traffic Selector - Initiator
  └─ TSr: Traffic Selector - Responder

Packet 4: IKE_AUTH Response (Responder → Initiator) [ENCRYPTED]
  CASE A — Success:
    IDr, [CERT], AUTH, SA, TSi, TSr
    → Tunnel established!
    
  CASE B — Auth failure:
    N(AUTHENTICATION_FAILED)
    → Check PSK, certs, identity
    
  CASE C — TS mismatch:
    N(TS_UNACCEPTABLE)
    → Traffic selectors rejected, check leftsubnet/rightsubnet
```

---

## 21. tcpdump Recipes

### 21.1 Comprehensive Capture Scripts

```bash
#!/bin/bash
# ipsec_capture.sh — Comprehensive IPsec packet capture

PEER="198.51.100.1"
IFACE="eth0"
CAPTURE_DIR="/tmp/ipsec_debug_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$CAPTURE_DIR"

echo "Starting IPsec packet captures..."
echo "Output directory: $CAPTURE_DIR"

# 1. IKE control plane (UDP 500 and 4500)
tcpdump -n -i "$IFACE" \
  "(udp port 500 or udp port 4500) and host $PEER" \
  -w "$CAPTURE_DIR/ike.pcap" &
IKE_PID=$!
echo "IKE capture PID: $IKE_PID"

# 2. ESP/AH data plane
tcpdump -n -i "$IFACE" \
  "(proto esp or proto ah) and host $PEER" \
  -w "$CAPTURE_DIR/esp.pcap" &
ESP_PID=$!
echo "ESP capture PID: $ESP_PID"

# 3. All traffic to/from peer (comprehensive)
tcpdump -n -i "$IFACE" \
  "host $PEER" \
  -w "$CAPTURE_DIR/all.pcap" &
ALL_PID=$!
echo "All traffic capture PID: $ALL_PID"

# 4. Inner network traffic (traffic that SHOULD be going through tunnel)
INNER_SRC="192.168.1.0/24"
INNER_DST="10.0.0.0/8"
tcpdump -n -i any \
  "src net $INNER_SRC and dst net $INNER_DST" \
  -w "$CAPTURE_DIR/inner_traffic.pcap" &
INNER_PID=$!
echo "Inner traffic capture PID: $INNER_PID"

echo "Captures running. Press Ctrl+C to stop."
echo "Load $CAPTURE_DIR/ike.pcap in Wireshark for IKE analysis"

# Wait for interrupt
trap "kill $IKE_PID $ESP_PID $ALL_PID $INNER_PID 2>/dev/null; echo 'Captures stopped'" INT
wait

echo "Capture files:"
ls -la "$CAPTURE_DIR/"

# Quick analysis
echo ""
echo "=== Quick Analysis ==="
echo "IKE packets:"
tcpdump -n -r "$CAPTURE_DIR/ike.pcap" 2>/dev/null | head -20

echo ""
echo "ESP packet count:"
tcpdump -n -r "$CAPTURE_DIR/esp.pcap" 2>/dev/null | wc -l

echo ""
echo "Any ICMP errors?"
tcpdump -n -r "$CAPTURE_DIR/all.pcap" 'icmp' 2>/dev/null | head -20
```

### 21.2 One-Line Diagnostic Commands

```bash
# Is IKE daemon communicating with peer?
tcpdump -n -c 5 'udp port 500 and host 198.51.100.1'
# If no output: network connectivity issue or IKE daemon not sending

# Are ESP packets flowing?
tcpdump -n -c 10 'proto esp'
# Count: should be nonzero if tunnel is up and traffic is flowing

# Are we seeing ESP in both directions?
tcpdump -n -c 20 'proto esp' | grep -o 'IP [^ ]*' | sort | uniq -c
# Should see counts for both directions: 203.0.113.1 > 198.51.100.1 and vice versa

# Is NAT-T active? (ESP inside UDP 4500)
tcpdump -n -c 5 'udp port 4500 and host 198.51.100.1'
# If traffic only on 4500, not proto 50: NAT-T is active

# Detect retransmissions (IKE daemon not getting responses)
tcpdump -n 'udp port 500' | grep -o "length [0-9]*" | sort | uniq -c
# Identical length packets in bursts = retransmissions

# Quick MTU test (can large packets traverse the path?)
ping -c 5 -M do -s 1400 198.51.100.1  # DF bit set, 1400-byte payload
# If all 5 succeed: MTU is fine
# If fail: MTU issue; try smaller size to find exact limit

# Watch ESP packet sequence numbers (detect gaps/replays)
tcpdump -n -v 'proto esp and host 198.51.100.1' 2>/dev/null | \
  grep -oP 'seq \K0x[0-9a-f]+' | \
  python3 -c "
import sys
prev = None
for line in sys.stdin:
    seq = int(line.strip(), 16)
    if prev is not None and seq != prev + 1:
        print(f'GAP or REORDER: expected {prev+1:#010x}, got {seq:#010x}')
    prev = seq
    print(f'seq: {seq:#010x}')
"
```

---

## 22. Common Failure Scenarios — Root Cause Diagnosis

### 22.1 Scenario: "Tunnel Not Coming Up — Peer Not Responding"

```
Symptom: IKE daemon sends requests, no response from peer
Log: "peer not responding, retrying (2/5)..."
     "giving up connecting"

Diagnosis Tree:

Is UDP 500 reaching the peer?
  tcpdump -n 'udp port 500 and host PEER' on BOTH sides
  
  A — No packets seen on PEER side:
      Firewall is blocking UDP 500
      Fix: Allow UDP 500 (bidirectional) between the VPN endpoints
      Check: iptables -L INPUT -n | grep 500
             iptables -L OUTPUT -n | grep 500
      Also check: cloud security groups, hardware firewall ACLs
      
  B — Packets arrive at PEER but no response:
      IKE daemon on peer not running
      Fix: sudo systemctl start strongswan (or equivalent)
      Check: ps aux | grep charon
             ss -ulnp | grep :500
      
  C — Response sent but not arriving at initiator:
      Asymmetric network issue
      Check: traceroute from PEER to initiator
      Check: firewall on path between PEER and initiator

Is the peer IP correct?
  ping 198.51.100.1  # Basic reachability
  traceroute 198.51.100.1  # Path analysis
  
Is there a DNS resolution issue?
  # If config uses hostname instead of IP:
  nslookup vpn.remote.example.com  # Must resolve to correct IP
  host vpn.remote.example.com
```

### 22.2 Scenario: "Tunnel Up but No Traffic"

```
Symptom: IKE negotiation succeeds, ESP SAs installed, but ping fails
Log: "CHILD_SA established with SPIs..."
     But ping returns nothing or "Destination Host Unreachable"

Check 1: Is traffic matching the IPsec policy?
  ip xfrm policy  # Verify correct selectors
  
  # Test packet policy:
  ip xfrm policy get \
    src 192.168.1.10/32 dst 10.0.0.5/32 dir out proto 1
  # Should show: action=protect

Check 2: Is traffic being encrypted?
  # Monitor ESP packet count while pinging:
  watch -n 1 'ip -s xfrm state | grep -A5 "GW1 → GW2"'
  # "pkts" counter should increment

  # If policy matches but packets not encrypted:
  # SA may be installed for different traffic selectors
  ip xfrm state | grep "sel src"
  # Ensure selectors include the IP range you're testing

Check 3: Are packets arriving at remote side?
  tcpdump -n 'proto esp' on remote gateway
  # If ESP packets arrive but pings don't reach target host:
  # Inner packet delivery problem
  
Check 4: Is the remote side forwarding decrypted packets?
  sysctl net.ipv4.ip_forward  # Must be 1 on gateway
  
  # Check if decrypted packet routing is correct:
  ip route get 10.0.0.5 from 192.168.1.10  # From remote gateway
  
Check 5: Return path — is response coming back through tunnel?
  # On target host (10.0.0.5):
  ip route get 192.168.1.10  # Check return path
  # Response must go back through GW2 → tunnel → GW1 → host

Check 6: Firewall on either end blocking decrypted traffic?
  # After ESP decryption, inner packet passes through firewall again
  iptables -L FORWARD -n -v | grep -E "192.168|10.0"
  # Must have ACCEPT rules for forwarded VPN traffic
```

### 22.3 Scenario: "Tunnel Works Then Drops"

```
Symptom: Tunnel establishes fine, works for minutes/hours, then drops
         Sometimes reconnects automatically, sometimes doesn't

Possible Cause A: SA Lifetime Expiry without Rekeying
  Check: SA rekeying logs
  journalctl -fu strongswan | grep "rekey\|expire\|delete"
  
  Pattern in logs:
  "CHILD_SA ... will expire in 5m, rekeying"  ← rekeying starting
  "creating CHILD_SA ... failed"               ← rekey failed!
  "deleting CHILD_SA ..."                      ← SA expired, deleted
  
  Root Cause: Rekeying fails because peer is temporarily unreachable
  Fix: Increase rekey margin, configure dpdaction=restart

Possible Cause B: DPD Killing Idle Tunnel
  Check: DPD timeout and action settings
  If tunnel only drops during idle periods:
  → DPD firing with no traffic to prove liveness
  → Reduce dpddelay or configure NAT keepalives
  
  Fix: 
  connections.myconn.dpd_delay = 10s
  connections.myconn.children.mychild.dpd_action = restart

Possible Cause C: ISP-Level NAT Mapping Expiry
  Pattern: Drops exactly at regular intervals (30s, 60s, etc.)
  → NAT mapping between client and server expired
  Fix: Enable NAT keepalives (charon.keep_alive = 20)
  
Possible Cause D: Sequence Number Exhaustion (High-traffic tunnels)
  Check: XfrmOutStateSeqError in /proc/net/xfrm_stat
  Fix: Enable ESN, or reduce SA lifetime to force rekeying earlier

Possible Cause E: Hardware or Software Bug
  Check: Kernel and IKE daemon logs around the time of drop
  Check: Memory pressure (OOM killer may kill charon)
  journalctl | grep -E "oom|killed|charon"
```

### 22.4 Scenario: "MTU / Fragmentation Issues"

```
Symptom: Small packets work, large packets fail or are very slow
         TCP connections hang after initial handshake
         ICMP pings work, HTTP fails

Root Cause: IPsec adds overhead to each packet:
  ESP tunnel overhead:
    Outer IP header:   20 bytes
    ESP header:         8 bytes  (SPI + SeqNum)
    IV:               12 bytes  (AES-GCM nonce)
    Padding:          0-15 bytes (average ~8 bytes)
    ESP trailer:        2 bytes  (pad_len + next_hdr)
    ICV:              16 bytes  (AES-GCM tag)
    UDP encap (NAT-T): 8 bytes  (if NAT-T active)
    TOTAL OVERHEAD: 66+ bytes (without NAT-T) or 74+ bytes (with NAT-T)
  
  Standard Ethernet MTU: 1500 bytes
  Maximum inner packet:  1500 - 66 = 1434 bytes (without NAT-T)
                         1500 - 74 = 1426 bytes (with NAT-T)
  Maximum TCP payload:   1434 - 20 (IP) - 20 (TCP) = 1394 bytes
                         (So TCP MSS should be ~1394 or lower)

Diagnosis:
  # Test with various packet sizes (DF bit set):
  for size in 1500 1450 1400 1350 1300; do
    result=$(ping -c 2 -M do -s $size 10.0.0.5 2>&1 | tail -1)
    echo "Size $size: $result"
  done
  # First size that fails shows where fragmentation occurs

  # Test TCP MSS (using hping3):
  hping3 -S -p 80 10.0.0.5 -d 1400  # TCP SYN with 1400-byte data
  
  # Check current MSS clamping:
  iptables -t mangle -L | grep MSS  # Should show TCPMSS target

Solutions:
  1. MSS Clamping (most common fix):
     iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN \
       -j TCPMSS --clamp-mss-to-pmtu
     # Alternatively set explicit MSS:
     iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN \
       -j TCPMSS --set-mss 1360
     
  2. Reduce interface MTU:
     ip link set eth0 mtu 1400  # Reduce physical interface MTU
     # VTI/XFRM interface MTU auto-calculation usually handles this
     
  3. Enable PMTUD (Path MTU Discovery):
     sysctl -w net.ipv4.ip_no_pmtu_disc=0  # Should be 0 (PMTUD enabled)
     
  4. On Cisco: crypto map + ip tcp adjust-mss
     interface Tunnel0
      ip tcp adjust-mss 1360  # Clamp TCP MSS on tunnel interface
```

---

## 23. Performance Troubleshooting

### 23.1 IPsec Throughput Bottlenecks

```
Throughput limiting factors:

1. CRYPTO CPU BOTTLENECK:
   - Software crypto on single core maxes out at ~1-2 Gbps (AES-CBC)
   - AES-NI (hardware) brings this to 5-10+ Gbps per core
   
   Check:
     grep -m1 'aes' /proc/cpuinfo  # AES-NI flag "aes" in flags
     openssl speed aes-256-gcm     # Benchmark software crypto speed
     
   Enable hardware acceleration:
     # Check if kernel is using hardware:
     lsmod | grep aes  # Should show: aes_x86_64, ghash_clmulni_intel
     
     # Disable and re-enable to verify:
     modprobe -r aesni_intel && modprobe aesni_intel
     
   Multi-core scaling:
     strongSwan: Use multiple threads (charon.threads = N_CPU * 2)
     Or use hardware offload via kernel's XFRM offload

2. KERNEL PROCESSING OVERHEAD:
   XFRM in kernel has per-packet overhead for policy lookup
   
   # Profile where CPU time goes:
   perf top -g  # During sustained traffic test
   # Look for: xfrm_output, esp_output, crypto functions
   
   Solutions:
   - XDP offload (DPDK-based bypass)
   - Hardware crypto NICs (Marvell, Cavium)
   - XFRM offload: ip xfrm state ... offload dev eth0 dir out

3. UDP SEND/RECV BUFFER SIZES:
   # For IKE performance (control plane):
   sysctl -w net.core.rmem_max=33554432
   sysctl -w net.core.wmem_max=33554432
   sysctl -w net.core.rmem_default=16777216
   sysctl -w net.core.wmem_default=16777216

4. PACKET RATE LIMITING:
   # Check if packets are being dropped before IPsec:
   ethtool -S eth0 | grep -i drop
   ip -s link show eth0 | grep "dropped\|error"

5. INTERRUPT COALESCING:
   # Check NIC interrupt settings:
   ethtool -c eth0
   # Tune for IPsec workload (lower latency vs higher throughput):
   ethtool -C eth0 rx-usecs 50 tx-usecs 50
```

### 23.2 Performance Benchmarking

```bash
# Benchmark IPsec tunnel throughput:

# Method 1: iperf3 through tunnel
# On server side (10.0.0.5):
iperf3 -s -p 5201

# On client side (through IPsec tunnel):
iperf3 -c 10.0.0.5 -p 5201 -t 30 -P 4 -i 5
# -P 4: 4 parallel streams (use multiple CPU cores)
# -t 30: 30-second test
# -i 5: Report every 5 seconds

# Method 2: iperf3 bidirectional (tests full-duplex):
iperf3 -c 10.0.0.5 -p 5201 -t 30 --bidir

# Method 3: Compare with non-encrypted baseline:
# 1. Measure raw throughput without IPsec
iperf3 -c 198.51.100.1 -p 5201 -t 10  # Direct to gateway
# 2. Measure through IPsec
iperf3 -c 10.0.0.5 -p 5201 -t 10
# Difference = IPsec overhead

# Latency test:
ping -c 100 -i 0.01 10.0.0.5 | tail -5
# Check: min/avg/max/mdev — stddev shows jitter
# IPsec adds ~0.1-0.5ms per packet typically

# Crypto throughput benchmark (without network):
openssl speed -evp aes-256-gcm
openssl speed -evp aes-256-cbc
# Compare: GCM should be faster than CBC + HMAC

# Kernel crypto subsystem stats:
cat /proc/sys/kernel/perf_event_paranoid
cat /sys/kernel/debug/x86/pat_memtype_list  # Cache policy
```

---

## 24. IPsec Security Audit Checklist

### 24.1 Algorithm Security Assessment

```
AUDIT CHECKLIST — Run against every IPsec deployment:

IKE SA Algorithms:
  □ Encryption: No 3DES, No DES, No NULL
    Recommended: AES-256-GCM or AES-256-CBC
  □ Integrity: No MD5, No SHA-1 (if possible)
    Recommended: SHA-256, SHA-384, SHA-512
  □ PRF: No MD5, No SHA-1
    Recommended: PRF-HMAC-SHA256
  □ DH Group: No Group 1 (768-bit), No Group 2 (1024-bit), No Group 5 (1536-bit)
    Recommended: Group 14 (minimum), Group 19/20 (preferred)

Child SA (ESP) Algorithms:
  □ Encryption: No NULL (unless AH is used alongside), No 3DES, No DES
    Recommended: AES-256-GCM-16
  □ If non-AEAD: Auth algo must be present (no encrypt-only without auth)
    Recommended: HMAC-SHA256-128
  □ PFS: Should be enabled for forward secrecy
    Recommended: Same DH group as IKE or stronger

Authentication:
  □ PSK: Minimum 256 bits of entropy (32+ random characters)
    Not: Dictionary words, short strings, default values
  □ Certificates: Not self-signed for production (use proper PKI)
  □ Certificates: Check expiry dates (audit > 30 days before expiry)
  □ CRL or OCSP: Certificate revocation checking enabled
  □ Wildcard certs: Avoid for IPsec identity (use specific CN/SAN)
```

### 24.2 Configuration Security Check Script

```bash
#!/bin/bash
# ipsec_security_audit.sh

echo "=== IPsec Security Audit ==="
echo "Date: $(date)"
echo ""

# Check IKE SA algorithms in use
echo "--- Active IKE SAs ---"
swanctl --list-sas 2>/dev/null | grep -E "IKE|AES|SHA|ECP|Group" || \
  ipsec statusall 2>/dev/null | grep -E "IKE|AES|SHA|ECP|Group"

# Check ESP SA algorithms
echo ""
echo "--- Active Child SAs (ESP) ---"
ip xfrm state | grep -E "aead|auth-trunc|enc|comp"

# Check for weak DH groups
echo ""
echo "--- DH Group Check ---"
ip xfrm state | grep -i "group\|DH"
swanctl --list-sas 2>/dev/null | grep -i "DH\|group"

# Check kernel security stats
echo ""
echo "--- XFRM Error Counters (non-zero = problem) ---"
awk '$2 != 0 {print $0}' /proc/net/xfrm_stat

# Check SA lifetimes
echo ""
echo "--- SA Lifetimes ---"
ip xfrm state | grep -A8 "lifetime config"

# Check replay window sizes
echo ""
echo "--- Anti-Replay Configuration ---"
ip xfrm state | grep "replay-window"

# Check NAT-T status
echo ""
echo "--- NAT-T Status ---"
ip xfrm state | grep encap

# Check certificates
echo ""
echo "--- Certificate Expiry ---"
for cert in /etc/ipsec.d/certs/*.pem /etc/swanctl/x509/*.pem 2>/dev/null; do
    [ -f "$cert" ] || continue
    expiry=$(openssl x509 -in "$cert" -noout -enddate 2>/dev/null | cut -d= -f2)
    days_left=$(( ($(date -d "$expiry" +%s) - $(date +%s)) / 86400 ))
    if [ "$days_left" -lt 30 ]; then
        echo "WARNING: $cert expires in $days_left days ($expiry)"
    else
        echo "OK: $cert expires in $days_left days"
    fi
done

echo ""
echo "=== Audit Complete ==="
```

### 24.3 IPsec Hardening Recommendations

```
HARDENING CHECKLIST:

1. ALGORITHM LOCKDOWN:
   # strongSwan — enforce strong algorithms only:
   connections.myconn.proposals = aes256gcm16-prfsha256-ecp256
   connections.myconn.children.mychild.esp_proposals = aes256gcm16-ecp256
   
   # Do NOT include weak fallback proposals in production.
   # Fallbacks allow downgrade attacks if attacker can interfere.

2. ANTI-REPLAY:
   # Ensure replay protection is not disabled:
   ip xfrm state | grep "no-ar"  # Should return empty! no-ar = disabled!
   
   # If using VTI or XFRM interfaces, replay is handled differently
   # Verify it's actually enabled

3. IDENTITY VALIDATION:
   # Ensure peer identity is strictly validated:
   # strongSwan: 'rightid' must be set to specific identity, not wildcard
   # Avoid: rightid = %any  (accepts any identity)
   # Prefer: rightid = vpn.remote.example.com  (exact match)

4. PERFECT FORWARD SECRECY:
   # PFS must be enabled for Child SAs:
   # ESP proposals must include DH group
   # connections.myconn.children.X.esp_proposals includes DH group!

5. DEAD PEER DETECTION:
   # Never disable DPD:
   # Disabled DPD → zombie SAs with stale keys → potential security risk
   # dpdaction=clear or restart, never none

6. LOGGING:
   # Log IKE events for security monitoring:
   # All AUTH failures, SA establishments, SA deletions
   # Forward logs to SIEM system

7. FIREWALL LOCKDOWN:
   # Allow ONLY specific peer IPs for IKE (UDP 500/4500):
   iptables -A INPUT -p udp --dport 500 -s 198.51.100.1 -j ACCEPT
   iptables -A INPUT -p udp --dport 500 -j DROP  # Drop all others
   
   # Allow ONLY ESP from known peer:
   iptables -A INPUT -p esp -s 198.51.100.1 -j ACCEPT
   iptables -A INPUT -p esp -j DROP

8. VPN BYPASS PREVENTION:
   # Add DISCARD policies to prevent traffic bypassing IPsec:
   # Traffic to/from VPN subnets MUST go through IPsec:
   ip xfrm policy add \
     src 0.0.0.0/0 dst 10.0.0.0/8 dir out priority 1 action block
   # (Lower priority protect policies installed by IKE will override this)
   # If IKE goes down: policies deleted, discard policy kicks in → no bypass
```

---

## 25. Quick Reference — State Machines and Timers

### 25.1 IKEv2 Timer Reference

```
TIMER NAME          DEFAULT     PURPOSE                    CONFIGURE IN
---------------------------------------------------------------------------
reauth_time         0 (=off)   Reauthenticate IKE SA      strongSwan conn
rekey_time          4h         Rekey IKE SA               strongSwan conn
over_time           10min      Delete grace period        strongSwan (margin)
life_time (child)   1h         Child SA hard lifetime     strongSwan child
rekey_time (child)  54min      Child SA soft lifetime     strongSwan child
rand_time           ~10%       Random variation           strongSwan child
dpd_delay           30s        DPD probe interval         strongSwan conn
dpd_timeout         150s       DPD total timeout          strongSwan conn
keep_alive          20s        NAT keepalive interval     strongswan.conf
retry_initiate      5s         Retransmit interval        strongSwan global
max_packet          1500       Max UDP packet size        strongSwan global
```

### 25.2 Protocol Number Quick Reference

```
IP Protocol Numbers (used in packet headers and tcpdump filters):
  4   = IPv4 (inner packet in tunnel)
  6   = TCP
  17  = UDP  
  41  = IPv6
  50  = ESP (Encapsulating Security Payload)
  51  = AH (Authentication Header)
  89  = OSPF (sometimes runs over IPsec)

Well-Known Ports for IPsec:
  UDP 500   = ISAKMP / IKE
  UDP 4500  = IKE NAT-T + ESP NAT-T
  TCP 4500  = (not standard, some implementations use for reliability)

IANA Protocol Transform IDs (used in IKEv2 proposals):
  ENCR:
    3  = 3DES-CBC (deprecated)
    11 = NULL encryption
    12 = AES-CBC
    13 = AES-CTR
    18 = AES-GCM (8-byte ICV)
    19 = AES-GCM (12-byte ICV)
    20 = AES-GCM (16-byte ICV)   ← RECOMMENDED
    28 = ChaCha20-Poly1305
  PRF:
    1  = PRF-HMAC-MD5 (deprecated)
    2  = PRF-HMAC-SHA1
    5  = PRF-HMAC-SHA2-256      ← RECOMMENDED
    6  = PRF-HMAC-SHA2-384
    7  = PRF-HMAC-SHA2-512
  AUTH:
    1  = HMAC-MD5-96 (deprecated)
    2  = HMAC-SHA1-96
    12 = HMAC-SHA2-256-128      ← RECOMMENDED
    13 = HMAC-SHA2-384-192
    14 = HMAC-SHA2-512-256
  DH:
    2  = MODP-1024 (deprecated)
    5  = MODP-1536
    14 = MODP-2048               ← MINIMUM ACCEPTABLE
    19 = ECP-256                 ← RECOMMENDED
    20 = ECP-384                 ← RECOMMENDED
    21 = ECP-521
    31 = Curve25519 (RFC 8031)
```

### 25.3 Troubleshooting Decision Tree

```
TUNNEL NOT WORKING — START HERE:

1. Can you reach peer on UDP 500?
   tcpdump -n -c 5 'udp port 500 and host PEER'
   
   NO → Network/firewall issue (Layer 0)
        Fix: Check routing, firewall, cloud security groups
   
   YES → Continue to 2.

2. Is IKE negotiation completing?
   journalctl -fu strongswan | grep -E "established|failed|error"
   
   NO → IKE-level failure (Layer 1-2)
        3a. "no proposal chosen" → Algorithm mismatch
        3b. "authentication failed" → PSK/cert issue
        3c. "peer not responding" → UDP not arriving at peer daemon
        3d. "TS unacceptable" → Traffic selector mismatch
   
   YES → Continue to 3.

3. Are Child SAs installed in kernel?
   ip xfrm state | grep "spi"
   
   NO → Child SA failure (Layer 3)
        Check: "creating CHILD_SA failed" in logs
        Fix: Proposals, PFS settings, traffic selectors
   
   YES → Continue to 4.

4. Are SPD policies installed?
   ip xfrm policy | grep "dir out"
   
   NO → Policy missing (Layer 4)
        Restart IKE daemon, check config
   
   YES → Continue to 5.

5. Does traffic match policy?
   ip xfrm policy get src SRCIP dst DSTIP dir out
   
   NO → Selector mismatch (Layer 4)
        Check leftsubnet/rightsubnet
   
   YES → Continue to 6.

6. Are packets being encrypted?
   watch 'ip -s xfrm state | grep -A5 "pkts"'
   Run ping → watch counter increment
   
   NO → Routing issue (Layer 5)
        ip route get DESTIP → check if traffic reaches policy check
        ip_forward enabled?
   
   YES → Continue to 7.

7. Are encrypted packets arriving at remote?
   tcpdump 'proto esp' on remote gateway
   
   NO → Network path issue for ESP (Layer 0)
        Firewall blocking proto 50?
        Use NAT-T: encapsulate ESP in UDP 4500
   
   YES → Continue to 8.

8. Are packets being decrypted successfully?
   awk '$2!=0' /proc/net/xfrm_stat on remote side
   ip -s xfrm state | grep "stats" on remote side
   
   NO → Decryption failure (auth error, key mismatch, replay)
        Check failed counter, check SA keys, check rekeying
   
   YES → Continue to 9.

9. Is decrypted traffic reaching destination host?
   tcpdump on remote side inner interface
   ip route on remote gateway for inner destination
   
   NO → Routing/forwarding issue on remote side
        ip_forward enabled? Routes correct? Firewall blocking?
   
   YES → It should be working. 
         Check application-level (correct ports, protocol?)
```

### 25.4 Log Message Quick Reference

```
MESSAGE                               MEANING / ACTION
--------------------------------------------------------------
"no proposal chosen"                  Algorithm mismatch — compare proposals
"authentication failed"               PSK wrong / cert not trusted / identity mismatch
"peer not responding"                 Network / firewall / daemon not running
"TS unacceptable"                     Traffic selector rejected — check subnets
"INVALID_KE_PAYLOAD"                  DH group mismatch (auto-corrects, normal)
"COOKIE required"                     Peer under load — normal, retry with cookie
"CHILD_SA_NOT_FOUND"                  Rekeying race condition — usually self-corrects
"DPD request timed out"               Peer unreachable — check network
"SA expired"                          Rekeying failed before hard lifetime
"sequence number overflow"            SA rekeying too slow — force rekey
"replay detected"                     Replay attack or severe reordering
"auth_failed N"                       Auth errors on SA (from ip -s xfrm state)
"XfrmInNoStates N"                    Packet arrived with no matching SA (SPI not found)
"XfrmInStateMismatch N"               Packet's inner selectors don't match SA selectors
"XfrmOutNoStates N"                   Outbound packet needs SA — triggering IKE ACQUIRE
"ACQUIRE"                             Kernel asking IKE to create SA — IKE must respond
```

---

## Appendix A: Complete Python Script — IPsec SA Monitor

```python
#!/usr/bin/env python3
"""
ipsec_monitor.py — Real-time IPsec SA monitor
Polls kernel XFRM stats and SA state, alerts on anomalies
Usage: python3 ipsec_monitor.py [--interval 5]
"""

import subprocess
import re
import time
import argparse
from dataclasses import dataclass, field
from typing import Dict, Optional
from datetime import datetime


@dataclass
class XfrmStat:
    """Parsed /proc/net/xfrm_stat counters"""
    in_no_states: int = 0          # No SA for inbound packet
    in_state_proto_error: int = 0  # SA protocol error (ICV fail)
    in_state_seq_error: int = 0    # Replay window error
    in_state_expired: int = 0      # SA expired
    in_tmpl_mismatch: int = 0      # Template mismatch
    out_no_states: int = 0         # No SA for outbound packet
    out_state_seq_error: int = 0   # Sequence overflow
    out_state_expired: int = 0     # Outbound SA expired

    @classmethod
    def from_proc(cls) -> 'XfrmStat':
        stat = cls()
        try:
            with open('/proc/net/xfrm_stat') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) != 2:
                        continue
                    name, val = parts[0], int(parts[1])
                    field_map = {
                        'XfrmInNoStates': 'in_no_states',
                        'XfrmInStateProtoError': 'in_state_proto_error',
                        'XfrmInStateSeqError': 'in_state_seq_error',
                        'XfrmInStateExpired': 'in_state_expired',
                        'XfrmInTmplMismatch': 'in_tmpl_mismatch',
                        'XfrmOutNoStates': 'out_no_states',
                        'XfrmOutStateSeqError': 'out_state_seq_error',
                        'XfrmOutStateExpired': 'out_state_expired',
                    }
                    if name in field_map:
                        setattr(stat, field_map[name], val)
        except FileNotFoundError:
            print("WARNING: /proc/net/xfrm_stat not found (not Linux?)")
        return stat


@dataclass
class SaState:
    """Parsed SA from 'ip xfrm state'"""
    src: str = ""
    dst: str = ""
    proto: str = ""
    spi: str = ""
    mode: str = ""
    seq: int = 0
    oseq: int = 0
    auth_errors: int = 0
    replay_errors: int = 0
    lifetime_soft_secs: Optional[int] = None
    lifetime_hard_secs: Optional[int] = None


def parse_xfrm_states() -> list:
    """Run 'ip -s xfrm state' and parse output"""
    try:
        output = subprocess.check_output(
            ['ip', '-s', 'xfrm', 'state'],
            stderr=subprocess.DEVNULL,
            text=True
        )
    except subprocess.CalledProcessError:
        return []

    states = []
    current = None
    for line in output.split('\n'):
        line = line.strip()
        # New SA starts with "src ... dst ..."
        m = re.match(r'^src (\S+) dst (\S+)$', line)
        if m:
            if current:
                states.append(current)
            current = SaState(src=m.group(1), dst=m.group(2))
            continue
        if not current:
            continue
        # Proto, SPI, mode
        m = re.match(r'proto (\w+) spi (0x[0-9a-f]+) .* mode (\w+)', line)
        if m:
            current.proto = m.group(1)
            current.spi   = m.group(2)
            current.mode  = m.group(3)
        # Anti-replay context
        m = re.search(r'seq (0x[0-9a-f]+), oseq (0x[0-9a-f]+)', line)
        if m:
            current.seq  = int(m.group(1), 16)
            current.oseq = int(m.group(2), 16)
        # Error stats
        m = re.search(r'replay-window (\d+) replay (\d+) failed (\d+)', line)
        if m:
            current.replay_errors = int(m.group(2))
            current.auth_errors   = int(m.group(3))

    if current:
        states.append(current)
    return states


def monitor_loop(interval: int = 5):
    """Main monitoring loop"""
    prev_stat = XfrmStat.from_proc()
    prev_states: Dict[str, SaState] = {}

    print(f"{'='*60}")
    print(f"IPsec SA Monitor — Started at {datetime.now().strftime('%H:%M:%S')}")
    print(f"Poll interval: {interval}s")
    print(f"{'='*60}")

    while True:
        time.sleep(interval)
        ts = datetime.now().strftime('%H:%M:%S')

        # ── XFRM Stat Deltas ──────────────────────────────────────
        curr_stat = XfrmStat.from_proc()
        alerts = []

        delta_auth_err   = curr_stat.in_state_proto_error - prev_stat.in_state_proto_error
        delta_replay_err = curr_stat.in_state_seq_error   - prev_stat.in_state_seq_error
        delta_no_sa_in   = curr_stat.in_no_states         - prev_stat.in_no_states
        delta_no_sa_out  = curr_stat.out_no_states         - prev_stat.out_no_states
        delta_seq_ovfl   = curr_stat.out_state_seq_error  - prev_stat.out_state_seq_error

        if delta_auth_err   > 0: alerts.append(f"ICV_AUTH_ERRORS +{delta_auth_err}")
        if delta_replay_err > 0: alerts.append(f"REPLAY_ERRORS +{delta_replay_err}")
        if delta_no_sa_in   > 0: alerts.append(f"NO_INBOUND_SA +{delta_no_sa_in}")
        if delta_no_sa_out  > 0: alerts.append(f"NO_OUTBOUND_SA +{delta_no_sa_out}")
        if delta_seq_ovfl   > 0: alerts.append(f"SEQ_OVERFLOW(CRITICAL!) +{delta_seq_ovfl}")

        prev_stat = curr_stat

        # ── SA State ──────────────────────────────────────────────
        curr_states = {f"{s.spi}:{s.dst}": s for s in parse_xfrm_states()}
        new_sas     = set(curr_states) - set(prev_states)
        deleted_sas = set(prev_states) - set(curr_states)

        for key in new_sas:
            s = curr_states[key]
            print(f"[{ts}] NEW SA: {s.proto.upper()} spi={s.spi} "
                  f"{s.src}→{s.dst} mode={s.mode}")

        for key in deleted_sas:
            s = prev_states[key]
            print(f"[{ts}] DEL SA: {s.proto.upper()} spi={s.spi} "
                  f"{s.src}→{s.dst}")

        # Check for high sequence numbers (rekeying should have happened)
        for key, sa in curr_states.items():
            if sa.oseq > 0xFFFF0000:
                alerts.append(f"SEQNUM_CRITICAL spi={sa.spi}: oseq={sa.oseq:#010x}")
            if sa.auth_errors > 0 and (
                key not in prev_states or
                prev_states[key].auth_errors != sa.auth_errors
            ):
                alerts.append(f"AUTH_ERR spi={sa.spi}: {sa.auth_errors} errors")

        prev_states = curr_states

        # ── Print Alerts ──────────────────────────────────────────
        for alert in alerts:
            print(f"[{ts}] *** ALERT: {alert} ***")

        if not alerts and not new_sas and not deleted_sas:
            sa_count = len(curr_states)
            print(f"[{ts}] OK — {sa_count} SAs active, no anomalies")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Monitor IPsec SA state")
    parser.add_argument('--interval', type=int, default=5, help="Poll interval in seconds")
    args = parser.parse_args()
    try:
        monitor_loop(args.interval)
    except KeyboardInterrupt:
        print("\nMonitor stopped.")
```

## Appendix B: Bash Debug Toolkit — One-File Reference

```bash
#!/bin/bash
# ipsec_toolkit.sh — All-in-one IPsec debug helper
# Usage: source ipsec_toolkit.sh

# Quick status overview
ipsec_status() {
    echo "=== IKE SAs ==="
    swanctl --list-sas 2>/dev/null || ipsec statusall 2>/dev/null | head -40

    echo ""
    echo "=== Kernel SA (XFRM State) ==="
    ip xfrm state | head -40

    echo ""
    echo "=== Kernel Policies (SPD) ==="
    ip xfrm policy

    echo ""
    echo "=== XFRM Error Counters ==="
    awk '$2 != 0 {print $1": "$2}' /proc/net/xfrm_stat

    echo ""
    echo "=== Network Sockets ==="
    ss -ulnp | grep -E "500|4500"
}

# Watch traffic counters
ipsec_watch() {
    watch -n 1 'ip -s xfrm state | grep -E "pkts|bytes|stats|failed|replay"'
}

# Full packet capture
ipsec_capture() {
    PEER="${1:?Usage: ipsec_capture PEER_IP [DURATION_SECS]}"
    DURATION="${2:-60}"
    FILE="/tmp/ipsec_$(date +%H%M%S)_${PEER}.pcap"
    echo "Capturing ${DURATION}s of IPsec traffic to/from $PEER → $FILE"
    timeout "$DURATION" tcpdump -n -w "$FILE" \
        "host $PEER and (udp port 500 or udp port 4500 or proto esp or proto ah)"
    echo "Saved to $FILE — open in Wireshark"
}

# Test proposals quickly
ipsec_probe() {
    PEER="${1:?Usage: ipsec_probe PEER_IP}"
    echo "Probing IKEv2 at $PEER..."
    ike-scan --ikev2 "$PEER" 2>/dev/null || \
        echo "ike-scan not installed. Install: apt install ike-scan"
}

# Check certificate
ipsec_cert() {
    CERT="${1:?Usage: ipsec_cert /path/to/cert.pem}"
    openssl x509 -in "$CERT" -noout -text | grep -E "Subject:|Issuer:|Not Before:|Not After:|Subject Alt"
    DAYS=$(( ($(date -d "$(openssl x509 -in "$CERT" -noout -enddate | cut -d= -f2)" +%s) - $(date +%s)) / 86400 ))
    echo "Days until expiry: $DAYS"
    [ "$DAYS" -lt 30 ] && echo "WARNING: Certificate expires soon!"
}

# Test connectivity to peer
ipsec_ping() {
    PEER="${1:?Usage: ipsec_ping PEER_IP}"
    echo "=== ICMP to peer ==="
    ping -c 4 "$PEER"
    echo ""
    echo "=== UDP 500 to peer ==="
    nc -zu -w 3 "$PEER" 500 && echo "UDP 500: OPEN" || echo "UDP 500: BLOCKED"
    echo ""
    echo "=== UDP 4500 to peer ==="
    nc -zu -w 3 "$PEER" 4500 && echo "UDP 4500: OPEN" || echo "UDP 4500: BLOCKED"
    echo ""
    echo "=== MTU test ==="
    for size in 1400 1300 1200; do
        result=$(ping -c 2 -M do -s "$size" "$PEER" 2>&1 | grep -c "bytes from")
        [ "$result" -gt 0 ] && echo "MTU ${size}B+28: OK" || echo "MTU ${size}B+28: FAIL"
    done
}

echo "IPsec toolkit loaded. Commands: ipsec_status, ipsec_watch, ipsec_capture, ipsec_probe, ipsec_cert, ipsec_ping"
```

---

*Reference RFCs: RFC 4301 (IPsec), RFC 4302 (AH), RFC 4303 (ESP), RFC 7296 (IKEv2), RFC 3706 (DPD), RFC 3948 (NAT-T), RFC 4555 (MOBIKE), RFC 8031 (Curve25519 for IKEv2)*