# Administrative Domain in Networking

## What is an Administrative Domain?

An **Administrative Domain (AD)** is a collection of networks, hosts, routers, and other resources that are **managed and controlled by a single authority** (an organization, company, ISP, or institution).

Think of it like a **country** — it has its own laws (policies), borders (boundaries), and a government (administrator) that controls what happens inside.

---

## Core Mental Model

```
REAL WORLD ANALOGY
══════════════════════════════════════════════════════════

  ┌─────────────────────────────────────────────────────┐
  │              COUNTRY (Administrative Domain)        │
  │                                                     │
  │   ┌──────────┐  ┌──────────┐  ┌──────────┐         │
  │   │  City A  │  │  City B  │  │  City C  │         │
  │   │(Subnet 1)│  │(Subnet 2)│  │(Subnet 3)│         │
  │   └──────────┘  └──────────┘  └──────────┘         │
  │                                                     │
  │   🏛️  Government = Network Administrator           │
  │   📜  Laws       = Routing Policies                 │
  │   🚧  Borders    = Firewalls / Border Routers       │
  │   🛂  Customs    = Access Control Lists (ACLs)      │
  └─────────────────────────────────────────────────────┘

  Two countries interact via TREATIES = BGP (Border Gateway Protocol)
```

---

## Formal Definition — Broken Down

```
Administrative Domain
        │
        ├── WHO controls it?
        │       └── A single administrative authority
        │           (Google, ISP, University, Enterprise)
        │
        ├── WHAT does it contain?
        │       ├── Routers
        │       ├── Switches
        │       ├── Hosts / Servers
        │       ├── Subnets
        │       └── Network links
        │
        ├── HOW is it identified?
        │       └── AS Number (Autonomous System Number)
        │           Example: Google = AS15169
        │                    Cloudflare = AS13335
        │
        └── WHY does it matter?
                ├── Routing decisions stay internal
                ├── Policies are self-defined
                └── External communication is controlled
```

---

## The Big Picture — Internet as Multiple Domains

```
THE INTERNET — A FEDERATION OF ADMINISTRATIVE DOMAINS
═══════════════════════════════════════════════════════════════════

  ┌─────────────────────┐         ┌─────────────────────┐
  │   Admin Domain A    │         │   Admin Domain B    │
  │   (Google AS15169)  │         │  (Cloudflare AS13335│
  │                     │         │                     │
  │  R1──R2──R3         │         │   R7──R8            │
  │  |       |          │◄───────►│   |    |            │
  │  R4──R5──R6         │  eBGP   │   R9──R10           │
  │                     │         │                     │
  │  [Internal routing  │         │  [Internal routing  │
  │   uses OSPF/ISIS]   │         │   uses OSPF/ISIS]   │
  └─────────────────────┘         └─────────────────────┘
            ▲                               ▲
            │ eBGP                          │ eBGP
            ▼                               ▼
  ┌─────────────────────┐         ┌─────────────────────┐
  │   Admin Domain C    │         │   Admin Domain D    │
  │   (ISP AS7922)      │◄───────►│  (University AS789) │
  │                     │  eBGP   │                     │
  └─────────────────────┘         └─────────────────────┘

  eBGP = external BGP  (between domains — like international treaties)
  OSPF = Open Shortest Path First (inside a domain — internal roads)
  ISIS = Intermediate System to Intermediate System (also internal)
```

---

## Key Terminology — Every Word Explained

### 1. Autonomous System (AS)
An Administrative Domain is technically called an **Autonomous System** in networking.

```
AUTONOMOUS SYSTEM
─────────────────
"Autonomous" = Self-governing = Makes its OWN routing decisions

┌──────────────────────────────────────────┐
│  AS (Autonomous System)                  │
│                                          │
│  • Has a unique AS Number (ASN)          │
│    - 16-bit: 1 to 65535                  │
│    - 32-bit: 65536 to 4,294,967,295      │
│                                          │
│  • Controls its own routing policy       │
│  • Decides how traffic enters/exits      │
│  • Examples:                             │
│    - AS15169 → Google                    │
│    - AS32934 → Facebook/Meta             │
│    - AS13335 → Cloudflare                │
│    - AS7018  → AT&T                      │
└──────────────────────────────────────────┘
```

---

### 2. Interior vs Exterior — The Two Worlds

