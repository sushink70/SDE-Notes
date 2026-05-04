# Authentication & Directory Protocols: Kerberos vs LDAP vs SAML vs NTLM

> Before diving in, let's build the **mental model foundation** — because these protocols solve *different problems* in the identity ecosystem.

---

## 🧠 Mental Model: The "Who Are You?" Stack

Think of identity management like a **3-layer problem**:

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 3 — FEDERATION (Cross-org trust)   →   SAML          │
│  "I trust Google that you are who you say you are"          │
├─────────────────────────────────────────────────────────────┤
│  LAYER 2 — AUTHENTICATION (Proving identity) → Kerberos,   │
│            NTLM                                              │
│  "Prove to me you are Alice"                                │
├─────────────────────────────────────────────────────────────┤
│  LAYER 1 — DIRECTORY (Storing identity data)  → LDAP        │
│  "Here is where Alice's data lives"                         │
└─────────────────────────────────────────────────────────────┘
```

**Critical insight:** These are NOT competing technologies. They are **complementary layers** of an identity system. Kerberos *uses* LDAP to look up users. SAML *trusts* Kerberos to authenticate first.

---

## 📖 Glossary (Essential Terms)

| Term | Plain Meaning |
|------|--------------|
| **Authentication (AuthN)** | *Who are you?* — Proving identity |
| **Authorization (AuthZ)** | *What can you do?* — Permissions |
| **Principal** | Any entity that can be authenticated (user, machine, service) |
| **Ticket** | A cryptographic token proving you already authenticated |
| **Token** | A signed data package asserting claims about identity |
| **Realm** | A Kerberos administrative domain (like a company boundary) |
| **Assertion** | A signed statement: "This user has property X" |
| **Bind** | LDAP term for "logging in / connecting" |
| **Distinguished Name (DN)** | Unique address of an entry in LDAP directory |
| **SSO** | Single Sign-On — Login once, access many services |
| **Federation** | Trust between two separate identity systems |
| **Challenge-Response** | A security protocol: "I'll give you a puzzle, solve it to prove you know the secret" |

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 1. LDAP — Lightweight Directory Access Protocol

### What is a "Directory"?

A **directory** is a **specialized database optimized for reads**, storing hierarchical information about users, groups, computers, and resources. Think of it like a phone book — you look things up far more than you write.

```
LDAP Tree Structure (like a file system hierarchy):

dc=company,dc=com              ← Root (Domain Component)
│
├── ou=Users                   ← Organizational Unit
│   ├── cn=Alice               ← Common Name (leaf entry)
│   │   ├── mail: alice@co.com
│   │   ├── uid: alice
│   │   └── userPassword: {hash}
│   └── cn=Bob
│
├── ou=Groups
│   └── cn=Engineering
│       └── member: cn=Alice,ou=Users,dc=company,dc=com
│
└── ou=Computers
    └── cn=WebServer01
```

### LDAP Flow

```
CLIENT                        LDAP SERVER
  │                               │
  │──── TCP Connect (port 389) ──►│
  │                               │
  │──── BIND Request ────────────►│  ← "Login" with DN + password
  │                               │
  │◄─── BIND Response (success) ──│
  │                               │
  │──── SEARCH Request ──────────►│  ← "Find all users in Engineering"
  │     (base DN, filter, attrs)  │
  │                               │
  │◄─── SEARCH Entries ───────────│  ← Returns matching entries
  │◄─── SEARCH Done ──────────────│
  │                               │
  │──── UNBIND ──────────────────►│  ← "Logout"
  │                               │
```

### Key Facts
- **Protocol type:** Directory access protocol (not purely authentication)
- **Port:** 389 (plain), 636 (LDAPS — encrypted)
- **Data format:** Attributes and values in a tree
- **Used for:** Storing and querying user data
- **Does NOT:** Handle tickets, tokens, federation
- **Standard:** RFC 4511

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 2. NTLM — NT LAN Manager

### What is NTLM?

NTLM is Microsoft's **challenge-response authentication protocol** — a legacy system. Before Kerberos became standard, Windows used NTLM to authenticate users on a local network.

### Key Concept: Challenge-Response

```
The core idea:
"I won't send your password over the wire.
 Instead, I'll send you a random puzzle.
 Solve it using your password as the key.
 Only someone who knows the password can solve it correctly."
