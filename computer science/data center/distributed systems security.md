# DISTRIBUTED SYSTEMS SECURITY: COMPREHENSIVE GUIDE

## TABLE OF CONTENTS
1. Foundational Concepts
2. Threat Models & Attack Surface
3. Authentication & Identity Management
4. Authorization & Access Control
5. Secure Communication
6. Data Security & Encryption
7. Network Security Architecture
8. Consensus & Byzantine Fault Tolerance
9. Security in Microservices
10. Monitoring, Auditing & Incident Response
11. Common Attack Vectors
12. Defense Strategies & Best Practices

---

## 1. FOUNDATIONAL CONCEPTS

### What is a Distributed System?

A **distributed system** is a collection of independent computers (nodes) that appears to users as a single coherent system. These nodes:
- Communicate over a network
- Coordinate actions without shared memory
- Work toward common goals
- May fail independently

**Mental Model**: Think of a distributed system like a global corporation with offices worldwide. Each office (node) operates independently but must coordinate with others to achieve company objectives.

```
Single Machine System          Distributed System
┌──────────────┐              ┌─────┐   ┌─────┐   ┌─────┐
│              │              │Node │◄──┤Node │──►│Node │
│   CPU + RAM  │              │  A  │   │  B  │   │  C  │
│              │              └─────┘   └─────┘   └─────┘
│   Storage    │                 ▲         ▲         ▲
│              │                 │         │         │
└──────────────┘                 └─────Network──────┘
```

### Why Security is Harder in Distributed Systems

**Expanded Attack Surface**: More components = more potential entry points
**No Single Source of Truth**: Trust must be established across boundaries
**Network Unreliability**: Messages can be delayed, duplicated, or lost
**Partial Failures**: Some nodes may fail while others continue
**Coordination Challenges**: Security decisions must be consistent across nodes

```
Security Challenges Visualization:

                    ┌──────────────────────────┐
                    │   Network Boundary       │
    ┌───────────────┼──────────────────────────┼───────────────┐
    │               │                          │               │
┌───▼───┐       ┌───▼───┐                  ┌───▼───┐      ┌───▼───┐
│Node A │◄─────►│Node B │                  │Node C │      │Node D │
│(OK)   │       │(COMP.)│◄────────────────►│(FAIL) │      │(OK)   │
└───────┘       └───────┘                  └───────┘      └───────┘
   │                │                          │               │
   │    ┌──────────────────────────────────────┘               │
   │    │           Attacker may:                              │
   │    │           • Intercept traffic                        │
   │    │           • Impersonate nodes                        │
   │    └─────────► • Manipulate messages                      │
   │                • Exploit failed nodes                     │
   └──────────────────────────────────────────────────────────┘
```

### Core Security Principles (CIA Triad + Extensions)

**CIA Triad** is the foundation:

1. **Confidentiality**: Information is accessible only to authorized entities
2. **Integrity**: Data remains accurate and unaltered
3. **Availability**: System remains accessible when needed

Extended principles:

