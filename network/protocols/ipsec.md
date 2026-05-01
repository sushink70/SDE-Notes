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
|  Layer 3: Network      <<< IPSec lives here >>>
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
| SA #1001  |<------ Direction A→B ------->| SA #1001  |
|  SPI=101  |                              |  SPI=101  |
|  AES-256  |                              |  AES-256  |
|  Key=0xAB |                              |  Key=0xAB |
|           |                              |           |
| SA #1002  |<------ Direction B→A ------->| SA #1002  |
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
     |   [ID_A, AUTH data]  <-- encrypted with SKEYID  |
     |                                                  |
     |<------ Message 6: Identity + Auth [ENCRYPTED]--  |
     |   [ID_B, AUTH data]  <-- encrypted with SKEYID  |
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
     |-- Message 1: SA + DH + Nonce + ID_A ----------> |
     |   [All crypto params + identity in one msg]      |
     |                                                  |
     |<- Message 2: SA + DH + Nonce + ID_B + AUTH ---- |
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
     |== EXCHANGE: IKE_SA_INIT ==========================|
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
     |== EXCHANGE: IKE_AUTH =============================|
     |                                                  |
     |------- Request 2: IKE_AUTH [ENCRYPTED] ------->  |
     |   HDR, SK { IDi, [CERT,] [CERTREQ,]             |
     |             [IDr,] AUTH, SAi2, TSi, TSr }        |
     |   [Identity, Auth proof, IPSec SA proposal,      |
     |    Traffic selectors]                            |
     |                                                  |
     |<------ Response 2: IKE_AUTH [ENCRYPTED] -------  |
     |   HDR, SK { IDr, [CERT,] AUTH, SAr2, TSi, TSr } |
     |   [Identity, Auth proof, IPSec SA acceptance,    |
     |    Traffic selectors]                            |
     |                                                  |
     |   === IKE SA + First IPSec SA both established! =|
     |   === Data can flow immediately after 4 messages =|
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
     |   HDR, SK { N(DELETE) }               |
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
     |   HDR, SK { SA, Ni, [KEi], TSi, TSr } |
     |                                        |
     |<-- CREATE_CHILD_SA [ENCRYPTED] ------  |
     |   HDR, SK { SA, Nr, [KEr], TSi, TSr } |
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
|IP Header: src=192.168.1.10, dst=10.0.0.20, proto=TCP           |
+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
|TTL|Pro|    Header Checksum    |    Source IP (192.168.1.10)     |
+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
|         Destination IP (10.0.0.20)    |    TCP Src Port         |
+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
|       TCP Dst Port        |          Sequence Number            |
+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
|                 Acknowledgment Number                           |
+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
|   Application Data (HTTP, SSH, etc.)                           |
+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+

After ESP Tunnel Mode (Gateway GW1 → Gateway GW2):
Byte 0         4         8         12        16
|     |     |     |     |     |     |     |     |     |     |
+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
|Ver=4|IHL=5|TOS  |       Total Length      | Identification |
+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
|Flags|FragOff    |TTL  |Proto=50 (ESP)|  Header Checksum    |
+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
|            Source IP: GW1 (203.0.113.1)                    |
+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
|         Destination IP: GW2 (198.51.100.1)                 |
+===================== ESP Header ============================+
|           Security Parameters Index (SPI) e.g. 0x0000C6BA  |
+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
|          Sequence Number (e.g., 00 00 27 10 = 10000)        |
+================= ESP IV (for CBC) or Nonce (for GCM) =======+
|    IV/Nonce: 8 or 12 bytes of random data                   |
|   (e.g., A3 F2 9B 1C 7E 44 D8 0F 22 B5 91 3A)              |
+================= ENCRYPTED PAYLOAD =========================+
|         [Original IP Header (192.168.1.10 → 10.0.0.20)]    |
|         [Original TCP Header (src:12345 dst:443)]           |
|         [HTTP Data: GET / HTTP/1.1...]                      |
|         ... all encrypted with AES-256-GCM ...              |
|         (nobody can see inner addresses or content)         |
+================= ESP Trailer ================================+
|                Padding (variable, 0-255 bytes)              |
+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
|  Pad Length   |  Next Header (4 = IPv4, inner packet)       |
+================= ICV (Authentication Tag) ===================+
|    GCM Tag: 16 bytes (128 bits) e.g.,                       |
|    8F 3A 91 C2 4B D0 E7 F5 12 6A 88 C4 3D 97 B1 2E         |
+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
```

### 14.2 IKEv2 IKE_SA_INIT Message Format

```
IKEv2 Message: IKE_SA_INIT Request
+========================================================+
|                   IKE HEADER                           |
+-----+-----+-----+-----+-----+-----+-----+-----+-------+
| Initiator SPI (8 bytes, random)                        |
| e.g.: A1 B2 C3 D4 E5 F6 07 18                          |
+-----+-----+-----+-----+-----+-----+-----+-----+-------+
| Responder SPI (8 bytes, zero for initial request)      |
| 00 00 00 00 00 00 00 00                                |
+-----+-----+-----+-----+-----+-----+-----+-----+-------+
|Next Payload|Vers|Exch Type|Flags|      Message ID      |
|  SA (33)   | 2.0| 34      | 0x08|      0x00000001      |
+-----+-----+-----+-----+-----+-----+-----+-----+-------+
|                   Total Length                         |
+========================================================+
|               SA PAYLOAD (Security Associations)       |
+-----+-----+-----+-----+-----+-----+-----+-----+-------+
|Next |Critical|      SA Payload Length                  |
| KE  |   0   |                                          |
+-----+-----+-----+-----+-----+-----+-----+-----+-------+
|       PROPOSAL #1                                      |
|  Proposal Num | Protocol ID=IKE | SPI Size=0 | 4 Trans |
+-----+-----+-----+-----+-----+-----+-----+-----+-------+
| Transform 1: ENCR_AES_CBC (type=1, id=12) keylen=256   |
| Transform 2: PRF_HMAC_SHA2_256 (type=2, id=5)          |
| Transform 3: AUTH_HMAC_SHA2_256_128 (type=3, id=12)    |
| Transform 4: DH_GROUP_19 (type=4, id=19)               |
+========================================================+
|               KE PAYLOAD (Key Exchange)                |
+-----+-----+-----+-----+-----+-----+-----+-----+-------+
|Next |Critical|       KE Payload Length                 |
| Ni  |   0   |                                          |
+-----+-----+-----+-----+-----+-----+-----+-----+-------+
| DH Group: 19 |          RESERVED                       |
+-----+-----+-----+-----+-----+-----+-----+-----+-------+
| DH Public Key (g^a mod p), 64 bytes for Group 19       |
| 04 7B 2A 9C F1 3D 5E 8B ... (64 bytes of DH public key)|
+========================================================+
|               Ni PAYLOAD (Nonce)                       |
+-----+-----+-----+-----+-----+-----+-----+-----+-------+
|Next |Critical|       Nonce Payload Length              |
|  0  |   0   |                                          |
+-----+-----+-----+-----+-----+-----+-----+-----+-------+
| Nonce data (16-32 bytes of random):                    |
| 3F A8 C1 9D 72 B4 E6 01 5C 8A 2F 7E D3 94 B0 61       |
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