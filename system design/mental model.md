# 🏆 SENIOR SDE INTERVIEW — COMPLETE MASTER GUIDE
### From Fundamentals to World-Class Readiness

---

> **Mental Model Before You Start:**
> A Senior SDE interview is NOT a test of whether you can *do* things.
> It is a test of whether you can *think* at scale — across systems, people, trade-offs, and time.
> Every question is secretly asking: "Can I trust this person with the company's most critical infrastructure and team?"

---

## TABLE OF CONTENTS

```
PART 0 — MINDSET & META-STRATEGY
PART 1 — SYSTEM DESIGN & ARCHITECTURE
PART 2 — TECHNICAL LEADERSHIP & DEEP DIVE
PART 3 — BEHAVIORAL & SOFT SKILLS (STAR METHOD)
PART 4 — PROBLEM SOLVING & DEBUGGING
PART 5 — CORE COMPETENCIES EVALUATED
PART 6 — CODING ROUNDS (Senior-Level Expectations)
PART 7 — WHAT MOST CANDIDATES MISS
PART 8 — 8-WEEK PREPARATION ROADMAP
PART 9 — MASTER CHEAT SHEET & QUICK REFERENCES
```

---

# PART 0 — MINDSET & META-STRATEGY

## The Senior vs Mid-Level Mental Shift

```
MID-LEVEL ENGINEER BRAIN:
┌─────────────────────────────────────────────────────────┐
│  "How do I solve this problem?"                         │
│  Focus: Correctness, implementation, personal output    │
└─────────────────────────────────────────────────────────┘

SENIOR ENGINEER BRAIN:
┌─────────────────────────────────────────────────────────┐
│  "Should we even solve this problem? If yes, how do     │
│   we solve it in a way that is scalable, maintainable,  │
│   cost-effective, and elevates the entire team?"        │
│  Focus: Systems, people, trade-offs, second-order       │
│         consequences, ambiguity management              │
└─────────────────────────────────────────────────────────┘
```

## The 5 Dimensions Interviewers Always Judge

```
                     ┌─────────────────┐
                     │   INTERVIEWER   │
                     │   SCORECARD     │
                     └────────┬────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
   ┌───────────┐       ┌───────────┐       ┌───────────┐
   │ TECHNICAL │       │LEADERSHIP │       │BEHAVIORAL │
   │ DEPTH     │       │& STRATEGY │       │& CULTURE  │
   └───────────┘       └───────────┘       └───────────┘
         │                    │                    │
         ▼                    ▼                    ▼
   ┌───────────┐       ┌───────────┐
   │COMMUNICATION│     │OWNERSHIP  │
   │ CLARITY   │       │& IMPACT   │
   └───────────┘       └───────────┘
```

## Deliberate Practice Principle (Cognitive Science)
- **Chunking**: Break each interview topic into sub-skills and practice each in isolation.
  - e.g., "System Design" = [Requirement Clarification] + [API Design] + [Data Modeling] + [Capacity Estimation] + [Component Placement] — practice each separately.
- **Spaced Repetition**: Review earlier concepts 1, 3, 7, 14 days after learning.
- **Meta-cognition**: After every mock interview, ask "What mental models did I NOT apply?"

---

# PART 1 — SYSTEM DESIGN & ARCHITECTURE

## 1.1 The Universal System Design Framework (RADIO)

Use this framework for EVERY design question. Never skip steps.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    RADIO FRAMEWORK                                  │
├───────────────┬─────────────────────────────────────────────────────┤
│ R - Requirements│ Functional + Non-Functional + Constraints         │
│ A - API Design  │ What interfaces does the system expose?           │
│ D - Data Model  │ Schema, storage choices, access patterns          │
│ I - Infrastructure│ Components, services, communication patterns   │
│ O - Optimize   │ Bottlenecks, caching, sharding, trade-offs         │
└───────────────┴─────────────────────────────────────────────────────┘
```

## 1.2 Requirements Gathering — The Non-Negotiable First Step

**NEVER start designing without asking these:**

```
FUNCTIONAL REQUIREMENTS (What should the system DO?)
─────────────────────────────────────────────────────
 • What are the core user-facing features?
 • What are the edge cases? (e.g., what if a user posts the same URL twice?)
 • Are there admin/internal operations?

NON-FUNCTIONAL REQUIREMENTS (How well should it do it?)
─────────────────────────────────────────────────────
 • Scale: How many users? Reads vs Writes ratio?
 • Latency: What is acceptable response time? (p50, p99)
 • Availability: 99.9% (8.7hr downtime/yr) vs 99.99% (53min/yr) vs 99.999%?
 • Consistency: Strong vs Eventual (CAP Theorem)?
 • Data durability: Can we lose any data?

CAPACITY ESTIMATION (Back-of-envelope)
─────────────────────────────────────────────────────
 • Daily Active Users (DAU)?
 • Read/Write QPS (Queries Per Second)?
 • Storage requirements?
 • Bandwidth requirements?
```

### Key Numbers Every Senior Engineer Should Know

```
LATENCY HIERARCHY (Know this cold):
─────────────────────────────────────────────────────────────
 L1 cache reference              :    0.5 ns
 Branch mispredict               :    5   ns
 L2 cache reference              :    7   ns
 Mutex lock/unlock               :   25   ns
 Main memory (RAM) reference     :  100   ns
 Compress 1KB with Zippy         :   10   µs
 Send 1KB over 1 Gbps network    :   10   µs
 Read 4KB randomly from SSD      :  150   µs
 Round-trip within data center   :  500   µs
 Read 1MB sequentially from SSD  :    1   ms
 HDD random seek                 :   10   ms
 Read 1MB sequentially from HDD  :   30   ms
 Send packet CA → Netherlands→CA : 150   ms

STORAGE HIERARCHY:
─────────────────────────────────────────────────────────────
 CPU Registers  → L1 Cache → L2 Cache → L3 Cache → RAM → SSD → HDD → Network

QUICK MATH TOOLS:
─────────────────────────────────────────────────────────────
 1 million req/day   = ~12 req/sec
 1 billion req/day   = ~12,000 req/sec
 1 KB × 1 million    = 1 GB
 10 bytes × 1 billion = 10 GB
```

## 1.3 CAP Theorem — The Foundation of Distributed Systems

**What is CAP?** In a distributed system, during a network partition (P), you must choose between:

```
        C ─────────── A
       /               \
      /    Pick 2 of 3  \
     /                   \
    P─────────────────────+