```
TWO WORLDS OF ROUTING
══════════════════════════════════════════════════════

  INSIDE an Admin Domain          BETWEEN Admin Domains
  ────────────────────            ────────────────────
  Interior Gateway Protocol       Exterior Gateway Protocol
  (IGP)                           (EGP)

  Goal: Find FASTEST path         Goal: Follow POLICY

  Examples:                       Examples:
  • OSPF                          • BGP (Border Gateway Protocol)
  • IS-IS                           (THE protocol of the Internet)
  • RIP
  • EIGRP

  Metric: bandwidth, delay,       Metric: Policy, business
          hop count                       agreements, cost

  ┌──────────────────────────────────────────────────┐
  │                                                  │
  │  [Host A]──[R1]──[R2]──[R3]──[Border Router]    │
  │               ↑                      ↑           │
  │           IGP (OSPF)              eBGP to        │
  │           runs here               next AS        │
  │                                                  │
  └──────────────────────────────────────────────────┘
```

---

### 3. Border Router — The Gateway Concept

```
BORDER ROUTER — The "Customs Officer"
══════════════════════════════════════

        Admin Domain A              Admin Domain B
   ┌────────────────────┐      ┌────────────────────┐
   │                    │      │                    │
   │  R1──R2──R3        │      │   R7──R8──R9       │
   │           │        │      │   │                │
   │           R4 ◄─────┼──────┼─► R5               │
   │           │        │      │   │                │
   │        [BORDER]    │      │ [BORDER]           │
   │        ROUTER A    │      │ ROUTER B           │
   └────────────────────┘      └────────────────────┘
              │                         │
              └──────── eBGP ───────────┘
                   (speaks to each other)

  Border Router responsibilities:
  ├── Run eBGP with neighboring AS
  ├── Enforce inbound/outbound policies
  ├── Filter routes (what to advertise, what to accept)
  └── Translate between internal and external routing
```

---

## Types of Administrative Domains

```
CLASSIFICATION BY ROLE
══════════════════════════════════════════════════════════════════

  1. STUB AS (End customer)
  ─────────────────────────
  • Has only ONE connection to the Internet
  • Traffic either originates or terminates here
  • Example: A small company, university

        [Stub AS]───[ISP AS]───[Internet]
           ↑
      Only one exit point

  ──────────────────────────────────────────────────────────────

  2. TRANSIT AS (Carrier/ISP)
  ───────────────────────────
  • Allows traffic to PASS THROUGH it
  • Connects multiple other ASes
  • Example: AT&T, Verizon, Tata Communications

        [AS_A]───[Transit ISP AS]───[AS_B]
                        │
                      [AS_C]
             Traffic flows through it

  ──────────────────────────────────────────────────────────────

  3. MULTIHOMED AS (Redundant connections)
  ─────────────────────────────────────────
  • Connected to MULTIPLE ISPs
  • For reliability and load balancing
  • But does NOT carry transit traffic

        [ISP_1]
            \
          [Multihomed AS]  ← Big enterprise
            /
        [ISP_2]

  ──────────────────────────────────────────────────────────────

  DECISION TREE: What type is your AS?

  Do you have only one upstream connection?
           │
        YES─────────────► STUB AS
           │
          NO
           │
  Do you carry traffic for others?
           │
        YES─────────────► TRANSIT AS
           │
          NO
           ▼
        MULTIHOMED AS
```

---

## How Routing Works Across Domains — Step by Step

```
PACKET JOURNEY: Host in India → Server in USA
═══════════════════════════════════════════════════════════════

  Source: 192.168.1.10 (BSNL network, India)
  Dest:   142.250.67.46 (Google, USA)

  STEP 1: Packet created at host
  ────────────────────────────────
  [Your PC] → [Home Router] → [BSNL Local Router]
                                     │
                              (IGP routing inside BSNL AS)

  STEP 2: Reaches BSNL Border Router
  ────────────────────────────────────
  BSNL AS ──[Border Router]──► Tata Communications AS
                   │
              eBGP used here
              "Where is 142.250.67.46?"
              BGP table consulted

  STEP 3: Transit through multiple AS
  ─────────────────────────────────────
  Tata AS ──► TISPN AS ──► NTT AS ──► Google AS
         eBGP       eBGP        eBGP

  STEP 4: Arrives at Google AS Border Router
  ───────────────────────────────────────────
  [Google Border Router]
         │
         ▼ (IGP routing inside Google)
  [Google Data Center Router] → [Server 142.250.67.46]

  TOTAL FLOW:
  ─────────────────────────────────────────────────────
  [Host]─IGP─[Border]─eBGP─[Transit]─eBGP─[Destination]
              BSNL              Tata          Google
```

---

## Policy — The Real Purpose of Admin Domains