```

### NTLM Authentication Flow

```
CLIENT                    SERVER                   DOMAIN CONTROLLER
  │                          │                            │
  │── NEGOTIATE Message ────►│   ← "I speak NTLM"        │
  │                          │                            │
  │◄─ CHALLENGE Message ─────│   ← "Here's a random      │
  │   (8-byte nonce/random)  │      challenge string"     │
  │                          │                            │
  │  [Client hashes password │                            │
  │   + challenge together]  │                            │
  │                          │                            │
  │── AUTHENTICATE Message ──►│  ← "Here's my response"  │
  │   (username + response)  │                            │
  │                          │──── Pass to DC ───────────►│
  │                          │                            │ [DC verifies]
  │                          │◄─── Accept/Reject ─────────│
  │                          │                            │
  │◄─ Success / Failure ─────│                            │
```

### NTLM Weaknesses (Critical to Know)

```
ATTACK VECTOR          DESCRIPTION
─────────────────────────────────────────────────────────
Pass-the-Hash        Attacker captures hash, replays it without
                     knowing the actual password

NTLM Relay           Attacker sits in the middle, relays your
                     auth to another server, gains access

Brute-forceable      NTLMv1 hashes are weak, crackable offline

No mutual auth       Server never proves its identity to client
(NTLMv1)             → Man-in-the-Middle possible
```

### NTLM Versions

```
NTLMv1  →  Broken. Use only for ancient legacy.
NTLMv2  →  Much stronger. Challenge includes timestamp + client nonce.
            Still inferior to Kerberos.
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 3. KERBEROS — The Three-Headed Guard Dog

### What is Kerberos?

Named after the mythological **three-headed dog** guarding Hades, Kerberos is a **ticket-based authentication protocol**. The three "heads" represent: Client, Server, and Key Distribution Center (KDC).

### Core Mental Model: The Theme Park Ticket System

```
WITHOUT KERBEROS (naive approach):
  Every ride → You show your passport → Ride operator calls HQ to verify
  Problem: Slow. HQ gets hammered. Password goes everywhere.

WITH KERBEROS:
  Gate entry → Show passport once → Get wristband (TGT)
  Each ride  → Show wristband    → Get ride-specific ticket (Service Ticket)
  Ride       → Show ride ticket  → No need to show passport again

Your password NEVER travels across the network after initial login.
```

### Key Components

```
┌────────────────────────────────────────────────────────────┐
│                 KDC — Key Distribution Center              │
│                                                            │
│  ┌──────────────────┐    ┌───────────────────────────┐    │
│  │  AS               │    │  TGS                      │    │
│  │  Authentication   │    │  Ticket Granting Service  │    │
│  │  Service          │    │                           │    │
│  │                   │    │  Issues service tickets   │    │
│  │  Issues TGT       │    │  when you show TGT        │    │
│  └──────────────────┘    └───────────────────────────┘    │
│                                                            │
│  Also holds: Database of all users + their secret keys    │
└────────────────────────────────────────────────────────────┘

TGT  = Ticket Granting Ticket  → Master pass (valid 8-10 hours)
ST   = Service Ticket          → Access pass for one specific service
```

### Full Kerberos Flow (Step by Step)

```
CLIENT              AS (Auth Svc)        TGS                  SERVICE
  │                      │                │                       │
  │                      │                │                       │
  │ [Step 1: Pre-auth]   │                │                       │
  │── AS-REQ ───────────►│                │                       │
  │  (username,          │                │                       │
  │   timestamp enc      │                │                       │
  │   with user key)     │                │                       │
  │                      │ [Verify user]  │                       │
  │                      │ [Check LDAP]   │                       │
  │                      │                │                       │
  │◄─ AS-REP ────────────│                │                       │
  │  (TGT encrypted with │                │                       │
  │   KDC secret key +   │                │                       │
  │   Session Key enc    │                │                       │
  │   with user key)     │                │                       │
  │                      │                │                       │
  │  [Client decrypts    │                │                       │
  │   session key with   │                │                       │
  │   own password]      │                │                       │
  │                      │                │                       │
  │ [Step 2: Get Service Ticket]          │                       │
  │── TGS-REQ ──────────────────────────►│                       │
  │  (TGT + Authenticator enc            │                       │
  │   with session key +                 │                       │
  │   target service name)               │                       │
  │                      │               │ [Verify TGT]          │
  │                      │               │ [Check permissions]   │
  │◄─ TGS-REP ───────────────────────────│                       │
  │  (Service Ticket enc with            │                       │
  │   service's secret key +             │                       │
  │   new session key enc with           │                       │
  │   client session key)                │                       │
  │                      │               │                       │
  │ [Step 3: Access Service]             │                       │
  │── AP-REQ ─────────────────────────────────────────────────►│
  │  (Service Ticket +                                          │
  │   Authenticator enc with new session key)                   │
  │                      │               │  [Decrypt ticket]    │
  │                      │               │  [Verify timestamp]  │
  │◄─ AP-REP ─────────────────────────────────────────────────│
  │  (Timestamp enc — proves server identity — MUTUAL AUTH)     │
  │                      │               │                       │
  │  ✅ ACCESS GRANTED                                           │
```