C = Consistency   : Every read receives the most recent write or an error
A = Availability  : Every request receives a (non-error) response (may not be latest)
P = Partition Tolerance: System continues despite network failures

REAL-WORLD MAPPINGS:
────────────────────────────────────────────────────────────
 CA Systems : Traditional RDBMS (MySQL, PostgreSQL) — assumes no partition
 CP Systems : HBase, MongoDB (in some configs), ZooKeeper, etcd
             → Sacrifices availability during partition (returns error)
 AP Systems : Cassandra, DynamoDB, CouchDB
             → Sacrifices consistency (returns stale data during partition)

DECISION TREE:
────────────────────────────────────────────────────────────
 Is data loss catastrophic? (Financial, Medical)
   └─ YES → Lean CP (strong consistency)
 Is downtime catastrophic? (Social media, streaming)
   └─ YES → Lean AP (high availability)
 Can you tolerate stale reads for milliseconds?
   └─ YES → Use eventual consistency with compensation logic
```

## 1.4 SQL vs NoSQL Decision Framework

```
USE SQL (PostgreSQL, MySQL) WHEN:
─────────────────────────────────
 ✓ Data has complex relationships (JOINs)
 ✓ You need ACID transactions
 ✓ Schema is well-defined and stable
 ✓ Complex queries, aggregations, reporting
 ✓ Small-to-medium scale OR scale with read replicas
 Examples: Banking, E-commerce orders, User accounts

USE NoSQL WHEN:
─────────────────────────────────
 ✓ Schema is flexible/evolving
 ✓ Horizontal scaling is primary concern
 ✓ High write throughput needed
 ✓ Simple access patterns (key-value, document)
 ✓ Geo-distributed data

 NoSQL Types:
 ┌────────────┬──────────────────┬──────────────────────┐
 │ Type       │ Engine           │ Use Case             │
 ├────────────┼──────────────────┼──────────────────────┤
 │ Key-Value  │ Redis, DynamoDB  │ Sessions, caching    │
 │ Document   │ MongoDB, Couchdb │ Catalogs, CMS        │
 │ Column     │ Cassandra, HBase │ Time-series, IoT     │
 │ Graph      │ Neo4j, Neptune   │ Social networks, rec │
 │ Search     │ Elasticsearch    │ Full-text search     │
 └────────────┴──────────────────┴──────────────────────┘
```

## 1.5 Sharding — What It Is and How to Think About It

**Sharding** = horizontally splitting a database into smaller pieces called "shards", each shard holds a subset of the data and runs on a different server.

```
WITHOUT SHARDING (Vertical Scaling):
──────────────────────────────────────
 All data → One huge server → Eventually hits ceiling

WITH SHARDING (Horizontal Scaling):
──────────────────────────────────────
                  ┌──────────────┐
   Request  ───→  │  Shard Router │
                  └──────┬───────┘
                         │ hash(key) % N
            ┌────────────┼────────────┐
            ▼            ▼            ▼
        ┌───────┐    ┌───────┐    ┌───────┐
        │Shard 0│    │Shard 1│    │Shard 2│
        │users  │    │users  │    │users  │
        │A–G    │    │H–P    │    │Q–Z    │
        └───────┘    └───────┘    └───────┘

SHARDING STRATEGIES:
──────────────────────────────────────
 1. Range-Based  : shard by ID range (1–1M, 1M–2M)
    → Risk: Hotspots (if most users are in recent range)

 2. Hash-Based   : shard by hash(userId) % N
    → Risk: Resharding is expensive

 3. Geo-Based    : shard by region (US, EU, APAC)
    → Natural for compliance (GDPR), latency

 4. Directory    : lookup table maps key → shard
    → Flexible, but lookup table is single point of failure

GEOGRAPHIC + TIME-SERIES SHARDING:
──────────────────────────────────────
 Composite sharding key: (region, time_bucket)
 e.g., "US_2024_Q1", "EU_2024_Q2"
 → Queries for "all EU data in Q1" hit exactly one shard
 → Old shards can be archived/cold-stored
```

## 1.6 Caching — The Most Impactful Optimization

```
CACHE PLACEMENT STRATEGIES:
────────────────────────────────────────────────────────────
                           Client
                             │
                    ┌────────▼────────┐
                    │  CDN (Edge)     │  ← Static assets, geo-near caching
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ API Gateway /   │  ← Rate limiting cache, auth token cache
                    │ Load Balancer   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Application     │  ← In-memory (local) cache
                    │ Server          │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Redis / Memcached│ ← Distributed cache
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   Database      │  ← Query result cache, buffer pool
                    └─────────────────┘

CACHE PATTERNS:
────────────────────────────────────────────────────────────
 Cache-Aside (Lazy Loading):
   App checks cache → MISS → App queries DB → App writes to cache
   Pro: Only caches what's needed. Con: Cold start penalty.

 Write-Through:
   App writes to cache AND DB synchronously
   Pro: Cache always fresh. Con: Write latency doubles.

 Write-Behind (Write-Back):
   App writes to cache → asynchronously writes to DB
   Pro: Fast writes. Con: Risk of data loss on crash.

 Read-Through:
   Cache handles DB reads automatically on miss
   Pro: Transparent. Con: Less control.

CACHE EVICTION POLICIES:
────────────────────────────────────────────────────────────
 LRU  (Least Recently Used)    → Good for temporal locality
 LFU  (Least Frequently Used)  → Good for popularity-based access
 TTL  (Time-to-Live)           → Good for data freshness
 FIFO (First In, First Out)    → Simple, rarely optimal
```

## 1.7 Designing for High Availability

**Key Concept — SPOF (Single Point of Failure)**: Any component whose failure brings down the system. Eliminate every SPOF.

```
AVAILABILITY PATTERNS:
────────────────────────────────────────────────────────────
 Active-Passive (Primary-Replica):
   Primary handles writes → Replica syncs → On failure, replica promotes
   Pro: Simple. Con: Failover takes time (seconds to minutes).

 Active-Active:
   Both nodes handle traffic → Load balanced
   Pro: Zero-downtime failover. Con: Conflict resolution complexity.

LOAD BALANCING ALGORITHMS:
────────────────────────────────────────────────────────────
 Round Robin       → Simple, works if servers are equal
 Least Connections → Sends to server with fewest active connections
 IP Hash           → Same client always hits same server (session affinity)
 Weighted Round Robin → Handles heterogeneous servers