```
WHY POLICIES MATTER
══════════════════════════════════════════════════════

  Without Admin Domains:
  • Any router could change any route
  • No business control
  • No security boundaries
  • Chaos

  With Admin Domains:
  ┌────────────────────────────────────────────────────┐
  │  Policy Examples                                   │
  │                                                    │
  │  1. "Don't send our internal routes to ISP B"      │
  │     → Route filtering at border router             │
  │                                                    │
  │  2. "Prefer ISP A over ISP B for outgoing traffic" │
  │     → Local preference in BGP                     │
  │                                                    │
  │  3. "Block all traffic from AS X"                  │
  │     → BGP community filtering                     │
  │                                                    │
  │  4. "Only accept /24 or shorter prefixes"          │
  │     → Prefix length filtering                     │
  └────────────────────────────────────────────────────┘

  POLICY ENFORCEMENT POINTS:
  ─────────────────────────────────────────────────────
                 Admin Domain
        ┌─────────────────────────┐
  IN ──►│ [Inbound Policy Filter] │
        │         │               │
        │    [IGP Routing]        │
        │         │               │
  OUT ◄─│[Outbound Policy Filter] │
        └─────────────────────────┘
```

---

## Trust Model — Security Perspective

```
TRUST LEVELS ACROSS DOMAINS
════════════════════════════════════════════════════════

  HIGH TRUST          MEDIUM TRUST        LOW/NO TRUST
  ─────────────       ─────────────       ─────────────
  Inside your         Peering partners    Unknown AS /
  own AS              (agreed BGP peers)  Internet at large

  ┌──────────────────────────────────────────────────────┐
  │                                                      │
  │  [Your AS - TRUST ZONE]  ←──── Firewall ────►        │
  │  ┌──────────────────┐         (DMZ)          │       │
  │  │ All hosts trust  │                    [Internet]  │
  │  │ each other       │                               │
  │  │ (relatively)     │    BGP Peers                  │
  │  └──────────────────┘    ─────────────              │
  │                          Verify prefixes            │
  │                          Use MD5 auth               │
  │                          Apply filters              │
  └──────────────────────────────────────────────────────┘

  KEY INSIGHT:
  ─────────────────────────────────────────────────────
  You CANNOT trust routes advertised by other AS
  blindly. BGP hijacking happens when a rogue AS
  advertises prefixes it doesn't own.
  
  Famous example: Pakistan Telecom hijacked YouTube
  prefix (2008) → Global outage for 2 hours.
```

---

## Summary — The Complete Mental Map

```
ADMINISTRATIVE DOMAIN — COMPLETE MENTAL MAP
════════════════════════════════════════════════════════════════

                    Administrative Domain
                           │
          ┌────────────────┼────────────────┐
          │                │                │
      Identity         Contents          Behavior
          │                │                │
       AS Number       Routers,         Internal: IGP
     (unique global    Hosts,           External: eBGP
      identifier)      Subnets,         Policy: BGP attrs
                        Links            Trust: filtered

          Types                    Role in Internet
          ─────                    ───────────────────
          Stub AS ────────────►  End user / Enterprise
          Transit AS ──────────►  ISP / Carrier
          Multihomed AS ───────►  Redundant Enterprise

          Boundary Mechanism
          ──────────────────
          Border Router (speaks eBGP to outside world)
          Firewall (enforces security policy)
          ACL (Access Control List — packet filtering)
```

---

## 🧠 Mental Models & Cognitive Anchors

| Concept | Mental Model |
|---|---|
| Administrative Domain | A country with its own laws |
| AS Number | Country's unique phone code |
| BGP | Diplomatic protocol between countries |
| IGP | Internal road network of a country |
| Border Router | Customs & immigration officer |
| Route Policy | Trade agreements & import/export rules |
| BGP Hijacking | A country falsely claiming another's territory |

---

## 🎯 Expert Insight — What Most People Miss

**1. Administrative Domains ≠ Physical boundaries**
A company with offices in Mumbai, Delhi, and Chennai can be ONE administrative domain if managed centrally.

**2. Trust is asymmetric**
You trust your own AS completely. You partially trust peers. You verify (and distrust by default) the rest of the Internet.

**3. The Internet has no central authority**
It is a collection of ~100,000+ administrative domains, each self-governing, cooperating through BGP policies. This is why the internet is resilient but also why BGP hijacking is dangerous.

**4. Policy overrides performance**
Inside a domain → optimize for speed (shortest path). Between domains → optimize for policy (business contracts, cost, legal). This is a fundamental design philosophy.

---

> 🏔️ **Monk's Note:** The administrative domain concept is the foundation of how the entire Internet is structured. Every routing protocol you learn (BGP, OSPF, ISIS) will make more sense when you anchor it to this boundary. Master the boundary, master the internet architecture.