### Kerberos Security Properties

```
PROPERTY              HOW ACHIEVED
──────────────────────────────────────────────────────────────
Password never sent   Only cryptographic proofs travel the wire
Mutual authentication Server proves identity too (AP-REP step)
Time-limited tickets  TGT expires (replay attacks bounded)
No central bottleneck After TGT, KDC not involved per-request
Replay protection     Timestamps + sequence numbers in authenticator
```

### Kerberos Attacks to Know

```
ATTACK              DESCRIPTION
────────────────────────────────────────────────────────
Kerberoasting       Request service ticket for any SPN,
                    brute-force offline (service account risk)

Pass-the-Ticket     Steal TGT from memory, use on another machine

Golden Ticket       Forge TGT using stolen KDC secret (krbtgt hash)
                    → Total domain compromise, valid 10 years

Silver Ticket       Forge Service Ticket using stolen service key
                    → Access to specific service, no KDC involved

AS-REP Roasting     Attack accounts with pre-auth disabled,
                    crack their hash offline
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 4. SAML — Security Assertion Markup Language

### What is SAML?

SAML is an **XML-based federation protocol** for Single Sign-On across **organizational boundaries**. While Kerberos handles auth within one company's network, SAML handles: *"Company A trusts Company B's authentication."*

### New Vocabulary for SAML

```
TERM                  MEANING
────────────────────────────────────────────────────────────────
Identity Provider     The party that AUTHENTICATES the user
(IdP)                 Example: Google, Okta, Active Directory FS

Service Provider      The application/resource the user wants
(SP)                  Example: Salesforce, GitHub, your web app

Assertion             A signed XML document saying "This user
                      has these attributes and logged in at X time"

Metadata              XML document describing an IdP or SP's
                      capabilities and public keys

ACS URL               Assertion Consumer Service URL —
                      where the SP receives SAML assertions
```

### SAML Trust Model

```
Before SAML flow begins, a one-time setup occurs:

IdP                                SP
 │                                  │
 │◄──── Exchange Metadata ─────────►│
 │  (Public keys, endpoints,        │
 │   supported bindings)            │
 │                                  │
 │  Now they trust each other's     │
 │  digital signatures              │
```

### SAML SP-Initiated Flow (Most Common)

```
BROWSER              SERVICE PROVIDER (SP)         IDENTITY PROVIDER (IdP)
   │                        │                               │
   │── Access Resource ────►│                               │
   │   (not logged in)      │                               │
   │                        │ [Generate SAML Request]       │
   │◄── Redirect ───────────│                               │
   │    (to IdP with        │                               │
   │     AuthnRequest)      │                               │
   │                        │                               │
   │── AuthnRequest ────────────────────────────────────►  │
   │                                                        │
   │◄── Login Page ─────────────────────────────────────── │
   │                                                        │
   │── Credentials ─────────────────────────────────────►  │
   │   (username/password                                   │
   │    or MFA)                                             │
   │                        │  [IdP creates signed          │
   │                        │   XML Assertion]              │
   │                        │                               │
   │◄── HTML form (auto-submit) ◄────────────────────────── │
   │    with SAML Response  │                               │
   │    (Base64 encoded XML) │                               │
   │                        │                               │
   │── POST SAML Response ─►│                               │
   │   (to ACS URL)         │                               │
   │                        │ [Verify XML signature]        │
   │                        │ [Check assertion validity]    │
   │                        │ [Extract user attributes]     │
   │                        │                               │
   │◄── Access Granted ─────│                               │
   │    (session cookie)    │                               │
```

### SAML Assertion Structure (Simplified)

```xml
<SAMLAssertion>
  <Issuer>https://idp.google.com</Issuer>
  <Subject>
    <NameID>alice@company.com</NameID>
  </Subject>
  <Conditions
    NotBefore="2026-05-04T10:00:00"
    NotOnOrAfter="2026-05-04T10:05:00">
  </Conditions>
  <AttributeStatement>
    <Attribute Name="Role">Admin</Attribute>
    <Attribute Name="Department">Engineering</Attribute>
  </AttributeStatement>
  <Signature>
    <!-- Cryptographic proof this came from the IdP -->
  </Signature>