4. **Authenticity**: Verification of identity and origin
5. **Non-repudiation**: Proof that an action occurred (can't deny)
6. **Authorization**: Control over what authenticated entities can do

```
Security Principles in Action:

Request Flow Through Security Layers:

Client Request
     │
     ▼
┌─────────────────────────────────────┐
│ AUTHENTICATION                      │
│ "Who are you?"                      │ ──► Authenticity
│ • Verify identity                   │
│ • Check credentials                 │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ AUTHORIZATION                       │
│ "What can you do?"                  │ ──► Authorization
│ • Check permissions                 │
│ • Evaluate policies                 │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ SECURE COMMUNICATION                │
│ • Encrypt data in transit           │ ──► Confidentiality
│ • Verify message integrity          │ ──► Integrity
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ DATA ACCESS                         │
│ • Serve/modify data                 │ ──► Availability
│ • Log action                        │ ──► Non-repudiation
└─────────────────────────────────────┘
```

---

## 2. THREAT MODELS & ATTACK SURFACE

### Understanding Threat Models

A **threat model** is a structured representation of potential threats to your system. It helps identify:
- What you're protecting (assets)
- Who might attack (adversaries)
- How they might attack (attack vectors)
- What damage they could cause (impact)

**Mental Model**: Think like a fortress architect. You must understand every possible way an enemy could breach your defenses - walls, gates, underground tunnels, insider betrayal.

### Types of Adversaries

```
Adversary Capability Spectrum:

Weak                                                          Strong
├────────┼────────┼────────┼────────┼────────┼────────┼────────┤
│        │        │        │        │        │        │        │
Script   Skilled  Insider  Organized Nation  Advanced Advanced
Kiddie   Hacker   Threat   Crime    State    Persistent Persistent
                                              Threat   Threat
                                              (APT)    (Quantum)

Capabilities by Adversary Type:

┌─────────────────┬──────────────┬──────────────┬──────────────┐
│ Script Kiddie   │ Skilled      │ Organized    │ Nation State │
│                 │ Hacker       │ Crime        │ / APT        │
├─────────────────┼──────────────┼──────────────┼──────────────┤
│ • Use tools     │ • Develop    │ • Coordinate │ • Unlimited  │
│ • Limited skill │   exploits   │   attacks    │   resources  │
│ • Opportunistic │ • Target     │ • Financial  │ • Zero-days  │
│                 │   specific   │   motivated  │ • Long-term  │
│                 │   systems    │ • Resources  │   campaigns  │
└─────────────────┴──────────────┴──────────────┴──────────────┘
```

### Byzantine Threat Model

**Byzantine failure** occurs when a node behaves arbitrarily - it might send conflicting information to different nodes, crash, or act maliciously.

**Origin**: Named after the "Byzantine Generals Problem" - generals must coordinate an attack but some may be traitors.

```
Byzantine Scenario:

Honest Nodes vs Byzantine (Malicious) Node:

General A (Honest)          General B (Byzantine)      General C (Honest)
     │                              │                         │
     │  "Attack at dawn"            │                         │
     ├─────────────────────────────►│                         │
     │                              │  "A says: Attack"       │
     │                              ├────────────────────────►│
     │                              │                         │
     │                              │  "A says: Retreat"      │
     │                              ├────────────────────────►│
     │                                                        │
     │  "Attack at dawn"                                      │
     ├────────────────────────────────────────────────────────►
     
Node B is Byzantine - sends conflicting messages!
Node C cannot trust any single message.
```

### Common Attack Vectors

```
Attack Surface Map:

┌──────────────────────────────────────────────────────────────┐
│                    DISTRIBUTED SYSTEM                        │
│                                                              │
│  ┌────────────┐         ┌────────────┐         ┌─────────┐  │
│  │  Client    │         │   Load     │         │ Service │  │
│  │  Layer     │◄───────►│  Balancer  │◄───────►│  A      │  │
│  └────────────┘         └────────────┘         └─────────┘  │
│       ▲                      ▲                      ▲        │
│       │                      │                      │        │
│  [1] Man-in-Middle      [2] DDoS              [3] Injection │
│  [4] Session Hijack     [5] Route Poison      [6] IDOR      │
│       │                      │                      │        │
│       ▼                      ▼                      ▼        │
│  ┌────────────┐         ┌────────────┐         ┌─────────┐  │
│  │  Message   │◄───────►│   Service  │◄───────►│Database │  │
│  │  Queue     │         │     B      │         │         │  │
│  └────────────┘         └────────────┘         └─────────┘  │
│       ▲                      ▲                      ▲        │
│  [7] Poison Msgs        [8] Privilege Esc     [9] SQL Inj  │
│  [10] Replay Attack     [11] Code Injection   [12] Data Leak│
│                                                              │
└──────────────────────────────────────────────────────────────┘

Network Layer Attacks:
    [13] Eavesdropping  [14] Packet Sniffing  [15] DNS Spoofing

Infrastructure Attacks:
    [16] Supply Chain   [17] Side Channel     [18] Physical Access
```

### Attack Types Detailed

**1. Man-in-the-Middle (MITM)**
- Attacker intercepts communication between two parties
- Can read, modify, or inject messages
- Defense: End-to-end encryption, certificate pinning

**2. Distributed Denial of Service (DDoS)**
- Overwhelm system with massive traffic
- Makes service unavailable to legitimate users
- Defense: Rate limiting, traffic filtering, CDN

**3. Injection Attacks**
- Inserting malicious data into inputs
- Examples: SQL injection, command injection, LDAP injection
- Defense: Input validation, parameterized queries, sandboxing

**4. Session Hijacking**
- Stealing or predicting session tokens
- Impersonating legitimate users
- Defense: Secure session management, token rotation, HTTP-only cookies

**5. Route Poisoning**
- Corrupting routing information
- Misdirecting traffic to malicious nodes
- Defense: Authenticated routing protocols, secure BGP

**6. Insecure Direct Object Reference (IDOR)**
- Accessing resources without authorization by changing identifiers
- Example: Changing user_id=123 to user_id=124 in URL
- Defense: Proper authorization checks, indirect references

**7. Message Queue Poisoning**
- Injecting malicious messages into queues
- Can crash consumers or trigger unintended actions
- Defense: Message signing, schema validation, dead letter queues

**8. Privilege Escalation**
- Gaining higher access levels than authorized
- Horizontal (same level, different user) or Vertical (higher privileges)
- Defense: Principle of least privilege, proper role management

**9. SQL Injection**
- Manipulating database queries through untrusted input
- Can read, modify, or delete data
- Defense: Prepared statements, ORMs, input validation

**10. Replay Attack**
- Capturing and resending valid messages
- Can duplicate transactions or gain unauthorized access
- Defense: Timestamps, nonces, sequence numbers

---

## 3. AUTHENTICATION & IDENTITY MANAGEMENT

### What is Authentication?

**Authentication** is the process of verifying the identity of a user, service, or device.

**Mental Model**: Authentication is like showing your passport at airport security - you prove you are who you claim to be.

### Authentication Factors

```
Three Categories of Authentication Factors:

┌──────────────────┬──────────────────┬──────────────────┐
│ Something You    │ Something You    │ Something You    │
│ KNOW             │ HAVE             │ ARE              │
├──────────────────┼──────────────────┼──────────────────┤
│ • Password       │ • Security Token │ • Fingerprint    │
│ • PIN            │ • Smart Card     │ • Facial Recog   │
│ • Security Q&A   │ • Phone (SMS)    │ • Iris Scan      │
│ • Passphrase     │ • Hardware Key   │ • Voice Pattern  │
└──────────────────┴──────────────────┴──────────────────┘

Security Strength:

Single Factor:        Weak
    [Password]
         │
         ▼
Two Factor (2FA):     Strong
    [Password] + [Phone SMS]
         │
         ▼
Multi-Factor (MFA):   Very Strong
    [Password] + [Hardware Key] + [Biometric]
```

### Authentication Methods in Distributed Systems

**1. Token-Based Authentication**

```
Token Authentication Flow:

Client                    Auth Server              Resource Server
  │                            │                          │
  │ 1. Login Credentials       │                          │
  ├───────────────────────────►│                          │
  │                            │ 2. Validate              │
  │                            │    Credentials           │
  │                            │                          │
  │ 3. Return Access Token     │                          │
  │◄───────────────────────────┤                          │
  │                            │                          │
  │ 4. Request + Token                                    │
  ├──────────────────────────────────────────────────────►│
  │                                         5. Validate   │
  │                                            Token      │
  │                            6. Optional: Verify with   │
  │                               Auth Server             │
  │                            ◄─────────────────────────►│
  │                                                       │
  │ 7. Return Protected Resource                         │
  │◄──────────────────────────────────────────────────────┤
  │                                                       │

Token Structure (JWT Example):
┌──────────┬────────────┬───────────┐
│  Header  │  Payload   │ Signature │
├──────────┼────────────┼───────────┤
│ Algorithm│ Claims:    │ Crypto    │
│ Type     │ • user_id  │ Signature │
│          │ • exp_time │           │
│          │ • roles    │           │
└──────────┴────────────┴───────────┘
```

**JWT (JSON Web Token)**: A compact, self-contained token format
- **Header**: Metadata (algorithm used)
- **Payload**: Claims (user info, expiration)
- **Signature**: Cryptographic signature for verification

**Advantages**: Stateless, scalable, cross-domain
**Disadvantages**: Cannot revoke before expiration, token size

**2. OAuth 2.0 / OpenID Connect**

**OAuth 2.0**: Authorization framework for delegated access
**OpenID Connect**: Authentication layer built on OAuth 2.0

```
OAuth 2.0 Authorization Code Flow:

User        Client App      Authorization       Resource
Browser                     Server              Server
  │              │               │                  │
  │ 1. Request   │               │                  │
  │   Resource   │               │                  │
  ├─────────────►│               │                  │
  │              │ 2. Redirect   │                  │
  │              │   to Auth     │                  │
  │◄─────────────┤               │                  │
  │                              │                  │
  │ 3. Login & Authorize         │                  │
  ├─────────────────────────────►│                  │
  │              4. Auth Code    │                  │
  │◄─────────────────────────────┤                  │
  │              │               │                  │
  │ 5. Send Auth │               │                  │
  │    Code      │               │                  │
  ├─────────────►│               │                  │
  │              │ 6. Exchange   │                  │
  │              │   Code for    │                  │
  │              │   Tokens      │                  │
  │              ├──────────────►│                  │
  │              │ 7. Access +   │                  │
  │              │   Refresh     │                  │
  │              │   Tokens      │                  │
  │              │◄──────────────┤                  │
  │              │               │                  │
  │              │ 8. Request    │                  │
  │              │   Resource    │                  │
  │              │   + Token     │                  │
  │              ├────────────────────────────────► │
  │              │               │ 9. Resource Data │
  │              │◄───────────────────────────────── │
  │ 10. Display  │               │                  │
  │    Resource  │               │                  │
  │◄─────────────┤               │                  │
```

**Key OAuth 2.0 Concepts**:
- **Resource Owner**: The user
- **Client**: Application requesting access
- **Authorization Server**: Issues tokens
- **Resource Server**: Hosts protected resources
- **Authorization Code**: Temporary code exchanged for token
- **Access Token**: Used to access resources
- **Refresh Token**: Used to get new access tokens

**3. Mutual TLS (mTLS)**

Both client and server authenticate each other using certificates.

```
Mutual TLS Handshake:

Client                              Server
  │                                    │
  │ 1. Client Hello                    │
  ├───────────────────────────────────►│
  │                                    │ 2. Server Hello
  │                                    │    + Server Certificate
  │◄───────────────────────────────────┤
  │                                    │
  │ 3. Verify Server Certificate       │
  │    (Check: CA, expiry, hostname)   │
  │                                    │
  │ 4. Client Certificate              │
  │    + Certificate Verify            │
  ├───────────────────────────────────►│
  │                                    │ 5. Verify Client Cert
  │                                    │    (Check: CA, expiry)
  │                                    │
  │ 6. Encrypted Communication         │
  │◄──────────────────────────────────►│
  │    Both parties authenticated!     │

Certificate Chain:
┌─────────────────┐
│ Root CA         │ (Trusted anchor)
└────────┬────────┘
         │
    ┌────▼────────┐
    │ Intermediate│ (Intermediate CA)
    │ CA          │
    └────┬────────┘
         │
    ┌────▼────────┐
    │ End Entity  │ (Server/Client Certificate)
    │ Certificate │
    └─────────────┘
```

**4. API Keys**

Simple secret strings used to authenticate API requests.

```
API Key Authentication:

Client Request:
┌────────────────────────────────────────────┐
│ GET /api/data                              │
│ Headers:                                   │
│   X-API-Key: sk_live_abc123xyz...          │
└────────────────────────────────────────────┘
         │
         ▼
Server Validation:
┌────────────────────────────────────────────┐
│ 1. Extract API key from header             │
│ 2. Look up key in database                 │
│ 3. Check:                                  │
│    • Key exists and is active              │
│    • Key hasn't expired                    │
│    • Rate limits not exceeded              │
│ 4. Identify associated account/project     │
│ 5. Apply permissions/quotas                │
└────────────────────────────────────────────┘

Weakness: Keys are static and long-lived
         If compromised, attacker has full access
```

### Identity Federation

**Identity Federation**: Linking user identities across multiple systems.

**SAML (Security Assertion Markup Language)**: XML-based standard for exchanging authentication data.

```
SAML SSO Flow (Service Provider Initiated):

User        Service Provider       Identity Provider
  │               │                       │
  │ 1. Access     │                       │
  │    Resource   │                       │
  ├──────────────►│                       │
  │               │ 2. Check if           │
  │               │    authenticated      │
  │               │    (No session)       │
  │               │                       │
  │               │ 3. Generate SAML      │
  │               │    Request            │
  │               │                       │
  │ 4. Redirect   │                       │
  │    to IdP     │                       │
  │◄──────────────┤                       │
  │                                       │
  │ 5. Present SAML Request               │
  ├──────────────────────────────────────►│
  │                       6. Authenticate │
  │                          User         │
  │                                       │
  │ 7. SAML Response (Assertion)          │
  │◄──────────────────────────────────────┤
  │                                       │
  │ 8. POST Assertion                     │
  │    to SP                              │
  ├──────────────►│                       │
  │               │ 9. Validate Signature │
  │               │    Extract Claims     │
  │               │    Create Session     │
  │               │                       │
  │ 10. Access    │                       │
  │     Granted   │                       │
  │◄──────────────┤                       │
```

### Service-to-Service Authentication

```
Service Mesh Authentication Pattern:

┌─────────────────────────────────────────────────────┐
│                  Service Mesh                       │
│                                                     │
│  ┌─────────┐                      ┌─────────┐      │
│  │Service A│                      │Service B│      │
│  │         │                      │         │      │
│  │  ┌───┐  │                      │  ┌───┐  │      │
│  │  │App│  │                      │  │App│  │      │
│  │  └─┬─┘  │                      │  └─▲─┘  │      │
│  │    │    │                      │    │    │      │
│  │  ┌─▼────┐│    mTLS Encrypted   │  ┌─┴────┐│      │
│  │  │Proxy ├┼──────────────────────┼─►│Proxy ││      │
│  │  │(Envoy││     Connection      ││ │(Envoy││      │
│  │  └──────┘│                      │  └──────┘│      │
│  └─────────┘│                      │└─────────┘      │
│             │                      │                 │
│     ▲       │                      │      ▲          │
│     │       │                      │      │          │
│     │  ┌────▼──────────────────────▼──────┴───┐     │
│     │  │    Control Plane (Istio/Linkerd)     │     │
│     │  │  • Certificate Management            │     │
│     └──┤  • Identity Assignment               │     │
│        │  • Policy Enforcement                │     │
│        └──────────────────────────────────────┘     │
└─────────────────────────────────────────────────────┘

Identity Assignment:
Each service gets a cryptographic identity (SPIFFE ID)
Example: spiffe://cluster.local/ns/default/sa/service-a
```

---

## 4. AUTHORIZATION & ACCESS CONTROL

### What is Authorization?

**Authorization** determines what an authenticated entity is permitted to do.

**Mental Model**: After showing your passport (authentication), the customs officer checks your visa to see which areas you can enter (authorization).

### Access Control Models

**1. Discretionary Access Control (DAC)**

Resource owner decides who gets access.

```
DAC Example - File System:

Owner: Alice
┌──────────────────────────────────┐
│ File: document.txt               │
│ Owner: Alice                     │
│ Permissions:                     │
│   Owner (Alice):    Read, Write  │
│   User (Bob):       Read         │
│   User (Charlie):   None         │
└──────────────────────────────────┘

Alice (owner) has full control to grant/revoke access
```

**2. Mandatory Access Control (MAC)**

System enforces access based on security labels/classifications.

```
MAC Security Levels:

┌─────────────────────────────────────────┐
│          Top Secret                     │  Highest
├─────────────────────────────────────────┤
│              Secret                     │
├─────────────────────────────────────────┤
│          Confidential                   │
├─────────────────────────────────────────┤
│             Public                      │  Lowest
└─────────────────────────────────────────┘

Rules:
• No Read Up: Can't read higher classification
• No Write Down: Can't write to lower classification

User with Secret clearance:
  ✓ Can read: Public, Confidential, Secret
  ✗ Cannot read: Top Secret
  ✓ Can write: Secret, Top Secret
  ✗ Cannot write: Public, Confidential
```

**3. Role-Based Access Control (RBAC)**

Permissions assigned to roles, users assigned to roles.

```
RBAC Structure:

Users          Roles          Permissions
┌──────┐      ┌────────┐     ┌──────────────┐
│Alice │─────►│ Admin  │────►│ CreateUser   │
└──────┘      └────────┘     │ DeleteUser   │
                              │ ViewAuditLog │
┌──────┐      ┌────────┐     └──────────────┘
│ Bob  │─────►│ Editor │────►┌──────────────┐
└──────┘      └────────┘     │ CreatePost   │
                              │ EditPost     │
┌──────┐      ┌────────┐     │ DeletePost   │
│Carol │─────►│ Viewer │     └──────────────┘
└──────┘      └────────┘     ┌──────────────┐
                         ────►│ ViewPost     │
                              └──────────────┘

Hierarchy Example:
     Admin
       │
   ┌───┴───┐
   │       │
Editor   Moderator
   │       │
   └───┬───┘
       │
    Viewer

(Higher roles inherit lower role permissions)
```

**4. Attribute-Based Access Control (ABAC)**

Access based on attributes of user, resource, environment.

```
ABAC Decision Process:

Request: Can Alice access Document X?

┌──────────────────────────────────────────────────────┐
│                Policy Evaluation                      │
│                                                       │
│  Subject Attributes:        Resource Attributes:     │
│  ┌────────────────┐         ┌────────────────┐      │
│  │ name: Alice    │         │ type: Document │      │
│  │ role: Manager  │         │ classification:│      │
│  │ department: HR │         │   Confidential │      │
│  │ clearance:     │         │ owner: HR      │      │
│  │   Secret       │         │ created: 2024  │      │
│  └────────────────┘         └────────────────┘      │
│                                                       │
│  Environment Attributes:                             │
│  ┌────────────────────────────┐                      │
│  │ time: 09:00                │                      │
│  │ location: Office Network   │                      │
│  │ device: Managed Laptop     │                      │
│  └────────────────────────────┘                      │
│                                                       │
│  Policy Rules:                                       │
│  IF subject.role == "Manager"                        │
│     AND subject.department == resource.owner         │
│     AND subject.clearance >= resource.classification │
│     AND environment.location == "Office Network"     │
│  THEN ALLOW                                          │
│                                                       │
│  Decision: ✓ ALLOW                                   │
└──────────────────────────────────────────────────────┘
```

**5. Relationship-Based Access Control (ReBAC)**

Access based on relationships between entities (used in social networks, Google Drive sharing).

```
ReBAC Example - Document Sharing:

          Alice
            │ owner
            ▼
        Document
            │ shared_with (editor)
            ├─────────────┐
            │             │
            ▼             ▼
          Bob           Carol
            │ shared_with (viewer)
            ▼
          Dave

Access Rights:
• Alice: Full control (owner)
• Bob: Read, Write (editor)
• Carol: Read, Write (editor)
• Dave: Read only (viewer through Bob)

Query: "Can Dave read Document?"
Path: Dave ──(viewer)──► Bob ──(editor)──► Document
Answer: Yes (transitive relationship)
```

### Policy Enforcement Architectures

**1. Policy Enforcement Point (PEP)**

```
Policy-Based Access Control Architecture:

                    Request
                       │
                       ▼
    ┌──────────────────────────────────────┐
    │  Policy Enforcement Point (PEP)      │
    │  (API Gateway / Service Mesh)        │
    └──────────────┬───────────────────────┘
                   │
                   │ Decision Query:
                   │ "Can Alice DELETE /resource/123?"
                   │
                   ▼
    ┌──────────────────────────────────────┐
    │ Policy Decision Point (PDP)          │
    │ • Evaluates policies                 │
    │ • Combines rules                     │
    │ • Returns ALLOW/DENY                 │
    └──────────────┬───────────────────────┘
                   │
           ┌───────┴───────┐
           │               │
           ▼               ▼
    ┌──────────┐    ┌─────────────┐
    │ Policy   │    │ Policy Info │
    │ Admin    │    │ Point (PIP) │
    │ Point    │    │ (Attributes)│
    │ (PAP)    │    └─────────────┘
    │ (Policies│
    │  Rules)  │
    └──────────┘
         ▲
         │ Policy Updates
         │
    Administrator
```

**2. Zero Trust Architecture**

**Zero Trust**: "Never trust, always verify" - no implicit trust based on location.

```
Traditional Perimeter Model vs Zero Trust:

TRADITIONAL PERIMETER:
┌────────────────────────────────────────┐
│        Trusted Internal Network        │
│  ┌────┐  ┌────┐  ┌────┐  ┌────┐       │
│  │User│  │Svc │  │Svc │  │DB  │       │
│  └────┘  └────┘  └────┘  └────┘       │
│     │       │       │       │          │
│     └───────┴───────┴───────┘          │
│         Implicit Trust                 │
└────────────────────────────────────────┘
         Firewall (Hard Shell)
┌────────────────────────────────────────┐
│         Untrusted Internet             │
└────────────────────────────────────────┘

ZERO TRUST:
Every connection authenticated & authorized
┌────────────────────────────────────────┐
│    User                  Service A     │
│     │ ①Auth               │            │
│     ├────────►[PDP]       │            │
│     │ ②Allow              │            │
│     ├────────────────────►│ ③Auth      │
│     │                     ├────►[PDP]  │
│     │              Service B ④Allow    │
│     │                     │◄───┘       │
│     │              ⑤Auth  ▼            │
│     │              ┌────[PDP]          │
│     │              │   ⑥Allow          │
│     │              ▼                   │
│     │         Database                 │
└────────────────────────────────────────┘

Principles:
• Verify explicitly (authenticate every request)
• Least privilege access
• Assume breach (micro-segmentation)
```

### Common Authorization Patterns

**1. Token-Based Authorization**

```
JWT Claims for Authorization:

{
  "sub": "user123",
  "name": "Alice",
  "roles": ["editor", "viewer"],
  "permissions": [
    "post:create",
    "post:edit",
    "post:delete"
  ],
  "resource_access": {
    "project_x": ["read", "write"],
    "project_y": ["read"]
  },
  "iat": 1640000000,
  "exp": 1640003600
}

Service checks token claims:
IF "post:edit" IN token.permissions
   AND requested_resource IN token.resource_access
THEN ALLOW
```

**2. OAuth Scopes**

```
OAuth Scope Authorization:

User authorizes app with limited scopes:

┌────────────────────────────────────┐
│   Authorization Request            │
│                                    │
│ Client: PhotoApp                   │
│ Requesting:                        │
│   • profile:read                   │
│   • photos:read                    │
│   • photos:write                   │
│                                    │
│ [Allow] [Deny]                     │
└────────────────────────────────────┘

Issued Access Token includes scopes:
{
  "access_token": "...",
  "scope": "profile:read photos:read photos:write"
}

When accessing resources:
GET /api/photos/123
Authorization: Bearer <token>

Resource Server checks:
• Token valid?
• "photos:read" scope present?
→ ALLOW
```

---

## 5. SECURE COMMUNICATION

### Encryption Fundamentals

**Encryption**: Converting plaintext to ciphertext using a key.
**Decryption**: Reversing ciphertext back to plaintext.

**Mental Model**: Encryption is like locking a message in a box. Only those with the correct key can open it.

```
Encryption Process:

Plaintext ──►[ Encryption ]──► Ciphertext ──►[ Decryption ]──► Plaintext
                  ▲    Algorithm       ▲           ▲
                  │                    │           │
                Key                    Key         Key
```

### Symmetric vs Asymmetric Encryption

**Symmetric Encryption**: Same key for encryption and decryption.

```
Symmetric Encryption:

Alice                                    Bob
  │                                       │
  │  Shared Secret Key: K                │
  │         ┌────────────────────┐       │
  │ ───────►│  AES Encryption    │       │
  │ Message │  with Key K        │       │
  │         └─────────┬──────────┘       │
  │                   │                  │
  │         Encrypted Message            │
  ├─────────────────────────────────────►│
  │                                  ┌───▼────────┐
  │                                  │  Decrypt   │
  │                                  │  with Key K│
  │                                  └───┬────────┘
  │                                      │
  │                                  Message

Advantages: Fast, efficient for bulk data
Disadvantages: Key distribution problem
              (How do Alice and Bob securely share K?)

Common Algorithms: AES, ChaCha20
```

**Asymmetric Encryption**: Different keys for encryption (public) and decryption (private).

```
Asymmetric Encryption:

Alice                                    Bob
  │                                       │
  │                    ┌──────────────────┤
  │                    │  Key Pair:       │
  │                    │  • Public Key    │
  │  ◄─────────────────┤  • Private Key   │
  │  (Bob's public key)└──────────────────┘
  │                                       │
  │  ┌──────────────┐                     │
  │  │ Encrypt with │                     │
  │──► Bob's Public │                     │
  │  │     Key      │                     │
  │  └──────┬───────┘                     │
  │         │                             │
  │    Ciphertext                         │
  ├─────────────────────────────────────► │
  │                           ┌───────────▼──┐
  │                           │ Decrypt with │
  │                           │ Bob's Private│
  │                           │     Key      │
  │                           └───────────┬──┘
  │                                       │
  │                                   Message

Advantages: Solves key distribution problem
           Public key can be shared openly
Disadvantages: Slow, computationally expensive

Common Algorithms: RSA, ECC, ElGamal
```

### Hybrid Encryption (TLS Model)

Real-world systems combine both:

```
TLS Hybrid Encryption:

1. Handshake (Asymmetric):
   Establish shared symmetric key

Client                          Server
  │                               │
  │  ──── Client Hello ─────────► │
  │  ◄─── Server Hello ──────────  │
  │  ◄─── Server Certificate ────  │
  │       (RSA Public Key)         │
  │                               │
  │  Generate random symmetric    │
  │  key (Session Key)            │
  │                               │
  │  Encrypt Session Key with     │
  │  Server's Public Key          │
  │  ─────────────────────────────►│
  │                          Decrypt with
  │                          Private Key
  │                               │
  │ Both now share Session Key    │
  │◄──────────────────────────────►│

2. Data Transfer (Symmetric):
   Use session key with AES

  │   Encrypt data with Session Key
  ├──────────────────────────────►│
  │◄───────────────────────────────┤
     Decrypt with Session Key

Benefit: Asymmetric for key exchange (security)
        Symmetric for data transfer (speed)
```

### Transport Layer Security (TLS)

**TLS Handshake** in detail:

```
Detailed TLS 1.3 Handshake:

Client                                         Server
  │                                              │
  │ ClientHello                                  │
  │ • Supported cipher suites                    │
  │ • Random nonce                               │
  │ • Key share (DH public key)                  │
  ├─────────────────────────────────────────────►│
  │                                              │
  │                                    ServerHello│
  │                    • Selected cipher suite    │
  │                    • Random nonce             │
  │                    • Key share (DH public)    │
  │                              {EncryptedExtens}│
  │                              {Certificate}    │
  │                              {CertVerify}     │
  │◄─────────────────────────────────────────────┤
  │                              {Finished}       │
  │                                              │
  │ (Compute shared secret from DH exchange)     │
  │ (Derive encryption keys)                     │
  │                                              │
  │ {Finished}                                   │
  ├─────────────────────────────────────────────►│
  │                                              │
  │ ═══════ Encrypted Application Data ═══════  │
  │◄────────────────────────────────────────────►│

{ } = Encrypted
DH = Diffie-Hellman key exchange

Perfect Forward Secrecy (PFS):
Even if server's long-term key is compromised later,
past session keys cannot be recovered.
```

### Message Authentication & Integrity

**HMAC (Hash-based Message Authentication Code)**: Verifies both integrity and authenticity.

```
HMAC Construction:

Message: "Transfer $100 to Bob"
Shared Secret: K

┌──────────────────────────────────┐
│  HMAC = Hash(K || Hash(K || M))  │
└──────────────────────────────────┘

Sender (Alice):
Message + HMAC(K, Message) ───────► Receiver (Bob)

Verification (Bob):
1. Compute HMAC'= HMAC(K, received_message)
2. Compare HMAC' with received HMAC
3. If equal: ✓ Message authentic and intact
   If different: ✗ Message tampered or fake

Properties:
• Integrity: Detects any modification
• Authenticity: Only holder of K can create valid HMAC
• Non-repudiation: (Limited - requires shared secret)
```

### Digital Signatures

**Digital Signature**: Asymmetric equivalent of HMAC.

```
Digital Signature Process:

Signing (Alice):
┌─────────────────────────────────────────────┐
│  Message                                    │
│     │                                       │
│     ▼                                       │
│  [Hash Function] ──► Message Digest        │
│                         │                  │
│                         ▼                  │
│                   [Encrypt with            │
│                    Alice's Private Key]    │
│                         │                  │
│                         ▼                  │
│                  Digital Signature         │
└─────────────────────────────────────────────┘

Transmission:
Message + Signature ──────────► Bob

Verification (Bob):
┌─────────────────────────────────────────────┐
│  Signature           Message                │
│     │                   │                   │
│     ▼                   ▼                   │
│  [Decrypt with      [Hash Function]         │
│   Alice's            │                      │
│   Public Key]        ▼                      │
│     │           Message Digest'             │
│     ▼                   │                   │
│  Original Digest        │                   │
│     │                   │                   │
│     └───────[Compare]───┘                   │
│                │                            │
│                ▼                            │
│          If equal: ✓ Valid                  │
│          If different: ✗ Invalid            │
└─────────────────────────────────────────────┘

Properties:
• Non-repudiation: Only Alice could have signed
• Integrity: Detects tampering
• Authenticity: Verifies sender identity

Common Algorithms: RSA, ECDSA, EdDSA
```

### Certificate Authorities & PKI

**PKI (Public Key Infrastructure)**: System for managing certificates and public keys.

```
Certificate Authority Hierarchy:

┌────────────────────────────────────┐
│  Root CA                           │  Self-signed
│  • Highest trust anchor            │  Offline storage
│  • Self-signed certificate         │  Rarely used
└──────────────┬─────────────────────┘
               │ Signs
               ▼
┌────────────────────────────────────┐
│  Intermediate CA                   │  Online
│  • Signed by Root CA               │  Issues certs
│  • Issues end-entity certificates  │  Can be revoked
└──────────────┬─────────────────────┘
               │ Signs
               ▼
┌────────────────────────────────────┐
│  End-Entity Certificate            │  Server cert
│  • For specific domain/service     │  
│  • Signed by Intermediate CA       │  
└────────────────────────────────────┘

Certificate Content:
┌──────────────────────────────────────────┐
│ Certificate for: www.example.com        │
│                                          │
│ Subject: CN=www.example.com             │
│ Issuer: CN=Intermediate CA              │
│ Valid From: 2024-01-01                  │
│ Valid To: 2025-01-01                    │
│ Public Key: [RSA 2048-bit public key]  │
│ Signature: [Signed by Intermediate CA]  │
│ Serial Number: 0x123abc...              │
│ Extensions:                             │
│   • Subject Alternative Names           │
│   • Key Usage                           │
│   • Extended Key Usage                  │
└──────────────────────────────────────────┘

Verification Chain:
User's Browser
  │
  ├─► Has Root CA certificate (pre-installed)
  │
  ├─► Receives: Server Cert + Intermediate Cert
  │
  ├─► Verify: Server Cert signed by Intermediate?
  │          ✓ Valid
  │
  └─► Verify: Intermediate signed by Root CA?
             ✓ Valid
      
      → Trust established!
```

### Certificate Revocation

What if a certificate is compromised before expiration?

```
Certificate Revocation Methods:

1. CRL (Certificate Revocation List):
┌────────────────────────────────────┐
│  Periodically published list of    │
│  revoked certificate serial numbers│
│                                    │
│  Revoked Certificates:             │
│  • Serial: 0x123abc (Date: 2024..) │
│  • Serial: 0x456def (Date: 2024..) │
│  • Serial: 0x789ghi (Date: 2024..) │
└────────────────────────────────────┘
Problem: List can grow large, delay in updates

2. OCSP (Online Certificate Status Protocol):
Client                    OCSP Responder
  │                             │
  │ "Is cert 0x123abc valid?"   │
  ├────────────────────────────►│
  │                             │
  │ Response:                   │
  │ • Good / Revoked / Unknown  │
  │◄────────────────────────────┤

Problem: Privacy (CA learns what sites you visit)
        Performance (extra round trip)

3. OCSP Stapling:
Server periodically fetches OCSP response
and "staples" it to TLS handshake

Server                    Client
  │                         │
  │ Certificate + OCSP      │
  │ Response (Good)         │
  ├────────────────────────►│
  │                    (Client trusts
  │                     timestamped
  │                     response)

Benefit: No client→CA communication
        Faster, more private
```

### End-to-End Encryption (E2EE)

```
E2EE Architecture (Signal Protocol):

Alice                 Server                 Bob
  │                     │                     │
  │  Generate Key Pair  │  Generate Key Pair  │
  ├──────────┐          │          ┌──────────┤
  │          │          │          │          │
  │  Private │          │          │ Private  │
  │  Public  │          │          │ Public   │
  │          │          │          │          │
  │  Upload Public Key  │  Upload Public Key  │
  ├────────────────────►│◄────────────────────┤
  │                     │                     │
  │  Request Bob's      │                     │
  │  Public Key         │                     │
  ├────────────────────►│                     │
  │  Receive Bob's Pub  │                     │
  │◄────────────────────┤                     │
  │                     │                     │
  │ Compute Shared      │                     │
  │ Secret using:       │                     │
  │ • Alice's Private   │                     │
  │ • Bob's Public      │                     │
  │                     │                     │
  │ Encrypt: "Hello"    │                     │
  │    with Shared Key  │                     │
  ├────────────────────►│                     │
  │  Forward encrypted  │                     │
  │  (Server can't      │                     │
  │   decrypt)          ├────────────────────►│
  │                     │         Compute     │
  │                     │         Shared      │
  │                     │         Secret:     │
  │                     │         • Bob's     │
  │                     │           Private   │
  │                     │         • Alice's   │
  │                     │           Public    │
  │                     │                     │
  │                     │         Decrypt:    │
  │                     │         "Hello"     │

Key Point: Server NEVER has decryption keys
          Even server compromise doesn't expose messages
```

---

## 6. DATA SECURITY & ENCRYPTION

### Data States

Data exists in three states, each requiring different security:

```
Three States of Data:

1. Data at Rest               2. Data in Transit
┌─────────────┐              ┌─────────────┐

# DISTRIBUTED SYSTEMS SECURITY: COMPREHENSIVE GUIDE
## Part 2: Data Security Through Defense Strategies

---

## 6. DATA SECURITY & ENCRYPTION

### 6.1 Understanding Data States

**Concept Foundation**: Before securing data, understand that data exists in three fundamental states, each vulnerable to different attack vectors and requiring distinct protection mechanisms.

```
THREE STATES OF DATA
═══════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│                    1. DATA AT REST                              │
│  (Stored on disk, database, backup, or any storage medium)     │
└─────────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
   ┌─────────┐         ┌─────────┐        ┌─────────┐
   │Database │         │  File   │        │ Backup  │
   │Storage  │         │ System  │        │ Archive │
   └─────────┘         └─────────┘        └─────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   2. DATA IN TRANSIT                            │
│     (Moving across network between systems or services)         │
└─────────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
   ┌─────────┐         ┌─────────┐        ┌─────────┐
   │ Network │         │  API    │        │Inter-DC │
   │ Traffic │         │  Calls  │        │Transfer │
   └─────────┘         └─────────┘        └─────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   3. DATA IN USE                                │
│   (Being actively processed in memory or CPU registers)         │
└─────────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
   ┌─────────┐         ┌─────────┐        ┌─────────┐
   │  RAM    │         │  CPU    │        │ Cache   │
   │ Memory  │         │Register │        │  L1/L2  │
   └─────────┘         └─────────┘        └─────────┘
```

### 6.2 Encryption Fundamentals

**Symmetric Encryption**: Same key for encryption and decryption
- **Use Case**: Fast bulk data encryption (files, databases)
- **Algorithms**: AES-256, ChaCha20
- **Key Challenge**: Secure key distribution

**Asymmetric Encryption**: Public key encrypts, private key decrypts
- **Use Case**: Key exchange, digital signatures, authentication
- **Algorithms**: RSA, ECC (Elliptic Curve Cryptography)
- **Trade-off**: Slower but solves key distribution

```
ENCRYPTION TYPES COMPARISON
═══════════════════════════════════════════════════════════════════

SYMMETRIC ENCRYPTION (Same Key Both Ways)
─────────────────────────────────────────────────────────────
  Plaintext                                    Ciphertext
     │                                              │
     │  ┌──────────┐         ┌──────────┐         │
     └─→│ Encrypt  │────────→│ Decrypt  │─────────┘
        │ with Key │         │ with Key │
        └──────────┘         └──────────┘
             ↑                    ↑
             │                    │
             └────────────────────┘
                  Same Key K

    Speed: FAST (10-100x faster)
    Key Size: 128-256 bits
    Problem: How to share key securely?


ASYMMETRIC ENCRYPTION (Different Keys)
─────────────────────────────────────────────────────────────
  Plaintext                                    Ciphertext
     │                                              │
     │  ┌──────────┐         ┌──────────┐         │
     └─→│ Encrypt  │────────→│ Decrypt  │─────────┘
        │Public Key│         │PrivateKey│
        └──────────┘         └──────────┘
             ↑                    ↑
             │                    │
        Anyone can          Only holder
        use this            can decrypt

    Speed: SLOW (computationally expensive)
    Key Size: 2048-4096 bits (RSA)
    Advantage: No key distribution problem


HYBRID APPROACH (Best of Both Worlds)
─────────────────────────────────────────────────────────────
Step 1: Generate random symmetric key (session key)
Step 2: Encrypt data with symmetric key (FAST)
Step 3: Encrypt session key with receiver's public key
Step 4: Send both encrypted data + encrypted session key

    ┌──────────────┐
    │  Large Data  │
    └──────┬───────┘
           │
           ▼
    ┌─────────────┐    Session Key (K)
    │  AES-256    │◄───────┐
    │  Encrypt    │        │
    └──────┬──────┘        │
           │               │
           ▼               │
    ┌─────────────┐        │
    │  Encrypted  │        │
    │    Data     │        │
    └─────────────┘        │
                           │
                    ┌──────┴──────┐
                    │  RSA Public │
                    │  Key Encrypt│
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Encrypted  │
                    │ Session Key │
                    └─────────────┘

This is what TLS/SSL does!
```

### 6.3 Encryption at Rest

**Definition**: Protecting data stored on physical or virtual storage media.

```
ENCRYPTION AT REST ARCHITECTURE
═══════════════════════════════════════════════════════════════════

                    ┌─────────────────────────┐
                    │   Application Layer     │
                    │  (Plaintext Operations) │
                    └───────────┬─────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │  Encryption Layer       │
                    │  • Transparent          │
                    │  • Application-level    │
                    │  • Field-level          │
                    └───────────┬─────────────┘
                                │
                    ┌───────────┴────────────┐
                    │                        │
                    ▼                        ▼
          ┌─────────────────┐      ┌────────────────┐
          │ File System     │      │   Database     │
          │  Encryption     │      │  Encryption    │
          │  (LUKS, dm-crypt)│     │  (TDE, CLE)   │
          └─────────┬───────┘      └────────┬───────┘
                    │                        │
                    └───────────┬────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │  Physical Storage       │
                    │  (Encrypted at rest)    │
                    │  • HDD/SSD              │
                    │  • Cloud Storage        │
                    │  • Backup Tapes         │
                    └─────────────────────────┘


KEY MANAGEMENT FOR DATA AT REST
─────────────────────────────────────────────────────────────

Hierarchical Key Structure (Industry Standard):

┌──────────────────────────────────────────────────────────┐
│              Master Key (Root Key)                       │
│  • Stored in HSM or Key Management Service              │
│  • Rarely rotated (yearly)                              │
│  • Protected by hardware security                       │
└─────────────────────┬────────────────────────────────────┘
                      │ Encrypts
                      ▼
┌──────────────────────────────────────────────────────────┐
│           Key Encryption Keys (KEK)                      │
│  • Per-service or per-region                            │
│  • Rotated quarterly                                    │
│  • Encrypted by Master Key                              │
└─────────────────────┬────────────────────────────────────┘
                      │ Encrypts
                      ▼
┌──────────────────────────────────────────────────────────┐
│         Data Encryption Keys (DEK)                       │
│  • Per-table, per-file, or per-record                   │
│  • Rotated monthly or on-demand                         │
│  • Encrypted by KEK                                     │
└─────────────────────┬────────────────────────────────────┘
                      │ Encrypts
                      ▼
┌──────────────────────────────────────────────────────────┐
│               Actual Data                                │
│  • User records, files, backups                         │
│  • Encrypted with DEK                                   │
└──────────────────────────────────────────────────────────┘


Why This Hierarchy?
──────────────────
1. Key Rotation: Can rotate DEKs without re-encrypting Master
2. Separation: Compromise of one DEK doesn't expose all data
3. Performance: DEKs cached in memory, Master stays in HSM
4. Compliance: Different keys for different data classifications
```

### 6.4 Encryption in Transit

**Definition**: Protecting data while moving across networks between endpoints.

```
TLS/SSL HANDSHAKE (The Foundation of Transit Security)
═══════════════════════════════════════════════════════════════════

Client                                              Server
  │                                                    │
  │  1. ClientHello                                   │
  │    • Supported cipher suites                      │
  │    • Random nonce                                 │
  │    • TLS version                                  │
  ├──────────────────────────────────────────────────►│
  │                                                    │
  │                       2. ServerHello              │
  │                          • Chosen cipher          │
  │                          • Random nonce           │
  │                          • Server certificate     │
  │◄───────────────────────────────────────────────────┤
  │                                                    │
  │  3. Verify Certificate                            │
  │    • Check CA signature                           │
  │    • Validate domain name                         │
  │    • Check expiration                             │
  │    • Check revocation status                      │
  │                                                    │
  │  4. Key Exchange                                  │
  │    • Generate pre-master secret                   │
  │    • Encrypt with server's public key             │
  ├──────────────────────────────────────────────────►│
  │                                                    │
  │  5. Both derive session keys                      │
  │    from pre-master secret + nonces                │
  │                                                    │
  │  6. ChangeCipherSpec                              │
  │    "All future messages encrypted"                │
  ├──────────────────────────────────────────────────►│
  │                                                    │
  │                       7. ChangeCipherSpec         │
  │◄───────────────────────────────────────────────────┤
  │                                                    │
  │  8. Encrypted Application Data                    │
  │◄──────────────────────────────────────────────────►│
  │                                                    │


TLS 1.3 IMPROVEMENTS (Current Standard)
─────────────────────────────────────────────────────────────

1. Faster Handshake: 1-RTT instead of 2-RTT
2. 0-RTT Resumption: No handshake for returning clients
3. Removed weak ciphers: Only AEAD ciphers allowed
4. Perfect Forward Secrecy: Mandatory in all cipher suites


PERFECT FORWARD SECRECY (PFS) Explained
─────────────────────────────────────────────────────────────

Without PFS:
  If server's private key is compromised in future,
  attacker can decrypt ALL past recorded traffic.

With PFS:
  Each session uses ephemeral (temporary) keys.
  Compromising server key doesn't expose past sessions.

  Session 1: Uses Key A (destroyed after session)
  Session 2: Uses Key B (destroyed after session)
  Session 3: Uses Key C (destroyed after session)
  
  Compromise of server key can't recover Keys A, B, or C!
```

### 6.5 Encryption in Use (Advanced Concepts)

**Challenge**: Data must be decrypted to process it, leaving it vulnerable in memory.

```
DATA IN USE SECURITY APPROACHES
═══════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│  TRADITIONAL APPROACH (Vulnerable)                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Encrypted      Decrypt       Process        Encrypt       │
│    Data    ───►  to RAM  ───► in RAM   ───►  Result       │
│                                                             │
│                     ▲                                       │
│                     │                                       │
│              ┌──────┴──────┐                               │
│              │  VULNERABLE  │                               │
│              │  Memory Dump │                               │
│              │ Cold Boot    │                               │
│              │Side Channel  │                               │
│              └─────────────┘                               │
└─────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────┐
│  HOMOMORPHIC ENCRYPTION (Theoretical Ideal)                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Encrypted      Process         Encrypted                  │
│    Data    ───►  Encrypted  ───►  Result                   │
│                    Data                                     │
│                                                             │
│  Never decrypted! Compute on encrypted data directly.      │
│  Problem: 1000-10000x slower, not practical yet            │
└─────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────┐
│  TRUSTED EXECUTION ENVIRONMENT (TEE) - Practical Solution   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│         Regular OS & Applications                          │
│  ┌─────────────────────────────────────────────┐          │
│  │     Untrusted Environment                   │          │
│  │     • Cannot access TEE memory              │          │
│  │     • Cannot inspect TEE processes          │          │
│  └─────────────────────────────────────────────┘          │
│                       │                                     │
│                       │ API Boundary                        │
│                       │                                     │
│  ┌─────────────────────────────────────────────┐          │
│  │    Trusted Execution Environment (TEE)      │          │
│  │  ┌───────────────────────────────────────┐ │          │
│  │  │  • Hardware-isolated memory (enclave)│ │          │
│  │  │  • Encrypted memory by CPU           │ │          │
│  │  │  • Attestation: Prove code integrity │ │          │
│  │  │  • Secure key storage                │ │          │
│  │  └───────────────────────────────────────┘ │          │
│  │                                             │          │
│  │  Technologies:                              │          │
│  │  • Intel SGX (Software Guard Extensions)   │          │
│  │  • AMD SEV (Secure Encrypted Virtualization)│         │
│  │  • ARM TrustZone                            │          │
│  └─────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘


SECURE ENCLAVE WORKFLOW
─────────────────────────────────────────────────────────────

1. Enclave Creation
   ┌─────────────┐
   │ Application │
   └──────┬──────┘
          │ Creates
          ▼
   ┌─────────────┐
   │   Enclave   │ ← CPU ensures memory is encrypted
   └─────────────┘    and isolated from OS/hypervisor

2. Remote Attestation
   ┌─────────────┐          ┌─────────────┐
   │   Enclave   │─────────►│   Remote    │
   │             │  Proof   │   Server    │
   └─────────────┘          └─────────────┘
   
   "I'm running authentic code X in secure hardware Y"
   Server verifies cryptographic proof before sending data

3. Secure Processing
   Encrypted Data ──► Enclave ──► Encrypted Result
                      (Decrypts, processes, encrypts
                       all within protected memory)
```

### 6.6 Key Management Strategies

**Key Management Service (KMS)**: Centralized system for cryptographic key lifecycle.

```
KEY LIFECYCLE MANAGEMENT
═══════════════════════════════════════════════════════════════════

┌──────────────────────────────────────────────────────────────┐
│                    KEY LIFECYCLE STAGES                      │
└──────────────────────────────────────────────────────────────┘

  1. GENERATION          2. DISTRIBUTION       3. STORAGE
  ─────────────         ────────────────       ──────────
  ┌───────────┐         ┌────────────┐        ┌────────┐
  │  Create   │────────►│  Secure    │───────►│  HSM   │
  │  Random   │         │  Channel   │        │  Vault │
  │   Key     │         │  (TLS)     │        └────────┘
  └───────────┘         └────────────┘             │
       │                                            │
       │                                            │
       ▼                                            ▼
  Must be truly random         4. USAGE        5. ROTATION
  (CSPRNG - Cryptographically  ──────────      ────────────
   Secure Pseudo-Random        ┌────────┐     ┌──────────┐
   Number Generator)           │Encrypt/│────►│ Generate │
                               │Decrypt │     │ New Key  │
                               └────────┘     └──────────┘
                                    │              │
                                    │              ▼
                                    │         Re-encrypt
                                    │         data or use
                                    │         envelope method
                                    ▼
                            6. REVOCATION    7. DESTRUCTION
                            ────────────     ──────────────
                            ┌──────────┐    ┌───────────┐
                            │Mark as   │───►│Securely   │
                            │Invalid   │    │Wipe       │
                            └──────────┘    └───────────┘


KEY ROTATION STRATEGIES
─────────────────────────────────────────────────────────────

Strategy 1: Re-encryption (Expensive but Simple)
────────────────────────────────────────────────
  Old Data          New Data
  ┌────────┐        ┌────────┐
  │ Enc(K1)│───────►│ Enc(K2)│
  └────────┘ Decrypt└────────┘
              then
           Re-encrypt

  • Decrypt all data with K1
  • Re-encrypt all data with K2
  • Problem: Expensive for large datasets


Strategy 2: Envelope Encryption (Industry Standard)
────────────────────────────────────────────────────
  Data encrypted with DEK (never changes)
  DEK encrypted with KEK (rotated)

  Before Rotation:
    Data ← DEK ← KEK_v1

  After Rotation:
    Data ← DEK ← KEK_v2
    
  • Only re-encrypt small DEK, not entire data
  • Fast, efficient, scalable


Strategy 3: Versioning (Support Both Keys During Transition)
─────────────────────────────────────────────────────────────
  Grace Period: Both K1 and K2 valid
  
  Phase 1: K1 primary, generate new data with K2
  Phase 2: Both K1 and K2 valid (reading)
  Phase 3: All new writes use K2
  Phase 4: Background job migrates K1→K2
  Phase 5: Retire K1
```

### 6.7 Data Classification & Protection

**Principle**: Not all data requires the same level of protection. Classification drives security controls.

```
DATA CLASSIFICATION FRAMEWORK
═══════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│  Level 1: PUBLIC                                            │
│  ────────────────────────────────────────────────────────── │
│  • Marketing materials, press releases                      │
│  • Public documentation                                     │
│  Security: None required                                    │
│  Encryption: Optional                                       │
└─────────────────────────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Level 2: INTERNAL                                          │
│  ────────────────────────────────────────────────────────── │
│  • Internal communications, company directory               │
│  • General business documents                               │
│  Security: Access control, basic authentication            │
│  Encryption: TLS in transit, at rest recommended            │
└─────────────────────────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Level 3: CONFIDENTIAL                                      │
│  ────────────────────────────────────────────────────────── │
│  • Customer data, business strategies                       │
│  • Financial records, employee information                  │
│  Security: Strong authentication, audit logging             │
│  Encryption: Mandatory at rest & in transit                 │
│  Access: Need-to-know basis, MFA required                   │
└─────────────────────────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Level 4: RESTRICTED (Highly Sensitive)                     │
│  ────────────────────────────────────────────────────────── │
│  • Payment card data (PCI-DSS)                              │
│  • Health records (HIPAA/PHI)                               │
│  • Secrets, keys, credentials                               │
│  Security: Highest-grade encryption, HSM storage            │
│  Encryption: Field-level + envelope encryption              │
│  Access: Minimal privilege, frequent audits                 │
│  Monitoring: Real-time alerting, anomaly detection          │
└─────────────────────────────────────────────────────────────┘


FIELD-LEVEL ENCRYPTION (For Sensitive Fields)
─────────────────────────────────────────────────────────────

Database Record:
┌────────────────────────────────────────────────────────┐
│ User ID: 12345                  (plaintext, indexed)   │
│ Name: "John Doe"                (plaintext, searchable)│
│ Email: "john@example.com"       (plaintext)           │
│ SSN: "Enc(537-12-8934)"        (ENCRYPTED)           │
│ Credit Card: "Enc(4532...)"    (ENCRYPTED)           │
│ Created: 2024-01-15             (plaintext)           │
└────────────────────────────────────────────────────────┘

Benefits:
• Only sensitive fields encrypted (performance)
• Can still query by name, email
• Even DBA can't see SSN or credit card
• Granular key management per field type
```

---

## 7. NETWORK SECURITY ARCHITECTURE

### 7.1 Network Segmentation & Isolation

**Principle**: Divide network into isolated segments to contain breaches and control traffic flow.

```
NETWORK SEGMENTATION ARCHITECTURE
═══════════════════════════════════════════════════════════════════

                        Internet
                           │
                           ▼
                ┌──────────────────┐
                │  Edge Firewall   │
                │  • DDoS Protection│
                │  • WAF           │
                └────────┬─────────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │     DMZ (Demilitarized Zone)   │
        │  ┌──────────┐  ┌──────────┐   │
        │  │   Proxy  │  │   LB     │   │
        │  │  Servers │  │ (Load    │   │
        │  └──────────┘  │ Balancer)│   │
        │                └──────────┘   │
        └────────────┬───────────────────┘
                     │
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
    ┌──────────┐          ┌──────────┐
    │Internal  │          │ Internal │
    │Firewall 1│          │Firewall 2│
    └────┬─────┘          └────┬─────┘
         │                     │
         ▼                     ▼
  ┌─────────────┐      ┌─────────────┐
  │Application  │      │  Database   │
  │   Tier      │      │    Tier     │
  │ ┌─────────┐ │      │ ┌─────────┐ │
  │ │API Srvr │ │      │ │Primary  │ │
  │ │Web Srvr │ │◄────►│ │ DB      │ │
  │ │App Srvr │ │      │ │Replica  │ │
  │ └─────────┘ │      │ └─────────┘ │
  └─────────────┘      └─────────────┘
         │                     │
         └──────────┬──────────┘
                    │
                    ▼
            ┌───────────────┐
            │ Management    │
            │    Tier       │
            │ • Monitoring  │
            │ • Logging     │
            │ • Admin Access│
            └───────────────┘


ZONE-BASED SECURITY POLICY
─────────────────────────────────────────────────────────────

Rule: Default DENY, explicitly ALLOW required traffic

  Internet → DMZ:      HTTPS (443), HTTP (80)
  DMZ → App Tier:      HTTPS (443), gRPC (custom)
  App → Database:      PostgreSQL (5432), MySQL (3306)
  Management → All:    SSH (22), HTTPS (443)
  All → Management:    Logs (514), Metrics (custom)

Firewall Rules (Simplified):
┌──────────────┬─────────┬──────────┬──────┬─────────┐
│   Source     │  Dest   │   Port   │ Proto│ Action  │
├──────────────┼─────────┼──────────┼──────┼─────────┤
│ Internet     │ DMZ     │ 443      │ TCP  │ ALLOW   │
│ DMZ          │ App     │ 8080     │ TCP  │ ALLOW   │
│ App          │ DB      │ 5432     │ TCP  │ ALLOW   │
│ Any          │ Any     │ Any      │ Any  │ DENY    │
└──────────────┴─────────┴──────────┴──────┴─────────┘
```

### 7.2 Zero Trust Network Architecture

**Core Principle**: "Never trust, always verify" - Don't trust network location as security perimeter.

```
TRADITIONAL PERIMETER vs ZERO TRUST
═══════════════════════════════════════════════════════════════════

TRADITIONAL PERIMETER MODEL (Castle & Moat)
─────────────────────────────────────────────────────────────
              Firewall (Perimeter)
     ┌────────────────────────────────────┐
     │                                    │
     │    Inside = Trusted                │
     │  ┌──────┐  ┌──────┐  ┌──────┐    │
     │  │Server│◄─►│Server│◄─►│Server│   │
     │  └──────┘  └──────┘  └──────┘    │
     │    No authentication between      │
     │    internal systems               │
     └────────────────────────────────────┘
                    ▲
                    │
           Problem: Lateral movement!
           Once inside, attacker has
           broad access


ZERO TRUST MODEL
─────────────────────────────────────────────────────────────
     No implicit trust anywhere

     ┌──────┐       ┌──────┐       ┌──────┐
     │Server│       │Server│       │Server│
     │  A   │       │  B   │       │  C   │
     └───┬──┘       └───┬──┘       └───┬──┘
         │              │              │
         └──────┬───────┴───────┬──────┘
                │               │
                ▼               ▼
         ┌─────────────┐ ┌─────────────┐
         │  Identity   │ │   Policy    │
         │  Provider   │ │   Engine    │
         │  (mTLS,     │ │  (Decision  │
         │   JWT)      │ │   Point)    │
         └─────────────┘ └─────────────┘

     Every request:
     1. Authenticate identity
     2. Authorize based on policy
     3. Encrypt communication
     4. Audit the transaction


ZERO TRUST PRINCIPLES
─────────────────────────────────────────────────────────────

1. VERIFY EXPLICITLY
   ────────────────
   • Authenticate & authorize based on:
     - User identity
     - Device health
     - Location
     - Time of day
     - Risk score

2. LEAST PRIVILEGE ACCESS
   ───────────────────────
   • Just-in-time access
   • Just-enough access
   • Risk-based adaptive policies

3. ASSUME BREACH
   ─────────────
   • Segment access
   • Verify end-to-end encryption
   • Use analytics for threat detection
   • Automate threat response


IMPLEMENTATION ARCHITECTURE
─────────────────────────────────────────────────────────────

                     User/Service Request
                            │
                            ▼
                ┌───────────────────────┐
                │   Policy Engine       │
                │  • Who? (Identity)    │
                │  • What? (Resource)   │
                │  • When? (Time/Loc)   │
                │  • How? (Device)      │
                │  • Risk Score         │
                └──────────┬────────────┘
                           │
                   ┌───────┴───────┐
                   │               │
                ALLOW?           DENY
                   │               │
                   ▼               ▼
            ┌─────────────┐  ┌────────┐
            │  Grant      │  │  Block │
            │  Token      │  │  & Log │
            └──────┬──────┘  └────────┘
                   │
                   ▼
            ┌─────────────┐
            │  Resource   │
            │  Access     │
            └─────────────┘
                   │
                   ▼
            ┌─────────────┐
            │  Continuous │
            │  Monitoring │
            │  & Audit    │
            └─────────────┘
```

### 7.3 Service Mesh Security

**Definition**: Infrastructure layer for handling service-to-service communication with built-in security, observability, and reliability features.

```
SERVICE MESH ARCHITECTURE
═══════════════════════════════════════════════════════════════════

WITHOUT SERVICE MESH (Point-to-Point)
─────────────────────────────────────────────────────────────
  Service A                Service B
  ┌───────────┐           ┌───────────┐
  │           │           │           │
  │  ┌─────┐  │──────────►│  ┌─────┐  │
  │  │Logic│  │ HTTP/gRPC │  │Logic│  │
  │  └──┬──┘  │           │  └──┬──┘  │
  │     │     │           │     │     │
  │  ┌──▼──┐  │           │  ┌──▼──┐  │
  │  │Auth │  │           │  │Auth │  │
  │  │Retry│  │           │  │Retry│  │
  │  │Enc  │  │           │  │Enc  │  │
  │  │Trace│  │           │  │Trace│  │
  │  └─────┘  │           │  └─────┘  │
  └───────────┘           └───────────┘
  
  Problem: Security logic duplicated in every service!


WITH SERVICE MESH (Sidecar Pattern)
─────────────────────────────────────────────────────────────

Control Plane (Brain)
┌─────────────────────────────────────────────────────┐
│  • Certificate Authority                            │
│  • Policy Management                                │
│  • Service Discovery                                │
│  • Telemetry Collection                             │
└────────┬────────────────────────────┬───────────────┘
         │                            │
         ▼                            ▼
    Service A Pod              Service B Pod
┌─────────────────────┐   ┌─────────────────────┐
│ ┌─────────────────┐ │   │ ┌─────────────────┐ │
│ │  Application    │ │   │ │  Application    │ │
│ │    Logic        │ │   │ │    Logic        │ │
│ └────────┬────────┘ │   │ └────────┬────────┘ │
│          │          │   │          │          │
│   localhost:8080   │   │   localhost:8080   │
│          │          │   │          │          │
│ ┌────────▼────────┐ │   │ ┌────────▼────────┐ │
│ │  Sidecar Proxy  │◄├───┤►│  Sidecar Proxy  │ │
│ │  (Envoy)        │ │mTLS│ │  (Envoy)        │ │
│ │  • Intercepts   │ │   │ │  • Mutual TLS   │ │
│ │  • Encrypts     │ │   │ │  • Auth checks  │ │
│ │  • Retries      │ │   │ │  • Metrics      │ │
│ │  • Metrics      │ │   │ │  • Tracing      │ │
│ └─────────────────┘ │   │ └─────────────────┘ │
└─────────────────────┘   └─────────────────────┘

Benefits:
• Security decoupled from application code
• Automatic mTLS between all services
• Centralized policy enforcement
• Zero-trust by default


MUTUAL TLS (mTLS) IN SERVICE MESH
─────────────────────────────────────────────────────────────

Step 1: Certificate Issuance
────────────────────────────
       Control Plane CA
              │
        ┌─────┴─────┐
        │           │
        ▼           ▼
    Cert for A   Cert for B
    (TTL: 1hr)   (TTL: 1hr)

Step 2: Automatic Rotation
────────────────────────────
    Before expiry, sidecars
    automatically request new
    certificates from CA

Step 3: Connection Establishment
─────────────────────────────────
  Service A Sidecar         Service B Sidecar
        │                          │
        │  1. Client Hello         │
        │  (with Cert A)           │
        ├─────────────────────────►│
        │                          │
        │  2. Server Hello         │
        │  (with Cert B)           │
        │◄─────────────────────────┤
        │                          │
        │  3. Both verify certs    │
        │     against CA           │
        │                          │
        │  4. Encrypted channel    │
        │◄────────────────────────►│
        

POLICY ENFORCEMENT EXAMPLE
─────────────────────────────────────────────────────────────

Policy: "Only 'frontend' can call 'payment-service'"

┌─────────────────────────────────────────────────────┐
│  apiVersion: security.istio.io/v1                   │
│  kind: AuthorizationPolicy                          │
│  metadata:                                          │
│    name: payment-authz                              │
│    namespace: production                            │
│  spec:                                              │
│    selector:                                        │
│      matchLabels:                                   │
│        app: payment-service                         │
│    rules:                                           │
│    - from:                                          │
│      - source:                                      │
│          principals:                                │
│          - "cluster.local/ns/prod/sa/frontend"     │
│      to:                                            │
│      - operation:                                   │
│          methods: ["POST", "GET"]                   │
│          paths: ["/api/payment/*"]                  │
└─────────────────────────────────────────────────────┘

Control plane pushes this policy to all sidecars.
Sidecar proxies enforce at runtime.
```

### 7.4 DDoS Protection Layers

**Distributed Denial of Service**: Overwhelming a system with traffic to make it unavailable.

```
MULTI-LAYER DDoS DEFENSE
═══════════════════════════════════════════════════════════════════

                        Attack Traffic
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1: NETWORK EDGE                                      │
│  ────────────────────────────────────────────────────────   │
│  • BGP Anycast Routing (Traffic distributed globally)       │
│  • Scrubbing Centers (Cloud providers: AWS Shield,          │
│    Cloudflare, Akamai)                                      │
│  • SYN Cookies (Mitigate SYN flood)                         │
│                                                             │
│  Blocks: Volumetric attacks (100+ Gbps)                    │
└──────────────────────┬──────────────────────────────────────┘
                       │ Clean traffic
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 2: FIREWALL / WAF                                    │
│  ────────────────────────────────────────────────────────   │
│  • Rate Limiting (requests per IP)                          │
│  • Geo-blocking (Block regions)                             │
│  • Protocol validation (Malformed packets)                  │
│  • Pattern matching (Known attack signatures)               │
│                                                             │
│  Blocks: Protocol attacks (SYN flood, UDP flood)           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 3: APPLICATION LOAD BALANCER                         │
│  ────────────────────────────────────────────────────────   │
│  • Health checks (Remove unhealthy backends)                │
│  • Connection draining                                      │
│  • Auto-scaling (Add capacity under load)                   │
│  • Queue management (Backpressure)                          │
│                                                             │
│  Mitigates: Sudden traffic spikes                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 4: APPLICATION LAYER                                 │
│  ────────────────────────────────────────────────────────   │
│  • CAPTCHA challenges (Bot detection)                       │
│  • JavaScript challenges                                    │
│  • Request prioritization (Authenticated users first)       │
│  • Circuit breakers (Fail fast on overload)                 │
│  • Resource quotas (Per-user limits)                        │
│                                                             │
│  Blocks: Application-layer attacks (Slowloris, HTTP flood) │
└─────────────────────────────────────────────────────────────┘


COMMON DDoS ATTACK TYPES & DEFENSES
─────────────────────────────────────────────────────────────

1. VOLUMETRIC ATTACKS (Overwhelm bandwidth)
   ────────────────────────────────────────
   Type: UDP Flood, ICMP Flood, DNS Amplification
   
   Attack Flow:
   Attacker → Amplification Servers → Victim
              (DNS, NTP, Memcached)
              
   Small request (60 bytes) → Large response (3000 bytes)
   Amplification factor: 50x
   
   Defense:
   • Anycast routing (Distribute load globally)
   • Scrubbing centers (Filter at ISP level)
   • BGP blackhole routing (Drop traffic upstream)

2. PROTOCOL ATTACKS (Exhaust connection state)
   ───────────────────────────────────────────
   Type: SYN Flood, Ping of Death, Smurf Attack
   
   SYN Flood Explained:
   Attacker               Victim
      │  SYN (spoofed IP)    │
      ├────────────────────► │ Allocates connection
      │                      │ Waits for ACK...
      │  (never sends ACK)   │ Connection times out
      │                      │ Repeat 100,000x
      
      Result: Connection table full, legitimate users rejected
   
   Defense:
   • SYN cookies (Stateless connection tracking)
   • Connection timeouts (Aggressive cleanup)
   • Rate limiting per IP

3. APPLICATION LAYER ATTACKS (Exploit app logic)
   ─────────────────────────────────────────────
   Type: HTTP Flood, Slowloris, Low-and-Slow
   
   Slowloris Attack:
   Attacker opens many connections, sends partial HTTP requests
   very slowly to keep connections alive, exhausting server threads
   
   GET / HTTP/1.1
   Host: victim.com
   [wait 10 seconds]
   X-Custom: header1
   [wait 10 seconds]
   X-Custom: header2
   [never completes request]
   
   Defense:
   • Request timeouts (Kill slow connections)
   • Connection limits per IP
   • Web Application Firewall (Detect patterns)
   • Rate limiting at application layer


RATE LIMITING STRATEGIES
─────────────────────────────────────────────────────────────

Token Bucket Algorithm (Industry Standard)
───────────────────────────────────────────

  Bucket Capacity: 100 tokens
  Refill Rate: 10 tokens/second
  
  ┌─────────────────────┐
  │   Token Bucket      │
  │  ┌───────────────┐  │  Refill: +10/sec
  │  │ ●●●●●●●●●●    │  │◄─────────────────
  │  │ ●●●●●●        │  │
  │  │ (60 tokens)   │  │
  │  └───────────────┘  │
  └─────────────────────┘
           │
           │ Each request consumes 1 token
           ▼
      ┌─────────┐
      │ Request │ ─► ALLOWED (tokens available)
      └─────────┘    or DENIED (bucket empty)

  Benefits:
  • Allows burst traffic (up to capacity)
  • Smooth rate limiting over time
  • Simple to implement

Sliding Window Counter
──────────────────────
  Track requests in fixed time windows

  Time:    10:00:00  10:00:01  10:00:02  10:00:03
  Requests:   50        30        40        20
  
  Limit: 100 requests per minute
  
  Current window (last 60 seconds):
  Sum = 50 + 30 + 40 + 20 = 140 → RATE LIMITED!
```

---

## 8. CONSENSUS & BYZANTINE FAULT TOLERANCE

### 8.1 Understanding Consensus

**Definition**: Agreement among distributed nodes on a single value or state, even in the presence of failures.

**Why Hard?**: Networks are unreliable, nodes can fail, messages can be lost/delayed/duplicated.

```
THE CONSENSUS PROBLEM
═══════════════════════════════════════════════════════════════════

Scenario: 5 nodes must agree on a value
─────────────────────────────────────────────────────────────

Node A proposes: "commit transaction X"

  Node A                  Network              Node B
    │                       │                    │
    │─── Proposal: X ──────►│────────────────────│ ✓ Received
    │                       │                    │
    │                       │─────X──────────────│ × Message lost!
    │                       │                    │
    │                       │                  Node C
    │                       │                    │
    │─── Proposal: X ──────►│────────────────────│ ✓ Received
    │                       │                    │
    │                       │                  Node D
    │                       │────────────────────│ ✓ Received (delayed)
    │                       │                    │
                          Node E
                            │  (crashed)

Question: How do we guarantee all working nodes agree?


CONSENSUS REQUIREMENTS (FLP Impossibility Result)
─────────────────────────────────────────────────────────────

Fischer-Lynch-Paterson Theorem (1985):
"No deterministic consensus protocol can guarantee termination
in an asynchronous system with even one faulty process."

Translation: Perfect consensus is impossible in real-world
distributed systems!

Requirements (Pick 2 out of 3):
┌────────────────────────────────────────────────────────┐
│  1. SAFETY (Correctness)                               │
│     All nodes that decide, decide the same value       │
│     Never decide wrong value                           │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│  2. LIVENESS (Progress)                                │
│     Eventually, nodes will decide                      │
│     System doesn't hang forever                        │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│  3. ASYNCHRONY (No timing assumptions)                 │
│     No bounds on message delays                        │
│     No bounds on process speeds                        │
└────────────────────────────────────────────────────────┘

Practical consensus algorithms sacrifice perfect asynchrony
(use timeouts) to achieve safety + liveness.
```

### 8.2 Crash Fault Tolerance vs Byzantine Fault Tolerance

**Crash Faults**: Nodes simply stop working (fail-stop).
**Byzantine Faults**: Nodes behave arbitrarily/maliciously.

```
FAULT TYPES COMPARISON
═══════════════════════════════════════════════════════════════════

CRASH FAULT TOLERANCE (CFT)
─────────────────────────────────────────────────────────────
Assumption: Nodes are honest but may crash

  Working Node: ✓ Sends correct messages, follows protocol
  Crashed Node: × Stops responding, no messages sent