CIRCUIT BREAKER PATTERN:
────────────────────────────────────────────────────────────
 Problem: A failing downstream service causes cascading failures

 State Machine:
  ┌─────────┐   failures > threshold   ┌──────────┐
  │  CLOSED │ ─────────────────────→  │   OPEN   │
  │(normal) │                          │(blocking)│
  └─────────┘                          └──────────┘
       ▲                                    │
       │ success                            │ timeout
       │                               ┌───▼──────┐
       └─────────────────────────────  │  HALF-   │
                                       │  OPEN    │
                                       └──────────┘
 CLOSED  → All requests pass through
 OPEN    → All requests fail fast (no downstream calls)
 HALF-OPEN → One probe request; if success → CLOSED, else → OPEN
```

## 1.8 Monitoring, Instrumentation & Alerting

What to instrument in any new service:

```
THE FOUR GOLDEN SIGNALS (Google SRE):
────────────────────────────────────────────────────────────
 1. Latency    : How long does it take to serve requests?
                 → Track p50, p95, p99 separately (averages lie)
 2. Traffic    : How much demand is the system receiving?
                 → Requests/sec, bytes/sec
 3. Errors     : What is the rate of failed requests?
                 → 5xx, 4xx, application-level errors
 4. Saturation : How "full" is the service?
                 → CPU %, memory %, queue depth, disk I/O

ALERTING HIERARCHY:
────────────────────────────────────────────────────────────
 Pages (PagerDuty/wake someone up):
   → Error rate > 1%, p99 latency > SLA, service completely down

 Tickets (create next-day issue):
   → Memory usage > 80%, disk > 70%, gradual latency increase

 Dashboards (visible but no alert):
   → Business metrics, cache hit rates, background job durations

OBSERVABILITY PILLARS:
────────────────────────────────────────────────────────────
 Metrics   → Prometheus, Datadog, CloudWatch (aggregated numbers)
 Logs      → ELK Stack, Splunk (detailed events, debug)
 Traces    → Jaeger, Zipkin, AWS X-Ray (request flow across services)
 Dashboards→ Grafana, Kibana (visualization layer)
```

## 1.9 Classic System Design Walkthroughs

### Example: URL Shortener (like bit.ly)

```
REQUIREMENTS:
─────────────────────────────────────────────────────────────
 Functional:
   • Create short URL from long URL
   • Redirect short URL → long URL
   • Optional: analytics (click count, geo)
 Non-Functional:
   • 100M URLs created/day → ~1200 writes/sec
   • 10B redirects/day → ~115,000 reads/sec (read-heavy: 10:1 ratio)
   • Low latency for redirect (< 10ms)
   • URLs never change once created (immutable)

API DESIGN:
─────────────────────────────────────────────────────────────
 POST /urls          body: {long_url}     → {short_code}
 GET  /{short_code}                       → 301/302 redirect

 Note: 301 (permanent) → browser caches, less server load
       302 (temporary) → every redirect hits server (better for analytics)

DATA MODEL:
─────────────────────────────────────────────────────────────
 Table: urls
  short_code  VARCHAR(8)  PRIMARY KEY
  long_url    TEXT        NOT NULL
  created_at  TIMESTAMP
  user_id     BIGINT      FK
  expires_at  TIMESTAMP   NULLABLE

SHORT CODE GENERATION STRATEGIES:
─────────────────────────────────────────────────────────────
 Option 1: hash(long_url) → take first 7 chars of base62 encoding
   Pro: Deterministic (same URL = same code)
   Con: Hash collisions need handling

 Option 2: Auto-increment ID → base62 encode
   base62 = [0-9][a-z][A-Z] → 62^7 = 3.5 trillion URLs
   Pro: No collision. Con: Sequential, guessable

 Option 3: Pre-generate a pool of random codes
   Background service generates codes → stores in Redis set
   App pops one on demand
   Pro: O(1) generation. Con: Pool management complexity

HIGH-LEVEL ARCHITECTURE:
─────────────────────────────────────────────────────────────
 User → CDN (static assets)
      → Load Balancer
      → App Servers (stateless, horizontally scalable)
      → Redis (cache: short_code → long_url, TTL=24h)
      → PostgreSQL (primary DB, with read replicas for redirect lookups)
      → Analytics Queue (Kafka) → Analytics Service → ClickHouse

BOTTLENECK ANALYSIS:
─────────────────────────────────────────────────────────────
 115k reads/sec → Cache is mandatory (Redis with 99% hit rate handles this)
 Redirect is critical path → Cache miss must hit DB read replica, not primary
 DB writes: 1200/sec → Single PostgreSQL can handle ~10k writes/sec → fine
```

### Example: Design a Chat System (like WhatsApp)

```
KEY CHALLENGE: Real-time message delivery
─────────────────────────────────────────────────────────────

MESSAGE DELIVERY OPTIONS:
─────────────────────────────────────────────────────────────
 Option 1: Short Polling
   Client: "Any new messages?" every 5 seconds
   Con: Wasted bandwidth, latency up to 5s

 Option 2: Long Polling
   Client holds open HTTP connection until message arrives
   Con: Stateful connection, not true real-time

 Option 3: WebSockets (BEST for chat)
   Persistent bidirectional TCP connection
   Pro: True real-time, low overhead
   Con: Each server holds N open connections
       → Need sticky sessions or message broker

 Option 4: SSE (Server-Sent Events)
   One-directional server→client stream
   Good for: Notifications, feeds (not bidirectional chat)

ARCHITECTURE FOR CHAT:
─────────────────────────────────────────────────────────────
 Client A ──WebSocket──→ Chat Server 1 ──→ Message Queue (Kafka)
                                                    │
 Client B ──WebSocket──→ Chat Server 2 ←── Message Queue (Kafka)
                                │
                         Presence Service (Redis: who is online?)
                         Message DB (Cassandra: time-series, high write)

 WHY CASSANDRA FOR MESSAGES?
 → Messages are append-only (insert-heavy)
 → Queried by conversation_id + timestamp (natural partition key)
 → Horizontal scale for billions of messages
 → No need for complex JOINs
```

---

# PART 2 — TECHNICAL LEADERSHIP & DEEP DIVE

## 2.1 How to Answer "Describe a Challenging Technical Project"

This is your flagship story. Prepare ONE deeply detailed story per key domain.

```
STRUCTURE — The "Impact Pyramid":
─────────────────────────────────────────────────────────────
                    ┌────────────┐
                    │  IMPACT    │  ← Numbers, business outcome, team effect
                    ├────────────┤
                    │  DECISION  │  ← What YOU specifically decided & why
                    ├────────────┤
                    │ TRADE-OFFS │  ← What you gave up, why it was worth it
                    ├────────────┤
                    │ COMPLEXITY │  ← What made it hard (technical specifics)
                    └────────────┘