</SAMLAssertion>
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## THE MASTER COMPARISON TABLE

```
DIMENSION          LDAP              NTLM              KERBEROS         SAML
───────────────────────────────────────────────────────────────────────────────
PURPOSE            Directory         Authentication    Authentication   Federation/SSO
                   storage/query     (legacy)          (enterprise)     (cross-org)

MECHANISM          Query protocol    Challenge-        Ticket-based     XML assertion
                                     response          (symmetric       (PKI signed)
                                                       crypto)

NETWORK SCOPE      Local/intranet    LAN/intranet      LAN/intranet     Internet/WAN

PASSWORD TRAVELS   Yes (BIND)        Never (hash       Never            Never
OVER WIRE?         unless LDAPS      only)

MUTUAL AUTH        No                NTLMv2 partial    YES ✅           SP-side only

TICKET/TOKEN       No                No                Yes (TGT + ST)   Yes (assertion)

STATELESS?         No (session)      No                No               Yes (assertion
                                                                        self-contained)

GOOD FOR           User lookup,      Legacy Windows    Windows AD,      Web SSO,
                   group mgmt        apps              Unix Kerberos    Cloud apps,
                                                                        Multi-org

BAD FOR            Authentication    Modern systems    Cross-internet   Internal ticket
                   alone             (use Kerberos)    (firewall UDP)   management

PROTOCOL           TCP 389/636       SMB/NetBIOS       UDP/TCP 88       HTTPS (POST/
PORT                                                                    Redirect)

SECURITY RISK      Credential        Pass-the-Hash,    Kerberoasting,   XML signature
                   exposure if       NTLM relay        Golden Ticket    wrapping attack
                   no TLS

STANDARD           RFC 4511          Microsoft         RFC 4120         OASIS standard
                                     proprietary       (MIT origin)

YEAR INTRODUCED    1993              1993              1988 (v4)        2002
```

---

## HOW THEY WORK TOGETHER (Enterprise Reality)

```
ENTERPRISE IDENTITY FLOW:

User opens browser → wants to access Salesforce
         │
         ▼
  ┌─────────────────────────────────────────────────────┐
  │  STEP 1: Kerberos authenticates user to Windows AD  │
  │          (on corporate LAN at login time)            │
  └────────────────────────┬────────────────────────────┘
                           │ Uses...
                           ▼
  ┌─────────────────────────────────────────────────────┐
  │  LDAP: Active Directory stores user data,           │
  │        groups, and attributes                       │
  └────────────────────────┬────────────────────────────┘
                           │ Then...
                           ▼
  ┌─────────────────────────────────────────────────────┐
  │  ADFS (or Okta) translates Kerberos identity        │
  │  into SAML Assertion for cloud services             │
  └────────────────────────┬────────────────────────────┘
                           │ Finally...
                           ▼
  ┌─────────────────────────────────────────────────────┐
  │  Salesforce receives SAML Assertion                 │
  │  → Grants access without knowing your password      │
  └─────────────────────────────────────────────────────┘

NTLM is only used if Kerberos fails (legacy fallback)
```

---

## 🐧 LINUX ALTERNATIVES & EQUIVALENTS

### Authentication Daemons & Frameworks

```
WINDOWS TECHNOLOGY     LINUX EQUIVALENT(s)           NOTES
─────────────────────────────────────────────────────────────────────
Active Directory (AD)  FreeIPA                       Most complete AD
                       (= MIT Kerberos +              alternative;
                        389-DS LDAP +                 RedHat backed
                        Dogtag PKI +
                        SSSD + DNS)

Active Directory       Samba (AD DC mode)            Implements full
Domain Controller      (Samba 4.x)                   AD-compatible DC

LDAP (AD's LDAP)       OpenLDAP                      Bare-bones LDAP
                       389 Directory Server           server (RedHat)
                       Apache Directory Server        Java-based

Kerberos (Microsoft)   MIT Kerberos (krb5)           THE reference
                       Heimdal Kerberos              implementation

NTLM Auth              winbind (part of Samba)       For Linux to auth
                                                     against Windows NTLM

SAML IdP               Keycloak                      Full-featured OSS
                       Shibboleth                    identity provider
                       SimpleSAMLphp                 SAML + OIDC + OAuth2

SAML SP lib            python3-saml                  Library-level
                       pysaml2                       SAML consumption
                       lasso

Windows Login (GINA)   PAM                           Pluggable Auth
                       (Pluggable Auth Modules)       Modules — universal
                                                      Linux auth framework

Group Policy Objects   Ansible / Salt / Puppet       Policy enforcement
(GPO)                  FreeIPA Host-based policies

Windows Credential     SSSD                          System Security
Cache                  (System Security Services D.) Services Daemon
                                                     → caches AD creds
                                                        offline
```