WHAT INTERVIEWERS ARE LOOKING FOR:
─────────────────────────────────────────────────────────────
 ✓ Can you articulate WHY decisions were made (not just what)?
 ✓ Did you consider alternatives before choosing?
 ✓ Can you quantify impact? (p99 latency reduced 40%, cost cut $50k/month)
 ✓ Did you handle ambiguity? (incomplete requirements, unclear ownership)
 ✓ Did you bring others along? (alignment, communication, mentorship)

RED FLAGS THAT KILL CANDIDATES:
─────────────────────────────────────────────────────────────
 ✗ "We did X" without a clear "I specifically did Y"
 ✗ No metrics/numbers attached to outcome
 ✗ No alternatives considered
 ✗ Couldn't explain technical depth when probed
 ✗ Blaming others for failures
```

## 2.2 Technical Decision Making Under Uncertainty

```
FRAMEWORK — The Decision Log:
─────────────────────────────────────────────────────────────
 Step 1: FRAME  → "What are we actually deciding?"
                  Separate the decision from the implementation.

 Step 2: OPTIONS → Generate at least 3 options (never 2 — binary thinking is lazy)
                   Include "do nothing" as an option.

 Step 3: CRITERIA → What properties matter?
                    (latency, cost, complexity, team familiarity, reversibility)

 Step 4: EVALUATE → Score each option against criteria

 Step 5: DECIDE  → Pick one. Document the reasoning.
                   KEY: Document what you DIDN'T choose and WHY.

 Step 6: REVISIT → Set a trigger to re-evaluate ("If traffic exceeds X...")

WHEN ASKED "How do you handle limited information?":
─────────────────────────────────────────────────────────────
 → "I ask: what is the cost of being wrong? If it's low + reversible,
    I bias toward action. If it's high + irreversible, I invest in
    reducing uncertainty first (prototype, data, expert consultation)."

 → "I distinguish between one-way doors (hard to reverse: DB migration)
    and two-way doors (easy to reverse: feature flag rollout).
    One-way doors get more deliberation."
```

## 2.3 Handling Technical Disagreements

```
CONFLICT RESOLUTION DECISION TREE:
─────────────────────────────────────────────────────────────
 Start → Is it a factual dispute or an opinion/preference dispute?
         │
         ▼
    FACTUAL → "Let's define success metrics upfront and test both approaches"
              → Build proof-of-concept, measure, let data decide
         │
         ▼
    OPINION → "Let's clarify what outcome we're actually optimizing for"
              → Find the shared goal, then disagree on the path
         │
         ▼
    STILL STUCK?
    → "I'll escalate to the tech lead with a written trade-off doc,
       not to be overruled, but to get a third technical perspective"
    → OR: "I'll disagree and commit — if we agree on the success criteria,
       I'll support the decision even if I'd have chosen differently"

KEY PHRASE TO KNOW: "Disagree and Commit"
─────────────────────────────────────────────────────────────
 This is an Amazon Leadership Principle but universally valued.
 Meaning: You've expressed your view clearly; the decision went another way;
 you now FULLY support executing the chosen direction — no passive resistance.
```

## 2.4 Technical Debt — The Right Mental Model

```
NOT ALL DEBT IS EQUAL:
─────────────────────────────────────────────────────────────

 INTENTIONAL (Strategic Debt):
   "We'll use a quick hacky solution to validate market fit.
    If it works, we'll rewrite. If not, we've saved time."
   → Write the "debt ticket" at the MOMENT you incur the debt.
   → Set a trigger: "We revisit this when traffic exceeds 10k rps"

 UNINTENTIONAL (Reckless Debt):
   Code written without care under no particular pressure.
   → This must be identified in code reviews and addressed early.

 INADVERTENT (Knowledge Debt):
   "We didn't know about this better pattern when we wrote it."
   → Normal. The solution is ongoing learning + refactoring sprints.

HOW TO BALANCE DEBT vs FEATURES:
─────────────────────────────────────────────────────────────
 Method 1: "20% Rule" — reserve 20% of each sprint for tech debt
 Method 2: "Boy Scout Rule" — always leave code cleaner than you found it
 Method 3: "Debt Threshold" — stop new features if test coverage < X%
                               or if build time > Y minutes
 Method 4: ROI Framing — "Fixing this will save 2 hrs/week for 10 engineers"
                          → make it a business case, not a "nice to have"
```

## 2.5 Code Review Strategy

```
WHAT A SENIOR ENGINEER LOOKS FOR IN CODE REVIEWS:
─────────────────────────────────────────────────────────────
 TIER 1 (Blockers — must fix):
   • Correctness bugs (logic errors, race conditions, off-by-one)
   • Security vulnerabilities (injection, auth bypasses, secret leaks)
   • Data loss risks (no transaction, missing rollback)
   • Performance landmines (N+1 queries, unindexed lookups in hot path)

 TIER 2 (Important — should fix):
   • Missing error handling / unhappy path coverage
   • Insufficient test coverage for critical paths
   • Unclear variable names or misleading comments
   • Violation of team's design principles

 TIER 3 (Nice to have — suggestions):
   • Style preferences (if not caught by linter)
   • Alternative approaches (offered as options, not mandates)

GIVING FEEDBACK — Tone Matters:
─────────────────────────────────────────────────────────────
 BAD:  "This is wrong."
 GOOD: "I think this might have a race condition — what do you think
        about adding a mutex here? Happy to pair on it."

 BAD:  "Why would you do it this way?"
 GOOD: "Curious about the trade-off here — is there a reason we're
        not using X? I've seen it work well for similar patterns."

 Rule: Code reviews are teaching moments. Your goal is to
       make the author a better engineer, not to be right.
```

---

# PART 3 — BEHAVIORAL & SOFT SKILLS (STAR METHOD)

## 3.1 The STAR+ Method (The + Matters)

STAR = Situation, Task, Action, Result. The "+" = **Reflection/Learning**.

```
STAR+ TEMPLATE:
─────────────────────────────────────────────────────────────
 S - SITUATION: Set context. 2–3 sentences max.
                "Our payment service was experiencing..."

 T - TASK:      What was YOUR specific responsibility?
                "I was tasked with leading the investigation
                 and proposing a solution..."

 A - ACTION:    3–5 specific actions YOU took.
                "First I did X because [reasoning]..."
                "Then I decided Y after considering Z..."
                (Use first person: "I", not "we")

 R - RESULT:    Quantified outcome. Business impact.
                "Reduced p99 latency by 60%, saving $30k/month.
                 Team shipped 2 weeks earlier than projected."

 + REFLECTION:  What did you learn? What would you do differently?
                "In retrospect, I'd have involved the DB team earlier.
                 This taught me to map stakeholders before scoping."

WHY THE + IS CRITICAL:
─────────────────────────────────────────────────────────────
 Senior engineers are expected to grow from experience.
 A candidate who can't reflect is seen as rigid.
 Interviewers use this to assess self-awareness and growth mindset.
```

## 3.2 Story Bank — Build These Before Your Interview

Prepare ONE detailed story for EACH of these themes:

```
┌─────────────────────────────────────────────────────────────┐
│ THEME                    │ WHAT IT DEMONSTRATES             │
├─────────────────────────────────────────────────────────────┤
│ Technical failure/mistake│ Humility, ownership, learning    │
│ Influencing without auth │ Leadership without title         │
│ Conflict with coworker   │ Communication, empathy, resolve  │
│ Conflict with manager    │ Courage, professionalism         │
│ Mentoring a junior dev   │ Teaching, patience, elevation    │
│ Handling ambiguity       │ Judgment, initiative, clarifying │
│ Tight deadline decision  │ Prioritization, trade-offs       │
│ Cross-team collaboration │ Coordination, alignment skills   │
│ Convincing non-technical │ Communication, empathy           │
│ Most complex project     │ Technical depth + leadership     │
└─────────────────────────────────────────────────────────────┘
```

## 3.3 Explaining Technical Issues to Non-Technical Stakeholders

```
THE ANALOGY LADDER:
─────────────────────────────────────────────────────────────
 Step 1: Identify what they CARE about (cost, time, risk, customer impact)
 Step 2: Frame the problem in those terms FIRST
 Step 3: Use a physical-world analogy for the mechanism
 Step 4: Give the recommendation, not just the problem
 Step 5: Offer a visual if needed (whiteboard/diagram)

EXAMPLE:
─────────────────────────────────────────────────────────────
 Technical: "Our database has no read replicas, creating a SPOF that
             risks data corruption under concurrent write load."

 Non-Technical: "Right now our data storage is like having one copy of
                 a critical document that everyone in the office edits
                 simultaneously. If that document gets corrupted, we lose
                 everything. Adding read replicas is like making backup
                 copies — it costs $X/month but protects us from a
                 potential $Y million outage."
```

## 3.4 Mentoring Junior Engineers — The Senior's Most Important Skill

```
MENTORSHIP APPROACHES:
─────────────────────────────────────────────────────────────
 BAD: "Here's the answer. Implement it."
   → Junior learns nothing. Creates dependency.

 GOOD: Socratic Method
   → "What have you tried so far?"
   → "What do you think is causing it?"
   → "If you had to guess, what would you try next?"
   → (Only then) "I'd also consider X — want to explore that together?"

CREATING PSYCHOLOGICAL SAFETY:
─────────────────────────────────────────────────────────────
 → Normalize asking questions: "The only bad question is the one not asked"
 → Share YOUR past mistakes openly (vulnerability = psychological safety)
 → Attribute their ideas publicly: "This was [Junior's] insight, which I think..."
 → Give feedback in private, praise in public

TRACKING GROWTH:
─────────────────────────────────────────────────────────────
 → Set 30/60/90 day goals with them, not FOR them
 → Regular 1:1s: "What's blocking you? What do you want to learn?"
 → Gradually increase scope of ownership (start with a module, then a feature,
   then a service, then a cross-team initiative)
```

---

# PART 4 — PROBLEM SOLVING & DEBUGGING

## 4.1 Debugging Critical Production Issues

```
THE PRODUCTION INCIDENT FRAMEWORK (DETECTIVE APPROACH):
─────────────────────────────────────────────────────────────

PHASE 1: TRIAGE (0–5 minutes)
 ┌─────────────────────────────────────────────────────────┐
 │ 1. What is the BLAST RADIUS?                            │
 │    → How many users affected? What services are down?   │
 │ 2. Can we MITIGATE first, investigate second?           │
 │    → Can we roll back? Feature flag off? Reroute traffic?│
 │ 3. Is this GETTING WORSE or stable?                     │
 │    → If escalating: MITIGATION IS PRIORITY #1           │
 └─────────────────────────────────────────────────────────┘

PHASE 2: INVESTIGATE (Once mitigated or stable)
 ┌─────────────────────────────────────────────────────────┐
 │ TIMELINE: "When did this start?" → Correlate with:      │
 │  • Recent deployments (git log, deployment history)     │
 │  • Config changes                                       │
 │  • Traffic spikes                                       │
 │  • Third-party service degradation                      │
 │  • Time of day patterns                                 │
 │                                                         │
 │ HYPOTHESIZE: Generate 3+ possible causes, rank by       │
 │ likelihood, test the most likely FIRST.                 │
 │                                                         │
 │ BISECT: If a recent change caused it, git bisect to     │
 │ find the exact commit.                                  │
 └─────────────────────────────────────────────────────────┘

PHASE 3: FIX & PREVENT
 ┌─────────────────────────────────────────────────────────┐
 │ • Root cause fix (not just symptom suppression)         │
 │ • Write postmortem (blameless)                          │
 │ • Add monitoring for this failure mode                  │
 │ • Add test to prevent regression                        │
 └─────────────────────────────────────────────────────────┘

DEBUGGING MENTAL MODELS:
─────────────────────────────────────────────────────────────
 Scientific Method : Hypothesis → Test → Observe → Repeat
 Rubber Duck Debug : Explain the problem out loud to a rubber duck
                     (Forces structured thinking, often reveals the bug)
 Divide & Conquer  : Binary search the problem space
                     (Remove half the code at a time)
 Follow the Data   : Trace the data from input to output step-by-step
```

## 4.2 Refactoring Legacy Code

```
REFACTORING STRATEGY — "Strangler Fig Pattern":
─────────────────────────────────────────────────────────────
 Named after the strangler fig tree that grows around an existing tree,
 gradually replacing it without disrupting the host.

 Step 1: Write tests around the existing behavior FIRST
         (The "golden master" or "characterization tests")
         → You can't refactor what you can't verify

 Step 2: Identify SEAMS — places where you can inject new behavior
         without changing existing code

 Step 3: Build the new implementation alongside the old
         → Route a small % of traffic to new path (canary)

 Step 4: Gradually shift traffic 1% → 10% → 50% → 100%

 Step 5: Delete the old implementation once new is stable