### Linux Auth Stack (How It All Connects)

```
APPLICATION (SSH, sudo, login, web app)
         │
         ▼
┌─────────────────────────────────────────┐
│  PAM (Pluggable Authentication Modules) │
│  /etc/pam.d/sshd, /etc/pam.d/sudo      │
│                                         │
│  Modules: pam_unix, pam_ldap,          │
│           pam_krb5, pam_sss            │
└────────────────┬────────────────────────┘
                 │ calls
         ┌───────┴────────┐
         ▼                ▼
┌──────────────┐   ┌──────────────────────────────┐
│  /etc/passwd │   │  SSSD                         │
│  /etc/shadow │   │  (talks to FreeIPA/AD/LDAP)  │
│  (local users│   │  Caches credentials locally   │
│   only)      │   │  Handles Kerberos tickets     │
└──────────────┘   └───────────────┬──────────────┘
                                   │ talks to
                    ┌──────────────┴─────────────────┐
                    ▼                                 ▼
           ┌────────────────┐             ┌──────────────────┐
           │  MIT Kerberos  │             │  OpenLDAP /      │
           │  KDC (krb5kdc) │             │  FreeIPA 389-DS  │
           │  Port 88       │             │  Port 389/636    │
           └────────────────┘             └──────────────────┘
```

### FreeIPA — The Linux AD (Deep Dive)

```
FreeIPA = Integrated Identity Management for Linux

┌──────────────────────────────────────────────────────────┐
│                     FreeIPA Server                        │
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │ MIT Kerberos│  │ 389 Dir Srv │  │  Dogtag PKI      │  │
│  │ (AuthN)     │  │ (LDAP store)│  │  (Certificates)  │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │  BIND DNS   │  │  Web UI     │  │  SSSD Client     │  │
│  │  (SRV recs) │  │  (manage)   │  │  Integration     │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
└──────────────────────────────────────────────────────────┘

FreeIPA can also establish TRUST with Windows Active Directory
→ Windows users can access Linux resources and vice versa
```

### Quick Reference: Which Linux Tool for What?

```
NEED                              USE
──────────────────────────────────────────────────────────────
Simple LDAP server               OpenLDAP
Full AD replacement              FreeIPA
Linux joining Windows AD         sssd + realmd + Kerberos
SAML Identity Provider (web)     Keycloak
SAML/OAuth2 for apps             Keycloak (also does OIDC)
Authenticate against NTLM        winbind (Samba)
PAM-level AD auth on server      pam_sss + sssd
Federated Kerberos across realms MIT krb5 cross-realm trust
SSH key management at scale      Vault (HashiCorp) / FreeIPA
Passwordless auth (FIDO2)        Keycloak + WebAuthn
```

---

## 🔑 The Expert's Decision Framework

```
START
  │
  ▼
Are users within ONE organization's network?
  │
  ├── YES → Need ticket-based SSO?
  │           ├── YES → KERBEROS (+ LDAP backend)
  │           └── NO  → LDAP (for lookup only)
  │                      + PAM/SSSD for auth
  │
  └── NO → Are organizations separate companies / cloud?
              │
              ├── YES → SAML (or OIDC/OAuth2 for modern APIs)
              │
              └── Legacy Windows-only environment?
                    └── NTLM (but plan to migrate away)
```

---

## 🧘 Cognitive Principle for This Topic

This topic is a perfect exercise in **chunking** — the cognitive science principle where experts group related facts into single mental units. You've now built these chunks:

```
CHUNK 1: LDAP = Phone book (store + query)
CHUNK 2: NTLM = Prove yourself with a puzzle (legacy, insecure)
CHUNK 3: Kerberos = Ticket system (efficient, mutual, secure)
CHUNK 4: SAML = Signed letter of introduction between organizations
CHUNK 5: Linux = FreeIPA + SSSD + PAM = complete open-source stack
```

When you encounter these in a real system (e.g., reading `/etc/sssd/sssd.conf` or a Keycloak config), your brain will immediately map them to these chunks — that's **expert pattern recognition** developing.