FOR TESTABILITY SPECIFICALLY:
─────────────────────────────────────────────────────────────
 • Extract dependencies (DB, network calls) behind interfaces
 • Inject dependencies instead of creating them inside functions
 • Remove global state (convert to function parameters)
 • Make pure functions (same input → same output, no side effects)
 • Example (C):
   BAD:  int get_user_age(int id) { db_connect(); ... }
   GOOD: int get_user_age(Database* db, int id) { db->query(...); }
         → Now you can inject a mock DB in tests
```

---

# PART 5 — CORE COMPETENCIES DEEP DIVE

## 5.1 Scalability — Mental Model

```
SCALABILITY AXES:
─────────────────────────────────────────────────────────────

         Vertical Scaling (Scale Up)         Horizontal Scaling (Scale Out)
         ──────────────────────────────────   ──────────────────────────────
         Add more CPU/RAM to one server       Add more servers
         Simple, no code change needed        Requires stateless design
         Has a ceiling (server max)           Theoretically unlimited
         Single point of failure              Fault tolerant
         Good for: Databases, ML training     Good for: Web servers, APIs

STATELESS vs STATEFUL:
─────────────────────────────────────────────────────────────
 STATELESS: Server holds no session data.
   → Any server can handle any request.
   → Scale out trivially.
   → Store state externally: Redis, DB, JWT tokens.

 STATEFUL: Server holds session state.
   → Requires sticky sessions (same user → same server).
   → Harder to scale, but sometimes necessary (WebSockets).

QUEUE-BASED LOAD LEVELING:
─────────────────────────────────────────────────────────────
 Problem: 10x traffic spike overwhelms downstream service.

 Without queue:       With queue:
 Traffic → Service    Traffic → Queue → Service (steady rate)
 → Service crashes    → Queue absorbs spikes, service processes at capacity

 Use when: Video processing, email sending, order fulfillment, notifications
```

## 5.2 Trade-Offs — The Senior Engineer's Core Skill

```
TRADE-OFF DIMENSIONS TO ALWAYS CONSIDER:
─────────────────────────────────────────────────────────────
 Performance  vs  Cost
 Consistency  vs  Availability
 Simplicity   vs  Flexibility
 Speed-to-ship vs  Quality
 Coupling     vs  Autonomy (microservices)

THE "REVERSIBILITY" META-PRINCIPLE:
─────────────────────────────────────────────────────────────
 Before making a decision, ask:
   "If we're wrong, how hard is it to undo?"

 High reversibility  → Bias toward action, learn quickly
 Low reversibility   → Invest time in getting it right

 Examples:
   High: Feature flags, config values, UI changes, API addition
   Low:  Database schema migration, protocol changes, breaking APIs,
         infrastructure redesign
```

## 5.3 Microservices vs Monolith — When to Choose What

```
MONOLITH FIRST (Default for most systems):
─────────────────────────────────────────────────────────────
 + Simple deployment, debugging, testing
 + No network latency between components
 + Easy cross-component transactions
 + Lower operational overhead
 - Tight coupling over time
 - Scaling entire app for one hot service
 - Slow builds as app grows

MICROSERVICES (After you have traction):
─────────────────────────────────────────────────────────────
 + Independent deployment of each service
 + Independent scaling (scale only hot services)
 + Technology diversity
 + Team autonomy (Conway's Law: system mirrors org structure)
 - Distributed system complexity (network failures, distributed transactions)
 - Operational overhead (service mesh, observability stack)
 - Harder to debug (traces span multiple services)

MIGRATION PATTERN (Monolith → Microservices):
─────────────────────────────────────────────────────────────
 1. Identify bounded contexts (auth, payments, notifications, catalog)
 2. Extract the service with LEAST dependencies first
 3. Use the Strangler Fig pattern
 4. Establish contracts (API versioning, event schemas) before splitting
```

---

# PART 6 — CODING ROUNDS (SENIOR LEVEL EXPECTATIONS)

## What "Senior Level" Means in a Coding Interview

```
JUNIOR:   Solves the problem correctly
MID:      Solves optimally + explains trade-offs
SENIOR:   Solves optimally + explains trade-offs + discusses edge cases +
          considers production concerns (thread safety, error handling,
          observability) + suggests follow-on improvements
```

## The Expert's Problem-Solving Protocol

```
STEP-BY-STEP BEFORE WRITING A SINGLE LINE:
─────────────────────────────────────────────────────────────
 1. UNDERSTAND (2 min):
    Read problem twice. Ask: "Is the input sorted? Can values repeat?
    What are the constraints? Are inputs valid?"

 2. EXAMPLES (2 min):
    Work through a simple example by hand.
    Then: edge case (empty, single element, all duplicates, max size).

 3. BRUTE FORCE (2 min mental):
    State the O(n²) or O(n³) naive solution.
    Don't implement yet. Just name it.

 4. OPTIMIZE (3 min):
    Ask: "What information am I recomputing unnecessarily?"
    → Can I use a hash map to trade space for time?
    → Can I sort first to enable binary search?
    → Is there a sliding window / two-pointer pattern here?
    → Is this a DP problem? (Optimal substructure + overlapping subproblems)

 5. IMPLEMENT (10 min):
    Write clean code. Use meaningful names.
    Think out loud.

 6. VERIFY (3 min):
    Trace through your example.
    Check edge cases.
    State time and space complexity.
```

## Complexity Quick Reference

```
COMMON PATTERNS AND THEIR COMPLEXITY:
────────────────────────────────────────────────────────────────────
 Two Pointers     → O(n) time, O(1) space    (sorted array problems)
 Sliding Window   → O(n) time, O(k) space    (subarray/substring problems)
 Hash Map         → O(n) time, O(n) space    (frequency, lookup, two-sum)
 Binary Search    → O(log n) time, O(1) space (sorted search)
 BFS/DFS on Graph → O(V + E) time, O(V) space (traversal, shortest path)
 Heap (Priority Q)→ O(n log k) time          (top-k problems)
 Dynamic Prog.    → varies (usually O(n²) or O(n*m)) (optimization)
 Trie             → O(m) time per op (m=key length) (prefix matching)
 Union-Find       → O(α(n)) ≈ O(1) amortized (connectivity)
```

## Rust/C/C++/Go/Python Code Quality (Language-Specific Tips)

```
RUST:
─────────────────────────────────────────────────────────────
 • Use iterators + combinators (map, filter, fold) over raw loops when readable
 • Prefer Result<T, E> over panicking for recoverable errors
 • Use Vec<T> for dynamic arrays, &[T] slices for read-only views
 • HashMap is O(1) average — use for frequency counting
 • For concurrent algorithms, use Arc<Mutex<T>> or channels

C/C++:
─────────────────────────────────────────────────────────────
 • In C: Always check malloc return value
 • In C++: Prefer std::vector, std::unordered_map over raw arrays
 • RAII: Resource acquisition is initialization (smart pointers in C++)
 • Use const correctness aggressively
 • Always initialize variables (undefined behavior is a silent killer)

Go:
─────────────────────────────────────────────────────────────
 • Use slices over arrays for most problems
 • map[int]int for frequency counting
 • goroutines + channels for concurrent problems (if asked)
 • Always handle errors (if err != nil)
 • Use defer for cleanup

Python:
─────────────────────────────────────────────────────────────
 • collections.Counter for frequency
 • collections.defaultdict to avoid key-not-found errors
 • heapq for priority queue (min-heap by default)
 • bisect for binary search on sorted lists
 • Use list comprehensions but not at the cost of readability
```

---

# PART 7 — WHAT MOST CANDIDATES MISS

```
1. NOT CLARIFYING REQUIREMENTS FIRST
   → Designing without asking = answering a different question.
   → ALWAYS spend 2–3 minutes on requirements before designing.

2. IGNORING NON-FUNCTIONAL REQUIREMENTS
   → "It works" is not enough. How fast? How reliable? How cheap?

3. NOT HAVING NUMBERS
   → "We'll shard the database" → INTERVIEWER: "Why? How many rows?
     What's the QPS?" → If you can't estimate, you can't design.

4. JUMPING TO MICROSERVICES
   → Default answer is always monolith unless you have a clear
     reason to decompose. Microservices complexity is a tax.

5. FORGETTING FAILURE MODES
   → "What happens when the cache goes down? When the DB is slow?
     When the message queue fills up?" → Senior engineers think in
     failure modes first.

6. NO STORY PREPARATION (BEHAVIORAL)
   → Most candidates fail behavioral rounds because they haven't
     prepared specific stories. Prepare 10 stories, practice them.

7. WEAK METRICS IN IMPACT STATEMENTS
   → "I improved performance" → WEAK
   → "I reduced p99 API latency from 800ms to 120ms, improving
      checkout conversion by 3.2% ($2M ARR impact)" → STRONG

8. NOT ASKING CLARIFYING QUESTIONS IN CODING
   → Not asking is a red flag. It signals you don't think about
     edge cases, constraints, or production concerns.

9. CONFUSING AVAILABILITY AND DURABILITY
   → Availability: Can the system respond to requests? (uptime)
   → Durability: Is the data safe from loss? (persistence)
   → These require DIFFERENT solutions. Don't conflate them.

10. NOT KNOWING THE "WHY" OF TOOLS THEY USE
    → "We use Kafka" → "Why Kafka and not RabbitMQ or Redis Streams?"
    → Senior engineers must articulate the trade-offs of their choices.
```

---

# PART 8 — 8-WEEK PREPARATION ROADMAP

```
WEEK 1: FOUNDATION
─────────────────────────────────────────────────────────────
 Monday    : Re-read CAP Theorem, ACID vs BASE, SQL vs NoSQL
 Tuesday   : Study caching patterns (read all 4, implement LRU in Go)
 Wednesday : Study load balancing, CDN, DNS
 Thursday  : Practice 2 medium LeetCode problems (arrays, hash maps)
 Friday    : Write your flagship "most complex project" story (STAR+)
 Weekend   : Mock behavioral round (record yourself)

WEEK 2: SYSTEM DESIGN BASICS
─────────────────────────────────────────────────────────────
 Monday    : Design URL shortener (from scratch, 45 min timed)
 Tuesday   : Review your design against a reference, note gaps
 Wednesday : Design a rate limiter (bonus: implement in Go)
 Thursday  : Practice 2 medium LeetCode problems (BFS/DFS)
 Friday    : Write 3 more STAR+ stories (failure, conflict, influence)
 Weekend   : Mock system design with a friend or record yourself

WEEK 3: DISTRIBUTED SYSTEMS
─────────────────────────────────────────────────────────────
 Monday    : Study consistent hashing (what it is, why it matters)
 Tuesday   : Study Kafka/message queues deeply
 Wednesday : Design a notification system
 Thursday  : Practice 2 hard LeetCode problems (DP)
 Friday    : Write stories: mentoring, cross-team collaboration
 Weekend   : Full mock interview (60 min system design + 45 min behavioral)

WEEK 4: LEADERSHIP & BEHAVIORAL DEPTH
─────────────────────────────────────────────────────────────
 Monday    : Study code review strategies, tech debt frameworks
 Tuesday   : Study incident management (postmortems, runbooks)
 Wednesday : Design a distributed message queue (like Kafka itself)
 Thursday  : Practice 3 medium problems timed (30 min each)
 Friday    : Refine all 10 stories, ensure each has a number
 Weekend   : Mock behavioral interview

WEEK 5: ADVANCED DESIGN
─────────────────────────────────────────────────────────────
 Monday    : Design a chat system (WhatsApp-scale)
 Tuesday   : Design a search autocomplete system (Trie + distributed)
 Wednesday : Design a video streaming platform (Netflix-scale)
 Thursday  : Practice concurrency problems in Rust/Go
 Friday    : Write stories on ambiguity and tough decisions
 Weekend   : Full mock (coding + system design + behavioral)

WEEK 6: GAPS & DEPTH
─────────────────────────────────────────────────────────────
 Monday    : Identify your 3 weakest areas from mock feedback
 Tue-Thu   : Deep dive on those weaknesses
 Friday    : Timed full system design (45 min, no notes)
 Weekend   : Study the company's engineering blog, tech stack

WEEK 7: COMPANY-SPECIFIC PREP
─────────────────────────────────────────────────────────────
 Monday    : Research company's scale, stack, known technical challenges
 Tuesday   : Map your stories to their leadership principles/values
 Wednesday : Practice "What questions do you have for us?" (prepare 5)
 Thursday  : Final mock with time pressure (simulate exact interview conditions)
 Friday    : Light review, rest, no new material

WEEK 8: FINAL POLISH
─────────────────────────────────────────────────────────────
 Monday    : Review master cheat sheet
 Tuesday   : Practice verbal explanation of 3 system designs out loud
 Wednesday : Light practice (1–2 easy LeetCode to stay warm)
 Thu/Fri   : REST, sleep, mental clarity
 Interview : You are ready.
```

---

# PART 9 — MASTER CHEAT SHEET

## System Design Quick Decisions

```
Need low latency reads?              → Add Redis cache
Need full-text search?               → Elasticsearch
Need time-series data?               → InfluxDB, ClickHouse, or Cassandra
Need analytics/reporting queries?    → Column store (Redshift, BigQuery)
Need event streaming?                → Kafka (high throughput) / RabbitMQ (routing)
Need distributed lock?               → Redis SETNX or ZooKeeper
Need service discovery?              → Consul, etcd, or k8s native
Need global CDN?                     → CloudFront, Fastly, Akamai
Need rate limiting?                  → Token bucket or leaky bucket in Redis
Need distributed tracing?            → Jaeger, Zipkin, AWS X-Ray
```

## Numbers to Know Cold

```
1 KB  = 1,000 bytes
1 MB  = 1,000 KB
1 GB  = 1,000 MB
1 TB  = 1,000 GB

1 million operations/day = 12 ops/sec
1 billion ops/day        = 12,000 ops/sec

SSD random read: 0.1ms    |  HDD random read: 10ms
RAM access:      0.1µs    |  Network same DC: 0.5ms
L1 cache:        0.5ns    |  Internet (cross-continent): 150ms
```

## Behavioral Power Phrases

```
On ambiguity:
  "The first thing I do is separate what we know from what we assume."

On conflict:
  "I try to understand what outcome they're optimizing for.
   Often conflicts dissolve when you find the shared goal."

On failure:
  "The failure itself mattered less than how quickly we contained it
   and what we put in place to ensure it couldn't recur."

On trade-offs:
  "Every architectural choice is a bet. I try to make that bet explicit —
   what are we optimizing for, and what are we giving up?"

On mentorship:
  "My goal is to make myself unnecessary — to give engineers the tools
   to solve the next problem without me."

On technical decisions under pressure:
  "I distinguish between reversible and irreversible decisions.
   For reversible ones, I bias toward moving fast and learning.
   For irreversible ones, I slow down and get alignment."
```

## The 10 Questions You Should Ask the Interviewer

```
TECHNICAL:
 1. "What does the on-call rotation look like, and how are incidents handled?"
 2. "How does the team make technical decisions? Is there an RFC process?"
 3. "What does the current testing philosophy and CI/CD pipeline look like?"

TEAM & CULTURE:
 4. "How does the team handle disagreements about technical direction?"
 5. "What does the growth path look like for an engineer at this level?"
 6. "How do senior engineers interact with product and design?"

CHALLENGES (Shows strategic thinking):
 7. "What's the biggest technical challenge the team is facing in the next 6 months?"
 8. "What does 'success' look like for someone in this role at 90 days? At 1 year?"

SELF-SELECTION:
 9. "Is there anything in my background that gives you pause? I'd love to address it."
10. "What do you enjoy most about working here?"
```

---

## Final Mental Model: The Senior Engineer's Inner Monologue

```
When given any problem, a world-class senior engineer asks:
─────────────────────────────────────────────────────────────
 1. "Do I understand the REAL problem, or just the stated one?"
 2. "What does success look like, and how will we measure it?"
 3. "What are the top 3 failure modes of my proposed solution?"
 4. "What am I assuming that could be wrong?"
 5. "How would this scale 10x? 100x?"
 6. "Who else is affected by this decision, and have I consulted them?"
 7. "What will maintaining this code look like in 2 years?"
 8. "If I'm wrong, how hard is it to course-correct?"
 9. "Am I solving a symptom or the root cause?"
10. "What would I do differently if I had 3x more time? 10x less?"
```

---

*"The expert has made all the mistakes possible in a very narrow field." — Niels Bohr*

*Build your expertise deliberately. Every interview is a data point. Every rejection is a gift of information. Train like a monk. Execute like a warrior.*

Here is your complete master guide. Below is a structured breakdown of everything covered and what was added beyond the Google overview:

---

## What's Inside (9 Parts)

**Part 0 — Mindset & Meta-Strategy**
The single most overlooked part. Senior interviews don't test *if* you can do things — they test whether you think at *scale across systems, people, and time*. I included the exact mental shift from mid-level to senior thinking, plus the cognitive science principles (chunking, deliberate practice) to accelerate your preparation.

**Part 1 — System Design & Architecture**
Full RADIO framework for any design question. CAP theorem, SQL vs NoSQL decision trees, sharding strategies (including the geographic + time-series sharding you were asked about), all four caching patterns, availability patterns (Circuit Breaker, Active-Active), and complete walkthroughs for URL Shortener and Chat System with capacity estimates included.

**Part 2 — Technical Leadership**
The "Impact Pyramid" for storytelling, the Decision Log framework for ambiguity, the "Disagree and Commit" principle, the technical debt taxonomy (Intentional vs Reckless vs Inadvertent), and a tiered code review strategy with exact phrasing that sounds senior.

**Part 3 — Behavioral & Soft Skills**
STAR+ method (the `+` for reflection is what separates strong candidates), a complete 10-story bank template, the Analogy Ladder for explaining tech to non-technical stakeholders, and the Socratic Method for mentoring juniors.

**Part 4 — Debugging & Problem Solving**
A 3-phase production incident framework, the Strangler Fig refactoring pattern with testability examples, and debugging mental models (Scientific Method, Divide & Conquer, Follow the Data).

**Part 5 — Core Competencies**
Scalability axes, stateless vs stateful design, queue-based load leveling, reversibility as a meta-principle for trade-offs, and Monolith vs Microservices with the migration pattern.

**Part 6 — Coding Rounds (Senior Expectations)**
The 6-step expert protocol before writing code, complexity quick reference, and language-specific tips for Rust, C/C++, Go, and Python.

**Parts 7–9 — What Most Candidates Miss, 8-Week Roadmap, and Master Cheat Sheet**
The 10 most common failure points, a day-by-day 8-week prep plan, system design quick-decision reference, numbers to memorize, behavioral power phrases, and 10 questions to ask your interviewer.

---

The guide is structured so you can work through it linearly like a course, or jump to any section as a reference. Ask me to deep-dive any specific topic and I'll go full depth on it.